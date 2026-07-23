from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.services.dataset_service import DatasetService


async def test_create_dataset_saves_file_and_creates_record() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project = SimpleNamespace(id=11)
    dataset = SimpleNamespace(id=13, project_id=project.id)
    repo = AsyncMock()
    repo.create.return_value = dataset
    project_service = AsyncMock()
    project_service.get_user_project.return_value = project
    file_storage_service = AsyncMock()
    service = DatasetService(
        repo=repo,
        project_service=project_service,
        file_storage_service=file_storage_service,
    )

    result = await service.create_dataset(
        db,
        project_id=project.id,
        current_user=current_user,
        name="orders.csv",
        file_path="uploads/datasets/orders.csv",
        file_content=b"csv-content",
    )

    assert result is dataset
    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=project.id,
        current_user=current_user,
    )
    file_storage_service.save_file.assert_awaited_once()
    repo.create.assert_awaited_once_with(
        db,
        name="orders.csv",
        file_path="uploads/datasets/orders.csv",
        project_id=project.id,
    )


async def test_get_missing_dataset_raises_not_found() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    project_service = AsyncMock()
    file_storage_service = AsyncMock()
    service = DatasetService(
        repo=repo,
        project_service=project_service,
        file_storage_service=file_storage_service,
    )

    with pytest.raises(ProjectNotFoundError):
        await service.get_user_dataset(
            db,
            dataset_id=999,
            current_user=current_user,
        )

    project_service.get_user_project.assert_not_awaited()
