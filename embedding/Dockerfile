# syntax=docker/dockerfile:1
FROM python:3.12

WORKDIR /app

COPY embedding/requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Run the service
CMD ["bentoml", "serve", "service:EmbeddingService", "--host", "0.0.0.0", "--port", "3000"]
