from pathlib import Path

from httpx import AsyncClient


async def test_upload_dataset(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> None:
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

    data = response.json()

    assert data["name"] == "orders.csv"
    assert data["project_id"] == project_id
    assert "id" in data
    assert data["file_path"].endswith(".csv")
    assert (
        Path(data["file_path"])
        .read_bytes()
        .startswith(b"order_id,customer_id,amount,status,created_at")
    )


async def test_upload_dataset_rejects_unsupported_file(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> None:
    response = await client.post(
        f"/projects/{project_id}/datasets",
        headers=auth_headers,
        files={
            "file": (
                "orders.txt",
                b"some text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV and JSON files are supported"


async def test_get_project_datasets(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> None:
    upload_response = await client.post(
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
    assert upload_response.status_code == 201, upload_response.text

    response = await client.get(
        f"/projects/{project_id}/datasets",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "orders.csv"


async def test_get_dataset_by_id(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> None:
    upload_response = await client.post(
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
    assert upload_response.status_code == 201, upload_response.text
    dataset_id = upload_response.json()["id"]

    response = await client.get(
        f"/datasets/{dataset_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == dataset_id
    assert response.json()["project_id"] == project_id


async def test_cannot_upload_dataset_to_another_user_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
) -> None:
    create_project_response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Private Project",
            "description": None,
        },
    )

    project_id = create_project_response.json()["id"]

    response = await client.post(
        f"/projects/{project_id}/datasets",
        headers=another_auth_headers,
        files={
            "file": (
                "orders.csv",
                b"order_id,customer_id,amount,status,created_at\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
    assert response.json()["error"]["code"] == "project_not_found"


async def test_cannot_get_another_users_dataset(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
    project_id: int,
) -> None:
    upload_response = await client.post(
        f"/projects/{project_id}/datasets",
        headers=auth_headers,
        files={
            "file": (
                "orders.csv",
                b"order_id,customer_id,amount,status,created_at\n",
                "text/csv",
            )
        },
    )
    assert upload_response.status_code == 201, upload_response.text
    dataset_id = upload_response.json()["id"]

    response = await client.get(
        f"/datasets/{dataset_id}",
        headers=another_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Dataset not found"
    assert response.json()["error"]["code"] == "dataset_not_found"


async def test_validate_valid_dataset(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_id: int,
) -> None:
    upload_response = await client.post(
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
    assert upload_response.status_code == 201, upload_response.text
    dataset_id = upload_response.json()["id"]

    response = await client.post(
        f"/datasets/{dataset_id}/validate",
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["validation_errors"] is None
    assert data["validated_at"] is not None


async def test_dataset_endpoints_require_auth(
    client: AsyncClient,
    project_id: int,
) -> None:
    response = await client.get(f"/projects/{project_id}/datasets")

    assert response.status_code == 401
