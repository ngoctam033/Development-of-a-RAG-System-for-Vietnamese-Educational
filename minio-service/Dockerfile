FROM bitnami/minio:latest
ENV BUCKET_NAME=datalakehouse
CMD ["/bin/sh", "-c", " \
    minio server --address ':9000' --console-address ':9001' /bitnami/minio/data & \
    MINIO_PID=$! ; \
    \
    echo 'Đang thiết lập Alias và chờ MinIO sẵn sàng...' ; \
    \
    # 1. Vòng lặp kiểm tra sẵn sàng
    for i in $(seq 1 20); do \
        /opt/bitnami/minio-client/bin/mc alias set local http://localhost:9000 $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD && break ; \
        echo 'Chưa sẵn sàng, chờ 3 giây...' ; \
        sleep 3 ; \
    done ; \
    \
    # 2. Tạo Bucket chỉ khi alias đã thiết lập thành công
    if /opt/bitnami/minio-client/bin/mc mb local/${BUCKET_NAME}; then \
        echo 'Khởi tạo hoàn tất. Bucket đã được tạo: ${BUCKET_NAME}' ; \
    else \
        echo '❌ Lỗi: Không thể tạo bucket ${BUCKET_NAME}. Vui lòng kiểm tra cấu hình và thử lại.' ; \
        /opt/bitnami/minio-client/bin/mc ls local || echo '❌ Lỗi: Không thể liệt kê các bucket. Kiểm tra kết nối MinIO.' ; \
        exit 1 ; \
    fi ; \
    \
    # 3. Giữ MinIO Server chạy ở foreground
    wait $MINIO_PID \
"]