from typing import Any

from mcp.server.fastmcp import FastMCP

from app.db.session import AsyncSessionLocal
from app.models.enums import PipelineRunStatus
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository

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
async def get_pipeline_status(
    project_id: int,
    pipeline_run_id: int,
) -> dict[str, Any]:
    """Get the status of a pipeline run."""
    async with AsyncSessionLocal() as session:
        pipeline_run = await PipelineRunRepository().get_by_id_and_project(
            session,
            pipeline_run_id=pipeline_run_id,
            project_id=project_id,
        )

    if pipeline_run is None:
        return {
            "tool": "get_pipeline_status",
            "data": {
                "pipeline_run_id": pipeline_run_id,
                "status": "not_found",
                "message": "Pipeline run not found in this project.",
            },
            "sources": [],
            "metadata": {"found": False},
        }

    message = pipeline_run.error_message
    if message is None:
        if pipeline_run.status == PipelineRunStatus.SUCCESS:
            message = "Pipeline run completed successfully."
        else:
            message = "Pipeline run is still in progress."

    return {
        "tool": "get_pipeline_status",
        "data": {
            "pipeline_run_id": pipeline_run_id,
            "dataset_id": pipeline_run.dataset_id,
            "status": pipeline_run.status.value,
            "message": message,
            "started_at": (
                pipeline_run.started_at.isoformat()
                if pipeline_run.started_at is not None
                else None
            ),
            "finished_at": (
                pipeline_run.finished_at.isoformat()
                if pipeline_run.finished_at is not None
                else None
            ),
        },
        "sources": [
            {
                "type": "postgres_table",
                "name": "pipeline_runs",
                "project_id": project_id,
                "pipeline_run_id": pipeline_run_id,
            }
        ],
        "metadata": {"found": True},
    }


if __name__ == "__main__":
    mcp.run()
