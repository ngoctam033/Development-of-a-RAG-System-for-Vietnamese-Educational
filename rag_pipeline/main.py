"""
Main RAG (Retrieval Augmented Generation) pipeline integrating retrieval and generation.
"""

from typing import Dict, Any, List
from rag_pipeline.retrieval.vector_store import VectorStore
from rag_pipeline.generation.llm import GeminiGenerator

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, generator: GeminiGenerator):
        """
        Initialize RAG pipeline with vector store and generator
        
        Args:
            vector_store (VectorStore): Vector store for document retrieval
            generator (GeminiGenerator): LLM generator for answer generation
        """
        self.vector_store = vector_store
        self.generator = generator
        
    def answer_question(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Answer a question using the RAG pipeline
        
        Args:
            question (str): User's question
            top_k (int): Number of similar documents to retrieve
            
        Returns:
            dict: Result containing question, answer and sources
        """
        # Retrieve relevant documents
        related_docs = self.vector_store.search_similar(question, top_k=top_k)
        
        # Build context from retrieved documents
        context = ""
        sources = []
        
        for i, doc in enumerate(related_docs):
            # Add content to context
            context += f"Tài liệu {i+1} ({doc['metadata']['header_path']}):\n{doc['content']}\n\n"
            
            # Collect source information
            source_info = {
                "header_path": doc["metadata"]["header_path"],
                "similarity_score": f"{doc['similarity_score']:.2f}"
            }
            sources.append(source_info)
        
        # Generate answer using LLM
        answer = self.generator.generate_answer(question, context)
        
        # Return complete result
        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }
