"""Aprendizaje en el RAG a partir del resultado de cada generación. Dos caras:
guardar ejemplos verificados (completos o el subconjunto de tests que pasó,
rankeados por cobertura) para reforzar futuras generaciones del módulo, y
guardar advertencias-lección (cobertura faltante, test smells, aserciones
incorrectas) cuando la generación quedó incompleta de forma reconocible. Es la
memoria del sistema: qué conservar como buen ejemplo y de qué fallo aprender."""

import re

from services.rag_service import RAGService
from services.quality_analyzer import find_vacuous_except_tests
from services.oracle import BUG as ORACLE_BUG
from services.llm_output_parser import check_compiles
from services.pytest_runner import run_pytest
from services.degraded_suite import filter_to_passing_tests


def _should_learn(compiles: bool, metrics: dict | None, quality: dict) -> bool:
    """Solo se aprende de resultados que compilan, pasan pytest sin fallos
    ni errores, cumplen todas las reglas OR del prompt (sin test smells) y
    cubren con al menos un test cada función detectada (OR-8).
    Esto evita contaminar el índice RAG con ejemplos defectuosos o incompletos."""
    if not compiles or metrics is None:
        return False
    if metrics["tests_total"] == 0 or metrics["tests_failed"] > 0 or metrics["tests_errors"] > 0:
        return False
    return (
        quality["is_clean_output"]
        and quality["starts_with_import_pytest"]
        and quality["has_expected_test_class"]
        and quality["has_given_when_then"]
        and not quality["smells_detected"]
        and all(count > 0 for count in quality["tests_per_function"].values())
    )


_LEARNED_COUNT_RE = re.compile(r"(\d+) test\(s\) verificados")
_SCORE_MARKER_RE = re.compile(r"\[meta score=([\d.]+) kept=(\d+)\]")
_COVERAGE_RE = re.compile(r"([\d.]+)% de cobertura")

# Cuántos ejemplos verificados se conservan por módulo. Varias versiones buenas
# (p.ej. una centrada en el camino feliz y otra en excepciones) le dan al RAG
# más diversidad few-shot que un único ejemplo sobrescrito una y otra vez.
MAX_EXAMPLES_PER_MODULE = 3


def _example_score(line_coverage: float, kept: int) -> float:
    """Calidad de un ejemplo verificado, para decidir cuál conservar cuando hay
    más candidatos que cupos. La cobertura manda (un ejemplo que ejercita más
    código enseña más); el nº de tests verificados solo desempata. Se combinan
    en un número monótono: la cobertura como parte entera dominante y los tests
    como fracción acotada (<1), así más cobertura siempre gana y, a igualdad de
    cobertura, gana el que tenga más tests.

    La cobertura recibida es la del código que realmente se guarda (en modo
    parcial, _learn_from_result re-ejecuta pytest sobre el subconjunto antes de
    llamar aquí), no la de la suite completa: así el score no se infla."""
    return round(line_coverage + min(kept, 99) / 100.0, 4)


def _parse_example_meta(text: str) -> tuple[float, int]:
    """(score, kept) de un ejemplo ya guardado. Usa el marcador `[meta ...]`; si
    no está (ejemplos de una versión anterior), lo deduce del texto en prosa."""
    m = _SCORE_MARKER_RE.search(text)
    if m:
        return float(m.group(1)), int(m.group(2))
    kept_m = _LEARNED_COUNT_RE.search(text)
    cov_m = _COVERAGE_RE.search(text)
    kept = int(kept_m.group(1)) if kept_m else 0
    cov = float(cov_m.group(1)) if cov_m else 0.0
    return _example_score(cov, kept), kept


def _example_code(text: str) -> str:
    """Código de prueba dentro del texto de un ejemplo guardado (lo que sigue a
    'Código de prueba:'). Sirve para detectar duplicados exactos entre slots."""
    return text.split("Código de prueba:\n", 1)[-1].strip()


def _next_slot_id(module_name: str, used_ids: set[str]) -> str:
    base = f"learned_{module_name}"
    n = 0
    while f"{base}#{n}" in used_ids:
        n += 1
    return f"{base}#{n}"


