from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from data.seed_data import SEED_DOCUMENTS


class RAGService:
    def __init__(self):
        self._documents: list[dict] = list(SEED_DOCUMENTS)
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self._matrix = None
        self._fit()

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
        self._documents = [d for d in self._documents if d["id"] != doc_id]
        self._documents.append({"id": doc_id, "text": text})
        self._fit()

    def list_documents(self) -> list[dict]:
        return [{"id": d["id"], "text": d["text"][:120] + "..."} for d in self._documents]


rag_service = RAGService()
