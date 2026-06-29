from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.report import Report


class ReportRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        title: str,
        content: str,
        metrics_snapshot: dict[str, Any],
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> Report:
        report = Report(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            title=title,
            content=content,
            metrics_snapshot=metrics_snapshot,
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report

    async def get_all_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> list[Report]:
        result = await db.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self,
        db: AsyncSession,
        *,
        report_id: int,
        owner_id: int,
    ) -> Report | None:
        result = await db.execute(
            select(Report)
            .join(Project)
            .where(
                Report.id == report_id,
                Project.owner_id == owner_id,
            )
        )

        return result.scalar_one_or_none()
