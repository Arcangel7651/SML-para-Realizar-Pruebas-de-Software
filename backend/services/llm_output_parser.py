"""Interpretación de la respuesta cruda del LLM: separar el bloque de código de
prueba del texto conversacional y verificar que ese código compila. Es la
frontera entre "lo que devolvió el modelo" y "código Python utilizable"."""

import os
import py_compile
import re
import tempfile


_CODE_FENCE_RE = re.compile(
    r"^[ \t]*```[ \t]*(?:python)?[ \t]*\r?\n(.*?)^[ \t]*```[ \t]*\r?$",
    re.DOTALL | re.MULTILINE,
)
_CODE_MARKERS_RE = re.compile(r"\bimport pytest\b|\bdef test_|\bclass Test\w*\(")


def extract_code(raw: str) -> tuple[str, str]:
    """Separa el bloque de código real del texto conversacional que el modelo
    a veces agrega (p.ej. "¡Claro! Aquí tienes..."). El patrón exige que la
    cerca ``` esté sola en su línea — así una mención incidental dentro de la
    explicación (p.ej. citando la regla "sin ```python") no rompe el pareo de
    cercas del bloque de código real. Como respaldo, entre los bloques
    encontrados se prioriza el que contiene marcadores propios de un test
    pytest. Devuelve (codigo, explicacion)."""
    matches = list(_CODE_FENCE_RE.finditer(raw))

    code_match = next(
        (m for m in matches if _CODE_MARKERS_RE.search(m.group(1))),
        None,
    )
    if code_match is None and matches:
        code_match = max(matches, key=lambda m: len(m.group(1)))

    if code_match is not None:
        code = code_match.group(1).strip()
        explanation = (raw[:code_match.start()] + raw[code_match.end():]).strip()
        return code, explanation

    stripped = raw.strip()
    if _CODE_MARKERS_RE.search(stripped) or stripped.startswith(("import ", "from ", "class ", "def ", "#")):
        return stripped, ""
    return "", stripped


def check_compiles(code: str) -> tuple[bool, str | None]:
    fd, tmp_path = tempfile.mkstemp(suffix=".py")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(code)
        py_compile.compile(tmp_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
