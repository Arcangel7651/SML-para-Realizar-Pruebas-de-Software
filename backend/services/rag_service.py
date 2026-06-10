import json
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from data.seed_data import SEED_DOCUMENTS

STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "rag_store.json")
LEARNED_STORE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "learned_store.json")


class RAGService:
    def __init__(self):
        seed_ids = {d["id"] for d in SEED_DOCUMENTS}
        user_docs = self._load_json(STORE_PATH)
        learned_docs = self._load_json(LEARNED_STORE_PATH)
        # seeds primero, luego documentos de usuario y aprendidos (sin duplicar ids de seed)
        self._documents: list[dict] = list(SEED_DOCUMENTS) + [
            d for d in user_docs + learned_docs if d["id"] not in seed_ids
        ]
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self._matrix = None
        self._fit()

    def _load_json(self, path: str) -> list[dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [{"id": k, "text": v} for k, v in data.items()]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, path: str, doc_ids: set[str]):
        docs = {d["id"]: d["text"] for d in self._documents if d["id"] in doc_ids}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=2)

    def _fit(self):
        texts = [doc["text"] for doc in self._documents]
        if texts:
            self._matrix = self._vectorizer.fit_transform(texts)

    def query(self, text: str, n_results: int = 3) -> list[str]:
        if self._matrix is None or self._matrix.shape[0] == 0:
            return []

        query_vec = self._vectorizer.transform([text])
        scores = cosine_similarity(query_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:n_results]
        return [self._documents[i]["text"] for i in top_indices if scores[i] > 0]

    def add_document(self, doc_id: str, text: str):
        """Documentos agregados manualmente (vía API) -> rag_store.json"""
        self._upsert(doc_id, text)
        self._save_split_stores()

    def add_learned_document(self, doc_id: str, text: str):
        """Documentos aprendidos automáticamente tras una generación de alta
        calidad -> learned_store.json (archivo separado del de documentos
        agregados manualmente)."""
        self._upsert(doc_id, text)
        self._save_split_stores()

    def _save_split_stores(self):
        seed_ids = {d["id"] for d in SEED_DOCUMENTS}
        user_ids = {
            d["id"] for d in self._documents
            if d["id"] not in seed_ids and not d["id"].startswith("learned_")
        }
        learned_ids = {
            d["id"] for d in self._documents
            if d["id"].startswith("learned_")
        }
        self._save_json(STORE_PATH, user_ids)
        self._save_json(LEARNED_STORE_PATH, learned_ids)

    def _upsert(self, doc_id: str, text: str):
        self._documents = [d for d in self._documents if d["id"] != doc_id]
        self._documents.append({"id": doc_id, "text": text})
        self._fit()

    def list_documents(self) -> list[dict]:
        return [{"id": d["id"], "text": d["text"][:120] + "..."} for d in self._documents]


rag_service = RAGService()
