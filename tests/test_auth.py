from httpx import AsyncClient


async def test_register_user(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data


async def test_register_duplicate_email_returns_400(
    client: AsyncClient,
) -> None:
    payload = {
        "email": "test@example.com",
        "password": "strongpassword",
    }

    first_response = await client.post("/auth/register", json=payload)
    second_response = await client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "User with this email already exists"
    )


async def test_login_user_returns_access_token(
    registered_user: dict,
    client: AsyncClient
) -> None:
    response = await client.post(
        "/auth/login",
        data={
            "username": registered_user["email"],
            "password": "strongpassword",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


async def test_me_returns_current_user(
    client: AsyncClient,
    auth_headers: dict[str, str],
    registered_user: dict,
) -> None:
    response = await client.get(
        "/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registered_user["id"]
    assert data["email"] == registered_user["email"]


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401
