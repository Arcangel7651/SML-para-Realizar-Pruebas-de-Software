"""Harness de evaluación del oráculo.

Cruza el veredicto automático del oráculo (`oracle_triage`, generado por
services/oracle.py contra el docstring de cada función) con el triaje manual
del humano (`triage`, la verdad de campo registrada por el revisor) que viven
juntos en data/bugs_store.json.

El objetivo es responder, con números y no a ojo, tres preguntas:

  1. ¿Sobre cuántos fallos se atreve a opinar el oráculo? (cobertura: cuántos
     deja en 'sin_oraculo' por falta de docstring o porque el juez no respondió).
  2. Cuando opina, ¿acierta? (precisión / recall / F1, clase positiva = bug_real).
  3. ¿En qué casos concretos se equivoca? (lista de desacuerdos para inspección).

No toca el pipeline ni el modelo: solo lee el store y reporta. Se puede correr
las veces que haga falta tras acumular generaciones con el oráculo activo:

    python evaluar_oraculo.py
    python evaluar_oraculo.py --md informe_oraculo.md   # además guarda Markdown
"""

import argparse
import json
import os
import sys
from collections import defaultdict

# En Windows la consola suele venir en cp1252 y los acentos del informe salen
# como mojibake. Forzar UTF-8 en stdout no afecta a otras plataformas.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "bugs_store.json")

BUG = "bug_real"
FALSE_POSITIVE = "falso_positivo"
NO_ORACLE = "sin_oraculo"

# Etiquetas que cuentan como "el oráculo emitió una decisión". 'sin_oraculo' y la
# ausencia de veredicto son abstenciones: no entran a precisión/recall, se
# reportan aparte como cobertura.
DECIDED = {BUG, FALSE_POSITIVE}


def _load_store() -> dict:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] No se pudo leer {STORE_PATH}: {e}")
        return {}


def _iter_labeled(store: dict):
    """Genera (modulo, bug) solo para los bugs con triaje humano (verdad de
    campo). Sin etiqueta humana no hay con qué evaluar al oráculo."""
    for module, bugs in store.items():
        for bug in bugs:
            if bug.get("triage") in (BUG, FALSE_POSITIVE):
                yield module, bug


def _metrics(tp: int, fp: int, fn: int, tn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    if precision and recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = None
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total else None
    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy}


def _fmt(x) -> str:
    return "—" if x is None else f"{x * 100:5.1f}%"


def _confusion(rows: list[dict]) -> dict:
    """Cuenta TP/FP/FN/TN y abstenciones sobre la clase positiva = bug_real.

    - TP: oráculo dijo bug_real  y el humano confirma bug_real.
    - FP: oráculo dijo bug_real  pero el humano dice falso_positivo.
    - TN: oráculo dijo falso_pos y el humano dice falso_positivo.
    - FN: oráculo dijo falso_pos pero el humano dice bug_real.
    - abst_pos / abst_neg: el oráculo se abstuvo (sin_oraculo / sin veredicto)
      sobre un caso que el humano marcó como bug_real / falso_positivo.
    """
    c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0, "abst_pos": 0, "abst_neg": 0}
    for r in rows:
        oracle = r["oracle"]
        human = r["human"]
        if oracle not in DECIDED:
            c["abst_pos" if human == BUG else "abst_neg"] += 1
        elif oracle == BUG and human == BUG:
            c["tp"] += 1
        elif oracle == BUG and human == FALSE_POSITIVE:
            c["fp"] += 1
        elif oracle == FALSE_POSITIVE and human == FALSE_POSITIVE:
            c["tn"] += 1
        elif oracle == FALSE_POSITIVE and human == BUG:
            c["fn"] += 1
    return c


def evaluar(store: dict) -> list[str]:
    rows = []
    for module, bug in _iter_labeled(store):
        rows.append({
            "module": module,
            "name": bug.get("name", ""),
            "oracle": bug.get("oracle_triage"),  # None si nunca se evaluó
            "human": bug["triage"],
        })

    out: list[str] = []
    def line(s=""):
        out.append(s)

    line("=" * 64)
    line(" EVALUACIÓN DEL ORÁCULO — oracle_triage vs triaje humano")
    line("=" * 64)
    line()

    if not rows:
        line("No hay posibles bugs con triaje humano en el store.")
        line("Triagea algunos bugs (campo `triage`) para tener verdad de campo.")
        return out

    decided = [r for r in rows if r["oracle"] in DECIDED]
    abstained = [r for r in rows if r["oracle"] not in DECIDED]

    line(f"Posibles bugs con triaje humano (verdad de campo): {len(rows)}")
    line(f"  · bug_real:        {sum(1 for r in rows if r['human'] == BUG)}")
    line(f"  · falso_positivo:  {sum(1 for r in rows if r['human'] == FALSE_POSITIVE)}")
    line()
    line(f"Veredictos del oráculo sobre esos bugs: {len(decided)}/{len(rows)} "
         f"({_fmt(len(decided) / len(rows))} de cobertura)")
    line(f"  · abstenciones (sin_oraculo / sin veredicto): {len(abstained)}")
    line()

    if not decided:
        line("El oráculo aún no ha emitido NINGÚN veredicto sobre estos bugs.")
        line("Causa probable: estos bugs se registraron antes de activar el")
        line("oráculo. Vuelve a generar tests para los módulos buggy con el")
        line("oráculo encendido y corre este script de nuevo: ahí ya habrá")
        line("`oracle_triage` que comparar contra el triaje humano.")
        return out

    # ── Métricas globales (solo sobre casos decididos) ──────────────────
    c = _confusion(rows)
    m = _metrics(c["tp"], c["fp"], c["fn"], c["tn"])

    line("Matriz de confusión (clase positiva = bug_real; solo casos decididos)")
    line("                       humano: bug_real   humano: falso_positivo")
    line(f"  oráculo: bug_real         TP = {c['tp']:<6}        FP = {c['fp']}")
    line(f"  oráculo: falso_positivo   FN = {c['fn']:<6}        TN = {c['tn']}")
    if c["abst_pos"] or c["abst_neg"]:
        line(f"  oráculo: (abstención)     {c['abst_pos']:<11}        {c['abst_neg']}")
    line()
    line(f"  Precisión: {_fmt(m['precision'])}   (de lo que llamó bug_real, cuánto lo era)")
    line(f"  Recall:    {_fmt(m['recall'])}   (de los bugs reales, cuántos cazó)")
    line(f"  F1:        {_fmt(m['f1'])}")
    line(f"  Accuracy:  {_fmt(m['accuracy'])}   (sobre {c['tp']+c['fp']+c['fn']+c['tn']} casos decididos)")
    line()

    # ── Desglose por módulo ─────────────────────────────────────────────
    by_mod: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_mod[r["module"]].append(r)

    line("Por módulo (D = decididos, A = abstenciones):")
    line(f"  {'módulo':24} {'D':>3} {'A':>3} {'TP':>3} {'FP':>3} {'FN':>3} {'TN':>3}  {'P':>6} {'R':>6}")
    for module in sorted(by_mod):
        mr = by_mod[module]
        mc = _confusion(mr)
        mm = _metrics(mc["tp"], mc["fp"], mc["fn"], mc["tn"])
        d = mc["tp"] + mc["fp"] + mc["fn"] + mc["tn"]
        a = mc["abst_pos"] + mc["abst_neg"]
        line(f"  {module[:24]:24} {d:>3} {a:>3} {mc['tp']:>3} {mc['fp']:>3} "
             f"{mc['fn']:>3} {mc['tn']:>3}  {_fmt(mm['precision']):>6} {_fmt(mm['recall']):>6}")
    line()

    # ── Desacuerdos (oráculo ≠ humano, solo casos decididos) ────────────
    disagreements = [r for r in decided if r["oracle"] != r["human"]]
    line(f"Desacuerdos del oráculo (oráculo ≠ humano): {len(disagreements)}")
    for r in disagreements:
        kind = "FALSO POSITIVO del oráculo" if r["oracle"] == BUG else "BUG NO CAZADO por el oráculo"
        line(f"  [{kind}] {r['module']} :: {r['name']}")
        line(f"      oráculo={r['oracle']}  humano={r['human']}")

    return out


def main():
    ap = argparse.ArgumentParser(description="Evalúa el oráculo contra el triaje humano.")
    ap.add_argument("--md", metavar="ARCHIVO", help="además, guarda el informe en Markdown")
    args = ap.parse_args()

    store = _load_store()
    report = evaluar(store)
    text = "\n".join(report)
    print(text)

    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("```\n" + text + "\n```\n")
        print(f"\n[OK] Informe guardado en {args.md}")


if __name__ == "__main__":
    main()
