import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from data.seed_data import SEED_DOCUMENTS
from infrastructure.ollama_client import embed_texts

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rag_store.json")
LEARNED_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learned_store.json")
WARNINGS_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "warnings_store.json")
LESSONS_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lessons_store.json")

WARNING_PREFIX = "learned_warning_"
# Tipos de advertencia que se generan por módulo (ver _learn_from_failure en
# test_generator). El doc_id de una advertencia es siempre de la forma
# f"{WARNING_PREFIX}{kind}_{module_name}".
WARNING_KINDS = ("coverage", "smells", "assertions")

# ── Memoria semántica/procedural (lecciones globales) ────────────────────
# Segundo nivel de aprendizaje (taxonomía CoALA): las advertencias por módulo
# son memoria episódica (atada a un módulo). Cuando el MISMO tipo de problema
# se repite en VARIOS módulos distintos, deja de ser un capricho del módulo y
# pasa a ser una debilidad sistemática del modelo: se promueve a "lección
# global", texto agnóstico del módulo que se inyecta en TODA generación (incluida
# la primera de un módulo nuevo → arregla el cold-start). Es texto-lección, no
# código y no entra al índice de similitud, así que NO puede reintroducir la
# contaminación cruzada entre módulos casi idénticos (problema 07).
GLOBAL_LESSON_TEXTS = {
    "coverage": (
        "LECCIÓN GENERAL (problema recurrente en varios módulos): el modelo tiende "
        "a dejar funciones sin ningún test. Incluye un método "
        "test_<función>_<escenario> para CADA función de 'FUNCIONES DETECTADAS POR "
        "AST PARSER', sin omitir ninguna (regla OR-8)."
    ),
    "smells": (
        "LECCIÓN GENERAL (problema recurrente en varios módulos): los tests suelen "
        "tener test smells. Cada test debe ejercitar comportamiento real e invocar "
        "la función bajo prueba; verifica excepciones con `with pytest.raises(...): "
        "funcion(...)` (nunca con un assert dentro de un except), usa nombres "
        "test_<función>_<escenario> y pon un mensaje en cada assert si hay más de uno."
    ),
    "assertions": (
        "LECCIÓN GENERAL (problema recurrente en varios módulos): el valor esperado "
        "de los asserts suele fijarse mal. Derívalo del COMPORTAMIENTO ESPERADO "
        "(docstring) de cada función, no de ejecutar el código mentalmente, y no "
        "copies a ciegas el valor que la función devuelve solo para que el test pase "
        "(regla OR-9)."
    ),
}

# Nº de módulos DISTINTOS en que debe haberse visto un tipo de problema para
# promover su lección a global. Bajo a propósito (corpus pequeño); subir si el
# prompt se infla o si las lecciones empiezan a inyectarse sin aportar.
PROMOTION_THRESHOLD = 2
# Tope de lecciones globales inyectadas por generación (evita inflar el prompt).
GLOBAL_LESSON_CAP = 3

# Interruptor de la INYECCIÓN de lecciones globales (no afecta el registro de
# señales, que sigue acumulándose siempre). Default por variable de entorno para
# poder correr un lote entero en una condición; cada petición puede sobreescribirlo
# (use_global_lessons) para intercalar ON/OFF en la ablación sin reiniciar.
GLOBAL_LESSONS_DEFAULT = os.getenv("GLOBAL_LESSONS_ENABLED", "1").lower() not in ("0", "false", "no")


def _is_warning_id(doc_id: str) -> bool:
    return doc_id.startswith(WARNING_PREFIX)


