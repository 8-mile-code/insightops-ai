from httpx import AsyncClient


async def test_error_response_contains_request_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/projects/999999",
        headers={
            **auth_headers,
            "X-Request-ID": "test-request-id",
        },
    )

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "test-request-id"

    data = response.json()

    assert data["detail"] == "Project not found"
    assert data["error"]["code"] == "project_not_found"
    assert data["error"]["request_id"] == "test-request-id"
    assert data["error"]["message"] == "Project not found"


async def test_validation_error_response_shape(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/projects",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 422

    data = response.json()

    assert data["detail"] == "Request validation failed"
    assert data["error"]["code"] == "validation_error"
    assert "request_id" in data["error"]
    assert isinstance(data["error"]["errors"], list)


async def test_request_id_is_generated_when_missing(
    client: AsyncClient,
) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
