# Các biến cấu hình MinIO/S3
MINIO_ENDPOINT = "localhost:9000"
MINIO_PORT = 9000
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
MINIO_SECURE = False  # True nếu dùng https

DEFAULT_BUCKET_NAME = "datawarehouse"

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