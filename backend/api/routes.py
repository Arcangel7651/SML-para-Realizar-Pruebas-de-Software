import os
import json
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.ablation import run_ablation

from infrastructure.ollama_client import list_models
from infrastructure.file_reader import read_python_file
from services.rag_service import rag_service, GLOBAL_LESSONS_DEFAULT
from services.test_generator import generate_tests, run_pipeline
from services.results_log import read_results
from services.bugs_store import set_triage, all_bugs

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
    triage: str | None = None          # triaje manual del humano (ground truth)
    oracle_triage: str | None = None   # veredicto automático del oráculo (docstring)


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
    use_global_lessons: bool = Form(GLOBAL_LESSONS_DEFAULT),
):
    source_code  = await read_python_file(file)
    module_name  = os.path.splitext(file.filename)[0]
    result       = generate_tests(source_code, prompt, model, rag_service, module_name, run_pytest, use_global_lessons)
    return result


@router.post("/generate-tests-stream")
async def generate_tests_stream_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(""),
    model: str = Form(...),
    run_pytest: bool = Form(True),
    use_global_lessons: bool = Form(GLOBAL_LESSONS_DEFAULT),
):
    source_code = await read_python_file(file)
    module_name = os.path.splitext(file.filename)[0]

    # El pipeline vive completo en services/test_generator.run_pipeline; aquí solo
    # se serializa cada evento a NDJSON. La ruta no-stream (generate_tests) consume
    # ese mismo generador, así que no hay lógica de dominio duplicada (regla 4).
    def event_stream():
        for event in run_pipeline(
            source_code, prompt, model, rag_service, module_name, run_pytest, use_global_lessons
        ):
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@router.get("/results")
async def get_results():
    return {"results": read_results()}


@router.post("/ablation/run")
async def ablation_run(
    correctos: list[UploadFile] = File(default=[]),
    incorrectos: list[UploadFile] = File(default=[]),
    model: str = Form(...),
    reps: int = Form(5),
):
    """Corre la ablación de lecciones globales (ON vs OFF) sobre los módulos
    subidos y transmite el progreso como NDJSON. Los archivos llegan en dos
    grupos etiquetados (correctos / incorrectos) para que el resumen separe
    ambas clases y mida bug_detected_rate en los incorrectos. Cada módulo se
    ejecuta con un nombre único por corrida (siempre fresco) y los stores se
    respaldan/restauran; ver services/ablation.py."""
    reps = max(1, min(reps, 20))
    modules: dict[str, dict] = {}
    for f in correctos:
        code = await read_python_file(f)
        modules[os.path.splitext(f.filename)[0]] = {"code": code, "label": "correcto"}
    for f in incorrectos:
        code = await read_python_file(f)
        modules[os.path.splitext(f.filename)[0]] = {"code": code, "label": "incorrecto"}

    def event_stream():
        for event in run_ablation(modules, model, reps):
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


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
