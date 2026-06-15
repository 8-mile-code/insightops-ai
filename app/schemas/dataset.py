from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import DatasetStatus
from app.schemas.base import BaseSchema


class DatasetCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    # file будет передаваться отдельно,
    # чуть позже можно добавить валидацию формата файла и размера
    # file: UploadFile


class DatasetRead(BaseSchema):
    id: int
    name: str
    status: DatasetStatus
    file_path: str
    project_id: int
    validation_errors: list[dict[str, Any]] | None = None
    validated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
