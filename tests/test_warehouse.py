def test_admin_create_warehouse(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Warehouse Admin",
            "email": "warehouse_admin@example.com",
            "password": "Test@123",
            "role": "Admin",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "warehouse_admin@example.com",
            "password": "Test@123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/warehouses",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Main Warehouse",
            "code": "WH-001",
            "address": "Industrial Area",
            "city": "Kurnool",
            "state": "Andhra Pradesh",
            "country": "India",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Main Warehouse"
    assert data["code"] == "WH-001"
    assert data["is_active"] is True


def test_customer_cannot_list_warehouses(client):
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Warehouse Customer",
            "email": "warehouse_customer@example.com",
            "password": "Test@123",
            "role": "Customer",
        },
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "warehouse_customer@example.com",
            "password": "Test@123",
        },
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/warehouses",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403