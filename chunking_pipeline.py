"""
Main module for running the complete RAG (Retrieval Augmented Generation) pipeline.
This pipeline processes PDF documents through three main stages:
1. Extraction: Convert PDFs to markdown format
2. Chunking: Split documents into manageable chunks
3. Vectorization: Convert text chunks into vector embeddings
"""

import os
import json
from typing import Dict, List, Any
from configs import RAW_DATA_FOLDER_PATH
# tuple
from typing import Tuple
import re
import pprint
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

def get_all_files_in_folder(
    folder_path: str = RAW_DATA_FOLDER_PATH, 
    extensions: List[str] = ['.md']
) -> List[Dict[str, str]]:
    """
    Lấy tất cả các file trong thư mục với định dạng được chỉ định

    Args:
        folder_path: Đường dẫn đến thư mục cần quét
        extensions: Danh sách các phần mở rộng file cần lọc (mặc định: ['.pdf'])

    Returns:
        Danh sách các dictionary chứa thông tin về file:
            - 'path': Đường dẫn đầy đủ của file
            - 'name': Tên file (bao gồm phần mở rộng)
            - 'base_name': Tên file (không có phần mở rộng)
            - 'ext': Phần mở rộng của file
    """
    # Kiểm tra nếu thư mục không tồn tại
    if not os.path.exists(folder_path):
        logger.error(f"Thư mục không tồn tại: {folder_path}")
        return []

    # Khởi tạo danh sách kết quả
    files_info = []

    # Chuyển extensions sang chữ thường để so sánh không phân biệt hoa thường
    extensions_lower = [ext.lower() for ext in extensions]

    # Lặp qua tất cả các file trong thư mục
    for file_name in os.listdir(folder_path):
        # Lấy đường dẫn đầy đủ của file
        file_path = os.path.join(folder_path, file_name)

        # Kiểm tra nếu là file (không phải thư mục)
        if os.path.isfile(file_path):
            # Lấy phần mở rộng của file
            _, ext = os.path.splitext(file_name)

            # Kiểm tra nếu file có phần mở rộng nằm trong danh sách cần lọc
            if ext.lower() in extensions_lower:
                # Lấy tên file không có phần mở rộng
                base_name = os.path.splitext(file_name)[0]

                # Thêm thông tin file vào danh sách kết quả
                files_info.append({
                    'path': file_path,
                    'name': file_name,
                    'base_name': base_name,
                    'ext': ext
                })

    # Ghi log thông báo
    if len(files_info) > 0:
        logger.info(f"Tìm thấy {len(files_info)} file {', '.join(extensions)} trong thư mục {folder_path}")
    else:
        logger.warning(f"Không tìm thấy file {', '.join(extensions)} nào trong thư mục {folder_path}")

    return files_info
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
        # time.sleep(5)
        headers = parent_headers + [node["header"]] if node["header"] else parent_headers
        header_path = source_info.get("source_document", "") + " > " + " > ".join([h for h in headers if h])
        meta = {
            "chapter_title": headers[0] if len(headers) > 0 else "",
            "section_title": headers[1] if len(headers) > 1 else "",
            "subsection_title": headers[2] if len(headers) > 2 else "",
            "subsubsection_title": headers[3] if len(headers) > 3 else "",
            "header_path": header_path
            # "document_name": 
        }
        meta.update(source_info)
        meta.update(extra_metadata)
        # Đệ quy cho children trước
        child_chapter_idx = chapter_idx + 1 if node["level"] == 1 else chapter_idx
        # Luôn lưu content của node nếu có nội dung thực sự
        content_stripped = node["content"].strip()
        document_name = node.get("document_name", "")
        logger.info("Processing node:\n" + pprint.pformat(node["content"].strip(), indent=2, width=120))
        if content_stripped and content_stripped != "\n":
            content = document_name + header_path + "\n" + content_stripped if content_stripped else header_path
            chunk = {"content": content, "metadata": meta}
            results.append(chunk)
        children_chunks = flatten_markdown_hierarchy(node["children"], headers, node["level"], extra_metadata, child_chapter_idx, source_info)
        results.extend(children_chunks)
    return results
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

    # logger.info(f"Cấu trúc phân cấp tối đa: {hierarchy_dict['nodes']}")

    # Bước 3: Tạo danh sách chunks từ cấu trúc phân cấp
    flat_chunks = flatten_markdown_hierarchy(hierarchy_dict['nodes'], source_info={
        "source_markdown": os.path.basename(input_file_path),
        "source_document": os.path.splitext(os.path.basename(input_file_path))[0],
        "source_type": "markdown"
    })

    # Bước 4: Xử lý lại các chunks nếu cần
    processed_chunks = flat_chunks

    # Bước 5: Lưu chunks ra file JSON
    save_success = save_chunks_to_json(processed_chunks, output_file_path)

    if not save_success:
        logger.warning("Có lỗi khi lưu file, nhưng chunks vẫn được trả về")

    logger.info(f"Chunking pipeline hoàn tất: {len(processed_chunks)} chunks")
    return processed_chunks
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
def load_embedding_model(model_name: str) -> SentenceTransformer:
    """
    Load embedding model từ sentence-transformers
    
    Args:
        model_name: Tên model để load
            - "bkai-foundation-models/vietnamese-bi-encoder": Model bi-encoder tiếng Việt
            
    Returns:
        SentenceTransformer model đã load
        
    Raises:
        Exception: Nếu không thể load model
    """
    logger.info(f"Loading embedding model: {model_name}")
    
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Successfully loaded model: {model_name}")
        logger.info(f"Model max sequence length: {model.max_seq_length}")
        return model
        
    except Exception as e:
        error_msg = f"Lỗi khi load embedding model {model_name}: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
