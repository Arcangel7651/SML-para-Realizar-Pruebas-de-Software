"""Orquestador de la ablación de lecciones globales, expuesto vía streaming.

Mide si inyectar las lecciones globales (memoria semántica) mejora la generación
en módulos FRESCOS (cold-start), que es donde aplican. Reusa generate_tests; cada
corrida usa un NOMBRE DE MÓDULO ÚNICO para garantizar que sea fresca (sin
advertencia ni ejemplo previo) y que el estado no se contamine entre repeticiones,
sin necesidad de reiniciar el servidor. Ver protocolo en
resultados/ablacion-lecciones-globales.md y problema 10.

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


def _build_jobs(modules: list[str], reps: int) -> list[tuple[str, str, bool]]:
    """Lista de (módulo_base, nombre_sintético_único, use_lessons), barajada con
    semilla fija para repartir las condiciones ON/OFF en el tiempo."""
    jobs = []
    for module in modules:
        for rep in range(1, reps + 1):
            for cond in (True, False):
                tag = "on" if cond else "off"
                jobs.append((module, f"{module}_abl{tag}{rep}", cond))
    random.Random(SEED).shuffle(jobs)
    return jobs


def _summary(results: list[dict]) -> dict:
    by = defaultdict(lambda: defaultdict(list))
    for r in results:
        for k in ("pass_rate", "line_coverage", "smells", "elapsed"):
            if r.get(k) is not None:
                by[r["cond"]][k].append(r[k])

    def stats(cond: str) -> dict:
        d = by[cond]
        mean = lambda k: round(st.mean(d[k]), 2) if d[k] else None
        return {
            "n": len(d["smells"]),
            "pass_rate": mean("pass_rate"),
            "line_coverage": mean("line_coverage"),
            "smells": mean("smells"),
            "elapsed": mean("elapsed"),
        }

    return {"ON": stats("ON"), "OFF": stats("OFF")}


def run_ablation(sources: dict[str, str], model: str, reps: int):
    """Generador de eventos de la ablación. `sources` = {módulo_base: código}."""
    modules = list(sources.keys())
    jobs = _build_jobs(modules, reps)
    total = len(jobs)

    yield {
        "type": "start",
        "total": total,
        "modules": modules,
        "model": model,
        "reps": reps,
        "est_minutes": round(total * 8),  # ~8 min/corrida en CPU
    }

    _snapshot()
    results: list[dict] = []
    try:
        for i, (module, synth, cond) in enumerate(jobs, 1):
            t0 = time.time()
            try:
                out = generate_tests(
                    sources[module], "", model, rag_service,
                    module_name=synth, run_pytest=True, use_global_lessons=cond,
                )
                m = out.get("metrics") or {}
                q = out.get("quality") or {}
                r = {
                    "module": module,
                    "cond": "ON" if cond else "OFF",
                    "lessons_injected": sum(
                        "LECCIÓN GENERAL" in f for f in (out.get("context_used") or [])
                    ),
                    "pass_rate": m.get("pass_rate"),
                    "line_coverage": m.get("line_coverage"),
                    "smells": len(q.get("smells_detected") or []),
                    "compiles": out.get("compiles"),
                    "degraded": out.get("degraded"),
                    "elapsed": round(time.time() - t0, 1),
                }
                results.append(r)
                yield {"type": "run", "i": i, "total": total, **r}
            except Exception as e:
                yield {
                    "type": "run_error", "i": i, "total": total,
                    "module": module, "cond": "ON" if cond else "OFF",
                    "message": str(e),
                }
    finally:
        _restore()

    yield {"type": "done", "summary": _summary(results), "completed": len(results), "total": total}