class RAGService:
    def __init__(self):
        seed_ids = {d["id"] for d in SEED_DOCUMENTS}
        self._seed_ids = seed_ids
        user_docs = self._load_json(STORE_PATH)
        learned_docs = self._load_json(LEARNED_STORE_PATH)
        warning_docs = self._load_json(WARNINGS_STORE_PATH)

        # Índice de similitud: seeds + documentos de usuario + ejemplos buenos
        # aprendidos. Las advertencias NO entran aquí: no deben competir por
        # los cupos del top-k de patrones ni filtrarse a otros módulos por
        # similitud de términos.
        positive = [
            d for d in user_docs + learned_docs
            if d["id"] not in seed_ids and not _is_warning_id(d["id"])
        ]
        self._documents: list[dict] = list(SEED_DOCUMENTS) + positive

        # Advertencias: dict {doc_id: text}, recuperadas por clave exacta de
        # módulo (no por similitud). Se cargan del archivo dedicado y, por
        # migración, también de cualquier advertencia que aún viva dentro de
        # learned_store.json (formato anterior); al guardar quedan separadas.
        legacy_warnings = [d for d in learned_docs if _is_warning_id(d["id"])]
        self._warnings: dict[str, str] = {
            d["id"]: d["text"] for d in warning_docs + legacy_warnings
        }

        # Lecciones globales: tally {kind: [módulos distintos]}. La primera vez
        # se bootstrappea desde las advertencias ya existentes (así el aprendizaje
        # acumulado hasta ahora cuenta de inmediato, sin esperar a re-observar
        # cada problema). Persiste aparte y NO se borra con clear_warnings.
        self._lessons: dict[str, list[str]] = self._load_lessons()
        if self._lessons is None:
            self._lessons = self._bootstrap_lessons_from_warnings()
            self._save_lessons()

        # Recuperación: se intentan embeddings semánticos (Ollama); si no están
        # disponibles, se cae a TF-IDF (similitud léxica). _use_embeddings se
        # decide en _fit() según si el servicio de embeddings respondió.
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self._matrix = None
        self._embeddings = None
        self._use_embeddings = False
        self._fit()

        # Si había advertencias dentro de learned_store.json (versión previa),
        # reescribe ambos archivos para dejarlas ya separadas en su store.
        if legacy_warnings:
            self._save_split_stores()
            self._save_warnings()

    def _load_json(self, path: str) -> list[dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [{"id": k, "text": v} for k, v in data.items()]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, path: str, docs: dict[str, str]):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

    def _fit(self):
        texts = [doc["text"] for doc in self._documents]
        self._matrix = None
        self._embeddings = None
        if not texts:
            self._use_embeddings = False
            return

        # Preferir embeddings semánticos; si Ollama no los da, caer a TF-IDF.
        vectors = embed_texts(texts)
        if vectors is not None:
            self._embeddings = np.array(vectors, dtype=float)
            self._use_embeddings = True
        else:
            self._use_embeddings = False
            self._matrix = self._vectorizer.fit_transform(texts)

    # ── Recuperación ─────────────────────────────────────────────────
    def query(self, text: str, n_results: int = 3, min_seeds: int = 1,
              include_learned: bool = True) -> list[str]:
        """Patrones/ejemplos relevantes por similitud coseno (embeddings
        semánticos si están disponibles, TF-IDF si no). No incluye
        advertencias (esas se recuperan con get_warnings, por clave).

        Reserva `min_seeds` cupos para patrones SEED (curados del SMS): los
        ejemplos aprendidos suelen ser los más similares (son del mismo módulo)
        y, a medida que crece el corpus aprendido, tenderían a desplazar del
        top-k a los patrones diversos. Reservar cupos de seed mantiene esa
        diversidad y evita el efecto eco (el modelo reproduciéndose a sí mismo).

        Con `include_learned=False` se excluyen TODOS los ejemplos aprendidos
        (`learned_*`): así un módulo no recibe por similitud el ejemplo aprendido
        de OTRO módulo casi idéntico (evita contaminación cruzada buggy↔corregido,
        problema 07). El ejemplo del propio módulo se inyecta aparte por el caller
        con get_learned_examples()."""
        if not self._documents:
            return []

        if self._use_embeddings and self._embeddings is not None:
            query_vec = embed_texts([text])
            if not query_vec:
                return []
            scores = cosine_similarity(np.array(query_vec, dtype=float), self._embeddings).flatten()
        elif self._matrix is not None:
            query_vec = self._vectorizer.transform([text])
            scores = cosine_similarity(query_vec, self._matrix).flatten()
        else:
            return []

        order = [int(i) for i in np.argsort(scores)[::-1] if scores[i] > 0]
        if not include_learned:
            order = [i for i in order if not self._documents[i]["id"].startswith("learned_")]
        if not order:
            return []

        # La mayoría de los cupos por relevancia global; el resto reservado a
        # los seeds más relevantes aún no incluidos.
        selected = list(order[: max(n_results - min_seeds, 0)])
        reserved = [
            i for i in order
            if self._documents[i]["id"] in self._seed_ids and i not in selected
        ]
        selected += reserved[:min_seeds]
        # Completar por relevancia si quedan cupos (p.ej. no había seeds).
        for i in order:
            if len(selected) >= n_results:
                break
            if i not in selected:
                selected.append(i)

        selected = sorted(selected, key=lambda i: scores[i], reverse=True)[:n_results]
        return [self._documents[i]["text"] for i in selected]

    def get_warnings(self, module_name: str) -> list[str]:
        """Advertencias del módulo, por clave exacta. Solo aplican a este
        módulo, así que se inyectan siempre que se regenera y nunca se
        filtran a otro módulo por azar de similitud."""
        out = []
        for kind in WARNING_KINDS:
            key = f"{WARNING_PREFIX}{kind}_{module_name}"
            if key in self._warnings:
                out.append(self._warnings[key])
        return out

    def get_learned_examples(self, module_name: str) -> list[dict]:
        """Ejemplos verificados de un módulo. Soporta el id histórico
        `learned_<modulo>` (un único ejemplo) y el esquema multi-ejemplo
        `learned_<modulo>#<slot>`. El delimitador '#' no aparece en nombres de
        módulo (vienen del nombre de un archivo .py), así que un módulo cuyo
        nombre sea prefijo de otro (p.ej. 'cuenta' vs 'cuenta_bancaria') no
        captura ejemplos ajenos."""
        legacy = f"learned_{module_name}"
        prefix = f"learned_{module_name}#"
        return [
            {"id": d["id"], "text": d["text"]}
            for d in self._documents
            if d["id"] == legacy or d["id"].startswith(prefix)
        ]

    # ── Escritura: ejemplos y docs de usuario (índice de similitud) ──
    def add_document(self, doc_id: str, text: str):
        """Documentos agregados manualmente (vía API) -> rag_store.json"""
        self._upsert(doc_id, text)
        self._save_split_stores()

    def add_learned_document(self, doc_id: str, text: str):
        """Ejemplo verificado de alta calidad tras una generación ->
        learned_store.json (índice de similitud)."""
        self._upsert(doc_id, text)
        self._save_split_stores()

    def _upsert(self, doc_id: str, text: str):
        self._documents = [d for d in self._documents if d["id"] != doc_id]
        self._documents.append({"id": doc_id, "text": text})
        self._fit()

    def remove_document(self, doc_id: str):
        """Elimina un ejemplo/documento del índice de similitud."""
        if not any(d["id"] == doc_id for d in self._documents):
            return
        self._documents = [d for d in self._documents if d["id"] != doc_id]
        self._fit()
        self._save_split_stores()

    # ── Escritura: advertencias (store por clave, fuera del índice) ──
    def add_warning(self, doc_id: str, text: str):
        """Lección por módulo -> warnings_store.json. No entra al índice de
        similitud; se recupera con get_warnings(module_name)."""
        self._warnings[doc_id] = text
        self._save_warnings()

    def clear_warnings(self, module_name: str):
        """Borra todas las advertencias de un módulo (p.ej. cuando una
        generación posterior salió limpia y las lecciones ya no aplican)."""
        removed = False
        for kind in WARNING_KINDS:
            key = f"{WARNING_PREFIX}{kind}_{module_name}"
            if key in self._warnings:
                del self._warnings[key]
                removed = True
        if removed:
            self._save_warnings()

    # ── Persistencia ─────────────────────────────────────────────────
    def _save_split_stores(self):
        seed_ids = {d["id"] for d in SEED_DOCUMENTS}
        user_docs = {
            d["id"]: d["text"] for d in self._documents
            if d["id"] not in seed_ids and not d["id"].startswith("learned_")
        }
        learned_docs = {
            d["id"]: d["text"] for d in self._documents
            if d["id"].startswith("learned_")
        }
        self._save_json(STORE_PATH, user_docs)
        self._save_json(LEARNED_STORE_PATH, learned_docs)

    def _save_warnings(self):
        self._save_json(WARNINGS_STORE_PATH, dict(self._warnings))

    # ── Lecciones globales (memoria semántica/procedural) ────────────
    def _load_lessons(self) -> dict[str, list[str]] | None:
        """Tally de lecciones desde lessons_store.json, o None si no existe aún
        (señal para bootstrappear desde las advertencias)."""
        try:
            with open(LESSONS_STORE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                k: list(dict.fromkeys(v))
                for k, v in data.items() if k in WARNING_KINDS
            }
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _bootstrap_lessons_from_warnings(self) -> dict[str, list[str]]:
        """Conteo inicial de módulos por tipo de problema, derivado de las
        advertencias ya guardadas (doc_id `learned_warning_<kind>_<module>`)."""
        tally: dict[str, list[str]] = {kind: [] for kind in WARNING_KINDS}
        for key in self._warnings:
            rest = key[len(WARNING_PREFIX):]  # <kind>_<module>
            for kind in WARNING_KINDS:
                if rest.startswith(kind + "_"):
                    module = rest[len(kind) + 1:]
                    if module not in tally[kind]:
                        tally[kind].append(module)
                    break
        return tally

    def record_lesson_signal(self, kind: str, module_name: str):
        """Registra que el problema `kind` se observó en `module_name`. Cuenta
        módulos DISTINTOS: una vez registrado un módulo, repetirlo no infla el
        conteo. Persiste aparte de las advertencias (no se borra al limpiarlas)."""
        if kind not in WARNING_KINDS:
            return
        modules = self._lessons.setdefault(kind, [])
        if module_name not in modules:
            modules.append(module_name)
            self._save_lessons()

    def get_warning_kinds(self, module_name: str) -> set[str]:
        """Tipos de advertencia que este módulo ya tiene (advertencia específica).
        Sirve para NO inyectarle además la lección global del mismo tipo (la
        específica del módulo es más relevante; la global cubre el resto)."""
        return {
            kind for kind in WARNING_KINDS
            if f"{WARNING_PREFIX}{kind}_{module_name}" in self._warnings
        }

    def get_global_lessons(self, exclude_kinds: set[str] | None = None) -> list[str]:
        """Lecciones promovidas a globales: las que se han visto en al menos
        PROMOTION_THRESHOLD módulos distintos, excluyendo las que el módulo actual
        ya cubre con su advertencia específica. Acotadas a GLOBAL_LESSON_CAP."""
        exclude = exclude_kinds or set()
        out = []
        for kind in WARNING_KINDS:
            if kind in exclude:
                continue
            if len(set(self._lessons.get(kind, []))) >= PROMOTION_THRESHOLD:
                out.append(GLOBAL_LESSON_TEXTS[kind])
            if len(out) >= GLOBAL_LESSON_CAP:
                break
        return out

    def _save_lessons(self):
        self._save_json(LESSONS_STORE_PATH, self._lessons)

    def get_document(self, doc_id: str) -> str | None:
        """Texto de un documento del índice por id, o None si no existe."""
        for d in self._documents:
            if d["id"] == doc_id:
                return d["text"]
        return None

    def list_documents(self) -> list[dict]:
        docs = [{"id": d["id"], "text": d["text"][:120] + "..."} for d in self._documents]
        warns = [{"id": k, "text": v[:120] + "..."} for k, v in self._warnings.items()]
        return docs + warns


rag_service = RAGService()
