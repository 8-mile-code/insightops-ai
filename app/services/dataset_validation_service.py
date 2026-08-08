import csv
from pathlib import Path
from typing import Any

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.orders_etl import validate_rows
from app.models.dataset import Dataset
from app.models.enums import DatasetStatus
from app.repositories.dataset_repository import DatasetRepository


class DatasetValidationService:
    def __init__(self, repo: DatasetRepository) -> None:
        self.repo = repo

    async def validate_dataset(
        self, db: AsyncSession, *, dataset: Dataset
    ) -> Dataset:
        file_path = Path(dataset.file_path)

        if not file_path.exists():
            return await self.repo.update_validation_result(
                db,
                dataset=dataset,
                status=DatasetStatus.FAILED,
                validation_errors=[
                    {
                        "type": "file_not_found",
                        "message": (
                            f"File not found at path: {dataset.file_path}"
                        ),
                    }
                ],
            )

        if file_path.suffix.lower() != ".csv":
            return await self.repo.update_validation_result(
                db,
                dataset=dataset,
                status=DatasetStatus.FAILED,
                validation_errors=[
                    {
                        "type": "unsupported_file_type",
                        "message": "Only CSV validation is supported for now.",
                    }
                ],
            )

        errors = await self._validate_csv(file_path)

        status = DatasetStatus.UPLOADED if not errors else DatasetStatus.FAILED

        return await self.repo.update_validation_result(
            db,
            dataset=dataset,
            status=status,
            validation_errors=errors or None,
        )

    async def _validate_csv(self, file_path: Path) -> list[dict[str, Any]]:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()

        rows: list[dict[str, Any]] = list(csv.DictReader(content.splitlines()))
        validation_result = validate_rows(rows)

        return validation_result["errors"]
