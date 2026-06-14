import os
import csv
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "results_log.csv")

FIELDNAMES = [
    # ── Identidad de la corrida ──────────────────────────────────────
    "timestamp", "model", "module",
    # ── Resultado de la generación ───────────────────────────────────
    "compiles", "degraded", "learned",
    # ── Ejecución de los tests (pytest) ──────────────────────────────
    "tests_total", "tests_passed", "tests_failed", "tests_skipped", "tests_errors", "pass_rate",
    # ── Cobertura del código bajo prueba ─────────────────────────────
    "line_coverage", "branch_coverage",
    # ── Cobertura a nivel de función (¿cuántas funciones del AST
    #    recibieron al menos un test? — regla OR-8) ──────────────────
    "funcs_total", "funcs_covered", "func_coverage_pct",
    # ── Calidad estructural (reglas OR / test smells del SMS) ────────
    "given_when_then", "smells_count", "smells",
    # ── Tiempo total de la generación ────────────────────────────────
    "time_s",
]


def _cell(value):
    """None -> celda vacía; el resto tal cual (csv lo serializa)."""
    return "" if value is None else value


def log_result(
    model: str,
    module: str,
    metrics: dict | None,
    quality: dict | None,
    functions_found: list[str] | None,
    compiles: bool,
    learned: bool,
    degraded: bool,
    time_s: float,
) -> None:
    """Anexa una fila por generación a results_log.csv (en data/, montado como
    volumen, así que persiste en el host). Pensado para armar la tabla de
    comparación de modelos del SMS sin copiar métricas a mano: junta en una sola
    fila el resultado de pytest, la cobertura (línea, rama y a nivel de función)
    y la calidad estructural (Given/When/Then y test smells). Nunca interrumpe la
    generación: si algo falla al escribir, se ignora."""
    m = metrics or {}
    q = quality or {}

    # Cobertura a nivel de función: de todas las funciones que detectó el AST,
    # cuántas recibieron al menos un test (señal directa de la regla OR-8).
    tests_per_function = q.get("tests_per_function") or {}
    funcs_total = len(functions_found or [])
    funcs_covered = sum(1 for count in tests_per_function.values() if count > 0)
    func_coverage_pct = (
        round(funcs_covered / funcs_total * 100, 1) if funcs_total else ""
    )
    smells = q.get("smells_detected") or []

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "module": module,
        "compiles": compiles,
        "degraded": degraded,
        "learned": learned,
        "tests_total": _cell(m.get("tests_total", 0)),
        "tests_passed": _cell(m.get("tests_passed", 0)),
        "tests_failed": _cell(m.get("tests_failed", 0)),
        "tests_skipped": _cell(m.get("tests_skipped", 0)),
        "tests_errors": _cell(m.get("tests_errors", 0)),
        "pass_rate": _cell(m.get("pass_rate")),
        "line_coverage": _cell(m.get("line_coverage")),
        "branch_coverage": _cell(m.get("branch_coverage")),
        "funcs_total": funcs_total,
        "funcs_covered": funcs_covered,
        "func_coverage_pct": func_coverage_pct,
        "given_when_then": _cell(q.get("has_given_when_then")),
        "smells_count": len(smells),
        "smells": ";".join(smells),
        "time_s": round(time_s, 1),
    }
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        file_exists = os.path.exists(LOG_PATH)
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[LOG] No se pudo registrar el resultado: {e}")


# ── Lectura para la UI ───────────────────────────────────────────────
_BOOL_COLS = {"compiles", "degraded", "learned", "given_when_then"}
_INT_COLS = {
    "tests_total", "tests_passed", "tests_failed", "tests_skipped",
    "tests_errors", "funcs_total", "funcs_covered", "smells_count",
}
_FLOAT_COLS = {"pass_rate", "line_coverage", "branch_coverage", "func_coverage_pct", "time_s"}


def _coerce(col: str, value):
    """Convierte la celda de texto del CSV al tipo que espera la UI (número,
    booleano o cadena). Celda vacía -> None."""
    if value is None or value == "":
        return None
    if col in _BOOL_COLS:
        return value == "True"
    if col in _INT_COLS:
        try:
            return int(value)
        except ValueError:
            return None
    if col in _FLOAT_COLS:
        try:
            return float(value)
        except ValueError:
            return None
    return value


def read_results() -> list[dict]:
    """Lee el log completo como lista de filas tipadas (números y booleanos ya
    convertidos), para servirlo a la UI. Si el archivo aún no existe, devuelve
    lista vacía. Nunca lanza: ante un CSV corrupto, devuelve lo que pudo leer."""
    if not os.path.exists(LOG_PATH):
        return []
    rows = []
    try:
        with open(LOG_PATH, newline="", encoding="utf-8") as f:
            for raw in csv.DictReader(f):
                rows.append({col: _coerce(col, raw.get(col)) for col in FIELDNAMES})
    except Exception as e:
        print(f"[LOG] No se pudo leer el log: {e}")
    return rows
