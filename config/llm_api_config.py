import dotenv
import os
dotenv.load_dotenv()

# Lấy tất cả các key có tên GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
GEMINI_API_KEYS = []
for i in range(1, 10):  # Giả sử tối đa 10 key, dừng khi không còn key
	key = os.getenv(f"GEMINI_API_KEY_{i}")
	if key:
		GEMINI_API_KEYS.append(key)
	else:
		break

class GeminiApiKeyRotator:
	def __init__(self, api_keys=None):
		if api_keys is None:
			api_keys = GEMINI_API_KEYS
		self.api_keys = api_keys
		self.index = 0
		self.n = len(api_keys)
		if self.n == 0:
			raise ValueError("No Gemini API keys found in environment.")

	def get_next_key(self):
		key = self.api_keys[self.index]
		self.index = (self.index + 1) % self.n
		return key