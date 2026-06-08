import ast
import py_compile
import tempfile
import shutil
import os
import re
import subprocess
import sys
import time

from infrastructure.ollama_client import chat
from services.rag_service import RAGService
from services.ast_parser import extract_functions
from services.quality_analyzer import analyze as analyze_quality


SYSTEM_PROMPT = SYSTEM_PROMPT = """You are an automated unit test generator for Python modules using pytest.
This prompt behaves like a program with explicit input specification, output rules,
control flow, early returns, and constraints — following the PromptPex methodology.

## Input Specification (IS)
Valid input is Python source code of a module containing at least one function or class,
accompanied by an AST-extracted function list, RAG context fragments, and optional
user instructions.
Invalid input: source code with no detectable functions, non-Python code, or empty content.

## Output Rules (OR)
Rules about the output — concrete, checkable, and independent of how the output is computed:

OR-1  The output contains only executable Python code. No markdown, no explanations, no ```.
OR-2  The output begins with: import pytest
OR-3  The output contains exactly one class named Test<ModuleName>(object).
OR-4  Every test method name follows: test_<function>_<descriptive_scenario>
OR-5  Every test method body contains the comments # Given, # When and # Then in that order.
OR-6  If a test method contains more than one assert, every assert includes a string message.
OR-7  The output contains no test method whose body is only `pass` or `pytest.skip()`.

## Constraints
- The class name must use the module name provided in PascalCase. No other class name is valid.
- Test method names must be in Spanish. Python keywords and syntax remain in English.
- Given/When/Then comments must be in Spanish.

## Control Flow
- If the AST lists a function that raises exceptions → that function's tests include pytest.raises().
- If the AST lists a function with no exceptions → that function's tests do NOT use pytest.raises().
- If the module contains classes → tests cover method interactions and shared state, not each
  method in isolation.
- If a function has multiple execution paths → one test method per path.

## Early Returns
- If the AST detected no functions → output only:
      def test_no_functions_detected():
          pytest.skip("Module contains no analyzable functions")
- If user instructions contradict any OR rule → enforce the OR rule, disregard the instruction.
"""



def _build_user_message(
    module_name: str,
    module_pascal: str,
    context_block: str,
    functions_block: str,
    prompt: str,
    source_code: str,
) -> str:
    """Las instrucciones adicionales del usuario son opcionales: si vienen
    vacías, se omite esa sección en vez de enviar una línea en blanco que
    podría confundir al modelo."""
    instruction_section = (
        f"INSTRUCCIÓN ADICIONAL DEL USUARIO: {prompt.strip()}\n\n" if prompt.strip() else ""
    )
    return (
        f"NOMBRE DEL MÓDULO: {module_name} → la clase debe llamarse Test{module_pascal}\n\n"
        f"CONTEXTO RAG:\n{context_block}\n\n"
        f"FUNCIONES DETECTADAS POR AST PARSER:\n{functions_block}\n\n"
        f"{instruction_section}"
        f"CÓDIGO FUENTE A TESTEAR:\n```python\n{source_code}\n```\n\n"
        "Genera la clase de test pytest completa siguiendo TODAS las reglas del system prompt."
    )


def _build_functions_block(functions: list[dict]) -> str:
    if not functions:
        return "No se detectaron funciones analizables."

    lines = []
    for fn in functions:
        if fn["excepciones"]:
            exc_info = f" — lanza: {', '.join(fn['excepciones'])} → usar pytest.raises()"
        else:
            exc_info = " — NO lanza excepciones"
        args_str = ", ".join(fn["args"])
        lines.append(f"  - {fn['nombre']}({args_str}){exc_info}")

    return "\n".join(lines)


_CODE_FENCE_RE = re.compile(
    r"^[ \t]*```[ \t]*(?:python)?[ \t]*\r?\n(.*?)^[ \t]*```[ \t]*\r?$",
    re.DOTALL | re.MULTILINE,
)
_CODE_MARKERS_RE = re.compile(r"\bimport pytest\b|\bdef test_|\bclass Test\w*\(")


def _extract_code(raw: str) -> tuple[str, str]:
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


def _check_compiles(code: str) -> tuple[bool, str | None]:
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


