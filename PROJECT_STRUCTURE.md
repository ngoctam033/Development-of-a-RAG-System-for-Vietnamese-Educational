# **Project Structure: Agentic RAG MLOps Pipeline**

This project builds a Vietnamese Educational RAG system with a fully modular MLOps pipeline. The current phase focuses on the Data Processing Pipeline (ETL/Indexing).

## **1. Directory Tree**

```
├── airflow/                    # Orchestration infrastructure with Apache Airflow
│   ├── dags/                   # Directed Acyclic Graph definitions
│   │   └── processor.py        # DAG: Markdown → JSON conversion (manual trigger)
│   ├── config/
│   │   └── airflow.cfg         # Airflow configuration overrides
│   ├── plugins/                # Custom Airflow plugins
│   ├── Dockerfile              # Custom Airflow image (offline pip install)
│   ├── docker-compose.airflow.yaml # Airflow service definitions
│   └── requirements.txt        # Python packages (minio, weaviate-client)
├── data/                       # Data management (not committed to Git)
│   ├── raw/                    # Original PDF input files
│   ├── intermediate/           # Extracted Markdown files (.md)
│   └── processed/              # Flat JSON chunks ready for indexing
├── docs/                       # Human-readable documentation
│   ├── architecture/
│   │   └── class_diagram.md    # Class hierarchy & component relationships
│   └── chunking_pipeline.md    # Detailed pipeline flow (PDF → MD → JSON → Vector)
├── minio/                      # Object Storage infrastructure
│   └── docker-compose.minio.yaml # MinIO service definition
├── setup/                      # Pre-build artifacts (gitignored)
│   └── python_packages/        # Offline pip packages for Airflow Dockerfile
├── specs/                      # Feature specifications (PRD)
│   └── data_pipeline_spec.md   # Functional spec for the data pipeline
├── src/                        # Main application source code
│   ├── __init__.py
│   ├── config/
│   │   └── configs.py          # Centralized environment variable loading
│   ├── core/                   # Shared logic (Logging, Base Classes)
│   │   ├── logger.py           # Singleton Logger (core)
│   │   └── base.py             # Abstract Base Class for all components
│   ├── database/               # Storage connectors
│   │   ├── __init__.py
│   │   └── minio_storage.py    # MinIO Object Storage client wrapper
│   ├── pipeline/               # Main data processing pipeline
│   │   ├── chunking/           # Chunking module
│   │   │   ├── p01_extractor.py # PDF → Markdown (vision-parse + Gemini)
│   │   │   ├── p02_processor.py # Markdown → Flat JSON chunks (ProcessorTasks)
│   │   │   └── p03_indexer.py  # JSON chunks → Vector Store
│   │   └── chunking_pipeline.py # End-to-end pipeline orchestrator
│   ├── agents/                 # Agent implementations (LangGraph/CrewAI)
│   └── utils/                  # Utility helpers
│       ├── __init__.py
│       ├── logger.py           # Singleton Logger (utils wrapper)
│       └── minio_path_manager.py # Centralized MinIO path conventions
├── weaviate/                   # Vector Database infrastructure
│   └── docker-compose.weaviate.yaml # Weaviate service definition
├── docker-compose.yaml         # Root compose using `include` to merge all services
├── .env.example                # Environment variable template
├── requirements.txt            # Root Python dependencies
└── README.md                   # Project overview & deployment guide
```

## **2. Data Pipeline Flow**

Pipeline is modular and tracked via MinIO at each stage:

1.  **Extractor (`p01_extractor.py`)**:
    *   Input: PDF from MinIO `raw/`.
    *   Technology: `vision-parse` + Gemini API.
    *   Output: `.md` file saved to MinIO `intermediate/`.

2.  **Processor (`p02_processor.py` — `ProcessorTasks` class)**:
    *   Reads `.md` from MinIO `intermediate/`.
    *   Parses Markdown header hierarchy into a nested dict.
    *   Flattens structure into a list of section dicts with `header_path` metadata.
    *   Output: Flat `.json` saved to MinIO `processed/`.

3.  **Indexer (`p03_indexer.py`)**:
    *   Reads chunks from MinIO `processed/`.
    *   Generates embeddings and inserts into Weaviate Vector DB.

4.  **Orchestration (`airflow/dags/processor.py`)**:
    *   Airflow DAG wiring tasks: `fetch_markdown → convert_to_json → save_json`.
    *   Manual trigger only.

## **3. Core Modules**

1.  **`BaseComponent` (`src/core/base.py`)**:
    *   Abstract Base Class for all pipeline components.
    *   Enforces a `run()` method. Provides unified logging.

2.  **`SingletonLogger` (`src/utils/logger.py`)**:
    *   Thread-safe, single-instance logger for the entire system.

3.  **`MinIOStorage` (`src/database/minio_storage.py`)**:
    *   Wraps the `minio` Python client.
    *   Loads credentials from `src/config/configs.py`.
    *   Verifies connection on startup via `ping()`.
    *   Methods: `list_buckets()`, `list_objects()`, `download_object()`, `upload_object()`.

4.  **`MinIOPathManager` (`src/utils/minio_path_manager.py`)**:
    *   Single source of truth for MinIO path conventions.
    *   Categories: `raw/`, `intermediate/`, `processed/`.
    *   Validates paths before any storage operation.

## **4. Infrastructure**

1.  **MinIO (`minio/`)**:
    *   S3-compatible Object Storage for all pipeline data stages.
    *   Console: [http://localhost:9001](http://localhost:9001)

2.  **Weaviate (`weaviate/`)**:
    *   Vector Database for semantic chunk storage and retrieval.
    *   API: [http://localhost:8080](http://localhost:8080)

3.  **Airflow (`airflow/`)**:
    *   CeleryExecutor-based orchestration with Redis + PostgreSQL.
    *   UI: [http://localhost:8081](http://localhost:8081)

4.  **Docker Compose Root (`docker-compose.yaml`)**:
    *   Uses `include` to compose all service files into one stack.
    *   All services share `rag_network`.