from typing import List, Dict, Any
import numpy as np
import faiss
from utils.logger import logger
import pandas as pd

def search_similar(
    query_text: str,
    store: Dict[str, Any],
    top_k: int = 3,
    header_path_filter: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Find documents similar to the query text using FAISS, with optional header_path filtering.
    """
    model = store["embedding_model"]
    faiss_index = store["faiss_index"]
    vectorized_data = store["vectorized_data"]

    # logger.info("🔍 Bắt đầu tìm kiếm tài liệu tương tự...")

    # Nếu có header_path_filter, lọc trước vectorized_data
    if header_path_filter is not None:
        # logger.info(f"🔎 Đang lọc vector theo header_path_filtr}")
        vectorized_data = filter_vectors_by_metadata(
            vectorized_data,
            {"header_path": header_path_filter}
        )
        # logger.info(f"✅ Số vector sau khi lọc: {len(vectorized_data)}")
        # Nếu lọc xong, cần build lại faiss_index cho tập này
        embeddings = np.array([item["embedding"] for item in vectorized_data]).astype('float32')
        if len(embeddings) > 0:
            faiss_index = faiss.IndexFlatIP(embeddings.shape[1])
            faiss.normalize_L2(embeddings)
            faiss_index.add(embeddings)
            # logger.info(f"✅ Đã build lại FAISS index cho tập vector đã lọc")
        else:
            # logger.warning("⚠️ Không còn vector nào sau khi lọc, trả về rỗng.")
            return []

    # logger.info(f"🔎 Đang mã hóa query và tìm kiếm tương đồng FAISS cho: '{query_text}'")
    query_embedding = model.encode(query_text)
    query_embedding = np.array(query_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    scores, indices = faiss_index.search(query_embedding, top_k)
    # logger.info(f"✅ Đã tìm kiếm xong, trả về top {top_k} kết quả.")
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= len(vectorized_data):
            continue
        doc = vectorized_data[idx]
        results.append({
            "content": doc["content"],
            "metadata": doc["metadata"],
            "similarity_score": float(scores[0][i])
        })
        if len(results) >= top_k:
            break
    # logger.info(f"✅ Số kết quả trả về: {len(results)}")
    # for item in results:
    #     logger.info(f"🔍 Kết quả: {item['metadata']['header_path']} (Score: {item['similarity_score']})")
    return results

def filter_vectors_by_metadata(vectorized_data: List[Dict[str, Any]], metadata_filter: dict) -> List[Dict[str, Any]]:
    """
    Lọc các vector theo điều kiện metadata_filter nâng cao.
    Nếu value là str, kiểm tra chuỗi con; nếu không, so sánh bằng tuyệt đối.
    """
    # logger.info(f"🔎 Bắt đầu lọc vector với metadata_filter: {metadata_filter}")
    # Sử dụng pandas để lọc các dict trong vectorized_data theo điều kiện metadata_filter
    df = pd.DataFrame([item['metadata'] for item in vectorized_data])
    mask = pd.Series([True] * len(df))
    for k, v in metadata_filter.items():
        if k not in df.columns:
            mask = mask & False
            continue
        if isinstance(v, list):
            mask = mask & df[k].isin(v)
        elif isinstance(v, str):
            mask = mask & df[k].astype(str).str.contains(v)
        else:
            mask = mask & (df[k] == v)
    filtered_indices = df[mask].index.tolist()
    filtered = [vectorized_data[i] for i in filtered_indices]
    # logger.info(f"✅ Đã lọc xong, còn lại {len(filtered)} vector.")
    return filtered