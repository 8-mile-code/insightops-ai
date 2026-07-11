from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.analytics_graph import build_analytics_agent
from app.core.exceptions import ProjectNotFoundError
from app.models.agent_message import AgentMessage
from app.models.user import User
from app.repositories.agent_message_repository import AgentMessageRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.agent import AskRequest


class AgentService:
    def __init__(
        self,
        *,
        project_repo: ProjectRepository,
        message_repo: AgentMessageRepository,
    ) -> None:
        self.project_repo = project_repo
        self.message_repo = message_repo

    async def ask(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
        ask_in: AskRequest,
    ) -> AgentMessage:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        agent_result = await self._run_agent(
            project_id=project_id,
            ask_in=ask_in,
        )

        return await self.message_repo.create(
            db,
            project_id=project_id,
            dataset_id=ask_in.dataset_id,
            pipeline_run_id=ask_in.pipeline_run_id,
            question=ask_in.question,
            answer=agent_result["answer"],
            used_tools=agent_result.get("used_tools", []),
            sources=agent_result.get("sources", []),
        )

    async def get_project_messages(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> list[AgentMessage]:
        await self._ensure_project_access(
            db,
            project_id=project_id,
            current_user=current_user,
        )

        return await self.message_repo.get_all_by_project(
            db,
            project_id=project_id,
        )

    async def _run_agent(
        self,
        *,
        project_id: int,
        ask_in: AskRequest,
    ) -> dict[str, Any]:
        agent = build_analytics_agent()

        initial_state = {
            "question": ask_in.question,
            "project_id": project_id,
            "dataset_id": ask_in.dataset_id,
            "pipeline_run_id": ask_in.pipeline_run_id,
            "compare_pipeline_run_id": ask_in.compare_pipeline_run_id,
            "action": "unknown",
            "tool_result": None,
            "used_tools": [],
            "sources": [],
            "answer": "",
        }

        return await agent.ainvoke(initial_state)

    async def _ensure_project_access(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        current_user: User,
    ) -> None:
        project = await self.project_repo.get_by_id_and_owner(
            db,
            project_id=project_id,
            owner_id=current_user.id,
        )

        if project is None:
            raise ProjectNotFoundError
