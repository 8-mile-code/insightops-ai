from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProjectNotFoundError
from app.models.dataset import Dataset
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.file_storage_service import FileStorageService
from app.services.project_service import ProjectService


class DatasetService:
    def __init__(
        self,
        repo: DatasetRepository,
        project_service: ProjectService,
        file_storage_service: FileStorageService,
    ) -> None:
        self.repo = repo
        self.project_service = project_service
        self.file_storage_service = file_storage_service

    async def create_dataset(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        name: str,
        file_path: str,
        file_content: bytes,
    ) -> Dataset:
        project = await self.project_service.get_user_project(
            db, project_id=project_id, current_user=current_user
        )
        await self.file_storage_service.save_file(
            Path(file_path),
            file_content,
        )

        return await self.repo.create(
            db, name=name, file_path=file_path, project_id=project.id
        )

    async def get_project_datasets(
        self, db: AsyncSession, *, project_id: int, current_user: User
    ) -> list[Dataset]:
        project = await self.project_service.get_user_project(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await self.repo.get_all_by_project(db, project_id=project.id)

    async def get_user_dataset(
        self,
        db: AsyncSession,
        *,
        dataset_id: int,
        current_user: User,
    ) -> Dataset:
        dataset = await self.repo.get_by_id(db, dataset_id)

        if dataset is None:
            raise ProjectNotFoundError

        await self.project_service.get_user_project(
            db,
            project_id=dataset.project_id,
            current_user=current_user,
        )

        return dataset
