# BÁO CÁO KẾT QUẢ TUẦN 3

**Tên đề tài:** Xây dựng hệ thống hỏi đáp tự động ứng dụng kỹ thuật LLM Ops và RAG  
**Giảng viên hướng dẫn:** ThS. Nguyễn Văn Chiến  
**Sinh viên thực hiện:**

- Nguyễn Ngọc Tâm - 2151040051
- Phạm Hoài Kiệt - 2251150058

**Thời gian thực hiện:** 28/10/2025 - 03/11/2025

---

## 1. Mục tiêu

Báo cáo tóm tắt kết quả tuần 3 đạt được, các điểm cải tiến so với tuần 2, hạn chế còn tồn tại và kế hoạch tuần 4.

---

## 2. Kết quả đạt được

- Chuẩn hóa prompting bằng template: Bổ sung config/prompt_templates.py và render_prompt(...); LLM giờ nhận prompt_template rõ ràng (planning/qa/acting/observing), thuận tiện A/B và tái sử dụng.
- Tăng độ chính xác truy hồi bằng pre-filter: Thêm bước lọc metadata trước khi search (header_path_filter, match linh hoạt: list→membership, str→substring, kiểu khác→exact), sau đó build FAISS tạm thời trên tập con ➜ giảm nhiễu và tập trung vào tài liệu phù hợp.Bổ sung chức năng trích xuất từ khóa trong câu hỏi, sử dụng KeyBERT kết hợp Jaccard similarity để lọc các vector ít liên quan trong top_k. Việc truy xuất tài liệu tập trung vào các chunk liên quan đến nội dung câu hỏi.
- Giảm độ trễ ở bước tổng hợp ngữ cảnh: Điều chỉnh top_k mặc định từ 100 → 10 trong answer generation, cắt chi phí hợp nhất ngữ cảnh khi tập sau lọc đã đủ hẹp.
- Quan sát/giám sát retrieval tốt hơn: Bổ sung logger chi tiết (số lượng vector sau lọc, đường đi dữ liệu, bước build index…), giúp debug sai lệch tìm kiếm nhanh hơn.
- Refactor luồng gọi LLM: GeminiGenerator.generate_answer(...) nhận template, thống nhất cách dựng prompt và tham số, giảm ràng buộc cứng trong mã.
### Sơ đồ xử lý: pre-filter ➜ sub-index ➜ top_k

```mermaid
flowchart LR
  A[User question]
  B[Keyword extractor - KeyBERT]
  C[Header / metadata filter]
  D[(Vector store)]
  E[Build sub-index - FAISS temp]
  F[ANN search - top_k = 10]
  G[Context builder]
  H[LLM - prompt templates]
  I[Answer]

  A --> B
  A --> C
  C --> D
  D --> E
  E --> F
  F --> G
  G --> H
  H --> I
```
- Thu hẹp không gian tìm kiếm trước bằng metadata filter.
- Sau đó lập chỉ mục con và query top_k trên tập nhỏ ⇒ precision tăng & latency giảm.
- Prompt templates + logging giúp ổn định đầu ra và dễ debug.
  
```mermaid
flowchart LR
%% ========= OFFLINE PREP =========
subgraph A ["Offline prep (không đổi)"]
    A1["Ingest tài liệu"] --> A2["Chunking"]
    A2 --> A3["Embedding"]
    A3 --> A4["Vector store + metadata (header_path, ...)"]
end

%% ========= ONLINE QUERY =========
subgraph B ["Online retrieval & generation (release-3-11)"]
    Q1["User question"] --> Q2["Keyword extractor (KeyBERT)"]
    Q1 --> Q3["Query embedding"]
    Q1 --> Q4["Metadata pre-filter (header_path_filter)"]

    Q4 --> Q5["Filtered IDs từ Vector store"]
    Q5 --> Q6["Build sub-index (FAISS tạm) ↳ theo Filtered IDs"]

    Q2 -- "query expansion / rerank" --> Q7
    Q3 --> Q7["ANN search trên sub-index (adaptive top_k: 8–30)"]

    Q7 --> Q8["Context builder"]
    Q8 --> Q9["LLM với Prompt templates (planning / qa / ...)"]
    Q9 --> Q10["Final answer"]
end

%% ========= OBSERVABILITY =========
subgraph C ["Observability (tuần 3)"]
    L1["Logger chi tiết: filtered size, build cost, search latency, top_k"]
end

Q4 -. "log" .-> L1
Q6 -. "log" .-> L1
Q7 -. "log" .-> L1
Q9 -. "log" .-> L1
```
- Pre-filter trước khi search: lọc theo header_path_filter ➜ chỉ build sub-index tạm trên tập con liên quan ⇒ giảm nhiễu.
- Adaptive top_k ở tầng ANN sau khi đã thu hẹp không gian tìm kiếm ⇒ độ trễ giảm, vẫn giữ độ liên quan.
- KeyBERT: dùng cho query expansion (đẩy tín hiệu vào ANN) hoặc rerank nhẹ sau search.
- Prompt templates: planning/qa/... giúp ổn định hành vi LLM và dễ A/B.
- Logger chi tiết: theo dõi filtered size, thời gian build sub-index, latency, token… ⇒ debug nhanh & đo lường rõ.
---

