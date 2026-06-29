import os
import csv
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "results_log.csv")

FIELDNAMES = [
    # ── Identidad de la corrida ──────────────────────────────────────
    "timestamp", "model", "module",
    # ── Resultado de la generación ───────────────────────────────────
    "compiles", "degraded", "learned",
    # ── Contexto RAG inyectado al prompt (la variable que explica la
    #    convergencia: nº de fragmentos, advertencias del módulo y si se
    #    recuperó el ejemplo aprendido propio del módulo) ──────────────
    "rag_fragments", "rag_warnings", "rag_used_learned", "rag_global_lessons",
    # ── Condición de la ablación: ¿se PIDIÓ usar las lecciones globales en esta
    #    generación? (flag use_global_lessons). Distinto de rag_global_lessons,
    #    que cuenta cuántas se INYECTARON de hecho: en ON pueden ser 0 si ninguna
    #    estaba promovida o si el módulo ya las cubría con su advertencia. ─────
    "global_lessons_enabled",
    # ── Ejecución de los tests (pytest) ──────────────────────────────
    "tests_total", "tests_passed", "tests_failed", "tests_skipped", "tests_errors", "pass_rate",
    # ── Cobertura del código bajo prueba ─────────────────────────────
    "line_coverage", "branch_coverage",
    # ── Cobertura a nivel de función (¿cuántas funciones del AST
    #    recibieron al menos un test? — regla OR-8) ──────────────────
    "funcs_total", "funcs_covered", "func_coverage_pct",
    # ── Calidad estructural (reglas OR / test smells del SMS) ────────
    "given_when_then", "smells_count", "smells",
    # ── Tiempo: total de la corrida y la fracción gastada en el SLM
    #    (generación + reintentos + oráculo). El resto (time_s - llm_s) es
    #    CPU (AST, pytest, cobertura, análisis) y no se acelera con GPU; la
    #    separación permite estimar cuánto ahorraría una GPU. ──────────────
    "time_s", "llm_s",
]


def _cell(value):
    """None -> celda vacía; el resto tal cual (csv lo serializa)."""
    return "" if value is None else value


def _rag_signals(module: str, context_fragments: list[str] | None, warnings: list[str] | None):
    """Señales compactas del contexto RAG usado en la generación: nº de
    fragmentos, nº de advertencias del módulo y si entre los fragmentos venía
    el ejemplo aprendido propio del módulo (texto 'Ejemplo verificado ... para
    el módulo <module>'). Detecta por contenido, no por id, así que es robusto
    al esquema de ids (legacy o por slots)."""
    frags = context_fragments or []
    warns = warnings or []
    marker = f"para el módulo '{module}'"
    used_learned = any("Ejemplo verificado" in f and marker in f for f in frags)
    # Lecciones globales (memoria semántica): se reconocen por su marcador de texto
    # "LECCIÓN GENERAL", para medir si su presencia mejora las métricas (ablación).
    global_lessons = sum("LECCIÓN GENERAL" in f for f in frags)
    return len(frags), len(warns), used_learned, global_lessons


def log_result(
    model: str,
    module: str,
    metrics: dict | None,
    quality: dict | None,
    functions_found: list[str] | None,
    context_fragments: list[str] | None,
    warnings: list[str] | None,
    compiles: bool,
    learned: bool,
    degraded: bool,
    time_s: float,
    global_lessons_enabled: bool = True,
    llm_time_s: float | None = None,
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
    rag_fragments, rag_warnings, rag_used_learned, rag_global_lessons = _rag_signals(module, context_fragments, warnings)

    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "module": module,
        "compiles": compiles,
        "degraded": degraded,
        "learned": learned,
        "rag_fragments": rag_fragments,
        "rag_warnings": rag_warnings,
        "rag_used_learned": rag_used_learned,
        "rag_global_lessons": rag_global_lessons,
        "global_lessons_enabled": global_lessons_enabled,
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
        "llm_s": round(llm_time_s, 1) if llm_time_s is not None else "",
    }
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        file_exists = os.path.exists(LOG_PATH)
        # Si el CSV existe con una cabecera vieja (p. ej. antes de añadir una
        # columna nueva), lo migramos: reescribimos con FIELDNAMES actual y las
        # celdas que falten en las filas históricas quedan vacías. Así anexar no
        # desalinea columnas cuando el esquema crece.
        if file_exists:
            _migrate_header()
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"[LOG] No se pudo registrar el resultado: {e}")


def _migrate_header() -> None:
    """Si la cabecera del CSV no coincide con FIELDNAMES, reescribe el archivo
    con el esquema actual conservando las filas existentes (las columnas nuevas
    quedan vacías y se descartan columnas que ya no existen). No-op si ya
    coincide. Nunca lanza hacia afuera."""
    try:
        with open(LOG_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames == FIELDNAMES:
                return
            old_rows = list(reader)
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            for r in old_rows:
                writer.writerow({col: r.get(col, "") for col in FIELDNAMES})
    except Exception as e:
        print(f"[LOG] No se pudo migrar la cabecera del log: {e}")


# ── Lectura para la UI ───────────────────────────────────────────────
_BOOL_COLS = {"compiles", "degraded", "learned", "given_when_then", "rag_used_learned", "global_lessons_enabled"}
_INT_COLS = {
    "tests_total", "tests_passed", "tests_failed", "tests_skipped",
    "tests_errors", "funcs_total", "funcs_covered", "smells_count",
    "rag_fragments", "rag_warnings", "rag_global_lessons",
}
_FLOAT_COLS = {"pass_rate", "line_coverage", "branch_coverage", "func_coverage_pct", "time_s", "llm_s"}


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
