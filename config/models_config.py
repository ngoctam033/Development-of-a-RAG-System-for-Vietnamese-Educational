# config/models_config.py

# Embedding khuyến nghị (đa ngôn ngữ tốt, rất hợp tiếng Việt)
EMBEDDING_MODEL = "BAAI/bge-m3"  # hoặc "intfloat/multilingual-e5-base"

# Reranker (cross-encoder) để lọc Top-k thật “đúng câu hỏi”
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# (Giữ nguyên phần LLM sinh trả lời nếu đã cấu hình Gemini/OpenAI v.v.)
