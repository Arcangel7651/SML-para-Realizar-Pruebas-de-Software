#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_ablation_eval.py — Ablación PAREADA cold-start de las lecciones globales
(memoria semántica) sobre el dataset de 200 archivos de GitHub.

Mide CAUSALMENTE si inyectar las lecciones globales mejora la generación en
archivos FRESCOS. Cada archivo se mide en AMBAS condiciones (ON/OFF) → diseño
within-subject (pareado) → cada archivo es su propio control.

Aislamiento del singleton (clave de validez): cada corrida sube el archivo con
un NOMBRE DE MÓDULO SINTÉTICO ÚNICO (`<archivo>_abl{on|off}{rep}`). Como la
memoria episódica (ejemplos/advertencias) se recupera por nombre exacto de
módulo, un nombre nunca-visto = generación fresca garantizada; lo ÚNICO que
comparten las corridas es el tally de lecciones globales = el tratamiento. Así
el problema del singleton se disuelve por construcción (no se resetea nada).

Reusa la maquinaria de `services.ablation` (_snapshot/_restore/SEED) y drena el
MISMO pipeline que la API vía `generate_tests` (regla 4): no duplica lógica de
dominio y cada corrida ya anexa su fila a `results_log.csv` (regla 7).

Protocolo: resultados/ablacion-lecciones-globales-200.md

Salida (en <dataset>\\resultados\\ablacion\\):
    por_corrida.csv — 1 fila por (archivo, rep, condición); en vivo.
    pareado.csv     — por (archivo, rep): ON, OFF y delta = ON - OFF de cada métrica.
    resumen.csv     — agregados ON vs OFF separando correctos / incorrectos
                      (+ Wilcoxon signed-rank sobre los deltas si scipy está).

Resistente a cortes: con --resume retoma saltando las (archivo, rep, cond) ya hechas.

Requiere: Ollama corriendo con el modelo pedido.

Uso:
    python dataset/run_ablation_eval.py --limit 10 --runs 3   # PILOTO (60 corridas)
    python dataset/run_ablation_eval.py --runs 3 --resume     # completo (1200 corridas)
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import statistics
import sys
import time
from pathlib import Path

# --- Hacer importable el backend (mismo cwd que uvicorn) ------------------- #
REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

DEFAULT_DATASET = Path(r"C:\Users\angel\Documents\PRACTICAS\Codigos Prueba")
DEFAULT_MODEL = "qwen2.5-coder:3b"
DEFAULT_RUNS = 3

PER_RUN_FIELDS = [
    "archivo", "label", "run_idx", "cond", "synth_name", "ok", "error",
    "compiles", "degraded", "lessons_injected",
    "tests_total", "tests_passed", "tests_failed", "tests_skipped", "tests_errors",
    "pass_rate", "line_coverage", "branch_coverage",
    "funcs_total", "funcs_covered", "func_coverage_pct",
    "given_when_then", "smells_count", "potential_bugs", "bug_detected",
    "time_s",
]

# Métricas que se comparan ON vs OFF (numéricas, mayor = mejor salvo smells).
PAIRED_METRICS = [
    "pass_rate", "line_coverage", "branch_coverage", "func_coverage_pct",
    "smells_count", "bug_detected",
]


