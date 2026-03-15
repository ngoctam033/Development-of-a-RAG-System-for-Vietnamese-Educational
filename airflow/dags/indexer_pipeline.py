from airflow.sdk import dag, task, Param
from src.pipeline.chunking.p03_indexer import IndexerTasks
from src.config.configs import MINIO_CONFIG
from src.utils.logger import logger

default_args = {
    'owner': 'tam',
}

@dag(
    dag_id='json_to_vector_indexing_pipeline',
    default_args=default_args,
    description='A DAG to vectorize JSON chunks and store them in Weaviate',
    schedule=None,
    catchup=False,
    tags=['json', 'indexing', 'weaviate', 'vector'],
    params={
        "input_file": Param(
            "processed/Mạng máy tính và truyền thông dữ liệu.json", 
            type="string", 
            description="Đường dẫn file JSON chunks trong bucket (processed/)"
        ),
    }
)
def indexer_pipeline():
    indexer = IndexerTasks()

    @task(task_id='fetch_chunks_file')
    def fetch_chunks(**kwargs):
        """Lấy file JSON chunks dựa trên tham số truyền vào."""
        conf = kwargs.get('dag_run').conf or {}
        input_file = conf.get('input_file', kwargs['params']['input_file'])
        
        logger.info(f"🚀 Đang xử lý file chunks: {input_file}")
        
        if "/" in input_file:
            parts = input_file.split("/")
            category = parts[0]
            filename = parts[-1]
        else:
            category = "processed"
            filename = input_file
        
        chunks = indexer.fetch_chunks(
            bucket_name=MINIO_CONFIG["bucket"],
            filename=filename,
            category=category
        )
        return chunks

    @task(task_id='vectorize_chunks')
    def vectorize_chunks(chunks: list):
        """Vector hóa nội dung các chunks."""
        return indexer.vectorize_content(chunks)

    @task(task_id='upsert_to_vector_db')
    def upsert_to_db(chunks: list, embeddings: list):
        """Lưu vào Vector Database."""
        return indexer.upsert_to_vector_db(chunks, embeddings)

    # Thiết lập luồng
    chunks_data = fetch_chunks()
    embeddings_data = vectorize_chunks(chunks_data)
    upsert_to_db(chunks_data, embeddings_data)

indexer_pipeline()
