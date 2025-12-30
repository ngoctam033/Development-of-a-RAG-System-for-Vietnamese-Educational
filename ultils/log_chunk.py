from .logger import logger
from typing import List, Dict, Any
import json
from .get_data import extract_header_paths

def log_chunk_details(chunk_relevant: List[Dict[str, Any]]):
    """
    Hàm tiện ích để in ra log thông tin tóm tắt của các chunk (Header, Index, Scores).
    Giúp debug dễ dàng hơn bằng cách loại bỏ nội dung text dài dòng.
    
    Args:
        chunk_relevant: Danh sách các chunk cần in thông tin.
    """
    if not chunk_relevant:
        return
    tree_header_path = extract_header_paths(chunk_relevant)
    logger.info(tree_header_path)

    for chunk in chunk_relevant:
        # Trích xuất các thông tin quan trọng cần hiển thị
        clean_chunk = {
            "header_path": chunk.get("metadata", {}).get("header_path", "N/A"),
            "chunk_index": chunk.get("metadata", {}).get("chunk_index", -1),
            "total_similarity_score": chunk.get("total_similarity_score", 0.0),
            "similarity_score": chunk.get("similarity_score", {})
        }
        
        # Chuyển đổi sang chuỗi JSON định dạng đẹp
        pretty_result = json.dumps(clean_chunk, indent=4, ensure_ascii=False)
        
        # Ghi log (Sử dụng logger nếu có, nếu không thì print)
        try:
            logger.info(pretty_result)
        except ImportError:
            print(pretty_result)