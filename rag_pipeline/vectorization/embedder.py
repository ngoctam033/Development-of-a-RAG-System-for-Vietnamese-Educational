"""
Embedder Module: Vector hóa dữ liệu text thành embeddings

Module này chịu trách nhiệm:
- Load embedding models
- Vector hóa text chunks
- Xử lý bảng và content đặc biệt
- Lưu trữ vectorized data
- Batch processing cho hiệu suất tối ưu
"""

import json
import pickle
import os
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from sentence_transformers import SentenceTransformer

from utils.logger import default_logger as logger


def load_embedding_model(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> SentenceTransformer:
    """
    Load embedding model từ sentence-transformers
    
    Args:
        model_name: Tên model để load
            - "sentence-transformers/all-MiniLM-L6-v2": 384 dimensions, nhẹ và nhanh
            - "sentence-transformers/all-mpnet-base-v2": 768 dimensions, chất lượng cao hơn
            - "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": Multilingual support
            
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
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
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


def load_vectorized_data(pickle_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load vectorized data từ pickle file
    
    Args:
        pickle_path: Đường dẫn đến pickle file
        
    Returns:
        List vectorized chunks hoặc None nếu lỗi
    """
    logger.info(f"Loading vectorized data from: {pickle_path}")
    
    try:
        with open(pickle_path, "rb") as f:
            vectorized_data = pickle.load(f)
        
        logger.info(f"Successfully loaded {len(vectorized_data)} vectorized chunks")
        return vectorized_data
        
    except Exception as e:
        logger.error(f"Lỗi khi load vectorized data: {str(e)}")
        return None
