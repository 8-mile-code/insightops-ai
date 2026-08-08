from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.agent_message import AgentMessage
from app.models.user import User
from app.repositories.agent_message_repository import AgentMessageRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.agent import AgentMessageRead, AskRequest, AskResponse
from app.services.agent_service import AgentService
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/projects/{project_id}/agent",
    tags=["🤖 Agent"],
)


def get_agent_service() -> AgentService:
    project_repo = ProjectRepository()
    project_service = ProjectService(repo=project_repo)

    analytics_service = AnalyticsService(
        project_service=project_service,
        analytics_repo=AnalyticsRepository(),
    )

    report_service = ReportService(
        report_repo=ReportRepository(),
        project_service=project_service,
        analytics_service=analytics_service,
        llm_service=LLMService(),
    )

    return AgentService(
        project_service=project_service,
        message_repo=AgentMessageRepository(),
        report_service=report_service,
    )


@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ask_agent(
    project_id: int,
    ask_in: AskRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> AgentMessage:
    return await agent_service.ask(
        db,
        project_id=project_id,
        current_user=current_user,
        ask_in=ask_in,
    )


@router.get(
    "/messages",
    response_model=list[AgentMessageRead],
)
async def get_agent_messages(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> list[AgentMessage]:
    return await agent_service.get_project_messages(
        db,
        project_id=project_id,
        current_user=current_user,
    )
