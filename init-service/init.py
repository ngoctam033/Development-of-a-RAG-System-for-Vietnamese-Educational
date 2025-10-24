from minio import Minio
import os
# from config import MINIO_CLUSTER_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_SECURE, DEFAULT_BUCKET_NAME

# Tạo path tuyệt đối cho file .duckdb trong project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Các biến cấu hình MinIO/S3
MINIO_ENDPOINT = "localhost:9000"
MINIO_PORT = 9000
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
MINIO_SECURE = False  # True nếu dùng https

DEFAULT_BUCKET_NAME = "datalakehouse"

# Endpoint cho MinIO
MINIO_CLUSTER_ENDPOINT = "minio1:9000"  # hoặc minio1:9000 nếu trong cluster

# Cấu hình DuckDB S3
S3_CONFIG = {
    "s3_endpoint": MINIO_ENDPOINT,
    "s3_access_key_id": MINIO_ACCESS_KEY,
    "s3_secret_access_key": MINIO_SECRET_KEY,
    "s3_url_style": "path",
    "s3_use_ssl": MINIO_SECURE,
    "s3_region": ""
}
# Kết nối tới MinIO
client = Minio(
    MINIO_CLUSTER_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

bucket_name = DEFAULT_BUCKET_NAME

# Tạo bucket nếu chưa có
if not client.bucket_exists(bucket_name):
    client.make_bucket(bucket_name)
    # nếu tạo thành công
    print(f"Bucket '{bucket_name}' đã được tạo thành công.")