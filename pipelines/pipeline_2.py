import json
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, util
from ultils.logger import logger
from .pipeline_1 import filter_header_path0, faiss_retrieve_top_k, filter_by_full_header_path, tokenize
from rank_bm25 import BM25Okapi
from ultils.log_chunk import log_chunk_details

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
from typing import List, Dict, Any

def filter_header_path1(question: str, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Xác định mức độ liên quan của câu hỏi đối với các nhóm tài liệu (Header/Context).
    In ra tài liệu/nhãn có điểm số cao nhất.
    """
    if not relevant_chunks:
        return []

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 1. Lấy danh sách Unique Root Headers
    unique_headers = set()
    for chunk in relevant_chunks:
        header = chunk.get("metadata", {}).get("header_path", "")
        if header:
            # Tách chuỗi theo " > " và lấy phần tử đầu tiên
            root_header = header.split(" > ")[1].strip()
            if root_header:
                unique_headers.add(root_header)
    
    unique_headers_list = list(unique_headers)
    
    if not unique_headers_list:
        return relevant_chunks

    # 2. Encode Headers và Question
    header_embeddings = model.encode(unique_headers_list, convert_to_tensor=True)
    question_embedding = model.encode(question, convert_to_tensor=True)

    # 3. Tính Cosine Similarity
    cos_scores = util.cos_sim(question_embedding, header_embeddings)[0]

    # 4. Tạo Map và Tìm Max Score
    header_score_map = {}
    best_score = -1.0

    for idx, header in enumerate(unique_headers_list):
        score = float(cos_scores[idx])
        header_score_map[header] = score
        
        # Kiểm tra xem đây có phải là điểm cao nhất không
        if score > best_score:
            best_score = score
            best_header = header
    # 5. Lọc (Filter) và Cập nhật điểm số
    filtered_chunks = []
    
    for chunk in relevant_chunks:
        # # Lấy root header của chunk hiện tại để so sánh
        # header = chunk.get("metadata", {}).get("header_path", "")
        # current_root = ""
        # if header:
        #     current_root = header.split(" > ")[1].strip()
        
        # # CHỈ GIỮ LẠI CÁC CHUNK THUỘC VỀ BEST HEADER
        # if current_root == best_header:
            
        #     # --- CẬP NHẬT ĐIỂM SỐ ---

        #     # Lưu điểm document score vào chunk
            chunk["similarity_score"]["header_path_1"] = round(best_score, 4)
            
        #     # Giữ lại chunk này
            filtered_chunks.append(chunk)
    
    return filtered_chunks
def calculate_bm25_scores(question: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tính điểm BM25 cho danh sách chunks dựa trên nội dung (content).
    Cập nhật điểm vào chunk["similarity_score"]["bm25"].
    """

    # 1. Tokenize Corpus (Tách từ cơ bản)
    # Lưu ý: Với tiếng Việt production nên dùng thư viện tách từ chuyên dụng (pyvi/underthesea)
    # Ở đây dùng split() đơn giản để đảm bảo tốc độ và không phụ thuộc thư viện ngoài
    tokenized_corpus = [chunk.get("content", "").lower().split() for chunk in chunks]
    
    # 2. Tokenize Query
    tokenized_query = question.lower().split()

    # 3. Khởi tạo BM25 & Tính điểm
    bm25 = BM25Okapi(tokenized_corpus)
    doc_scores = bm25.get_scores(tokenized_query)

    # --- CHUẨN HÓA ĐIỂM SỐ (NORMALIZE) ---
    # Tìm điểm số lớn nhất trong danh sách kết quả
    max_score = max(doc_scores) if len(doc_scores) > 0 else 0.0

    # 4. Cập nhật vào Chunk
    for idx, chunk in enumerate(chunks):
        if "similarity_score" not in chunk:
            chunk["similarity_score"] = {}
        
        raw_score = float(doc_scores[idx])
        
        # Chuẩn hóa về [0, 1] để dễ phối hợp với điểm Vector (thường là 0-1)
        # Nếu max_score = 0 (tức là không chunk nào khớp từ khóa), thì điểm tất cả là 0
        if max_score > 0:
            normalized_score = raw_score / max_score
        else:
            normalized_score = 0.0
        
        # Lưu điểm số đã chuẩn hóa
        chunk["similarity_score"]["bm25"] = round(normalized_score, 4)

    return chunks
def filter_by_full_chunks(question, relevant_chunks):
    """
    Tính điểm tương đồng giữa câu hỏi và header_path của chunk bằng Jaccard Similarity.
    Trả về 10 chunk có điểm số cao nhất.
    """
    # Tokenize câu hỏi một lần để dùng lại
    question_tokens = tokenize(question)
    
    # Duyệt qua từng chunk để tính điểm và LƯU TRỰC TIẾP vào chunk
    for chunk in relevant_chunks:
        # 1. Lấy header_path từ metadata
        chunk_content = chunk["content"]
        
        # 2. Tokenize header_path
        header_tokens = tokenize(chunk_content)
        
        # 3. Tính Jaccard Similarity: Intersection / Union
        intersection = question_tokens & header_tokens
        union = question_tokens | header_tokens
        
        # Tránh chia cho 0 nếu union rỗng
        similarity = len(intersection) / len(union) if union else 0.0
        
        # 4. QUAN TRỌNG: Khởi tạo dict similarity_score nếu chưa có
        if "similarity_score" not in chunk:
            chunk["similarity_score"] = {}
            
        # 5. QUAN TRỌNG: Lưu điểm số vào chunk
        chunk["similarity_score"]["full_chunks"] = round(similarity, 4)

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
            "full_header_path": 0.0,
            "retrieve": 0.0
        }
    # layer_1: xác định tên tài liệu chứa chunk liên quan dựa vào phần từ đầu tiên của header_path, sử dụng cosine similarity
    chunk_relevant = filter_header_path0(question, chunk_relevant)
    # layer 2: xác định tên tài liệu chứa chunk liên quan dựa vào phần từ thứ hai của header_path, sử dụng cosine similarity
    # chunk_relevant = filter_header_path1(question, chunk_relevant)
    # layer 3: tính điểm BM25 dựa trên nội dung chunk
    chunk_relevant = calculate_bm25_scores(question, chunk_relevant)
    # layer_4: xác định mức độ liên quan của chunk dựa vào full header_path, sử dụng cosine similarity
    chunk_relevant = filter_by_full_header_path(question, chunk_relevant)
    # layer_5: dùng vector search để tìm các chunk liên quan nhất, sử dụng faiss và cosine similarity
    chunk_relevant = faiss_retrieve_top_k(question, chunk_relevant)
    # layer_6: xác định mức độ liên quan của chunk dựa vào full content của chunk, sử dụng Jaccard Similarity
    chunk_relevant = filter_by_full_chunks(question, chunk_relevant)
    sorted_chunks = sorted(
        chunk_relevant, 
        key=lambda x: x.get("similarity_score", {}).get("retrieve", 0.0), 
        reverse=True
    )
    # In kết quả sau cùng
    log_chunk_details(chunk_relevant)
    return sorted_chunks