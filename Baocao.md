# HỆ THỐNG HỎI ĐÁP SỬ DỤNG AGENTIC RAG CHO TÀI LIỆU GIÁO DỤC TIẾNG VIỆT

---

## PHẦN MỞ ĐẦU (FORMALIA)

*(Không đánh số trang)*

- **Bìa chính, Bìa phụ**
- **Lời cam đoan**
- **Lời cảm ơn**
- **Tóm tắt luận văn (Tiếng Việt và Tiếng Anh)**
- **Mục lục**
- **Danh mục các bảng biểu**
- **Danh mục các hình vẽ, sơ đồ**
- **Danh mục các từ viết tắt**

---

## MỞ ĐẦU

*(Dự kiến: 3-5 trang)*

### 1. Đặt vấn đề (Bối cảnh và Vấn đề thực tiễn) *(~1.5 trang)*

- **Xu hướng chung:** Trí tuệ Nhân tạo (AI), đặc biệt là các Mô hình Ngôn ngữ Lớn (LLM), đang tạo ra một làn sóng chuyển đổi mạnh mẽ trong hầu hết các lĩnh vực kinh tế - xã hội.
- **Ứng dụng trong Giáo dục:** Lĩnh vực Giáo dục không nằm ngoài xu hướng này, với nhiều tiềm năng ứng dụng AI để cá nhân hóa lộ trình học tập, tự động hóa các quy trình quản lý và nâng cao trải nghiệm, hiệu quả học tập của người học.
- **Vấn đề tra cứu thông tin:** Một trong những thách thức thực tế mà sinh viên, giảng viên, và cán bộ quản lý thường xuyên gặp phải là nhu cầu tra cứu nhanh chóng, chính xác các thông tin từ kho tài liệu khổng lồ của nhà trường (chương trình khung, chương trình đào tạo, các quy chế, và văn bản học vụ).
- **Vấn đề tự động hóa:** Các bộ phận hỗ trợ (như phòng đào tạo, phòng công tác sinh viên) phải liên tục xử lý và trả lời các câu hỏi có nội dung lặp lại, gây lãng phí nguồn lực. Điều này tạo ra nhu cầu cấp thiết về một hệ thống có khả năng tự động hóa việc hỏi đáp các câu hỏi thường gặp này.
- **Hạn chế của tài liệu số hóa:** Mặc dù nhiều tổ chức giáo dục đã số hóa các tài liệu này (thường dưới dạng PDF), việc tra cứu thủ công vẫn tốn thời gian, dễ gây nhầm lẫn và có nguy cơ bỏ sót chi tiết.
- **Hạn chế của công cụ truyền thống:** Các công cụ tìm kiếm dựa trên từ khóa truyền thống không đáp ứng tốt cho các câu hỏi phức tạp (ví dụ: "So sánh điều kiện tốt nghiệp của hai chuyên ngành?", "Tổng hợp các môn học tiên quyết của ngành X?"). Các công cụ này gặp khó khăn do cấu trúc tài liệu phức tạp (phân cấp, bảng biểu) và đặc thù của ngôn ngữ tiếng Việt.

### 2. Động lực và Giải pháp đề xuất *(~1 trang)*

**Động lực:**
- Cần một hệ thống hỏi đáp chuyên biệt cho tài liệu giáo dục tiếng Việt, có khả năng kết hợp truy vấn ngữ nghĩa với sinh ngôn ngữ tự nhiên để trả lời chính xác và có dẫn nguồn (citations).
- Hệ thống RAG cơ bản (Baseline) tuy giải quyết được các câu hỏi tra cứu đơn giản, nhưng vẫn gặp thất bại (failure cases) khi xử lý các câu hỏi phức tạp (so sánh, tổng hợp) đòi hỏi suy luận nhiều bước.
- Do đó, động lực chính của nghiên cứu là đề xuất một kiến trúc nâng cao – Agentic RAG – để khắc phục những hạn chế này. Kiến trúc này cho phép hệ thống tự lập kế hoạch (planning), thực hiện truy vấn lặp (iterative querying), và tự đánh giá thông tin (self-correction) để giải quyết các tác vụ phức tạp.

**Giải pháp đề xuất:**
- Xây dựng một pipeline hoàn chỉnh bao gồm:
    1. Xây dựng hệ thống RAG cơ bản làm nền tảng (baseline).
    2. Thiết kế và hiện thực hóa kiến trúc Agentic RAG (kiến trúc đề xuất) có khả năng phân rã câu hỏi, lập kế hoạch suy luận, và ghi lại dấu vết (reasoning_trace).
    3. Toàn bộ pipeline xử lý dữ liệu (Extraction, Chunking, Vectorization) được tối ưu cho tài liệu có cấu trúc phân cấp.

### 3. Mục tiêu nghiên cứu *(~0.5 trang)*

#### 3.1. Mục tiêu tổng quát *(~0.2 trang)*
- Xây dựng hệ thống hỏi đáp tự động dựa trên Agentic RAG cho tài liệu giáo dục tiếng Việt.

