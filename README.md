# Hệ thống RAG cho Hỏi Đáp Chương Trình Đào Tạo (Vietnamese Educational RAG System)

## Giới thiệu

Hệ thống này sử dụng mô hình RAG (Retrieval Augmented Generation) để xây dựng một nền tảng hỏi đáp cho tài liệu giáo dục tiếng Việt. Pipeline gồm các bước: trích xuất dữ liệu từ PDF, phân đoạn (chunking), vector hóa, lưu trữ và tìm kiếm ngữ nghĩa, kết hợp với mô hình sinh để trả lời tự động.

## Các thành phần chính

### 1. Extraction & Chunking
- Trích xuất nội dung từ file PDF sang Markdown.
- Phân đoạn tài liệu thành các chunk nhỏ, lưu metadata cho từng chunk.

### 2. Vectorization
- Sử dụng SentenceTransformer để chuyển đổi các chunk thành vector embeddings.
- Lưu trữ embeddings và metadata vào file pickle và JSON.

### 3. Vector Store & Retrieval
- Sử dụng FAISS để xây dựng chỉ mục tìm kiếm ngữ nghĩa.
- Hàm `search_similar` cho phép tìm kiếm các chunk tương tự với câu hỏi đầu vào, có thể lọc theo `header_path`.

### 4. Keyword Extraction
- Sử dụng KeyBERT và các phương pháp tiền xử lý để trích xuất từ khóa từ câu hỏi.
- Từ khóa được dùng để lọc các chunk liên quan trong quá trình truy vấn.

### 5. Generation
- Sử dụng mô hình Gemini (Google Generative AI) để sinh câu trả lời dựa trên ngữ cảnh các chunk liên quan.

### 6. Command Line Interface
- Giao diện dòng lệnh cho phép người dùng nhập câu hỏi, nhận câu trả lời và nguồn tham khảo.

## Cách sử dụng

1. **Chạy pipeline xử lý dữ liệu:**
   - Thực thi file main.py để trích xuất, chunking và vector hóa dữ liệu.
   - Kết quả lưu tại thư mục cấu hình trong `VECTOR_STORE_PATH`.

2. **Khởi động hệ thống hỏi đáp:**
   - Chạy file qa_interface.py để sử dụng giao diện hỏi đáp CLI.
   - Nhập câu hỏi, hệ thống sẽ trả về câu trả lời và nguồn tham khảo.

3. **Tìm kiếm ngữ nghĩa:**
   - Hàm `search_similar` trong `vector_store.py` cho phép tìm kiếm các chunk tương tự với câu hỏi, có thể lọc theo `header_path`.

## Yêu cầu cài đặt

- Python >= 3.8
- Các thư viện: numpy, sentence_transformers, keybert, spacy, google.generativeai, pymupdf4llm, faiss

Cài đặt nhanh:
```bash
pip install -r requirements.txt
```

## Cấu trúc thư mục

- rag_pipeline: Chứa các module pipeline (extraction, chunking, vectorization, retrieval, generation)
- question_analysis: Trích xuất từ khóa từ câu hỏi
- data: Lưu trữ dữ liệu gốc, dữ liệu đã xử lý, vector store
- config: Cấu hình pipeline, model, API key
- utils: Các hàm tiện ích, logger

## Ví dụ sử dụng

```bash
python main.py
python qa_interface.py
```

## Tác giả & Liên hệ

- Phát triển bởi nhóm nghiên cứu AI cho giáo dục Việt Nam.
- Liên hệ: [nguyenngoctam0332003@gmail.com](mailto:nguyenngoctam0332003@gmail.com)