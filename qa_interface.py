"""
Command line interface for the RAG system
"""

import os
from rag_pipeline.retrieval.vector_store import VectorStore
from rag_pipeline.generation.llm import GeminiGenerator
from rag_pipeline.main import RAGPipeline

def run_qa_interface():
    """
    Simple command-line interface for Q&A system
    """
    
    # Initialize components
    vector_store = VectorStore()
    generator = GeminiGenerator(api_key="")
    
    # Create RAG pipeline
    pipeline = RAGPipeline(vector_store, generator)
    
    print("\n" + "="*50)
    print("🤖 HỆ THỐNG HỎI ĐÁP CHƯƠNG TRÌNH ĐÀO TẠO")
    print("="*50)
    print("Nhập 'exit' để thoát.\n")
    
    while True:
        # Get user question
        question = input("\n❓ Hỏi: ")
        
        # Check exit condition
        if question.lower() == 'exit':
            print("👋 Cảm ơn đã sử dụng hệ thống!")
            break
        
        # Get answer from pipeline
        result = pipeline.answer_question(question, top_k=3)
        
        # Display results
        print("\n" + "-"*50)
        print("📝 Câu trả lời:")
        print("-"*50)
        print(result["answer"])
        
        print("\n" + "-"*50)
        print("🔍 Nguồn tham khảo:")
        print("-"*50)
        for i, source in enumerate(result["sources"]):
            print(f"  [{i+1}] {source['header_path']} (Score: {source['similarity_score']})")
        print("-"*50)

if __name__ == "__main__":
    run_qa_interface()