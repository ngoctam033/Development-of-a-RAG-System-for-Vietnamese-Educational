# Project Class Hierarchy

This document describes the architectural structure of the Agentic RAG system using a class diagram. To maintain consistency and modularity, all system components inherit from a common base class.

## Class Diagram

```mermaid
classDiagram
    %% Base class defining the standard interface
    class BaseComponent {
        <<abstract>>
        +String name
        +Dict config
        +Logger logger
        +__init__(name, config)
        +run()* void
        +get_status() String
        +to_dict() Dict
    }

    %% PDF to Markdown extraction
    class Extractor {
        +String input_path
        +String output_format
        +MinIOStorage storage
        +__init__(name, config)
        +extract_text(local_pdf_path) String
        +save_intermediate(content, object_name) bool
        +run() String
    }

    %% Content chunking and metadata enrichment
    class Processor {
        +MinIOStorage storage
        +int chunk_size
        +int chunk_overlap
        +fetch_markdown(bucket_name, object_name) String
        +convert_to_json(markdown_content) Dict
        +save_json(bucket_name, object_name, data) bool
        +chunk_data(markdown_content) List
        +add_metadata(chunks) List
        +run() void
    }

    %% Vectorization and storage
    class Indexer {
        +String vector_db_type
        +String embedding_model_id
        +create_embeddings(text_list) List
        +upsert_to_vector_store(embeddings, metadata) void
        +run() void
    }

    %% Retrieval logic
    class Retriever {
        +int top_k
        +float similarity_threshold
        +search(query) List
        +rerank(results) List
        +run() void
    }

    %% LLM Response Generation
    class Generator {
        +String model_name
        +PromptTemplate template
        +generate_response(context, query) String
        +run() void
    }

    %% Object Storage (MinIO)
    class MinIOStorage {
        +String endpoint
        +String bucket_name
        +list_buckets() List
        +list_objects(bucket_name, prefix) List
        +download_object(bucket_name, object_name) bytes
        +upload_object(bucket_name, object_name, data) bool
        +run() void
    }

    %% System utility
    class SingletonLogger {
        -SingletonLogger _instance$
        -Lock _lock$
        +Logger logger
        +__new__() SingletonLogger
        +__init__() void
        +get_logger() Logger
    }

    %% Relationships (Inheritance)
    BaseComponent <|-- Extractor
    BaseComponent <|-- Processor
    BaseComponent <|-- Indexer
    BaseComponent <|-- Retriever
    BaseComponent <|-- Generator
    BaseComponent <|-- MinIOStorage

    %% Composition/Usage
    Extractor "1" --> "1" MinIOStorage : uses for storage
    Processor "1" --> "1" MinIOStorage : uses for storage
```

## Component Details

### 1. BaseComponent (Abstract)
The root class for all functional modules in the pipeline. It ensures that every component has a consistent way of being initialized, executed, and providing status updates.

- **`name`**: Unique identifier for the component instance.
- **`config`**: Dictionary containing component-specific settings (e.g., paths, hyperparameters).
- **`run()`**: The main execution entry point for the component.

### 2. Extractor
Handles the conversion of raw documents (PDFs) into an intermediate format (Markdown).
- **Inherits from**: `BaseComponent`

### 3. Processor
Responsible for semantic chunking of the intermediate Markdown content and enriching chunks with relevant metadata.
- **Inherits from**: `BaseComponent`

### 4. Indexer
Manages the embedding process and interaction with the Vector Database (e.g., Qdrant or Chroma).
- **Inherits from**: `BaseComponent`

### 5. Retriever
Executes the search logic to find the most relevant chunks based on a user query.
- **Inherits from**: `BaseComponent`

### 6. Generator
Interfaces with the LLM to generate the final educational responses based on retrieved context.
- **Inherits from**: `BaseComponent`

### 7. MinIOStorage
Handles interactions with MinIO for storing raw, intermediate, and processed files.
- **Inherits from**: `BaseComponent`

### 8. SingletonLogger
A thread-safe singleton utility providing a unified logging interface for the entire system.
- **Note**: This is a standalone utility, not inheriting from `BaseComponent`.

## Pipeline Flow

The following diagram illustrates how the components interact to create an automated ETL/Indexing pipeline.

```mermaid
graph TD
    A[Raw PDF in MinIO] --> B(Extractor)
    B -->|Markdown Output| C[MinIO Storage]
    C --> D(Processor)
    D -->|Semantic Chunks| E[MinIO Storage]
    E --> F(Indexer)
    F -->|Embedded Data| G[Vector Database]
    
    subgraph "Core Components"
        B
        D
        F
    end
    
    subgraph "Storage Layer (MinIO)"
        A
        C
        E
    end
    
    subgraph "Search Engine"
        G
    end
```

- **Modular Design**: Each step is implemented as a standalone component, allowing for easy testing and integration.
- **MinIO Intermediary Store**: MinIO serves as the source of truth for all data transitions between tasks, ensuring reproducibility and reliability.