#### 3.2. Mục tiêu cụ thể *(~0.3 trang)*
- Thiết kế pipeline xử lý dữ liệu từ PDF đến vector hóa, tối ưu cho tài liệu có cấu trúc phân cấp.
- Phát triển module reasoning lặp (agentic) với trace rõ ràng.
- Tối ưu hóa cho tiếng Việt: tiền xử lý, embedding, và chiến lược prompt.
- Đánh giá hiệu quả hệ thống trên tập dữ liệu thực tế.

### 4. Đối tượng và Phạm vi nghiên cứu *(~0.5 trang)*

#### 4.1. Đối tượng nghiên cứu *(~0.2 trang)*
- Hệ thống hỏi đáp và kiến trúc Agentic RAG.
- Các kỹ thuật xử lý ngôn ngữ tự nhiên cho tiếng Việt trong miền giáo dục.
- Hiệu quả của phương pháp truy xuất và sinh câu trả lời.

#### 4.2. Phạm vi nghiên cứu *(~0.3 trang)*
- **Về nội dung:** Tài liệu chương trình đào tạo, quy chế, phụ lục, quy định học vụ.
- **Về không gian:** Dữ liệu được lấy từ chương trình đào tạo của Trường Đại học Giao thông Vận tải TP. Hồ Chí Minh.
- **Về thời gian:** Dữ liệu được thu thập và thử nghiệm trong một khung thời gian xác định.

### 5. Phương pháp nghiên cứu *(~0.5 trang)*

- **Phương pháp nghiên cứu lý thuyết:** Tổng quan, phân tích các công trình, bài báo khoa học về RAG, Agentic RAG, LLMs, và các kỹ thuật liên quan.
- **Phương pháp thực nghiệm:** Thiết kế, xây dựng (hiện thực hóa) hệ thống, và chạy các thí nghiệm để kiểm thử các module (extraction, chunking, retrieval, generation).
- **Phương pháp so sánh, đánh giá:** Xây dựng bộ dữ liệu benchmark, thiết lập các chỉ số (metrics) và so sánh hiệu quả của mô hình đề xuất (Agentic RAG) với các mô hình cơ sở (baseline, ví dụ RAG truyền thống).

### 6. Đóng góp của luận văn *(~0.5 trang)*

#### 6.1. Đóng góp về mặt học thuật *(~0.2 trang)*
- Đề xuất kiến trúc Agentic RAG phù hợp cho các câu hỏi phức tạp bằng tiếng Việt.
- Xây dựng quy trình reasoning trace cho hệ thống Q&A trong lĩnh vực giáo dục.

#### 6.2. Đóng góp về mặt kỹ thuật *(~0.2 trang)*
- Phát triển các module xử lý dữ liệu, vector hóa, truy xuất ngữ nghĩa tối ưu cho tài liệu dài, nhiều cấp phân cấp.
- Đề xuất chiến lược prompt và đánh giá độ đầy đủ của quá trình suy luận.

#### 6.3. Đóng góp thực tiễn *(~0.1 trang)*
- Tạo nền tảng hỏi đáp tự động có thể ứng dụng cho các cơ sở giáo dục tại Việt Nam, nâng cao hiệu quả tra cứu và quản lý đào tạo.

### 7. Kết cấu của Luận văn *(~0.3 trang)*
- Ngoài các phần Mở đầu, Kết luận, Tài liệu tham khảo và Phụ lục, nội dung chính của luận văn được tổ chức thành 4 chương:
    - **Chương 1. Cơ sở lý thuyết về Hệ thống Hỏi đáp và RAG.**
    - **Chương 2. Thiết kế và hiện thực hóa hệ thống RAG truyền thống (Baseline).**
    - **Chương 3. Phát triển kiến trúc Agentic RAG (Kiến trúc đề xuất).**
    - **Chương 4. Thí nghiệm và đánh giá hiệu năng hệ thống.**

---


## CHƯƠNG 1. TỔNG QUAN LÝ THUYẾT VÀ CÔNG NGHỆ SỬ DỤNG

*(Dự kiến: 15-20 trang)*

### 1.1. Tổng quan về hệ thống hỏi đáp tự động *(~2 trang)*
- Phân loại hệ thống hỏi đáp: Extractive QA, Abstractive QA, Open-domain QA, Closed-domain QA.
- Thách thức của hệ thống hỏi đáp cho tài liệu chuyên ngành, đặc biệt là tiếng Việt.
- Vai trò của LLM trong việc nâng cao hiệu quả hệ thống hỏi đáp.

