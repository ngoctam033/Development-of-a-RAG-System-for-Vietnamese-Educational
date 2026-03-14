FROM apache/airflow:3.1.6

USER root

USER airflow

# Copy requirements và local packages (nếu có)
COPY --chown=airflow:0 airflow/requirements.txt /tmp/requirements.txt
COPY --chown=airflow:0 setup/python_packages /tmp/python_packages

# Bắt buộc cài đặt offline (--no-index) từ thư mục /tmp/python_packages
# Điều này đảm bảo hoàn toàn không tải lại từ internet mỗi lần build
RUN pip install --no-cache-dir --no-index --find-links=/tmp/python_packages -r /tmp/requirements.txt