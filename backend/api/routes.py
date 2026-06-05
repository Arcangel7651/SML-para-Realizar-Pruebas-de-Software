import os
import json
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from infrastructure.ollama_client import list_models, chat_stream
from infrastructure.file_reader import read_python_file
from services.rag_service import rag_service
from services.test_generator import (
    generate_tests,
    SYSTEM_PROMPT,
    _extract_code,
    _check_compiles,
    _run_pytest,
    _build_functions_block,
)
from services.ast_parser import extract_functions
from services.quality_analyzer import analyze as analyze_quality

router = APIRouter()


class DocumentRequest(BaseModel):
    doc_id: str
    text: str


class Metrics(BaseModel):
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    line_coverage: float
    pass_rate: float


class Quality(BaseModel):
    has_given_when_then: bool
    smells_detected: list[str]


class GenerateResponse(BaseModel):
    tests: str
    context_used: list[str]
    functions_found: list[str]
    compiles: bool
    compile_error: str | None
    metrics: Metrics | None
    quality: Quality


@router.get("/health")
async def health():
    models = list_models()
    return {"status": "ok", "models": models}


@router.get("/models")
async def get_models():
    return {"models": list_models()}


@router.post("/generate-tests", response_model=GenerateResponse)
async def generate_tests_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form(...),
    run_pytest: bool = Form(True),
):
    source_code  = await read_python_file(file)
    module_name  = os.path.splitext(file.filename)[0]
    result       = generate_tests(source_code, prompt, model, rag_service, module_name, run_pytest)
    return result


@router.post("/generate-tests-stream")
async def generate_tests_stream_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form(...),
    run_pytest: bool = Form(False),
):
    source_code  = await read_python_file(file)
    module_name  = os.path.splitext(file.filename)[0]
    module_pascal = "".join(w.capitalize() for w in module_name.split("_"))

    functions        = extract_functions(source_code)
    functions_found  = [fn["nombre"] for fn in functions]
    context_fragments = rag_service.query(source_code + " " + prompt, n_results=3)
    context_block    = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."
    functions_block  = _build_functions_block(functions)

    user_message = (
        f"NOMBRE DEL MÓDULO: {module_name} → la clase debe llamarse Test{module_pascal}\n\n"
        f"CONTEXTO RAG:\n{context_block}\n\n"
        f"FUNCIONES DETECTADAS POR AST PARSER:\n{functions_block}\n\n"
        f"INSTRUCCIÓN DEL USUARIO: {prompt}\n\n"
        f"CÓDIGO FUENTE A TESTEAR:\n```python\n{source_code}\n```\n\n"
        "Genera la clase de test pytest completa siguiendo TODAS las reglas del system prompt."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    def event_stream():
        yield json.dumps({
            "type": "meta",
            "functions_found": functions_found,
            "context_used": context_fragments,
        }) + "\n"

        raw_chunks = []
        for chunk in chat_stream(model=model, messages=messages):
            raw_chunks.append(chunk)
            yield json.dumps({"type": "token", "content": chunk}) + "\n"

        raw_response = "".join(raw_chunks)
        tests_code   = _extract_code(raw_response)
        compiles, compile_error = _check_compiles(tests_code)

        metrics = None
        if compiles and run_pytest:
            metrics = _run_pytest(source_code, tests_code, module_name)

        quality = analyze_quality(tests_code)

        yield json.dumps({
            "type":          "done",
            "tests":         tests_code,
            "compiles":      compiles,
            "compile_error": compile_error,
            "metrics":       metrics,
            "quality":       quality,
        }) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.get("/rag/documents")
async def list_rag_documents():
    return {"documents": rag_service.list_documents()}


@router.post("/rag/documents")
async def add_rag_document(body: DocumentRequest):
    rag_service.add_document(body.doc_id, body.text)
    return {"status": "ok", "doc_id": body.doc_id}
