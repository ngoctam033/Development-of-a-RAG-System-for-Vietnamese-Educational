"""
LLM generation module for answering questions using Gemini Pro.
"""

import google.generativeai as genai

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
                        user_chat_history: list) -> str:
        """
        Generate an answer using Gemini based on provided context
        
        Args:
            question (str): User's question
            context (str): Retrieved context for answering
            user_chat_history (list): User's chat history
        Returns:
            str: Generated answer
        """
    # Format user chat history for prompt
        history_text = "\n".join([f"- {q}" for q in user_chat_history]) if user_chat_history else "Không có lịch sử câu hỏi trước đó."
        prompt = f"""Bạn là trợ lý trí tuệ nhân tạo chuyên về các chương trình đào tạo đại học.
Hãy trả lời câu hỏi dưới đây dựa trên thông tin được cung cấp trong phần CONTEXT và lịch sử hội thoại trước đó của người dùng.

USER CHAT HISTORY:
{history_text}

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS (bắt buộc):
1) Trả lời NGẮN GỌN và RÕ RÀNG bằng tiếng Việt — phần "ANSWER" phải chứa câu trả lời trực tiếp, tối đa 3 câu.
2) Ngay sau phần ANSWER, thêm một phần "GIẢI THÍCH CHI TIẾT" giải thích vì sao câu trả lời như vậy — trình bày chính xác các bước suy luận (step-by-step).
3) Trong phần "GIẢI THÍCH CHI TIẾT", cho biết CĂN CỨ cụ thể từ CONTEXT cho mỗi bước, bằng cách:
- Trích dẫn chính xác (tối đa 200 ký tự) đoạn văn hoặc dòng hỗ trợ (viết nguyên văn trong ngoặc kép).
- Ghi chú vị trí/trích nguồn nếu có (ví dụ: header/section hoặc tên file).
4) Nếu CONTEXT không đủ thông tin để trả lời hoặc để chứng minh một luận điểm, viết rõ: "Tôi không tìm thấy thông tin đủ để trả lời câu hỏi này" và chỉ ra phần thiếu.
5) Không đưa thông tin ngoài CONTEXT. Nếu phải suy đoán, đánh dấu rõ là "suy đoán" và nêu cơ sở.
6) Ở cuối, cung cấp mục "NGUỒN THAM KHẢO" liệt kê các header/section trích dẫn trong phần giải thích.

OUTPUT FORMAT (phải đúng định dạng):
ANSWER:
<ngắn gọn>

GIẢI THÍCH CHI TIẾT:
1) Bước 1: ... 
- Căn cứ: "..." (vị trí)
2) Bước 2: ...
- Căn cứ: "..." (vị trí)
...

NGUỒN THAM KHẢO:
- Header/Section: dòng hoặc tiêu đề trích dẫn

Bắt đầu trả lời bây giờ.
"""
        # in log prompt for debugging
        # print("Generated prompt for LLM:\n", prompt)
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