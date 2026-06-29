"""Orquestador de la ablación de lecciones globales, expuesto vía streaming.

Mide si inyectar las lecciones globales (memoria semántica) mejora la generación
en módulos FRESCOS (cold-start), que es donde aplican. Reusa generate_tests; cada
corrida usa un NOMBRE DE MÓDULO ÚNICO para garantizar que sea fresca (sin
advertencia ni ejemplo previo) y que el estado no se contamine entre repeticiones,
sin necesidad de reiniciar el servidor. Ver protocolo en
resultados/ablacion-lecciones-globales.md y problema 10.

Los módulos se etiquetan como 'correcto' o 'incorrecto' (dataset de 200): así el
resumen separa ambas clases y, en los incorrectos, mide bug_detected_rate (¿la
generación CAZÓ el bug inyectado?), que es la señal clave del SMS. Cada corrida
expone también el código generado y el contexto RAG inyectado, para descarga.

run_ablation() es un generador que produce eventos (dict) para que el endpoint
los serialice como NDJSON y el frontend muestre el progreso en vivo.
"""

import os
import time
import random
import shutil
import statistics as st
from collections import defaultdict

from services.rag_service import rag_service
from services.test_generator import generate_tests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
SNAPSHOT_DIR = os.path.join(DATA_DIR, ".ablation_snapshot")
STORE_FILES = [
    "rag_store.json", "learned_store.json", "warnings_store.json",
    "lessons_store.json", "bugs_store.json",
]
SEED = 42


def _snapshot():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    for name in STORE_FILES:
        src = os.path.join(DATA_DIR, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(SNAPSHOT_DIR, name))


def _restore():
    """Restaura los stores y recarga el RAG en memoria, para que los módulos
    sintéticos de la ablación no queden ni en disco ni en el singleton."""
    for name in STORE_FILES:
        src = os.path.join(SNAPSHOT_DIR, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DATA_DIR, name))
    rag_service.reload()


def _conds(conditions: str) -> tuple[bool, ...]:
    """Condiciones a correr según la elección del usuario:
    'both' = ON y OFF (ablación pareada, default) · 'on' = solo ON · 'off' = solo OFF."""
    if conditions == "on":
        return (True,)
    if conditions == "off":
        return (False,)
    return (True, False)


def _build_jobs(modules: list[str], reps: int, conditions: str = "both") -> list[tuple[str, str, bool]]:
    """Lista de (módulo_base, nombre_sintético_único, use_lessons), barajada con
    semilla fija para repartir las condiciones ON/OFF en el tiempo."""
    jobs = []
    for module in modules:
        for rep in range(1, reps + 1):
            for cond in _conds(conditions):
                tag = "on" if cond else "off"
                jobs.append((module, f"{module}_abl{tag}{rep}", cond))
    random.Random(SEED).shuffle(jobs)
    return jobs


def _stats(rs: list[dict]) -> dict:
    """Agregados de un grupo de corridas (una clase × condición)."""
    def mean(k):
        vals = [r[k] for r in rs if r.get(k) is not None]
        return round(st.mean(vals), 2) if vals else None

    n = len(rs)
    bugs = sum(1 for r in rs if r.get("bug_detected"))
    return {
        "n": n,
        "pass_rate": mean("pass_rate"),
        "line_coverage": mean("line_coverage"),
        "func_coverage": mean("func_coverage_pct"),
        "smells": mean("smells"),
        # En incorrectos: % de corridas que cazaron el bug (mayor = mejor).
        # En correctos: % de falsos positivos (tests que fallan sobre código
        # correcto), donde menor = mejor.
        "bug_detected_rate": round(bugs / n * 100, 1) if n else None,
        "elapsed": mean("elapsed"),
    }


def _summary(results: list[dict]) -> dict:
    """Resumen ON vs OFF SEPARADO por clase (correcto / incorrecto)."""
    out: dict[str, dict] = {}
    for label in ("correcto", "incorrecto"):
        out[label] = {
            cond: _stats([r for r in results if r["label"] == label and r["cond"] == cond])
            for cond in ("ON", "OFF")
        }
    return out


def run_ablation(modules: dict[str, dict], model: str, reps: int, conditions: str = "both"):
    """Generador de eventos de la ablación.

    `modules` = {módulo_base: {"code": str, "label": "correcto"|"incorrecto"}}.
    `conditions` = 'both' (ON+OFF pareado) | 'on' (solo ON) | 'off' (solo OFF).
    """
    names = list(modules.keys())
    labels = {name: modules[name].get("label", "correcto") for name in names}
    jobs = _build_jobs(names, reps, conditions)
    total = len(jobs)

    yield {
        "type": "start",
        "total": total,
        "modules": names,
        "model": model,
        "reps": reps,
        "conditions": conditions,
        "n_correctos": sum(1 for l in labels.values() if l == "correcto"),
        "n_incorrectos": sum(1 for l in labels.values() if l == "incorrecto"),
        "est_minutes": round(total * 8),  # ~8 min/corrida en CPU
    }

    _snapshot()
    results: list[dict] = []
    try:
        for i, (module, synth, cond) in enumerate(jobs, 1):
            t0 = time.time()
            try:
                out = generate_tests(
                    modules[module]["code"], "", model, rag_service,
                    module_name=synth, run_pytest=True, use_global_lessons=cond,
                )
                m = out.get("metrics") or {}
                q = out.get("quality") or {}
                ctx = out.get("context_used") or []
                pbugs = out.get("potential_bugs") or []
                tpf = q.get("tests_per_function") or {}
                funcs_total = len(tpf)
                funcs_covered = sum(1 for c in tpf.values() if c > 0)
                tests_failed = m.get("tests_failed", 0) or 0
                tests_errors = m.get("tests_errors", 0) or 0
                r = {
                    "module": module,
                    "label": labels[module],
                    "cond": "ON" if cond else "OFF",
                    "lessons_injected": sum("LECCIÓN GENERAL" in f for f in ctx),
                    "pass_rate": m.get("pass_rate"),
                    "line_coverage": m.get("line_coverage"),
                    "branch_coverage": m.get("branch_coverage"),
                    "func_coverage_pct": (
                        round(funcs_covered / funcs_total * 100, 1) if funcs_total else None
                    ),
                    "smells": len(q.get("smells_detected") or []),
                    "given_when_then": q.get("has_given_when_then"),
                    "tests_total": m.get("tests_total", 0),
                    "tests_passed": m.get("tests_passed", 0),
                    "tests_failed": tests_failed,
                    "tests_errors": tests_errors,
                    "potential_bugs": len(pbugs),
                    # ¿La generación cazó algo? Para incorrectos = detectó el bug;
                    # para correctos = falso positivo.
                    "bug_detected": bool(tests_failed > 0 or tests_errors > 0 or pbugs),
                    "compiles": out.get("compiles"),
                    "degraded": out.get("degraded"),
                    "elapsed": round(time.time() - t0, 1),
                    # Artefactos para descarga (no se renderizan en vivo).
                    "tests": out.get("tests") or "",
                    "context": ctx,
                }
                results.append(r)
                yield {"type": "run", "i": i, "total": total, **r}
            except Exception as e:
                yield {
                    "type": "run_error", "i": i, "total": total,
                    "module": module, "label": labels[module],
                    "cond": "ON" if cond else "OFF", "message": str(e),
                }
    finally:
        _restore()

    yield {"type": "done", "summary": _summary(results), "completed": len(results), "total": total}
