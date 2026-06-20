from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import DatasetStatus

if TYPE_CHECKING:
    from app.models.pipeline_run import PipelineRun
    from app.models.project import Project


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(
            DatasetStatus,
            values_callable=lambda enum_cls: [
                status.value for status in enum_cls
            ],
        ),
        nullable=False,
        default=DatasetStatus.UPLOADED,
    )

    validation_errors: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    project: Mapped["Project"] = relationship(back_populates="datasets")
