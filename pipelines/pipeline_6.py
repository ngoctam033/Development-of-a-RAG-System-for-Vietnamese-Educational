import json
from ultils.load_vector_store import load_vector_store
from ultils.log_chunk import log_chunk_details
from configs import EMBEDDING_MODEL_NAME
from sentence_transformers import SentenceTransformer, util
from ultils.logger import logger
from .pipeline_1 import faiss_retrieve_top_k, filter_by_full_header_path
from .pipeline_2 import generate
from .pipeline_4 import rerank_with_cross_encoder
from render_prompt import render_prompt
from render_prompt import PROMPT_TEMPLATES

vector_store = load_vector_store()
model = SentenceTransformer(EMBEDDING_MODEL_NAME)
from typing import List, Dict, Any

def filter_by_keywords(question: str, relevant_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Lọc các chunk dựa trên độ tương đồng giữa 'danh sách từ khóa' (từ LLM) và nội dung chunk.
    Sử dụng cosine similarity với chiến lược Max Pooling (lấy điểm cao nhất trong các từ khóa).
    """

    # 1. Trích xuất từ khóa bằng LLM (Giả lập)
    # extracted_keywords là một LIST các string, ví dụ: ["tuyển sinh", "đối tượng", "đại học"]
    keywords = generate(prompt=question)
    logger.info(keywords)
    # 2. Chuẩn bị danh sách header_path và tách thành các header con
    # chunk_headers_parsed sẽ chứa list các list header con
    chunk_headers_parsed = set()

    for chunk in relevant_chunks:
        header_path = chunk.get("metadata", {}).get("header_path", "")
        
        # Tách chuỗi header_path thành list các header con theo ký tự ">"
        if header_path:
            # split(">") tách chuỗi, strip() xóa khoảng trắng thừa ở 2 đầu mỗi phần
            # if h.strip() giúp loại bỏ các phần tử rỗng nếu có
            sub_headers = [h.strip() for h in header_path.lower().split(">") if h.strip()]
            
        chunk_headers_parsed.update(sub_headers)
    chunk_headers_parsed = list(chunk_headers_parsed)

    # 4. Encode Keywords và Headers
    # kw_embeddings shape: [num_keywords, embedding_dim]
    kw_embeddings = model.encode(keywords, convert_to_tensor=True)
    
    # header_embeddings shape: [num_headers, embedding_dim]
    header_embeddings = model.encode(chunk_headers_parsed, convert_to_tensor=True)

    # 5. Tính Cosine Similarity & Lấy Top K
    # semantic_search trả về list các list result (mỗi list con ứng với 1 query/keyword)
    # Top 10 header cho mỗi keyword
    search_results = util.semantic_search(kw_embeddings, header_embeddings, top_k=10)
    logger.info(search_results)
    keyword_header_matches = {}

    for i, result_list in enumerate(search_results):
        current_keyword = keywords[i]
        top_matches = []
        
        for res in result_list:
            idx = res['corpus_id']
            score = res['score']
            header_text = chunk_headers_parsed[idx]
            
            match_info = {
                "header": header_text,
                "score": round(score, 4)
            }
            top_matches.append(match_info)
            
        keyword_header_matches[current_keyword] = top_matches
    # --- LỌC TRÙNG HEADER ---
    # Lấy tất cả các header từ các value của keyword_header_matches đưa vào một set
    unique_matched_headers_set = set()
    for matches_list in keyword_header_matches.values():
        for match_item in matches_list:
            # match_item là dict {'header': ..., 'score': ...}, ta lấy giá trị header
            unique_matched_headers_set.add(match_item["header"])
    
    # Chuyển về set để tối ưu hóa việc tra cứu (lookup)
    matched_headers_lookup = unique_matched_headers_set
    # In ra danh sách header tương đồng tìm được
    logger.info(f"--- LIST MATCHED HEADERS: {matched_headers_lookup}")
    # --- TÍNH ĐIỂM VÀ SẮP XẾP CHUNK ---
    for chunk in relevant_chunks:
        raw_path = chunk.get("metadata", {}).get("header_path", "")
        
        match_count = 0
        current_path_nodes = []

        if raw_path:
            # Tách node của path hiện tại (chuẩn hóa lower)
            current_path_nodes = [h.strip() for h in raw_path.lower().split(">") if h.strip()]
            
            # Tính giao giữa các node trong path và các node đã match với keyword
            intersection = set(current_path_nodes).intersection(matched_headers_lookup)
            match_count = len(intersection)
            
        chunk["similarity_score"]["keyword_match"] = match_count

    return relevant_chunks
def header_path_generator(question: str, relevant_chunks: List[Dict[str, Any]]):
    prompt = render_prompt(
        PROMPT_TEMPLATES["header_path_generator"]["template"],
        fields=PROMPT_TEMPLATES["header_path_generator"]["fields"],
        values={
            "user_query": question
        }
    )
    llm_output = generate(prompt)
    # --- LOGIC NỐI LIST THÀNH CHUỖI ---
    if isinstance(llm_output, list):
        # Nối các phần tử trong list bằng dấu " > "
        llm_predicted_path = " > ".join([str(item) for item in llm_output])
    logger.info(llm_predicted_path)
    # 3. Vector Search: So sánh Predicted Path vs Actual Paths
    
    # Encode Header Path dự đoán của LLM
    pred_embedding = model.encode(llm_predicted_path, convert_to_tensor=True)
    
    # Lấy danh sách Header Path thực tế từ các chunk
    # Nếu chunk không có header_path, dùng chuỗi rỗng
    chunk_headers = [chunk.get("metadata", {}).get("header_path", "") for chunk in relevant_chunks]
    
    # Encode danh sách Header Path thực tế
    chunk_embeddings = model.encode(chunk_headers, convert_to_tensor=True)

    # Tính Cosine Similarity
    # Kết quả là tensor chứa điểm số tương đồng
    cos_scores = util.cos_sim(pred_embedding, chunk_embeddings)[0]

    # 4. Cập nhật điểm số và Sắp xếp
    for idx, chunk in enumerate(relevant_chunks):
        score = float(cos_scores[idx])
        
        chunk["similarity_score"]["llm_path_similarity"] = round(score, 4)
    
    # Trả về danh sách chunk đã sắp xếp (thay vì chỉ trả về response text)
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
        filter_by_keywords(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("keyword_match", 0.0),
        reverse=True
    )[:100]
    chunk_relevant = sorted(
        filter_by_full_header_path(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("keyword_match", 0.0),
        reverse=True
    )[:70]
    chunk_relevant = sorted(
        faiss_retrieve_top_k(question, chunk_relevant),
        key=lambda x: x.get("similarity_score", {}).get("retrieve", 0.0),
        reverse=True
    )[:50]
    chunk_relevant = sorted(
        header_path_generator(question, chunk_relevant),
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