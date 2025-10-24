"""
Vector store module for similarity search functionality.
Handles loading and searching through vectorized documents.
Functional (non-OOP) version using FAISS.
"""

import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import faiss
from utils.logger import logger
from config.models_config import EMBEDDING_MODEL_NAME
import os

def load_vector_store(vector_store_path: str = "data/vector_store/vectorized_data.pkl") -> Dict[str, Any]:
    """
    Load vectorized data from pickle file and build FAISS index
    Returns a dict with vectorized_data, embeddings, faiss_index, and embedding_model
    """
    logger.info("📚 Đang tải dữ liệu vector từ file...")
    with open(vector_store_path, "rb") as f:
        vectorized_data = pickle.load(f)
    embeddings = np.array([item["embedding"] for item in vectorized_data]).astype('float32')
    logger.info(f"✅ Đã tải {len(vectorized_data)} documents với vector embeddings")
    logger.info(f"📊 Vector dimensions: {len(embeddings[0])}")

    # Build FAISS index
    dim = embeddings.shape[1]
    faiss_index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    faiss_index.add(embeddings)

    # Load embedding model from local or download if not available
    model_path = ".models/sentence-transformers"  # Thư mục lưu trữ model
    if not os.path.exists(model_path):
        logger.info("📥 Model chưa tồn tại, đang tải từ Hugging Face...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        embedding_model.save(model_path)  # Lưu model vào thư mục local
        logger.info(f"✅ Model đã được tải và lưu tại {model_path}")
    else:
        logger.info(f"📂 Đang tải model từ thư mục local: {model_path}")
        embedding_model = SentenceTransformer(model_path)

    return {
        "vectorized_data": vectorized_data,
        "embeddings": embeddings,
        "faiss_index": faiss_index,
        "embedding_model": embedding_model
    }