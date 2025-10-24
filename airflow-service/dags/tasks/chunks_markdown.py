from airflow.sdk import task
@task()
def hello_world():
    print("Hello from manual DAG!")