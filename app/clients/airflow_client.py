from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AirflowAPIError


class AirflowClient:
    def __init__(
        self,
        *,
        base_url: str = settings.AIRFLOW_API_BASE_URL,
        username: str = settings.AIRFLOW_API_USERNAME,
        password: str = settings.AIRFLOW_API_PASSWORD,
        timeout: float = settings.AIRFLOW_API_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

    async def trigger_dag(
        self,
        *,
        dag_id: str,
        dag_run_id: str,
        conf: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
            ) as client:
                token = await self._get_access_token(client)
                response = await client.post(
                    f"/api/v2/dags/{dag_id}/dagRuns",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "dag_run_id": dag_run_id,
                        "logical_date": None,
                        "conf": conf,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise AirflowAPIError(
                "Airflow rejected the DAG run request "
                f"with status {error.response.status_code}."
            ) from error
        except httpx.HTTPError as error:
            raise AirflowAPIError("Airflow API is unavailable.") from error

        return response.json()

    async def _get_access_token(
        self,
        client: httpx.AsyncClient,
    ) -> str:
        response = await client.post(
            "/auth/token",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        response.raise_for_status()

        access_token = response.json().get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise AirflowAPIError(
                "Airflow authentication response has no access token."
            )

        return access_token
