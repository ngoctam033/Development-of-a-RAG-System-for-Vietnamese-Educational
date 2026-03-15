# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

# Cài đặt thư viện sử dụng bind mount từ setup/python_packages để đảm bảo offline và tối ưu image
# Lưu ý: Cần build với context là root của project
RUN --mount=type=bind,source=setup/python_packages,target=/tmp/python_packages \
    --mount=type=bind,source=embedding/requirements.txt,target=/tmp/requirements.txt \
    pip install --no-cache-dir --no-index --find-links=/tmp/python_packages -r /tmp/requirements.txt

# Copy service code
COPY embedding/service.py .

# Expose BentoML port
EXPOSE 3000

# Run the service
CMD ["bentoml", "serve", "service:EmbeddingService", "--host", "0.0.0.0", "--port", "3000"]
