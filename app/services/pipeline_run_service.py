from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.airflow_client import AirflowClient
from app.core.config import settings
from app.core.exceptions import (
    AirflowAPIError,
    PipelineRunNotFoundError,
)
from app.models.enums import DatasetStatus
from app.models.pipeline_run import PipelineRun
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.pipeline_run_repository import PipelineRunRepository
from app.schemas.pipeline_run import PipelineRunTriggered
from app.services.dataset_service import DatasetService


class PipelineRunService:
    def __init__(
        self,
        *,
        pipeline_run_repo: PipelineRunRepository,
        dataset_repo: DatasetRepository,
        dataset_service: DatasetService,
        airflow_client: AirflowClient,
    ) -> None:
        self.pipeline_run_repo = pipeline_run_repo
        self.dataset_repo = dataset_repo
        self.dataset_service = dataset_service
        self.airflow_client = airflow_client

    async def start_dataset_processing(
        self,
        db: AsyncSession,
        *,
        dataset_id: int,
        current_user: User,
    ) -> PipelineRunTriggered:
        dataset = await self.dataset_service.get_user_dataset(
            db,
            dataset_id=dataset_id,
            current_user=current_user,
        )
        airflow_run_id = f"insightops__dataset_{dataset.id}__{uuid4().hex}"
        pipeline_run = await self.pipeline_run_repo.create(
            db,
            dataset_id=dataset.id,
            airflow_run_id=airflow_run_id,
        )

        try:
            dag_run = await self.airflow_client.trigger_dag(
                dag_id=settings.AIRFLOW_PROCESS_DATASET_DAG_ID,
                dag_run_id=airflow_run_id,
                conf={
                    "dataset_id": dataset.id,
                    "file_path": dataset.file_path,
                    "pipeline_run_id": pipeline_run.id,
                },
            )
        except AirflowAPIError as error:
            await self.pipeline_run_repo.mark_failed(
                db,
                pipeline_run=pipeline_run,
                error_message=str(error),
            )
            raise

        await self.dataset_repo.update_status(
            db,
            dataset=dataset,
            status=DatasetStatus.PROCESSING,
        )

        return PipelineRunTriggered(
            pipeline_run_id=pipeline_run.id,
            dataset_id=dataset.id,
            airflow_dag_id=settings.AIRFLOW_PROCESS_DATASET_DAG_ID,
            airflow_run_id=airflow_run_id,
            airflow_state=str(dag_run.get("state", "queued")),
        )

    async def get_dataset_pipeline_runs(
        self,
        db: AsyncSession,
        *,
        dataset_id: int,
        current_user: User,
    ) -> list[PipelineRun]:
        dataset = await self.dataset_service.get_user_dataset(
            db,
            dataset_id=dataset_id,
            current_user=current_user,
        )
        return await self.pipeline_run_repo.get_all_by_dataset(
            db,
            dataset_id=dataset.id,
        )

    async def get_pipeline_run(
        self,
        db: AsyncSession,
        *,
        pipeline_run_id: int,
        current_user: User,
    ) -> PipelineRun:
        pipeline_run = await self.pipeline_run_repo.get_by_id_and_owner(
            db,
            pipeline_run_id=pipeline_run_id,
            owner_id=current_user.id,
        )
        if pipeline_run is None:
            raise PipelineRunNotFoundError

        return pipeline_run
