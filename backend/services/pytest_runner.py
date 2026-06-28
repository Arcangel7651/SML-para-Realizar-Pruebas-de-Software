"""Ejecución de la suite generada bajo pytest+coverage y parseo de su salida.
Convierte el stdout de pytest en métricas (tests, pass-rate, cobertura de línea
y rama), el conjunto de tests que pasaron, y el detalle de cada aserción que
falló. También deriva de esos fallos los "posibles bugs" presentables al humano.
Es la capa de "qué pasó al correr los tests"."""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from services.quality_analyzer import find_empty_raises_tests


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


def run_pytest(source_code: str, tests_code: str, module_name: str) -> tuple[dict | None, set[str], dict[str, str]]:
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


def build_potential_bugs(
    failures: dict[str, str], degraded: bool, tests_code: str, functions_found: list[str],
    oracle_triage: dict[str, str] | None = None,
) -> list[dict]:
    """Opción A + oráculo: tests que compilaron y se ejecutaron pero FALLARON, con
    su detalle de aserción (esperado vs obtenido), presentados al humano como
    'posible bug detectado o aserción incorrecta'. Un fallo significa una de dos
    cosas: (a) el código tiene un bug que el test cazó, o (b) el modelo fijó un
    valor esperado equivocado. El ORÁCULO (docstring) intenta decidir cuál de
    forma automática y se adjunta como `oracle_triage` (bug_real / falso_positivo
    / sin_oraculo); es una señal revisable, no sustituye el triaje humano.

    Se excluyen los fallos de tests MALFORMADOS (un `pytest.raises` que nunca
    invoca la función → falla con 'DID NOT RAISE' aunque el código sea correcto):
    el roto es el test, no el código, así que no es un posible bug (reduce falsos
    positivos). No se incluyen tampoco en corridas degradadas: ahí el código son
    stubs del respaldo, no salida real del modelo."""
    if degraded or not failures:
        return []
    malformed = find_empty_raises_tests(tests_code, functions_found)
    oracle_triage = oracle_triage or {}
    return [
        {"name": name, "detail": detail, "oracle_triage": oracle_triage.get(name)}
        for name, detail in failures.items()
        if name not in malformed
    ]
