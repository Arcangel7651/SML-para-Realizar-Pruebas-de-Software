import os
from collections.abc import Generator
import ollama


# Timeout por solicitud HTTP a Ollama. Si el servidor se queda colgado o sin
# responder, la llamada falla tras este tiempo en vez de bloquearse de forma
# indefinida (evita esperas de horas si Ollama deja de responder).
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
_client = ollama.Client(host=OLLAMA_HOST, timeout=OLLAMA_TIMEOUT)


def list_models() -> list[str]:
    try:
        response = _client.list()
        return [m.model for m in response.models]
    except Exception:
        return []


# Mantiene el modelo cargado en memoria/VRAM entre solicitudes para evitar
# el costo de recarga (varios segundos) si pasan más de 5 minutos (default
# de Ollama) entre generaciones.
KEEP_ALIVE = "30m"

# Límite de tokens generados. Una clase de tests pytest no necesita más de
# esto; acota el caso en que el modelo entra en un bucle de repetición y
# nunca emite un token de fin (lo que puede tardar horas en CPU).
CHAT_OPTIONS = {"num_predict": 4096}


def chat(model: str, messages: list[dict]) -> str:
    response = _client.chat(model=model, messages=messages, keep_alive=KEEP_ALIVE, options=CHAT_OPTIONS)
    return response.message.content


def chat_stream(model: str, messages: list[dict]) -> Generator[str, None, None]:
    for chunk in _client.chat(model=model, messages=messages, stream=True, keep_alive=KEEP_ALIVE, options=CHAT_OPTIONS):
        content = chunk.message.content
        if content:
            yield content


# Modelo de embeddings para la recuperación semántica del RAG. Más liviano que
# los de generación; se puede sobreescribir por entorno.
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Devuelve el embedding de cada texto, o None si el servicio de
    embeddings no está disponible (modelo no descargado, Ollama caído, etc.).
    El RAG usa None como señal para caer a TF-IDF en vez de romperse."""
    if not texts:
        return []
    try:
        vectors = []
        for text in texts:
            response = _client.embeddings(model=EMBED_MODEL, prompt=text, keep_alive=KEEP_ALIVE)
            vector = response["embedding"] if isinstance(response, dict) else response.embedding
            vectors.append(list(vector))
        return vectors
    except Exception as e:
        print(f"[EMBED] No disponible ({e}); se usará TF-IDF.")
        return None
