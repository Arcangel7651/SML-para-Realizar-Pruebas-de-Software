import os
import json
import time
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from infrastructure.ollama_client import list_models, chat, chat_stream
from infrastructure.file_reader import read_python_file
from services.rag_service import rag_service
from services.test_generator import (
    generate_tests,
    SYSTEM_PROMPT,
    _extract_code,
    _check_compiles,
    _run_pytest,
    _learn_from_result,
    _learn_from_failure,
    _build_functions_block,
    _build_classes_block,
    _build_user_message,
    _build_degraded_tests,
    _missing_function_coverage,
    _build_coverage_retry_message,
    _repair_generated_tests,
    _build_potential_bugs,
)
from services.ast_parser import extract_functions, extract_classes
from services.quality_analyzer import analyze as analyze_quality
from services.results_log import log_result, read_results
from services.bugs_store import record_and_annotate, set_triage, all_bugs

router = APIRouter()


class DocumentRequest(BaseModel):
    doc_id: str
    text: str


class Metrics(BaseModel):
    tests_total: int
    tests_passed: int
    tests_failed: int
    tests_skipped: int
    tests_errors: int
    line_coverage: float
    branch_coverage: float | None
    pass_rate: float
    run_summary: str | None


class Quality(BaseModel):
    has_given_when_then: bool
    smells_detected: list[str]
    tests_per_function: dict[str, int]
    is_clean_output: bool
    starts_with_import_pytest: bool
    has_expected_test_class: bool
    expected_class_name: str | None


class PotentialBug(BaseModel):
    name: str
    detail: str
    seen_now: bool = True
    count: int = 1
    first_seen: str | None = None
    last_seen: str | None = None
    triage: str | None = None


class TriageRequest(BaseModel):
    module: str
    name: str
    detail: str
    triage: str | None = None


