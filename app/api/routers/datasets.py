from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundError
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.dataset import DatasetRead
from app.services.dataset_service import DatasetService
from app.services.dataset_validation_service import DatasetValidationService
from app.services.file_storage_service import FileStorageService
from app.services.project_service import ProjectService

router = APIRouter(tags=["📁 Datasets"])

UPLOAD_DIR = Path("uploads/datasets")
ALLOWED_EXTENSIONS = {".csv", ".json"}


def get_dataset_service() -> DatasetService:
    project_service = ProjectService(repo=ProjectRepository())

    return DatasetService(
        repo=DatasetRepository(),
        project_service=project_service,
        file_storage_service=FileStorageService(),
    )


def get_dataset_validation_service() -> DatasetValidationService:
    return DatasetValidationService(repo=DatasetRepository())


@router.post(
    "/projects/{project_id}/datasets",
    response_model=DatasetRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
    file: UploadFile = File(...),
) -> Dataset:
    file_suffix = Path(file.filename or "").suffix.lower()

    if file_suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and JSON files are supported",
        )

    safe_filename = f"{uuid4()}{file_suffix}"
    file_path = UPLOAD_DIR / safe_filename

    content = await file.read()

    try:
        return await dataset_service.create_dataset(
            db,
            project_id=project_id,
            current_user=current_user,
            name=file.filename or safe_filename,
            file_path=str(file_path),
            file_content=content,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/projects/{project_id}/datasets",
    response_model=list[DatasetRead],
)
async def get_project_datasets(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> list[Dataset]:
    try:
        return await dataset_service.get_project_datasets(
            db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetRead,
)
async def get_dataset(
    dataset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> Dataset:
    try:
        return await dataset_service.get_user_dataset(
            db,
            dataset_id=dataset_id,
            current_user=current_user,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        ) from error


@router.post(
    "/datasets/{dataset_id}/validate",
    response_model=DatasetRead,
)
async def validate_dataset(
    dataset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    dataset_service: Annotated[DatasetService, Depends(get_dataset_service)],
    validation_service: Annotated[
        DatasetValidationService,
        Depends(get_dataset_validation_service),
    ],
) -> Dataset:
    try:
        dataset = await dataset_service.get_user_dataset(
            db,
            dataset_id=dataset_id,
            current_user=current_user,
        )

        return await validation_service.validate_dataset(
            db,
            dataset=dataset,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        ) from error
