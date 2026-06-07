from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProjectNotFoundError
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    def __init__(self, repo: ProjectRepository) -> None:
        self.repo = repo

    async def create_project(
        self,
        db: AsyncSession,
        *,
        project_in: ProjectCreate,
        current_user: User,
    ) -> Project:
        return await self.repo.create(
            db,
            owner_id=current_user.id,
            name=project_in.name,
            description=project_in.description,
        )

    async def get_user_projects(
        self,
        db: AsyncSession,
        current_user: User,
    ) -> list[Project]:
        return await self.repo.get_all_by_owner(
            db,
            owner_id=current_user.id,
        )

    async def get_user_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> Project:
        project = await self.repo.get_by_id_and_owner(
            db,
            project_id=project_id,
            owner_id=current_user.id,
        )

        if project is None:
            raise ProjectNotFoundError

        return project

    async def delete_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> None:
        project = await self.get_user_project(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        await self.repo.delete(db, project)