### 1.2. Mô hình Ngôn ngữ Lớn (LLM) *(~2 trang)*
- Khái niệm, lịch sử phát triển, kiến trúc Transformer.
- Ưu nhược điểm của LLM trong ứng dụng hỏi đáp.
- Một số LLM tiêu biểu: GPT, Gemini, Llama, v.v.
### 1.3. Kỹ thuật Retrieval-Augmented Generation (RAG) *(~2 trang)*
- Định nghĩa, nguyên lý hoạt động, các thành phần chính: Retriever, Generator.
- Ưu nhược điểm của RAG truyền thống.
- Ứng dụng thực tiễn của RAG.
### 1.4. Tại sao LLM cần kết hợp với RAG? *(~1 trang)*
- Hạn chế của LLM: hiện tượng "ảo giác" (hallucination), thiếu cập nhật dữ liệu mới, không thể truy xuất nguồn gốc thông tin.
- Kiến thức lỗi thời
- Nhu cầu tăng độ chính xác, minh bạch, khả năng kiểm chứng và cập nhật tri thức thực tế cho hệ thống hỏi đáp.
- Vai trò của RAG: cung cấp ngữ cảnh thực tế, bổ sung dữ liệu ngoài, giúp LLM trả lời sát thực tế và có dẫn nguồn.
- Động lực kết hợp: Tối ưu hóa hiệu quả ứng dụng LLM trong các bài toán thực tiễn, đặc biệt với dữ liệu chuyên ngành hoặc yêu cầu kiểm chứng nguồn thông tin.
### 1.5. Kỹ thuật Agentic RAG *(~2 trang)*
- Định nghĩa Agentic RAG: Từ RAG thụ động đến Agent chủ động.
- So sánh với RAG truyền thống.
- Các chiến lược agent: Planning (Lập kế hoạch), Reflection (Tự phản tư), Self-correction (Tự sửa lỗi).
- Reasoning trace (Dấu vết suy luận) và Iterative querying (Truy vấn lặp).

### 1.6. Embedding, Vector Search và FAISS *(~2 trang)*
- Biểu diễn dữ liệu dưới dạng vector: Dữ liệu (văn bản, hình ảnh, âm thanh) được ánh xạ thành các vector số thực nhiều chiều, mỗi chiều thể hiện một đặc trưng ngữ nghĩa hoặc hình thái học. Việc biểu diễn này giúp máy tính có thể đo lường mức độ tương đồng giữa các đối tượng dựa trên khoảng cách hoặc góc giữa các vector, thay vì chỉ so sánh ký tự hay từ khóa đơn thuần.
- So sánh truy vấn trong Vector Database và Relational Database:
    - Vector Database (như FAISS, Milvus): Truy vấn dựa trên phép đo khoảng cách (cosine, Euclidean, dot-product) giữa vector truy vấn và các vector lưu trữ, trả về các đối tượng gần nhất về mặt ngữ nghĩa (semantic similarity). Phù hợp cho các bài toán tìm kiếm ngữ nghĩa, truy xuất thông tin không cấu trúc, hình ảnh, âm thanh.
    - Relational Database (CSDL quan hệ truyền thống): Truy vấn dựa trên các phép so sánh giá trị thuộc tính (bằng, lớn hơn, nhỏ hơn, LIKE, v.v.) và các phép nối bảng (JOIN), phù hợp cho dữ liệu có cấu trúc rõ ràng (bảng, trường, khóa chính/phụ).
    - Khác biệt chính: Vector DB tối ưu cho tìm kiếm tương đồng ngữ nghĩa, còn RDBMS tối ưu cho truy vấn logic, lọc, tổng hợp dữ liệu có cấu trúc. Vector DB thường không hỗ trợ JOIN phức tạp, nhưng có thể tích hợp metadata để lọc kết quả.
    - Ứng dụng: Vector DB là nền tảng cho các hệ thống tìm kiếm ngữ nghĩa, RAG, recommendation, trong khi RDBMS vẫn là xương sống cho các hệ thống quản trị dữ liệu truyền thống.
- Khái niệm Embedding: Biểu diễn văn bản, câu, đoạn hoặc từ dưới dạng vector số thực nhiều chiều, giúp máy tính hiểu và xử lý ngữ nghĩa tự nhiên. Trình bày các phương pháp embedding truyền thống (Bag-of-Words, TF-IDF, Word2Vec, GloVe) và sự phát triển lên Sentence Embedding.
- Sentence Transformers: Giới thiệu kiến trúc, ưu điểm của các mô hình như all-MiniLM-L6-v2, multilingual, khả năng embedding cho tiếng Việt, hiệu quả so với các phương pháp cũ.
- Vector Search: Định nghĩa bài toán tìm kiếm gần đúng (Approximate Nearest Neighbor - ANN), vai trò trong hệ thống hỏi đáp (retrieval), so sánh với search truyền thống dựa trên từ khóa.
- Ứng dụng Vector Search trong RAG: Cho phép truy xuất các đoạn văn bản liên quan về mặt ngữ nghĩa, tăng độ chính xác khi xây dựng ngữ cảnh cho LLM.
- FAISS: Giới thiệu thư viện FAISS của Facebook AI, các loại index (Flat, IVF, HNSW), ưu điểm về tốc độ, khả năng mở rộng, hỗ trợ GPU, lý do lựa chọn FAISS cho hệ thống lớn, so sánh với các giải pháp khác (Annoy, ScaNN, Milvus).

