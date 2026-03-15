# syntax=docker/dockerfile:1
FROM apache/airflow:3.1.6

USER root

USER airflow

# Cài đặt thư viện từ requirements.txt sử dụng bind mount để tối ưu dung lượng image
# --mount=type=bind: Gắn tạm thư mục packages từ host vào container chỉ trong lúc install
# --no-index: Chỉ tìm kiếm package trong local, không qua internet
RUN --mount=type=bind,source=setup/python_packages,target=/tmp/python_packages \
    --mount=type=bind,source=airflow/requirements.txt,target=/tmp/requirements.txt \
    pip install --no-cache-dir --no-index --find-links=/tmp/python_packages -r /tmp/requirements.txt