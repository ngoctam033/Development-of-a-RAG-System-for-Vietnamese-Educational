from typing import List, Dict, Any
import numpy as np
import faiss

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

    query_embedding = model.encode(query_text)
    query_embedding = np.array(query_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    scores, indices = faiss_index.search(query_embedding, top_k)  # Lấy nhiều hơn để filter
    results = []
    for i, idx in enumerate(indices[0]):
        doc = vectorized_data[idx]
        header_path = doc["metadata"].get("header_path")
        if header_path_filter is None or header_path in header_path_filter:
            results.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "similarity_score": float(scores[0][i])
            })
        if len(results) >= top_k:
            break
    return results