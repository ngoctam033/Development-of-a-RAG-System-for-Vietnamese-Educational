# syntax=docker/dockerfile:1
FROM apache/airflow:3.1.6

USER root

USER airflow

COPY --chown=airflow:root airflow/requirements.txt /tmp/requirements.txt

RUN --mount=type=cache,target=/home/airflow/.cache/pip \
    pip install --user --no-cache-dir -r /tmp/requirements.txt