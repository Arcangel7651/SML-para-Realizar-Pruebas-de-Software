"""Ablación de las lecciones globales (memoria semántica).

Mide si inyectar las lecciones globales mejora la generación en módulos FRESCOS
(cold-start), que es donde aplican: un módulo con advertencia propia las excluye,
así que ON y OFF serían idénticos y no habría nada que medir.

Validez del experimento:
- Cada corrida usa un NOMBRE DE MÓDULO ÚNICO (p.ej. `conversor_temperatura_ablon1`),
  así siempre es un módulo fresco (sin advertencia ni ejemplo previo). Esto evita
  el confound de que el estado mute entre repeticiones (un módulo que falla
  adquiere su advertencia y quedaría excluido de la lección en la corrida
  siguiente). No hace falta reiniciar el servidor ni resetear su memoria.
- El orden ON/OFF se baraja (semilla fija) para repartir las condiciones en el
  tiempo y no confundir el efecto con la deriva del servidor.
- Cada fila queda en results_log.csv etiquetada por `rag_global_lessons`
  (>0 = ON, 0 = OFF). El análisis se hace agrupando por esa columna.

Los stores JSON se respaldan al inicio y se restauran al final, para que los
módulos sintéticos no dejen basura en warnings/lessons/bugs.

Uso:
    python ablacion_lecciones.py            # corre el experimento completo
    REPS=1 python ablacion_lecciones.py     # prueba de humo (1 repetición)
"""

import os
import csv
import glob
import time
import random
import shutil
import statistics as st
from collections import defaultdict

import requests

# ── Configuración ────────────────────────────────────────────────────────
BASE_URL = os.getenv("ABLATION_URL", "http://localhost:8000")
MODEL    = os.getenv("ABLATION_MODEL", "qwen2.5-coder:3b")
REPS     = int(os.getenv("REPS", "5"))          # repeticiones por (módulo, condición)
TIMEOUT  = int(os.getenv("ABLATION_TIMEOUT", "1800"))  # s por corrida (CPU lenta)
SEED     = 42

# Módulos FRESCOS (sin advertencia propia) y con docstring, para que la lección
# global se inyecte de verdad. Tres perfiles: funciones puras, clase y módulo chico.
MODULES = ["conversor_temperatura", "cuenta_bancaria_correguida", "validador_edad"]

HERE        = os.path.dirname(os.path.abspath(__file__))
CODES_DIR   = os.path.join(HERE, "..", "codigos-prueba")
DATA_DIR    = os.path.join(HERE, "data")
STORE_FILES = [
    "rag_store.json", "learned_store.json", "warnings_store.json",
    "lessons_store.json", "bugs_store.json",
]


def _read_source(module: str) -> str:
    with open(os.path.join(CODES_DIR, f"{module}.py"), encoding="utf-8") as f:
        return f.read()


def _snapshot() -> str:
    snap = os.path.join(HERE, ".ablation_snapshot")
    os.makedirs(snap, exist_ok=True)
    for name in STORE_FILES:
        src = os.path.join(DATA_DIR, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(snap, name))
    return snap


def _restore(snap: str):
    for name in STORE_FILES:
        src = os.path.join(snap, name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DATA_DIR, name))


def _run(module: str, synth_name: str, source: str, use_lessons: bool) -> dict | None:
    files = {"file": (f"{synth_name}.py", source, "text/x-python")}
    data = {
        "prompt": "",
        "model": MODEL,
        "run_pytest": "true",
        "use_global_lessons": "true" if use_lessons else "false",
    }
    t0 = time.time()
    resp = requests.post(f"{BASE_URL}/generate-tests", files=files, data=data, timeout=TIMEOUT)
    resp.raise_for_status()
    r = resp.json()
    m = r.get("metrics") or {}
    q = r.get("quality") or {}
    return {
        "module": module,
        "cond": "ON" if use_lessons else "OFF",
        "lessons_injected": sum("LECCIÓN GENERAL" in f for f in (r.get("context_used") or [])),
        "pass_rate": m.get("pass_rate"),
        "line_coverage": m.get("line_coverage"),
        "smells": len(q.get("smells_detected") or []),
        "compiles": r.get("compiles"),
        "degraded": r.get("degraded"),
        "elapsed": round(time.time() - t0, 1),
    }


def _build_jobs() -> list[tuple]:
    jobs = []
    for module in MODULES:
        for rep in range(1, REPS + 1):
            for cond in (True, False):
                tag = "on" if cond else "off"
                jobs.append((module, f"{module}_abl{tag}{rep}", cond))
    random.Random(SEED).shuffle(jobs)
    return jobs


def _summary(results: list[dict]):
    by = defaultdict(lambda: defaultdict(list))
    for r in results:
        for k in ("pass_rate", "line_coverage", "smells", "elapsed"):
            if r[k] is not None:
                by[r["cond"]][k].append(r[k])

    print("\n" + "=" * 64)
    print("RESUMEN DE LA ABLACIÓN  (lecciones globales: ON vs OFF)")
    print("=" * 64)
    print(f"{'cond':4}  n   pass_rate  line_cov  smells   time_s")
    for cond in ("ON", "OFF"):
        d = by[cond]
        n = len(d["smells"])
        if not n:
            continue
        mean = lambda k: st.mean(d[k]) if d[k] else float("nan")
        print(f"{cond:4} {n:2}   {mean('pass_rate'):7.1f}  {mean('line_coverage'):7.1f}  "
              f"{mean('smells'):5.2f}  {mean('elapsed'):7.0f}")
    print("=" * 64)
    print("Detalle completo en data/results_log.csv (columna rag_global_lessons).")


def main():
    print(f"Ablación lecciones globales | modelo={MODEL} | reps={REPS} | módulos={MODULES}")
    jobs = _build_jobs()
    total = len(jobs)
    est_h = total * 8 / 60  # ~8 min/corrida en CPU
    print(f"{total} corridas (~{est_h:.1f} h estimadas). Ctrl+C para abortar.\n")

    snap = _snapshot()
    results = []
    try:
        for i, (module, synth, cond) in enumerate(jobs, 1):
            tag = "ON " if cond else "OFF"
            print(f"[{i:2}/{total}] {tag} {module:28} ", end="", flush=True)
            try:
                r = _run(module, synth, _read_source(module), cond)
                results.append(r)
                print(f"pass={r['pass_rate']} cov={r['line_coverage']} "
                      f"smells={r['smells']} lecc={r['lessons_injected']} ({r['elapsed']}s)")
            except Exception as e:
                print(f"ERROR: {e}")
    except KeyboardInterrupt:
        print("\nAbortado por el usuario; resumen parcial:")
    finally:
        _restore(snap)
        print("\nStores restaurados (módulos sintéticos eliminados de los JSON).")
        if results:
            _summary(results)


if __name__ == "__main__":
    main()
