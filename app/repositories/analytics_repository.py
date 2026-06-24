from clickhouse_connect.driver.client import Client

from app.db.clickhouse import get_clickhouse_client


class AnalyticsRepository:
    def __init__(self, client: Client | None = None) -> None:
        self.client = client or get_clickhouse_client()

    def healthcheck(self) -> int:
        result = self.client.query("SELECT 1")
        return result.result_rows[0][0]

    def create_tables(self) -> None:
        for query in self._get_create_table_queries():
            self.client.command(query)

    def _get_create_table_queries(self) -> list[str]:
        return [
            """
            CREATE TABLE IF NOT EXISTS orders_events (
                project_id UInt64,
                dataset_id UInt64,
                pipeline_run_id UInt64,
                order_id String,
                customer_id String,
                amount Decimal(18, 2),
                status LowCardinality(String),
                created_at DateTime64(3, 'UTC'),
                ingested_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            ORDER BY (
                project_id,
                dataset_id,
                pipeline_run_id,
                created_at,
                order_id
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS daily_revenue (
                project_id UInt64,
                dataset_id UInt64,
                pipeline_run_id UInt64,
                date Date,
                revenue Decimal(18, 2),
                calculated_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            ORDER BY (
                project_id,
                dataset_id,
                date,
                pipeline_run_id
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS failed_payments (
                project_id UInt64,
                dataset_id UInt64,
                pipeline_run_id UInt64,
                failed_count UInt64,
                failed_amount Decimal(18, 2),
                calculated_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            ORDER BY (
                project_id,
                dataset_id,
                pipeline_run_id
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS top_customers (
                project_id UInt64,
                dataset_id UInt64,
                pipeline_run_id UInt64,
                customer_id String,
                revenue Decimal(18, 2),
                calculated_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            ORDER BY (
                project_id,
                dataset_id,
                pipeline_run_id,
                customer_id
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS orders_by_status (
                project_id UInt64,
                dataset_id UInt64,
                pipeline_run_id UInt64,
                status LowCardinality(String),
                orders_count UInt64,
                calculated_at DateTime64(3, 'UTC') DEFAULT now64(3)
            )
            ENGINE = MergeTree
            ORDER BY (
                project_id,
                dataset_id,
                pipeline_run_id,
                status
            )
            """,
        ]