### 1.7. Prompt Engineering *(~1-1.5 trang)*
- Khái niệm Prompt: Đoạn văn bản đầu vào hướng dẫn LLM thực hiện nhiệm vụ cụ thể (ví dụ: trả lời, tóm tắt, phân loại).
- Vai trò của Prompt Engineering: Ảnh hưởng trực tiếp đến chất lượng, độ chính xác và khả năng kiểm soát output của LLM; đặc biệt quan trọng trong các hệ thống RAG và Agentic RAG.
- Các loại prompt: Zero-shot, Few-shot, Chain-of-Thought, Instruction-based, Structured prompt (dùng tag, JSON, bảng).
- Chiến lược thiết kế prompt hiệu quả: Đưa ra ví dụ minh họa, hướng dẫn rõ ràng, kiểm soát ngôn ngữ đầu ra, tối ưu cho tiếng Việt (xử lý đặc thù ngôn ngữ, từ viết tắt, bảng biểu).
- Kỹ thuật nâng cao: Prompt chaining, dynamic prompt, sử dụng template và biến động nội dung theo ngữ cảnh truy vấn.
- Đánh giá hiệu quả prompt: Thử nghiệm A/B, đo lường các chỉ số (accuracy, relevance, completeness), phân tích lỗi output.
- Quy trình xây dựng và kiểm thử prompt: Lặp lại các bước thiết kế, kiểm thử, phân tích lỗi và tối ưu hóa prompt dựa trên phản hồi thực tế.
- Một prompt template chuẩn thường bao gồm các thành phần sau:
    - **Vai trò (Role):** Xác định vai trò mà LLM cần đóng (ví dụ: chuyên gia giáo dục, trợ lý học thuật...).
    - **Nhiệm vụ (Task):** Mô tả rõ ràng nhiệm vụ cần thực hiện (trả lời, phân loại, tóm tắt...).
    - **Yêu cầu đầu ra (Output Requirements):** Định dạng, cấu trúc, ngôn ngữ, độ chi tiết mong muốn của kết quả.
    - **Ngữ cảnh (Context):** Cung cấp thông tin nền, dữ liệu hoặc ví dụ minh họa nếu cần.
    - **Ràng buộc và lưu ý (Constraints/Notes):** Các quy tắc, giới hạn, chú ý đặc biệt (ví dụ: trả lời bằng tiếng Việt, trích dẫn nguồn...).
- Ví dụ minh họa prompt thực tế: Đưa ra một số ví dụ prompt tiếng Việt dùng trong hệ thống RAG/Agentic RAG (phân loại câu hỏi, sinh reasoning trace, tổng hợp câu trả lời).

### 1.8. Tổng quan các công trình liên quan *(~1-1.5 trang)*
- Tổng quan các nghiên cứu về RAG: Trình bày các công trình tiêu biểu về RAG (Lewis et al., 2020; các ứng dụng RAG trong QA, search, chatbot), các hướng tối ưu hóa retriever, generator, và tích hợp knowledge base.
- Agentic RAG: Tổng hợp các nghiên cứu mới về Agentic RAG (OPEN-RAG, Self-RAG, Corrective RAG, Chain-of-Thought RAG), các chiến lược agent (planning, reflection, self-correction), các benchmark và kết quả thực nghiệm.
- Ứng dụng RAG và Agentic RAG cho tiếng Việt: Đánh giá các nghiên cứu hiện có, chỉ ra hạn chế về tài nguyên, mô hình embedding, và dữ liệu tiếng Việt.
- Khoảng trống nghiên cứu: Thiếu hệ thống RAG/Agentic RAG tối ưu cho tài liệu giáo dục tiếng Việt, thiếu pipeline xử lý phân cấp, thiếu đánh giá thực nghiệm trên dữ liệu thực tế tại Việt Nam.
- Động lực thực hiện đề tài: Đáp ứng nhu cầu thực tiễn, đóng góp giải pháp kỹ thuật và học thuật cho cộng đồng nghiên cứu và ứng dụng AI trong giáo dục Việt Nam.


## CHƯƠNG 2. THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG RAG TRUYỀN THỐNG (BASELINE)

*(Dự kiến: 15 trang)*

### 2.1. Kiến trúc tổng thể và Lựa chọn công nghệ *(~2 trang)*

#### 2.1.1. Sơ đồ tổng thể hệ thống *(~0.5 trang)*
- Minh họa các thành phần chính và luồng dữ liệu (extraction → chunking → vectorization → retrieval → generation).

#### 2.1.2. Các module chính của hệ thống *(~0.5 trang)*
- Extraction, Chunking, Vectorization, Retrieval, Generation, Config, Utils.

#### 2.1.3. Lựa chọn công nghệ chung *(~1 trang)*
- Backend: Python 3.8+
- LLM: Google Gemini API
- Embedding: Sentence Transformers (ví dụ all-MiniLM-L6-v2)
- Vector DB: FAISS
- PDF Processing: pymupdf4llm
- Interface: Streamlit

### 2.2. Pipeline xử lý và vector hóa tài liệu giáo dục *(~2-2.5 trang)*

#### 2.2.1. Extraction Module (Trích xuất PDF sang Markdown) *(~0.7 trang)*
- Sử dụng thư viện `pymupdf4llm` để chuyển đổi PDF sang Markdown, bảo toàn cấu trúc chương/mục, bảng biểu.
- Hỗ trợ trích xuất toàn bộ tài liệu hoặc chia nhỏ theo trang (page_chunks).
- Lưu kết quả trích xuất ra file Markdown, hỗ trợ tách các phần/chunk bằng separator.
- Xử lý ngoại lệ và thông báo lỗi rõ ràng, đảm bảo pipeline không bị dừng đột ngột khi gặp file lỗi.

