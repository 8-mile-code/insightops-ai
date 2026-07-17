from datetime import datetime

from app.models.enums import PipelineRunStatus
from app.schemas.base import BaseSchema


class PipelineRunRead(BaseSchema):
    id: int
    dataset_id: int
    status: PipelineRunStatus
    airflow_run_id: str | None
    error_message: str | None
    validation_errors: list[dict] | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PipelineRunTriggered(BaseSchema):
    pipeline_run_id: int
    dataset_id: int
    airflow_dag_id: str
    airflow_run_id: str
    airflow_state: str
