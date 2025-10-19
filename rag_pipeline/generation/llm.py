"""
LLM generation module for answering questions using Gemini Pro.
"""

import google.generativeai as genai
from typing import Dict, Any

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
        
    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using Gemini based on provided context
        
        Args:
            question (str): User's question
            context (str): Retrieved context for answering
            
        Returns:
            str: Generated answer
        """
        prompt = f"""Bạn là trợ lý trí tuệ nhân tạo chuyên về các chương trình đào tạo đại học. 
        Hãy trả lời câu hỏi dưới đây dựa trên thông tin được cung cấp.

        CONTEXT:
        {context}

        QUESTION: {question}

        INSTRUCTIONS:
        - Trả lời bằng tiếng Việt
        - Chỉ sử dụng thông tin trong context đã cung cấp
        - Nếu không có thông tin đủ để trả lời, hãy nói "Tôi không tìm thấy thông tin đủ để trả lời câu hỏi này"
        - Trả lời ngắn gọn, súc tích nhưng đầy đủ thông tin
        - Nêu rõ nguồn trích dẫn khi cần thiết

        ANSWER:
        """
        # in log prompt for debugging
        print("Generated prompt for LLM:\n", prompt)
        # Generate response with specific configuration
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1000,
                top_p=0.95,
            )
        )
        
        return response.text