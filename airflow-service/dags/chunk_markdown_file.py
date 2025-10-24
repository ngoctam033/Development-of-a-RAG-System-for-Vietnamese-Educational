from airflow.sdk import dag
from datetime import datetime
from tasks.chunks_markdown import hello_world
from tasks.minio import get_file_from_minio

@dag(
    dag_id="chunk_markdown_file",
    schedule=None,
    start_date= datetime(2025, 1, 1),
    catchup=False,
    tags=["manual", "example"],
)
def chunk_markdown_file():
    a = hello_world()
    b = get_file_from_minio()
    a >> b

dag = chunk_markdown_file()
