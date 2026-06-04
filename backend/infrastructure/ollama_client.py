import os
import ollama


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_client = ollama.Client(host=OLLAMA_HOST)


def list_models() -> list[str]:
    try:
        response = _client.list()
        return [m.model for m in response.models]
    except Exception:
        return []


def chat(model: str, messages: list[dict]) -> str:
    response = _client.chat(model=model, messages=messages)
    return response.message.content
