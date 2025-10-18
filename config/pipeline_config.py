RAW_DATA_FOLDER_PATH = "data/raw/"
PROCESSING_DATA_FOLDER_PATH = "data/processed/"
VECTOR_STORE_PATH = "data/vector_store/"
# config/pipeline_config.py

# Chunking
CHUNK_SIZE = 800         # token/ký tự tùy cách bạn tính; 800 là điểm khởi đầu ổn
CHUNK_OVERLAP = 200      # giúp giữ ngữ cảnh liền mạch

# Retrieval
TOP_K_RECALL = 50        # số đoạn kéo về trước khi rerank
TOP_K_FINAL = 8          # số đoạn sau rerank đưa vào LLM
SIMILARITY_THRESHOLD = 0.55  # đừng bỏ các đoạn “biên” có thể đúng
HYBRID_ALPHA = 0.60      # 0.6 ~ dense ưu tiên hơn BM25

# FAISS index file
FAISS_INDEX_PATH = "data/vector_store/index.faiss"

# Lưu ý: nếu code cũ dùng .pkl cho vector, giữ đường dẫn cũ để migrate dần.
