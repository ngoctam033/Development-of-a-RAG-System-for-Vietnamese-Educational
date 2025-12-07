
from typing import List, Dict, Any
import json
from typing import Set
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer
from ultils.logger import logger
import numpy as np
import faiss

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def tokenize(text: str) -> Set[str]:
    """
    Tách từ, chuyển về chữ thường, loại bỏ ký tự đặc biệt.
    """
    return set(word.strip('.,;:!?()[]{}"\'').lower() for word in text.split())
def get_header_paths_from_json(json_path: str) -> List[str]:
    """
    Đọc danh sách header_path từ file json.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    header_paths = []
    for item in data:
        meta = item.get("metadata", {})
        header = meta.get("header_path")
        if header:
            header_paths.append(header)
    return header_paths

def filter_by_header_path(question, relevant_chunks):
    """
    Tính điểm tương đồng giữa câu hỏi và header_path của chunk bằng Jaccard Similarity.
    Trả về 10 chunk có điểm số cao nhất.
    """
    # Tokenize câu hỏi một lần để dùng lại
    question_tokens = tokenize(question)
    
    # Duyệt qua từng chunk để tính điểm và LƯU TRỰC TIẾP vào chunk
    for chunk in relevant_chunks:
        # 1. Lấy header_path từ metadata
        header_path = chunk["metadata"].get("header_path", "")
        
        # 2. Tokenize header_path
        header_tokens = tokenize(header_path)
        
        # 3. Tính Jaccard Similarity: Intersection / Union
        intersection = question_tokens & header_tokens
        union = question_tokens | header_tokens
        
        # Tránh chia cho 0 nếu union rỗng
        similarity = len(intersection) / len(union) if union else 0.0
        
        # 4. QUAN TRỌNG: Khởi tạo dict similarity_score nếu chưa có
        if "similarity_score" not in chunk:
            chunk["similarity_score"] = {}
            
        # 5. QUAN TRỌNG: Lưu điểm số vào chunk
        chunk["similarity_score"]["header_path"] = round(similarity, 4)

    # 6. Sắp xếp danh sách dựa trên điểm số vừa lưu
    sorted_chunks = sorted(
        relevant_chunks, 
        key=lambda x: x["similarity_score"]["header_path"], 
        reverse=True
    )

    return sorted_chunks

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

    TOP_K = 10

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
            "header_path": 0.0
        }
    # step_1: filter header path
    chunk_relevant = filter_by_header_path(question, chunk_relevant)[:10]
    # step_2: faiss retrieve top k
    chunk_relevant = faiss_retrieve_top_k(question, chunk_relevant)
    # In kết quả sau cùng
    for chunk in chunk_relevant:
        clean_chunk = {
            "header_path": chunk.get("metadata", {}).get("header_path", "N/A"),
            "similarity_score": chunk.get("similarity_score", {})
        }
        pretty_result = json.dumps(clean_chunk, indent=4, ensure_ascii=False)
        logger.info(pretty_result)
    return chunk_relevant