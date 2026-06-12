from datetime import datetime

from airflow.sdk import dag, task # type: ignore[import-not-found]


@dag(
    dag_id="hello_insightops",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["insightops", "day-7"],
)
def hello_insightops_dag():
    @task
    def say_hello() -> str:
        message = "Hello from InsightOps Airflow DAG"
        print(message)
        return message

    say_hello()


hello_insightops_dag()
