# BÁO CÁO KẾT QUẢ TUẦN 1

Tên đề tài: XÂY DỰNG HỆ THỐNG HỎI ĐÁP TỰ ĐỘNG ỨNG DỤNG KỸ THUẬT LLM OPS VÀ RAG  
Giảng viên hướng dẫn: ThS. Nguyễn Văn Chiến
Thời gian thực hiện: 13/10/2025 - 20/10/2025
Sinh viên thực hiện:

- Nguyễn Ngọc Tâm – 2151040051
- Phạm Hoài Kiệt – 2251150058

---

## 1. Mục tiêu ngắn gọn

Hoàn thiện và ổn định hóa RAG pipeline để xử lý tài liệu PDF tiếng Việt và hỗ trợ QA (hỏi đáp) ngữ cảnh thông qua chuỗi xử lý:  
Trích xuất PDF → Chuyển Markdown → Chia chunk → Vectorize → Truy vấn → Sinh câu trả lời bằng LLM.

---

## 2. Các kết quả chính đạt được

### 2.1. Triển khai end-to-end RAG pipeline

- Trích xuất nội dung PDF và lưu dưới dạng Markdown.
- Chia Markdown thành các chunk có cấu trúc phục vụ vectorization.
- Vector hóa các chunk và lưu vector store để phục vụ tìm kiếm tương đồng.
- Tích hợp mô-đun gọi LLM (Gemini) để sinh câu trả lời dựa trên ngữ cảnh được retrieve.

### 2.2. Cải thiện giao diện QA (qa_interface.py)

- Chuyển sang dạng CLI đơn giản, loại bỏ OOP thừa, xử lý input rỗng và log thông tin đầu vào.
- Thêm bước trích xuất từ khóa (KeyBERT) để tối ưu truy vấn tìm kiếm tài liệu liên quan.
- Hiển thị câu trả lời kèm nguồn tham khảo rõ ràng (header_path & similarity score).

### 2.3. Quản lý cấu hình và bảo mật

- Tách GEMINI_API_KEY ra config riêng.
- Cấu hình vectorization chuyển sang đọc động từ config.pipeline_config, dễ dàng thay đổi khi đổi model.

### 2.4. Logging & Observability

- Thống nhất sử dụng logger chung (utils.logger) thay thế print để dễ theo dõi và debug.

### 2.5. Cập nhật dependency

- Thêm KeyBERT và spaCy vào requirements.txt (cần cài model phù hợp cho tiếng Việt).

---

## 3. Artefacts/Outputs có thể kiểm tra

- Thư mục PROCESSING_DATA_FOLDER_PATH chứa file Markdown đã được extract.
- File/chunks (định dạng JSON hoặc internal format) thể hiện kết quả chunking.
- Vector store tại VECTOR_STORE_PATH (file/DB chứa embeddings).
- Logs chi tiết quá trình chạy (logger outputs).
- QA CLI hoạt động: nhập câu hỏi → trả về answer + sources.

---

## 4. Trạng thái hiện tại & mức độ sẵn sàng

- Mức độ hoàn thiện: pipeline chức năng (MVP) đã hoạt động end-to-end theo local run.
- Cần bổ sung: unit/integration tests, CI automation, và kiểm thử chất lượng kết quả (accuracy / độ phù hợp câu trả lời).
- Sẵn sàng cho: demo nội bộ / smoke-test.

---

## 5. Rủi ro chính (Impact / Likelihood)

- Thiếu test tự động → dễ bị regress khi refactor tiếp theo.
- KeyBERT / spaCy có thể không tối ưu cho tiếng Việt nếu không có model phù hợp → ảnh hưởng chất lượng trích xuất từ khóa và retrieval.
- Thao tác I/O với PDF đa dạng (bảng, hình, encoding) có thể gây lỗi runtime nếu chưa xử lý edge-case.
- Thay đổi embedding model/format có thể phá vỡ tương thích với vector store hiện tại.

---

## 6. Hướng nghiên cứu tiếp theo

1. Hoàn thiện phần đánh giá:

   - Chuẩn hóa dataset test, thu thập bộ câu hỏi mẫu.
   - Thực hiện human evaluation và báo cáo metrics.

2. Tài liệu viết báo cáo luận văn:

   - Mô tả kiến trúc hệ thống, luồng xử lý, lựa chọn thuật toán.
   - Phân tích hạn chế và minh họa qua case study.

3. Phân tích hạn chế & mở rộng:
   - Cải tiến bằng cách fine-tune embedding hoặc keyword extractor cho tiếng Việt.
   - Thử nghiệm vector DB khác, đề xuất chiến lược giảm hallucination.
   - Bổ sung test tự động và smoke test end-to-end để tăng tính tin cậy.

---

## 7. Kết luận ngắn gọn

Đề tài đã hoàn thiện prototype hệ thống RAG end-to-end đáp ứng mục tiêu ban đầu:

- Chứng minh được phương pháp.
- Có artefacts có thể tái tạo (Markdown, chunks, vector store).
- Demo QA hoạt động.

Tuy nhiên, hệ thống hiện mới dừng ở mức ổn định cơ bản, cần tiếp tục:

- Hoàn thiện phần đánh giá (metrics và human evaluation).
- Tối ưu pipeline.
- Bổ sung tài liệu hướng dẫn tái tạo để đảm bảo tính ổn định và độ tin cậy cho phiên bản cuối.
