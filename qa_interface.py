"""
Command line interface for the RAG system
"""

import os
from rag_pipeline.retrieval.vector_store import VectorStore
from rag_pipeline.generation.llm import GeminiGenerator
from rag_pipeline.main import RAGPipeline

from utils.logger import logger

def run_qa_interface():
    """
    Simple command-line interface for Q&A system
    """
    
    # Initialize components
    vector_store = VectorStore()
    generator = GeminiGenerator(api_key="")
    
    # Create RAG pipeline
    pipeline = RAGPipeline(vector_store, generator)

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
        
        # Get answer from pipeline
        result = pipeline.answer_question(question, top_k=3)
        
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