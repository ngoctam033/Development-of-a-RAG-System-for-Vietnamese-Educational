
from typing import List, Dict
from llm import LLMlocalGenerator
from ultils.logger import logger
import json
import copy
from typing import Any

class AgenticGeminiRAG(LLMlocalGenerator):
    def __init__(self):
        """
        Initialize the Agentic Gemini RAG generator
        """
        super().__init__()

    def agentic_pipeline(self,
                         question: str,
                         vector_store,
                         user_chat_history: List[str] = None,
                        ) -> Dict:
        """
        Run full agentic RAG pipeline
        Returns a dict with all intermediate results and the full reasoning trace
        """
        normalized_question = ""
        answer = ""
        all_sources = []
        reasoning_trace = {}
        # Step 1: Question Normalization
        normalized_question = self.normalize_question(
            question, user_chat_history
        )
        reasoning_trace["question_normalization"] = {
            "input_question": question,
            "normalized_question": normalized_question
        }
        # Step 2: Question Classification
        classify_question_result = self.classify_question(
            normalized_question
        )

        reasoning_trace["question_classification"] = {
            "input_question": normalized_question,
            "classification_result": classify_question_result
        }
        # Iterative reasoning loop (max 3 iterations)
        max_tier = 3
        for tier in range(1, max_tier + 1):
            query = normalized_question
            reasoning_trace[f"tier_{tier}"] = {}
            next_query_result = self.suggest_next_query(
                question=query,
                vector_store=vector_store,
                reasoning_trace=copy.deepcopy(reasoning_trace)
            )
            reasoning_trace[f"tier_{tier}"] = next_query_result
            if next_query_result.get("stop_reasoning", False):
                break
            if next_query_result.get("next_query_suggestion"):
                query = next_query_result["next_query_suggestion"]
        answer = self.final_answer(
            question=normalized_question,
            context=json.dumps(reasoning_trace, ensure_ascii=False, indent=2)
        )
        reasoning_trace["answer"] = answer
        return {
            "normalized_question": normalized_question,
            "answer": answer["final_answer"],
            "sources": all_sources,
            "reasoning_trace": reasoning_trace
        }
    def agentic_pipeline(self,
                         question: str,
                         user_chat_history: List[str] = None,
                        ) -> Dict:
        """
        Run full agentic RAG pipeline
        Returns a dict with all intermediate results and the full reasoning trace
        """
        normalized_question = question
        answer = ""
        all_sources = []
        reasoning_trace = {}
        # Step 1: Question Normalization
        normalized_question = self.normalize_question(
            question, user_chat_history
        )
        reasoning_trace["question_normalization"] = {
            "input_question": question,
            "normalized_question": normalized_question
        }
        # Step 2: Question Classification
        classify_question_result = self.classify_question(
            normalized_question
        )

        reasoning_trace["question_classification"] = {
            "input_question": normalized_question,
            "classification_result": classify_question_result
        }
        # Iterative reasoning loop (max 3 iterations)
        max_tier = 3
        query = normalized_question
        for tier in range(1, max_tier + 1):
            reasoning_trace[f"tier_{tier}"] = {}
            query_result = self.qa_viet_uni(
                question=query,
            )
            reasoning_trace[f"tier_{tier}"] = {query_result}
            next_query_result = self.suggest_next_query(
                question=normalized_question,
                reasoning_trace=copy.deepcopy(reasoning_trace)
            )
            reasoning_trace[f"tier_{tier}"]["evaluation"] = next_query_result
            if next_query_result.get("stop_reasoning", False):
                break
            if next_query_result.get("next_query_suggestion"):
                query = next_query_result["next_query_suggestion"]
        answer = self.final_answer(
            question=normalized_question,
            context=json.dumps(reasoning_trace, ensure_ascii=False, indent=2)
        )
        reasoning_trace["answer"] = answer
        return {
            "normalized_question": normalized_question,
            "answer":(
                        answer.get("final_answer", "")
                        if "final_answer" in answer
                        else (
                            answer.get("raw_response", "")
                        )
                    ),
            "sources": all_sources,
            "reasoning_trace": reasoning_trace
        }
    

def answer_question(
    question: str,
    user_chat_history,
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
    # print("User chat history:", user_chat_history)
    generator = AgenticGeminiRAG()
    # logger.info("Đang tạo câu trả lời dựa trên ngữ cảnh thu thập được...")
    # Generate answer using LLM
    result = generator.agentic_pipeline(question,
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