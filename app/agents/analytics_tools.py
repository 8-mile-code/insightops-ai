from typing import Any

from app.agents.tool_result import ToolResult
from app.repositories.analytics_repository import AnalyticsRepository


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


def get_daily_revenue_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> ToolResult:
    repository = AnalyticsRepository()

    data = repository.get_daily_revenue(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )

    return {
        "tool_name": "get_daily_revenue_tool",
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


def get_orders_by_status_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> ToolResult:
    repository = AnalyticsRepository()

    data = repository.get_orders_by_status(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )

    return {
        "tool_name": "get_orders_by_status_tool",
        "data": data,
        "sources": [
            _build_clickhouse_source(
                table="orders_by_status",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=pipeline_run_id,
            )
        ],
        "metadata": {
            "rows_count": len(data),
        },
    }


def get_failed_payments_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> ToolResult:
    repository = AnalyticsRepository()

    data = repository.get_failed_payments(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )

    return {
        "tool_name": "get_failed_payments_tool",
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


def get_top_customers_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
    limit: int = 5,
) -> ToolResult:
    repository = AnalyticsRepository()

    data = repository.get_top_customers(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
        limit=limit,
    )

    return {
        "tool_name": "get_top_customers_tool",
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
        },
    }


def compare_periods_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int,
    compare_pipeline_run_id: int,
) -> ToolResult:
    repository = AnalyticsRepository()

    current_revenue = repository.get_daily_revenue(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )
    previous_revenue = repository.get_daily_revenue(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=compare_pipeline_run_id,
    )

    current_total = round(
        sum(float(item["revenue"]) for item in current_revenue),
        2,
    )
    previous_total = round(
        sum(float(item["revenue"]) for item in previous_revenue),
        2,
    )
    diff = round(current_total - previous_total, 2)

    if previous_total:
        diff_percent = round((diff / previous_total) * 100, 2)
    else:
        diff_percent = None

    data = {
        "current_pipeline_run_id": pipeline_run_id,
        "compare_pipeline_run_id": compare_pipeline_run_id,
        "current_total_revenue": current_total,
        "previous_total_revenue": previous_total,
        "difference": diff,
        "difference_percent": diff_percent,
    }

    return {
        "tool_name": "compare_periods_tool",
        "data": data,
        "sources": [
            _build_clickhouse_source(
                table="daily_revenue",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=pipeline_run_id,
            ),
            _build_clickhouse_source(
                table="daily_revenue",
                project_id=project_id,
                dataset_id=dataset_id,
                pipeline_run_id=compare_pipeline_run_id,
            ),
        ],
        "metadata": {},
    }


def generate_report_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> ToolResult:
    daily_revenue = get_daily_revenue_tool(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )
    orders_by_status = get_orders_by_status_tool(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )
    failed_payments = get_failed_payments_tool(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )
    top_customers = get_top_customers_tool(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
        limit=5,
    )

    total_revenue = round(
        sum(float(item["revenue"]) for item in daily_revenue["data"]),
        2,
    )
    total_orders = sum(
        int(item["orders_count"]) for item in orders_by_status["data"]
    )

    data = {
        "summary": (
            f"Total revenue is {total_revenue:.2f}. "
            f"Total orders count is {total_orders}. "
            f"Failed payments count is "
            f"{failed_payments['data']['failed_count']}."
        ),
        "metrics": {
            "daily_revenue": daily_revenue["data"],
            "orders_by_status": orders_by_status["data"],
            "failed_payments": failed_payments["data"],
            "top_customers": top_customers["data"],
        },
    }

    return {
        "tool_name": "generate_report_tool",
        "data": data,
        "sources": (
            daily_revenue["sources"]
            + orders_by_status["sources"]
            + failed_payments["sources"]
            + top_customers["sources"]
        ),
        "metadata": {
            "composed_from_tools": [
                daily_revenue["tool_name"],
                orders_by_status["tool_name"],
                failed_payments["tool_name"],
                top_customers["tool_name"],
            ]
        },
    }
