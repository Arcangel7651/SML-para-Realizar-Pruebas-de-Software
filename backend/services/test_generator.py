"""Orquestador de la generación de tests. Coordina el pipeline completo de una
solicitud: análisis AST → recuperación de contexto RAG → construcción del prompt
→ llamada al LLM → reparación determinística → reintentos (compilación y
cobertura) → suite degradada de respaldo → ejecución bajo pytest → oráculo →
aprendizaje en RAG → registro de resultados. Cada paso vive en su propio módulo
de la capa `services/`; aquí solo se encadenan.

El pipeline se expresa UNA sola vez como `run_pipeline`, un generador que emite
eventos (`meta`/`token`/`retrying`/`error`/`done`). El endpoint de streaming
serializa esos eventos a NDJSON; `generate_tests` los drena e ignora los `token`
para devolver el resultado completo. Así ambas rutas (stream y no-stream)
comparten exactamente la misma lógica de dominio (ver regla 4 del proyecto)."""

import time
from collections.abc import Generator

from infrastructure.ollama_client import chat, chat_stream
from services.rag_service import RAGService
from services.ast_parser import extract_functions, extract_classes
from services.quality_analyzer import analyze as analyze_quality
from services.results_log import log_result
from services.bugs_store import record_and_annotate
from services.oracle import triage_failures

from services.test_prompt_builder import (
    SYSTEM_PROMPT,
    build_user_message,
    build_functions_block,
    build_classes_block,
    build_coverage_retry_message,
)
from services.llm_output_parser import extract_code, check_compiles
from services.test_repair import repair_generated_tests
from services.degraded_suite import build_degraded_tests, missing_function_coverage
from services.pytest_runner import run_pytest as run_pytest_suite, build_potential_bugs
from services.rag_learning import learn_from_result, learn_from_failure


