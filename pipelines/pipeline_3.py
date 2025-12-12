import json
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer
from ultils.logger import logger
from ultils.log_chunk import log_chunk_details
from .pipeline_1 import filter_header_path0, faiss_retrieve_top_k, tokenize
from .pipeline_2 import filter_by_full_chunks, calculate_bm25_scores

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def filter_by_full_chunk_jaccard_similarity(question, relevant_chunks):
    """
    Tính điểm tương đồng giữa câu hỏi và header_path của chunk bằng Jaccard Similarity.
    Trả về 10 chunk có điểm số cao nhất.
    """
    # Tokenize câu hỏi một lần để dùng lại
    question_tokens = tokenize(question)
    
    # Duyệt qua từng chunk để tính điểm và LƯU TRỰC TIẾP vào chunk
    for chunk in relevant_chunks:
        # 1. Lấy header_path từ metadata
        header_path = chunk["content"]
        
        # 2. Tokenize header_path
        header_tokens = tokenize(header_path)
        # Danh sách stopwords tiếng Việt cơ bản (cần bổ sung thêm)
        stopwords = {'là', 'của', 'những', 'các', 'về', 'trong', 'tôi', 'muốn', 'hỏi', 'gì', 'như', 'nào'}
        
        # Lọc bỏ stopwords để chỉ giữ lại từ khóa quan trọng (keywords)
        question_tokens = {w for w in question_tokens if w not in stopwords}
        header_tokens = {w for w in header_tokens if w not in stopwords}
        
        # 3. Tính Jaccard Similarity: Intersection / Union
        intersection = question_tokens & header_tokens
        union = question_tokens | header_tokens
        
        # Tránh chia cho 0 nếu union rỗng
        similarity = len(intersection) / len(union) if union else 0.0
        
        # 4. QUAN TRỌNG: Khởi tạo dict similarity_score nếu chưa có
        if "similarity_score" not in chunk:
            chunk["similarity_score"] = {}
            
        # 5. QUAN TRỌNG: Lưu điểm số vào chunk
        chunk["similarity_score"]["full_chunk_jaccard_similarity"] = round(similarity, 4)

    return relevant_chunks
def run(question: str):
    logger.info("Question: {}".format(question))
    chunk_relevant = vector_store
    # thêm key - value để luư điểm số sau mỗi lần filter vào chunk_relevant
    for chunk in chunk_relevant:
        chunk["total_similarity_score"] = 0.0
        chunk["similarity_score"] = {
            "header_path_0": 0.0,
            "header_path_1": 0.0,
            "full_chunks": 0.0,
            "bm25": 0.0,
            "full_chunk_jaccard_similarity": 0.0,
            "full_header_path": 0.0,
            "retrieve": 0.0
        }
    # tính điểm và sắp xếp từng bước một
    chunk_relevant = sorted(
        filter_header_path0(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("header_path_0", 0.0),
        reverse=True
    )
    chunk_relevant = sorted(
        filter_by_full_chunks(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("full_chunks", 0.0),
        reverse=True
    )
    chunk_relevant = sorted(
        calculate_bm25_scores(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("bm25", 0.0),
        reverse=True
    )
    chunk_relevant = sorted(
        faiss_retrieve_top_k(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("retrieve", 0.0),
        reverse=True
    )
    chunk_relevant = sorted(
        filter_by_full_chunk_jaccard_similarity(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("full_chunk_jaccard_similarity", 0.0),
        reverse=True
    )
    # Tính tổng điểm similarity_score cho mỗi chunk
    for chunk in chunk_relevant:
        total_score = (
            chunk["similarity_score"].get("header_path_0", 0.0) +
            chunk["similarity_score"].get("full_header_path", 0.0) +
            chunk["similarity_score"].get("retrieve", 0.0) +
            chunk["similarity_score"].get("full_chunks", 0.0) +
            chunk["similarity_score"].get("bm25", 0.0) +
            chunk["similarity_score"].get("full_chunk_jaccard_similarity", 0.0)
        )
        chunk["total_similarity_score"] = round(total_score, 4)
    # In kết quả sau cùng
    log_chunk_details(chunk_relevant)
    return chunk_relevant