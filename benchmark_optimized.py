from ultils.get_data import get_questions_from_file
from pipelines import pipeline_1
from ultils.logger import logger
import json
import optuna
import numpy as np
from typing import List, Dict, Any

optuna.logging.set_verbosity(optuna.logging.WARNING)

questions_list = get_questions_from_file()

# ---------------------------------------------------------
# BƯỚC 1: HÀM CHUYỂN ĐỔI DỮ LIỆU SANG NUMPY (CHẠY 1 LẦN)
# ---------------------------------------------------------
def preprocess_dataset_to_numpy(dataset: List[Dict[str, Any]]):
    """
    Chuyển đổi list of dicts thành list of numpy arrays để tính toán nhanh.
    Tối ưu: Pre-allocate arrays thay vì append.
    """
    processed_data = []
    
    for item in dataset:
        correct_id = item['correct_chunk_id']
        candidates = item['candidates']
        
        if not candidates:
            continue
        
        # Pre-allocate với size biết trước (6 features)
        n_cand = len(candidates)
        scores = np.zeros((n_cand, 7), dtype=np.float32)
        ids = np.empty(n_cand, dtype=object)
        
        for i, cand in enumerate(candidates):
            sim_score = cand.get('similarity_score', {})
            scores[i, 0] = sim_score.get('header_path_0', 0.0)
            scores[i, 1] = sim_score.get('header_path_1', 0.0)
            scores[i, 2] = sim_score.get('retrieve', 0.0)
            scores[i, 3] = sim_score.get('full_chunks', 0.0)
            scores[i, 4] = sim_score.get('full_header_path', 0.0)
            scores[i, 5] = sim_score.get('bm25', 0.0)
            scores[i, 6] = sim_score.get('full_chunk_jaccard_similarity', 0.0)
            ids[i] = cand['metadata']['chunk_index']
        
        processed_data.append({
            "scores_matrix": scores,
            "candidate_ids": ids,
            "correct_id": correct_id
        })
        
    return processed_data

# ---------------------------------------------------------
# BƯỚC 2: HÀM TÍNH RECALL SIÊU TỐC (VECTORIZED)
# ---------------------------------------------------------
def fast_evaluate_recall(weights_array, processed_data, k=10):
    """
    Tính Recall hoàn toàn vectorized - không dùng vòng lặp Python.
    """
    total_questions = len(processed_data)
    
    if total_questions == 0:
        return 0.0

    total_correct = 0
    
    for q_data in processed_data:
        scores_matrix = q_data["scores_matrix"]
        candidate_ids = q_data["candidate_ids"]
        correct_id = q_data["correct_id"]
        
        # Tính final scores - một phép nhân vector
        final_scores = scores_matrix @ weights_array
        
        # Lấy top k nhanh nhất
        current_k = min(k, len(candidate_ids))
        
        if current_k == len(candidate_ids):
            total_correct += int(correct_id in candidate_ids)
        else:
            # argpartition: O(n) thay vì O(n*log(n)) của sort
            top_k_indices = np.argpartition(final_scores, -current_k)[-current_k:]
            total_correct += int(correct_id in candidate_ids[top_k_indices])
            
    return total_correct / total_questions

# ---------------------------------------------------------
# BƯỚC 3: OBJECTIVE FUNCTION CHO OPTUNA (Tối ưu)
# ---------------------------------------------------------
def objective(trial, processed_data):
    w_doc = trial.suggest_float('w_doc', 0.0, 1.0)
    w_header = trial.suggest_float('w_header', 0.0, 1.0)
    w_vector = trial.suggest_float('w_vector', 0.0, 1.0)
    w_full_chunks = trial.suggest_float('w_full_chunks', 0.0, 1.0)
    w_full_header = trial.suggest_float('w_full_header', 0.0, 1.0)
    w_bm25 = trial.suggest_float('w_bm25', 0.0, 1.0)
    w_full_chunk_jaccard_similarity = trial.suggest_float('w_full_chunk_jaccard_similarity', 0.0, 1.0)
    
    # Gom 7 trọng số thành numpy array
    weights = np.array([w_doc, w_header, w_vector, w_full_chunks, w_full_header, w_bm25, w_full_chunk_jaccard_similarity], dtype=np.float32)
    
    recall = fast_evaluate_recall(weights, processed_data, k=10)
    return recall

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
