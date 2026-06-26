from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ProjectNotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.analytics import (
    DailyRevenueItem,
    FailedPaymentsRead,
    OrdersByStatusItem,
    TopCustomerItem,
)
from app.services.analytics_service import AnalyticsService


router = APIRouter(
    prefix="/projects/{project_id}/analytics",
    tags=["📊 Analytics"],
)


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        project_repo=ProjectRepository(),
        analytics_repo=AnalyticsRepository(),
    )


@router.get(
    "/revenue/daily",
    response_model=list[DailyRevenueItem],
)
async def get_daily_revenue(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    analytics_service: Annotated[
        AnalyticsService,
        Depends(get_analytics_service),
    ],
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> list[dict]:
    try:
        return await analytics_service.get_daily_revenue(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/orders/status",
    response_model=list[OrdersByStatusItem],
)
async def get_orders_by_status(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    analytics_service: Annotated[
        AnalyticsService,
        Depends(get_analytics_service),
    ],
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> list[dict]:
    try:
        return await analytics_service.get_orders_by_status(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/payments/failed",
    response_model=FailedPaymentsRead,
)
async def get_failed_payments(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    analytics_service: Annotated[
        AnalyticsService,
        Depends(get_analytics_service),
    ],
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
) -> dict:
    try:
        return await analytics_service.get_failed_payments(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error


@router.get(
    "/customers/top",
    response_model=list[TopCustomerItem],
)
async def get_top_customers(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    analytics_service: Annotated[
        AnalyticsService,
        Depends(get_analytics_service),
    ],
    dataset_id: int | None = None,
    pipeline_run_id: int | None = None,
    limit: int = Query(default=5, ge=1, le=50),
) -> list[dict]:
    try:
        return await analytics_service.get_top_customers(
            db,
            project_id=project_id,
            current_user=current_user,
            dataset_id=dataset_id,
            pipeline_run_id=pipeline_run_id,
            limit=limit,
        )
    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        ) from error
