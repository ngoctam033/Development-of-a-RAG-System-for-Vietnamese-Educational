"""
LLM generation module for answering questions using Gemini Pro.
"""

import google.generativeai as genai
from config.prompt_templates import PROMPT_TEMPLATES
from config.prompt_templates import render_prompt

class GeminiGenerator:
    def __init__(self, api_key: str):
        """
        Initialize the Gemini generator
        
        Args:
            api_key (str): Gemini API key
        """
        # Configure Gemini client
        genai.configure(api_key=api_key)
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
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = render_prompt(
            prompt_template["template"],
            fields=prompt_template["fields"],
            values={
                "question": question,
                "context": context,
                "user_chat_history": history_text
            }
        )
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1000,
                top_p=0.95,
            )
        )
        return response.text