#### 2.2.2. Chunking Module (Phân đoạn phân cấp) *(~0.8 trang)*
- Đọc nội dung markdown từ file, kiểm tra lỗi và log chi tiết.
- Phân tích cấu trúc phân cấp tài liệu bằng hàm `parse_markdown_hierarchy`, xây dựng cây header đa cấp (chapter, section, subsection, ...).
- Duyệt cây header để tạo các chunk văn bản, mỗi chunk gắn metadata: tiêu đề chương, mục, đường dẫn header (`header_path`), nguồn gốc tài liệu.
- Hỗ trợ flatten cây phân cấp thành danh sách chunk phục vụ vector hóa.
- Lưu danh sách chunk ra file JSON, đảm bảo chuẩn hóa dữ liệu cho các bước tiếp theo.
- Cung cấp hàm phân tích thống kê chunk: số lượng chunk, độ dài trung bình, phân phối theo chương/mục, hỗ trợ kiểm soát chất lượng dữ liệu.

#### 2.2.3. Vectorization Module (Vector hóa) *(~1 trang)*
- Tiền xử lý nội dung chunk: làm sạch, chuẩn hóa, đặc biệt xử lý bảng Markdown thành text có cấu trúc.
- Load embedding model từ thư viện `sentence-transformers` (hỗ trợ nhiều model, đa ngôn ngữ, tối ưu cho tiếng Việt).
- Vector hóa các chunk theo batch để tối ưu hiệu suất, hỗ trợ xử lý dữ liệu lớn.
- Gắn embedding vào từng chunk, bổ sung metadata về model, chiều vector, chỉ số chunk.
- Lưu dữ liệu vector hóa ra file pickle (bao gồm embedding) và file JSON (metadata, không chứa embedding) để phục vụ các bước truy vấn và phân tích.
- Tính toán và log thống kê embedding: số lượng vector, chiều vector, norm trung bình, min/max, kiểm soát chất lượng vector hóa.
- Cung cấp pipeline tự động: từ load model, tiền xử lý, vector hóa, lưu file, đến hiển thị tổng kết quá trình.

### 2.3. Lớp lưu trữ (FAISS và Metadata) *(~1 trang)*

#### 2.3.1. Vector Store với FAISS Index *(~1 trang)*
- Sử dụng thư viện FAISS để xây dựng chỉ mục (index) cho các vector embedding.
- Lựa chọn loại index phù hợp (Flat, IVF, v.v.) tùy theo quy mô dữ liệu và yêu cầu truy vấn.
- Lưu trữ toàn bộ ma trận vector embedding trong FAISS index, hỗ trợ truy vấn similarity search hiệu quả (top-k nearest neighbors).
- Lưu metadata (thông tin chunk, header_path, nguồn gốc, v.v.) song song với FAISS index để ánh xạ kết quả truy vấn về thông tin gốc.
- Hỗ trợ lưu/đọc FAISS index và metadata ra file (pickle, JSON) để tái sử dụng, giảm thời gian khởi tạo.
- Cung cấp các thao tác chính: thêm vector mới, truy vấn top-k, cập nhật hoặc xóa vector, đồng bộ metadata.
- Đảm bảo tính toàn vẹn giữa FAISS index và metadata (kiểm tra số lượng, chỉ số mapping).
- Log thống kê: số lượng vector, loại index, thời gian truy vấn trung bình, hỗ trợ đánh giá hiệu năng lưu trữ và truy xuất.

### 2.4. Thiết kế luồng xử lý RAG truyền thống *(~1.5-2 trang)*

#### 2.4.1. Luồng xử lý (Single-shot RAG) *(~1 trang)*
- Người dùng nhập câu hỏi.
- Tối ưu truy vấn (Query Optimization): Phân tích câu hỏi để trích xuất metadata làm bộ lọc (filter).
- Truy xuất (Retrieval): Hệ thống thực hiện 1 lần truy xuất (Retrieve top-k chunks) bằng cách kết hợp similarity search và metadata filter.
- Xây dựng ngữ cảnh (Context Building): Xây dựng ngữ cảnh (context) từ các chunks đã truy xuất.
- Đưa câu hỏi, ngữ cảnh và prompt template vào LLM để sinh câu trả lời (Prompted Generation).
- Sinh câu trả lời (Generation): LLM sinh câu trả lời dựa trên ngữ cảnh và câu hỏi.

