from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.services.project_service import ProjectService


async def test_daily_revenue_checks_access_and_delegates_query() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    project_service.get_user_project.return_value = SimpleNamespace(id=11)
    analytics_repo = Mock()
    analytics_repo.get_daily_revenue.return_value = [
        {"date": "2026-01-01", "revenue": 125.5}
    ]
    service = AnalyticsService(
        project_service=project_service,
        analytics_repo=analytics_repo,
    )

    result = await service.get_daily_revenue(
        db,
        project_id=11,
        current_user=current_user,
        dataset_id=12,
        pipeline_run_id=13,
    )

    assert result == [{"date": "2026-01-01", "revenue": 125.5}]
    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=11,
        current_user=current_user,
    )
    analytics_repo.get_daily_revenue.assert_called_once_with(
        project_id=11,
        dataset_id=12,
        pipeline_run_id=13,
    )


async def test_analytics_query_rejects_inaccessible_project() -> None:
    db = AsyncMock()
    current_user = User(
        id=7,
        email="owner@example.com",
        hashed_password="hashed",
    )
    project_service = AsyncMock(spec=ProjectService)
    project_service.get_user_project.side_effect = ProjectNotFoundError
    analytics_repo = Mock()
    service = AnalyticsService(
        project_service=project_service,
        analytics_repo=analytics_repo,
    )

    with pytest.raises(ProjectNotFoundError):
        await service.get_daily_revenue(
            db,
            project_id=999,
            current_user=current_user,
        )
    project_service.get_user_project.assert_awaited_once_with(
        db,
        project_id=999,
        current_user=current_user,
    )

    analytics_repo.get_daily_revenue.assert_not_called()
