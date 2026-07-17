from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.enums import PipelineRunStatus
from app.models.pipeline_run import PipelineRun
from app.models.project import Project


class PipelineRunRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        dataset_id: int,
        airflow_run_id: str,
    ) -> PipelineRun:
        pipeline_run = PipelineRun(
            dataset_id=dataset_id,
            airflow_run_id=airflow_run_id,
            status=PipelineRunStatus.RUNNING,
        )

        db.add(pipeline_run)
        await db.commit()
        await db.refresh(pipeline_run)
        return pipeline_run

    async def mark_failed(
        self,
        db: AsyncSession,
        *,
        pipeline_run: PipelineRun,
        error_message: str,
    ) -> PipelineRun:
        pipeline_run.status = PipelineRunStatus.FAILED
        pipeline_run.error_message = error_message
        pipeline_run.finished_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(pipeline_run)
        return pipeline_run

    async def get_all_by_dataset(
        self,
        db: AsyncSession,
        *,
        dataset_id: int,
    ) -> list[PipelineRun]:
        result = await db.execute(
            select(PipelineRun)
            .where(PipelineRun.dataset_id == dataset_id)
            .order_by(PipelineRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_owner(
        self,
        db: AsyncSession,
        *,
        pipeline_run_id: int,
        owner_id: int,
    ) -> PipelineRun | None:
        result = await db.execute(
            select(PipelineRun)
            .join(Dataset, PipelineRun.dataset_id == Dataset.id)
            .join(Project, Dataset.project_id == Project.id)
            .where(
                PipelineRun.id == pipeline_run_id,
                Project.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_project(
        self,
        db: AsyncSession,
        *,
        pipeline_run_id: int,
        project_id: int,
    ) -> PipelineRun | None:
        result = await db.execute(
            select(PipelineRun)
            .join(Dataset, PipelineRun.dataset_id == Dataset.id)
            .where(
                PipelineRun.id == pipeline_run_id,
                Dataset.project_id == project_id,
            )
        )
        return result.scalar_one_or_none()