#### 2.4.2. Hạn chế của mô hình Baseline *(~0.5-1 trang)*
- Chỉ ra các vấn đề khi gặp câu hỏi phức tạp, so sánh, hoặc yêu cầu tổng hợp thông tin từ nhiều nguồn. Đây là cơ sở để nâng cấp lên Chương 3.
- Các hạn chế chính của mô hình RAG truyền thống:
    - **Thiếu khả năng suy luận nhiều bước:** RAG truyền thống chỉ thực hiện truy xuất và sinh câu trả lời trong một lượt, không hỗ trợ lập kế hoạch hoặc reasoning lặp, dẫn đến thất bại với các câu hỏi cần tổng hợp, so sánh hoặc phân tích sâu.
    - **Phụ thuộc mạnh vào truy xuất top-k:** Nếu thông tin quan trọng không nằm trong top-k chunk được truy xuất, LLM sẽ không thể trả lời đúng hoặc đầy đủ.
    - **Không tận dụng lịch sử hội thoại:** Không xử lý tốt các câu hỏi liên quan đến ngữ cảnh trước đó hoặc cần giải quyết đại từ, dẫn đến trả lời thiếu chính xác trong các phiên hỏi đáp liên tục.
    - **Dễ sinh ra thông tin ngoài phạm vi (hallucination):** Khi ngữ cảnh truy xuất không đủ, LLM có thể tự suy diễn hoặc sinh thông tin không có trong tài liệu gốc.
    - **Khó kiểm soát nguồn trích dẫn:** Việc gắn nguồn (citation) cho từng phần trả lời còn hạn chế, đặc biệt khi câu trả lời tổng hợp từ nhiều đoạn khác nhau.
    - **Không tự động đánh giá độ đầy đủ của thông tin:** Không có cơ chế phản hồi hoặc đề xuất truy vấn tiếp theo nếu thông tin chưa đủ.
    - **Chưa tối ưu cho tài liệu phân cấp, dài:** Việc chunking và truy xuất chưa tận dụng tốt cấu trúc phân cấp của tài liệu giáo dục, dễ bỏ sót thông tin quan trọng ở các cấp nhỏ.
- *Ghi chú: Tổng hợp thêm từ tài liệu tham khảo

---

## CHƯƠNG 3. PHÁT TRIỂN KIẾN TRÚC AGENTIC RAG (KIẾN TRÚC ĐỀ XUẤT)

*(Dự kiến: 15-20 trang)*

### 3.1. Động lực nâng cấp từ RAG truyền thống *(~1 trang)*
- Phân tích các trường hợp thất bại (failure cases) của hệ thống ở Chương 2.
- Giới thiệu kiến trúc Agentic RAG như một giải pháp để giải quyết các vấn đề suy luận phức tạp.
- Các ý bổ sung:
    - Nhấn mạnh nhu cầu thực tiễn về khả năng trả lời các câu hỏi phức tạp, đa bước, tổng hợp hoặc so sánh mà RAG truyền thống không đáp ứng được.
    - Phân tích các hạn chế về mặt trải nghiệm người dùng khi hệ thống chỉ trả lời được các câu hỏi đơn lẻ, thiếu khả năng tương tác nhiều lượt hoặc tự động đề xuất truy vấn tiếp theo.
    - Đề cập đến yêu cầu về tính minh bạch, khả năng kiểm chứng nguồn thông tin và truy vết quá trình suy luận (reasoning trace) trong các ứng dụng giáo dục.
    - Nêu bật vai trò của Agentic RAG trong việc tự động hóa các bước lập kế hoạch truy vấn, tự đánh giá độ đầy đủ thông tin, và tự sửa lỗi (self-correction) để nâng cao chất lượng trả lời.
    - Trình bày động lực từ các nghiên cứu mới (OPEN-RAG, Self-RAG, CoT-RAG...) cho thấy hiệu quả vượt trội của các kiến trúc agentic so với RAG truyền thống trong các benchmark thực tế.
    - Nhấn mạnh Agentic RAG là xu hướng phát triển tất yếu để xây dựng hệ thống hỏi đáp thông minh, thích ứng tốt với dữ liệu phân cấp, dài và ngôn ngữ tiếng Việt.
    - Đề xuất Agentic RAG như một bước tiến quan trọng để hướng tới các hệ thống hỏi đáp tự động có khả năng tương tác, thích nghi và hỗ trợ người dùng hiệu quả hơn trong lĩnh vực giáo dục.
### 3.2. Nâng cấp lên luồng xử lý Agentic RAG *(~2-2.5 trang)*

#### 3.2.1. Chuẩn hóa và Phân loại câu hỏi *(~0.5 trang)*
- Tích hợp chat history, giải quyết đại từ (Question Normalization).
- Phân loại: Simple Lookup, Comparative, Analytical (Question Classification).
- Bổ sung bước nhận diện ý định người dùng và tự động chuyển đổi câu hỏi sang dạng tối ưu cho truy xuất.
- Áp dụng các kỹ thuật phân tích ngữ nghĩa để xác định loại câu hỏi và lựa chọn chiến lược agent phù hợp.
- Hỗ trợ nhận diện các câu hỏi đa ý, câu hỏi lồng ghép hoặc yêu cầu tổng hợp thông tin từ nhiều nguồn.

#### 3.2.2. Vòng lặp suy luận (Iterative Reasoning Loop) *(~0.8 trang)*
- Lặp tối đa 3 lần: Query vector store → Retrieve top-k → Build context.
- Đánh giá độ đầy đủ (suggest_next_query).
- Quyết định stop hoặc tiếp tục với truy vấn mới.
- Ghi lại reasoning trace chi tiết cho từng vòng lặp, bao gồm cả truy vấn, kết quả truy xuất và quyết định của agent.
- Cho phép agent tự động điều chỉnh truy vấn dựa trên kết quả vòng trước (query refinement).
- Có thể tích hợp các tiêu chí dừng linh hoạt: dựa vào độ tự tin, độ phủ thông tin hoặc phản hồi người dùng.

