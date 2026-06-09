from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.project import Project
from app.repositories.dataset_repository import DatasetRepository


class DatasetService:
    def __init__(self, repo: DatasetRepository) -> None:
        self.repo = repo

    async def create_dataset(
        self,
        db: AsyncSession,
        *,
        project: Project,
        name: str,
        file_path: str
    ) -> Dataset:
        return await self.repo.create(
            db,
            name=name,
            file_path=file_path,
            project_id=project.id
        )

    async def get_project_datasets(
            self,
            db: AsyncSession,
            project: Project
    ) -> list[Dataset]:
        return await self.repo.get_all_by_project(db, project_id=project.id)

    async def get_dataset(
            self,
            db: AsyncSession,
            dataset_id: int
    ) -> Dataset | None:
        return await self.repo.get_by_id(db, dataset_id)
