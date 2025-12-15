from ultils.get_data import get_questions_from_file
from pipelines import pipeline_1, pipeline_2, pipeline_5
from ultils.logger import logger
import json
import optuna
# Tắt log rác của Optuna để dễ nhìn
optuna.logging.set_verbosity(optuna.logging.WARNING)
questions_list = get_questions_from_file()
from benchmark_optimized import preprocess_dataset_to_numpy, objective

def run_benchmark_1():
    bench_mark_data = []
    logger.info("Đang chạy pipeline để thu thập dữ liệu benchmark...")
    
    # --- PHẦN 1: CHẠY PIPELINE (Chậm - IO Bound) ---
    # Phần này không thể tối ưu bằng thuật toán, chỉ có thể cache lại file json
    # Nếu file json đã tồn tại, bạn nên load từ file thay vì chạy lại pipeline
    try:
        with open("benchmark_results.json", "r", encoding="utf-8") as f:
            bench_mark_data = json.load(f)
        logger.info("Đã load dữ liệu từ file benchmark_results.json")
    except FileNotFoundError:
        for question in questions_list:   
            benchmark_item = {
                "question": question['question'],
                "correct_chunk_id": question['correct_chunk_id'],
                "candidates": []
            }   
            result = pipeline_5.run(question['question'])
            benchmark_item["candidates"] = result
            bench_mark_data.append(benchmark_item)
            
        with open("benchmark_results.json", "w", encoding="utf-8") as f:
            json.dump(bench_mark_data, f, ensure_ascii=False, indent=4)

    # --- PHẦN 2: CHUẨN BỊ DỮ LIỆU (Pre-processing) ---
    logger.info("Đang chuyển đổi dữ liệu sang NumPy...")
    numpy_data = preprocess_dataset_to_numpy(bench_mark_data)
    
    # --- PHẦN 3: TỐI ƯU HÓA (CPU Bound - Đã được tối ưu) ---
    logger.info("Bắt đầu tối ưu hóa trọng số với Optuna...")
    
    # Dùng TPESampler (mặc định) là đủ tốt
    study = optuna.create_study(direction='maximize')
    
    # VỚI NUMPY, 100,000 trials sẽ chạy rất nhanh (chỉ vài chục giây đến vài phút)
    # Tuy nhiên, với bài toán 3 tham số đơn giản này, 2000-5000 trials là quá đủ để hội tụ.
    study.optimize(lambda trial: objective(trial, numpy_data), n_trials=5000)

    logger.info("-" * 50)
    logger.info("KẾT QUẢ TỐI ƯU NHẤT:")
    logger.info(f"Recall@10 cao nhất: {study.best_value * 100:.2f}%")
    logger.info("Bộ trọng số vàng:")
    for key, value in study.best_params.items():
        logger.info(f"  - {key}: {value:.4f}")
        
    sum_w = sum(study.best_params.values())
    logger.info("-" * 50)
    logger.info("Trọng số chuẩn hóa (Tổng = 1):")
    for key, value in study.best_params.items():
        if sum_w > 0:
            logger.info(f"  - {key}: {value/sum_w:.4f}")
        else:
            logger.info(f"  - {key}: 0.0")

if __name__ == "__main__":
    run_benchmark_1()
    

if __name__ == "__main__":
    #logger.info("Bắt đầu chạy pipeline 1...")
    run_benchmark_1()
    #logger.info("Kết thúc chạy pipeline 1.")