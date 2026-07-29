from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["📁 Projects"])


def get_project_service() -> ProjectService:
    return ProjectService(repo=ProjectRepository())


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_in: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[
        ProjectService,
        Depends(get_project_service),
    ],
) -> Project:
    return await project_service.create_project(
        db,
        project_in=project_in,
        current_user=current_user,
    )


@router.get("", response_model=list[ProjectRead])
async def get_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[
        ProjectService,
        Depends(get_project_service),
    ],
) -> list[Project]:
    return await project_service.get_user_projects(
        db,
        current_user=current_user,
    )


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[
        ProjectService,
        Depends(get_project_service),
    ],
) -> Project:
    return await project_service.get_user_project(
        db,
        project_id=project_id,
        current_user=current_user,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[
        ProjectService,
        Depends(get_project_service),
    ],
) -> Response:
    await project_service.delete_project(
        db,
        project_id=project_id,
        current_user=current_user,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
