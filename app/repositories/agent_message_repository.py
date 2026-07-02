from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_message import AgentMessage


class AgentMessageRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        question: str,
        answer: str,
        used_tools: list[str],
        sources: list[dict[str, Any]],
        dataset_id: int | None = None,
        pipeline_run_id: int | None = None,
    ) -> AgentMessage:
        message = AgentMessage(
            project_id=project_id,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            question=question,
            answer=answer,
            used_tools=used_tools,
            sources=sources,
        )

        db.add(message)
        await db.commit()
        await db.refresh(message)

        return message

    async def get_all_by_project(
        self,
        db: AsyncSession,
        *,
        project_id: int,
    ) -> list[AgentMessage]:
        result = await db.execute(
            select(AgentMessage)
            .where(AgentMessage.project_id == project_id)
            .order_by(AgentMessage.created_at.desc())
        )

        return list(result.scalars().all())
