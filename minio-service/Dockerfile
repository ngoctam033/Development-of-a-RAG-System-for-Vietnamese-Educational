FROM bitnami/minio:latest

# Chạy MinIO và tạo bucket trực tiếp
CMD ["/bin/sh", "-c", "minio server --address ':9000' --console-address ':9001' /bitnami/minio/data"]