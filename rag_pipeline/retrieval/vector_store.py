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
from config.pipeline_config import EMBEDDING_MODEL_NAME

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

    # Load embedding model
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return {
        "vectorized_data": vectorized_data,
        "embeddings": embeddings,
        "faiss_index": faiss_index,
        "embedding_model": embedding_model
    }

def search_similar(query_text: str, store: Dict[str, Any], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Find documents similar to the query text using FAISS
    Args:
        query_text (str): Query text to find similar documents for
        store (dict): Dictionary returned by load_vector_store
        top_k (int): Number of results to return
    Returns:
        list: List of similar documents with similarity scores
    """
    model = store["embedding_model"]
    faiss_index = store["faiss_index"]
    vectorized_data = store["vectorized_data"]

    query_embedding = model.encode(query_text)
    query_embedding = np.array(query_embedding, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)

    scores, indices = faiss_index.search(query_embedding, top_k)
    results = []
    for i, idx in enumerate(indices[0]):
        results.append({
            "content": vectorized_data[idx]["content"],
            "metadata": vectorized_data[idx]["metadata"],
            "similarity_score": float(scores[0][i])
        })
    return results