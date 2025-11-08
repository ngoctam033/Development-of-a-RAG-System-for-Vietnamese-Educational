from typing import Dict, Any
from rag_pipeline.llm.llm import AgenticGeminiRAG
from rag_pipeline.retrieval.vector_store import load_vector_store
from rag_pipeline.chat_context import context_manager
from utils.logger import logger


def answer_question(
    question: str,
    chat_context_manager: context_manager.ChatContextManager,
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
    user_chat_history = chat_context_manager.get_user_questions()
    # print("User chat history:", user_chat_history)



    # logger.info("Đang tạo câu trả lời dựa trên ngữ cảnh thu thập được...")
    # Generate answer using LLM
    result = generator.agentic_pipeline(question,
                                        user_chat_history,
                                        vector_store=vector_store
                                        )


    # Return complete result
    return {
        "question": question,
        "plan": result["plan"],
        # "reasoning": result["reasoning"],
        # "action": result["action"],
        # "observation": result["observation"],
        "answer": result["answer"],
        "sources": result["sources"]
    }