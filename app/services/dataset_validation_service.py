import csv
from pathlib import Path
from typing import Any

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.models.enums import DatasetStatus
from app.repositories.dataset_repository import DatasetRepository


class DatasetValidationService:
    REQUIRED_COLUMNS = {
        "order_id",
        "customer_id",
        "amount",
        "status",
        "created_at",
    }

    ALLOWED_STATUSES = {
        "paid",
        "failed",
        "pending",
        "cancelled",
        "refunded"
    }

    def __init__(self, repo: DatasetRepository):
        self.repo = repo

    async def validate_dataset(
            self,
            db: AsyncSession,
            *,
            dataset: Dataset
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
                        )
                    }
                ]
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
        errors: list[dict[str, Any]] = []

        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            content = await file.read()

        rows = list(csv.DictReader(content.splitlines()))

        if not rows:
            return [
                {
                    "type": "empty_file",
                    "message": "CSV file is empty or contains only headers.",
                }
            ]

        headers = set(rows[0].keys())
        missing_columns = self.REQUIRED_COLUMNS - headers

        if missing_columns:
            errors.append(
                {
                    "type": "missing_columns",
                    "message": "CSV file is missing required columns.",
                    "columns": sorted(missing_columns),
                }
            )
            return errors

        for row_index, row in enumerate(rows, start=2):
            errors.extend(self._validate_row(row, row_index))

        return errors

    def _validate_row(
        self,
        row: dict[str, str],
        row_index: int,
    ) -> list[dict[str, Any]]:
        errors: list[dict[str, Any]] = []

        for column in self.REQUIRED_COLUMNS:
            if row.get(column) in (None, ""):
                errors.append(
                    {
                        "type": "empty_value",
                        "message": "Required value is empty.",
                        "row": row_index,
                        "column": column,
                    }
                )

        amount = row.get("amount")

        if amount:
            try:
                float(amount)
            except ValueError:
                errors.append(
                    {
                        "type": "invalid_amount",
                        "message": "Amount must be a number.",
                        "row": row_index,
                        "column": "amount",
                        "value": amount,
                    }
                )

        status = row.get("status")

        if status and status.lower() not in self.ALLOWED_STATUSES:
            errors.append(
                {
                    "type": "invalid_status",
                    "message": "Order status is not supported.",
                    "row": row_index,
                    "column": "status",
                    "value": status,
                    "allowed_values": sorted(self.ALLOWED_STATUSES),
                }
            )

        return errors