def fmt_eta(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m{s:02d}s"


def collect_files(dataset: Path, limit: int | None) -> list[tuple[Path, str]]:
    """Devuelve [(path, label)] para correctos e incorrectos."""
    items: list[tuple[Path, str]] = []
    for sub, label in (("correctos", "correcto"), ("incorrectos", "incorrecto")):
        folder = dataset / sub
        if not folder.exists():
            print(f"[AVISO] no existe {folder}")
            continue
        files = sorted(folder.glob("*.py"))
        if limit is not None:
            files = files[:limit]
        items.extend((p, label) for p in files)
    return items


def build_jobs(files: list[tuple[Path, str]], reps: int, seed: int) -> list[dict]:
    """(archivo, rep, condición) con nombre sintético único, barajado con semilla
    fija para repartir ON/OFF en el tiempo. Mismo patrón que services.ablation."""
    jobs: list[dict] = []
    for path, label in files:
        module = path.stem
        for rep in range(1, reps + 1):
            for cond in (True, False):
                tag = "on" if cond else "off"
                jobs.append({
                    "path": path, "label": label, "module": module,
                    "rep": rep, "cond": cond,
                    "synth": f"{module}_abl{tag}{rep}",
                })
    random.Random(seed).shuffle(jobs)
    return jobs


def load_done(per_run_csv: Path) -> set[tuple[str, int, str]]:
    """(archivo, rep, cond) ya registrados, para --resume."""
    done: set[tuple[str, int, str]] = set()
    if not per_run_csv.exists():
        return done
    with per_run_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                done.add((row["archivo"], int(row["run_idx"]), row["cond"]))
            except (KeyError, ValueError):
                continue
    return done


def run_once(generate_tests, rag_service, source: str, synth: str,
             model: str, cond: bool) -> dict:
    """Una generación fresca (nombre sintético). Devuelve métricas planas; nunca lanza."""
    t0 = time.perf_counter()
    out = {k: "" for k in PER_RUN_FIELDS}
    try:
        res = generate_tests(
            source, "", model, rag_service, synth, True, cond
        )
        m = res.get("metrics") or {}
        q = res.get("quality") or {}
        pbugs = res.get("potential_bugs") or []
        ctx = res.get("context_used") or []
        tpf = q.get("tests_per_function") or {}
        funcs_covered = sum(1 for c in tpf.values() if c > 0)
        funcs_total = len(tpf)
        tests_failed = m.get("tests_failed", 0) or 0
        tests_errors = m.get("tests_errors", 0) or 0
        out.update({
            "ok": True, "error": "",
            "compiles": res.get("compiles"),
            "degraded": res.get("degraded"),
            "lessons_injected": sum("LECCIÓN GENERAL" in f for f in ctx),
            "tests_total": m.get("tests_total", 0),
            "tests_passed": m.get("tests_passed", 0),
            "tests_failed": tests_failed,
            "tests_skipped": m.get("tests_skipped", 0),
            "tests_errors": tests_errors,
            "pass_rate": m.get("pass_rate"),
            "line_coverage": m.get("line_coverage"),
            "branch_coverage": m.get("branch_coverage"),
            "funcs_total": funcs_total,
            "funcs_covered": funcs_covered,
            "func_coverage_pct": round(funcs_covered / funcs_total * 100, 1) if funcs_total else "",
            "given_when_then": q.get("has_given_when_then"),
            "smells_count": len(q.get("smells_detected") or []),
            "potential_bugs": len(pbugs),
            "bug_detected": bool(tests_failed > 0 or tests_errors > 0 or pbugs),
        })
    except Exception as e:  # noqa: BLE001 — una corrida que falla no aborta el lote
        out.update({"ok": False, "error": str(e)[:300]})
    out["time_s"] = round(time.perf_counter() - t0, 1)
    return out


# --------------------------------------------------------------------------- #
# Agregación pareada
# --------------------------------------------------------------------------- #
def _num(v):
    """Convierte celda a float; bool/strings de bool a 1.0/0.0; '' -> None."""
    if v in ("", None):
        return None
    if v in (True, "True"):
        return 1.0
    if v in (False, "False"):
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _mean(values: list) -> float | str:
    nums = [v for v in (_num(x) for x in values) if v is not None]
    return round(statistics.mean(nums), 3) if nums else ""


def _wilcoxon(deltas: list[float]):
    """(stat, p) con scipy si está; (None, None) si no. Ignora deltas == 0."""
    nz = [d for d in deltas if d != 0]
    if len(nz) < 1:
        return None, None
    try:
        from scipy.stats import wilcoxon
        stat, p = wilcoxon(nz)
        return round(float(stat), 3), round(float(p), 5)
    except Exception:  # noqa: BLE001 — scipy ausente o muestra degenerada
        return None, None


def aggregate(per_run_csv: Path, out_dir: Path) -> None:
    if not per_run_csv.exists():
        print("[agg] no hay por_corrida.csv todavía")
        return
    with per_run_csv.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("ok") == "True"]

    # ---- pareado: emparejar ON y OFF por (archivo, rep) ----
    by_pair: dict[tuple[str, str], dict[str, dict]] = {}
    label_of: dict[str, str] = {}
    for r in rows:
        key = (r["archivo"], r["run_idx"])
        by_pair.setdefault(key, {})[r["cond"]] = r
        label_of[r["archivo"]] = r["label"]

    paired_fields = ["archivo", "label", "run_idx"] + [
        f"{m}_{c}" for m in PAIRED_METRICS for c in ("on", "off", "delta")
    ]
    paired_rows = []
    # deltas[label][metric] = [delta, ...] para el resumen/Wilcoxon
    deltas: dict[str, dict[str, list[float]]] = {
        lab: {m: [] for m in PAIRED_METRICS} for lab in ("correcto", "incorrecto")
    }
    for (archivo, run_idx), pair in sorted(by_pair.items()):
        if "ON" not in pair or "OFF" not in pair:
            continue  # par incompleto (corte a mitad); se ignora hasta completarse
        label = label_of[archivo]
        row = {"archivo": archivo, "label": label, "run_idx": run_idx}
        for m in PAIRED_METRICS:
            on, off = _num(pair["ON"][m]), _num(pair["OFF"][m])
            row[f"{m}_on"] = on if on is not None else ""
            row[f"{m}_off"] = off if off is not None else ""
            if on is not None and off is not None:
                d = round(on - off, 3)
                row[f"{m}_delta"] = d
                if label in deltas:
                    deltas[label][m].append(d)
            else:
                row[f"{m}_delta"] = ""
        paired_rows.append(row)

    with (out_dir / "pareado.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=paired_fields)
        w.writeheader()
        w.writerows(paired_rows)

    # ---- resumen ON vs OFF por clase, con Wilcoxon sobre los deltas ----
    summary_fields = [
        "label", "metric", "n_pares", "mean_on", "mean_off", "mean_delta",
        "pct_on_gana", "wilcoxon_stat", "p_value",
    ]
    summary_rows = []
    for label in ("correcto", "incorrecto"):
        lab_rows = [r for r in rows if r["label"] == label]
        for m in PAIRED_METRICS:
            # bug_detected solo tiene sentido en incorrectos; smells/cobertura en
            # ambos pero el foco de correctos es calidad.
            if m == "bug_detected" and label == "correcto":
                continue
            ds = deltas[label][m]
            if not ds:
                continue
            on_vals = [r[m] for r in lab_rows if r["cond"] == "ON"]
            off_vals = [r[m] for r in lab_rows if r["cond"] == "OFF"]
            # smells: menor es mejor, así que "gana" si delta < 0.
            better = (lambda d: d < 0) if m == "smells_count" else (lambda d: d > 0)
            wins = sum(1 for d in ds if better(d))
            stat, p = _wilcoxon(ds)
            summary_rows.append({
                "label": label, "metric": m, "n_pares": len(ds),
                "mean_on": _mean(on_vals), "mean_off": _mean(off_vals),
                "mean_delta": round(statistics.mean(ds), 3),
                "pct_on_gana": round(wins / len(ds) * 100, 1),
                "wilcoxon_stat": stat if stat is not None else "",
                "p_value": p if p is not None else "",
            })

    with (out_dir / "resumen.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary_fields)
        w.writeheader()
        w.writerows(summary_rows)

    print("\n== RESUMEN ON vs OFF (pareado) ==")
    print(f"  {'clase':11s} {'métrica':18s} {'n':>4s} {'ON':>8s} {'OFF':>8s} "
          f"{'Δ':>8s} {'%ON':>6s} {'p':>8s}")
    for r in summary_rows:
        p = r["p_value"] if r["p_value"] != "" else "n/a"
        print(f"  {r['label']:11s} {r['metric']:18s} {r['n_pares']:>4d} "
              f"{str(r['mean_on']):>8s} {str(r['mean_off']):>8s} "
              f"{str(r['mean_delta']):>8s} {str(r['pct_on_gana']):>6s} {str(p):>8s}")
    print(f"\n  -> {out_dir / 'pareado.csv'}")
    print(f"  -> {out_dir / 'resumen.csv'}")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    ap.add_argument("--out", type=Path, default=None, help="def: <dataset>\\resultados\\ablacion")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="reps por (archivo×condición)")
    ap.add_argument("--limit", type=int, default=None, help="máx archivos por clase (piloto)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--only-aggregate", action="store_true", help="solo recalcular CSV agregados")
    args = ap.parse_args()

    out_dir = args.out or (args.dataset / "resultados" / "ablacion")
    out_dir.mkdir(parents=True, exist_ok=True)
    per_run_csv = out_dir / "por_corrida.csv"

    if args.only_aggregate:
        aggregate(per_run_csv, out_dir)
        return 0

    # cwd = backend (como uvicorn) para que stores y rutas relativas resuelvan igual.
    os.chdir(BACKEND)
    from services.test_generator import generate_tests
    from services.rag_service import rag_service
    from services.ablation import _snapshot, _restore
    from infrastructure.ollama_client import list_models

    # Precheck de Ollama / modelo.
    try:
        models = list_models()
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Ollama no responde ({e}). Levántalo antes de correr.")
        return 2
    if args.model not in models:
        print(f"[ERROR] modelo '{args.model}' no está en Ollama. Disponibles: {models}")
        print(f"        Haz:  ollama pull {args.model}")
        return 2

    # Precondición: ¿las lecciones están promovidas? Si no, ON ≡ OFF y hay que saberlo.
    promoted = rag_service.get_global_lessons()
    print(f"\n== LECCIONES GLOBALES PROMOVIDAS: {len(promoted)} ==")
    if not promoted:
        print("  [AVISO] no hay lecciones promovidas: ON ≡ OFF. El experimento no medirá efecto.")
    for txt in promoted:
        print(f"  - {txt[:80]}...")

    files = collect_files(args.dataset, args.limit)
    if not files:
        print("[ERROR] no se encontraron archivos en el dataset.")
        return 2

    jobs = build_jobs(files, args.runs, args.seed)
    done = load_done(per_run_csv) if args.resume else set()

    new_file = not per_run_csv.exists()
    fout = per_run_csv.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fout, fieldnames=PER_RUN_FIELDS)
    if new_file:
        writer.writeheader()
        fout.flush()

    pending = [j for j in jobs if (j["path"].name, j["rep"], "ON" if j["cond"] else "OFF") not in done]
    print(f"\n== ABLACIÓN PAREADA ==")
    print(f"  dataset : {args.dataset}")
    print(f"  archivos: {len(files)}  x  runs: {args.runs}  x  2 cond = {len(jobs)} corridas")
    print(f"  modelo  : {args.model}")
    if args.resume:
        print(f"  resume  : {len(done)} ya hechas, faltan {len(pending)}")

    # Snapshot de stores: los nombres sintéticos no deben dejar basura ni ensuciar
    # el aprendizaje real. Se restaura SIEMPRE al terminar (o ante corte).
    _snapshot()
    completed = 0
    t_start = time.perf_counter()
    try:
        for j in pending:
            source = j["path"].read_text(encoding="utf-8")
            row = run_once(generate_tests, rag_service, source, j["synth"],
                           args.model, j["cond"])
            row["archivo"] = j["path"].name
            row["label"] = j["label"]
            row["run_idx"] = j["rep"]
            row["cond"] = "ON" if j["cond"] else "OFF"
            row["synth_name"] = j["synth"]
            writer.writerow(row)
            fout.flush()
            completed += 1
            elapsed = time.perf_counter() - t_start
            avg = elapsed / completed
            remaining = (len(pending) - completed) * avg
            status = "ok" if row["ok"] else f"FALLÓ: {row['error'][:50]}"
            tag = row["cond"]
            print(f"  [{completed}/{len(pending)}] {j['path'].name} r{j['rep']} {tag:3s} "
                  f"{row['time_s']}s {status} | ETA {fmt_eta(remaining)}")
    finally:
        fout.close()
        _restore()
        print("  [stores restaurados]")

    print("\n== Agregando ==")
    aggregate(per_run_csv, out_dir)
    print(f"\n  telemetría cruda del pipeline: {BACKEND / 'data' / 'results_log.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
