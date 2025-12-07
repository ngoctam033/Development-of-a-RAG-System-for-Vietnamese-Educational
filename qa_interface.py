"""
Command line interface for the RAG system
"""

import os
import re

from agentic_rag import answer_question
# from rag_pipeline.chat_context import context_manager
# from rag_pipeline.retrieval.vector_store import load_vector_store

from ultils.logger import logger
import time
import json

def run_qa_interface():
    """
    Simple command-line interface for Q&A system
    """

    logger.info("\n" + "="*50)
    logger.info("🤖 HỆ THỐNG HỎI ĐÁP CHƯƠNG TRÌNH ĐÀO TẠO")
    logger.info("="*50)
    logger.info("Nhập 'exit' để thoát.\n")

    # user_chat_context = context_manager.ChatContextManager()
    user_chat_context = []
    # vector_store = load_vector_store()
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

        # Update user chat context
        # user_chat_context.append_message(original_question)

        # In ra quá trình xử lý câu hỏi và trả lời
        logger.info("⏳ Đang xử lý câu hỏi...")
        # Get answer from pipeline (functional)
        result = answer_question(question,user_chat_context)
        # Log answer
        logger.info("✅ Câu hỏi đã được xử lý.")
        
        # Display results
        logger.info("\n" + "-"*50)
        logger.info("📝 Câu trả lời:")
        logger.info("-"*50)
        logger.info(result["answer"])
        logger.info("\n" + "-"*50)
        logger.info("🔍 Nguồn tham khảo:")
        logger.info("-"*50)
        logger.info("Reasoning Trace:\n" + json.dumps(result['reasoning_trace'],
                                                      ensure_ascii=False,
                                                      indent=2))
        logger.info("-"*50)

if __name__ == "__main__":
    run_qa_interface()