"""
LLM generation module for answering questions using Gemini Pro.
"""

import google.generativeai as genai
from config.prompt_templates import PROMPT_TEMPLATES
from config.llm_api_config import GeminiApiKeyRotator
from config.prompt_templates import render_prompt
from rag_pipeline.retrieval.search import search_similar
from rag_pipeline.question_analysis.keyword_extractor import extract_keywords
from utils.logger import logger
import re
from typing import List

class GeminiGenerator:
    def __init__(self):
        """
        Initialize the Gemini generator
        
        Args:
            api_key (str): Gemini API key
        """
        self.api_key_rotator = GeminiApiKeyRotator()
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
    def generate_answer(self,
                        question: str,
                        context: str,
                        user_chat_history: list,
                        prompt_template: dict = PROMPT_TEMPLATES["qa"]) -> str:
        """
        Generate an answer using Gemini based on provided context and external prompt template
        
        Args:
            question (str): User's question
            context (str): Retrieved context for answering
            user_chat_history (list): User's chat history
            prompt_template (dict): Dict chứa template và fields
        Returns:
            str: Generated answer
        """
        # Configure Gemini client
        genai.configure(api_key=self.api_key_rotator.get_next_key())
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            prompt_template["template"],
            fields=prompt_template["fields"],
            values={
                "question": question,
                "context": context,
                "user_chat_history": history_text,
                "results": context,
            }
        )
        response = self._generate(prompt, temperature=0.2, max_output_tokens=1000, top_p=0.95)
        return response.text

    def _generate(self, prompt: str, temperature=0.2, max_output_tokens=1000, top_p=0.95) -> str:
        # Configure Gemini client
        genai.configure(api_key=self.api_key_rotator.get_next_key())
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
            )
        )
        return response

class AgenticGeminiRAG(GeminiGenerator):
    def __init__(self):
        """
        Initialize the Agentic Gemini RAG generator
        """
        super().__init__()

    def normalize_question(self, question: str) -> str:
        prompt = render_prompt(
            PROMPT_TEMPLATES["question_normalization"]["template"],
            fields=PROMPT_TEMPLATES["question_normalization"]["fields"],
            values={
                "question": question
            }
        )
        logger.info("=========Gemini Question Normalization Prompt=========")
        logger.info(prompt)
        response = self._generate(prompt)
        """
        Trích xuất câu hỏi đã được chuẩn hóa từ kết quả trả về của agent chuẩn hóa.
        """
        pattern = r"QUESTION CHUẨN HÓA:\s*(.+)"
        match = re.search(pattern, response.text)
        if match:
            question_normalized = match.group(1).strip()
        logger.info("========= Gemini response normalized question =========")
        logger.info(question_normalized)
        logger.info("=============================================")
        return question_normalized


    def plan(self, question: str,
             user_chat_history: list,
             vector_store) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        context_and_sources = self.build_context_and_sources(question,vector_store,top_k=10)
        prompt = render_prompt(
            PROMPT_TEMPLATES["planning"]["template"],
            fields=PROMPT_TEMPLATES["planning"]["fields"],
            values={
                "question": question,
                "context": context_and_sources["context"],
                "user_chat_history": history_text
            }
        )
        response = self._generate(prompt)
        """
        Tách các bước [STEP n]: ... từ đoạn text và lưu vào một chuỗi, mỗi bước trên một dòng.
        """
        pattern = r"\[STEP\s*\d+\]:\s*(.+)"
        steps = re.findall(pattern, response.text)
        result = steps
        return {
            "result": result,
            "sources": context_and_sources["sources"]
        }

    def reason(self,
               plan: str,
               question: str,
               vector_store) -> str:
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=10)
        prompt = render_prompt(
            PROMPT_TEMPLATES["reasoning"]["template"],
            fields=PROMPT_TEMPLATES["reasoning"]["fields"],
            values={
                "question": question,
                "retrieved_docs": context_and_sources["context"]
            }
        )
        response = self._generate(prompt)
        logger.info("=========Gemini Reasoning Prompt=========")
        logger.info(prompt)
        logger.info("========= Gemini response reasoning =========")
        logger.info(response.text)
        logger.info("=============================================")
        return response.text

    def act(self,
            steps: List,
            question: str,
            vector_store,
            ) -> str:
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=10)
        prompt = render_prompt(
            PROMPT_TEMPLATES["acting"]["template"],
            fields=PROMPT_TEMPLATES["acting"]["fields"],
            values={
                "reasoning": None,
                "context": None,
            }
        )
        response = self._generate(prompt)
        logger.info("=========Gemini Acting Prompt=========")
        logger.info(prompt)       
        logger.info("========= Gemini response acting =========")
        logger.info(response.text)
        logger.info("===========================================")
        return response.text

    def observe(self, action: str,
                vector_store,
                question: str,
                context: str,
                user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=10)
        prompt = render_prompt(
            PROMPT_TEMPLATES["observing"]["template"],
            fields=PROMPT_TEMPLATES["observing"]["fields"],
            values={
                "action": action,
                "context": context,
                "user_chat_history": history_text
            }
        )
        response = self._generate(prompt)
        logger.info("=========Gemini Observing Prompt=========")
        logger.info(prompt)
        logger.info("========= Gemini response observing =========")
        logger.info(response.text)
        logger.info("=============================================")
        return response.text

    def answer(self, question: str, context: str, user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            PROMPT_TEMPLATES["qa"]["template"],
            fields=PROMPT_TEMPLATES["qa"]["fields"],
            values={
                "question": question,
                "context": context,
                "user_chat_history": history_text
            }
        )
        response = self._generate(prompt)
        logger.info("=========Gemini Observing Prompt=========")
        logger.info(prompt)
        logger.info("========= Gemini response answer =========")
        logger.info(response.text)
        logger.info("===========================================")
        return response.text
    
    def build_context_and_sources(self, question, vector_store, top_k=10):
        """
        Truy xuất các tài liệu liên quan và xây dựng context, sources cho pipeline agentic RAG.
        """
        context = ""
        sources = []
        header_path_filter = extract_keywords(question)
        related_docs = search_similar(
            question,
            vector_store,
            top_k=top_k,
            header_path_filter=header_path_filter
        )
        for i, doc in enumerate(related_docs):
            context += f"Tài liệu {i+1}:\n{doc['content']}\n\n"
            source_info = {
                "header_path": doc["metadata"]["header_path"],
                "similarity_score": f"{doc['similarity_score']:.2f}"
            }
            sources.append(source_info)
        return {
            "context": context,
            "sources": sources
        }
    def agentic_pipeline(self,
                         question: str,
                         user_chat_history: list,
                         vector_store
                        ) -> dict:
        """
        Run full agentic RAG pipeline: Planning -> Reasoning -> Acting -> Observing -> QA
        Returns a dict with all intermediate results
        """
        sources = []
        # question_normalized = self.normalize_question(question)
        question_normalized = question
        plan = self.plan(question_normalized,
                         user_chat_history,
                         vector_store
                         )
        sources.extend(plan["sources"])
        action = self.act(plan["result"],
                         question,
                         vector_store
                         )
        answer = plan
        # answer = self.answer(question,
        #                      user_chat_history)
        logger.info("========= Sources used in Agentic RAG Pipeline =========")
        logger.info(sources)
        logger.info("========================================================")
        return {
            "plan": plan,
            # "reasoning": reasoning,
            # "action": action,
            # "observation": observation,
            "answer": answer,
            "sources": sources
        }