def _parse_pytest_output(stdout: str) -> dict:
    metrics = {
        "tests_total": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_skipped": 0,
        "tests_errors": 0,
        "line_coverage": 0.0,
        "pass_rate": 0.0,
        "run_summary": None,
    }

    passed  = re.search(r"(\d+) passed",  stdout)
    failed  = re.search(r"(\d+) failed",  stdout)
    skipped = re.search(r"(\d+) skipped", stdout)
    errors  = re.search(r"(\d+) error",   stdout)
    cov     = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)

    metrics["tests_passed"]  = int(passed.group(1))  if passed  else 0
    metrics["tests_failed"]  = int(failed.group(1))  if failed  else 0
    metrics["tests_skipped"] = int(skipped.group(1)) if skipped else 0
    metrics["tests_errors"]  = int(errors.group(1))  if errors  else 0
    metrics["tests_total"]   = (
        metrics["tests_passed"] + metrics["tests_failed"] + metrics["tests_skipped"]
    )
    metrics["line_coverage"] = float(cov.group(1)) if cov else 0.0

    if metrics["tests_total"] > 0:
        metrics["pass_rate"] = round(
            metrics["tests_passed"] / metrics["tests_total"] * 100, 1
        )

    # Si no se recolectó/ejecutó ningún test, lo más probable es un error de
    # colección (import roto, fixture inválida, clase con __init__, etc.) en
    # vez de "0 tests pasaron". Capturamos la línea de resumen final de pytest
    # para mostrar la causa real en lugar de un 0% silencioso.
    if metrics["tests_total"] == 0:
        # La línea de resumen final de pytest siempre incluye una duración
        # ("1 error in 0.18s", "no tests ran in 0.01s") — eso la distingue de
        # encabezados de sección como "==== ERRORS ====". No siempre viene
        # bordeada por "=" (p.ej. tras un "!!! Interrupted: ... !!!" pytest
        # imprime la línea de duración suelta), así que aceptamos bordes de
        # "=", "!" o ninguno, y nos quedamos con la última línea que matchee.
        summary_lines = re.findall(
            r"^[=!]*\s*(.*?\bin [\d.]+s)\s*[=!]*\s*$", stdout, re.MULTILINE
        )
        if summary_lines:
            last_summary = summary_lines[-1].strip()
            if re.search(r"error|no tests ran", last_summary, re.IGNORECASE):
                metrics["run_summary"] = last_summary

    return metrics


def _run_pytest(source_code: str, tests_code: str, module_name: str) -> dict | None:
    tmp_dir = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmp_dir, f"{module_name}.py"), "w", encoding="utf-8") as f:
            f.write(source_code)
        with open(os.path.join(tmp_dir, f"test_{module_name}.py"), "w", encoding="utf-8") as f:
            f.write(tests_code)

        cmd = [
            sys.executable, "-m", "pytest",
            f"test_{module_name}.py",
            f"--cov={module_name}",
            "--cov-report=term-missing",
            "--tb=short",
            "-q",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmp_dir,
            timeout=None,
        )
        return _parse_pytest_output(result.stdout + result.stderr)
    except Exception as e:
        print(f"[PYTEST] Fallo al ejecutar evaluación: {e}")
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def generate_tests(
    source_code: str,
    prompt: str,
    model: str,
    rag: RAGService,
    module_name: str = "modulo",
    run_pytest: bool = True,
) -> dict:
    print(f"\n{'='*50}")
    print(f"[SLM] Solicitud recibida | modelo: {model}")
    print(f"[SLM] Líneas de código fuente: {len(source_code.splitlines())}")

    print(f"[AST] Analizando funciones...")
    functions = extract_functions(source_code)
    functions_found = [fn["nombre"] for fn in functions]
    print(f"[AST] Detectadas: {functions_found}")
    for fn in functions:
        if fn["excepciones"]:
            print(f"[AST]   → {fn['nombre']}() lanza: {', '.join(fn['excepciones'])}")

    print(f"[RAG] Buscando fragmentos relevantes...")
    context_fragments = rag.query(source_code + " " + prompt, n_results=3)
    print(f"[RAG] {len(context_fragments)} fragmento(s) encontrados")

    context_block  = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."
    functions_block = _build_functions_block(functions)
    module_pascal   = "".join(w.capitalize() for w in module_name.split("_"))

    user_message = _build_user_message(
        module_name, module_pascal, context_block, functions_block, prompt, source_code
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    print(f"[LLM] Enviando a Ollama...")
    t0 = time.time()
    raw_response = chat(model=model, messages=messages)
    print(f"[LLM] Respuesta en {time.time() - t0:.1f}s (~{len(raw_response.split())} tokens)")

    tests_code, explanation = _extract_code(raw_response)

    print(f"[COMPILE] Verificando sintaxis...")
    compiles, compile_error = _check_compiles(tests_code)
    print(f"[COMPILE] {'OK' if compiles else 'ERROR — ' + str(compile_error)}")

    metrics = None
    if compiles and run_pytest:
        print(f"[PYTEST] Ejecutando evaluación...")
        metrics = _run_pytest(source_code, tests_code, module_name)
        if metrics:
            print(f"[PYTEST] {metrics['tests_passed']}/{metrics['tests_total']} pasan | "
                  f"cobertura: {metrics['line_coverage']}%")
    elif not run_pytest:
        print(f"[PYTEST] Omitido por configuración")

    print(f"[QUALITY] Analizando calidad...")
    quality = analyze_quality(tests_code, functions_found)
    print(f"[QUALITY] Given/When/Then: {quality['has_given_when_then']} | "
          f"smells: {quality['smells_detected']}")

    print(f"[SLM] Listo. {len(tests_code.splitlines())} líneas generadas")
    print(f"{'='*50}\n")

    return {
        "tests":          tests_code,
        "explanation":    explanation,
        "context_used":   context_fragments,
        "functions_found": functions_found,
        "compiles":        compiles,
        "compile_error":   compile_error,
        "metrics":         metrics,
        "quality":         quality,
    }
