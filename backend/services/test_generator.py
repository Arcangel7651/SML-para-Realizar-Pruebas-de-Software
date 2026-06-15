import ast
import py_compile
import tempfile
import textwrap
import shutil
import os
import re
import subprocess
import sys
import time

from infrastructure.ollama_client import chat
from services.rag_service import RAGService
from services.ast_parser import extract_functions, extract_classes
from services.quality_analyzer import analyze as analyze_quality, count_tests_by_function, find_empty_raises_tests
from services.results_log import log_result
from services.bugs_store import record_and_annotate


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
OR-8  Every function/method listed in "FUNCIONES DETECTADAS POR AST PARSER" has at least
      one corresponding test method (test_<function>_<scenario>). No function from that
      list is left without a test.

## Constraints
- The class name must use the module name provided in PascalCase. No other class name is valid.
- Test method names must be in Spanish. Python keywords and syntax remain in English.
- Given/When/Then comments must be in Spanish.
- Every function or method called on the code under test must exist in the AST-extracted
  function list or in the provided source code. Never call a function or method that is
  not present there, even if it appears in a RAG context example — RAG examples are
  illustrative patterns, not literal code to copy.
- pytest.raises() may only be used for exceptions that the AST-extracted info or the
  source code shows the function/method actually raises.
- If the source code defines a class (see "CLASES DETECTADAS" in the user message), the
  test file must import it with `from <module_name> import <ClassName>` and call its
  methods on an instance, e.g. `<ClassName>().metodo(...)`.
  Inside a test method, `self` always refers to the Test<ModuleName> instance — NEVER
  call `self.<metodo_de_la_clase_bajo_prueba>(...)`. That method does not exist on the
  test class and will raise AttributeError.
- If the source code only defines top-level functions (no class), import them directly
  with `from <module_name> import <function1>, <function2>, ...` and call them as
  plain functions, not via `self`.

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



def _build_classes_block(module_name: str, classes: list[str]) -> str:
    if not classes:
        return (
            "No se detectaron clases en el código fuente: son funciones a nivel de "
            f"módulo. Importarlas con `from {module_name} import <funcion>, ...` y "
            "llamarlas directamente, no a través de `self`."
        )

    lines = []
    for class_name in classes:
        lines.append(
            f"  - {class_name} → `from {module_name} import {class_name}` y "
            f"`{class_name}().metodo(...)` para llamar sus métodos. "
            f"`self` en los tests NUNCA es una instancia de {class_name}."
        )
    return "\n".join(lines)