class GenerateResponse(BaseModel):
    tests: str
    explanation: str
    context_used: list[str]
    functions_found: list[str]
    compiles: bool
    compile_error: str | None
    metrics: Metrics | None
    quality: Quality
    learned: bool
    potential_bugs: list[PotentialBug] = []


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
    prompt: str = Form(""),
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
    prompt: str = Form(""),
    model: str = Form(...),
    run_pytest: bool = Form(True),
):
    source_code  = await read_python_file(file)
    module_name  = os.path.splitext(file.filename)[0]
    module_pascal = "".join(w.capitalize() for w in module_name.split("_"))

    functions        = extract_functions(source_code)
    functions_found  = [fn["nombre"] for fn in functions]
    # Advertencias del módulo (clave exacta) + patrones por similitud, aditivo.
    warnings          = rag_service.get_warnings(module_name)
    patterns          = rag_service.query(source_code + " " + prompt, n_results=3)
    context_fragments = warnings + patterns
    context_block    = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."
    functions_block  = _build_functions_block(functions)
    classes_block    = _build_classes_block(module_name, extract_classes(source_code))

    user_message = _build_user_message(
        module_name, module_pascal, context_block, functions_block, classes_block, prompt, source_code
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    def event_stream():
        t_start = time.time()
        yield json.dumps({
            "type": "meta",
            "functions_found": functions_found,
            "context_used": context_fragments,
        }) + "\n"

        raw_chunks = []
        try:
            for chunk in chat_stream(model=model, messages=messages):
                raw_chunks.append(chunk)
                yield json.dumps({"type": "token", "content": chunk}) + "\n"
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": f"Ollama no respondió: {e}",
            }) + "\n"
            return

        raw_response = "".join(raw_chunks)
        tests_code, explanation = _extract_code(raw_response)
        tests_code = _repair_generated_tests(
            tests_code, module_name, extract_classes(source_code), functions_found
        )
        compiles, compile_error = _check_compiles(tests_code)

        if not compiles:
            yield json.dumps({"type": "retrying", "reason": compile_error}) + "\n"
            retry_messages = messages + [
                {"role": "assistant", "content": raw_response},
                {"role": "user", "content": (
                    f"El código generado tiene un error de sintaxis Python:\n{compile_error}\n\n"
                    f"Corrige únicamente ese error y devuelve el código completo corregido. "
                    f"Solo código Python válido, sin explicaciones ni markdown."
                )},
            ]
            raw_retry = chat(model=model, messages=retry_messages)
            tests_retry, explanation_retry = _extract_code(raw_retry)
            tests_retry = _repair_generated_tests(
                tests_retry, module_name, extract_classes(source_code), functions_found
            )
            compiles_retry, compile_error_retry = _check_compiles(tests_retry)
            if compiles_retry:
                tests_code    = tests_retry
                explanation   = explanation_retry or explanation
                compiles      = True
                compile_error = None

        if compiles:
            missing_functions = _missing_function_coverage(tests_code, functions_found)
            if missing_functions:
                yield json.dumps({
                    "type": "retrying",
                    "reason": f"Faltan tests para: {', '.join(missing_functions)}",
                }) + "\n"
                retry_messages = messages + [
                    {"role": "assistant", "content": tests_code},
                    _build_coverage_retry_message(missing_functions),
                ]
                raw_retry2 = chat(model=model, messages=retry_messages)
                tests_retry2, explanation_retry2 = _extract_code(raw_retry2)
                tests_retry2 = _repair_generated_tests(
                    tests_retry2, module_name, extract_classes(source_code), functions_found
                )
                compiles_retry2, compile_error_retry2 = _check_compiles(tests_retry2)
                if compiles_retry2:
                    tests_code  = tests_retry2
                    explanation = explanation_retry2 or explanation

        degraded = False
        if not compiles:
            classes_detected = extract_classes(source_code)
            degraded_code = _build_degraded_tests(
                tests_code, module_name, module_pascal, functions_found, classes_detected, compile_error
            )
            degraded_compiles, degraded_compile_error = _check_compiles(degraded_code)
            if degraded_compiles:
                tests_code    = degraded_code
                compiles      = True
                compile_error = None
                degraded      = True

        metrics = None
        passing_tests = set()
        failures = {}
        if compiles and run_pytest:
            metrics, passing_tests, failures = _run_pytest(source_code, tests_code, module_name)

        quality = analyze_quality(tests_code, functions_found, f"Test{module_pascal}")

        learned = _learn_from_result(
            rag_service, module_name, functions_found, tests_code, compiles, metrics, quality,
            passing_tests, source_code,
        )
        _learn_from_failure(rag_service, module_name, quality, compiles, metrics, failures, degraded)

        log_result(model, module_name, metrics, quality, functions_found, context_fragments, warnings, compiles, learned, degraded, time.time() - t_start)

        potential_bugs = record_and_annotate(module_name, _build_potential_bugs(failures, degraded, tests_code, functions_found))

        yield json.dumps({
            "type":          "done",
            "tests":         tests_code,
            "explanation":   explanation,
            "compiles":      compiles,
            "compile_error": compile_error,
            "metrics":       metrics,
            "quality":       quality,
            "learned":       learned,
            "degraded":      degraded,
            "potential_bugs": potential_bugs,
        }) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.get("/results")
async def get_results():
    return {"results": read_results()}


@router.get("/bugs")
async def get_bugs_endpoint():
    """Todos los posibles bugs registrados por módulo (para análisis de datos).
    No interviene en la generación."""
    return {"bugs": all_bugs()}


@router.post("/bugs/triage")
async def triage_bug(body: TriageRequest):
    """Clasifica un posible bug (bug_real / falso_positivo / None). Anotación
    privada para análisis; no influye en el modelo."""
    ok = set_triage(body.module, body.name, body.detail, body.triage)
    return {"status": "ok" if ok else "not_found"}


@router.get("/rag/documents")
async def list_rag_documents():
    return {"documents": rag_service.list_documents()}


@router.post("/rag/documents")
async def add_rag_document(body: DocumentRequest):
    rag_service.add_document(body.doc_id, body.text)
    return {"status": "ok", "doc_id": body.doc_id}
