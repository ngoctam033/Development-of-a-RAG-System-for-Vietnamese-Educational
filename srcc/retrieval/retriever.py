# src/retrieval/retriever.py
import math
from sentence_transformers import CrossEncoder
from config.pipeline_config import TOP_K_RECALL, TOP_K_FINAL, HYBRID_ALPHA, SIMILARITY_THRESHOLD
from config.models_config import RERANKER_MODEL

class HybridRetriever:
    def __init__(self, faiss_store, bm25_store, corpus):
        self.faiss = faiss_store
        self.bm25 = bm25_store
        self.corpus = corpus
        self.reranker = CrossEncoder(RERANKER_MODEL)

    @staticmethod
    def _normalize(pairs):
        if not pairs: return {}
        vals = [v for _, v in pairs]
        lo, hi = min(vals), max(vals)
        denom = (hi - lo) if hi > lo else 1.0
        return {i: (v - lo) / denom for i, v in pairs}

    def search(self, query):
        # 1) dense
        d_pairs = self.faiss.dense_search(query, top_k=TOP_K_RECALL)  # [(idx, score)]
        # 2) sparse
        s_pairs = self.bm25.topk(query, k=TOP_K_RECALL)
        # 3) blend
        d_norm = self._normalize(d_pairs)
        s_norm = self._normalize(s_pairs)
        ids = set(list(d_norm.keys()) + list(s_norm.keys()))
        blended = []
        for i in ids:
            score = HYBRID_ALPHA * d_norm.get(i, 0.0) + (1 - HYBRID_ALPHA) * s_norm.get(i, 0.0)
            blended.append((i, score))
        blended.sort(key=lambda x: x[1], reverse=True)
        candidates = blended[:TOP_K_RECALL]

        # 4) rerank (cross-encoder)
        passages = [{"idx": i, "text": self.corpus[i]} for i, _ in candidates]
        if not passages:
            return []

        pairs = [[query, p["text"]] for p in passages]
        ce_scores = self.reranker.predict(pairs).tolist()
        for p, s in zip(passages, ce_scores):
            p["rerank_score"] = float(s)

        passages.sort(key=lambda x: x["rerank_score"], reverse=True)
        top = []
        for p in passages[:TOP_K_FINAL]:
            # lọc mềm theo threshold với điểm dense gốc (nếu muốn chặt chẽ hơn)
            # ở đây giữ tất cả top_final; nếu cần: kiểm tra lại bằng dense score
            top.append(p)
        return top  # [{idx, text, rerank_score}]
