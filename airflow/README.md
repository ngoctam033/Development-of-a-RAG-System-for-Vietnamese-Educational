# Apache Airflow — RAG Pipeline Orchestration

This module orchestrates the **Markdown → JSON** data pipeline for the Vietnamese Educational RAG system using Apache Airflow 3 with CeleryExecutor.

---

## 📂 Directory Structure

```text
airflow/
├── dags/
│   ├── processor.py            # DAG: Markdown → JSON conversion (manually triggered)
│   └── src -> (mounted from ../src)  # Pipeline source code (volume mount)
├── config/
│   └── airflow.cfg             # Airflow configuration overrides
├── plugins/                    # Custom Airflow plugins (currently empty)
├── logs/                       # Task execution logs (auto-generated, gitignored)
├── Dockerfile                  # Custom Airflow image with pre-installed packages
├── docker-compose.airflow.yaml # Airflow service definitions
└── requirements.txt            # Python packages installed into the image
```

---

## ⚙️ DAGs

### `processor.py` — Markdown to JSON Pipeline
- **Trigger**: Manual only (`schedule=None`).
- **Tasks**:
  1. `fetch_markdown` — Downloads a `.md` file from MinIO `intermediate/`.
  2. `convert_to_json` — Parses Markdown hierarchy into a flat list of JSON sections.
  3. `save_json` — Uploads the result to MinIO `processed/`.
- **Uses**: `ProcessorTasks` class from `src/pipeline/chunking/p02_processor.py`.

---

## 🐳 Dockerfile Pre-Build Setup (Offline Installation)

The `Dockerfile` installs Python packages from a **local folder** (`setup/python_packages`) instead of downloading from PyPI at build time. This makes subsequent builds fast and fully offline.

> [!IMPORTANT]
> You **must** complete this setup before running `docker compose up --build` for the first time.

### Step 1: Create the local packages folder

```bash
mkdir -p setup/python_packages
```

### Step 2: Download packages into the local folder

This downloads all packages from `airflow/requirements.txt` and their dependencies:

```bash
pip download \
  -r airflow/requirements.txt \
  -d setup/python_packages
```

> [!NOTE]
> This step requires an internet connection and takes a few minutes. It only needs to be done once, or when `requirements.txt` changes.

### Step 3: Verify the folder is populated

```bash
ls setup/python_packages
# Expected output: minio-*.whl, weaviate_client-*.whl, etc.
```

### Step 4: Build and start all services

```bash
docker compose up -d --build
```

The Dockerfile will install packages directly from `setup/python_packages` — **no internet needed** during the build.

---

## 🤖 Tải Embedding Model (Offline usage)

Hệ thống sử dụng model `AITeamVN/Vietnamese_Embedding` để vector hóa dữ liệu. Để Airflow có thể chạy offline hoàn toàn, bạn cần tải model này về máy host trước bằng script tự động.

### Step 1: Cài đặt thư viện hỗ trợ
```bash
pip install huggingface_hub
```

### Step 2: Chạy script tải model
Script `get_model.py` tại root của dự án sẽ tự động tải đúng model và lưu vào đúng thư mục (`setup/models/embedding-model`) đã được mount vào container.

```bash
python get_model.py
```

> [!TIP]
> Việc mount thư mục này giúp bạn tránh việc phải tải lại model (~2GB) mỗi lần khởi động container và đảm bảo tính nhất quán giữa file cấu hình `configs.py` và model thực tế.

---

## 🔑 Environment Variables

All variables are loaded from the root `.env` file (see `.env.example`). Key variables for Airflow:

```dotenv
AIRFLOW_UID=1000                    # Must match your host user UID (run: id -u)
MINIO_ENDPOINT=minio1:9000          # Internal MinIO address
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123
MINIO_BUCKET=rag
GEMINI_API_KEY_1=your_key_here
```

---

## 🌐 Included Services

The `docker-compose.airflow.yaml` defines the following containers, all on `rag_network`:

| Container | Role |
| :--- | :--- |
| `rag_af_api` | Airflow API Server & Web UI (port `8081`) |
| `rag_af_scheduler` | Task scheduler |
| `rag_af_worker` | Celery worker (executes tasks) |
| `rag_af_processor` | DAG file processor |
| `rag_af_triggerer` | Async task triggerer |
| `rag_af_init` | One-time DB migration & admin user creation |
| `rag_af_db` | PostgreSQL metadata database |
| `rag_af_redis` | Redis broker for Celery |

---

## 📡 Dashboard

- **Airflow UI**: [http://localhost:8081](http://localhost:8081) — Default credentials: `airflow` / `airflow`
