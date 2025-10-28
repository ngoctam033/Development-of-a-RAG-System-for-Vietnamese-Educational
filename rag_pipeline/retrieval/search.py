from typing import List, Dict, Any
import numpy as np
import faiss
from utils.logger import logger

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

    # Nếu có header_path_filter, lọc trước vectorized_data
    if header_path_filter is not None:
        # logger.info(f"🔎 Đang lọc vector theo header_path_filter: {header_path_filter}")
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
            logger.info(f"✅ Đã build lại FAISS index cho tập vector đã lọc")
        else:
            logger.warning("⚠️ Không còn vector nào sau khi lọc, trả về rỗng.")
            return []

    logger.info(f"🔎 Đang mã hóa query và tìm kiếm tương đồng FAISS cho: '{query_text}'")
    query_embedding = model.encode(query_text)
    query_embedding = np.array(query_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    scores, indices = faiss_index.search(query_embedding, top_k)
    logger.info(f"✅ Đã tìm kiếm xong, trả về top {top_k} kết quả.")
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
    logger.info(f"✅ Số kết quả trả về: {len(results)}")
    return results

def filter_vectors_by_metadata(vectorized_data: List[Dict[str, Any]], metadata_filter: dict) -> List[Dict[str, Any]]:
    """
    Lọc các vector theo điều kiện metadata_filter nâng cao.
    Nếu value là str, kiểm tra chuỗi con; nếu không, so sánh bằng tuyệt đối.
    """
    # logger.info(f"🔎 Bắt đầu lọc vector với metadata_filter: {metadata_filter}")
    filtered = []
    for item in vectorized_data:
        # logger.info(f"Checking item with metadata: {item['metadata']}")
        meta = item["metadata"]
        match = True
        for k, v in metadata_filter.items():
            meta_value = meta.get(k)
            # logger.info(f"Comparing metadata key '{k}': filter value '{v}' with item value '{meta_value}'")
            if isinstance(v, list):
                # Nếu v là list, kiểm tra meta_value có nằm trong list v
                if meta_value not in v:
                    match = False
                    break
            elif isinstance(v, str) and isinstance(meta_value, str):
                # Nếu v là string, kiểm tra chuỗi con
                if v not in meta_value:
                    match = False
                    break
            else:
                # So sánh tuyệt đối
                if meta_value != v:
                    match = False
                    break
        if match:
            filtered.append(item)
    logger.info(f"✅ Đã lọc xong, còn lại {len(filtered)} vector.")
    return filtered