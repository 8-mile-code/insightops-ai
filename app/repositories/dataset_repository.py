from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.enums import DatasetStatus


class DatasetRepository:
    async def create(
            self,
            db: AsyncSession,
            *,
            name: str,
            file_path: str,
            project_id: int
    ) -> Dataset:
        dataset = Dataset(
            name=name, file_path=file_path, project_id=project_id
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)
        return dataset

    async def get_by_id(
            self, db: AsyncSession, dataset_id: int
    ) -> Dataset | None:
        result = await db.execute(
            select(Dataset).where(Dataset.id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def get_all_by_project(
            self,
            db: AsyncSession,
            project_id: int
    ) -> list[Dataset]:
        result = await db.execute(
            select(Dataset).where(
                Dataset.project_id == project_id
            ).order_by(Dataset.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_validation_result(
            self,
            db: AsyncSession,
            *,
            dataset: Dataset,
            status: DatasetStatus,
            validation_errors: list[dict] | None
    ) -> Dataset:
        dataset.status = status
        dataset.validation_errors = validation_errors
        dataset.validated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(dataset)
        return dataset
