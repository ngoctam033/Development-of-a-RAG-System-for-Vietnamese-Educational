# Kiến trúc Pipeline Xử lý Dữ liệu (Chunking & Indexing)

Tài liệu này mô tả chi tiết luồng xử lý dữ liệu từ các file PDF thô cho đến khi được lưu trữ vào Vector Database để phục vụ hệ thống RAG.

## 1. Tổng quan Pipeline

Hệ thống sử dụng quy trình xử lý 3 giai đoạn chính, tập trung vào việc bảo toàn cấu trúc phân cấp của tài liệu (Hierarchical Structure) để tối ưu hóa quá trình truy vấn ngữ cảnh.

```mermaid
flowchart TD
    %% Nodes
    PDF(["📄 PDF Files (Raw Data)"])
    MD(["📝 Markdown (Intermediate)"])
    CHUNKS(["🧩 Chunks + Metadata (Structured Data)"])
    VEC(["🗄️ Vector Store (FAISS / Pickle)"])

    %% Main Flow
    PDF -->|"Extraction"| MD
    MD -->|"Semantic Chunking"| CHUNKS
    CHUNKS -->|"Embedding"| VEC

    %% Subgraphs
    subgraph S1 ["Giai đoạn 1: Trích xuất"]
        E1["Marker / Docling"]
        E2["Xử lý bảng biểu"]
        E3["Clean Text"]
    end

    subgraph S2 ["Giai đoạn 2: Phân đoạn"]
        C1["Parse Hierarchy"]
        C2["Header Path Tracking"]
        C3["Table Flattening"]
    end

    subgraph S3 ["Giai đoạn 3: Vector hóa"]
        I1["Sentence Transformer"]
        I2["Batch Encoding"]
        I3["Metadata Mapping"]
    end

    %% Internal Connections
    PDF -.-> E1
    E1 --> E2
    E2 --> E3
    E3 -.-> MD
    
    MD -.-> C1
    C1 --> C2
    C2 --> C3
    C3 -.-> CHUNKS
    
    CHUNKS -.-> I1
    I1 --> I2
    I2 --> I3
    I3 -.-> VEC

    %% Styling
    style PDF fill:#f9f,stroke:#333,stroke-width:2px
    style MD fill:#bbf,stroke:#333,stroke-width:2px
    style CHUNKS fill:#bfb,stroke:#333,stroke-width:2px
    style VEC fill:#fbb,stroke:#333,stroke-width:2px

    classDef steps fill:#fff,stroke:#333,stroke-dasharray: 5 5
    class E1,E2,E3,C1,C2,C3,I1,I2,I3 steps
```

## 2. Chi tiết các giai đoạn

### Giai đoạn 1: PDF to Markdown
*   **Công cụ**: Sử dụng **Marker** hoặc **Docling** để trích xuất nội dung từ PDF.
*   **Mục tiêu**: Chuyển đổi PDF sang Markdown để giữ lại các định dạng cấu trúc như Headers (#, ##, ###), bảng (Tables), và danh sách (Lists).
*   **Xử lý bảng**: Các bảng được nhận diện và chuyển đổi sang dạng text có cấu trúc để model embedding dễ hiểu hơn.

### Giai đoạn 2: Markdown to Chunks & Metadata
*   **Semantic Chunking**: Thay vì cắt theo độ dài cố định, hệ thống cắt dựa trên cấu trúc Header của Markdown.
*   **Header Path**: Mỗi chunk sẽ mang theo "đường dẫn" của nó (ví dụ: `Ngành CNTT > Chương trình chi tiết > Kiến thức cơ sở`).
*   **Metadata**: Lưu trữ thông tin về tiêu đề chương, mục, tên file nguồn để phục vụ việc hiển thị nguồn tham khảo sau này.

### Giai đoạn 3: Vector Store & Indexing
*   **Embedding Model**: Sử dụng mô hình `AITeamVN/Vietnamese_Embedding` (hoặc tương đương) được tối ưu cho tiếng Việt.
*   **Lưu trữ**:
    *   `vectorized_data.pkl`: Chứa vector embeddings và metadata đầy đủ.
    *   `vectorized_metadata.json`: Chứa thông tin văn bản và metadata để tra cứu nhanh.
*   **Cấu trúc Vector**: Mỗi đoạn văn bản được chuyển thành một vector 768 chiều (tùy model) và lưu vào FAISS Index để tìm kiếm độ tương đồng cosine.

---
*Tài liệu này được cập nhật tự động bởi hệ thống Agentic RAG.*
