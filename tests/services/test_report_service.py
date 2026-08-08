from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.repositories.report_repository import ReportRepository
from app.services.analytics_service import AnalyticsService
from app.services.llm_service import LLMService
from app.services.project_service import ProjectService
from app.services.report_service import ReportService


async def test_get_project_reports_checks_access() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    report_repo = AsyncMock(spec=ReportRepository)
    report_repo.get_all_by_project.return_value = []

    service = ReportService(
        report_repo=report_repo,
        project_service=project_service,
        analytics_service=AsyncMock(spec=AnalyticsService),
        llm_service=AsyncMock(spec=LLMService),
    )

    result = await service.get_project_reports(
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
    report_repo.get_all_by_project.assert_awaited_once_with(
        db,
        project_id=5,
    )


async def test_get_project_reports_rejects_inaccessible_project() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    project_service.get_user_project.side_effect = ProjectNotFoundError
    report_repo = AsyncMock(spec=ReportRepository)

    service = ReportService(
        report_repo=report_repo,
        project_service=project_service,
        analytics_service=AsyncMock(spec=AnalyticsService),
        llm_service=AsyncMock(spec=LLMService),
    )

    with pytest.raises(ProjectNotFoundError):
        await service.get_project_reports(
            db,
            project_id=999,
            current_user=current_user,
        )

    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=999,
        current_user=current_user,
    )
    report_repo.get_all_by_project.assert_not_awaited()
