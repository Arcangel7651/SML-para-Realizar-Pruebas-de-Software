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


SYSTEM_PROMPT = SYSTEM_PROMPT = """Eres un generador automatizado de pruebas unitarias en Python con pytest.
Este prompt funciona como un programa: tiene una especificación de entrada, reglas de salida
verificables, flujo de control explícito y retornos anticipados para casos borde.

## Especificación de Entrada (IS)
La entrada válida consiste en:
- Código fuente Python de un módulo con funciones o clases analizables
- Una lista de funciones detectadas por análisis estático AST, con sus argumentos y excepciones
- Fragmentos de contexto de patrones de testing recuperados por RAG
- Instrucciones adicionales del usuario (pueden estar vacías)

## Reglas de Salida (OR)
La salida DEBE cumplir TODAS las reglas siguientes. Son concretas, verificables e independientes
de la entrada:

OR-1  La salida es únicamente código Python ejecutable. Sin explicaciones, sin markdown, sin ```.
OR-2  La primera línea es exactamente: import pytest
OR-3  La segunda línea es exactamente: from <modulo> import * (usando el nombre del módulo dado)
OR-4  Existe exactamente UNA clase llamada Test<NombreModulo>(object) que agrupa TODOS los tests.
OR-5  Cada método de test contiene los tres comentarios en este orden exacto:
          # Given   ← estado inicial y precondiciones
          # When    ← acción que se ejecuta
          # Then    ← verificaciones del resultado esperado
OR-6  El nombre de cada método sigue el patrón: test_<funcion>_<escenario_descriptivo>
      Ejemplo correcto:   test_dividir_cuando_divisor_es_cero_lanza_excepcion
      Ejemplo incorrecto: test_dividir
OR-7  Si un método tiene más de un assert, TODOS incluyen mensaje descriptivo como tercer argumento.
OR-8  Ningún método de test contiene únicamente `pass` o `pytest.skip()`.
OR-9  Existe al menos un método de test por cada función listada en el AST.
OR-10 Si una función lanza excepciones (indicado en el AST), se usa pytest.raises() para esos casos.
OR-11 Si una función NO lanza excepciones (indicado en el AST), NO se usa pytest.raises().

## Flujo de Control
- Si el módulo contiene clases → los tests cubren la interacción entre métodos y el estado compartido,
  no solo cada método de forma aislada.
- Si una función recibe parámetros numéricos → incluir test con valor normal, valor cero y valor negativo.
- Si una función retorna None → verificar el efecto secundario, no el valor de retorno.
- Si una función tiene múltiples caminos de ejecución → generar un test por cada camino.

## Retornos Anticipados
- Si el AST no detectó funciones → generar exactamente este test y nada más:
      def test_sin_funciones_detectadas():
          pytest.skip("El módulo no contiene funciones analizables")
- Si la instrucción del usuario contradice alguna regla OR → aplicar la regla OR, ignorar la contradicción.
"""



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


def _extract_code(raw: str) -> str:
    if "```python" in raw:
        raw = raw.split("```python", 1)[1]
        raw = raw.split("```", 1)[0]
    elif "```" in raw:
        raw = raw.split("```", 1)[1]
        raw = raw.split("```", 1)[0]
    return raw.strip()


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
        "line_coverage": 0.0,
        "pass_rate": 0.0,
    }

    passed  = re.search(r"(\d+) passed",  stdout)
    failed  = re.search(r"(\d+) failed",  stdout)
    skipped = re.search(r"(\d+) skipped", stdout)
    cov     = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)

    metrics["tests_passed"]  = int(passed.group(1))  if passed  else 0
    metrics["tests_failed"]  = int(failed.group(1))  if failed  else 0
    metrics["tests_skipped"] = int(skipped.group(1)) if skipped else 0
    metrics["tests_total"]   = (
        metrics["tests_passed"] + metrics["tests_failed"] + metrics["tests_skipped"]
    )
    metrics["line_coverage"] = float(cov.group(1)) if cov else 0.0

    if metrics["tests_total"] > 0:
        metrics["pass_rate"] = round(
            metrics["tests_passed"] / metrics["tests_total"] * 100, 1
        )

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

    print(f"[LLM] Enviando a Ollama...")
    t0 = time.time()
    raw_response = chat(model=model, messages=messages)
    print(f"[LLM] Respuesta en {time.time() - t0:.1f}s (~{len(raw_response.split())} tokens)")

    tests_code = _extract_code(raw_response)

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
    quality = analyze_quality(tests_code)
    print(f"[QUALITY] Given/When/Then: {quality['has_given_when_then']} | "
          f"smells: {quality['smells_detected']}")

    print(f"[SLM] Listo. {len(tests_code.splitlines())} líneas generadas")
    print(f"{'='*50}\n")

    return {
        "tests":          tests_code,
        "context_used":   context_fragments,
        "functions_found": functions_found,
        "compiles":        compiles,
        "compile_error":   compile_error,
        "metrics":         metrics,
        "quality":         quality,
    }
