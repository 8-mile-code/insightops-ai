import csv
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg2  # type: ignore[import-not-found]
from psycopg2.extras import Json  # type: ignore[import-not-found]
from airflow.exceptions import AirflowFailException  # type: ignore[import-not-found]
from airflow.sdk import dag, task  # type: ignore[import-not-found]

PIPELINE_STATUS_RUNNING = "running"
PIPELINE_STATUS_SUCCESS = "success"
PIPELINE_STATUS_FAILED = "failed"

REQUIRED_COLUMNS = {
    "order_id",
    "customer_id",
    "amount",
    "status",
    "created_at",
}

ALLOWED_STATUSES = {
    "paid",
    "failed",
    "pending",
    "cancelled",
    "refunded",
}


def get_connection():
    return psycopg2.connect(
        host=os.environ["INSIGHTOPS_DB_HOST"],
        port=os.environ["INSIGHTOPS_DB_PORT"],
        user=os.environ["INSIGHTOPS_DB_USER"],
        password=os.environ["INSIGHTOPS_DB_PASSWORD"],
        dbname=os.environ["INSIGHTOPS_DB_NAME"],
    )


def mark_pipeline_run_failed(context: dict[str, Any]) -> None:
    task_instance = context["task_instance"]
    pipeline_run_id = task_instance.xcom_pull(
        task_ids="create_pipeline_run",
    )

    if pipeline_run_id is None:
        return

    exception = context.get("exception")
    error_message = (
        str(exception)
        if exception is not None
        else f"Task {task_instance.task_id} failed."
    )
    errors = [
        {
            "type": "pipeline_task_error",
            "task": task_instance.task_id,
            "message": error_message,
        }
    ]

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE pipeline_runs
                SET
                    status = %s,
                    validation_errors = %s,
                    error_message = %s,
                    finished_at = %s,
                    updated_at = now()
                WHERE id = %s;
                """,
                (
                    PIPELINE_STATUS_FAILED,
                    Json(errors),
                    error_message,
                    datetime.now(UTC),
                    pipeline_run_id,
                ),
            )

    print(
        f"Pipeline run {pipeline_run_id} failed "
        f"in task={task_instance.task_id}"
    )


@dag(
    dag_id="process_dataset",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["insightops", "datasets", "day-8"],
)
def process_dataset_dag():
    @task
    def create_pipeline_run(dataset_id: int, airflow_run_id: str) -> int:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO pipeline_runs (
                        status,
                        airflow_run_id,
                        dataset_id,
                        started_at,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        now(),
                        now()
                    )
                    RETURNING id;
                    """,
                    (
                        PIPELINE_STATUS_RUNNING,
                        airflow_run_id,
                        dataset_id,
                        datetime.now(UTC),
                    ),
                )

                pipeline_run_id = cursor.fetchone()[0]

        print(f"Created pipeline_run_id={pipeline_run_id}")

        return pipeline_run_id

    @task(on_failure_callback=mark_pipeline_run_failed)
    def extract(file_path: str) -> list[dict[str, Any]]:
        airflow_file_path = file_path.replace(
            "uploads/",
            "/opt/airflow/uploads/",
            1,
        )

        path = Path(airflow_file_path)

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        if path.suffix.lower() != ".csv":
            raise ValueError("Only CSV files are supported for now.")

        with path.open("r", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        if not rows:
            raise ValueError("CSV file is empty or contains only headers.")

        print(f"Extracted {len(rows)} rows from {path}")

        return rows

    @task(on_failure_callback=mark_pipeline_run_failed)
    def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        errors: list[dict[str, Any]] = []

        headers = set(rows[0].keys())
        missing_columns = REQUIRED_COLUMNS - headers

        if missing_columns:
            result = {
                "is_valid": False,
                "errors": [
                    {
                        "type": "missing_columns",
                        "message": "CSV file is missing required columns.",
                        "columns": sorted(missing_columns),
                    }
                ],
                "rows_count": len(rows),
            }

            print(f"Validation result: {result}")

            return result

        for row_index, row in enumerate(rows, start=2):
            errors.extend(validate_row(row, row_index))

        result = {
            "is_valid": not errors,
            "errors": errors,
            "rows_count": len(rows),
        }

        print(f"Validation result: {result}")

        return result

    @task(on_failure_callback=mark_pipeline_run_failed)
    def finalize_pipeline_run(
        pipeline_run_id: int,
        validation_result: dict[str, Any],
    ) -> None:
        is_valid = validation_result["is_valid"]
        errors = validation_result["errors"]

        status = (
            PIPELINE_STATUS_SUCCESS
            if is_valid
            else PIPELINE_STATUS_FAILED
        )
        error_message = None if is_valid else "Dataset validation failed."

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        validation_errors = %s,
                        error_message = %s,
                        finished_at = %s,
                        updated_at = now()
                    WHERE id = %s;
                    """,
                    (
                        status,
                        Json(errors) if errors else None,
                        error_message,
                        datetime.now(UTC),
                        pipeline_run_id,
                    ),
                )

        print(
            f"Pipeline run {pipeline_run_id} finalized "
            f"with status={status}"
        )

    @task
    def fail_if_invalid(validation_result: dict[str, Any]) -> None:
        if not validation_result["is_valid"]:
            raise AirflowFailException("Dataset validation failed.")

    pipeline_run_id = create_pipeline_run(
        dataset_id="{{ dag_run.conf['dataset_id'] }}",
        airflow_run_id="{{ run_id }}",
    )

    rows = extract("{{ dag_run.conf['file_path'] }}")
    pipeline_run_id >> rows

    validation_result = validate(rows)

    finalize_task = finalize_pipeline_run(
        pipeline_run_id=pipeline_run_id,
        validation_result=validation_result,
    )
    validation_check = fail_if_invalid(validation_result)

    finalize_task >> validation_check


def validate_row(
    row: dict[str, Any],
    row_index: int,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    for column in REQUIRED_COLUMNS:
        if row.get(column) in (None, ""):
            errors.append(
                {
                    "type": "empty_value",
                    "message": "Required value is empty.",
                    "row": row_index,
                    "column": column,
                }
            )

    amount = row.get("amount")

    if amount:
        try:
            float(amount)
        except ValueError:
            errors.append(
                {
                    "type": "invalid_amount",
                    "message": "Amount must be a number.",
                    "row": row_index,
                    "column": "amount",
                    "value": amount,
                }
            )

    status = row.get("status")

    if status and status.lower() not in ALLOWED_STATUSES:
        errors.append(
            {
                "type": "invalid_status",
                "message": "Order status is not supported.",
                "row": row_index,
                "column": "status",
                "value": status,
                "allowed_values": sorted(ALLOWED_STATUSES),
            }
        )

    return errors


process_dataset_dag()
