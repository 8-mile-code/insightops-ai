import pytest

from app.domain.orders_etl import (
    build_aggregates,
    transform_row,
    transform_rows,
    validate_rows,
)


def test_validate_rows_accepts_valid_orders() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "cust_001",
            "amount": "120.50",
            "status": "paid",
            "created_at": "2026-01-01T10:00:00",
        }
    ]

    result = validate_rows(rows)

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["rows_count"] == 1


def test_validate_rows_detects_missing_columns() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "cust_001",
            "amount": "120.50",
        }
    ]

    result = validate_rows(rows)

    assert result["is_valid"] is False
    assert result["errors"][0]["type"] == "missing_columns"
    assert "created_at" in result["errors"][0]["columns"]
    assert "status" in result["errors"][0]["columns"]


def test_validate_rows_detects_invalid_values() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "",
            "amount": "not_number",
            "status": "unknown",
            "created_at": "2026-01-01T10:00:00",
        }
    ]

    result = validate_rows(rows)

    error_types = {error["type"] for error in result["errors"]}

    assert result["is_valid"] is False
    assert "empty_value" in error_types
    assert "invalid_amount" in error_types
    assert "invalid_status" in error_types


def test_transform_row_normalizes_order_data() -> None:
    row = {
        "order_id": " ord_001 ",
        "customer_id": " cust_001 ",
        "amount": "120.50",
        "status": " PAID ",
        "created_at": "2026-01-01T10:00:00",
    }

    result = transform_row(row, row_index=2)

    assert result["order_id"] == "ord_001"
    assert result["customer_id"] == "cust_001"
    assert result["amount"] == 120.50
    assert result["status"] == "paid"
    assert result["created_at"] == "2026-01-01T10:00:00"


def test_transform_row_raises_for_invalid_created_at() -> None:
    row = {
        "order_id": "ord_001",
        "customer_id": "cust_001",
        "amount": "120.50",
        "status": "paid",
        "created_at": "not-a-date",
    }

    with pytest.raises(ValueError, match="Invalid created_at value"):
        transform_row(row, row_index=2)


def test_build_aggregates() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "cust_001",
            "amount": "120.50",
            "status": "paid",
            "created_at": "2026-01-01T10:00:00",
        },
        {
            "order_id": "ord_002",
            "customer_id": "cust_002",
            "amount": "89.99",
            "status": "paid",
            "created_at": "2026-01-01T12:30:00",
        },
        {
            "order_id": "ord_003",
            "customer_id": "cust_001",
            "amount": "45.00",
            "status": "failed",
            "created_at": "2026-01-02T09:15:00",
        },
    ]

    transform_result = transform_rows(rows)
    aggregate_result = build_aggregates(transform_result["transformed_rows"])

    assert aggregate_result["rows_count"] == 3
    assert aggregate_result["daily_revenue"] == [
        {
            "date": "2026-01-01",
            "revenue": 210.49,
        }
    ]
    assert aggregate_result["failed_payments"] == {
        "count": 1,
        "amount": 45.00,
    }
    assert aggregate_result["orders_by_status"] == {
        "paid": 2,
        "failed": 1,
    }
    assert aggregate_result["top_customers"][0] == {
        "customer_id": "cust_001",
        "revenue": 120.50,
    }


def test_validate_rows_rejects_empty_input() -> None:
    result = validate_rows([])

    assert result == {
        "is_valid": False,
        "errors": [
            {
                "type": "empty_file",
                "message": "CSV file is empty or contains only headers.",
            }
        ],
        "rows_count": 0,
    }


def test_validate_rows_detects_invalid_created_at() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "cust_001",
            "amount": "120.50",
            "status": "paid",
            "created_at": "not-a-date",
        }
    ]

    result = validate_rows(rows)

    assert result["is_valid"] is False
    assert result["rows_count"] == 1
    assert result["errors"] == [
        {
            "type": "invalid_created_at",
            "message": "Created at must be a valid ISO datetime.",
            "row": 2,
            "column": "created_at",
            "value": "not-a-date",
        }
    ]


def test_validate_rows_treats_whitespace_as_empty() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "   ",
            "amount": "   ",
            "status": "paid",
            "created_at": "2026-01-01T10:00:00",
        }
    ]

    result = validate_rows(rows)

    errors = {
        (error["type"], error.get("column")) for error in result["errors"]
    }

    assert result["is_valid"] is False
    assert errors == {
        ("empty_value", "customer_id"),
        ("empty_value", "amount"),
    }


def test_validate_rows_accepts_normalized_values() -> None:
    rows = [
        {
            "order_id": "ord_001",
            "customer_id": "cust_001",
            "amount": " 120.50 ",
            "status": " PAID ",
            "created_at": " 2026-01-01T10:00:00Z ",
        }
    ]

    result = validate_rows(rows)

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["rows_count"] == 1
