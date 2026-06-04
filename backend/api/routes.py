from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from infrastructure.ollama_client import list_models
from infrastructure.file_reader import read_python_file
from services.rag_service import rag_service
from services.test_generator import generate_tests

router = APIRouter()


class DocumentRequest(BaseModel):
    doc_id: str
    text: str


@router.get("/health")
async def health():
    models = list_models()
    return {"status": "ok", "models": models}


@router.get("/models")
async def get_models():
    return {"models": list_models()}


@router.post("/generate-tests")
async def generate_tests_endpoint(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form(...),
):
    source_code = await read_python_file(file)
    result = generate_tests(source_code, prompt, model, rag_service)
    return result


@router.get("/rag/documents")
async def list_rag_documents():
    return {"documents": rag_service.list_documents()}


@router.post("/rag/documents")
async def add_rag_document(body: DocumentRequest):
    rag_service.add_document(body.doc_id, body.text)
    return {"status": "ok", "doc_id": body.doc_id}
