from typing import Dict

class ChatContextManager:
    def __init__(self):
        # In-memory list to store all user questions
        self.user_questions = []

    def append_message(self, question: str):
        # Save the user question in the in-memory list
        if question:
            self.user_questions.append(question)
            # Keep only the 5 most recent questions
            if len(self.user_questions) > 5:
                self.user_questions = self.user_questions[-5:]

    def clear_history(self):
        self.user_questions = []

    def get_user_questions(self) -> list:
        """Return the list of the most recent user questions."""
        return self.user_questions
