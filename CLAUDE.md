# Instrucciones del proyecto — SLM Test Generator

## Documentación de hallazgos, problemas y soluciones (regla principal)

Cuando durante el trabajo en este proyecto descubramos un **problema, hallazgo o decisión relevante** junto con su solución, documentarlo **siempre** como un archivo Markdown nuevo en:

```
C:\Users\angel\Documents\PRACTICAS\resultados\problemas-y-soluciones\
```

- Nombre de archivo: `NN-titulo-en-kebab.md` (numeración correlativa).
- Contenido: **Contexto**, **Problema**, **Evidencia**, **Causa raíz**, **Solución** (propuesta o implementada) y **Estado**.
- Mantener actualizado el `indice.md` de esa carpeta (tabla con # / problema / estado).

Esta regla aplica a esta conversación y a futuras. Si un hallazgo aplica también a otras conversaciones de este tipo (resultados experimentales, problemas con solución), agregarlo igualmente.

## Resultados experimentales por módulo

Los resultados de los experimentos de generación de tests (por módulo) van en:

```
C:\Users\angel\Documents\PRACTICAS\resultados\<modulo>.md
```

con su índice y conclusiones transversales en `resumen-general.md` de esa misma carpeta.

## Arquitectura (respetar SIEMPRE al construir)

Stack: **Backend** Python 3.11 + FastAPI (arquitectura por capas) · **Frontend** React 18 + Vite 5 · **LLM** Ollama (SLMs locales) + RAG · **Contenedores** Docker Compose.

### Backend — capas (la dependencia fluye hacia adentro, nunca al revés)

```
api/  ──>  services/  ──>  infrastructure/  ──>  data/
```

- **`api/`** (`routes.py`): solo HTTP. Define endpoints, valida request (Pydantic), arma `StreamingResponse` NDJSON, delega en services. No mete lógica de negocio ni acceso directo a archivos/Ollama.
- **`services/`**: toda la lógica de dominio. **Un módulo = una responsabilidad** (este es el patrón establecido tras refactorizar el monolito `test_generator.py`):
  - `test_generator.py` — **orquestador** del pipeline; compone los demás módulos, no reimplementa su lógica.
  - `test_prompt_builder.py` (construcción de prompts/system prompt SMS) · `llm_output_parser.py` (extraer código, `check_compiles`) · `test_repair.py` (reparación determinística) · `degraded_suite.py` (suite degradada + cobertura faltante) · `pytest_runner.py` (ejecutar pytest, potential bugs) · `rag_learning.py` (`learn_from_result`/`learn_from_failure`) · `rag_service.py` (RAGService singleton + 3 stores) · `ast_parser.py` · `quality_analyzer.py` · `oracle.py` (triage) · `bugs_store.py` · `results_log.py` (telemetría CSV) · `ablation.py`.
- **`infrastructure/`**: adaptadores a sistemas externos. `ollama_client.py` (chat/chat_stream/embed/list_models) y `file_reader.py` (valida/decodifica el .py subido). Es el ÚNICO lugar que habla con Ollama o el filesystem de entrada.
- **`data/`**: stores JSON, seeds, CSV de resultados (volumen persistente en Docker).
- `main.py`: solo wiring (FastAPI app, CORS abierto demo, `include_router`).

### Frontend — componentes (React + Vite, sin framework de estado externo)

- `App.jsx`: estado global y orquestación (streaming NDJSON robusto, auto-selección de modelo, timer, abort). Mantiene el estado, lo baja por props.
- `components/`: presentación. Un componente por archivo con su `.css` hermano (`TestOutput`, `MetricsPanel`, `ResultsModal`, `AblationModal`, `FileUpload`, `PromptPanel`, `Icon`). Consumen `/api/*` vía axios; reciben datos por props, no hacen lógica de dominio.
- `main.jsx`: entrypoint.

## Reglas de construcción (aplican a todo cambio en este repo)

1. **Respetar las capas.** Lógica nueva de dominio → `services/`. Acceso a Ollama/FS → `infrastructure/`. HTTP → `api/`. Nada de lógica de negocio en `routes.py` ni de IO directo en services.
2. **Una responsabilidad por módulo.** No volver a engordar `test_generator.py`: si crece una nueva etapa del pipeline, extraer un módulo nuevo en `services/` y orquestarlo, igual que `test_repair`, `degraded_suite`, etc.
3. **No reintroducir dependencias prohibidas.** Para RAG nada de `chromadb` (falla en Windows): embeddings de Ollama con fallback TF-IDF + cosine de scikit-learn.
4. **Mantener paridad stream / no-stream.** Existe lógica de retry duplicada entre `generate_tests` y el `event_stream` de `routes.py`: si tocas el pipeline, actualiza AMBOS o factoriza la lógica compartida a un módulo de `services/`.
5. **No romper las decisiones del SMS** (testing a nivel de clase, Given-When-Then, system prompt estilo PromptPex/anti-smells, compilabilidad con py_compile). Cualquier cambio que las afecte se discute antes.
6. **Aprender solo de lo verificado.** El RAG guarda únicamente código que pasó pytest; los "posibles bugs" van a `bugs_store`, no al RAG. No mezclar esas vías.
7. **Telemetría.** Toda generación anexa fila a `data/results_log.csv` vía `results_log.log_result`. Si agregas una señal relevante, súmala como columna ahí, no en un sitio nuevo.
8. **Frontend sin lógica de dominio.** Componentes presentacionales; estado en `App.jsx`; cada componente con su `.css` hermano.
9. **Documentar hallazgos** según la regla principal de arriba (carpeta `problemas-y-soluciones/`).
