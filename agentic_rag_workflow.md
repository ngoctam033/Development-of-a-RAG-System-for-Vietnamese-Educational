
# 🧠 Agentic RAG Workflow Instructions

## 🎯 Mục tiêu
Hệ thống Agentic RAG hỗ trợ người dùng truy xuất thông tin từ nhiều nguồn và trả lời thông minh thông qua mô hình ngôn ngữ.

## 📋 Các bước thực hiện

### Bước 1: Hiểu yêu cầu người dùng
- Phân tích câu hỏi đầu vào
- Xác định loại thông tin cần truy xuất

### Bước 2: Lập kế hoạch hành động
- Sử dụng Chain-of-Thought để suy luận các bước cần thiết
- Chọn công cụ phù hợp (retriever, API, calculator,...)

### Bước 3: Truy xuất thông tin
- Gọi retriever để lấy tài liệu liên quan
- Nếu cần, thực hiện multi-hop retrieval

### Bước 4: Tổng hợp và suy luận
- Đọc và phân tích nội dung tài liệu truy xuất
- Sử dụng reasoning để đưa ra câu trả lời phù hợp

### Bước 5: Phản hồi người dùng
- Trình bày câu trả lời rõ ràng, có dẫn chứng nếu cần
- Nếu chưa đủ thông tin, quay lại bước 2 để truy xuất thêm

## 🧪 Ví dụ
```markdown
User: "Khi nào bắt đầu đăng ký học phần?"

Agent:
1. Phân tích: Câu hỏi liên quan đến lịch đăng ký học phần
2. Truy xuất: Gọi API `get_registration_schedule()`
3. Tổng hợp: Trích xuất ngày bắt đầu từ dữ liệu
4. Phản hồi: "Đăng ký học phần bắt đầu từ ngày 5/11."
```

## ✅ Ghi chú cho mô hình
- Luôn thực hiện các bước theo thứ tự
- Nếu không đủ thông tin, hãy truy xuất thêm hoặc hỏi lại người dùng
- Có thể gọi công cụ nếu cần thiết
