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
import time

from utils.logger import logger

def parse_markdown_hierarchy(markdown_content: str) -> dict:
    """
    Phân tích cấu trúc phân cấp của file markdown và trả về dict dạng cây
    Args:
        markdown_content: Nội dung markdown đầy đủ
    Returns:
        Dict biểu diễn cấu trúc phân cấp các headers và nội dung
    """
    lines = markdown_content.split('\n')
    root = {"children": []}
    stack = [(0, root)]  # (header_level, node)
    max_level = 0

    for line in lines:
        header_level, header_text = extract_header_info(line)
        # logger.info (f"Processing line: {line}, header_level: {header_level}, header_text: {header_text}")
        if header_level > 0:
            node = {"header": header_text, "level": header_level, "content": "", "children": []}
            # Tìm parent phù hợp
            while stack and stack[-1][0] >= header_level:
                stack.pop()
            parent = stack[-1][1]
            parent["children"].append(node)
            stack.append((header_level, node))
            if header_level > max_level:
                max_level = header_level
        else:
            # Thêm nội dung vào node hiện tại (nếu có)
            if len(stack) > 1:
                stack[-1][1]["content"] += line + '\n'
        # time.sleep(1)
        # logger.info('=========================')

    return {"nodes": root["children"], "max_level": max_level}

def flatten_markdown_hierarchy(nodes, parent_headers=None, parent_level=0, extra_metadata=None, chapter_idx=0, source_info=None):
    """
    Duyệt cây phân cấp markdown, tạo list dict với content gồm header_path + content
    Args:
        nodes: list node (cây phân cấp)
        parent_headers: list header cha
        parent_level: level cha
        extra_metadata: dict metadata bổ sung
        chapter_idx: index chapter (tăng dần theo node cấp 1)
        source_info: dict thông tin nguồn (pdf, markdown, document_name)
    Returns:
        List dict với content và metadata
    """
    if parent_headers is None:
        parent_headers = []
    if extra_metadata is None:
        extra_metadata = {}
    if source_info is None:
        source_info = {}
    results = []
    for idx, node in enumerate(nodes):
        headers = parent_headers + [node["header"]] if node["header"] else parent_headers
        header_path = " > ".join([h for h in headers if h])
        meta = {
            "chapter_title": headers[0] if len(headers) > 0 else "",
            "section_title": headers[1] if len(headers) > 1 else "",
            "subsection_title": headers[2] if len(headers) > 2 else "",
            "subsubsection_title": headers[3] if len(headers) > 3 else "",
            "header_path": header_path
        }
        meta.update(source_info)
        meta.update(extra_metadata)
        # Đệ quy cho children trước
        child_chapter_idx = chapter_idx + 1 if node["level"] == 1 else chapter_idx
        children_chunks = flatten_markdown_hierarchy(node["children"], headers, node["level"], extra_metadata, child_chapter_idx, source_info)
        results.extend(children_chunks)
        # Nếu là node lá (không có children) và content thực sự có nội dung
        content_stripped = node["content"].strip()
        if not node["children"] and content_stripped and content_stripped != "\n":
            content = header_path + "\n" + content_stripped if content_stripped else header_path
            chunk = {"content": content, "metadata": meta}
            results.append(chunk)
    return results

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

    # Bước 2: Phân tích cấu trúc phân cấp
    hierarchy_dict = parse_markdown_hierarchy(markdown_content)

    # Bước 3: Tạo danh sách chunks từ cấu trúc phân cấp
    flat_chunks = flatten_markdown_hierarchy(hierarchy_dict['nodes'])

    # Bước 4: Xử lý lại các chunks nếu cần
    processed_chunks = flat_chunks

    # Bước 5: Lưu chunks ra file JSON
    save_success = save_chunks_to_json(processed_chunks, output_file_path)

    if not save_success:
        logger.warning("Có lỗi khi lưu file, nhưng chunks vẫn được trả về")

    logger.info(f"Chunking pipeline hoàn tất: {len(processed_chunks)} chunks")
    return processed_chunks


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
    chapters = [chunk["metadata"].get("chapter_title", "") for chunk in chunks]
    sections = [chunk["metadata"].get("section_title", "") for chunk in chunks]
    subsections = [chunk["metadata"].get("subsection_title", "") for chunk in chunks]
    subsubsections = [chunk["metadata"].get("subsubsection_title", "") for chunk in chunks]

    def count_nonempty(items):
        return len([x for x in items if x])

    # Phân phối số chunk theo chapter, section, ...
    from collections import Counter
    chapter_dist = Counter([c for c in chapters if c])
    section_dist = Counter([s for s in sections if s])
    subsection_dist = Counter([s for s in subsections if s])
    subsubsection_dist = Counter([s for s in subsubsections if s])

    stats = {
        "total_chunks": len(chunks),
        "total_chapters": len(set(chapters) - {''}),
        "total_sections": len(set(sections) - {''}),
        "total_subsections": len(set(subsections) - {''}),
        "total_subsubsections": len(set(subsubsections) - {''}),
        "avg_content_length": sum(content_lengths) / len(content_lengths) if content_lengths else 0,
        "min_content_length": min(content_lengths) if content_lengths else 0,
        "max_content_length": max(content_lengths) if content_lengths else 0,
        "total_characters": sum(content_lengths),
        "chapter_distribution": dict(chapter_dist),
        "section_distribution": dict(section_dist),
        "subsection_distribution": dict(subsection_dist),
        "subsubsection_distribution": dict(subsubsection_dist)
    }

    logger.info("Thống kê chunks:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")

    return stats
