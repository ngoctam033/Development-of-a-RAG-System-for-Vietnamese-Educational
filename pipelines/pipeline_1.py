
from typing import List, Dict, Any
from typing import Set
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, util
from ultils.logger import logger
from .pipeline_0 import faiss_retrieve_top_k
from ultils.log_chunk import log_chunk_details
from ultils.get_data import extract_header_paths

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

def tokenize(text: str) -> Set[str]:
    """
    Tách từ, chuyển về chữ thường, loại bỏ ký tự đặc biệt.
    """
    return set(word.strip('.,;:!?()[]{}"\'').lower() for word in text.split())

def filter_by_full_header_path_jaccard_similarity(question, relevant_chunks):
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
        # Danh sách stopwords tiếng Việt cơ bản (cần bổ sung thêm)
        stopwords = {'là', 'của', 'những', 'các', 'về', 'trong', 'tôi', 'muốn', 'hỏi', 'gì', 'như', 'nào', '*', '>'}
        
        # Lọc bỏ stopwords để chỉ giữ lại từ khóa quan trọng (keywords)
        question_tokens = {w for w in question_tokens if w not in stopwords}
        header_tokens = {w for w in header_tokens if w not in stopwords}
        
        # 3. Tính Jaccard Similarity: Intersection / Union
        intersection = question_tokens & header_tokens
        union = question_tokens | header_tokens
        
        # Tránh chia cho 0 nếu union rỗng
        similarity = len(intersection) / len(union) if union else 0.0
            
        # 5. QUAN TRỌNG: Lưu điểm số vào chunk
        chunk["similarity_score"]["full_header_path_jaccard"] = round(similarity, 4)

    return relevant_chunks

def filter_header_path0(question: str, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            root_header = header.split(" > ")[0].strip()
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
        # Lấy root header của chunk hiện tại để so sánh
        header = chunk.get("metadata", {}).get("header_path", "")
        current_root = ""
        if header:
             current_root = header.split(" > ")[0].strip()
        
        # CHỈ GIỮ LẠI CÁC CHUNK THUỘC VỀ BEST HEADER
        if current_root == best_header:
            
             # --- CẬP NHẬT ĐIỂM SỐ ---

        #     # Lưu điểm document score vào chunk
            chunk["similarity_score"]["header_path_0"] = round(best_score, 4)
            
             # Giữ lại chunk này
            filtered_chunks.append(chunk)
    
    return filtered_chunks

def run(question: str):
    logger.info("Question: {}".format(question))
    chunk_relevant = vector_store
    # thêm key - value để luư điểm số sau mỗi lần filter vào chunk_relevant
    for chunk in chunk_relevant:
        chunk["total_similarity_score"] = 0.0
        chunk["similarity_score"] = {
            "header_path_0": 0.0,
            "full_header_path": 0.0,
            "retrieve": 0.0
        }
    # layer_1: xác định tên tài liệu chứa chunk liên quan dựa vào phần từ đầu tiên của header_path, sử dụng cosine similarity
    chunk_relevant = filter_header_path0(question, chunk_relevant)
    # layer_2: xác định mức độ liên quan của chunk dựa vào full header_path, sử dụng cosine similarity
    chunk_relevant = filter_by_full_header_path_jaccard_similarity(question, chunk_relevant)
    # layer_3: dùng vector search để tìm các chunk liên quan nhất, sử dụng faiss và cosine similarity
    chunk_relevant = faiss_retrieve_top_k(question, chunk_relevant)
    # Tính tổng điểm similarity_score cho mỗi chunk
    for chunk in chunk_relevant:
        # total_score bằng document_score*0.7 + header_path*0.2 + retrieve*0.1
        total_score = (
            chunk["similarity_score"].get("header_path_0", 0.0) * 0.5847 +
            chunk["similarity_score"].get("full_header_path", 0.0) * 0.2217 +
            chunk["similarity_score"].get("retrieve", 0.0) * 0.1937
        )
        chunk["total_similarity_score"] = round(total_score, 4)
    # Sắp xếp lại chunk_relevant theo tổng điểm similarity_score từ cao đến thấp
    chunk_relevant.sort(key=lambda x: x["total_similarity_score"], reverse=True)
    # trả về top 10 chunk liên quan nhất
    chunk_relevant = chunk_relevant[:10]
    log_chunk_details(chunk_relevant)
    return chunk_relevant