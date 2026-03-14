# Data Pipeline Specification — Markdown to JSON Conversion

## 1. Goal & Scope

This specification covers the **Chunking & Processing** stage of the RAG pipeline. It transforms raw Markdown documents (extracted from PDFs) into flat, structured JSON records ready for vector indexing.

**In scope**: MinIO storage interaction, Markdown parsing, section flattening, metadata enrichment, Airflow orchestration.
**Out of scope**: PDF extraction (Stage 1), vector embedding & indexing (Stage 3).

---

## 2. Data Flow

```
MinIO: raw/        →   [Extractor]   →   MinIO: intermediate/
MinIO: intermediate/ →  [Processor]  →   MinIO: processed/
MinIO: processed/   →   [Indexer]    →   Weaviate Vector DB
```

This spec focuses on the **[Processor]** step.

---

## 3. MinIO Bucket Structure

All data within a single bucket (default: `rag`) is separated by directory prefix:

| Directory | Content | Managed By |
| :--- | :--- | :--- |
| `raw/` | Original PDF files | `Extractor` |
| `intermediate/` | Markdown files (`.md`) | `Extractor` |
| `processed/` | Flat JSON chunk files (`.json`) | `ProcessorTasks` |

Path resolution is centralized in `MinIOPathManager` to ensure consistency.

---

## 4. Class Responsibilities

### `MinIOPathManager` (`src/utils/minio_path_manager.py`)
- Defines the canonical directory structure for MinIO.
- `get_path(category, filename)` → returns the full object path (e.g., `intermediate/my_file.md`).
- `validate_category(category)` → raises an error if the category is not `raw`, `intermediate`, or `processed`.

### `MinIOStorage` (`src/database/minio_storage.py`)
- Wraps the `minio` Python client.
- Loads credentials from `src/config/configs.py` (environment variables).
- On initialization, calls `ping()` to verify the connection.
- Key methods: `list_buckets()`, `list_objects()`, `download_object()`, `upload_object()`.

### `ProcessorTasks` (`src/pipeline/chunking/p02_processor.py`)
Orchestrates the full Markdown → JSON conversion workflow.

| Method | Description |
| :--- | :--- |
| `fetch_markdown(bucket, filename, category)` | Downloads `.md` from MinIO, returns content as `str`. |
| `parse_markdown_to_dict(content, file_title)` | Parses hierarchy of headers into a nested dict tree. |
| `flatten_hierarchical_dict(nested_dict)` | Converts the nested tree into a flat `list[dict]`. |
| `convert_to_json(content, file_title)` | Orchestrates parse + flatten, returns formatted JSON string. |
| `save_json(bucket, filename, data, category)` | Serializes and uploads JSON to MinIO. |

---

## 5. Output Format

Each processed file is a JSON array. Each element represents one section (header node):

```json
[
    {
        "id": "section_1",
        "title": "Chương trình đào tạo",
        "content": "Nội dung của section...",
        "metadata": {
            "header_path": "Ten File > Chương trình đào tạo"
        }
    },
    {
        "id": "section_1_1",
        "title": "Mục tiêu đào tạo",
        "content": "Nội dung mục tiêu...",
        "metadata": {
            "header_path": "Ten File > Chương trình đào tạo > Mục tiêu đào tạo"
        }
    }
]
```

**Key fields**:
- `id`: Hierarchical key (e.g., `section_1_2_3`) reflecting document structure.
- `title`: Section header text (Markdown `**` stripped).
- `content`: Text content under this header.
- `metadata.header_path`: Breadcrumb trail from file root to this section, joined by ` > `.

---

## 6. Airflow DAG Design

- **DAG ID**: defined in `airflow/dags/processor.py`.
- **Trigger**: Manual only (`schedule=None`). No automatic scheduling.
- **Task dependencies**: `fetch_markdown → convert_to_json → save_json` (sequential).
- **Error handling**: Each task logs success/failure via the singleton logger. Failures raise exceptions, allowing Airflow to retry.
