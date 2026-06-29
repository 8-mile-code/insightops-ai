from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    LLMServiceError,
    ProjectNotFoundError,
    ReportNotFoundError,
)
from app.models.report import Report
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportGenerateRequest
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService


class ReportService:
    def __init__(
        self,
        *,
        report_repo: ReportRepository,
        project_repo: ProjectRepository,
        analytics_service: AnalyticsService,
        llm_service: LLMService,
    ) -> None:
        self.report_repo = report_repo
        self.project_repo = project_repo
        self.analytics_service = analytics_service
        self.llm_service = llm_service

    async def generate_report(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        report_in: ReportGenerateRequest,
    ) -> Report:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        metrics_snapshot = await self._collect_metrics(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=report_in.dataset_id,
            pipeline_run_id=report_in.pipeline_run_id,
        )

        title = self._build_title(
            project_id=project_id,
            pipeline_run_id=report_in.pipeline_run_id,
        )

        content = await self._build_report_content(metrics_snapshot)

        return await self.report_repo.create(
            db,
            project_id=project_id,
            dataset_id=report_in.dataset_id,
            pipeline_run_id=report_in.pipeline_run_id,
            title=title,
            content=content,
            metrics_snapshot=metrics_snapshot,
        )

    async def get_project_reports(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> list[Report]:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await self.report_repo.get_all_by_project(
            db,
            project_id=project_id,
        )

    async def get_report(
        self,
        db: AsyncSession,
        *,
        report_id: int,
        current_user: User,
    ) -> Report:
        report = await self.report_repo.get_by_id_and_owner(
            db,
            report_id=report_id,
            owner_id=current_user.id,
        )

        if report is None:
            raise ReportNotFoundError

        return report

    async def _ensure_project_access(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> None:
        project = await self.project_repo.get_by_id_and_owner(
            db,
            project_id=project_id,
            owner_id=current_user.id,
        )

        if project is None:
            raise ProjectNotFoundError

    async def _collect_metrics(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        dataset_id: int | None,
        pipeline_run_id: int | None,
    ) -> dict[str, Any]:
        daily_revenue = await self.analytics_service.get_daily_revenue(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        orders_by_status = await self.analytics_service.get_orders_by_status(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        failed_payments = await self.analytics_service.get_failed_payments(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
        top_customers = await self.analytics_service.get_top_customers(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            limit=5,
        )

        return {
            "filters": {
                "project_id": project_id,
                "dataset_id": dataset_id,
                "pipeline_run_id": pipeline_run_id,
            },
            "daily_revenue": self._serialize_dates(daily_revenue),
            "orders_by_status": orders_by_status,
            "failed_payments": failed_payments,
            "top_customers": top_customers,
        }

    def _serialize_dates(
        self,
        items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        serialized_items = []

        for item in items:
            serialized_item = item.copy()

            if isinstance(serialized_item.get("date"), date):
                serialized_item["date"] = serialized_item["date"].isoformat()

            serialized_items.append(serialized_item)

        return serialized_items

    def _build_title(
        self,
        *,
        project_id: int,
        pipeline_run_id: int | None,
    ) -> str:
        if pipeline_run_id is not None:
            return (
                f"Analytics report for project {project_id},"
                f" pipeline run {pipeline_run_id}"
            )

        return f"Analytics report for project {project_id}"

    async def _build_report_content(
        self,
        metrics_snapshot: dict[str, Any],
    ) -> str:
        deterministic_summary = self._build_summary(metrics_snapshot)

        try:
            llm_summary = await self.llm_service.generate_report_summary(
                metrics_snapshot,
            )
        except LLMServiceError:
            return deterministic_summary

        return llm_summary

    def _build_summary(
        self,
        metrics: dict[str, Any],
    ) -> str:
        daily_revenue = metrics["daily_revenue"]
        orders_by_status = metrics["orders_by_status"]
        failed_payments = metrics["failed_payments"]
        top_customers = metrics["top_customers"]
        filters = metrics["filters"]

        total_revenue = round(
            sum(item["revenue"] for item in daily_revenue),
            2,
        )
        revenue_days_count = len(daily_revenue)
        total_orders = sum(item["orders_count"] for item in orders_by_status)

        top_status = max(
            orders_by_status,
            key=lambda item: item["orders_count"],
            default=None,
        )
        top_customer = top_customers[0] if top_customers else None

        lines = [
            "Analytical report",
            "",
            f"Project ID: {filters['project_id']}",
            f"Dataset ID: {filters['dataset_id'] or 'all'}",
            f"Pipeline run ID: {filters['pipeline_run_id'] or 'all'}",
            "",
            f"Total revenue: {total_revenue:.2f}",
            f"Revenue days: {revenue_days_count}",
            f"Total orders: {total_orders}",
            (
                "Most frequent order status: "
                f"{top_status['status']} ({top_status['orders_count']} orders)"
                if top_status
                else "Most frequent order status: no data"
            ),
            (
                "Top customer: "
                f"{top_customer['customer_id']} "
                f"with revenue {top_customer['revenue']:.2f}"
                if top_customer
                else "Top customer: no data"
            ),
            (
                "Failed payments: "
                f"{failed_payments['failed_count']} "
                f"with amount {failed_payments['failed_amount']:.2f}"
            ),
        ]

        return "\n".join(lines)