def run_pipeline(
    source_code: str,
    prompt: str,
    model: str,
    rag: RAGService,
    module_name: str = "modulo",
    run_pytest: bool = True,
    use_global_lessons: bool = True,
) -> Generator[dict, None, None]:
    """Ejecuta el pipeline completo y emite eventos. La primera llamada al LLM
    se hace siempre en streaming (emite eventos `token`); el resto del pipeline
    es idéntico para ambas rutas. El consumidor decide qué hacer con los eventos:
    el endpoint stream los manda por NDJSON, `generate_tests` los acumula."""
    print(f"\n{'='*50}")
    print(f"[SLM] Solicitud recibida | modelo: {model}")
    print(f"[SLM] Líneas de código fuente: {len(source_code.splitlines())}")
    t_total = time.time()

    print(f"[AST] Analizando funciones...")
    functions = extract_functions(source_code)
    functions_found = [fn["nombre"] for fn in functions]
    print(f"[AST] Detectadas: {functions_found}")
    for fn in functions:
        if fn["excepciones"]:
            print(f"[AST]   → {fn['nombre']}() lanza: {', '.join(fn['excepciones'])}")

    print(f"[RAG] Buscando fragmentos relevantes...")
    warnings = rag.get_warnings(module_name)
    # Lecciones globales (memoria semántica): debilidades sistemáticas vistas en
    # varios módulos. Se inyectan en TODA generación, salvo las que este módulo ya
    # cubre con su advertencia específica (más relevante). Dan contexto útil
    # incluso en la primera corrida de un módulo nuevo (cold-start).
    # use_global_lessons=False las desactiva (condición OFF de la ablación).
    global_lessons = (
        rag.get_global_lessons(exclude_kinds=rag.get_warning_kinds(module_name))
        if use_global_lessons else []
    )
    # Anclaje al MISMO módulo: el único ejemplo aprendido que se inyecta es el
    # del propio módulo. Los patrones por similitud excluyen los aprendidos
    # (include_learned=False) para no recibir el ejemplo de otro módulo casi
    # idéntico (contaminación cruzada buggy↔corregido, problema 07).
    own_examples = [e["text"] for e in rag.get_learned_examples(module_name)][:1]
    patterns = rag.query(source_code + " " + prompt, n_results=3 - len(own_examples), include_learned=False)
    # Advertencias del módulo y lecciones globales van primero (por clave, aditivas),
    # luego el ejemplo propio y los patrones por similitud.
    context_fragments = warnings + global_lessons + own_examples + patterns
    print(f"[RAG] {len(warnings)} advertencia(s) + {len(global_lessons)} lección(es) global(es) + {len(own_examples)} ejemplo(s) propio(s) + {len(patterns)} patrón(es)")

    context_block  = "\n\n".join(context_fragments) if context_fragments else "Sin contexto adicional."
    functions_block = build_functions_block(functions)
    classes_block   = build_classes_block(module_name, extract_classes(source_code))
    module_pascal   = "".join(w.capitalize() for w in module_name.split("_"))

    user_message = build_user_message(
        module_name, module_pascal, context_block, functions_block, classes_block, prompt, source_code
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    # Metadatos tempranos: el front pinta funciones detectadas y contexto usado
    # antes de que empiece a llegar el código. En no-stream se acumulan igual.
    yield {
        "type": "meta",
        "functions_found": functions_found,
        "context_used": context_fragments,
    }

    print(f"[LLM] Enviando a Ollama...")
    t0 = time.time()
    raw_chunks: list[str] = []
    try:
        for chunk in chat_stream(model=model, messages=messages):
            raw_chunks.append(chunk)
            yield {"type": "token", "content": chunk}
    except Exception as e:
        yield {"type": "error", "message": f"Ollama no respondió: {e}"}
        return
    raw_response = "".join(raw_chunks)
    print(f"[LLM] Respuesta en {time.time() - t0:.1f}s (~{len(raw_response.split())} tokens)")

    tests_code, explanation = extract_code(raw_response)
    tests_code = repair_generated_tests(
        tests_code, module_name, extract_classes(source_code), functions_found
    )

    print(f"[COMPILE] Verificando sintaxis...")
    compiles, compile_error = check_compiles(tests_code)
    print(f"[COMPILE] {'OK' if compiles else 'ERROR — ' + str(compile_error)}")

    if not compiles:
        print(f"[RETRY] Compilación fallida, reintentando con error en contexto...")
        yield {"type": "retrying", "reason": compile_error}
        retry_messages = messages + [
            {"role": "assistant", "content": raw_response},
            {"role": "user", "content": (
                f"El código generado tiene un error de sintaxis Python:\n{compile_error}\n\n"
                f"Corrige únicamente ese error y devuelve el código completo corregido. "
                f"Solo código Python válido, sin explicaciones ni markdown."
            )},
        ]
        t0 = time.time()
        raw_retry = chat(model=model, messages=retry_messages)
        print(f"[RETRY] Respuesta en {time.time() - t0:.1f}s")
        tests_retry, explanation_retry = extract_code(raw_retry)
        tests_retry = repair_generated_tests(
            tests_retry, module_name, extract_classes(source_code), functions_found
        )
        compiles_retry, compile_error_retry = check_compiles(tests_retry)
        if compiles_retry:
            print(f"[RETRY] Éxito — código corregido compila")
            tests_code    = tests_retry
            explanation   = explanation_retry or explanation
            compiles      = True
            compile_error = None
        else:
            print(f"[RETRY] Fallido de nuevo — manteniendo resultado inicial")

    if compiles:
        missing_functions = missing_function_coverage(tests_code, functions_found)
        if missing_functions:
            print(f"[RETRY] Faltan tests para: {', '.join(missing_functions)} — reintentando...")
            yield {"type": "retrying", "reason": f"Faltan tests para: {', '.join(missing_functions)}"}
            retry_messages = messages + [
                {"role": "assistant", "content": tests_code},
                build_coverage_retry_message(missing_functions),
            ]
            t0 = time.time()
            raw_retry2 = chat(model=model, messages=retry_messages)
            print(f"[RETRY] Respuesta en {time.time() - t0:.1f}s")
            tests_retry2, explanation_retry2 = extract_code(raw_retry2)
            tests_retry2 = repair_generated_tests(
                tests_retry2, module_name, extract_classes(source_code), functions_found
            )
            compiles_retry2, compile_error_retry2 = check_compiles(tests_retry2)
            if compiles_retry2:
                print(f"[RETRY] Éxito — código corregido compila")
                tests_code  = tests_retry2
                explanation = explanation_retry2 or explanation
            else:
                print(f"[RETRY] Fallido de nuevo — manteniendo resultado anterior")

    degraded = False
    if not compiles:
        print(f"[DEGRADE] Generando suite de respaldo (rescate de métodos + skips)...")
        classes_detected = extract_classes(source_code)
        degraded_code = build_degraded_tests(
            tests_code, module_name, module_pascal, functions_found, classes_detected, compile_error
        )
        degraded_compiles, degraded_compile_error = check_compiles(degraded_code)
        if degraded_compiles:
            tests_code = degraded_code
            compiles = True
            compile_error = None
            degraded = True
            print(f"[DEGRADE] Suite de respaldo compila — se ejecutará con métricas degradadas")
        else:
            print(f"[DEGRADE] Suite de respaldo tampoco compiló: {degraded_compile_error}")

    metrics = None
    passing_tests: set[str] = set()
    failures: dict[str, str] = {}
    if compiles and run_pytest:
        print(f"[PYTEST] Ejecutando evaluación...")
        metrics, passing_tests, failures = run_pytest_suite(source_code, tests_code, module_name)
        if metrics:
            print(f"[PYTEST] {metrics['tests_passed']}/{metrics['tests_total']} pasan | "
                  f"cobertura: {metrics['line_coverage']}%")
    elif not run_pytest:
        print(f"[PYTEST] Omitido por configuración")

    print(f"[QUALITY] Analizando calidad...")
    quality = analyze_quality(tests_code, functions_found, f"Test{module_pascal}")
    print(f"[QUALITY] Given/When/Then: {quality['has_given_when_then']} | "
          f"smells: {quality['smells_detected']}")

    # ORÁCULO: clasifica cada test que falló contra el docstring de su función
    # (bug_real / falso_positivo / sin_oraculo). Solo corre si hubo fallos reales
    # (no en degradado: ahí el código son stubs del respaldo). Cada veredicto es
    # otra llamada al SLM, así que solo se invoca cuando hay algo que juzgar.
    oracle_triage: dict[str, str] = {}
    if failures and not degraded:
        print(f"[ORACLE] Clasificando {len(failures)} fallo(s) contra el docstring...")
        oracle_triage = triage_failures(failures, functions, model)
        for name, verdict in oracle_triage.items():
            print(f"[ORACLE]   {name}: {verdict}")

    learned = learn_from_result(
        rag, module_name, functions_found, tests_code, compiles, metrics, quality,
        passing_tests, source_code,
    )
    if learned:
        print(f"[RAG] Ejemplo verificado (completo o parcial) guardado como 'learned_{module_name}'")
    # Las advertencias se evalúan aparte: aplican aunque se haya aprendido un
    # subconjunto parcial (p.ej. cobertura incompleta o smells).
    if learn_from_failure(rag, module_name, quality, compiles, metrics, failures, degraded, oracle_triage):
        print(f"[RAG] Advertencia(s) guardada(s) para '{module_name}'")

    log_result(model, module_name, metrics, quality, functions_found, context_fragments, warnings, compiles, learned, degraded, time.time() - t_total, global_lessons_enabled=use_global_lessons)

    # Opción A + oráculo + persistencia: registra los fallos de esta corrida (con
    # el veredicto del oráculo) en un store aparte del RAG y recupera los
    # acumulados del módulo (incluye runs previos).
    potential_bugs = record_and_annotate(
        module_name,
        build_potential_bugs(failures, degraded, tests_code, functions_found, oracle_triage),
    )

    print(f"[SLM] Listo. {len(tests_code.splitlines())} líneas generadas")
    print(f"{'='*50}\n")

    yield {
        "type":          "done",
        "tests":         tests_code,
        "explanation":   explanation,
        "compiles":      compiles,
        "compile_error": compile_error,
        "metrics":       metrics,
        "quality":       quality,
        "learned":       learned,
        "degraded":      degraded,
        "potential_bugs": potential_bugs,
    }


def generate_tests(
    source_code: str,
    prompt: str,
    model: str,
    rag: RAGService,
    module_name: str = "modulo",
    run_pytest: bool = True,
    use_global_lessons: bool = True,
) -> dict:
    """Variante no-stream: drena `run_pipeline`, ignora los tokens y arma el dict
    de respuesta a partir de los eventos `meta` y `done`. Misma firma y mismas
    claves de retorno de siempre."""
    result: dict = {}
    for event in run_pipeline(
        source_code, prompt, model, rag, module_name, run_pytest, use_global_lessons
    ):
        kind = event["type"]
        if kind == "error":
            # Sin stream no hay canal de eventos: propagamos como excepción para
            # conservar el comportamiento previo (500 en el endpoint).
            raise RuntimeError(event["message"])
        if kind in ("meta", "done"):
            result.update(event)
    result.pop("type", None)
    return result
