from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    dataset_id: int | None = None
    pipeline_run_id: int | None = None
    compare_pipeline_run_id: int | None = None


class AskResponse(BaseSchema):
    id: int
    project_id: int
    dataset_id: int | None
    pipeline_run_id: int | None
    question: str
    answer: str
    used_tools: list[str]
    sources: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class AgentMessageRead(BaseSchema):
    id: int
    project_id: int
    dataset_id: int | None
    pipeline_run_id: int | None
    question: str
    answer: str
    used_tools: list[str]
    sources: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime
