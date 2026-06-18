"""Replay del oráculo sobre fallos ya etiquetados.

El harness de evaluación (evaluar_oraculo.py) necesita que el campo
`oracle_triage` esté poblado para poder compararlo con el triaje humano. Pero
esos veredictos solo se generan dentro del pipeline completo de generación, que
tarda varios minutos por módulo en CPU. Este script corta ese acoplamiento:
toma los posibles bugs YA registrados en data/bugs_store.json (con su `name` y
`detail` de la aserción que falló) y re-ejecuta ÚNICAMENTE al juez del oráculo
contra el docstring de la función correspondiente, sin regenerar tests.

Así se puede medir la calidad del oráculo sobre la verdad de campo existente en
minutos en vez de horas, y re-evaluarlo cada vez que se ajuste su prompt.

El veredicto depende del docstring (la spec): una función sin docstring no tiene
oráculo y el fallo queda 'sin_oraculo' (el oráculo se abstiene, nunca inventa).

Uso:
    python replay_oraculo.py                 # en seco: solo imprime la tabla
    python replay_oraculo.py --write         # además persiste oracle_triage
    python replay_oraculo.py --model codellama:7b-instruct
    python replay_oraculo.py --solo-etiquetados   # solo bugs con triaje humano
"""

import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

from services.ast_parser import extract_functions
from services.oracle import triage_failures

STORE_PATH = os.path.join(os.path.dirname(__file__), "data", "bugs_store.json")
# Los nombres de módulo del store corresponden 1:1 con codigos-prueba/<modulo>.py
SOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "codigos-prueba")

DEFAULT_MODEL = "qwen2.5-coder:3b"


def _load_store() -> dict:
    with open(STORE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_store(data: dict) -> None:
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _source_for(module: str) -> str | None:
    path = os.path.join(SOURCES_DIR, f"{module}.py")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def replay(store: dict, model: str, solo_etiquetados: bool) -> dict[tuple, str]:
    """Devuelve {(modulo, name, detail): veredicto} re-ejecutando el oráculo.
    No escribe nada: la persistencia la decide main() según --write."""
    verdicts: dict[tuple, str] = {}

    for module, bugs in store.items():
        if solo_etiquetados:
            bugs = [b for b in bugs if b.get("triage") in ("bug_real", "falso_positivo")]
        if not bugs:
            continue

        source = _source_for(module)
        if source is None:
            print(f"[SKIP] {module}: no se encontró codigos-prueba/{module}.py")
            continue

        functions = extract_functions(source)
        # triage_failures espera {test_name: detail}; reusamos el mismo juez que
        # corre en el pipeline, así el replay mide EXACTAMENTE al oráculo real.
        failures = {b["name"]: b["detail"] for b in bugs}
        print(f"[ORACLE] {module}: juzgando {len(failures)} fallo(s) con {model}...")
        mod_verdicts = triage_failures(failures, functions, model)

        for b in bugs:
            verdicts[(module, b["name"], b["detail"])] = mod_verdicts.get(b["name"], "sin_oraculo")

    return verdicts


def _apply(store: dict, verdicts: dict[tuple, str]) -> int:
    """Escribe oracle_triage en las entradas correspondientes. Devuelve cuántas
    actualizó."""
    n = 0
    for module, bugs in store.items():
        for b in bugs:
            key = (module, b["name"], b["detail"])
            if key in verdicts:
                b["oracle_triage"] = verdicts[key]
                n += 1
    return n


def _print_table(store: dict, verdicts: dict[tuple, str]) -> None:
    print()
    print("=" * 78)
    print(" REPLAY DEL ORÁCULO — veredicto re-ejecutado vs triaje humano")
    print("=" * 78)
    print(f"  {'módulo':22} {'oráculo':14} {'humano':14} {'¿coincide?':10} test")
    agree = decided = 0
    for module, bugs in store.items():
        for b in bugs:
            key = (module, b["name"], b["detail"])
            if key not in verdicts:
                continue
            oracle = verdicts[key]
            human = b.get("triage")
            if oracle in ("bug_real", "falso_positivo") and human in ("bug_real", "falso_positivo"):
                decided += 1
                match = "sí" if oracle == human else "NO"
                if oracle == human:
                    agree += 1
            elif human in ("bug_real", "falso_positivo"):
                match = "(abst.)"
            else:
                match = "(sin GT)"
            print(f"  {module[:22]:22} {oracle:14} {str(human):14} {match:10} {b['name'][:34]}")
    print()
    if decided:
        print(f"  Coincidencias sobre casos decididos: {agree}/{decided} ({agree/decided*100:.1f}%)")
    print("  (Para precisión/recall/F1 detallados corre: python evaluar_oraculo.py)")


def main():
    ap = argparse.ArgumentParser(description="Re-ejecuta el oráculo sobre bugs ya registrados.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"modelo juez (default {DEFAULT_MODEL})")
    ap.add_argument("--write", action="store_true", help="persiste oracle_triage en bugs_store.json")
    ap.add_argument("--solo-etiquetados", action="store_true",
                    help="solo re-juzga bugs con triaje humano (verdad de campo)")
    args = ap.parse_args()

    store = _load_store()
    verdicts = replay(store, args.model, args.solo_etiquetados)
    _print_table(store, verdicts)

    if args.write:
        n = _apply(store, verdicts)
        _save_store(store)
        print(f"\n[OK] {n} entrada(s) actualizada(s) con oracle_triage en bugs_store.json")
        print("     Ahora corre: python evaluar_oraculo.py")
    else:
        print("\n[SECO] No se escribió nada. Añade --write para persistir los veredictos.")


if __name__ == "__main__":
    main()
