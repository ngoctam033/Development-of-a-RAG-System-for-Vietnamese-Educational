"""
LLM generation module for answering questions using Gemini Pro.
"""

import google.generativeai as genai
from config.prompt_templates import PROMPT_TEMPLATES
from config.llm_api_config import GeminiApiKeyRotator
from config.prompt_templates import render_prompt

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
    def __init__(self, api_key: str):
        """
        Initialize the Agentic Gemini RAG generator
        Args:
            api_key (str): Gemini API key
        """
        super().__init__(api_key=api_key)

    def plan(self, question: str, context: str, user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            PROMPT_TEMPLATES["planning"]["template"],
            fields=PROMPT_TEMPLATES["planning"]["fields"],
            values={
                "question": question,
                "context": None,
                "user_chat_history": None
            }
        )
        response = self._generate(prompt)
        return response.text

    def reason(self, plan: str, context: str, user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            PROMPT_TEMPLATES["reasoning"]["template"],
            fields=PROMPT_TEMPLATES["reasoning"]["fields"],
            values={
                "plan": plan,
                "context": context,
                "user_chat_history": history_text
            }
        )
        return self._generate(prompt)

    def act(self, reasoning: str, context: str, user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            PROMPT_TEMPLATES["acting"]["template"],
            fields=PROMPT_TEMPLATES["acting"]["fields"],
            values={
                "reasoning": reasoning,
                "context": context,
                "user_chat_history": history_text
            }
        )
        return self._generate(prompt)

    def observe(self, action: str, context: str, user_chat_history: list) -> str:
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            PROMPT_TEMPLATES["observing"]["template"],
            fields=PROMPT_TEMPLATES["observing"]["fields"],
            values={
                "action": action,
                "context": context,
                "user_chat_history": history_text
            }
        )
        return self._generate(prompt)

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
        return self._generate(prompt)

    def agentic_pipeline(self, question: str, context: str, user_chat_history: list) -> dict:
        """
        Run full agentic RAG pipeline: Planning -> Reasoning -> Acting -> Observing -> QA
        Returns a dict with all intermediate results
        """
        plan = self.plan(question, context, user_chat_history)
        reasoning = self.reason(plan, context, user_chat_history)
        action = self.act(reasoning, context, user_chat_history)
        observation = self.observe(action, context, user_chat_history)
        answer = self.answer(question, context, user_chat_history)
        return {
            "plan": plan,
            "reasoning": reasoning,
            "action": action,
            "observation": observation,
            "answer": answer
        }