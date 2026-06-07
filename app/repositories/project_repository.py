from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        owner_id: int,
        name: str,
        description: str | None,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            name=name,
            description=description,
        )

        db.add(project)
        await db.commit()
        await db.refresh(project)

        return project

    async def get_by_id(
        self,
        db: AsyncSession,
        project_id: int,
    ) -> Project | None:
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_owner(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        owner_id: int,
    ) -> Project | None:
        result = await db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_owner(
        self,
        db: AsyncSession,
        owner_id: int,
    ) -> list[Project]:
        result = await db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(
        self,
        db: AsyncSession,
        project: Project,
    ) -> None:
        await db.delete(project)
        await db.commit()
