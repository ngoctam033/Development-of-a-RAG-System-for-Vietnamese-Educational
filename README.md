# 📈 Một số bổ sung (so với `Development-of-a-RAG-System-for-Vietnamese-Educational-main`)

> Phạm vi: **Backend + RAG pipeline** (hiệu suất, độ chính xác, logic)

## 📂 Cấu trúc & thành phần mới

- Thêm **Hybrid Retrieval layer**:
  - `rag_pipeline/indexes/faiss_store.py` — FAISS index (dense).
  - `rag_pipeline/retrieval/bm25_store.py` — BM25 (sparse).
  - `rag_pipeline/retrieval/retriever.py` — hợp nhất điểm **dense + sparse + rerank**.
  - `rag_pipeline/retrieval/keyword_extractor.py` — trích xuất keyword hỗ trợ truy hồi.
- Bổ sung script tiện ích:
  - `reindex_faiss.py` — (re)build FAISS nhanh từ corpus.
- Tối ưu module hiện có:
  - `rag_pipeline/generation/llm.py` — điều phối LLM + retry + safety.
  - `rag_pipeline/vectorization/embedder.py` — chuyển sang logger mặc định, tương thích cấu hình mới.
  - `rag_pipeline/processing/chunking.py` — thống nhất logger, giữ nguyên API.

## ⚙️ Pipeline RAG (logic & tham số)

- Thêm file cấu hình rõ ràng:
  - `config/models_config.py`
    - `EMBEDDING_MODEL = "BAAI/bge-m3"` _(đa ngôn ngữ, rất hợp tiếng Việt)_.
    - `RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"`.
  - `config/pipeline_config.py`
    ```python
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 200
    TOP_K_RECALL = 50         # kéo rộng trước khi rerank
    TOP_K_FINAL = 8           # đưa vào LLM sau rerank
    SIMILARITY_THRESHOLD = 0.55
    HYBRID_ALPHA = 0.60       # ưu tiên dense hơn BM25
    FAISS_INDEX_PATH = "data/vector_store/index.faiss"
    ```
- Chuỗi truy hồi mới:
  1. **FAISS (dense)** lấy top-k rộng →
  2. **BM25 (sparse)** bổ sung phủ chỉ mục →
  3. **Cross-Encoder reranker** sắp xếp lại theo mức độ liên quan →
  4. **Chọn TOP_K_FINAL** cho LLM.
- Chuẩn hóa logging: dùng `default_logger` (thay vì `logger` rải rác) để thống nhất đầu ra.

## 🤖 LLM Orchestration

- **Tự động chọn model Gemini** khả dụng (ưu tiên dòng 2.5) và **fallback** nếu model/safety không tương thích.
- **Retry chiến lược**:
  - Thử với `safety_settings` typed; nếu lỗi → chuyển sang dict; nếu vẫn lỗi → tạm **tắt safety** (trong phạm vi an toàn) và retry lần cuối.
- **Prompting** giữ nguyên cấu trúc RAG nhưng ổn định hơn với rerank đầu vào.

## 🧠 Vector hóa & Chỉ mục

- Chuyển embedding từ `all-MiniLM-L6-v2` → **`BAAI/bge-m3`** (đa ngôn ngữ, cải thiện tiếng Việt).
- Chuẩn hóa **FAISS index** (file `.faiss`) + metadata kèm id để truy vết nguồn.
- Giữ khả năng **migrate** từ vector `.pkl` cũ (đường dẫn tương thích trong config).

## 🔍 Truy hồi lai (Hybrid Retrieval)

- **Kết hợp điểm**: `score = α * dense + (1-α) * BM25` với `HYBRID_ALPHA = 0.60`.
- **Rerank bằng Cross-Encoder** sau hợp nhất để lọc nhiễu và đẩy các đoạn “đúng câu hỏi” lên đầu.
- **KeywordExtractor** giúp ổn định truy hồi với câu hỏi ngắn/gãy.

## 📦 Phụ thuộc & môi trường

- `requirements.txt` bổ sung:
  - `faiss-cpu` — chỉ mục & tìm kiếm vector nhanh.
  - `rank-bm25` — BM25 sparse retrieval.
  - (Giữ `sentence_transformers`, `google.generativeai`, …)

## 📊 Hiệu suất & Chất lượng (tác động kỳ vọng)

- **Độ chính xác**:
  - Dense tốt tiếng Việt (BGE-M3) + **BM25 bổ khuyết từ khóa** + **Cross-Encoder rerank** ⇒ tăng **precision@k** và chất lượng trích dẫn.
- **Độ bao phủ**:
  - `TOP_K_RECALL = 50` trước rerank giúp **không bỏ sót** đoạn liên quan (nhất là mô tả học phần/danh mục CTĐT dài).
- **Tốc độ**:
  - **FAISS** thay vì thuần cosine + NumPy ⇒ truy vấn dense nhanh và ổn định ở quy mô lớn.
  - Chu trình **reindex** riêng (`reindex_faiss.py`) rút ngắn thời gian build/rebuild chỉ mục.

---

### Tóm tắt nhanh

**Hybrid (FAISS + BM25 + Rerank)**, **BGE-M3**, tham số truy hồi rõ ràng, **LLM Gemini** có **retry + safety fallback**, chỉ mục FAISS, script reindex, logging thống nhất.

## How to run

```bash
# 1) Environment
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Linux/Mac: source .venv/bin/activate
pip install -U pip
pip install sentence-transformers faiss-cpu rank-bm25 google-generativeai python-dotenv pymupdf4llm

# 2) Config .env
# .env
# GEMINI_API_KEY=YOUR_KEY
# (optional) GEMINI_MODEL_NAME=models/gemini-2.5-flash
# (optional) MAX_CONTEXT_CHARS=12000
# (optional) SHOW_DEBUG=1

# 3) Build index
python main.py

# 4) Ask questions about the curriculum (CLI)
python qa_interface.py
```
