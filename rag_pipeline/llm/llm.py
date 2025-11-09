"""
LLM generation module for answering questions using Gemini Pro.
"""

from email.mime import text
from urllib import response
import google.generativeai as genai
from config.prompt_templates import PROMPT_TEMPLATES
from config.llm_api_config import GeminiApiKeyRotator
from config.prompt_templates import render_prompt
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
        return response

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
        logger.info("========= Gemini response normalized question =========")
        logger.info(question_normalized)
        logger.info("=============================================")
        return question_normalized

    def suggest_next_query(self,
                           vector_store,
                           question: str,
                           reasoning_trace: str) -> dict:
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=10)
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
        logger.info("========= Gemini response for next query suggestion =========")
        logger.info(response)
        logger.info("=============================================")
        # Trích xuất các trường đặc biệt từ response bằng regex không cần tag đóng
        result = {}
        pattern = r"<<([^>]+)>>\s*([\s\S]*?)(?=(<<[^>]+>>|##STOP_REASONING##|$))"
        matches = re.findall(pattern, response)
        for match in matches:
            tag = match[0].strip()
            content = match[1].strip()
            result[tag] = content
        result["stop_reasoning"] = bool(re.search(r'##STOP_REASONING##', response))
        #  in ra result
        logger.info("========= Parsed next query suggestion result =========")
        logger.info(result)
        logger.info("=============================================")
        return result
    
    def evaluate_reasoning_trace_completeness(self,
                                            question: str,
                                            reasoning_trace: str) -> dict:
        prompt = render_prompt(
            PROMPT_TEMPLATES["evaluate_reasoning_trace_completeness"]["template"],
            fields=PROMPT_TEMPLATES["evaluate_reasoning_trace_completeness"]["fields"],
            values={
                "question": question,
                "reasoning_trace": reasoning_trace
            }
        )
        response = self._generate(prompt)
        # Lấy trạng thái lặp lại tìm kiếm

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
        steps = re.findall(pattern, response)
        result = steps
        return {
            "result": result,
            "sources": context_and_sources["sources"]
        }

    def evaluate_answer_completeness(self,
                                     question: str,
                                     answer: str) -> dict:
        prompt = render_prompt(
            PROMPT_TEMPLATES["answer_completeness_evaluation"]["template"],
            fields=PROMPT_TEMPLATES["answer_completeness_evaluation"]["fields"],
            values={
                "question": question,
                "answer": answer
            }
        )
        response = self._generate(prompt)
        # Lấy trạng thái lặp lại tìm kiếm
        repeat_search = False
        repeat_match = re.search(r'#LẶP_LẠI_TÌM_KIẾM#:\s*(YES|NO)', response)
        if repeat_match:
            repeat_search = True if repeat_match.group(1) == "YES" else False
        # Tách phần đánh giá độ đầy đủ
        completeness_match = re.search(
            r'ĐÁNH GIÁ ĐỘ ĐẦY ĐỦ:\s*(.*?)\n\s*CÂU HỎI CẦN LÀM RÕ TIẾP THEO:', response, re.DOTALL)
        completeness_evaluation = completeness_match.group(1).strip() if completeness_match else ""
        # Tách phần câu hỏi cần làm rõ tiếp theo
        next_question_match = re.search(
            r'CÂU HỎI CẦN LÀM RÕ TIẾP THEO:\s*-\s*(.*?)\n\s*#LẶP_LẠI_TÌM_KIẾM#:', response, re.DOTALL)
        next_question = next_question_match.group(1).strip() if next_question_match else ""
        return {
            "repeat_search": repeat_search,
            "completeness_evaluation": completeness_evaluation,
            "next_question": next_question
        }

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
        return response
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
        return response

    def act(self,
            plan: Dict[str, List[str]],
            vector_store,
            ) -> str:
        # lấy step trong plan
        steps = plan["result"]
        # Biến lưu kết quả thực thi từng step
        step_results = []
        # Biến lưu kết quả tích lũy để truyền vào context của step sau
        accumulated_result = ""
        # duyệt qua từng step trong plan để thực hiện action
        for step in steps:
            # context sẽ gồm cả context truy xuất và kết quả các step trước (nếu có)
            context_and_sources = self.build_context_and_sources(step, vector_store, top_k=10)
            # Ghép kết quả các step trước vào context
            context = context_and_sources["context"]
            if accumulated_result:
                context += f"\nKẾT QUẢ CÁC STEP TRƯỚC:\n{accumulated_result}\n"
            prompt = render_prompt(
                PROMPT_TEMPLATES["executing_step"]["template"],
                fields=PROMPT_TEMPLATES["executing_step"]["fields"],
                values={
                    "step": step,
                    "context": context,
                }
            )
            response = self._generate(prompt)
            # Lưu kết quả thực thi của step
            step_results.append(response)
            # Cộng dồn kết quả cho step tiếp theo
            accumulated_result += f"\n[STEP]: {step}\n[RESULT]: {response}\n"
            logger.info(f"Đang thực hiện step: {step}")
        return step_results

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
        logger.info(response)
        logger.info("=============================================")
        return response

    def answer(self,
            question: str,
            vector_store) -> str:
        context_and_sources = self.build_context_and_sources(question, vector_store, top_k=10)
        prompt = render_prompt(
            PROMPT_TEMPLATES["answer"]["template"],
            fields=PROMPT_TEMPLATES["answer"]["fields"],
            values={
                "question": question,
                "context": context_and_sources["context"]
            }
        )
        response = self._generate(prompt)
        answer_match = re.search(r'ANSWER:\s*(.*?)\n\s*GIẢI THÍCH CHI TIẾT:', response, re.DOTALL)
        answer = ""
        if answer_match:
            answer = answer_match.group(1).strip()
        logger.info("========= Gemini response answer with suggestion =========")
        logger.info(f"Answer: {answer}")
        logger.info("===========================================")
        return {
            "answer": answer,
        }
    
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