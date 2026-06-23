"""Oráculo de comportamiento esperado.

Usa el docstring de cada función como fuente de verdad INDEPENDIENTE del código,
para clasificar los tests que fallan en 'bug del código' vs 'falso positivo del
test' (LLM-as-judge). Es el mecanismo que rompe el problema del oráculo: sin una
spec externa, el sistema solo puede converger a lo que el código HACE; con ella,
puede juzgar si el código cumple lo que DEBERÍA hacer.

Reglas de diseño:
- Sin docstring no hay oráculo: el fallo queda 'sin_oraculo' (modo
  caracterización) y NUNCA se afirma que haya un bug.
- El veredicto es una señal REVISABLE por el humano, no una verdad absoluta: un
  SLM pequeño puede equivocarse al juzgar. Por eso se guarda como `oracle_triage`,
  separado del triaje manual del humano (`triage` en bugs_store).
"""

import re

from infrastructure.ollama_client import chat

BUG = "bug_real"
FALSE_POSITIVE = "falso_positivo"
NO_ORACLE = "sin_oraculo"


def guess_function(test_name: str, functions_found: list[str]) -> str | None:
    """Función bajo prueba a la que apunta un test, según el nombre
    test_<funcion>_<escenario>. Empareja el nombre de función más largo que sea
    prefijo del sufijo, para que p.ej. 'es_par' no eclipse a 'es_par_negativo'
    si ambos existen."""
    if not test_name.startswith("test_"):
        return None
    suffix = test_name[len("test_"):]
    for fn in sorted(functions_found, key=len, reverse=True):
        if suffix == fn or suffix.startswith(fn + "_"):
            return fn
    return None


_JUDGE_SYSTEM = (
    "Eres un árbitro de pruebas de software. Según la especificación (docstring) "
    "de cada función, decides si un test que falló detectó un bug del código o si "
    "el test fijó un valor esperado equivocado. Para cada test respondes con "
    "BUG_CODIGO o FALSO_POSITIVO."
)


def _classify_verdict(verdict: str) -> str:
    """Mapea el texto del juez a una de las constantes del oráculo."""
    verdict = verdict.upper()
    if "BUG_CODIGO" in verdict or verdict.strip().startswith("BUG"):
        return BUG
    if "FALSO" in verdict or "FALSE" in verdict:
        return FALSE_POSITIVE
    return NO_ORACLE


def _build_batch_prompt(judgeable: dict[str, tuple[str | None, str, str]]) -> str:
    """Arma un único prompt con TODOS los fallos juzgables. Cada caso pide un
    veredicto en una línea parseable `<nombre_test> => BUG_CODIGO|FALSO_POSITIVO`,
    para que una sola llamada al juez resuelva todos los fallos de la corrida (en
    vez de una llamada por fallo, costosísimo en CPU)."""
    bloques = []
    for test_name, (fn_name, spec, detail) in judgeable.items():
        bloques.append(
            f"TEST: {test_name}\n"
            f"  FUNCIÓN: {fn_name or 'desconocida'}\n"
            f"  COMPORTAMIENTO ESPERADO (docstring): {spec.strip()}\n"
            f"  FALLO: {detail}"
        )
    casos = "\n\n".join(bloques)
    return (
        "Cada uno de los siguientes tests falló: esperaba un valor y el código "
        "devolvió otro. Para CADA test decide:\n"
        "- Si el valor que el test esperaba CONCUERDA con el docstring, el código "
        "está mal → BUG_CODIGO.\n"
        "- Si el valor que el test esperaba CONTRADICE el docstring, el test está "
        "mal → FALSO_POSITIVO.\n\n"
        f"{casos}\n\n"
        "Responde EXACTAMENTE una línea por test, con este formato y nada más:\n"
        "<nombre_test> => BUG_CODIGO\n"
        "o\n"
        "<nombre_test> => FALSO_POSITIVO"
    )


def _parse_batch_verdicts(response: str, judgeable_names: list[str]) -> dict[str, str]:
    """Lee la respuesta del juez (una línea `<test> => VEREDICTO` por caso) y la
    asocia a cada test juzgable. Empareja por nombre EXACTO en el lado izquierdo
    de `=>` (un token), para que p.ej. 'test_sumar' no capture la línea de
    'test_sumar_negativo'. Lo no emparejado queda como sin_oraculo."""
    verdicts: dict[str, str] = {name: NO_ORACLE for name in judgeable_names}
    name_set = set(judgeable_names)
    for line in response.splitlines():
        if "=>" not in line:
            continue
        left, right = line.split("=>", 1)
        tokens = re.findall(r"test_\w+", left)
        matched = next((t for t in tokens if t in name_set), None)
        if matched:
            verdicts[matched] = _classify_verdict(right)
    return verdicts


def triage_failures(failures: dict[str, str], functions: list[dict], model: str) -> dict[str, str]:
    """Veredicto del oráculo por cada test que falló: {nombre_test: veredicto}.
    Solo se juzgan los fallos cuya función tiene docstring (los demás quedan
    'sin_oraculo' sin gastar inferencia). Todos los fallos juzgables se resuelven
    en UNA sola llamada al SLM (batch), en vez de una por fallo: en CPU cada
    llamada pesa minutos, así que batchear es donde está el mayor ahorro."""
    spec_by_fn = {fn["nombre"]: fn.get("docstring", "") for fn in functions}
    fn_names = [fn["nombre"] for fn in functions]

    verdicts: dict[str, str] = {}
    judgeable: dict[str, tuple[str | None, str, str]] = {}
    for test_name, detail in failures.items():
        fn = guess_function(test_name, fn_names)
        spec = spec_by_fn.get(fn, "")
        if (spec or "").strip():
            judgeable[test_name] = (fn, spec, detail)
        else:
            verdicts[test_name] = NO_ORACLE  # sin docstring: no hay oráculo

    if not judgeable:
        return verdicts

    try:
        response = chat(model, [
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user", "content": _build_batch_prompt(judgeable)},
        ])
    except Exception as e:
        print(f"[ORACLE] Juez no disponible ({e}); fallos sin clasificar.")
        verdicts.update({name: NO_ORACLE for name in judgeable})
        return verdicts

    verdicts.update(_parse_batch_verdicts(response, list(judgeable)))
    return verdicts
