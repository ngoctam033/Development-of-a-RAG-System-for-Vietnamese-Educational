from typing import Dict, Any
from rag_pipeline.llm.llm import GeminiGenerator
from rag_pipeline.retrieval.vector_store import search_similar
from rag_pipeline.question_analysis.keyword_extractor import extract_keywords
from rag_pipeline.retrieval.vector_store import load_vector_store
from config.llm_api_config import GEMINI_API_KEY
from rag_pipeline.chat_context import context_manager


def answer_question(
    question: str,
    chat_context_manager: context_manager.ChatContextManager,
    generator: GeminiGenerator = None,
    vector_store: Dict[str, Any] = None,
    top_k: int = 100,
    header_path_filter=None,
    related_docs=None
) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline (functional version)
    Args:
        question (str): User's question
        vector_store (dict): Store returned by load_vector_store
        generator (GeminiGenerator): LLM generator for answer generation
        top_k (int): Number of similar documents to retrieve
        header_path_filter: Optional filter for document headers
        related_docs: Optional list of retrieved documents
    Returns:
        dict: Result containing question, answer and sources
    """
    # If not provided, extract keywords and search similar docs
    if header_path_filter is None:
        header_path_filter = extract_keywords(question)
    # If not generator provided
    if generator is None:
        generator = GeminiGenerator(api_key=GEMINI_API_KEY)  # Placeholder, should raise error or handle properly
    if vector_store is None:
        vector_store = load_vector_store()
    if related_docs is None:
        related_docs = search_similar(question, vector_store, top_k=top_k, header_path_filter=header_path_filter)

    # Build context from retrieved documents
    context = ""
    user_chat_history = chat_context_manager.get_user_questions()
    print("User chat history:", user_chat_history)

    sources = []
    for i, doc in enumerate(related_docs):
        context += f"Tài liệu {i+1}:\n{doc['content']}\n\n"
        source_info = {
            "header_path": doc["metadata"]["header_path"],
            "similarity_score": f"{doc['similarity_score']:.2f}"
        }
        sources.append(source_info)

    # Generate answer using LLM
    answer = generator.generate_answer(question, context, user_chat_history)

    # Return complete result
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }