from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.routers.datasets import get_dataset_service
from app.clients.airflow_client import AirflowClient

from app.db.session import get_db
from app.models.pipeline_run import PipelineRun
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository
from app.schemas.pipeline_run import PipelineRunRead, PipelineRunTriggered
from app.services.pipeline_run_service import PipelineRunService


router = APIRouter(tags=["⚙️ Pipeline runs"])


def get_pipeline_run_service() -> PipelineRunService:
    return PipelineRunService(
        pipeline_run_repo=PipelineRunRepository(),
        dataset_repo=DatasetRepository(),
        dataset_service=get_dataset_service(),
        airflow_client=AirflowClient(),
    )


@router.post(
    "/datasets/{dataset_id}/process",
    response_model=PipelineRunTriggered,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_dataset(
    dataset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pipeline_service: Annotated[
        PipelineRunService,
        Depends(get_pipeline_run_service),
    ],
) -> PipelineRunTriggered:
    return await pipeline_service.start_dataset_processing(
        db,
        dataset_id=dataset_id,
        current_user=current_user,
    )


@router.get(
    "/datasets/{dataset_id}/pipeline-runs",
    response_model=list[PipelineRunRead],
)
async def get_dataset_pipeline_runs(
    dataset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pipeline_service: Annotated[
        PipelineRunService,
        Depends(get_pipeline_run_service),
    ],
) -> list[PipelineRun]:
    return await pipeline_service.get_dataset_pipeline_runs(
        db,
        dataset_id=dataset_id,
        current_user=current_user,
    )


@router.get(
    "/pipeline-runs/{pipeline_run_id}",
    response_model=PipelineRunRead,
)
async def get_pipeline_run(
    pipeline_run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    pipeline_service: Annotated[
        PipelineRunService,
        Depends(get_pipeline_run_service),
    ],
) -> PipelineRun:
    return await pipeline_service.get_pipeline_run(
        db,
        pipeline_run_id=pipeline_run_id,
        current_user=current_user,
    )