def process_markdown_tables(content: str) -> str:
    """
    Xử lý bảng Markdown và chuyển thành text có cấu trúc
    
    Args:
        content: Content chứa bảng Markdown
        
    Returns:
        Content với bảng đã được xử lý
    """
    import re
    
    lines = content.split('\n')
    processed_lines = []
    in_table = False
    table_headers = []
    
    for line in lines:
        # Phát hiện bảng Markdown (line có | và không phải separator)
        if '|' in line and not re.match(r'^\s*\|[\s\-\|]+\|\s*$', line):
            if not in_table:
                # Bắt đầu bảng mới
                in_table = True
                table_headers = [header.strip() for header in line.split('|')[1:-1]]
                processed_lines.append(f"Bảng dữ liệu với các cột: {', '.join(table_headers)}")
            else:
                # Dòng dữ liệu trong bảng
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                if len(cells) == len(table_headers):
                    row_text = "; ".join([f"{header}: {cell}" for header, cell in zip(table_headers, cells) if cell])
                    if row_text:
                        processed_lines.append(row_text)
        elif in_table and '|' not in line:
            # Kết thúc bảng
            in_table = False
            table_headers = []
            processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)
def clean_content_for_embedding(content: str) -> str:
    """
    Làm sạch content để tối ưu cho embedding
    
    Args:
        content: Content cần làm sạch
        
    Returns:
        Content đã được làm sạch
    """
    import re
    
    # Loại bỏ multiple spaces
    content = re.sub(r' +', ' ', content)
    
    # Loại bỏ multiple newlines (giữ lại cấu trúc đoạn văn)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Loại bỏ trailing/leading whitespaces
    content = content.strip()
    
    return content
def preprocess_content_for_embedding(content: str) -> str:
    """
    Tiền xử lý content trước khi vector hóa
    
    Args:
        content: Text content cần xử lý
        
    Returns:
        Content đã được xử lý
    """
    # Xử lý bảng Markdown
    processed_content = process_markdown_tables(content)
    
    # Loại bỏ ký tự đặc biệt có thể gây nhiễu
    processed_content = clean_content_for_embedding(processed_content)
    
    return processed_content
