from datetime import datetime

from pydantic import Field

from app.models.dataset import DatasetStatus
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
    created_at: datetime
    updated_at: datetime
