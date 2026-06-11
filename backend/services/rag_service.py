import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from data.seed_data import SEED_DOCUMENTS

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rag_store.json")
LEARNED_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learned_store.json")
WARNINGS_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "warnings_store.json")

WARNING_PREFIX = "learned_warning_"
# Tipos de advertencia que se generan por módulo (ver _learn_from_failure en
# test_generator). El doc_id de una advertencia es siempre de la forma
# f"{WARNING_PREFIX}{kind}_{module_name}".
WARNING_KINDS = ("coverage", "smells")


def _is_warning_id(doc_id: str) -> bool:
    return doc_id.startswith(WARNING_PREFIX)


class RAGService:
    def __init__(self):
        seed_ids = {d["id"] for d in SEED_DOCUMENTS}
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

        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self._matrix = None
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
        if texts:
            self._matrix = self._vectorizer.fit_transform(texts)

    # ── Recuperación ─────────────────────────────────────────────────
    def query(self, text: str, n_results: int = 3) -> list[str]:
        """Patrones/ejemplos relevantes por similitud coseno. No incluye
        advertencias (esas se recuperan con get_warnings, por clave)."""
        if self._matrix is None or self._matrix.shape[0] == 0:
            return []

        query_vec = self._vectorizer.transform([text])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:n_results]
        return [self._documents[i]["text"] for i in top_indices if scores[i] > 0]

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

    def list_documents(self) -> list[dict]:
        docs = [{"id": d["id"], "text": d["text"][:120] + "..."} for d in self._documents]
        warns = [{"id": k, "text": v[:120] + "..."} for k, v in self._warnings.items()]
        return docs + warns


rag_service = RAGService()
