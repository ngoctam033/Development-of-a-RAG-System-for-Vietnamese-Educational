# BÁO CÁO KẾT QUẢ TUẦN 2

**Tên đề tài:** XÂY DỰNG HỆ THỐNG HỎI ĐÁP TỰ ĐỘNG ỨNG DỤNG KỸ THUẬT LLM OPS VÀ RAG  
**Giảng viên hướng dẫn:** ThS. Nguyễn Văn Chiến  
**Sinh viên thực hiện:**

- Nguyễn Ngọc Tâm - 2151040051  
- Phạm Hoài Kiệt - 2251150058

**Thời gian thực hiện:** 20/10/2025 - 27/10/2025

---

## 1. Mục tiêu ngắn gọn
Mục tiêu báo cáo: Tóm tắt kết quả đạt được, nêu điểm cải tiến so với tuần 1, những hạn chế còn tồn tại và kế hoạch thực hiện cho tuần 3.

---

## 2. Kết quả chính đạt được
- **Vectorization pipeline:** Hoàn thiện tích hợp mô hình embedding và lưu trữ vector (FAISS). Vectorization hoạt động ổn định và có cấu hình động trong pipeline.  
- **QA pipeline:** Đã đơn giản hoá và refactor QA interface (loại bớt OOP phức tạp), cải thiện flow CLI để dễ chạy và debug.  
- **Trích xuất từ khóa:** Thêm module keyword extraction (KeyBERT và tiền xử lý) để cải thiện truy xuất tài liệu so với chỉ dùng câu hỏi thô.  
- **Xử lý tài liệu / chunking:** Cải thiện parsing markdown, hierachical parsing và tối ưu sinh chunk.  
- **Logging & cấu hình:** Thêm logging cho prompt/embedding/chunk processing; chuẩn hóa config (GEMINI_API_KEY từ env).   
- **Quản lý mã:** Cập nhật .gitignore (ẩn .env, vector store files, venv, logs) giúp repo sạch hơn.

---

## 3. Điểm cải tiến tuần này so với tuần 1
- **Refactor rõ rệt:** QA interface được làm gọn, dễ theo dõi; nhiều function được tách/đơn giản hoá → tăng maintainability.  
- **Retrieval cải thiện bước đầu:** Bổ sung keyword extraction giúp tăng tỉ lệ tìm đúng chunk liên quan so với chỉ query bằng câu hỏi đơn.  
- **Debug / monitoring tốt hơn:** Logging mở rộng giúp theo dõi pipeline chi tiết hơn khi test.    
- **Cấu hình môi trường chuyên nghiệp hơn:** API key và các tham số đưa về config/env.

---

## 4. Hạn chế còn tồn tại
- **Mô hình chưa có conversation memory:** Hiện chưa thấy cơ chế lưu lịch sử hội thoại. Do đó model trả lời chủ yếu dựa trên câu hỏi hiện tại, chưa kết hợp ngữ cảnh các câu hỏi trước.  
- **Truy xuất chỉ một lượt:** Retrieval hiện tại chủ yếu dựa vào một lần truy vấn (một lượt tìm các chunk liên quan). Với các câu hỏi đòi hỏi thu thập thông tin từ nhiều tài liệu, nhiều từ khóa hoặc multi-hop reasoning, pipeline chưa hỗ trợ retrieval lặp/agentic orchestration.   
- **Thiếu evaluation multi-turn / multi-doc:** Cần bộ test case để đánh giá nâng cao (multi-turn dialogues, multi-doc QA).

---

## 5. Hướng nghiên cứu và kế hoạch cho tuần 3
Nhóm dự định thực hiện trong tuần này:
- Lưu lại lịch sử chat và đưa vào model để hỗ trợ đoạn hội thoại dài.  
- Refactor code: chia nhỏ src thành nhiều module nhỏ hơn để dễ quản lý các step trong pipeline.  
- Tìm kiếm và thu thập tài liệu liên quan đến LLMOps và Agentic RAG.  
- Build các framework trong Docker để triển khai hệ thống LLMOps (containerize pipeline sau khi nghiên cứu).

---

## 6. Tóm tắt báo cáo tuần 2 (20/10/2025 - 27/10/2025)
- Đã hoàn thành và ổn định phần vectorization (embedding + FAISS).  
- Tuần này có tiến bộ rõ rệt: refactor QA interface, thêm keyword extraction, logging và tài liệu hóa.  
- Vẫn còn 2 điểm cần khắc phục: tích hợp conversation memory (multi-turn) và xây pipeline multi-step retrieval/Agentic RAG.  
- Kế hoạch tuần này tập trung vào: lưu lịch sử chat vào model, tách module src, thu thập tài liệu LLMOps/Agentic RAG và đóng gói Docker để sẵn sàng triển khai sau nghiên cứu.

```

