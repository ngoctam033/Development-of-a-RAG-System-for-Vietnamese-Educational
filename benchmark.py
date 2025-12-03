from rag_pipeline.generation.answer_generator import answer_question
from rag_pipeline.chat_context import context_manager
from rag_pipeline.retrieval.vector_store import load_vector_store

from utils.logger import logger
import time
import json
import os

def run_benchmark():
    """
    Simple command-line interface for Q&A system
    """
    
    # Kiểm tra xem file có tồn tại không để tránh lỗi
    if not os.path.exists("data_test.txt"):
        print(f"Lỗi: Không tìm thấy file tại đường dẫn: data_test.txt")
        return

    try:
        # Mở file với encoding='utf-8' để hỗ trợ tiếng Việt
        with open("data_test.txt", 'r', encoding='utf-8') as file:
            questions_list = [line.strip() for line in file if line.strip()]
# /home/ngoctam/code/Development-of-a-RAG-System-for-Vietnamese-Educational/data_test.txt
        # In ra số lượng câu hỏi đã đọc được (để kiểm tra)
        print(f"Đã đọc thành công {len(questions_list)} câu hỏi vào list.\n")
        print("-" * 30)

        # BƯỚC 3: Duyệt qua list và in từng câu hỏi
        for index, question in enumerate(questions_list, 1):
            # Giả lập xử lý benchmark ở đây nếu cần
            print(f"Đang xử lý dòng {index}: {question}")
            
        print("-" * 30)
        print("Hoàn tất.")

    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file: {e}")
    # vector_store = load_vector_store()
    # while True:
    #     # Get user question
    #     question = ""
        
    #     # Clean question
    #     original_question = question
        
    #     # Log cleaned question if different
    #     if question != original_question:
    #         logger.info(f"🔄 Câu hỏi sau khi làm sạch: {question}")

    #     # In ra quá trình xử lý câu hỏi và trả lời
    #     logger.info("⏳ Đang xử lý câu hỏi...")
    #     # Get answer from pipeline (functional)
    #     result = answer_question(question,vector_store=vector_store)
    #     # Log answer
    #     logger.info("✅ Câu hỏi đã được xử lý.")
        
    #     # Display results
    #     logger.info("\n" + "-"*50)
    #     logger.info("📝 Câu trả lời:")
    #     logger.info("-"*50)
    #     logger.info(result["answer"])
    #     logger.info("\n" + "-"*50)
    #     logger.info("🔍 Nguồn tham khảo:")
    #     logger.info("-"*50)
    #     logger.info("Reasoning Trace:\n" + json.dumps(result['reasoning_trace'],
    #                                                   ensure_ascii=False,
    #                                                   indent=2))
    #     for i, source in enumerate(result["sources"]):
    #         logger.info(f"  [{i+1}] {source['header_path']} (Score: {source['similarity_score']})")
    #     logger.info("-"*50)

if __name__ == "__main__":
    run_benchmark()