def extract_texts_from_chunks(chunks: List[Dict[str, Any]]) -> List[str]:
    """
    Trích xuất texts từ danh sách chunks để vector hóa
    
    Args:
        chunks: List các chunks với structure {"content": str, "metadata": dict}
        
    Returns:
        List các text strings đã được xử lý
    """
    logger.info(f"Extracting texts from {len(chunks)} chunks for embedding")
    
    texts = []
    for i, chunk in enumerate(chunks):
        if "content" not in chunk:
            logger.warning(f"Chunk {i} không có 'content' field")
            continue
            
        # Preprocess content
        processed_content = preprocess_content_for_embedding(chunk["content"])
        texts.append(processed_content)
        # in ra bieens chunk dang xu ly
        logger.info(f"Chunk {i} processed content:\n{chunk}\n")
    
    logger.info(f"Extracted {len(texts)} texts for embedding")
    return texts
def generate_embeddings_batch(
    texts: List[str], 
    model: SentenceTransformer,
    batch_size: int = 32,
    show_progress: bool = True
) -> np.ndarray:
    """
    Tạo embeddings cho list texts với batch processing
    
    Args:
        texts: List các text cần vector hóa
        model: SentenceTransformer model
        batch_size: Kích thước batch để xử lý
        show_progress: Hiển thị progress bar
        
    Returns:
        numpy array chứa embeddings
    """
    logger.info(f"Generating embeddings for {len(texts)} texts (batch_size={batch_size})")
    
    try:
        # Encode tất cả texts
        embeddings = model.encode(
            texts, 
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        
        logger.info(f"Successfully generated embeddings: shape {embeddings.shape}")
        return embeddings
        
    except Exception as e:
        error_msg = f"Lỗi khi generate embeddings: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)
def attach_embeddings_to_chunks(
    chunks: List[Dict[str, Any]], 
    embeddings: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Gắn embeddings vào chunks
    
    Args:
        chunks: List chunks gốc
        embeddings: numpy array embeddings tương ứng
        
    Returns:
        List chunks đã được gắn embeddings
    """
    if len(chunks) != len(embeddings):
        raise ValueError(f"Số lượng chunks ({len(chunks)}) không khớp với số embeddings ({len(embeddings)})")
    
    logger.info(f"Attaching embeddings to {len(chunks)} chunks")
    
    vectorized_chunks = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        # Copy chunk gốc
        vectorized_chunk = chunk.copy()
        
        # Thêm embedding (convert to list để serialize JSON)
        vectorized_chunk["embedding"] = embedding.tolist()
        
        # Thêm metadata về embedding
        if "metadata" not in vectorized_chunk:
            vectorized_chunk["metadata"] = {}
            
        vectorized_chunk["metadata"].update({
            "embedding_model": "sentence-transformers",
            "vector_dimensions": len(embedding),
            "chunk_index": i
        })
        
        vectorized_chunks.append(vectorized_chunk)
    
    logger.info(f"Successfully attached embeddings to all chunks")
    return vectorized_chunks
def save_vectorized_data_pickle(vectorized_chunks: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Lưu vectorized data dưới dạng pickle (bao gồm cả embeddings)
    
    Args:
        vectorized_chunks: List chunks đã vector hóa
        output_path: Đường dẫn file pickle output
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    logger.info(f"Saving vectorized data to pickle: {output_path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            pickle.dump(vectorized_chunks, f)
        
        logger.info(f"Successfully saved vectorized data to {output_path}")
        return True
        
    except Exception as e:
        error_msg = f"Lỗi khi lưu pickle file: {str(e)}"
        logger.error(error_msg)
        return False
def save_vectorized_metadata_json(vectorized_chunks: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Lưu metadata của vectorized data dưới dạng JSON (không bao gồm embeddings)
    
    Args:
        vectorized_chunks: List chunks đã vector hóa
        output_path: Đường dẫn file JSON output
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    logger.info(f"Saving vectorized metadata to JSON: {output_path}")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Remove embeddings để giảm kích thước file
        metadata_chunks = []
        for chunk in vectorized_chunks:
            chunk_copy = chunk.copy()
            if "embedding" in chunk_copy:
                del chunk_copy["embedding"]
            metadata_chunks.append(chunk_copy)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata_chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved metadata to {output_path}")
        return True
        
    except Exception as e:
        error_msg = f"Lỗi khi lưu JSON file: {str(e)}"
        logger.error(error_msg)
        return False
def get_embedding_statistics(embeddings: np.ndarray) -> Dict[str, Any]:
    """
    Tính toán thống kê về embeddings
    
    Args:
        embeddings: numpy array embeddings
        
    Returns:
        Dictionary chứa thống kê
    """
    if embeddings.size == 0:
        return {"error": "Empty embeddings array"}
    
    stats = {
        "total_vectors": len(embeddings),
        "vector_dimensions": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
        "mean_norm": float(np.mean(np.linalg.norm(embeddings, axis=1))),
        "std_norm": float(np.std(np.linalg.norm(embeddings, axis=1))),
        "min_value": float(np.min(embeddings)),
        "max_value": float(np.max(embeddings)),
        "mean_value": float(np.mean(embeddings))
    }
    
    return stats
def display_vectorization_summary(
    vectorized_chunks: List[Dict[str, Any]], 
    embeddings: np.ndarray,
    model_name: str,
    pickle_path: str,
    json_path: str
) -> None:
    """
    Hiển thị tóm tắt quá trình vector hóa
    
    Args:
        vectorized_chunks: List chunks đã vector hóa
        embeddings: numpy array embeddings
        model_name: Tên model đã sử dụng
        pickle_path: Đường dẫn file pickle
        json_path: Đường dẫn file JSON
    """
    stats = get_embedding_statistics(embeddings)
    
    logger.info("=" * 70)
    logger.info("✅ VECTOR HÓA HOÀN TẤT")
    logger.info("=" * 70)
    logger.info(f"   Model: {model_name}")
    logger.info(f"   Total chunks: {len(vectorized_chunks)}")
    logger.info(f"   Vector dimensions: {stats.get('vector_dimensions', 'N/A')}")
    logger.info(f"   Mean vector norm: {stats.get('mean_norm', 'N/A'):.4f}")
    logger.info("=" * 70)
    logger.info("📁 Files saved:")
    logger.info(f"   Pickle (with embeddings): {pickle_path}")
    logger.info(f"   JSON (metadata only): {json_path}")
    logger.info("=" * 70)
def vectorize_chunks_pipeline(
    chunks: List[Dict[str, Any]],
    model_name: str,
    output_dir: str = "data/vector_store",
    batch_size: int = 32,
    save_pickle: bool = True,
    save_json: bool = True
) -> Dict[str, Any]:
    """
    Pipeline hoàn chỉnh để vector hóa chunks
    
    Args:
        chunks: List chunks cần vector hóa
        model_name: Tên embedding model
        output_dir: Thư mục lưu output files
        batch_size: Kích thước batch để xử lý
        save_pickle: Có lưu file pickle không
        save_json: Có lưu file JSON không
        
    Returns:
        Dictionary chứa kết quả và thống kê
    """
    logger.info("🚀 Bắt đầu vectorization pipeline")
    
    if not chunks:
        logger.error("Không có chunks để vector hóa")
        return {"success": False, "error": "Empty chunks list"}
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Bước 1: Load embedding model
        model = load_embedding_model(model_name)
        
        # Bước 2: Extract và preprocess texts
        texts = extract_texts_from_chunks(chunks)
        
        # Bước 3: Generate embeddings
        embeddings = generate_embeddings_batch(texts, model, batch_size)
        
        # Bước 4: Attach embeddings to chunks
        vectorized_chunks = attach_embeddings_to_chunks(chunks, embeddings)
        
        # Bước 5: Save data
        pickle_path = os.path.join(output_dir, "vectorized_data.pkl")
        json_path = os.path.join(output_dir, "vectorized_metadata.json")
        
        pickle_success = True
        json_success = True
        
        if save_pickle:
            pickle_success = save_vectorized_data_pickle(vectorized_chunks, pickle_path)
        
        if save_json:
            json_success = save_vectorized_metadata_json(vectorized_chunks, json_path)
        
        # Bước 6: Display summary
        if pickle_success and json_success:
            display_vectorization_summary(
                vectorized_chunks, embeddings, model_name, pickle_path, json_path
            )
        
        # Return results
        result = {
            "success": True,
            "vectorized_chunks": vectorized_chunks,
            "embeddings": embeddings,
            "statistics": get_embedding_statistics(embeddings),
            "model_name": model_name,
            "files_saved": {
                "pickle": pickle_path if save_pickle and pickle_success else None,
                "json": json_path if save_json and json_success else None
            }
        }
        
        logger.info("✅ Vectorization pipeline hoàn tất thành công")
        return result
        
    except Exception as e:
        error_msg = f"Vectorization pipeline thất bại: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
from configs import (
    PROCESSING_DATA_FOLDER_PATH, 
    VECTOR_STORE_PATH,
    VECTORIZATION_CONFIG
)
from configs import EMBEDDING_MODEL_NAME

from ultils.logger import logger

def main() -> None:
    """
    Execute the complete RAG pipeline workflow.
    
    The pipeline consists of three main stages:
    1. PDF Processing: Extract text from PDFs and convert to markdown
    2. Chunking: Split documents into semantic chunks
    3. Vectorization: Convert text chunks into vector embeddings
    
    Each stage includes error handling and progress tracking.
    Results are saved at each stage for validation and debugging.
    """
    # Initialize output directories
    os.makedirs(PROCESSING_DATA_FOLDER_PATH, exist_ok=True)
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)

    logger.info("🚀 RAG PIPELINE - COMPLETE WORKFLOW")
    logger.info("=" * 60)

    # Initialize tracking variables
    all_chunks: List[Dict[str, Any]] = []  # Store all processed chunks
    processed_files: List[str] = []        # Track successfully processed files
    
    # Stage 1: PDF Processing
    # ----------------------------------------------------
    files = get_all_files_in_folder()
    
    if not files:
        logger.warning("❌ Không tìm thấy file PDF nào để xử lý")
        return

    logger.info(f"\n📄 BƯỚC 1: PROCESSING {len(files)} PDF FILES")
    logger.info("-" * 40)

    for file in files:
        logger.info(f"Processing file: {file['name']}")

        # Setup output paths for both markdown and chunks
        output_md_filename = f"{file['base_name']}.md"
        output_path = os.path.join(PROCESSING_DATA_FOLDER_PATH, output_md_filename)
        output_chunks_path = os.path.join(PROCESSING_DATA_FOLDER_PATH, f"{file['base_name']}_chunks.json")

        # Extract PDF content to markdown
        # TODO: Uncomment for production use
        # success = pdf_extractor.extract_pdf_pipeline(file['path'], output_path)
        success = True  # Demo mode: assume extraction success
        
        if not success:
            logger.error(f"❌ Failed to extract: {file['name']}")
            continue

        logger.info(f"✅ Successfully extracted: {file['name']} -> {output_md_filename}")

        # Process chunks if markdown file exists
        if not os.path.exists(output_path):
            logger.error(f"❌ File markdown không tồn tại: {output_path}")
            continue
            
        # Generate chunks from markdown
        logger.info(f"🔪 Chunking: {output_md_filename}")
        chunks = chunk_markdown_file(output_path, output_chunks_path)
        # Enrich chunk metadata
        for chunk in chunks:
            chunk['metadata'].update({
                'source_pdf': file['path'],
                'source_markdown': output_path,
                'document_name': file['base_name']
            })
        
        # Track progress
        all_chunks.extend(chunks)
        processed_files.append(file['base_name'])
        logger.info(f"✅ Generated {len(chunks)} chunks")

        logger.info("-" * 50)

    # Validate chunks before proceeding
    if not all_chunks:
        logger.error("❌ Không có chunks nào được tạo. Pipeline dừng lại.")
        return
    
    # Stage 1 Summary
    logger.info(f"\n📊 TỔNG KẾT BƯỚC 1:")
    logger.info(f"   Documents processed: {len(processed_files)}")
    logger.info(f"   Total chunks: {len(all_chunks)}")
    logger.info(f"   Files: {', '.join(processed_files)}")

    # Analyze chunk statistics
    logger.info(f"\n📊 PHÂN TÍCH THỐNG KÊ CHUNKS:")
    stats = analyze_chunk_statistics(all_chunks)
    # đánh số thứ tự cho chunk để dễ theo dõi
    for i, chunk in enumerate(all_chunks):
        chunk["metadata"]["chunk_index"] = i
    
    # Save combined chunks for backup and analysis
    all_chunks_path = os.path.join(PROCESSING_DATA_FOLDER_PATH, "all_chunks_combined.json")
    try:
        with open(all_chunks_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved all chunks to: {all_chunks_path}")
    except Exception as e:
        logger.warning(f"⚠️ Warning: Could not save combined chunks: {str(e)}")
        logger.debug(f"⚠️ Debug info: {e}")
    logger.info("-" * 50)
    # Stage 2: Vectorization
    # ----------------------------------------------------
    logger.info(f"\n🧮 BƯỚC 2: VECTORIZATION")
    logger.info("-" * 40)
    logger.info(f"Vector hóa {len(all_chunks)} chunks...")
    
    # Configure and run vectorization using config settings
    vectorization_result = vectorize_chunks_pipeline(
        chunks=all_chunks,
        model_name=EMBEDDING_MODEL_NAME,
        output_dir=VECTOR_STORE_PATH,
        batch_size=VECTORIZATION_CONFIG["batch_size"],
        save_pickle=True,  # Save vectors in binary format
        save_json=True    # Save metadata in readable format
    )
    
    # Process vectorization results
    if vectorization_result["success"]:
        logger.info(f"\n✅ VECTORIZATION THÀNH CÔNG!")
        
        stats = vectorization_result["statistics"]
        files_saved = vectorization_result["files_saved"]
        
        # Display vectorization details
        logger.info(f"   Model: {vectorization_result['model_name']}")
        logger.info(f"   Vector dimensions: {stats.get('vector_dimensions')}")
        logger.info(f"   Total vectors: {stats.get('total_vectors')}")
        logger.info(f"   Files saved:")
        if files_saved.get("pickle"):
            logger.info(f"      Pickle: {files_saved['pickle']}")  # Binary vector storage
        if files_saved.get("json"):
            logger.info(f"      JSON: {files_saved['json']}")      # Metadata storage
    else:
        logger.error(f"❌ VECTORIZATION THẤT BẠI: {vectorization_result.get('error', 'Unknown error')}")
    
    # Final Pipeline Summary
    # ----------------------------------------------------
    logger.info(f"\n" + "=" * 60)
    logger.info("🎉 RAG PIPELINE HOÀN TẤT")
    logger.info("=" * 60)
    logger.info(f"   📄 PDF files processed: {len(processed_files)}")
    logger.info(f"   🔪 Total chunks created: {len(all_chunks)}")
    if vectorization_result["success"]:
        logger.info(f"   🧮 Vectors generated: {vectorization_result['statistics'].get('total_vectors')}")
        logger.info(f"   📁 Data ready for retrieval at: {VECTOR_STORE_PATH}")
        logger.info(f"   🚀 Ready for Q&A system!")
    else:
        logger.error(f"   ❌ Vectorization failed - manual intervention needed")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()