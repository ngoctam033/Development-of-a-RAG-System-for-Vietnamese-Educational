from ultils.get_data import get_questions_from_file
from pipelines import pipeline_0, pipeline_1, pipeline_2, pipeline_3, pipeline_4, pipeline_5, pipeline_6
from ultils.logger import logger
import json
import pandas as pd
from agentic_rag import answer_question
from agentic_rag import AgenticGeminiRAG

questions_list = get_questions_from_file()

def run_pipeline_1():
    # 1. Đọc file CSV để lấy danh sách câu hỏi CŨ (để loại trừ)
    csv_path = 'dashboard/fact_rag_query.csv'
    existing_questions = set()
    
    try:
        logger.info(f"Đang đọc file lọc câu hỏi từ: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Logic mới: Chỉ coi là "đã chạy" nếu câu hỏi đó đã có đủ kết quả của cả 2 pipeline
        # (hoặc >= 2 pipeline khác nhau được ghi nhận trong cột pipeline_name)
        if 'question' in df.columns:
            # Tìm cột xác định pipeline (thường là 'pipeline_name', 'pipeline', hoặc 'source')
            pipeline_col = next((col for col in ['pipeline_type'] if col in df.columns), None)
            
            if pipeline_col:
                # Chuẩn hóa cột question để tránh lỗi do khoảng trắng thừa
                df['question_clean'] = df['question'].astype(str).str.strip()
                
                # Đếm số lượng pipeline unique cho mỗi câu hỏi
                # Nếu một câu hỏi có >= 2 pipeline (ví dụ: 'base line' và 'metadata') thì mới tính là existing
                question_pipeline_counts = df.groupby('question_clean')[pipeline_col].nunique()
                existing_questions = set(question_pipeline_counts[question_pipeline_counts >= 1].index.tolist())
                
                logger.info(f"Tìm thấy {len(existing_questions)} câu hỏi đã chạy ĐỦ pipeline (>=1).")
            else:
                # Fallback: Nếu không tìm thấy cột pipeline, dùng logic cũ (có question là skip)
                logger.warning("Không tìm thấy cột pipeline trong CSV (ví dụ: 'pipeline_name'). Sử dụng logic cũ: chỉ cần tồn tại question là bỏ qua.")
                existing_questions = set(df['question'].dropna().astype(str).str.strip().tolist())
                logger.info(f"Tìm thấy {len(existing_questions)} câu hỏi đã tồn tại trong file CSV.")
        else:
             logger.warning(f"File CSV không có cột 'question'. Sẽ chạy tất cả.")
             
    except FileNotFoundError:
        logger.warning(f"Không tìm thấy file {csv_path}. Sẽ chạy tất cả câu hỏi.")
        # Nếu file không tồn tại, existing_questions vẫn là set rỗng -> chạy hết
    except Exception as e:
        logger.error(f"Lỗi khi đọc file CSV: {e}")
        return

    # 2. Lọc questions_list
    # Chỉ giữ lại những question KHÔNG nằm trong existing_questions (questions_list - csv)
    filtered_questions_list = [
        q for q in questions_list 
        if q.get('question', '').strip() not in existing_questions
    ]
    
    logger.info(f"Số lượng câu hỏi MỚI sẽ chạy (chưa có trong CSV): {len(filtered_questions_list)}")

    if not filtered_questions_list:
        logger.warning("Không có câu hỏi nào khớp giữa file input và file CSV.")
        return

    rag_system = AgenticGeminiRAG()
    # ----------------------------------------
    for question in filtered_questions_list:   
        # Chạy lặp lại 2 lần cho mỗi câu hỏi (theo logic vòng lặp con bạn yêu cầu)
        for i in range(2):   
            logger.info("="*50)
            logger.info(f"Question: {question['question']}")
            try:
                result_rag = rag_system.qa_viet_uni(
                        question=question["question"],
                    )
                logger.info(result_rag)
            except Exception as e:
                logger.error(f"Error running RAG System: {e}")
            
            logger.info("="*50)

if __name__ == "__main__":
    #logger.info("Bắt đầu chạy pipeline 1...")
    run_pipeline_1()
    #logger.info("Kết thúc chạy pipeline 1.")