"""
LLM generation module for answering questions using Gemini Pro.
"""

from email.mime import text
from urllib import response
import google.generativeai as genai
from config.render_prompt import PROMPT_TEMPLATES
from config.llm_api_config import GeminiApiKeyRotator
from config.render_prompt import render_prompt
from rag_pipeline.retrieval.search import search_similar
from rag_pipeline.question_analysis.keyword_extractor import extract_keywords
from utils.logger import logger
import re
from typing import List, Dict, Any
import time

class GeminiGenerator:
    def __init__(self):
        """
        Initialize the Gemini generator
        
        Args:
            api_key (str): Gemini API key
        """
        self.api_key_rotator = GeminiApiKeyRotator()
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def _generate(self, prompt: str, temperature=0.2, max_output_tokens=1000, top_p=0.95):
        time.sleep(10)  # tránh lỗi rate limit
        try:
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
            return response.text
        except Exception as e:
            return f"[LỖI] {str(e)}"  # Trả về chuỗi lỗi

    def normalize_question(self, question: str,
                           user_chat_history: list = None
                           ) -> str:
        prompt = render_prompt(
            PROMPT_TEMPLATES["question_normalization"]["template"],
            fields=PROMPT_TEMPLATES["question_normalization"]["fields"],
            values={
                "question": question,
                "user_chat_history": user_chat_history
            }
        )
        response = self._generate(prompt)
        """
        Trích xuất câu hỏi đã được chuẩn hóa từ kết quả trả về của agent chuẩn hóa.
        """
        pattern = r"QUESTION CHUẨN HÓA:\s*(.+)"

        match = re.search(pattern, response)
        if match:
            question_normalized = match.group(1).strip()
        else:
            question_normalized = question  # nếu không tìm thấy, giữ nguyên câu hỏi ban đầu
            logger.warning("========= Gemini response normalized question not found =========")
        return question_normalized

    def suggest_next_query(self,
                           vector_store,
                           question: str,
                           reasoning_trace: str) -> dict:
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=50)
        prompt = render_prompt(
            PROMPT_TEMPLATES["next_query_suggestion"]["template"],
            fields=PROMPT_TEMPLATES["next_query_suggestion"]["fields"],
            values={
                "reasoning_trace": reasoning_trace,
                "question": question,
                "context": context_and_sources["context"]
            }
        )
        response = self._generate(prompt)
        # Trích xuất các trường đặc biệt từ response bằng regex không cần tag đóng
        result = {}
        pattern = r"<<([^>]+)>>\s*([\s\S]*?)(?=(<<[^>]+>>|##STOP_REASONING##|$))"
        matches = re.findall(pattern, response)
        for match in matches:
            tag = match[0].strip()
            content = match[1].strip()
            result[tag] = content
        if result["next_query_suggestion"] == "Không cần":
            result["stop_reasoning"] = True
        else:
            result["stop_reasoning"] = False
        return result

    def classify_question(self, question: str) -> dict:
        prompt = render_prompt(
            PROMPT_TEMPLATES["question_classification_and_agentic_strategy"]["template"],
            fields=PROMPT_TEMPLATES["question_classification_and_agentic_strategy"]["fields"],
            values={
                "question": question
            }
        )
        result = {}
        response = self._generate(prompt)
        # PHÂN LOẠI CÂU HỎI
        match_type = re.search(r'PHÂN LOẠI CÂU HỎI:\s*(.*?)(?:\n|$)', response)
        if match_type:
            result["question_type"] = match_type.group(1).strip()

        # CHIẾN LƯỢC THỰC THI AGENTIC RAG
        match_strategy = re.search(r'CHIẾN LƯỢC THỰC THI AGENTIC RAG:\s*(.*?)(?:\n|$)', response)
        if match_strategy:
            result["agentic_strategy"] = match_strategy.group(1).strip()

        # PHƯƠNG PHÁP SUY LUẬN (PROMPT)
        match_prompt = re.search(r'PHƯƠNG PHÁP SUY LUẬN \(PROMPT\):\s*(.*?)(?:\n|$)', response)
        if match_prompt:
            result["reasoning_prompt"] = match_prompt.group(1).strip()

        # GIẢI THÍCH
        match_explain = re.search(r'GIẢI THÍCH:\s*(.*?)(?:\n|$)', response)
        if match_explain:
            result["explanation"] = match_explain.group(1).strip()
        return result

    def final_answer(self,
                        question: str,
                        context: str
        ) -> str:
        prompt = render_prompt(
            PROMPT_TEMPLATES["final_answer_from_reasoning_trace"]["template"],
            fields=PROMPT_TEMPLATES["final_answer_from_reasoning_trace"]["fields"],
            values={
                "question": question,
                "reasoning_trace": context
            }
        )
        response = self._generate(prompt)
        result = {}
        pattern = r"<<(final_answer|sources|reasoning_explanation)>>\s*([\s\S]*?)<</\1>>"
        matches = re.findall(pattern, response, re.IGNORECASE)
        for tag, content in matches:
            result[tag.lower()] = content.strip()
        # Đảm bảo result phải chứa đủ 3 key, nếu không thì trả về response gốc để debug
        required_keys = ["final_answer", "sources", "reasoning_explanation"]
        if not all(k in result and result[k] for k in required_keys):
            logger.warning("Không tách đủ các block bắt buộc từ response, trả về response gốc để debug.")
            return {"raw_response": response}
        return result
    
    def qa_viet_uni(self, question: str,
                    vector_store) -> dict:
        """
        Sinh câu trả lời ngắn gọn cho câu hỏi về chương trình đào tạo đại học, theo định dạng QA_VIET_UNI_PROMPT.
        Args:
            question (str): Câu hỏi của người dùng
            context (str): Văn bản truy xuất liên quan
            user_chat_history (list): Lịch sử hội thoại (List[str]), có thể None
        Returns:
            dict: Kết quả gồm answer, giải thích chi tiết, nguồn tham khảo
        """
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=50)
        prompt = render_prompt(
            PROMPT_TEMPLATES["qa"]["template"],
            fields=PROMPT_TEMPLATES["qa"]["fields"],
            values={
                "question": question,
                "context": context_and_sources["context"],
            }
        )
        response = self._generate(prompt)
        # Tách các phần theo định dạng OUTPUT FORMAT
        result = {}
        answer_match = re.search(r'ANSWER:\s*(.*?)\n\s*GIẢI THÍCH CHI TIẾT:', response, re.DOTALL)
        explain_match = re.search(r'GIẢI THÍCH CHI TIẾT:\s*(.*?)(?:\nNGUỒN THAM KHẢO:|\Z)', response, re.DOTALL)
        sources_match = re.search(r'NGUỒN THAM KHẢO:\s*(.*)', response, re.DOTALL)
        if answer_match:
            result["answer"] = answer_match.group(1).strip()
        if explain_match:
            result["explanation"] = explain_match.group(1).strip()
        if sources_match:
            # Tách từng dòng nguồn tham khảo
            # sources = [line.strip('- ').strip() for line in sources_match.group(1).strip().split('\n') if line.strip()]
            # result["sources"] = sources
            pass
        return result

    def build_context_and_sources(self, question, vector_store, top_k=50):
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