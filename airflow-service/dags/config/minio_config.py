# Thông tin kết nối MinIO
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123"
MINIO_SECURE = False
MINIO_BUCKET = "datalakehouse"
# MINIO_PROJECTS = ["math", "physics", "chemistry"]  # hoặc sinh động từ DB
MINIO_FOLDERS = {
    "raw": "raw",                # Dữ liệu gốc
    "processed": "processed",    # Dữ liệu đã xử lý
    "vectorized": "vectorized"   # Dữ liệu đã vector hóa
}

def get_minio_path(project, stage, filename):
    """
    Sinh đường dẫn lưu trữ cho file trong MinIO theo cấu trúc 3 lớp
    stage: 'raw', 'processed', 'vectorized'
    """
    return f"{MINIO_BUCKET}/{project}/{MINIO_FOLDERS[stage]}/{filename}"