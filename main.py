from ultils.get_data import get_questions_from_file
from pipelines import pipeline_1, pipeline_2, pipeline_3, pipeline_4
from ultils.logger import logger
import json
from agentic_rag import answer_question

questions_list = get_questions_from_file()
def run_pipeline_1():
    # ----------------------------------------
    for question in questions_list:      
        #logger.info("="*50)
        #logger.info(f"Question: {question}")
        # pipeline_2.run(questions_list[0]['question'])
        pipeline_4.run(question['question'])
        # result = answer_question(question['question'], user_chat_history=[])
        # pretty_result = json.dumps(result["sources"], indent=4, ensure_ascii=False)
        #logger.info(f"Context and Sources: {pretty_result}")
        #logger.info("="*50)

if __name__ == "__main__":
    #logger.info("Bắt đầu chạy pipeline 1...")
    run_pipeline_1()
    #logger.info("Kết thúc chạy pipeline 1.")