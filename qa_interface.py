"""
Command line interface for the RAG system
"""

import os
import re

from rag_pipeline.generation.answer_generator import answer_question

from utils.logger import logger

def run_qa_interface():
    """
    Simple command-line interface for Q&A system
    """

    logger.info("\n" + "="*50)
    logger.info("🤖 HỆ THỐNG HỎI ĐÁP CHƯƠNG TRÌNH ĐÀO TẠO")
    logger.info("="*50)
    logger.info("Nhập 'exit' để thoát.\n")

    while True:
        # Get user question
        question = input("\n❓ Hỏi: ")
        
        # Check exit condition
        if question.lower() == 'exit':
            logger.info("👋 Cảm ơn đã sử dụng hệ thống!")
            break
            
        # Skip empty questions
        if not question.strip():
            logger.warning("❗ Vui lòng nhập câu hỏi!")
            continue
        
        # Clean question
        original_question = question
        
        # Log cleaned question if different
        if question != original_question:
            logger.info(f"🔄 Câu hỏi sau khi làm sạch: {question}")
        
        # Get answer from pipeline (functional)
        result = answer_question(question)
        
        # Display results
        logger.info("\n" + "-"*50)
        logger.info("📝 Câu trả lời:")
        logger.info("-"*50)
        logger.info(result["answer"])
        
        logger.info("\n" + "-"*50)
        logger.info("🔍 Nguồn tham khảo:")
        logger.info("-"*50)
        for i, source in enumerate(result["sources"]):
            logger.info(f"  [{i+1}] {source['header_path']} (Score: {source['similarity_score']})")
        logger.info("-"*50)

if __name__ == "__main__":
    run_qa_interface()