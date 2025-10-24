import logging
from airflow.sdk import task
from airflow.operators.python import get_current_context
from tasks.minio_client import MinioClient
from config.minio_config import MINIO_FOLDERS, MINIO_BUCKET


@task()
def get_file_from_minio():
    """
    Fetch file content from MinIO and store it in XCom.

    Args:
        bucket_name (str): MinIO bucket name.
        object_name (str): MinIO object (file) name.
    """
    context = get_current_context()
    ti = context['ti']
    conf = context['dag_run'].conf if context.get('dag_run') else {}
    bucket_name = conf.get('bucket_name', MINIO_BUCKET)
    folder_prefix = conf.get('folder_prefix', MINIO_FOLDERS['raw'])
    if not bucket_name or not folder_prefix:
        logging.error("Missing required parameters: 'bucket_name' or 'folder_prefix' in DAG trigger.")
        ti.xcom_push(key="minio_file_data", value=None)
        raise ValueError("You must provide both 'bucket_name' and 'folder_prefix' when triggering the DAG!")
    try:
        client = MinioClient().get_client()
        files_data = {}
        for obj in client.list_objects(bucket_name, prefix=folder_prefix, recursive=True):
            try:
                response = client.get_object(bucket_name, obj.object_name)
                data = response.read()
                files_data[obj.object_name] = data
                logging.info(f"Fetched file '{obj.object_name}' from bucket '{bucket_name}'. Size: {len(data)} bytes.")
            except Exception as file_err:
                logging.error(f"Failed to fetch file '{obj.object_name}' from MinIO: {file_err}")
        ti.xcom_push(key="minio_file_data", value=files_data)
    except Exception as e:
        logging.error(f"Failed to list objects from MinIO: {e}")
        ti.xcom_push(key="minio_file_data", value=None)
