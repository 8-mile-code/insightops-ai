import csv
import os
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import clickhouse_connect  # type: ignore[import-not-found]
import psycopg2  # type: ignore[import-not-found]
from airflow.sdk import dag, task  # type: ignore[import-not-found]
from airflow.sdk.exceptions import (
    AirflowFailException,  # type: ignore[import-not-found]
)
from clickhouse_connect.driver.client import (
    Client,  # type: ignore[import-not-found]
)
from psycopg2.extras import Json  # type: ignore[import-not-found]

from app.domain.orders_etl import (
    build_aggregates as build_order_aggregates,
)
from app.domain.orders_etl import (
    transform_rows,
    validate_rows,
)

PIPELINE_STATUS_RUNNING = "running"
DATASET_STATUS_FAILED = "failed"
DATASET_STATUS_PROCESSED = "processed"
PIPELINE_STATUS_SUCCESS = "success"
PIPELINE_STATUS_FAILED = "failed"


def get_connection():
    return psycopg2.connect(
        host=os.environ["INSIGHTOPS_DB_HOST"],
        port=os.environ["INSIGHTOPS_DB_PORT"],
        user=os.environ["INSIGHTOPS_DB_USER"],
        password=os.environ["INSIGHTOPS_DB_PASSWORD"],
        dbname=os.environ["INSIGHTOPS_DB_NAME"],
    )


def get_clickhouse_client() -> Client:
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ["CLICKHOUSE_PORT"]),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=os.environ["CLICKHOUSE_DB"],
    )