## 3. Điểm cải tiến so với tuần 2

- Từ QA interface gọn hơn → “prompting có cấu trúc”: Tuần 2 dừng ở refactor interface; tuần 3 thêm bước chuẩn hóa template để kiểm soát hành vi mô hình theo từng pha.
- Từ “keyword extraction” → “pre-filter + sub-index”: Tuần 2 dùng KeyBERT + Jaccard để lọc top_k; tuần 3 đưa lọc lên trước khi search và lập chỉ mục con
  ➜ bớt nhiễu, tăng precision khi kho dữ liệu lớn.
- Logging rộng: Tuần 2 chuẩn hóa logging toàn pipeline; tuần 3 đặt log sâu ở retrieval (lọc/index/search) giúp rà lỗi thực chiến nhanh hơn.
- Tối ưu hiệu năng hướng mục tiêu: Giảm top_k mặc định giúp rút ngắn thời gian trả lời mà vẫn giữ liên quan.

---

## 4. Hạn chế

- Chưa tích hợp conversation memory, chưa có cơ chế lưu lịch sử hội thoại. Model trả lời dựa trên câu hỏi hiện tại, chưa kết hợp ngữ cảnh các câu hỏi trước.
- Retrieval hiện tại chỉ thực hiện một lượt truy vấn, chưa hỗ trợ multi-hop reasoning hoặc tổng hợp thông tin từ nhiều nguồn.
- Giảm top_k có rủi ro giảm recall: Với domain rộng/đề bài dài, top_k=10 đôi khi chưa đủ; cần cơ chế tự điều chỉnh theo truy vấn.

---

## 5. Hướng nghiên cứu và kế hoạch cho tuần 4

- Nghiên cứu về Agentic RAG để xây dựng pipeline có khả năng tự tổng hợp thông tin từ nhiều nguồn, giúp mô hình suy luận tốt hơn.
- Nghiên cứu tích hợp ngữ cảnh hội thoại (conversation memory) để mô hình trả lời thông minh hơn, có khả năng xử lý các đoạn chat dài và đa lượt.
- Tối ưu adaptive retrieval & caching (điều chỉnh top_k, cache sub-index) để giảm độ trễ mà vẫn giữ độ chính xác.

---

## 6. Tóm tắt tuần 3 (28/10/2025 - 03/11/2025)

- Precision tăng, Latency giảm nhờ pre-filter metadata → sub-index FAISS → ANN (adaptive top_k).
- Chuẩn hóa prompting với template (planning/qa/observing/acting); refactor luồng gọi LLM.
- Logging retrieval chi tiết (lọc/index/search) → dễ debug và giám sát.
- Còn 3 điểm cần khắc phục: tích hợp conversation memory (multi-turn), xây pipeline multi-step retrieval/Agentic RAG, top_k=10 có rủi ro giảm recall ở domain rộng.
- Kế hoạch tuần này tập trung vào: tiêp tục triển khai kế hoạch lưu lịch sử chat vào model, thu thập tài liệu LLMOps/Agentic RAG và triển khai Agentic/Multi-hop RAG và tối ưu adaptive retrieval & caching (auto-tune top_k, cache sub-index).
