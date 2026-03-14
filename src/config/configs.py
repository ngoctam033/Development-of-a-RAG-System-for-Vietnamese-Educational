import os
from dotenv import load_dotenv

load_dotenv()

# QUAN TRỌNG: Bật chế độ Offline để tránh lỗi ReadTimeout khi đã có model
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

EMBEDDING_MODEL_NAME = "AITeamVN/Vietnamese_Embedding"
CROSS_ENCODER_MODEL_NAME = 'cross-encoder/ms-marco-MiniLM-L-6-v2'

# Path configuration based on PROJECT_STRUCTURE.md
RAW_DATA_FOLDER_PATH = "data/raw/"
INTERMEDIATE_DATA_FOLDER_PATH = "data/intermediate/"
PROCESSING_DATA_FOLDER_PATH = "data/processed/"
VECTOR_STORE_PATH = "data/vector_store/"

VECTORIZATION_CONFIG = {
    "batch_size": 32
}

# Lấy tất cả các key có tên GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...
GEMINI_API_KEYS = []
for i in range(1, 10):  # Giả sử tối đa 10 key, dừng khi không còn key
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        GEMINI_API_KEYS.append(key)
    else:
        break

MINIO_CONFIG = {
    "endpoint": os.getenv("MINIO_ENDPOINT", "rag-minio:9000"),
    "access_key": os.getenv("MINIO_ROOT_USER", "admin"),
    "secret_key": os.getenv("MINIO_ROOT_PASSWORD", "admin123"),
    "secure": os.getenv("MINIO_SECURE", "False").lower() == "true",
    "bucket": os.getenv("MINIO_BUCKET", "rag"),
    "region": os.getenv("MINIO_REGION", "us-east-1")
}


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


def load_prompt(file_path):
    # Determine the directory where this script is located (src/config/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Prompts are located at src/prompts/
    full_path = os.path.abspath(os.path.join(current_dir, "..", "prompts", file_path))
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


# Prompt Templates loaded from external files
FINAL_ANSWER_FROM_REASONING_TRACE_PROMPT = load_prompt("final_answer_from_reasoning_trace.txt")
EVALUATE_REASONING_TRACE_COMPLETENESS_PROMPT = load_prompt("evaluate_reasoning_trace_completeness.txt")
NEXT_QUERY_SUGGESTION_PROMPT = load_prompt("next_query_suggestion.txt")
QUESTION_CLASSIFICATION_AND_AGENTIC_STRATEGY_PROMPT = load_prompt("question_classification_and_agentic_strategy.txt")
QUESTION_NORMALIZATION_PROMPT = load_prompt("question_normalization.txt")
QA_VIET_UNI_PROMPT = load_prompt("qa_viet_uni.txt")
QUERY_TO_HEADER_PROMPT = load_prompt("query_to_header.txt")