def learn_from_result(
    rag: RAGService,
    module_name: str,
    functions_found: list[str],
    tests_code: str,
    compiles: bool,
    metrics: dict | None,
    quality: dict,
    passing_tests: set[str] | None = None,
    source_code: str = "",
) -> bool:
    """Guarda ejemplos verificados en el RAG. Dos modos de contenido:

    - Completo: pasan todos los tests y se cumplen todas las reglas OR -> se
      guarda el archivo entero.
    - Parcial: solo algunos pasan pero la estructura es válida -> se guarda SOLO
      el subconjunto que pasó (código verificado-correcto, sin arrastrar las
      aserciones equivocadas que fallaron — cero contaminación).

    Se conservan hasta MAX_EXAMPLES_PER_MODULE ejemplos por módulo, rankeados por
    _example_score (cobertura y, en empate, nº de tests). Un ejemplo nuevo:
    actualiza su slot si su código es idéntico a uno existente, ocupa un cupo
    libre, o desplaza al peor existente solo si lo supera. Así no se regresa
    entre corridas (que en SLMs varían) ni se pierde diversidad por sobrescribir
    siempre el mismo id."""
    if not compiles or metrics is None:
        return False
    # estructura mínima: salida limpia, empieza con import pytest, clase Test única
    if not (
        quality["is_clean_output"]
        and quality["starts_with_import_pytest"]
        and quality["has_expected_test_class"]
    ):
        return False
    if metrics["tests_passed"] == 0 or metrics["tests_errors"] > 0:
        return False

    full = _should_learn(compiles, metrics, quality)
    if full:
        code_to_save = tests_code
        kept = metrics["tests_total"]
        suffix = ""
    else:
        if not passing_tests:
            return False
        # No aprender tests con assert dentro de except: 'pasan' de forma vacua
        # (la excepción no se lanzó) y perpetuarían el smell (problema 07).
        clean_passing = passing_tests - find_vacuous_except_tests(tests_code)
        if not clean_passing:
            return False
        code_to_save = filter_to_passing_tests(tests_code, clean_passing)
        ok, _ = check_compiles(code_to_save)
        if not ok:
            return False
        kept = len(clean_passing)
        suffix = " (subconjunto de tests que pasaron)"
        if kept == 0:
            return False

    coverage = metrics["line_coverage"]
    if not full and source_code:
        # Cobertura REAL del subconjunto guardado: la suite completa cubría más
        # líneas gracias a los tests que luego se descartaron por fallar, así que
        # usar esa cifra inflaría el score del ejemplo parcial. Se re-ejecuta
        # pytest solo sobre lo que se conserva; si esa corrida falla, se mantiene
        # la cobertura de la suite como aproximación.
        subset_metrics, _, _ = run_pytest(source_code, code_to_save, module_name)
        if subset_metrics:
            coverage = subset_metrics["line_coverage"]
    score = _example_score(coverage, kept)
    code_to_save = code_to_save.strip()

    examples = rag.get_learned_examples(module_name)
    used_ids = {ex["id"] for ex in examples}

    twin = next((ex for ex in examples if _example_code(ex["text"]) == code_to_save), None)
    if twin is not None:
        # 1) Mismo código que un slot existente -> actualizar ese slot (sin
        #    duplicar) y solo si el nuevo no baja su score medido.
        prev_score, _ = _parse_example_meta(twin["text"])
        if score < prev_score:
            return False
        target_id = twin["id"]
    elif len(examples) < MAX_EXAMPLES_PER_MODULE:
        # 2) Hay cupo libre.
        target_id = _next_slot_id(module_name, used_ids)
    else:
        # 3) Lleno: desplazar al peor solo si el nuevo lo supera.
        worst = min(examples, key=lambda ex: _parse_example_meta(ex["text"])[0])
        worst_score, _ = _parse_example_meta(worst["text"])
        if score <= worst_score:
            return False
        rag.remove_document(worst["id"])
        used_ids.discard(worst["id"])
        target_id = _next_slot_id(module_name, used_ids)

    text = (
        f"[meta score={score} kept={kept}] "
        f"Ejemplo verificado de tests pytest para el módulo '{module_name}'{suffix} "
        f"(funciones: {', '.join(functions_found) or 'sin funciones detectadas'}). "
        f"{kept} test(s) verificados que pasan, "
        f"{coverage}% de cobertura de línea. "
        f"Código de prueba:\n{code_to_save}"
    )
    rag.add_learned_document(target_id, text)

    # Solo en el caso completo las advertencias dejan de aplicar.
    if full:
        rag.clear_warnings(module_name)
    return True


