from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task


@dag(
    dag_id="process_dataset",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["insightops", "datasets", "day-7"],
)
def process_dataset_dag():
    @task
    def check_dataset_file(file_path: str) -> str:
        airflow_file_path = file_path.replace(
            "uploads/",
            "/opt/airflow/uploads/",
            1,
        )

        path = Path(airflow_file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        print(f"Dataset file found: {path}")
        return str(path)

    check_dataset_file("{{ dag_run.conf['file_path'] }}")


process_dataset_dag()
