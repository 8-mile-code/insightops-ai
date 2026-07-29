from httpx import AsyncClient


async def test_create_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Test Project",
            "description": "Project for tests",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Project"
    assert data["description"] == "Project for tests"
    assert "id" in data


async def test_get_projects_returns_only_user_projects(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
) -> None:
    await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Project A",
            "description": None,
        },
    )

    await client.post(
        "/projects",
        headers=another_auth_headers,
        json={
            "name": "Project B",
            "description": None,
        },
    )

    response = await client.get(
        "/projects",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Project A"


async def test_cannot_get_another_user_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
) -> None:
    create_response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Private Project",
            "description": None,
        },
    )
    project_id = create_response.json()["id"]

    response = await client.get(
        f"/projects/{project_id}",
        headers=another_auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"
    assert response.json()["error"]["code"] == "project_not_found"


async def test_cannot_delete_another_user_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    another_auth_headers: dict[str, str],
) -> None:
    create_response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Private Project",
            "description": None,
        },
    )
    project_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/projects/{project_id}",
        headers=another_auth_headers,
    )

    assert delete_response.status_code == 404

    owner_response = await client.get(
        f"/projects/{project_id}",
        headers=auth_headers,
    )

    assert owner_response.status_code == 200


async def test_get_missing_project_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/projects/999",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


async def test_projects_require_auth(client: AsyncClient) -> None:
    response = await client.get("/projects")

    assert response.status_code == 401


async def test_owner_can_delete_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    create_response = await client.post(
        "/projects",
        headers=auth_headers,
        json={
            "name": "Project to delete",
            "description": None,
        },
    )
    project_id = create_response.json()["id"]

    delete_response = await client.delete(
        f"/projects/{project_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code == 204

    get_response = await client.get(
        f"/projects/{project_id}",
        headers=auth_headers,
    )

    assert get_response.status_code == 404
