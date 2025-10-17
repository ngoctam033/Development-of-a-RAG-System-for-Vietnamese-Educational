"""
Vector store module for similarity search functionality.
Handles loading and searching through vectorized documents.
"""

import pickle
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class VectorStore:
    def __init__(self, vector_store_path: str = "data/vector_store/vectorized_data.pkl"):
        """
        Initialize the vector store with pre-computed embeddings
        
        Args:
            vector_store_path (str): Path to the pickle file containing vectorized data
        """
        self.vector_store_path = vector_store_path
        self.vectorized_data = None
        self.embeddings = None
        self.model = None
        
        # Load data on initialization
        self.load_vector_store()
        
    def load_vector_store(self) -> None:
        """Load vectorized data from pickle file"""
        print("\n📚 Đang tải dữ liệu vector từ file...")
        
        with open(self.vector_store_path, "rb") as f:
            self.vectorized_data = pickle.load(f)
            
        self.embeddings = np.array([item["embedding"] for item in self.vectorized_data])
        print(f"✅ Đã tải {len(self.vectorized_data)} documents với vector embeddings")
        print(f"📊 Vector dimensions: {len(self.embeddings[0])}")
        
    def get_embedding_model(self) -> SentenceTransformer:
        """
        Load or return cached embedding model
        
        Returns:
            SentenceTransformer: The embedding model
        """
        if self.model is None:
            self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return self.model
        
    def search_similar(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find documents similar to the query text
        
        Args:
            query_text (str): Query text to find similar documents for
            top_k (int): Number of results to return
            
        Returns:
            list: List of similar documents with similarity scores
        """
        # Get query embedding
        model = self.get_embedding_model()
        query_embedding = model.encode(query_text)
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "content": self.vectorized_data[idx]["content"],
                "metadata": self.vectorized_data[idx]["metadata"],
                "similarity_score": float(similarities[idx])
            })
        
        return results