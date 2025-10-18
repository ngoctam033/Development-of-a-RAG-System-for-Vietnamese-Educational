# reindex_faiss.py
"""
Rebuild FAISS index directly from processed chunks (all_chunks_combined.json).
Không cần chạy lại extract/chunk/vectorize.
"""

import os
import json
import numpy as np

from rag_pipeline.indexes.faiss_store import FaissStore

try:
    from config.pipeline_config import PROCESSING_DATA_FOLDER_PATH, FAISS_INDEX_PATH
except Exception:
    PROCESSING_DATA_FOLDER_PATH = "data/processed"
    FAISS_INDEX_PATH = "data/vector_store/index.faiss"


def extract_text(c: dict) -> str:
    # Linh hoạt tên khoá nội dung tùy chunking.py
    return (
        c.get("text")
        or c.get("content")
        or c.get("chunk_text")
        or c.get("chunk")
        or ""
    )


def main():
    all_chunks_path = os.path.join(PROCESSING_DATA_FOLDER_PATH, "all_chunks_combined.json")
    if not os.path.exists(all_chunks_path):
        raise FileNotFoundError(f"Không thấy file: {all_chunks_path}. Hãy chạy main.py để tạo chunks trước.")

    with open(all_chunks_path, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    corpus_texts = [extract_text(c) for c in all_chunks]
    corpus_meta  = [{**c.get("metadata", {}), "text": extract_text(c)} for c in all_chunks]

    fs = FaissStore()
    fs.build(corpus_texts, corpus_meta)

    # (tuỳ chọn) Lưu thêm 2 mảng để CLI load nhanh
    os.makedirs(os.path.dirname(FAISS_INDEX_PATH), exist_ok=True)
    np.save(FAISS_INDEX_PATH + ".texts.npy", np.array(corpus_texts, dtype=object))
    np.save(FAISS_INDEX_PATH + ".metas.npy",  np.array(corpus_meta,  dtype=object))

    print(f"✅ Rebuilt FAISS at {FAISS_INDEX_PATH} (n={len(corpus_texts)}) with batch_size=4")


if __name__ == "__main__":
    main()
