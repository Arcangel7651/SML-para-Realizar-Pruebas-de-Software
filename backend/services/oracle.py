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
    "de una función, decides si un test que falló detectó un bug del código o si "
    "el test fijó un valor esperado equivocado. Respondes con UNA sola palabra: "
    "BUG_CODIGO o FALSO_POSITIVO."
)


def triage_failure(fn_name: str | None, spec: str, failure_detail: str, model: str) -> str:
    """Clasifica un test que falló comparándolo contra la spec (docstring).

    BUG_CODIGO    → el valor que el test esperaba concuerda con el docstring, así
                    que el código está mal: el test cazó un bug. Se conserva.
    FALSO_POSITIVO→ el valor esperado del test contradice el docstring, así que el
                    test está mal.
    sin_oraculo   → no hay docstring (o el juez no respondió): no se afirma nada.
    """
    if not (spec or "").strip():
        return NO_ORACLE

    user_prompt = (
        f"FUNCIÓN: {fn_name or 'desconocida'}\n"
        f"COMPORTAMIENTO ESPERADO (docstring): {spec.strip()}\n"
        f"TEST QUE FALLÓ: {failure_detail}\n\n"
        "El test esperaba un valor y el código devolvió otro.\n"
        "- Si el valor que el test esperaba CONCUERDA con el docstring, el código "
        "está mal: responde BUG_CODIGO.\n"
        "- Si el valor que el test esperaba CONTRADICE el docstring, el test está "
        "mal: responde FALSO_POSITIVO.\n"
        "Responde solo una palabra."
    )
    try:
        verdict = chat(model, [
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]).strip().upper()
    except Exception as e:
        print(f"[ORACLE] Juez no disponible ({e}); fallo sin clasificar.")
        return NO_ORACLE

    if "BUG_CODIGO" in verdict or verdict.startswith("BUG"):
        return BUG
    if "FALSO" in verdict or "FALSE" in verdict:
        return FALSE_POSITIVE
    return NO_ORACLE


def triage_failures(failures: dict[str, str], functions: list[dict], model: str) -> dict[str, str]:
    """Veredicto del oráculo por cada test que falló: {nombre_test: veredicto}.
    Solo invoca al juez (otra llamada al SLM) cuando la función tiene docstring,
    así el costo se acota a los fallos que sí tienen oráculo contra el cual juzgar."""
    spec_by_fn = {fn["nombre"]: fn.get("docstring", "") for fn in functions}
    fn_names = [fn["nombre"] for fn in functions]
    verdicts: dict[str, str] = {}
    for test_name, detail in failures.items():
        fn = guess_function(test_name, fn_names)
        verdicts[test_name] = triage_failure(fn, spec_by_fn.get(fn, ""), detail, model)
    return verdicts
