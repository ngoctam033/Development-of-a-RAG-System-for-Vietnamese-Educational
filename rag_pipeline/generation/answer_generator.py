from typing import Dict, Any
import json
from rag_pipeline.llm.agentic_rag import AgenticGeminiRAG
from rag_pipeline.retrieval.vector_store import load_vector_store
from rag_pipeline.chat_context import context_manager
from utils.logger import logger


def answer_question(
    question: str,
    user_chat_history,
    generator: AgenticGeminiRAG = None,
    vector_store: Dict[str, Any] = None,
    top_k: int = 10,
) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline (functional version)
    Args:
        question (str): User's question
        vector_store (dict): Store returned by load_vector_store
        generator (AgenticGeminiRAG): LLM generator for answer generation
        top_k (int): Number of similar documents to retrieve
        header_path_filter: Optional filter for document headers
        related_docs: Optional list of retrieved documents
    Returns:
        dict: Result containing question, answer and sources
    """
    # If not generator provided
    if generator is None:
        generator = AgenticGeminiRAG()  # Placeholder, should raise error or handle properly
    if vector_store is None:
        vector_store = load_vector_store()
    # print("User chat history:", user_chat_history)



    # logger.info("Đang tạo câu trả lời dựa trên ngữ cảnh thu thập được...")
    # Generate answer using LLM
    result = generator.agentic_pipeline(question,
                                        vector_store,
                                        user_chat_history=user_chat_history
                                        )

    return_dict = {
        "question": question,
        "answer": result.get("answer", ""),
        "reasoning_trace": result.get("reasoning_trace", [])
    }
    #  in ra return
    logger.info("Return dict:\n" + json.dumps(return_dict, ensure_ascii=False, indent=2))
    logger.info("-" * 50)
    # Return all keys from agentic_pipeline result
    return return_dict