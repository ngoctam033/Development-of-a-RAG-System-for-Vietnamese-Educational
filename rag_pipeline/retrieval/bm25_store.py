# retrieval/bm25_store.py
from rank_bm25 import BM25Okapi

class BM25Store:
    def __init__(self, docs):
        # docs: list[str]
        self.docs = docs
        self.tokens = [d.lower().split() for d in docs]
        self.bm25 = BM25Okapi(self.tokens)

    def sparse_scores(self, query):
        return self.bm25.get_scores(query.lower().split())

    def topk(self, query, k=10):
        scores = self.sparse_scores(query)
        ranked = sorted(list(enumerate(scores)), key=lambda x: x[1], reverse=True)[:k]
        return ranked  # [(idx, score)]