def _build_user_message(
    module_name: str,
    module_pascal: str,
    context_block: str,
    functions_block: str,
    classes_block: str,
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
        f"CLASES DETECTADAS:\n{classes_block}\n\n"
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


_TEST_METHOD_RE = re.compile(r"^([ \t]*)def (test_\w+)\s*\(", re.MULTILINE)


def _referenced_names(code: str) -> set[str]:
    """Nombres (ast.Name) usados en el código de prueba."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return set()
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}


def _already_imports_module(code: str, module_name: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
        if isinstance(node, ast.Import) and any(a.name == module_name for a in node.names):
            return True
    return False


def _ensure_module_import(
    code: str, module_name: str, classes: list[str], functions_found: list[str]
) -> str:
    """Fix determinístico del fallo más común: el modelo genera tests que usan
    `Calculadora()` o `funcion()` del módulo bajo prueba pero olvida importarlos.
    Eso compila (NameError es error de ejecución), pero hace fallar TODOS los
    tests con 0% de cobertura. Si detecta símbolos del módulo usados sin
    importar, inyecta `from <module> import <símbolos>` tras `import pytest`.

    Si el módulo define clases, los símbolos importables son las clases (sus
    métodos no se importan); si solo hay funciones a nivel de módulo, esas."""
    if _already_imports_module(code, module_name):
        return code

    symbols = classes if classes else functions_found
    used = _referenced_names(code)
    needed = [s for s in dict.fromkeys(symbols) if s in used]
    if not needed:
        return code

    import_line = f"from {module_name} import {', '.join(needed)}"
    lines = code.splitlines()
    insert_at = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("import pytest"):
            insert_at = i + 1
            break
    lines.insert(insert_at, import_line)
    return "\n".join(lines)


def _fix_self_method_calls(code: str, classes: list[str], functions_found: list[str]) -> str:
    """Reescribe `self.<metodo>(...)` por `<Clase>().<metodo>(...)` para los
    métodos de la clase bajo prueba. El modelo a veces invoca los métodos sobre
    `self` (estilo unittest), pero en pytest `self` es la instancia de
    Test<Modulo>, no de la clase bajo prueba, así que `self.sumar(...)` lanza
    AttributeError y ningún test toca el código real (0% de cobertura). Solo se
    reescriben nombres que son métodos reales de la clase (lista del AST), para
    no tocar helpers legítimos del test."""
    if not classes or not functions_found:
        return code
    class_name = classes[0]
    # nombres más largos primero para que p.ej. "es_par" no quede eclipsado
    methods = sorted(dict.fromkeys(functions_found), key=len, reverse=True)
    pattern = re.compile(r"\bself\.(" + "|".join(re.escape(m) for m in methods) + r")\b")
    return pattern.sub(rf"{class_name}().\1", code)


def _repair_generated_tests(
    code: str, module_name: str, classes: list[str], functions_found: list[str]
) -> str:
    """Aplica los fixes determinísticos a la salida del modelo, en orden:
    1) corrige `self.<metodo>()` -> `<Clase>().<metodo>()` (así el código pasa
       a referenciar la clase), y luego
    2) inyecta el import de la clase/funciones si falta.
    El orden importa: el paso 2 detecta que la clase se usa gracias al paso 1."""
    code = _fix_self_method_calls(code, classes, functions_found)
    code = _ensure_module_import(code, module_name, classes, functions_found)
    return code


def _salvage_test_methods(code: str) -> list[str]:
    """Cuando el archivo completo no compila (ni tras el reintento), rescata
    los métodos test_* que sí son sintácticamente válidos por sí solos,
    descartando el resto. Permite conservar parte del trabajo del LLM en
    vez de tirar todo el archivo a la basura."""
    lines = code.splitlines()
    matches = list(_TEST_METHOD_RE.finditer(code))

    salvaged = []
    for m in matches:
        indent = len(m.group(1))
        start_line = code[:m.start()].count("\n")
        end_line = len(lines)
        for j in range(start_line + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                continue
            cur_indent = len(lines[j]) - len(lines[j].lstrip())
            if cur_indent <= indent:
                end_line = j
                break

        block = lines[start_line:end_line]
        dedented = "\n".join(
            l[indent:] if len(l) >= indent else l.lstrip() for l in block
        )
        try:
            ast.parse(dedented)
        except SyntaxError:
            continue
        salvaged.append(dedented.rstrip())

    return salvaged


def _filter_to_passing_tests(code: str, passing: set[str]) -> str:
    """Devuelve el código conservando el encabezado (imports, clase, fixtures
    al inicio) y SOLO los métodos test_* cuyo nombre está en `passing`.
    Se basa en líneas (no en ast.unparse) para preservar los comentarios
    Given/When/Then. Usado para aprender únicamente del subconjunto de tests
    verificados que pasaron, sin arrastrar los que fallaron."""
    lines = code.splitlines()
    matches = list(_TEST_METHOD_RE.finditer(code))
    if not matches:
        return code

    first_start = code[: matches[0].start()].count("\n")
    header = lines[:first_start]

    kept_blocks = []
    for m in matches:
        name = m.group(2)
        indent = len(m.group(1))
        start_line = code[: m.start()].count("\n")
        end_line = len(lines)
        for j in range(start_line + 1, len(lines)):
            stripped = lines[j].strip()
            if not stripped:
                continue
            cur_indent = len(lines[j]) - len(lines[j].lstrip())
            if cur_indent <= indent:
                end_line = j
                break
        if name not in passing:
            continue
        block = lines[start_line:end_line]
        while block and not block[-1].strip():
            block.pop()
        kept_blocks.append("\n".join(block))

    if not kept_blocks:
        return code

    return "\n".join(header).rstrip() + "\n\n" + "\n\n".join(kept_blocks) + "\n"


def _build_skip_stub(name: str, reason: str) -> str:
    safe_reason = reason.replace('"', "'")
    return (
        f"    def test_{name}_no_generado(self):\n"
        f"        # Given: el modelo no generó un test válido para '{name}'\n"
        f"        # When: se ejecuta la suite generada\n"
        f"        # Then: se omite hasta regenerar manualmente\n"
        f'        pytest.skip("Generación de SLM falló: {safe_reason}")'
    )


def _build_degraded_imports(module_name: str, functions_found: list[str], classes: list[str]) -> str:
    names = classes or functions_found
    if not names:
        return f"# {module_name}: no se detectaron símbolos importables"
    return f"from {module_name} import {', '.join(dict.fromkeys(names))}"


def _build_degraded_tests(
    raw_code: str,
    module_name: str,
    module_pascal: str,
    functions_found: list[str],
    classes: list[str],
    compile_error: str | None,
) -> str:
    """Última red de seguridad cuando ni la generación inicial ni el
    reintento compilan. Rescata los métodos test_* que sí compilan de
    forma aislada y cubre con pytest.skip() cualquier función sin un test
    sobreviviente, para que la suite siempre se pueda ejecutar y produzca
    métricas reales (en vez de terminar vacía)."""
    salvaged = _salvage_test_methods(raw_code)
    salvaged_code = "\n\n".join(salvaged)
    covered = count_tests_by_function(salvaged_code, functions_found)

    reason = (compile_error or "error de compilación desconocido").splitlines()[0][:200]
    stubs = [
        _build_skip_stub(fn, reason)
        for fn, count in covered.items()
        if count == 0
    ]
    if not functions_found and not salvaged:
        stubs = [_build_skip_stub("modulo", reason)]

    salvaged_methods = [textwrap.indent(s, "    ") for s in salvaged]
    body = "\n\n".join(salvaged_methods + stubs)

    return (
        "import pytest\n"
        f"{_build_degraded_imports(module_name, functions_found, classes)}\n\n\n"
        f"class Test{module_pascal}(object):\n"
        f"{body}\n"
    )


def _missing_function_coverage(tests_code: str, functions_found: list[str]) -> list[str]:
    """Funciones detectadas por el AST parser que no tienen ningún
    test_<funcion>_<escenario> asociado (OR-8). Se usa para decidir si vale
    la pena un retry pidiéndole al modelo que complete la cobertura."""
    counts = count_tests_by_function(tests_code, functions_found)
    return [fn for fn, count in counts.items() if count == 0]


def _build_coverage_retry_message(missing_functions: list[str]) -> dict:
    return {
        "role": "user",
        "content": (
            "El archivo de tests no cubre estas funciones detectadas por el AST parser: "
            f"{', '.join(missing_functions)}.\n"
            "Agrega al menos un método test_<función>_<escenario> para cada una de ellas, "
            "sin eliminar ni modificar los tests ya existentes. Devuelve la clase de test "
            "completa con los cambios aplicados, solo código Python válido, sin "
            "explicaciones ni markdown."
        ),
    }


def _parse_pytest_output(stdout: str) -> dict:
    metrics = {
        "tests_total": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_skipped": 0,
        "tests_errors": 0,
        "line_coverage": 0.0,
        "branch_coverage": None,
        "pass_rate": 0.0,
        "run_summary": None,
    }

    passed  = re.search(r"(\d+) passed",  stdout)
    failed  = re.search(r"(\d+) failed",  stdout)
    skipped = re.search(r"(\d+) skipped", stdout)
    errors  = re.search(r"(\d+) error",   stdout)
    # Con --cov-branch: TOTAL  stmts  miss  branch  brpart  cover%
    cov_branch = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+(\d+)%", stdout)
    # Sin branch:       TOTAL  stmts  miss  cover%
    cov = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout) if not cov_branch else None

    metrics["tests_passed"]  = int(passed.group(1))  if passed  else 0
    metrics["tests_failed"]  = int(failed.group(1))  if failed  else 0
    metrics["tests_skipped"] = int(skipped.group(1)) if skipped else 0
    metrics["tests_errors"]  = int(errors.group(1))  if errors  else 0
    metrics["tests_total"]   = (
        metrics["tests_passed"] + metrics["tests_failed"] + metrics["tests_skipped"]
    )
    if cov_branch:
        total_br   = int(cov_branch.group(1))
        partial_br = int(cov_branch.group(2))
        metrics["line_coverage"]   = float(cov_branch.group(3))
        metrics["branch_coverage"] = (
            round((total_br - partial_br) / total_br * 100, 1)
            if total_br > 0 else 100.0
        )
    elif cov:
        metrics["line_coverage"] = float(cov.group(1))

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


_PYTEST_RESULT_RE = re.compile(r"::(test_\w+).*?(PASSED|FAILED|ERROR|SKIPPED)")


def _parse_passing_tests(stdout: str) -> set[str]:
    """Nombres de los métodos test_* que pasaron, según la salida verbose de
    pytest (líneas tipo `...::TestX::test_y PASSED`). Usado para aprender solo
    del subconjunto verificado-correcto cuando no pasan todos."""
    passing = set()
    for name, status in _PYTEST_RESULT_RE.findall(stdout):
        if status == "PASSED":
            passing.add(name)
    return passing


_FAIL_HEADER_RE = re.compile(r"^_{3,}\s+(?:\w+\.)?(test_\w+)\b.*?\s+_{3,}\s*$", re.MULTILINE)


def _parse_failure_details(stdout: str) -> dict[str, str]:
    """Extrae, por cada test que FALLÓ, un resumen de la aserción incumplida: la
    línea `assert ...` del código y la explicación `E   assert X == Y` que pytest
    imprime con --tb=short. Es la señal semántica más rica que produce la corrida
    (el modelo fijó un valor esperado incorrecto), y es justo la que el resto del
    pipeline descartaba. Devuelve {nombre_test: detalle}."""
    start = re.search(r"^=+ FAILURES =+$", stdout, re.MULTILINE)
    if not start:
        return {}
    section = stdout[start.end():]
    # Cortar en la siguiente sección con borde de '=' (resumen corto, total, etc.).
    end = re.search(r"^=+ \w", section, re.MULTILINE)
    if end:
        section = section[:end.start()]

    details: dict[str, str] = {}
    headers = list(_FAIL_HEADER_RE.finditer(section))
    for i, h in enumerate(headers):
        name = h.group(1)
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(section)
        block = section[h.end():block_end]

        assert_line = None
        error_lines = []
        for raw in block.splitlines():
            stripped = raw.strip()
            if assert_line is None and stripped.startswith("assert "):
                assert_line = stripped
            elif raw.lstrip().startswith("E ") or raw.lstrip() == "E":
                err = raw.lstrip()[1:].strip()
                if err:
                    error_lines.append(err)

        parts = []
        if assert_line:
            parts.append(assert_line)
        if error_lines:
            # La primera línea E suele ser "assert 4 == 5"; la siguiente el
            # "+ where 4 = sumar(2, 2)". Con dos basta para dar contexto.
            parts.append(" | ".join(error_lines[:2]))
        if parts:
            details[name] = " → ".join(parts)[:240]
    return details


def _run_pytest(source_code: str, tests_code: str, module_name: str) -> tuple[dict | None, set[str], dict[str, str]]:
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
            "--cov-branch",
            "--tb=short",
            "-v",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=tmp_dir,
            timeout=None,
        )
        output = result.stdout + result.stderr
        return (
            _parse_pytest_output(output),
            _parse_passing_tests(output),
            _parse_failure_details(output),
        )
    except Exception as e:
        print(f"[PYTEST] Fallo al ejecutar evaluación: {e}")
        return None, set(), {}
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _build_potential_bugs(
    failures: dict[str, str], degraded: bool, tests_code: str, functions_found: list[str]
) -> list[dict]:
    """Opción A: tests que compilaron y se ejecutaron pero FALLARON, con su
    detalle de aserción (esperado vs obtenido), presentados al humano como
    'posible bug detectado o aserción incorrecta' en vez de descartarlos en
    silencio. Un fallo aquí significa una de dos cosas, y solo un humano puede
    decidir cuál: (a) el código bajo prueba tiene un bug que el test cazó, o
    (b) el modelo fijó un valor esperado equivocado.

    Se excluyen los fallos de tests MALFORMADOS (un `pytest.raises` que nunca
    invoca la función → falla con 'DID NOT RAISE' aunque el código sea correcto):
    el roto es el test, no el código, así que no es un posible bug (reduce falsos
    positivos). No se incluyen tampoco en corridas degradadas: ahí el código son
    stubs del respaldo, no salida real del modelo."""
    if degraded or not failures:
        return []
    malformed = find_empty_raises_tests(tests_code, functions_found)
    return [
        {"name": name, "detail": detail}
        for name, detail in failures.items()
        if name not in malformed
    ]


def _should_learn(compiles: bool, metrics: dict | None, quality: dict) -> bool:
    """Solo se aprende de resultados que compilan, pasan pytest sin fallos
    ni errores, cumplen todas las reglas OR del prompt (sin test smells) y
    cubren con al menos un test cada función detectada (OR-8).
    Esto evita contaminar el índice RAG con ejemplos defectuosos o incompletos."""
    if not compiles or metrics is None:
        return False
    if metrics["tests_total"] == 0 or metrics["tests_failed"] > 0 or metrics["tests_errors"] > 0:
        return False
    return (
        quality["is_clean_output"]
        and quality["starts_with_import_pytest"]
        and quality["has_expected_test_class"]
        and quality["has_given_when_then"]
        and not quality["smells_detected"]
        and all(count > 0 for count in quality["tests_per_function"].values())
    )


_LEARNED_COUNT_RE = re.compile(r"(\d+) test\(s\) verificados")
_SCORE_MARKER_RE = re.compile(r"\[meta score=([\d.]+) kept=(\d+)\]")
_COVERAGE_RE = re.compile(r"([\d.]+)% de cobertura")

# Cuántos ejemplos verificados se conservan por módulo. Varias versiones buenas
# (p.ej. una centrada en el camino feliz y otra en excepciones) le dan al RAG
# más diversidad few-shot que un único ejemplo sobrescrito una y otra vez.
MAX_EXAMPLES_PER_MODULE = 3


def _example_score(line_coverage: float, kept: int) -> float:
    """Calidad de un ejemplo verificado, para decidir cuál conservar cuando hay
    más candidatos que cupos. La cobertura manda (un ejemplo que ejercita más
    código enseña más); el nº de tests verificados solo desempata. Se combinan
    en un número monótono: la cobertura como parte entera dominante y los tests
    como fracción acotada (<1), así más cobertura siempre gana y, a igualdad de
    cobertura, gana el que tenga más tests.

    La cobertura recibida es la del código que realmente se guarda (en modo
    parcial, _learn_from_result re-ejecuta pytest sobre el subconjunto antes de
    llamar aquí), no la de la suite completa: así el score no se infla."""
    return round(line_coverage + min(kept, 99) / 100.0, 4)


def _parse_example_meta(text: str) -> tuple[float, int]:
    """(score, kept) de un ejemplo ya guardado. Usa el marcador `[meta ...]`; si
    no está (ejemplos de una versión anterior), lo deduce del texto en prosa."""
    m = _SCORE_MARKER_RE.search(text)
    if m:
        return float(m.group(1)), int(m.group(2))
    kept_m = _LEARNED_COUNT_RE.search(text)
    cov_m = _COVERAGE_RE.search(text)
    kept = int(kept_m.group(1)) if kept_m else 0
    cov = float(cov_m.group(1)) if cov_m else 0.0
    return _example_score(cov, kept), kept


def _example_code(text: str) -> str:
    """Código de prueba dentro del texto de un ejemplo guardado (lo que sigue a
    'Código de prueba:'). Sirve para detectar duplicados exactos entre slots."""
    return text.split("Código de prueba:\n", 1)[-1].strip()


def _next_slot_id(module_name: str, used_ids: set[str]) -> str:
    base = f"learned_{module_name}"
    n = 0
    while f"{base}#{n}" in used_ids:
        n += 1
    return f"{base}#{n}"


def _learn_from_result(
    rag: RAGService,
    module_name: str,
    functions_found: list[str],
    tests_code: str,
    compiles: bool,
    metrics: dict | None,
    quality: dict,
    passing_tests: set[str] | None = None,
    source_code: str = "",
) -> bool:
    """Guarda ejemplos verificados en el RAG. Dos modos de contenido:

    - Completo: pasan todos los tests y se cumplen todas las reglas OR -> se
      guarda el archivo entero.
    - Parcial: solo algunos pasan pero la estructura es válida -> se guarda SOLO
      el subconjunto que pasó (código verificado-correcto, sin arrastrar las
      aserciones equivocadas que fallaron — cero contaminación).

    Se conservan hasta MAX_EXAMPLES_PER_MODULE ejemplos por módulo, rankeados por
    _example_score (cobertura y, en empate, nº de tests). Un ejemplo nuevo:
    actualiza su slot si su código es idéntico a uno existente, ocupa un cupo
    libre, o desplaza al peor existente solo si lo supera. Así no se regresa
    entre corridas (que en SLMs varían) ni se pierde diversidad por sobrescribir
    siempre el mismo id."""
    if not compiles or metrics is None:
        return False
    # estructura mínima: salida limpia, empieza con import pytest, clase Test única
    if not (
        quality["is_clean_output"]
        and quality["starts_with_import_pytest"]
        and quality["has_expected_test_class"]
    ):
        return False
    if metrics["tests_passed"] == 0 or metrics["tests_errors"] > 0:
        return False

    full = _should_learn(compiles, metrics, quality)
    if full:
        code_to_save = tests_code
        kept = metrics["tests_total"]
        suffix = ""
    else:
        if not passing_tests:
            return False
        code_to_save = _filter_to_passing_tests(tests_code, passing_tests)
        ok, _ = _check_compiles(code_to_save)
        if not ok:
            return False
        kept = len(passing_tests)
        suffix = " (subconjunto de tests que pasaron)"
        if kept == 0:
            return False

    coverage = metrics["line_coverage"]
    if not full and source_code:
        # Cobertura REAL del subconjunto guardado: la suite completa cubría más
        # líneas gracias a los tests que luego se descartaron por fallar, así que
        # usar esa cifra inflaría el score del ejemplo parcial. Se re-ejecuta
        # pytest solo sobre lo que se conserva; si esa corrida falla, se mantiene
        # la cobertura de la suite como aproximación.
        subset_metrics, _, _ = _run_pytest(source_code, code_to_save, module_name)
        if subset_metrics:
            coverage = subset_metrics["line_coverage"]
    score = _example_score(coverage, kept)
    code_to_save = code_to_save.strip()

    examples = rag.get_learned_examples(module_name)
    used_ids = {ex["id"] for ex in examples}

    twin = next((ex for ex in examples if _example_code(ex["text"]) == code_to_save), None)
    if twin is not None:
        # 1) Mismo código que un slot existente -> actualizar ese slot (sin
        #    duplicar) y solo si el nuevo no baja su score medido.
        prev_score, _ = _parse_example_meta(twin["text"])
        if score < prev_score:
            return False
        target_id = twin["id"]
    elif len(examples) < MAX_EXAMPLES_PER_MODULE:
        # 2) Hay cupo libre.
        target_id = _next_slot_id(module_name, used_ids)
    else:
        # 3) Lleno: desplazar al peor solo si el nuevo lo supera.
        worst = min(examples, key=lambda ex: _parse_example_meta(ex["text"])[0])
        worst_score, _ = _parse_example_meta(worst["text"])
        if score <= worst_score:
            return False
        rag.remove_document(worst["id"])
        used_ids.discard(worst["id"])
        target_id = _next_slot_id(module_name, used_ids)

    text = (
        f"[meta score={score} kept={kept}] "
        f"Ejemplo verificado de tests pytest para el módulo '{module_name}'{suffix} "
        f"(funciones: {', '.join(functions_found) or 'sin funciones detectadas'}). "
        f"{kept} test(s) verificados que pasan, "
        f"{coverage}% de cobertura de línea. "
        f"Código de prueba:\n{code_to_save}"
    )
    rag.add_learned_document(target_id, text)

    # Solo en el caso completo las advertencias dejan de aplicar.
    if full:
        rag.clear_warnings(module_name)
    return True


_SMELL_GUIDANCE = {
    "assertion_roulette": (
        "no incluyas más de un assert por test sin un mensaje descriptivo en cada "
        "uno (segundo argumento de assert) — regla OR-6"
    ),
    "empty_test": (
        "no generes métodos test_* cuyo cuerpo sea solo `pass` o `pytest.skip()` — "
        "cada test debe verificar comportamiento real del código bajo prueba (OR-7)"
    ),
    "generic_name": (
        "los nombres de test deben seguir test_<función>_<escenario_descriptivo>, "
        "nunca test_<función> a secas sin describir el escenario (OR-4)"
    ),
    "empty_raises": (
        "dentro de un bloque `with pytest.raises(...)` SIEMPRE invoca la "
        "función/método bajo prueba (p.ej. `funcion(args)`); no basta con asignar "
        "variables: si no se llama a nada, no se lanza la excepción y el test "
        "falla con 'DID NOT RAISE' sin probar el código"
    ),
}


def _learn_from_failure(
    rag: RAGService,
    module_name: str,
    quality: dict,
    compiles: bool,
    metrics: dict | None,
    failures: dict[str, str] | None = None,
    degraded: bool = False,
) -> bool:
    """Si la generación compiló y corrió, pero quedó incompleta de una forma
    reconocible (cobertura de funciones faltante pese al retry de OR-8, test
    smells, o tests que fallaron por una aserción con el valor esperado
    incorrecto), guarda advertencias en RAG para que futuras generaciones de
    este mismo módulo reciban ese contexto. Son documentos de "lección", no
    ejemplos de código (a diferencia de _learn_from_result).

    No se aprende de corridas degradadas: en ese caso el código son stubs
    pytest.skip() generados por el respaldo, no salida real del modelo, así
    que sus "smells" y huecos de cobertura son artefactos, no lecciones."""
    if not compiles or metrics is None or degraded:
        return False

    learned_something = False

    missing = [fn for fn, count in quality["tests_per_function"].items() if count == 0]
    if missing:
        doc_id = f"learned_warning_coverage_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, el "
            f"modelo no incluyó ningún test para estas funciones detectadas por el AST "
            f"parser: {', '.join(missing)}. Al generar tests para este módulo, incluye un "
            f"método test_<función>_<escenario> para CADA función listada en "
            f"'FUNCIONES DETECTADAS POR AST PARSER', sin omitir ninguna (regla OR-8)."
        )
        rag.add_warning(doc_id, text)
        learned_something = True

    smells = quality.get("smells_detected") or []
    if smells:
        guidance = "; ".join(_SMELL_GUIDANCE.get(s, s) for s in smells)
        doc_id = f"learned_warning_smells_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, los "
            f"tests generados tuvieron estos test smells: {', '.join(smells)}. Al generar "
            f"tests para este módulo, recuerda que {guidance}."
        )
        rag.add_warning(doc_id, text)
        learned_something = True

    # Lección de aserciones: la señal semántica más rica. El modelo fijó el valor
    # esperado equivocado y pytest lo demostró al ejecutar. Se la devolvemos para
    # que reconsidere, advirtiéndole de NO copiar el valor obtenido a ciegas (eso
    # produciría un test tautológico que oculta el bug en vez de detectarlo).
    if failures:
        items = list(failures.items())[:4]
        detalle = "\n".join(f"  - {name}: {detail}" for name, detail in items)
        doc_id = f"learned_warning_assertions_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, estos "
            f"tests fallaron al ejecutarse porque su aserción no se cumplió:\n{detalle}\n"
            f"Revisa el comportamiento REAL de cada función (su código y su docstring) antes "
            f"de fijar el valor esperado en el assert. No copies a ciegas el valor que la "
            f"función devolvió solo para que el test pase: si ese valor no es el correcto "
            f"según el contrato de la función, el test sería tautológico y ocultaría un bug."
        )
        rag.add_warning(doc_id, text)
        learned_something = True

    return learned_something


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
    t_total = time.time()

    print(f"[AST] Analizando funciones...")
    functions = extract_functions(source_code)
    functions_found = [fn["nombre"] for fn in functions]
    print(f"[AST] Detectadas: {functions_found}")
    for fn in functions:
        if fn["excepciones"]:
            print(f"[AST]   → {fn['nombre']}() lanza: {', '.join(fn['excepciones'])}")

    print(f"[RAG] Buscando fragmentos relevantes...")
    warnings = rag.get_warnings(module_name)
    patterns = rag.query(source_code + " " + prompt, n_results=3)
    # Las advertencias del módulo (por clave exacta) van primero y son
    # aditivas: no le quitan cupo a los patrones recuperados por similitud.
    context_fragments = warnings + patterns
    print(f"[RAG] {len(warnings)} advertencia(s) + {len(patterns)} patrón(es)")

    context_block  = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."
    functions_block = _build_functions_block(functions)
    classes_block   = _build_classes_block(module_name, extract_classes(source_code))
    module_pascal   = "".join(w.capitalize() for w in module_name.split("_"))

    user_message = _build_user_message(
        module_name, module_pascal, context_block, functions_block, classes_block, prompt, source_code
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
    tests_code = _repair_generated_tests(
        tests_code, module_name, extract_classes(source_code), functions_found
    )

    print(f"[COMPILE] Verificando sintaxis...")
    compiles, compile_error = _check_compiles(tests_code)
    print(f"[COMPILE] {'OK' if compiles else 'ERROR — ' + str(compile_error)}")

    if not compiles:
        print(f"[RETRY] Compilación fallida, reintentando con error en contexto...")
        retry_messages = messages + [
            {"role": "assistant", "content": raw_response},
            {"role": "user", "content": (
                f"El código generado tiene un error de sintaxis Python:\n{compile_error}\n\n"
                f"Corrige únicamente ese error y devuelve el código completo corregido. "
                f"Solo código Python válido, sin explicaciones ni markdown."
            )},
        ]
        t0 = time.time()
        raw_retry = chat(model=model, messages=retry_messages)
        print(f"[RETRY] Respuesta en {time.time() - t0:.1f}s")
        tests_retry, explanation_retry = _extract_code(raw_retry)
        tests_retry = _repair_generated_tests(
            tests_retry, module_name, extract_classes(source_code), functions_found
        )
        compiles_retry, compile_error_retry = _check_compiles(tests_retry)
        if compiles_retry:
            print(f"[RETRY] Éxito — código corregido compila")
            tests_code    = tests_retry
            explanation   = explanation_retry or explanation
            compiles      = True
            compile_error = None
        else:
            print(f"[RETRY] Fallido de nuevo — manteniendo resultado inicial")

    if compiles:
        missing_functions = _missing_function_coverage(tests_code, functions_found)
        if missing_functions:
            print(f"[RETRY] Faltan tests para: {', '.join(missing_functions)} — reintentando...")
            retry_messages = messages + [
                {"role": "assistant", "content": tests_code},
                _build_coverage_retry_message(missing_functions),
            ]
            t0 = time.time()
            raw_retry2 = chat(model=model, messages=retry_messages)
            print(f"[RETRY] Respuesta en {time.time() - t0:.1f}s")
            tests_retry2, explanation_retry2 = _extract_code(raw_retry2)
            tests_retry2 = _repair_generated_tests(
                tests_retry2, module_name, extract_classes(source_code), functions_found
            )
            compiles_retry2, compile_error_retry2 = _check_compiles(tests_retry2)
            if compiles_retry2:
                print(f"[RETRY] Éxito — código corregido compila")
                tests_code  = tests_retry2
                explanation = explanation_retry2 or explanation
            else:
                print(f"[RETRY] Fallido de nuevo — manteniendo resultado anterior")

    degraded = False
    if not compiles:
        print(f"[DEGRADE] Generando suite de respaldo (rescate de métodos + skips)...")
        classes_detected = extract_classes(source_code)
        degraded_code = _build_degraded_tests(
            tests_code, module_name, module_pascal, functions_found, classes_detected, compile_error
        )
        degraded_compiles, degraded_compile_error = _check_compiles(degraded_code)
        if degraded_compiles:
            tests_code = degraded_code
            compiles = True
            compile_error = None
            degraded = True
            print(f"[DEGRADE] Suite de respaldo compila — se ejecutará con métricas degradadas")
        else:
            print(f"[DEGRADE] Suite de respaldo tampoco compiló: {degraded_compile_error}")

    metrics = None
    passing_tests: set[str] = set()
    failures: dict[str, str] = {}
    if compiles and run_pytest:
        print(f"[PYTEST] Ejecutando evaluación...")
        metrics, passing_tests, failures = _run_pytest(source_code, tests_code, module_name)
        if metrics:
            print(f"[PYTEST] {metrics['tests_passed']}/{metrics['tests_total']} pasan | "
                  f"cobertura: {metrics['line_coverage']}%")
    elif not run_pytest:
        print(f"[PYTEST] Omitido por configuración")

    print(f"[QUALITY] Analizando calidad...")
    quality = analyze_quality(tests_code, functions_found, f"Test{module_pascal}")
    print(f"[QUALITY] Given/When/Then: {quality['has_given_when_then']} | "
          f"smells: {quality['smells_detected']}")

    learned = _learn_from_result(
        rag, module_name, functions_found, tests_code, compiles, metrics, quality,
        passing_tests, source_code,
    )
    if learned:
        print(f"[RAG] Ejemplo verificado (completo o parcial) guardado como 'learned_{module_name}'")
    # Las advertencias se evalúan aparte: aplican aunque se haya aprendido un
    # subconjunto parcial (p.ej. cobertura incompleta o smells).
    if _learn_from_failure(rag, module_name, quality, compiles, metrics, failures, degraded):
        print(f"[RAG] Advertencia(s) guardada(s) para '{module_name}'")

    log_result(model, module_name, metrics, quality, functions_found, context_fragments, warnings, compiles, learned, degraded, time.time() - t_total)

    # Opción A + persistencia: registra los fallos de esta corrida en un store
    # aparte del RAG y recupera los acumulados del módulo (incluye runs previos).
    potential_bugs = record_and_annotate(module_name, _build_potential_bugs(failures, degraded, tests_code, functions_found))

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
        "learned":         learned,
        "degraded":        degraded,
        "potential_bugs":  potential_bugs,
    }
