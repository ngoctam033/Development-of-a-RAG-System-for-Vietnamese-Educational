"""
Main RAG (Retrieval Augmented Generation) pipeline integrating retrieval and generation.
Functional (non-OOP) version.
"""

from typing import Dict, Any, List
from rag_pipeline.retrieval.vector_store import search_similar
from rag_pipeline.generation.llm import GeminiGenerator
from utils.logger import logger
from question_analysis.keyword_extractor import extract_keywords
from config.pipeline_config import (
    PROCESSING_DATA_FOLDER_PATH, 
    VECTOR_STORE_PATH,
    EMBEDDING_MODEL_NAME,
    VECTORIZATION_CONFIG
)

def answer_question(question: str, vector_store: Dict[str, Any], generator: GeminiGenerator, top_k: int = 3) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline (functional version)
    Args:
        question (str): User's question
        vector_store (dict): Store returned by load_vector_store
        generator (GeminiGenerator): LLM generator for answer generation
        top_k (int): Number of similar documents to retrieve
    Returns:
        dict: Result containing question, answer and sources
    """
    header_path_filter = extract_keywords(question, VECTOR_STORE_PATH)
    # Retrieve relevant documents
    related_docs = search_similar(question, vector_store, top_k=top_k, header_path_filter=header_path_filter)

    # Build context from retrieved documents
    context = ""
    sources = []
    for i, doc in enumerate(related_docs):
        context += f"Tài liệu {i+1}:\n{doc['content']}\n\n"
        source_info = {
            "header_path": doc["metadata"]["header_path"],
            "similarity_score": f"{doc['similarity_score']:.2f}"
        }
        sources.append(source_info)

    # Generate answer using LLM
    answer = generator.generate_answer(question, context)

    # Return complete result
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }
