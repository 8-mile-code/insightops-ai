from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundError
from app.db.session import get_db
from app.models.agent_message import AgentMessage
from app.models.user import User
from app.repositories.agent_message_repository import AgentMessageRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.agent import AgentMessageRead, AskRequest, AskResponse
from app.services.agent_service import AgentService


router = APIRouter(
    prefix="/projects/{project_id}/agent",
    tags=["🤖 Agent"],
)


def get_agent_service() -> AgentService:
    return AgentService(
        project_repo=ProjectRepository(),
        message_repo=AgentMessageRepository(),
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
    try:
        return await agent_service.ask(
            db,
            project_id=project_id,
            current_user=current_user,
            ask_in=ask_in,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


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
    try:
        return await agent_service.get_project_messages(
            db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error
