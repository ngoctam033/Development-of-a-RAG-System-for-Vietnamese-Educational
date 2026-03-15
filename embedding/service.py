import bentoml
import os
from sentence_transformers import SentenceTransformer

# Load model from the mapped path
MODEL_PATH = "/opt/models/embedding-model"

@bentoml.service(
    name="rag_embedding_service",
    traffic={"timeout": 60},
)
class EmbeddingService:
    def __init__(self):
        print(f"Loading model from {MODEL_PATH}...")
        self.model = SentenceTransformer(MODEL_PATH)
        print("Model loaded successfully.")

    @bentoml.api
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Gencode embeddings for a list of input texts.
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
