from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundError, ReportNotFoundError
from app.db.session import get_db
from app.models.report import Report
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportGenerateRequest, ReportRead
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService


router = APIRouter(tags=["📋 Reports"])


def get_report_service() -> ReportService:
    project_repo = ProjectRepository()

    analytics_service = AnalyticsService(
        project_repo=project_repo,
        analytics_repo=AnalyticsRepository(),
    )

    return ReportService(
        report_repo=ReportRepository(),
        project_repo=project_repo,
        analytics_service=analytics_service,
    )


@router.post(
    "/projects/{project_id}/reports/generate",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    project_id: int,
    report_in: ReportGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[
        ReportService,
        Depends(get_report_service),
    ],
) -> Report:
    try:
        return await report_service.generate_report(
            db,
            project_id=project_id,
            current_user=current_user,
            report_in=report_in,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/projects/{project_id}/reports",
    response_model=list[ReportRead],
)
async def get_project_reports(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[
        ReportService,
        Depends(get_report_service),
    ],
) -> list[Report]:
    try:
        return await report_service.get_project_reports(
            db,
            project_id=project_id,
            current_user=current_user,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/reports/{report_id}",
    response_model=ReportRead,
)
async def get_report(
    report_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    report_service: Annotated[
        ReportService,
        Depends(get_report_service),
    ],
) -> Report:
    try:
        return await report_service.get_report(
            db,
            report_id=report_id,
            current_user=current_user,
        )
    except ReportNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        ) from error
