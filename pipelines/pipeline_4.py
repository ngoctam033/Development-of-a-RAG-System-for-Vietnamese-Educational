import json
from ultils.load_vector_store import load_vector_store
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, CrossEncoder
from ultils.logger import logger
from .pipeline_1 import filter_header_path0, faiss_retrieve_top_k, filter_by_full_header_path
from .pipeline_2 import filter_by_full_chunks, calculate_bm25_scores
from .pipeline_3 import filter_by_full_chunk_jaccard_similarity
from configs import CROSS_ENCODER_MODEL_NAME

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
            "retrieve": 0.0,
            "cross_encoder": 0.0
        }
    # tính điểm và sắp xếp từng bước một
    chunk_relevant = sorted(
        filter_header_path0(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("header_path_0", 0.0),
        reverse=True
    )
    chunk_relevant = sorted(
        filter_by_full_header_path(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("full_header_path", 0.0),
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
    chunk_relevant = sorted(
        rerank_with_cross_encoder(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("cross_encoder", 0.0),
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
            chunk["similarity_score"].get("full_chunk_jaccard_similarity", 0.0) +
            chunk["similarity_score"].get("cross_encoder", 0.0)
        )
        chunk["total_similarity_score"] = round(total_score, 4)
    chunk_relevant = chunk_relevant[:10]
    # In kết quả sau cùng
    for chunk in chunk_relevant:
        clean_chunk = {
            "header_path": chunk.get("metadata", {}).get("header_path", "N/A"),
            "chunk_index": chunk.get("metadata", {}).get("chunk_index", "N/A"),
            "total_similarity_score": chunk.get("total_similarity_score", 0.0),
            "similarity_score": chunk.get("similarity_score", {})
        }
        pretty_result = json.dumps(clean_chunk, indent=4, ensure_ascii=False)
        logger.info(pretty_result)
    return chunk_relevant