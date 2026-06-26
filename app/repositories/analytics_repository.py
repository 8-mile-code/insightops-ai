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

    def get_daily_revenue(
        self,
        *,
        project_id: int,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> list[dict[str, object]]:
        where_clause, parameters = self._build_filters(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

        result = self.client.query(
            f"""
            SELECT
                date,
                sum(revenue) AS revenue
            FROM daily_revenue
            WHERE {where_clause}
            GROUP BY date
            ORDER BY date
            """,
            parameters=parameters,
        )

        return [
            {
                "date": row[0],
                "revenue": round(float(row[1]), 2),
            }
            for row in result.result_rows
        ]

    def get_orders_by_status(
        self,
        *,
        project_id: int,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> list[dict]:
        where_clause, parameters = self._build_filters(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

        result = self.client.query(
            f"""
            SELECT
                status,
                sum(orders_count) AS orders_count
            FROM orders_by_status
            WHERE {where_clause}
            GROUP BY status
            ORDER BY status
            """,
            parameters=parameters,
        )

        return [
            {
                "status": row[0],
                "orders_count": int(row[1]),
            }
            for row in result.result_rows
        ]

    def get_failed_payments(
        self,
        *,
        project_id: int,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> dict:
        where_clause, parameters = self._build_filters(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

        result = self.client.query(
            f"""
            SELECT
                sum(failed_count) AS failed_count,
                sum(failed_amount) AS failed_amount
            FROM failed_payments
            WHERE {where_clause}
            """,
            parameters=parameters,
        )

        row = result.result_rows[0]

        return {
            "failed_count": int(row[0] or 0),
            "failed_amount": round(float(row[1] or 0), 2),
        }

    def get_top_customers(
        self,
        *,
        project_id: int,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
        limit: int = 5,
    ) -> list[dict]:
        where_clause, parameters = self._build_filters(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        parameters["limit"] = limit

        result = self.client.query(
            f"""
            SELECT
                customer_id,
                sum(revenue) AS revenue
            FROM top_customers
            WHERE {where_clause}
            GROUP BY customer_id
            ORDER BY revenue DESC
            LIMIT {{limit: UInt32}}
            """,
            parameters=parameters,
        )

        return [
            {
                "customer_id": row[0],
                "revenue": round(float(row[1]), 2),
            }
            for row in result.result_rows
        ]

    def _build_filters(
        self,
        *,
        project_id: int,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> tuple[str, dict]:
        where_parts = ["project_id = {project_id: UInt64}"]
        parameters = {"project_id": project_id}

        if dataset_id is not None:
            where_parts.append("dataset_id = {dataset_id: UInt64}")
            parameters["dataset_id"] = dataset_id

        if pipeline_run_id is not None:
            where_parts.append("pipeline_run_id = {pipeline_run_id: UInt64}")
            parameters["pipeline_run_id"] = pipeline_run_id

        return " AND ".join(where_parts), parameters

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
