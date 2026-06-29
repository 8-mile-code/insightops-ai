from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.base import BaseSchema


class ReportGenerateRequest(BaseModel):
    dataset_id: int | None = None
    pipeline_run_id: int | None = None


class ReportRead(BaseSchema):
    id: int
    project_id: int
    dataset_id: int | None
    pipeline_run_id: int | None
    title: str
    content: str
    metrics_snapshot: dict[str, Any]
    created_at: datetime
    updated_at: datetime