#### 3.2.3. Đề xuất truy vấn con (Next Query Suggestion) *(~0.6 trang)*
- Phân tích reasoning trace, đánh giá completeness.
- Sinh truy vấn con tự động khi phát hiện thiếu thông tin hoặc cần làm rõ các khía cạnh cụ thể của câu hỏi.
- Hỗ trợ đề xuất nhiều truy vấn con song song cho các trường hợp cần tổng hợp hoặc so sánh đa chiều.
- Có thể tích hợp phản hồi người dùng để xác nhận hoặc điều chỉnh truy vấn tiếp theo.

#### 3.2.4. Sinh câu trả lời cuối cùng (Final Answer Generation) *(~0.6 trang)*
- Tổng hợp reasoning trace, sinh câu trả lời và trích xuất sources.
- Kết hợp thông tin từ nhiều vòng lặp và nhiều nguồn để tạo ra câu trả lời hoàn chỉnh, có dẫn nguồn rõ ràng.
- Đảm bảo giải thích được quá trình suy luận (explainability) và cung cấp reasoning trace cho người dùng kiểm chứng.
- Có thể sinh ra các cảnh báo hoặc chú thích nếu thông tin chưa đủ hoặc còn nghi vấn.

### 3.3. Thiết kế các module chức năng mở rộng *(~2 trang)*

#### 3.3.1. Retrieval Module (Cập nhật) *(~0.7 trang)*
- search_similar, filter_vectors_by_metadata.

#### 3.3.2. LLM Module (Mở rộng) *(~0.7 trang)*
- AgenticGeminiRAG và các methods (normalize_question, classify_question, suggest_next_query, agentic_pipeline...).

#### 3.3.3. Chat Context Manager *(~0.6 trang)*
- Quản lý lịch sử hội thoại (In-memory storage).

### 3.4. Thiết kế Prompt (Prompt Engineering) cho Agent *(~1-1.5 trang)*

#### 3.4.1. Các Prompt Templates chính *(~0.5 trang)*
- QUESTION_CLASSIFICATION_AND_AGENTIC_STRATEGY_PROMPT
- NEXT_QUERY_SUGGESTION_PROMPT
- FINAL_ANSWER_FROM_REASONING_TRACE_PROMPT

#### 3.4.2. Nguyên tắc thiết kế Prompt *(~0.5 trang)*
- Structured output (tags << >>), Explicit instructions, Vietnamese-specific considerations.

#### 3.4.3. Output Parsing *(~0.5 trang)*
- Regex-based extraction, JSON parsing.

### 3.5. Quản lý cấu hình hệ thống (Cập nhật) *(~1 trang)*
- Tách biệt tham số và mã nguồn (pipeline_config.py, models_config.py, llm_api_config.py, prompt_templates.py).
- Quản lý API key (GeminiApiKeyRotator).

### 3.6. Sơ đồ luồng xử lý chi tiết Agentic RAG *(~1.5 trang)*

#### 3.6.1. Flowchart tổng thể *(~0.5 trang)*
- Minh họa luồng xử lý từ input đến output.
- Các decision points trong vòng lặp reasoning.
- Điều kiện dừng và tiếp tục.

#### 3.6.2. State Diagram *(~0.5 trang)*
- Các trạng thái của agent: Normalizing, Classifying, Retrieving, Evaluating, Suggesting, Generating.
- Chuyển đổi giữa các trạng thái.
- Handling exceptions và fallback states.

#### 3.6.3. Sequence Diagram *(~0.5 trang)*
- Tương tác giữa các components trong iterative loop.
- Message passing và data flow.
- Timing và synchronization.

### 3.7. Xử lý các trường hợp đặc biệt *(~1 trang)*

#### 3.7.1. Handling Ambiguous Questions *(~0.3 trang)*
- Phát hiện và xử lý câu hỏi mơ hồ.
- Yêu cầu làm rõ từ người dùng.
- Fallback strategies.

#### 3.7.2. Handling Multi-turn Conversations *(~0.4 trang)*
- Quản lý context trong hội thoại nhiều lượt.
- Xử lý follow-up questions.
- Context window management.

#### 3.7.3. Handling Out-of-Scope Questions *(~0.3 trang)*
- Phát hiện câu hỏi ngoài phạm vi.
- Thông báo và gợi ý cho người dùng.
- Graceful degradation.

## CHƯƠNG 4. THÍ NGHIỆM VÀ ĐÁNH GIÁ HIỆU NĂNG HỆ THỐNG

*(Dự kiến: 10-15 trang)*

### 4.1. Thiết kế thí nghiệm *(~2 trang)*

#### 4.1.1. Bộ dữ liệu (Dataset) tài liệu giáo dục *(~0.7 trang)*
- Mô tả dataset (nguồn, số lượng, cấu trúc).
- Xây dựng bộ câu hỏi đánh giá (Benchmark Q&A).

#### 4.1.2. Các mô hình so sánh (Baselines) *(~0.7 trang)*
- Baseline: RAG truyền thống (single-shot) (Hiện thực hóa ở Chương 2).
- Mô hình đề xuất: Agentic RAG (Hiện thực hóa ở Chương 3).

