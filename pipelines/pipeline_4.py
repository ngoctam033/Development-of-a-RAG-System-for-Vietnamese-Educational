import json
from ultils.load_vector_store import load_vector_store
from ultils.log_chunk import log_chunk_details
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, CrossEncoder, util
from ultils.logger import logger
from .pipeline_1 import faiss_retrieve_top_k
from .pipeline_2 import generate
from configs import CROSS_ENCODER_MODEL_NAME
import torch

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
from typing import List, Dict, Any

def rerank_with_cross_encoder(question: str, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sử dụng Cross-Encoder để chấm điểm lại (Rerank) và lọc danh sách chunks.
    Cross-Encoder chính xác hơn Bi-Encoder nhưng chậm hơn.
    
    Args:
        question (str): Câu hỏi của người dùng.
        relevant_chunks (list): Danh sách các chunk ứng viên
        
    Returns:
        List[Dict]: Top K chunk có điểm Cross-Encoder cao nhất.
    """

    # 1. Khởi tạo Cross-Encoder
    # 'cross-encoder/ms-marco-MiniLM-L-6-v2' là model chuẩn, nhẹ và hiệu quả.
    # Tuy nhiên, nếu muốn tối ưu cho tiếng Việt, có thể cân nhắc các model multilingual khác.
    # Nhưng MiniLM-L-6-v2 vẫn hoạt động khá tốt nhờ tính chất đa ngữ của BERT gốc.
    model = CrossEncoder(CROSS_ENCODER_MODEL_NAME)

    # 2. Chuẩn bị dữ liệu input (List of pairs)
    # Cross-Encoder yêu cầu input dạng: [['Câu hỏi', 'Văn bản 1'], ['Câu hỏi', 'Văn bản 2'], ...]
    sentence_combinations = [[question, chunk.get("content", "")] for chunk in relevant_chunks]

    # 3. Dự đoán điểm số (Predict)
    # similarity_scores sẽ là một list các số thực (logits), giá trị càng cao càng phù hợp
    similarity_scores = model.predict(sentence_combinations)

    # 4. Cập nhật điểm số vào Chunk
    for idx, score in enumerate(similarity_scores):
        chunk = relevant_chunks[idx]
        
        # Lưu raw score (logits)
        chunk["similarity_score"]["cross_encoder"] = float(score)

    # Trả về Top K chunk tốt nhất
    return relevant_chunks
def filter_by_full_header_path(question: str, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tính điểm tương đồng giữa câu hỏi và header_path của chunk bằng Cosine Similarity.
    Cập nhật điểm số vào chunk["similarity_score"]["header_path"] và trả về 10 chunk cao nhất.
    """
    # 2. Lấy danh sách Unique Header Paths (để tối ưu hóa tốc độ encode)
    unique_headers = set()
    for chunk in relevant_chunks:
        # Lấy header_path từ metadata, xử lý an toàn nếu key không tồn tại
        header = chunk.get("metadata", {}).get("header_path", "")
        if header:
            unique_headers.add(header)
    
    unique_headers_list = list(unique_headers)

    # 3. Encode (Mã hóa vector)
    # Encode danh sách header
    header_embeddings = model.encode(unique_headers_list, convert_to_tensor=True)
    # Encode câu hỏi
    question_embedding = model.encode(question, convert_to_tensor=True)

    # 4. Tính Cosine Similarity
    # util.cos_sim trả về ma trận (1, n_headers), lấy [0] để được vector điểm số tương ứng
    cos_scores = util.cos_sim(question_embedding, header_embeddings)[0]

    # 5. Tạo Map: Header Path -> Score để tra cứu nhanh
    header_score_map = {}
    for idx, header in enumerate(unique_headers_list):
        header_score_map[header] = float(cos_scores[idx])

    # 6. Cập nhật điểm số vào từng Chunk
    for chunk in relevant_chunks:
        header_path = chunk.get("metadata", {}).get("header_path", "")
        
        # Lấy điểm từ map (mặc định 0.0 nếu không tìm thấy)
        score = header_score_map.get(header_path, 0.0)
            
        # Lưu điểm số header_path
        chunk["similarity_score"]["full_header_path"] = round(score, 4)

    return relevant_chunks
def filter_by_keywords(question: str, relevant_chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Lọc các chunk dựa trên độ tương đồng giữa 'danh sách từ khóa' (từ LLM) và nội dung chunk.
    Sử dụng cosine similarity với chiến lược Max Pooling (lấy điểm cao nhất trong các từ khóa).
    """

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # 1. Trích xuất từ khóa bằng LLM (Giả lập)
    # extracted_keywords là một LIST các string, ví dụ: ["tuyển sinh", "đối tượng", "đại học"]
    keywords = generate(prompt=question)
    for key in keywords:
        logger.info("Generated response: {}".format(key))
    # 2. Chuẩn bị danh sách header_path để so sánh (Thay vì content)
    chunk_headers = [chunk.get("metadata", {}).get("header_path", "") for chunk in relevant_chunks]

    # 3. Encode Keywords (List) và Chunk Contents
    # chunk_embeddings shape: [num_chunks, embedding_dim]
    chunk_embeddings = model.encode(chunk_headers, convert_to_tensor=True)
    
    # keyword_embeddings shape: [num_keywords, embedding_dim]
    keyword_embeddings = model.encode(keywords, convert_to_tensor=True)

    # 4. Tính Cosine Similarity
    # Kết quả là ma trận [num_keywords, num_chunks]
    # cos_scores[i][j] là độ tương đồng giữa keyword[i] và chunk[j]
    cos_scores = util.cos_sim(keyword_embeddings, chunk_embeddings)

    # 5. Tính điểm tổng hợp cho từng Chunk
    # Chiến lược: Max Pooling. 
    # Một chunk được coi là relevant nếu nó khớp tốt với ÍT NHẤT MỘT từ khóa quan trọng.
    # Lấy max theo trục 0 (dọc theo các keywords) -> kết quả là tensor [num_chunks] chứa điểm cao nhất
    max_scores, _ = torch.max(cos_scores, dim=0)

    # Chuyển về list float để xử lý
    chunk_scores_list = max_scores.tolist()

    # 6. Gán điểm (Không sort, không filter top_k)
    for idx, chunk in enumerate(relevant_chunks):
        score = chunk_scores_list[idx]
        
        # Lưu điểm match keyword vào
        chunk["similarity_score"]["keyword_match"] = round(score, 4)

    logger.info(f"Keyword Scoring: Updated scores for {len(relevant_chunks)} chunks.")

    # Trả về nguyên danh sách chunks với điểm số mới
    return relevant_chunks
def run(question: str):
    logger.info("Question: {}".format(question))
    chunk_relevant = vector_store
    # thêm key - value để luư điểm số sau mỗi lần filter vào chunk_relevant
    for chunk in chunk_relevant:
        chunk["total_similarity_score"] = 0.0
        chunk["similarity_score"] = {
            "full_header_path": 0.0,
            "retrieve": 0.0,
            "cross_encoder": 0.0,
            "keyword_match": 0.0
        }
    chunk_relevant = sorted(
        faiss_retrieve_top_k(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("retrieve", 0.0),
        reverse=True
    )[:100]
    # tính điểm và sắp xếp từng bước một
    chunk_relevant = sorted(
        filter_by_full_header_path(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("full_header_path", 0.0),
        reverse=True
    )[:50]
    chunk_relevant = sorted(
        filter_by_keywords(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("keyword_match", 0.0),
        reverse=True
    )[:30]
    chunk_relevant = sorted(
        rerank_with_cross_encoder(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("cross_encoder", 0.0),
        reverse=True
    )[:10]
    # Tính tổng điểm similarity_score cho mỗi chunk
    for chunk in chunk_relevant:
        total_score = (
            # chunk["similarity_score"].get("header_path_0", 0.0) +
            chunk["similarity_score"].get("full_header_path", 0.0) +
            chunk["similarity_score"].get("retrieve", 0.0) +
            chunk["similarity_score"].get("keyword_match", 0.0) +
            chunk["similarity_score"].get("cross_encoder", 0.0)
        )
        chunk["total_similarity_score"] = round(total_score, 4)
    chunk_relevant = chunk_relevant[:10]
    # In kết quả sau cùng
    log_chunk_details(chunk_relevant)
    return chunk_relevant