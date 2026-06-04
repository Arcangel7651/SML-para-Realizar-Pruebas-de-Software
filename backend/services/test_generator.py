import py_compile
import tempfile
import os

from infrastructure.ollama_client import chat
from services.rag_service import RAGService


SYSTEM_PROMPT = """Eres un experto en testing de software Python con pytest.

REGLAS OBLIGATORIAS:
1. Genera UNA SOLA clase de test completa que cubra toda la clase bajo prueba.
   Incluye tests que ejerciten la interacción entre métodos y el estado compartido.
   NO generes tests sueltos por método fuera de una clase.

2. Cada método de test debe contener comentarios internos con la estructura:
   # Given  (precondiciones y estado inicial)
   # When   (acción que se ejecuta)
   # Then   (verificaciones del resultado esperado)

3. Los nombres de los métodos deben ser descriptivos en español y reflejar
   el escenario completo. Ejemplo:
   test_cuando_lista_vacia_entonces_suma_retorna_cero

4. Incluye TODOS los imports necesarios al inicio (pytest, unittest.mock, etc.).

5. EVITA estos test smells documentados en la literatura:
   - No uses assert dentro de bucles (pueden enmascarar fallos parciales)
   - No combines múltiples asserts no relacionados en un mismo test
   - No uses nombres genéricos como "result" sin contexto descriptivo
   - No dejes tests vacíos con solo "pass"

6. Retorna ÚNICAMENTE el código Python, sin explicaciones ni bloques markdown.
   No uses ```python ni ``` en tu respuesta.
"""


def _extract_code(raw: str) -> str:
    if "```python" in raw:
        raw = raw.split("```python", 1)[1]
        raw = raw.split("```", 1)[0]
    elif "```" in raw:
        raw = raw.split("```", 1)[1]
        raw = raw.split("```", 1)[0]
    return raw.strip()


def _check_compiles(code: str) -> tuple[bool, str | None]:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    try:
        py_compile.compile(tmp_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    finally:
        os.unlink(tmp_path)


def generate_tests(
    source_code: str,
    prompt: str,
    model: str,
    rag: RAGService,
) -> dict:
    context_fragments = rag.query(source_code + " " + prompt, n_results=3)
    context_block = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."

    user_message = (
        f"CONTEXTO RAG (patrones y buenas prácticas relevantes):\n{context_block}\n\n"
        f"INSTRUCCIÓN DEL USUARIO: {prompt}\n\n"
        f"CÓDIGO FUENTE A TESTEAR:\n```python\n{source_code}\n```\n\n"
        "Genera la clase de test pytest completa."
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    raw_response = chat(model=model, messages=messages)
    tests_code = _extract_code(raw_response)
    compiles, compile_error = _check_compiles(tests_code)

    return {
        "tests": tests_code,
        "context_used": context_fragments,
        "compiles": compiles,
        "compile_error": compile_error,
    }