def mark_pipeline_run_failed(context: dict[str, Any]) -> None:
    task_instance = context["task_instance"]
    pipeline_run_id = task_instance.xcom_pull(
        task_ids="initialize_pipeline_run",
    )

    if pipeline_run_id is None:
        dag_run = context.get("dag_run")
        if dag_run is not None:
            pipeline_run_id = dag_run.conf.get("pipeline_run_id")

    if not pipeline_run_id:
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

            cursor.execute(
                """
                UPDATE datasets
                SET
                    status = %s,
                    updated_at = now()
                WHERE id = (
                    SELECT dataset_id
                    FROM pipeline_runs
                    WHERE id = %s
                );
                """,
                (
                    DATASET_STATUS_FAILED,
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
    tags=["insightops", "datasets", "day-9"],
)
def process_dataset_dag():
    @task(on_failure_callback=mark_pipeline_run_failed)
    def initialize_pipeline_run(
        dataset_id: int,
        airflow_run_id: str,
        pipeline_run_id: str,
    ) -> int:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if pipeline_run_id:
                    cursor.execute(
                        """
                        UPDATE pipeline_runs
                        SET
                            status = %s,
                            started_at = %s,
                            updated_at = now()
                        WHERE id = %s AND dataset_id = %s
                        RETURNING id;
                        """,
                        (
                            PIPELINE_STATUS_RUNNING,
                            datetime.now(UTC),
                            int(pipeline_run_id),
                            int(dataset_id),
                        ),
                    )
                else:
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
                        VALUES (%s, %s, %s, %s, now(), now())
                        RETURNING id;
                        """,
                        (
                            PIPELINE_STATUS_RUNNING,
                            airflow_run_id,
                            dataset_id,
                            datetime.now(UTC),
                        ),
                    )

                row = cursor.fetchone()

                if row is None:
                    raise ValueError(
                        "Pipeline run does not match the dataset."
                    )

                initialized_pipeline_run_id = row[0]

        print(f"Initialized pipeline_run_id={initialized_pipeline_run_id}")

        return initialized_pipeline_run_id

    @task(on_failure_callback=mark_pipeline_run_failed)
    def get_dataset_context(dataset_id: int) -> dict[str, Any]:
        dataset_id = int(dataset_id)

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT project_id
                    FROM datasets
                    WHERE id = %s;
                    """,
                    (dataset_id,),
                )

                row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Dataset not found: {dataset_id}")

        return {
            "dataset_id": dataset_id,
            "project_id": row[0],
        }

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

        print(f"Extracted {len(rows)} rows from {path}")

        return rows

    @task(on_failure_callback=mark_pipeline_run_failed)
    def validate(rows: list[dict[str, Any]]) -> dict[str, Any]:
        result = validate_rows(rows)

        print(f"Validation result: {result}")

        return result

    @task(on_failure_callback=mark_pipeline_run_failed)
    def save_validation_failure_if_needed(
        pipeline_run_id: int,
        validation_result: dict[str, Any],
    ) -> None:
        if validation_result["is_valid"]:
            print("Validation passed. Pipeline run is not finalized yet.")
            return

        errors = validation_result["errors"]
        error_message = "Dataset validation failed."

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
                        Json(errors) if errors else None,
                        error_message,
                        datetime.now(UTC),
                        pipeline_run_id,
                    ),
                )

        print(
            f"Pipeline run {pipeline_run_id} marked as failed "
            "because validation failed."
        )

    @task
    def fail_if_invalid(validation_result: dict[str, Any]) -> None:
        if not validation_result["is_valid"]:
            raise AirflowFailException("Dataset validation failed.")

    @task(on_failure_callback=mark_pipeline_run_failed)
    def transform(rows: list[dict[str, Any]]) -> dict[str, Any]:
        result = transform_rows(rows)

        print(f"Transformed {result['rows_count']} rows")

        return result

    @task(on_failure_callback=mark_pipeline_run_failed)
    def build_aggregates(
        transform_result: dict[str, Any],
    ) -> dict[str, Any]:
        result = build_order_aggregates(
            transform_result["transformed_rows"],
        )

        print(f"Aggregates result: {result}")

        return result

    @task(on_failure_callback=mark_pipeline_run_failed)
    def load_to_clickhouse(
        pipeline_run_id: int,
        dataset_context: dict[str, Any],
        transform_result: dict[str, Any],
        aggregate_result: dict[str, Any],
    ) -> dict[str, Any]:
        client = get_clickhouse_client()

        project_id = int(dataset_context["project_id"])
        dataset_id = int(dataset_context["dataset_id"])
        pipeline_run_id = int(pipeline_run_id)

        transformed_rows = transform_result["transformed_rows"]

        orders_events_rows = [
            (
                project_id,
                dataset_id,
                pipeline_run_id,
                row["order_id"],
                row["customer_id"],
                Decimal(str(row["amount"])),
                row["status"],
                datetime.fromisoformat(row["created_at"]),
            )
            for row in transformed_rows
        ]

        if orders_events_rows:
            client.insert(
                "orders_events",
                orders_events_rows,
                column_names=[
                    "project_id",
                    "dataset_id",
                    "pipeline_run_id",
                    "order_id",
                    "customer_id",
                    "amount",
                    "status",
                    "created_at",
                ],
            )

        daily_revenue_rows = [
            (
                project_id,
                dataset_id,
                pipeline_run_id,
                date.fromisoformat(item["date"]),
                Decimal(str(item["revenue"])),
            )
            for item in aggregate_result["daily_revenue"]
        ]

        if daily_revenue_rows:
            client.insert(
                "daily_revenue",
                daily_revenue_rows,
                column_names=[
                    "project_id",
                    "dataset_id",
                    "pipeline_run_id",
                    "date",
                    "revenue",
                ],
            )

        failed_payments = aggregate_result["failed_payments"]

        client.insert(
            "failed_payments",
            [
                (
                    project_id,
                    dataset_id,
                    pipeline_run_id,
                    int(failed_payments["count"]),
                    Decimal(str(failed_payments["amount"])),
                )
            ],
            column_names=[
                "project_id",
                "dataset_id",
                "pipeline_run_id",
                "failed_count",
                "failed_amount",
            ],
        )

        top_customers_rows = [
            (
                project_id,
                dataset_id,
                pipeline_run_id,
                item["customer_id"],
                Decimal(str(item["revenue"])),
            )
            for item in aggregate_result["top_customers"]
        ]

        if top_customers_rows:
            client.insert(
                "top_customers",
                top_customers_rows,
                column_names=[
                    "project_id",
                    "dataset_id",
                    "pipeline_run_id",
                    "customer_id",
                    "revenue",
                ],
            )

        orders_by_status_rows = [
            (
                project_id,
                dataset_id,
                pipeline_run_id,
                status,
                int(orders_count),
            )
            for status, orders_count in aggregate_result[
                "orders_by_status"
            ].items()
        ]

        if orders_by_status_rows:
            client.insert(
                "orders_by_status",
                orders_by_status_rows,
                column_names=[
                    "project_id",
                    "dataset_id",
                    "pipeline_run_id",
                    "status",
                    "orders_count",
                ],
            )

        result = {
            "rows_count": len(orders_events_rows),
            "orders_events_count": len(orders_events_rows),
            "daily_revenue_count": len(daily_revenue_rows),
            "failed_payments_count": 1,
            "top_customers_count": len(top_customers_rows),
            "orders_by_status_count": len(orders_by_status_rows),
        }

        print(f"Loaded data to ClickHouse: {result}")

        return result

    @task(on_failure_callback=mark_pipeline_run_failed)
    def finalize_pipeline_run_success(
        pipeline_run_id: int,
        load_result: dict[str, Any],
    ) -> None:
        rows_count = load_result["rows_count"]

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        validation_errors = NULL,
                        error_message = NULL,
                        finished_at = %s,
                        updated_at = now()
                    WHERE id = %s;
                    """,
                    (
                        PIPELINE_STATUS_SUCCESS,
                        datetime.now(UTC),
                        pipeline_run_id,
                    ),
                )

                cursor.execute(
                    """
                    UPDATE datasets
                    SET
                        status = %s,
                        updated_at = now()
                    WHERE id = (
                        SELECT dataset_id
                        FROM pipeline_runs
                        WHERE id = %s
                    );
                    """,
                    (
                        DATASET_STATUS_PROCESSED,
                        pipeline_run_id,
                    ),
                )

        print(
            f"Pipeline run {pipeline_run_id} finalized with "
            f"status={PIPELINE_STATUS_SUCCESS}. "
            f"Transformed rows: {rows_count}. "
            "ClickHouse load completed successfully."
        )

    dataset_id = "{{ dag_run.conf['dataset_id'] }}"

    pipeline_run_id = initialize_pipeline_run(
        dataset_id=dataset_id,
        airflow_run_id="{{ run_id }}",
        pipeline_run_id=("{{ dag_run.conf.get('pipeline_run_id', '') }}"),
    )

    dataset_context = get_dataset_context(dataset_id)
    pipeline_run_id >> dataset_context

    rows = extract("{{ dag_run.conf['file_path'] }}")
    pipeline_run_id >> rows

    validation_result = validate(rows)

    validation_failure_save = save_validation_failure_if_needed(
        pipeline_run_id=pipeline_run_id,
        validation_result=validation_result,
    )
    validation_check = fail_if_invalid(validation_result)

    validation_failure_save >> validation_check

    transform_result = transform(rows)
    validation_check >> transform_result

    aggregate_result = build_aggregates(transform_result)

    load_result = load_to_clickhouse(
        pipeline_run_id=pipeline_run_id,
        dataset_context=dataset_context,
        transform_result=transform_result,
        aggregate_result=aggregate_result,
    )

    finalize_pipeline_run_success(
        pipeline_run_id=pipeline_run_id,
        load_result=load_result,
    )


process_dataset_dag()