#### 4.1.3. Các chỉ số đánh giá (Metrics) *(~0.6 trang)*
- Retrieval Metrics: Precision@K, Recall@K, MRR (Mean Reciprocal Rank), NDCG.
- Generation Metrics: BLEU, ROUGE, BERTScore, và Human evaluation (relevance, accuracy, completeness, faithfulness).
- Agentic Metrics: Số vòng lặp trung bình, Stop decision accuracy, Reasoning quality, Query refinement quality.
- End-to-end Metrics: Answer correctness, Citation accuracy, User satisfaction.

#### 4.1.4. Thiết lập thí nghiệm *(~0.4 trang)*
- Môi trường thử nghiệm: Hardware, Software requirements.
- Cấu hình tham số: K value, threshold, iteration limits.
- Reproducibility: Random seeds, versioning.
- Testing scenarios: Simple, Comparative, Analytical questions.

### 4.2. Kết quả thí nghiệm và Phân tích *(~3-4 trang)*

#### 4.2.1. Phân tích kết quả truy xuất (Retrieval Performance) *(~1 trang)*
- Trình bày kết quả (bảng, biểu đồ) so sánh các metrics truy xuất.

#### 4.2.2. Phân tích chất lượng sinh câu trả lời (Generation Quality) *(~1 trang)*
- So sánh điểm số BLEU, ROUGE và đánh giá thủ công.

#### 4.2.3. Phân tích hiệu quả của Agentic RAG (Case Studies) *(~1 trang)*
- Trình bày các ví dụ cụ thể (câu hỏi phức tạp, câu hỏi so sánh).
- Phân tích reasoning trace để so sánh output giữa hai hệ thống.

#### 4.2.4. Phân tích hiệu năng và chi phí (Efficiency Analysis) *(~1 trang)*
- Latency analysis (Độ trễ), Token consumption, API cost.

### 4.3. Thảo luận và Phân tích lỗi *(~1-1.5 trang)*

#### 4.3.1. Ablation Study (Nghiên cứu loại bỏ) *(~0.7 trang)*
- Ảnh hưởng của question normalization.
- Ảnh hưởng của classification.
- Ảnh hưởng của iterative reasoning.

#### 4.3.2. Phân tích các trường hợp thất bại (Error Analysis) *(~0.8 trang)*
- Phân tích các trường hợp Agent lập kế hoạch sai hoặc Tool trả về thông tin không chính xác.

---

## KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

*(Dự kiến: 2-3 trang)*

### 1. Tổng kết kết quả đạt được *(~1 trang)*
- Đánh giá các mục tiêu đã đạt được so với Mở đầu.
- Tóm tắt điểm mạnh của hệ thống và các đóng góp khoa học.

### 2. Hạn chế của luận văn *(~0.5 trang)*
- Phụ thuộc vào LLM API (chi phí, độ trễ).
- Hạn chế về bộ dữ liệu đánh giá.

### 3. Hướng phát triển trong tương lai *(~0.5-1 trang)*
- Fine-tune embedding model cho tiếng Việt.
- Caching và optimization.
- Multi-modal RAG (xử lý ảnh, bảng phức tạp).
- Khám phá Self-RAG và Corrective RAG.
- Tích hợp User feedback loop.

---

## TÀI LIỆU THAM KHẢO

*(Phần này không tính vào 60 trang nội dung chính)*

> **Lưu ý:** Trình bày theo chuẩn IEEE như Hướng dẫn đã quy định, ví dụ:  
[1] S. B. Islam, et al., "OPEN-RAG: Enhanced Retrieval-Augmented Reasoning with Open-Source Large Language Models," in Findings of the Association for Computational Linguistics: EMNLP 2024, pp. 14231-14244, Nov. 2024. 
[2] A. Singh, A. Ehtesham, S. Kumar, and T. T. Khoei, "AGENTIC RETRIEVAL-AUGMENTED GENERATION: A SURVEY ON AGENTIC RAG," arXiv:2501.09136v3 [cs.AI], Feb. 2025. [Online]. Available: https://arxiv.org/abs/2501.09136 
[3] A. Aryan, LLMOps: Managing Large Language Models in Production. O'Reilly Media, 2025. 
[4] P. Bhavsar, Mastering RAG: A comprehensive guide for building enterprise-grade RAG systems. Galileo, [n.d.]. 
[5] F. Li, et al., "CoT-RAG: Integrating Chain of Thought and Retrieval-Augmented Generation to Enhance Reasoning in Large Language Models," arXiv:2504.13534v3 [cs.CL], Sep. 2025. [Online]. Available: https://arxiv.org/abs/2504.13534
---

## PHỤ LỤC

*(Phần này không tính vào 60 trang nội dung chính)*

### A. Code Structure *(~0.5 trang)*
- Cấu trúc thư mục chi tiết
- Class diagrams, Sequence diagrams (nếu có)

### B. Configuration Examples *(~0.5 trang)*
- Liệt kê chi tiết các biến trong từng file cấu hình.
- Sample configs.

### C. API Documentation (nếu có) *(~0.5 trang)*
- Function signatures
- Parameters description

### D. Sample Outputs *(~0.5 trang)*
- Example questions và reasoning traces chi tiết.