from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from app.repositories.analytics_repository import AnalyticsRepository


def test_get_daily_revenue_maps_rows_and_passes_filters() -> None:
    client = Mock()
    client.query.return_value = SimpleNamespace(
        result_rows=[
            (date(2026, 1, 1), 125.555),
            (date(2026, 1, 2), 200),
        ]
    )
    repository = AnalyticsRepository(client=client)

    result = repository.get_daily_revenue(
        project_id=11,
        dataset_id=12,
        pipeline_run_id=13,
    )

    assert result == [
        {"date": date(2026, 1, 1), "revenue": 125.56},
        {"date": date(2026, 1, 2), "revenue": 200.0},
    ]
    query = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]
    assert "FROM daily_revenue" in query
    assert parameters == {
        "project_id": 11,
        "dataset_id": 12,
        "pipeline_run_id": 13,
    }


def test_get_orders_by_status_maps_rows() -> None:
    client = Mock()
    client.query.return_value = SimpleNamespace(
        result_rows=[
            ("failed", 2),
            ("paid", 5),
        ]
    )
    repository = AnalyticsRepository(client=client)

    result = repository.get_orders_by_status(project_id=11)

    assert result == [
        {"status": "failed", "orders_count": 2},
        {"status": "paid", "orders_count": 5},
    ]
    assert client.query.call_args.kwargs["parameters"] == {"project_id": 11}


def test_get_failed_payments_converts_null_aggregates_to_zero() -> None:
    client = Mock()
    client.query.return_value = SimpleNamespace(result_rows=[(None, None)])
    repository = AnalyticsRepository(client=client)

    result = repository.get_failed_payments(
        project_id=11,
        dataset_id=12,
    )

    assert result == {
        "failed_count": 0,
        "failed_amount": 0.0,
    }
    assert client.query.call_args.kwargs["parameters"] == {
        "project_id": 11,
        "dataset_id": 12,
    }


def test_get_top_customers_passes_limit_and_maps_rows() -> None:
    client = Mock()
    client.query.return_value = SimpleNamespace(
        result_rows=[
            ("customer-1", 350.499),
        ]
    )
    repository = AnalyticsRepository(client=client)

    result = repository.get_top_customers(
        project_id=11,
        pipeline_run_id=13,
        limit=3,
    )

    assert result == [
        {
            "customer_id": "customer-1",
            "revenue": 350.5,
        }
    ]
    query = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]
    assert "FROM top_customers" in query
    assert parameters == {
        "project_id": 11,
        "pipeline_run_id": 13,
        "limit": 3,
    }
