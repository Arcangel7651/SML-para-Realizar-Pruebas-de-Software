import json
import os
from datetime import datetime

# Registro de posibles bugs por módulo, SEPARADO del RAG. El RAG solo guarda
# ejemplos verificados (no debe aprender aserciones que fallan ni confirmar
# bugs); este store, en cambio, conserva la señal para el humano y persiste
# entre runs, así un bug detectado en una generación fresca no se pierde cuando
# el sistema converge a la suite que lo evita.
STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "bugs_store.json")


def _load() -> dict:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def record_bugs(module: str, bugs: list[dict]) -> list[dict]:
    """Acumula los posibles bugs de un módulo (dedup por nombre+detalle), con
    marcas de primera/última vez vistos y cuántas veces. Devuelve la lista
    acumulada del módulo. Nunca interrumpe la generación: ante un error,
    devuelve lo recibido."""
    try:
        data = _load()
        index = {(b["name"], b["detail"]): b for b in data.get(module, [])}
        now = datetime.now().isoformat(timespec="seconds")
        for bug in bugs:
            key = (bug["name"], bug["detail"])
            if key in index:
                index[key]["last_seen"] = now
                index[key]["count"] = index[key].get("count", 1) + 1
            else:
                index[key] = {
                    "name": bug["name"],
                    "detail": bug["detail"],
                    "first_seen": now,
                    "last_seen": now,
                    "count": 1,
                }
        merged = list(index.values())
        data[module] = merged
        _save(data)
        return merged
    except Exception as e:
        print(f"[BUGS] No se pudo registrar: {e}")
        return list(bugs)


def record_and_annotate(module: str, current_bugs: list[dict]) -> list[dict]:
    """Registra los bugs de la corrida actual y devuelve la lista ACUMULADA del
    módulo (incluye runs anteriores), marcando cada uno con `seen_now` según si
    se reprodujo en esta corrida o solo viene del historial. Esto resuelve que
    la señal de la Opción A sea transitoria: el bug sigue visible aunque el run
    actual haya convergido a la suite que lo evita."""
    current_keys = {(b["name"], b["detail"]) for b in current_bugs}
    merged = record_bugs(module, current_bugs)
    return [
        {**b, "seen_now": (b["name"], b["detail"]) in current_keys}
        for b in merged
    ]


def get_bugs(module: str) -> list[dict]:
    return _load().get(module, [])


def all_bugs() -> dict:
    return _load()


# Clasificación manual del humano, SOLO para análisis de datos (precisión/recall).
# No la lee el pipeline de generación: no influye en el modelo ni en el RAG.
TRIAGE_VALUES = (None, "bug_real", "falso_positivo")


def set_triage(module: str, name: str, detail: str, triage) -> bool:
    """Marca un posible bug como 'bug_real' o 'falso_positivo' (o None para
    limpiar). Es una anotación privada del humano para analizar resultados;
    se persiste en bugs_store.json y se conserva entre runs (record_bugs no la
    sobrescribe). Devuelve True si encontró la entrada."""
    if triage not in TRIAGE_VALUES:
        return False
    try:
        data = _load()
        for bug in data.get(module, []):
            if bug["name"] == name and bug["detail"] == detail:
                if triage is None:
                    bug.pop("triage", None)
                else:
                    bug["triage"] = triage
                _save(data)
                return True
        return False
    except Exception as e:
        print(f"[BUGS] No se pudo clasificar: {e}")
        return False
