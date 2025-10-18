#!/bin/bash
set -e

# Function to start Spark Master
start_master() {
    echo "Starting Spark Master..."
    exec /opt/spark/bin/spark-class org.apache.spark.deploy.master.Master \
        --host 0.0.0.0 \
        --port 7077 \
        --webui-port 8080
}

# Function to start Spark Worker
start_worker() {
    echo "Starting Spark Worker..."
    # Simple wait without netcat
    echo "Waiting for Spark Master to be ready..."
    sleep 10
    
    exec /opt/spark/bin/spark-class org.apache.spark.deploy.worker.Worker \
        ${SPARK_MASTER_URL:-spark://spark-master:7077} \
        --memory ${SPARK_WORKER_MEMORY:-1g} \
        --cores ${SPARK_WORKER_CORES:-1} \
        --webui-port 8081
}

# Check SPARK_MODE environment variable
case "${SPARK_MODE:-}" in
    "master")
        start_master
        ;;
    "worker")
        start_worker
        ;;
    *)
        echo "Unknown SPARK_MODE: ${SPARK_MODE}"
        echo "Please set SPARK_MODE to 'master' or 'worker'"
        exit 1
        ;;
esac