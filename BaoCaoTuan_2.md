
# BÁO CÁO KẾT QUẢ TUẦN 2

**Tên đề tài:** Xây dựng hệ thống hỏi đáp tự động ứng dụng kỹ thuật LLM Ops và RAG  
**Giảng viên hướng dẫn:** ThS. Nguyễn Văn Chiến  
**Sinh viên thực hiện:**
- Nguyễn Ngọc Tâm - 2151040051  
- Phạm Hoài Kiệt - 2251150058

**Thời gian thực hiện:** 20/10/2025 - 27/10/2025

---

## 1. Mục tiêu
Báo cáo tóm tắt kết quả, các điểm cải tiến so với tuần 1, hạn chế còn tồn tại và kế hoạch tuần 3.

---

## 2. Kết quả đạt được

- Hoàn thiện pipeline vector hóa và lưu trữ dữ liệu: Đã xây dựng quy trình đọc tài liệu, chunking, embedding và lưu trữ vector.
- Bổ sung chức năng trích xuất từ khóa trong câu hỏi, sử dụng KeyBERT kết hợp Jaccard similarity để lọc các vector ít liên quan trong top_k. Việc truy xuất tài liệu tập trung vào các chunk liên quan đến nội dung câu hỏi.
- Đơn giản hóa và refactor QA interface, cải thiện flow CLI để thuận tiện cho việc chạy và kiểm thử.
- Tách các chức năng chính (vectorization, QA, keyword extraction, chunking, logging, config) thành các module riêng biệt. Việc này giúp tăng khả năng mở rộng, bảo trì và kiểm thử từng phần.
- Chuẩn hóa logging cho toàn bộ pipeline (prompt, embedding, chunk processing, QA), hỗ trợ theo dõi trạng thái và phát hiện lỗi.
- Cập nhật .gitignore để loại trừ các file nhạy cảm và file sinh ra trong quá trình vận hành.

---

## 3. Điểm cải tiến so với tuần 1
- QA interface được làm gọn, nhiều function được tách/đơn giản hóa, tăng khả năng bảo trì.
- Bổ sung keyword extraction giúp tăng tỉ lệ tìm đúng chunk liên quan so với chỉ truy vấn bằng câu hỏi.
- Logging mở rộng giúp theo dõi pipeline chi tiết hơn khi kiểm thử.
- Đưa API key và các tham số về config/env để quản lý môi trường tốt hơn.

---

## 4. Hạn chế
- Chưa tích hợp conversation memory, chưa có cơ chế lưu lịch sử hội thoại. Model trả lời dựa trên câu hỏi hiện tại, chưa kết hợp ngữ cảnh các câu hỏi trước.
- Retrieval hiện tại chỉ thực hiện một lượt truy vấn, chưa hỗ trợ multi-hop reasoning hoặc tổng hợp thông tin từ nhiều nguồn.

---

## 5. Hướng nghiên cứu và kế hoạch cho tuần 3
- Nghiên cứu về Agentic RAG để xây dựng pipeline có khả năng tự tổng hợp thông tin từ nhiều nguồn, giúp mô hình suy luận tốt hơn.
- Nghiên cứu tích hợp ngữ cảnh hội thoại (conversation memory) để mô hình trả lời thông minh hơn, có khả năng xử lý các đoạn chat dài và đa lượt.

---

## 6. Tóm tắt tuần 2 (20/10/2025 - 27/10/2025)
- Đã hoàn thiện và ổn định phần vectorization (embedding + FAISS).
- Đã refactor QA interface, bổ sung keyword extraction, logging và tài liệu hóa.
- Còn 2 điểm cần khắc phục: tích hợp conversation memory (multi-turn) và xây pipeline multi-step retrieval/Agentic RAG.
- Kế hoạch tuần này tập trung vào: lưu lịch sử chat vào model, tách module src, thu thập tài liệu LLMOps/Agentic RAG và đóng gói Docker phục vụ nghiên cứu.
