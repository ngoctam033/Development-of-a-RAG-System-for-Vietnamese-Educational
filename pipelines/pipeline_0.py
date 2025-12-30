
from typing import List, Dict, Any
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer
from ultils.logger import logger
import numpy as np
import faiss
from ultils.log_chunk import log_chunk_details

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def faiss_retrieve_top_k(
    query: str,
    vectorized_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm tài liệu tương đồng với câu truy vấn.
    Hàm này tự khởi tạo model, xây dựng FAISS index và thực hiện tìm kiếm.
    
    Args:
        query (str): Câu truy vấn của người dùng.
        vectorized_data (list): Danh sách dữ liệu (cần chứa key 'embedding' hoặc 'content').
        
    Returns:
        List[Dict]: Danh sách các chunk tương đồng nhất kèm điểm số.
    """

    TOP_K = 100

    corpus_embeddings = np.array([item["embedding"] for item in vectorized_data], dtype='float32')

    # 3. Xây dựng FAISS Index (In-memory)
    # Chuẩn hóa L2 cho Corpus để dùng Inner Product tương đương Cosine Similarity
    faiss.normalize_L2(corpus_embeddings)
    
    dimension = corpus_embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(dimension) # Inner Product
    faiss_index.add(corpus_embeddings)

    # 4. Xử lý Query
    query_embedding = model.encode(query)
    query_embedding = np.array(query_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    # 5. Tìm kiếm
    # Đảm bảo top_k không lớn hơn số lượng data
    actual_k = min(TOP_K, len(vectorized_data))
    scores, indices = faiss_index.search(query_embedding, actual_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx == -1 or idx >= len(vectorized_data):
            continue

        chunk = vectorized_data[idx]
        
        score_val = float(scores[0][i])
            
        # 2. Gán điểm số vào 'retrieve'
        chunk["similarity_score"]["retrieve"] = score_val
        
        # Thêm chunk (đã được chỉnh sửa) vào danh sách trả về
        results.append(chunk)

    return results

def run(question: str):
    logger.info("Question: {}".format(question))
    chunk_relevant = vector_store
    # thêm key - value để luư điểm số sau mỗi lần filter vào chunk_relevant
    for chunk in chunk_relevant:
        chunk["total_similarity_score"] = 0.0
        chunk["similarity_score"] = {
            "retrieve": 0.0
        }
    chunk_relevant = faiss_retrieve_top_k(question, chunk_relevant)
    for chunk in chunk_relevant:
        # total_score bằng document_score*0.7 + header_path*0.2 + retrieve*0.1
        total_score = (
            chunk["similarity_score"].get("retrieve", 0.0)
        )
        chunk["total_similarity_score"] = round(total_score, 4)
    # Sắp xếp lại chunk_relevant theo tổng điểm similarity_score từ cao đến thấp
    chunk_relevant.sort(key=lambda x: x["total_similarity_score"], reverse=True)
    # trả về top 10 chunk liên quan nhất
    chunk_relevant = chunk_relevant[:10]
    log_chunk_details(chunk_relevant)
    return chunk_relevant