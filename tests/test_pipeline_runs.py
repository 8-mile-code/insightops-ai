from typing import Any

import pytest
from httpx import AsyncClient

from app.clients.airflow_client import AirflowClient
from app.core.exceptions import AirflowAPIError


async def _upload_dataset(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> int:
    response = await client.post(
        f"/projects/{project_id}/datasets",
        headers=auth_headers,
        files={
            "file": (
                "orders.csv",
                b"order_id,customer_id,amount,status,created_at\n"
                b"1,cust_1,100.50,paid,2026-01-01T10:00:00\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 201, response.text

    return int(response.json()["id"])


async def test_process_dataset_triggers_airflow(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = await _upload_dataset(
        client,
        auth_headers,
        project_id,
    )

    captured_conf: dict[str, Any] = {}

    async def fake_trigger_dag(
        self: AirflowClient,
        *,
        dag_id: str,
        dag_run_id: str,
        conf: dict[str, Any],
    ) -> dict[str, Any]:
        captured_conf.update(conf)

        return {
            "dag_run_id": dag_run_id,
            "state": "queued",
        }

    monkeypatch.setattr(
        AirflowClient,
        "trigger_dag",
        fake_trigger_dag,
    )

    response = await client.post(
        f"/datasets/{dataset_id}/process",
        headers=auth_headers,
    )

    assert response.status_code == 202, response.text

    data = response.json()

    assert data["dataset_id"] == dataset_id
    assert data["airflow_state"] == "queued"
    assert "pipeline_run_id" in data
    assert "airflow_run_id" in data

    assert captured_conf["dataset_id"] == dataset_id
    assert captured_conf["pipeline_run_id"] == data["pipeline_run_id"]
    assert captured_conf["file_path"].endswith(".csv")

    dataset_response = await client.get(
        f"/datasets/{dataset_id}",
        headers=auth_headers,
    )
    assert dataset_response.status_code == 200
    assert dataset_response.json()["status"] == "processing"

    pipeline_run_response = await client.get(
        f"/pipeline-runs/{data['pipeline_run_id']}",
        headers=auth_headers,
    )
    assert pipeline_run_response.status_code == 200
    assert pipeline_run_response.json()["status"] == "running"


async def test_process_dataset_returns_503_when_airflow_unavailable(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = await _upload_dataset(
        client,
        auth_headers,
        project_id,
    )

    async def fake_trigger_dag(
        self: AirflowClient,
        *,
        dag_id: str,
        dag_run_id: str,
        conf: dict[str, Any],
    ) -> dict[str, Any]:
        raise AirflowAPIError("Airflow API is unavailable.")

    monkeypatch.setattr(
        AirflowClient,
        "trigger_dag",
        fake_trigger_dag,
    )

    response = await client.post(
        f"/datasets/{dataset_id}/process",
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Airflow API is unavailable."
    assert response.json()["error"]["code"] == "airflow_api_error"

    pipeline_runs_response = await client.get(
        f"/datasets/{dataset_id}/pipeline-runs",
        headers=auth_headers,
    )
    assert pipeline_runs_response.status_code == 200

    pipeline_runs = pipeline_runs_response.json()
    assert len(pipeline_runs) == 1
    assert pipeline_runs[0]["status"] == "failed"
    assert pipeline_runs[0]["error_message"] == "Airflow API is unavailable."
    assert pipeline_runs[0]["finished_at"] is not None


async def test_get_dataset_pipeline_runs(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = await _upload_dataset(
        client,
        auth_headers,
        project_id,
    )

    async def fake_trigger_dag(
        self: AirflowClient,
        *,
        dag_id: str,
        dag_run_id: str,
        conf: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "dag_run_id": dag_run_id,
            "state": "queued",
        }

    monkeypatch.setattr(
        AirflowClient,
        "trigger_dag",
        fake_trigger_dag,
    )

    process_response = await client.post(
        f"/datasets/{dataset_id}/process",
        headers=auth_headers,
    )

    assert process_response.status_code == 202, process_response.text

    response = await client.get(
        f"/datasets/{dataset_id}/pipeline-runs",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["dataset_id"] == dataset_id


async def test_cannot_get_another_users_pipeline_run(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
    project_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_id = await _upload_dataset(
        client,
        auth_headers,
        project_id,
    )

    async def fake_trigger_dag(
        self: AirflowClient,
        *,
        dag_id: str,
        dag_run_id: str,
        conf: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "dag_run_id": dag_run_id,
            "state": "queued",
        }

    monkeypatch.setattr(
        AirflowClient,
        "trigger_dag",
        fake_trigger_dag,
    )

    process_response = await client.post(
        f"/datasets/{dataset_id}/process",
        headers=auth_headers,
    )
    assert process_response.status_code == 202, process_response.text
    pipeline_run_id = process_response.json()["pipeline_run_id"]

    response = await client.get(
        f"/pipeline-runs/{pipeline_run_id}",
        headers=another_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline run not found"
    assert response.json()["error"]["code"] == "pipeline_run_not_found"