_SMELL_GUIDANCE = {
    "assertion_roulette": (
        "no incluyas más de un assert por test sin un mensaje descriptivo en cada "
        "uno (segundo argumento de assert) — regla OR-6"
    ),
    "empty_test": (
        "no generes métodos test_* cuyo cuerpo sea solo `pass` o `pytest.skip()` — "
        "cada test debe verificar comportamiento real del código bajo prueba (OR-7)"
    ),
    "generic_name": (
        "los nombres de test deben seguir test_<función>_<escenario_descriptivo>, "
        "nunca test_<función> a secas sin describir el escenario (OR-4)"
    ),
    "empty_raises": (
        "dentro de un bloque `with pytest.raises(...)` SIEMPRE invoca la "
        "función/método bajo prueba (p.ej. `funcion(args)`); no basta con asignar "
        "variables: si no se llama a nada, no se lanza la excepción y el test "
        "falla con 'DID NOT RAISE' sin probar el código"
    ),
    "assert_in_except": (
        "no verifiques excepciones con try/except poniendo el assert dentro del "
        "except: si la excepción no se lanza, el assert nunca corre y el test pasa "
        "sin probar nada. Usa siempre `with pytest.raises(TipoError): funcion(...)`"
    ),
}


def learn_from_failure(
    rag: RAGService,
    module_name: str,
    quality: dict,
    compiles: bool,
    metrics: dict | None,
    failures: dict[str, str] | None = None,
    degraded: bool = False,
    oracle_triage: dict[str, str] | None = None,
) -> bool:
    """Si la generación compiló y corrió, pero quedó incompleta de una forma
    reconocible (cobertura de funciones faltante pese al retry de OR-8, test
    smells, o tests que fallaron por una aserción con el valor esperado
    incorrecto), guarda advertencias en RAG para que futuras generaciones de
    este mismo módulo reciban ese contexto. Son documentos de "lección", no
    ejemplos de código (a diferencia de _learn_from_result).

    No se aprende de corridas degradadas: en ese caso el código son stubs
    pytest.skip() generados por el respaldo, no salida real del modelo, así
    que sus "smells" y huecos de cobertura son artefactos, no lecciones."""
    if not compiles or metrics is None or degraded:
        return False

    learned_something = False

    missing = [fn for fn, count in quality["tests_per_function"].items() if count == 0]
    if missing:
        doc_id = f"learned_warning_coverage_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, el "
            f"modelo no incluyó ningún test para estas funciones detectadas por el AST "
            f"parser: {', '.join(missing)}. Al generar tests para este módulo, incluye un "
            f"método test_<función>_<escenario> para CADA función listada en "
            f"'FUNCIONES DETECTADAS POR AST PARSER', sin omitir ninguna (regla OR-8)."
        )
        rag.add_warning(doc_id, text)
        rag.record_lesson_signal("coverage", module_name)
        learned_something = True

    smells = quality.get("smells_detected") or []
    if smells:
        guidance = "; ".join(_SMELL_GUIDANCE.get(s, s) for s in smells)
        doc_id = f"learned_warning_smells_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, los "
            f"tests generados tuvieron estos test smells: {', '.join(smells)}. Al generar "
            f"tests para este módulo, recuerda que {guidance}."
        )
        rag.add_warning(doc_id, text)
        rag.record_lesson_signal("smells", module_name)
        learned_something = True

    # Lección de aserciones: la señal semántica más rica. El modelo fijó el valor
    # esperado equivocado y pytest lo demostró al ejecutar. Se la devolvemos para
    # que reconsidere, advirtiéndole de NO copiar el valor obtenido a ciegas (eso
    # produciría un test tautológico que oculta el bug en vez de detectarlo).
    #
    # ORÁCULO: los fallos que el oráculo clasificó como 'bug_real' NO entran a esta
    # advertencia. Pedirle al modelo que "reconsidere su aserción" en un test que
    # cazó un bug real es justo la presión que confirmaba el defecto (problema 01):
    # el test tenía razón, el roto es el código. Solo se advierte de los fallos que
    # NO son bug_real (falsos positivos o sin oráculo claro).
    oracle_triage = oracle_triage or {}
    correctable = {
        name: detail for name, detail in (failures or {}).items()
        if oracle_triage.get(name) != ORACLE_BUG
    }
    if correctable:
        items = list(correctable.items())[:4]
        detalle = "\n".join(f"  - {name}: {detail}" for name, detail in items)
        doc_id = f"learned_warning_assertions_{module_name}"
        text = (
            f"ADVERTENCIA para el módulo '{module_name}': en una generación previa, estos "
            f"tests fallaron al ejecutarse porque su aserción no se cumplió:\n{detalle}\n"
            f"Revisa el comportamiento REAL de cada función (su código y su docstring) antes "
            f"de fijar el valor esperado en el assert. No copies a ciegas el valor que la "
            f"función devolvió solo para que el test pase: si ese valor no es el correcto "
            f"según el contrato de la función, el test sería tautológico y ocultaría un bug."
        )
        rag.add_warning(doc_id, text)
        rag.record_lesson_signal("assertions", module_name)
        learned_something = True

    return learned_something
