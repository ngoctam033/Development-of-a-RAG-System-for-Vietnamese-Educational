from airflow.sdk import dag, task, Param

from src.pipeline.chunking.p02_processor import ProcessorTasks

from src.config.configs import MINIO_CONFIG

import os

# Default arguments for the DAG
default_args = {
    'owner': 'tam',
}

@dag(
    dag_id='md_to_json_conversion_pipeline',
    default_args=default_args,
    description='A DAG to convert Markdown files to JSON via Dictionary parsing',
    schedule=None,
    catchup=False,
    tags=['markdown', 'processing', 'json'],
    # Cấu hình Params để hiển thị Form nhập liệu trên UI
    params={
        "input_file": Param(
            "intermediate/Mạng máy tính và truyền thông dữ liệu.md", 
            type="string", 
            description="Đường dẫn file Markdown đầu vào trong bucket"
        ),
    }
)
def md_to_json_pipeline():
    processor = ProcessorTasks()

    @task(task_id='fetch_markdown_file')
    def fetch_markdown(**kwargs):
        """Lấy file Markdown dựa trên tham số truyền vào."""
        # Lấy file_path từ params (ưu tiên) hoặc conf
        conf = kwargs.get('dag_run').conf or {}
        input_file = conf.get('input_file', kwargs['params']['input_file'])
        
        print(f"🚀 Đang xử lý file: {input_file}")
        
        # Lưu input_file vào XCom để task sau biết đường mà đặt tên file JSON
        kwargs['ti'].xcom_push(key='current_input_file', value=input_file)
        
        # Tách category và filename nếu có đường dẫn
        # Ví dụ: "intermediate/file.md" -> category="intermediate", filename="file.md"
        if "/" in input_file:
            parts = input_file.split("/")
            category = parts[0]
            filename = parts[-1]
        else:
            category = "intermediate"
            filename = input_file
        
        return processor.fetch_markdown(
            bucket_name=MINIO_CONFIG["bucket"],
            filename=filename,
            category=category
        )

    @task(task_id='convert_to_json')
    def convert_to_json(markdown_content: str, **kwargs):
        """Chuyển đổi Markdown sang JSON kèm theo tên file trong metadata."""
        # Lấy tên file gốc từ XCom (do task fetch_markdown_file đẩy lên)
        input_file = kwargs['ti'].xcom_pull(task_ids='fetch_markdown_file', key='current_input_file')
        
        # Lấy tên file không bao gồm extension làm title
        file_title = os.path.splitext(os.path.basename(input_file))[0]
        
        return processor.convert_to_json(
            markdown_content=markdown_content,
            file_title=file_title
        )

    @task(task_id='save_json_file')
    def save_json(data: dict, **kwargs):
        """Lưu file JSON với tên tương ứng với file đầu vào."""
        # Lấy lại tên file đầu vào từ Task trước đó qua XCom
        input_file = kwargs['ti'].xcom_pull(task_ids='fetch_markdown_file', key='current_input_file')
        
        # Lấy tên file không bao gồm thư mục
        filename = os.path.basename(input_file).replace('.md', '.json')
        
        print(f"💾 Đang lưu kết quả vào thư mục processed với tên: {filename}")
        
        return processor.save_json(
            bucket_name=MINIO_CONFIG["bucket"],
            filename=filename,
            data=data,
            category="processed"
        )

    # Thiết lập luồng
    md_content = fetch_markdown()
    json_data = convert_to_json(md_content)
    save_json(json_data)

md_to_json_pipeline()
