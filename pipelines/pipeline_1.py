
from typing import List, Dict, Any
import json
from typing import Set
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, util
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

def filter_by_full_header_path(question, relevant_chunks):
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
        
        # 4. QUAN TRỌNG: Khởi tạo dict similarity_score nếu chưa có
        if "similarity_score" not in chunk:
            chunk["similarity_score"] = {}
            
        # 5. QUAN TRỌNG: Lưu điểm số vào chunk
        chunk["similarity_score"]["full_header_path"] = round(similarity, 4)

    return relevant_chunks

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

    TOP_K = len(vectorized_data)

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
    chunk_relevant = filter_by_full_header_path(question, chunk_relevant)
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
    for chunk in chunk_relevant:
        clean_chunk = {
            "header_path": chunk.get("metadata", {}).get("header_path", "N/A"),
            "total_similarity_score": chunk.get("total_similarity_score", 0.0),
            "similarity_score": chunk.get("similarity_score", {})
        }
        pretty_result = json.dumps(clean_chunk, indent=4, ensure_ascii=False)
        logger.info(pretty_result)
    return chunk_relevant