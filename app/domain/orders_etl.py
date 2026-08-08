from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

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
    "refunded",
}


def validate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "is_valid": False,
            "errors": [
                {
                    "type": "empty_file",
                    "message": "CSV file is empty or contains only headers.",
                }
            ],
            "rows_count": 0,
        }

    errors: list[dict[str, Any]] = []

    headers = set(rows[0].keys())
    missing_columns = REQUIRED_COLUMNS - headers

    if missing_columns:
        return {
            "is_valid": False,
            "errors": [
                {
                    "type": "missing_columns",
                    "message": "CSV file is missing required columns.",
                    "columns": sorted(missing_columns),
                }
            ],
            "rows_count": len(rows),
        }

    for row_index, row in enumerate(rows, start=2):
        errors.extend(validate_row(row, row_index))

    return {
        "is_valid": not errors,
        "errors": errors,
        "rows_count": len(rows),
    }


def validate_row(
    row: dict[str, Any],
    row_index: int,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    for column in REQUIRED_COLUMNS:
        value = row.get(column)

        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(
                {
                    "type": "empty_value",
                    "message": "Required value is empty.",
                    "row": row_index,
                    "column": column,
                }
            )

    amount = row.get("amount")

    if amount is not None:
        normalized_amount = (
            amount.strip() if isinstance(amount, str) else amount
        )

        if normalized_amount != "":
            try:
                float(normalized_amount)
            except TypeError, ValueError:
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

    if isinstance(status, str) and status.strip():
        normalized_status = status.strip().lower()

        if normalized_status not in ALLOWED_STATUSES:
            errors.append(
                {
                    "type": "invalid_status",
                    "message": "Order status is not supported.",
                    "row": row_index,
                    "column": "status",
                    "value": status,
                    "allowed_values": sorted(ALLOWED_STATUSES),
                }
            )

    created_at = row.get("created_at")

    if isinstance(created_at, str) and created_at.strip():
        try:
            datetime.fromisoformat(created_at.strip().replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                {
                    "type": "invalid_created_at",
                    "message": "Created at must be a valid ISO datetime.",
                    "row": row_index,
                    "column": "created_at",
                    "value": created_at,
                }
            )

    return errors


def transform_row(
    row: dict[str, Any],
    row_index: int,
) -> dict[str, Any]:
    try:
        created_at = datetime.fromisoformat(
            row["created_at"].strip().replace("Z", "+00:00")
        )
    except ValueError as error:
        raise ValueError(
            f"Invalid created_at value at row {row_index}: {row['created_at']}"
        ) from error

    return {
        "order_id": row["order_id"].strip(),
        "customer_id": row["customer_id"].strip(),
        "amount": float(row["amount"]),
        "status": row["status"].strip().lower(),
        "created_at": created_at.isoformat(),
    }


def transform_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    transformed_rows = [
        transform_row(row, row_index)
        for row_index, row in enumerate(rows, start=2)
    ]

    return {
        "rows_count": len(transformed_rows),
        "transformed_rows": transformed_rows,
    }


def build_aggregates(
    transformed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    daily_revenue: dict[str, float] = defaultdict(float)
    customer_revenue: dict[str, float] = defaultdict(float)
    orders_by_status: Counter[str] = Counter()

    failed_payments_count = 0
    failed_payments_amount = 0.0

    for row in transformed_rows:
        status = row["status"]
        amount = float(row["amount"])
        order_date = (
            datetime.fromisoformat(row["created_at"]).date().isoformat()
        )

        orders_by_status[status] += 1

        if status == "paid":
            daily_revenue[order_date] += amount
            customer_revenue[row["customer_id"]] += amount

        if status == "failed":
            failed_payments_count += 1
            failed_payments_amount += amount

    top_customers = sorted(
        [
            {
                "customer_id": customer_id,
                "revenue": round(revenue, 2),
            }
            for customer_id, revenue in customer_revenue.items()
        ],
        key=lambda item: item["revenue"],
        reverse=True,
    )[:5]

    return {
        "rows_count": len(transformed_rows),
        "daily_revenue": [
            {
                "date": revenue_date,
                "revenue": round(revenue, 2),
            }
            for revenue_date, revenue in sorted(daily_revenue.items())
        ],
        "failed_payments": {
            "count": failed_payments_count,
            "amount": round(failed_payments_amount, 2),
        },
        "top_customers": top_customers,
        "orders_by_status": dict(orders_by_status),
    }
