from typing import Any

from mcp.server.fastmcp import FastMCP

from app.repositories.analytics_repository import AnalyticsRepository

mcp = FastMCP(
    "InsightOps Analytics MCP",
    json_response=True,
)


def _build_clickhouse_source(
    *,
    table: str,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> dict[str, Any]:
    return {
        "type": "clickhouse_table",
        "name": table,
        "project_id": project_id,
        "dataset_id": dataset_id,
        "pipeline_run_id": pipeline_run_id,
    }


def _get_repository() -> AnalyticsRepository:
    return AnalyticsRepository()


@mcp.tool()
def get_daily_revenue(
    project_id: int,
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> dict[str, Any]:
    """Get daily revenue analytics from ClickHouse."""
    repository = _get_repository()

    data = repository.get_daily_revenue(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )

    return {
        "tool": "get_daily_revenue",
        "data": data,
        "sources": [
            _build_clickhouse_source(
                table="daily_revenue",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=pipeline_run_id,
            )
        ],
        "metadata": {
            "rows_count": len(data),
        },
    }


@mcp.tool()
def get_failed_payments(
    project_id: int,
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> dict[str, Any]:
    """Get failed payments analytics from ClickHouse."""
    repository = _get_repository()

    data = repository.get_failed_payments(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )

    return {
        "tool": "get_failed_payments",
        "data": data,
        "sources": [
            _build_clickhouse_source(
                table="failed_payments",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=pipeline_run_id,
            )
        ],
        "metadata": {
            "rows_count": 1,
            "result_type": "aggregate",
        },
    }


@mcp.tool()
def get_top_customers(
    project_id: int,
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Get top customers by revenue from ClickHouse."""
    repository = _get_repository()

    data = repository.get_top_customers(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
        limit=limit,
    )

    return {
        "tool": "get_top_customers",
        "data": data,
        "sources": [
            _build_clickhouse_source(
                table="top_customers",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=pipeline_run_id,
            )
        ],
        "metadata": {
            "rows_count": len(data),
            "limit": limit,
        },
    }


@mcp.tool()
def get_pipeline_status(
    pipeline_run_id: int,
) -> dict[str, Any]:
    """Get the status of a pipeline run."""
    return {
        "tool": "get_pipeline_status",
        "data": {
            "pipeline_run_id": pipeline_run_id,
            "status": "not_implemented",
            "message": (
                "Pipeline status tool is registered. "
                "PostgreSQL-backed implementation will be added next."
            ),
        },
        "sources": [
            {
                "type": "postgres_table",
                "name": "pipeline_runs",
                "pipeline_run_id": pipeline_run_id,
            }
        ],
        "metadata": {},
    }


if __name__ == "__main__":
    mcp.run()
