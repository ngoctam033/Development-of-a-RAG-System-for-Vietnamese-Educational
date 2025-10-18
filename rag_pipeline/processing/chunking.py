"""
Chunking Module: Phân chia markdown thành các chunks để vectorization

Module này chịu trách nhiệm:
- Đọc markdown content từ file
- Phân chia theo chapters và sections
- Trích xuất headers và metadata
- Tạo chunks có cấu trúc cho vectorization
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional

from utils.logger import logger


def read_markdown_file(file_path: str) -> str:
    """
    Đọc nội dung markdown từ file
    
    Args:
        file_path: Đường dẫn đến file markdown
        
    Returns:
        Nội dung markdown dưới dạng string
        
    Raises:
        FileNotFoundError: Nếu file không tồn tại
        IOError: Nếu có lỗi khi đọc file
    """
    logger.info(f"Đang đọc file markdown: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File không tồn tại: {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        
        logger.info(f"Đã đọc thành công {len(content)} ký tự từ file")
        return content
        
    except IOError as e:
        logger.error(f"Lỗi khi đọc file {file_path}: {str(e)}")
        raise


def split_markdown_into_chapters(markdown_content: str) -> List[str]:
    """
    Phân chia markdown thành các chapters
    
    Args:
        markdown_content: Nội dung markdown đầy đủ
        
    Returns:
        List các chapter strings
    """
    logger.info("Phân chia markdown thành chapters...")
    
    # Phân chia theo các section bắt đầu bằng # I., # II., # III., etc.
    chapters = re.split(r'(?=# [IVX]+\.)', markdown_content)
    
    # Loại bỏ chapter rỗng
    chapters = [chapter.strip() for chapter in chapters if chapter.strip()]
    
    logger.info(f"Đã tìm thấy {len(chapters)} chapters")
    return chapters


def extract_header_info(line: str) -> Tuple[int, str]:
    """
    Trích xuất thông tin header từ một dòng
    
    Args:
        line: Dòng text cần phân tích
        
    Returns:
        Tuple (header_level, header_text)
        - header_level: Cấp độ header (1-6)
        - header_text: Text của header (đã loại bỏ #)
    """
    if not re.match(r'^#{1,6}\s+', line):
        return 0, ""
    
    header_match = re.match(r'^(#+)', line)
    header_level = len(header_match.group(1))
    header_text = line.lstrip('#').strip()
    
    return header_level, header_text


def update_headers_hierarchy(current_headers: Dict[str, str], header_level: int, header_text: str) -> Dict[str, str]:
    """
    Cập nhật hierarchy của headers dựa trên level mới
    
    Args:
        current_headers: Dict chứa headers hiện tại
        header_level: Cấp độ header mới
        header_text: Text của header mới
        
    Returns:
        Dict headers đã được cập nhật
    """
    # Copy để tránh mutate original dict
    updated_headers = current_headers.copy()
    
    if header_level == 1:  # # Chapter title
        updated_headers["chapter_title"] = header_text
        updated_headers["section_title"] = ""
        updated_headers["subsection_title"] = ""
        updated_headers["subsubsection_title"] = ""
    elif header_level == 2:  # ## Section title
        updated_headers["section_title"] = header_text
        updated_headers["subsection_title"] = ""
        updated_headers["subsubsection_title"] = ""
    elif header_level == 3:  # ### Subsection title
        updated_headers["subsection_title"] = header_text
        updated_headers["subsubsection_title"] = ""
    elif header_level == 4:  # #### Subsubsection title
        updated_headers["subsubsection_title"] = header_text
    
    return updated_headers


def create_header_path(headers: Dict[str, str]) -> str:
    """
    Tạo header path từ hierarchy của headers
    
    Args:
        headers: Dict chứa các headers
        
    Returns:
        String header path được nối bằng " > "
    """
    path_components = [
        headers.get("chapter_title", ""),
        headers.get("section_title", ""),
        headers.get("subsection_title", ""),
        headers.get("subsubsection_title", "")
    ]
    
    return " > ".join(filter(None, path_components))


def create_chunk_metadata(chapter_idx: int, headers: Dict[str, str]) -> Dict[str, any]:
    """
    Tạo metadata cho một chunk
    
    Args:
        chapter_idx: Index của chapter
        headers: Dict chứa headers hiện tại
        
    Returns:
        Dict metadata hoàn chỉnh
    """
    return {
        "chapter_idx": chapter_idx,
        "chapter": chapter_idx + 1,
        "chapter_title": headers.get("chapter_title", ""),
        "section_title": headers.get("section_title", ""),
        "subsection_title": headers.get("subsection_title", ""),
        "subsubsection_title": headers.get("subsubsection_title", ""),
        "header_path": create_header_path(headers)
    }


def process_content_buffer(content_buffer: List[str], chapter_idx: int, headers: Dict[str, str]) -> Optional[Dict[str, any]]:
    """
    Xử lý content buffer và tạo chunk nếu có nội dung
    
    Args:
        content_buffer: List các dòng content
        chapter_idx: Index của chapter
        headers: Dict headers hiện tại
        
    Returns:
        Dict chunk hoặc None nếu không có content
    """
    if not content_buffer:
        return None
    
    content = "\n".join(content_buffer).strip()
    if not content:
        return None
    
    return {
        "content": content,
        "metadata": create_chunk_metadata(chapter_idx, headers)
    }


def process_single_chapter(chapter: str, chapter_idx: int) -> List[Dict[str, any]]:
    """
    Xử lý một chapter và trích xuất các chunks
    
    Args:
        chapter: Nội dung chapter
        chapter_idx: Index của chapter
        
    Returns:
        List các chunks từ chapter này
    """
    logger.debug(f"Xử lý chapter {chapter_idx + 1}")
    
    chapter_lines = chapter.strip().split('\n')
    current_headers = {}
    content_buffer = []
    chunks = []
    
    for line in chapter_lines:
        header_level, header_text = extract_header_info(line)
        
        if header_level > 0:  # Là header
            # Lưu content buffer hiện tại nếu có
            chunk = process_content_buffer(content_buffer, chapter_idx, current_headers)
            if chunk:
                chunks.append(chunk)
            
            # Reset buffer và cập nhật headers
            content_buffer = []
            current_headers = update_headers_hierarchy(current_headers, header_level, header_text)
            
        else:  # Là content
            content_buffer.append(line)
    
    # Xử lý content buffer cuối cùng
    chunk = process_content_buffer(content_buffer, chapter_idx, current_headers)
    if chunk:
        chunks.append(chunk)
    
    logger.debug(f"Chapter {chapter_idx + 1}: tạo {len(chunks)} chunks")
    return chunks


def process_all_chapters(chapters: List[str]) -> List[Dict[str, any]]:
    """
    Xử lý tất cả chapters và tạo danh sách chunks
    
    Args:
        chapters: List các chapter strings
        
    Returns:
        List tất cả chunks từ tất cả chapters
    """
    logger.info("Bắt đầu xử lý tất cả chapters...")
    
    all_chunks = []
    for chapter_idx, chapter in enumerate(chapters):
        chapter_chunks = process_single_chapter(chapter, chapter_idx)
        all_chunks.extend(chapter_chunks)
    
    logger.info(f"Đã tạo tổng cộng {len(all_chunks)} chunks từ {len(chapters)} chapters")
    return all_chunks


def save_chunks_to_json(chunks: List[Dict[str, any]], output_path: str) -> bool:
    """
    Lưu chunks ra file JSON
    
    Args:
        chunks: List các chunks
        output_path: Đường dẫn file output
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    logger.info(f"Lưu {len(chunks)} chunks vào file: {output_path}")
    
    try:
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(chunks, file, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã lưu thành công chunks vào {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Lỗi khi lưu file {output_path}: {str(e)}")
        return False


def chunk_markdown_file(input_file_path: str, output_file_path: str = "vectorization_data.json") -> List[Dict[str, any]]:
    """
    Pipeline hoàn chỉnh để chunk markdown file
    
    Args:
        input_file_path: Đường dẫn file markdown input
        output_file_path: Đường dẫn file JSON output
        
    Returns:
        List các chunks đã tạo
        
    Raises:
        FileNotFoundError: Nếu input file không tồn tại
        IOError: Nếu có lỗi đọc/ghi file
    """
    logger.info("Bắt đầu chunking pipeline")
    
    # Bước 1: Đọc markdown file
    markdown_content = read_markdown_file(input_file_path)
    
    # Bước 2: Phân chia thành chapters
    chapters = split_markdown_into_chapters(markdown_content)
    
    # Bước 3: Xử lý từng chapter để tạo chunks
    chunks = process_all_chapters(chapters)
    
    # Bước 4: Lưu chunks ra file JSON
    save_success = save_chunks_to_json(chunks, output_file_path)
    
    if not save_success:
        logger.warning("Có lỗi khi lưu file, nhưng chunks vẫn được trả về")
    
    logger.info(f"Chunking pipeline hoàn tất: {len(chunks)} chunks")
    return chunks


# Utility function để test và debug
def analyze_chunk_statistics(chunks: List[Dict[str, any]]) -> Dict[str, any]:
    """
    Phân tích thống kê về chunks
    
    Args:
        chunks: List các chunks
        
    Returns:
        Dict chứa thống kê
    """
    if not chunks:
        return {"total_chunks": 0}
    
    content_lengths = [len(chunk["content"]) for chunk in chunks]
    chapters = set(chunk["metadata"]["chapter"] for chunk in chunks)
    
    stats = {
        "total_chunks": len(chunks),
        "total_chapters": len(chapters),
        "avg_content_length": sum(content_lengths) / len(content_lengths),
        "min_content_length": min(content_lengths),
        "max_content_length": max(content_lengths),
        "total_characters": sum(content_lengths)
    }
    
    logger.info("Thống kê chunks:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    return stats
