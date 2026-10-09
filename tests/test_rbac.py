def create_user(client, email, role):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "password": "Test@123",
            "role": role,
        },
    )

    assert response.status_code == 201

    return response.json()


def login(client, email):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_customer_cannot_create_warehouse(client):
    email = "customer_rbac@example.com"

    create_user(client, email, "Customer")

    token = login(client, email)

    response = client.post(
        "/api/warehouses",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Test Warehouse",
            "code": "RBAC-WH-001",
            "address": "Test Address",
            "city": "Kurnool",
            "state": "Andhra Pradesh",
            "country": "India",
        },
    )

    assert response.status_code == 403


def test_customer_cannot_create_product(client):
    email = "customer_product_rbac@example.com"

    create_user(client, email, "Customer")

    token = login(client, email)

    response = client.post(
        "/api/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "sku": "RBAC-SKU-001",
            "name": "RBAC Product",
            "category_id": 999999,
            "price": 100,
            "is_active": True,
        },
    )

    assert response.status_code == 403


def test_customer_cannot_access_inventory(client):
    email = "customer_inventory_rbac@example.com"

    create_user(client, email, "Customer")

    token = login(client, email)

    response = client.get(
        "/api/inventory",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403