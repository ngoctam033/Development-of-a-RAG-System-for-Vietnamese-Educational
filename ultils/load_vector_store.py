
from typing import Dict, List, Any

import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
# from configs import EMBEDDING_MODEL_NAME
from ultils.logger import logger
def load_vector_store(vector_store_path: str = "data/vector_store/vectorized_data.pkl") -> Dict[str, Any]:
    """
    Load vectorized data from pickle file and build FAISS index
    Returns a dict with vectorized_data, embeddings, faiss_index, and embedding_model
    """
    #logger.info("📚 Đang tải dữ liệu vector từ file...")
    with open(vector_store_path, "rb") as f:
        vectorized_data = pickle.load(f)

    return vectorized_data