from typing import Any

from app.repositories.analytics_repository import AnalyticsRepository


def get_daily_revenue_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> list[dict[str, Any]]:
    repository = AnalyticsRepository()

    return repository.get_daily_revenue(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )


def get_orders_by_status_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> list[dict[str, Any]]:
    repository = AnalyticsRepository()

    return repository.get_orders_by_status(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )


def get_failed_payments_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
) -> dict[str, Any]:
    repository = AnalyticsRepository()

    return repository.get_failed_payments(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
    )


def get_top_customers_tool(
    *,
    project_id: int,
    dataset_id: int | None,
    pipeline_run_id: int | None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    repository = AnalyticsRepository()

    return repository.get_top_customers(
        project_id=project_id,
        dataset_id=dataset_id,
        pipeline_run_id=pipeline_run_id,
        limit=limit,
    )
