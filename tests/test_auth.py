from uuid import uuid4


def unique_email():
    """
    Generate a unique email for every test.
    This prevents duplicate-email conflicts between tests.
    """
    return f"test_{uuid4().hex[:8]}@example.com"


def register_user(client, role="Customer"):
    """
    Helper function to register a user.
    """

    payload = {
        "full_name": "Test Customer",
        "email": unique_email(),
        "password": "Test@123",
        "role": role,
    }

    response = client.post(
        "/api/auth/register",
        json=payload,
    )

    return response, payload


# ============================================================
# Registration
# ============================================================

def test_register_customer(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == payload["full_name"]
    assert data["email"] == payload["email"]
    assert data["is_active"] is True
    assert "role" in data
    assert data["role"]["name"] == "Customer"


def test_register_duplicate_email(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    duplicate_response = client.post(
        "/api/auth/register",
        json=payload,
    )

    assert duplicate_response.status_code in [400, 409]


# ============================================================
# Login
# ============================================================

def test_login_success(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    assert data["access_token"]
    assert data["refresh_token"]


def test_login_invalid_password(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": "WrongPassword@123",
        },
    )

    assert login_response.status_code in [401, 400]


def test_login_nonexistent_user(client):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": unique_email(),
            "password": "Test@123",
        },
    )

    assert login_response.status_code in [401, 404]


# ============================================================
# Current User
# ============================================================

def test_get_me_with_valid_token(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    data = me_response.json()

    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]


def test_get_me_without_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_get_me_with_invalid_token(client):
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


# ============================================================
# Change Password
# ============================================================

def test_change_password(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_response = client.post(
        "/api/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@123",
            "new_password": "NewTest@123",
        },
    )

    assert change_response.status_code == 204

    # Login using the new password
    new_login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": "NewTest@123",
        },
    )

    assert new_login_response.status_code == 200


def test_change_password_wrong_current_password(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    change_response = client.post(
        "/api/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "WrongPassword@123",
            "new_password": "NewTest@123",
        },
    )

    assert change_response.status_code in [400, 401]




# ============================================================
# Refresh Token
# ============================================================

def test_refresh_token(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    # Refresh-token rotation should give us a different token
    assert data["refresh_token"] != refresh_token


def test_refresh_token_cannot_be_reused(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/api/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert first_refresh.status_code == 200

    second_refresh = client.post(
        "/api/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert second_refresh.status_code == 401


# ============================================================
# Logout
# ============================================================

def test_logout(client):
    response, payload = register_user(client)

    assert response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": payload["email"],
            "password": payload["password"],
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout_response.status_code == 204

    # Revoked refresh token must no longer work
    refresh_response = client.post(
        "/api/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 401