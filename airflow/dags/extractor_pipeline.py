from airflow.sdk import dag, task, Param
from src.pipeline.chunking.p01_extractor import Extractor
from src.config.configs import MINIO_CONFIG
from src.utils.logger import logger
import os

default_args = {
    'owner': 'tam',
}

@dag(
    dag_id='pdf_to_md_extraction_pipeline',
    default_args=default_args,
    description='A DAG to extract Markdown from PDF files using vision-parse',
    schedule=None,
    catchup=False,
    tags=['pdf', 'extraction', 'markdown'],
    params={
        "input_file": Param(
            "raw/Mạng máy tính và truyền thông dữ liệu.pdf", 
            type="string", 
            description="Đường dẫn file PDF trong bucket (raw/)"
        ),
    }
)
def extraction_pipeline():
    extractor = Extractor()

    @task(task_id='fetch_pdf_file')
    def fetch_pdf(**kwargs):
        """Lấy file PDF dựa trên tham số truyền vào."""
        conf = kwargs.get('dag_run').conf or {}
        input_file = conf.get('input_file', kwargs['params']['input_file'])
        
        logger.info(f"🚀 Đang xử lý file PDF: {input_file}")
        
        # Lưu input_file vào XCom cho các task sau
        kwargs['ti'].xcom_push(key='current_input_file', value=input_file)
        
        if "/" in input_file:
            parts = input_file.split("/")
            category = parts[0]
            filename = parts[-1]
        else:
            category = "raw"
            filename = input_file
        
        return extractor.fetch_pdf(
            bucket_name=MINIO_CONFIG["bucket"],
            filename=filename,
            category=category
        )

    @task(task_id='convert_pdf_to_md')
    def convert_to_md(pdf_bytes: bytes, **kwargs):
        """Chuyển đổi PDF sang Markdown."""
        input_file = kwargs['ti'].xcom_pull(task_ids='fetch_pdf_file', key='current_input_file')
        filename = os.path.basename(input_file)
        
        return extractor.convert_to_markdown(pdf_bytes, filename)

    @task(task_id='save_md_file')
    def save_md(markdown_content: str, **kwargs):
        """Lưu file Markdown kết quả."""
        input_file = kwargs['ti'].xcom_pull(task_ids='fetch_pdf_file', key='current_input_file')
        filename = os.path.basename(input_file)
        
        return extractor.save_markdown(
            bucket_name=MINIO_CONFIG["bucket"],
            filename=filename,
            markdown_content=markdown_content,
            category="intermediate"
        )

    # Thiết lập luồng
    pdf_data = fetch_pdf()
    md_content = convert_to_md(pdf_data)
    save_md(md_content)

extraction_pipeline()
