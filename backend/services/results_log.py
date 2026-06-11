import os
import csv
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "results_log.csv")

FIELDNAMES = [
    "timestamp", "model", "module",
    "tests_total", "tests_passed", "tests_failed", "tests_skipped", "tests_errors",
    "line_coverage", "branch_coverage", "pass_rate",
    "time_s", "compiles", "learned", "degraded",
]


def _cell(value):
    """None -> celda vacía; el resto tal cual (csv lo serializa)."""
    return "" if value is None else value


def log_result(
    model: str,
    module: str,
    metrics: dict | None,
    compiles: bool,
    learned: bool,
    degraded: bool,
    time_s: float,
) -> None:
    """Anexa una fila por generación a results_log.csv (en data/, montado como
    volumen, así que persiste en el host). Pensado para armar la tabla de
    comparación de modelos sin copiar métricas a mano. Nunca interrumpe la
    generación: si algo falla al escribir, se ignora."""
    m = metrics or {}
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "module": module,
        "tests_total": _cell(m.get("tests_total", 0)),
        "tests_passed": _cell(m.get("tests_passed", 0)),
        "tests_failed": _cell(m.get("tests_failed", 0)),
        "tests_skipped": _cell(m.get("tests_skipped", 0)),
        "tests_errors": _cell(m.get("tests_errors", 0)),
        "line_coverage": _cell(m.get("line_coverage")),
        "branch_coverage": _cell(m.get("branch_coverage")),
        "pass_rate": _cell(m.get("pass_rate")),
        "time_s": round(time_s, 1),
        "compiles": compiles,
        "learned": learned,
        "degraded": degraded,
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
