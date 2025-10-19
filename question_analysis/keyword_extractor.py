

import json
import os
from typing import List, Set
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from config.pipeline_config import VECTOR_STORE_PATH

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

def get_common_words(question: str, list_of_strings: List[str]) -> List[str]:
    """
    Trích xuất các từ chung giữa câu hỏi và danh sách string.
    """
    question_words = tokenize(question)
    common_words = set()
    for s in list_of_strings:
        s_words = tokenize(s)
        common_words.update(question_words & s_words)
    return list(common_words)

def match_labels_by_keywords(labels: List[str], keywords: List[str], threshold: float = 0.5, top_k: int = 10) -> List[str]:
    """
    So sánh mức độ tương đồng giữa label và từ khóa, trả về các label khớp nhất.
    """
    scored_labels = []
    keywords_set = set(k.lower() for k in keywords)
    for label in labels:
        label_set = set(label.lower().split())
        intersection = label_set & keywords_set
        union = label_set | keywords_set
        similarity = len(intersection) / len(union) if union else 0
        scored_labels.append((label, similarity))
    scored_labels.sort(key=lambda x: x[1], reverse=True)
    return [label for label, sim in scored_labels[:top_k]]

def extract_keywords(question: str, vector_store_path: str, top_n: int = 100, threshold: float = 0.5) -> List[str]:
    """
    Trích xuất từ khóa từ câu hỏi sử dụng KeyBERT và các phương pháp khác.
    """
    if not question or not isinstance(question, str):
        return []
    kw_model = KeyBERT(SentenceTransformer("vinai/phobert-base-v2"))
    # KeyBERT keywords
    keybert_keywords = []
    if kw_model:
        keybert_keywords = [kw[0] for kw in kw_model.extract_keywords(
            question,
            keyphrase_ngram_range=(1, 3),
            stop_words=None,
            top_n=top_n*2
        )]
    # NER keywords (spaCy) - bỏ qua nếu không có model
    ner_keywords = []
    noun_chunks = []
    # Common words
    output_chunks_path = os.path.join(vector_store_path, "vectorized_metadata.json")
    list_of_strings = get_header_paths_from_json(output_chunks_path)
    common_words = get_common_words(question, list_of_strings)
    # Gộp, loại trùng
    all_keywords = []
    for kw in ner_keywords + noun_chunks + keybert_keywords + common_words:
        kw = kw.strip()
        if kw and kw.lower() not in [k.lower() for k in all_keywords]:
            all_keywords.append(kw)
        if len(all_keywords) >= top_n:
            break
    list_labels = match_labels_by_keywords(list_of_strings, all_keywords[:top_n], threshold=threshold)
    return list_labels[:10]

# Ví dụ sử dụng
if __name__ == "__main__":
    test_q = "Ngành Mạng máy tính và truyền thông dữ liệu có học môn đại số không?"
    print(extract_keywords(test_q, VECTOR_STORE_PATH))