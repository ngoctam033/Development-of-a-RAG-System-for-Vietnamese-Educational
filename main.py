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

from rag_pipeline import pdf_extractor
from rag_pipeline.processing.chunking import chunk_markdown_file, analyze_chunk_statistics
from rag_pipeline.vectorization.embedder import vectorize_chunks_pipeline
from config.pipeline_config import (
    PROCESSING_DATA_FOLDER_PATH, 
    VECTOR_STORE_PATH,
    EMBEDDING_MODEL_NAME,
    VECTORIZATION_CONFIG
)

from utils.logger import logger

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
    files = pdf_extractor.get_all_files_in_folder()
    
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