from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.project_repository import ProjectRepository


class AnalyticsService:
    def __init__(
        self,
        *,
        project_repo: ProjectRepository,
        analytics_repo: AnalyticsRepository,
    ) -> None:
        self.project_repo = project_repo
        self.analytics_repo = analytics_repo

    async def get_daily_revenue(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> list[dict]:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await run_in_threadpool(
            self.analytics_repo.get_daily_revenue,
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

    async def get_orders_by_status(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> list[dict]:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await run_in_threadpool(
            self.analytics_repo.get_orders_by_status,
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

    async def get_failed_payments(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> dict:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await run_in_threadpool(
            self.analytics_repo.get_failed_payments,
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )

    async def get_top_customers(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
        limit: int = 5,
    ) -> list[dict]:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await run_in_threadpool(
            self.analytics_repo.get_top_customers,
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            limit=limit,
        )

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
