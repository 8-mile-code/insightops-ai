from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.repositories.agent_message_repository import AgentMessageRepository
from app.schemas.agent import AskRequest
from app.services.agent_service import AgentService
from app.services.project_service import ProjectService
from app.services.report_service import ReportService


async def test_get_project_messages_checks_access() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    message_repo = AsyncMock(spec=AgentMessageRepository)
    message_repo.get_all_by_project.return_value = []

    service = AgentService(
        project_service=project_service,
        message_repo=message_repo,
        report_service=AsyncMock(spec=ReportService),
    )

    result = await service.get_project_messages(
        db,
        project_id=5,
        current_user=current_user,
    )

    assert result == []
    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=5,
        current_user=current_user,
    )
    message_repo.get_all_by_project.assert_awaited_once_with(
        db,
        project_id=5,
    )


async def test_ask_rejects_inaccessible_project() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    project_service.get_user_project.side_effect = ProjectNotFoundError
    message_repo = AsyncMock(spec=AgentMessageRepository)

    service = AgentService(
        project_service=project_service,
        message_repo=message_repo,
        report_service=AsyncMock(spec=ReportService),
    )

    with pytest.raises(ProjectNotFoundError):
        await service.ask(
            db,
            project_id=999,
            current_user=current_user,
            ask_in=AskRequest(question="Show revenue"),
        )

    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=999,
        current_user=current_user,
    )
    message_repo.create.assert_not_awaited()
