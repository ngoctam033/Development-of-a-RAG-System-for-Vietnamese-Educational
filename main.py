from ultils.get_data import get_questions_from_file
from pipelines import pipeline_1
from ultils.logger import logger
import json

questions_list = get_questions_from_file()
def run_pipeline_1():
    # ----------------------------------------
    for question in questions_list:      
        #logger.info("="*50)
        #logger.info(f"Question: {question}")
        result = pipeline_1.run(question)
        # pretty_result = json.dumps(result["sources"], indent=4, ensure_ascii=False)
        #logger.info(f"Context and Sources: {pretty_result}")
        #logger.info("="*50)

if __name__ == "__main__":
    #logger.info("Bắt đầu chạy pipeline 1...")
    run_pipeline_1()
    #logger.info("Kết thúc chạy pipeline 1.")