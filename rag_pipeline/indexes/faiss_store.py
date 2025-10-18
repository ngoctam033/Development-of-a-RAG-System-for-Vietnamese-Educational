#indexes/faiss_store.py
import os
import numpy as np
import faiss
from typing import List, Dict, Optional

from sentence_transformers import SentenceTransformer

# Lấy cấu hình model & đường dẫn index
try:
    from config.models_config import EMBEDDING_MODEL  # ví dụ: "intfloat/multilingual-e5-base"
except Exception:
    EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

try:
    from config.pipeline_config import FAISS_INDEX_PATH, MAX_EMBED_TEXT_CHARS
except Exception:
    # Fallback nếu bạn chưa khai báo trong pipeline_config
    FAISS_INDEX_PATH = "data/vector_store/index.faiss"
    MAX_EMBED_TEXT_CHARS = 3000  # cắt bớt text dài để tránh OOM

# Batch size cố định theo yêu cầu
EMBED_BATCH_SIZE = 4


class FaissStore:
    """
    FAISS vector store:
      - Build index từ list văn bản + metadata
      - Load index/metadata để search
      - Dense search bằng cosine (dot-product nếu đã normalize)
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or EMBEDDING_MODEL
        self.model = SentenceTransformer(self.model_name)
        self.index: Optional[faiss.Index] = None
        self.meta: List[Dict] = []

    # --------- Helpers ---------
    def _prepare_texts(self, texts: List[str]) -> List[str]:
        # Cắt bớt text (tránh OOM với chunk cực dài)
        safe = []
        for t in texts:
            s = (t or "")
            if MAX_EMBED_TEXT_CHARS and len(s) > MAX_EMBED_TEXT_CHARS:
                s = s[:MAX_EMBED_TEXT_CHARS]
            safe.append(s)
        return safe

    # --------- Public API ---------
    def build(self, texts: List[str], metadatas: List[Dict]) -> None:
        """
        Build FAISS index từ văn bản & metadata.
        - Chuẩn hoá embedding (normalize=True) ⇒ dùng IndexFlatIP cho cosine.
        - Dùng batch_size=4 theo yêu cầu.
        """
        safe_texts = self._prepare_texts(texts)

        # Encode theo batch nhỏ + truncate để không bùng RAM
        embs = self.model.encode(
            safe_texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        ).astype("float32")

        # FAISS index (cosine nếu đã normalize)
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs)

        # Lưu metadata song song
        self.meta = metadatas

        # Persist
        os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
        faiss.write_index(self.index, FAISS_INDEX_PATH)
        np.save(FAISS_INDEX_PATH + ".metas.npy", np.array(self.meta, dtype=object))

    def load(self) -> None:
        """Load FAISS index + metadata từ đĩa."""
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        self.meta = np.load(FAISS_INDEX_PATH + ".meta.npy", allow_pickle=True).tolist()

    def dense_search(self, query: str, top_k: int = 10):
        """
        Tìm kiếm dense: encode query (normalize) → dot-product (cosine).
        Trả về list[(idx, score)] đã lọc i=-1.
        """
        if self.index is None:
            raise RuntimeError("FAISS index is not loaded. Call load() first.")

        q = self.model.encode(
            [query],
            batch_size=1,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

        scores, idxs = self.index.search(q, top_k)
        result = []
        for i, s in zip(idxs[0], scores[0]):
            if int(i) == -1:
                continue
            result.append((int(i), float(s)))
        return result

    def get_meta(self, i: int) -> Dict:
        if not (0 <= i < len(self.meta)):
            return {}
        return self.meta[i]
