def admin_register(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Admin",
            "email": "catalog_admin@example.com",
            "password": "Test@123",
            "role": "Admin",
        },
    )

    assert response.status_code == 201

    return response.json()


def admin_login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "catalog_admin@example.com",
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_create_category(client):
    admin_register(client)

    token = admin_login(client)

    response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Electronics",
            "description": "Electronic products",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Electronics"
    assert data["description"] == "Electronic products"


def test_create_product(client):
    admin_register(client)

    token = admin_login(client)

    category_response = client.post(
        "/api/categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "name": "Laptop",
            "description": "Laptop products",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    product_response = client.post(
        "/api/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "sku": "LAP-001",
            "name": "Test Laptop",
            "description": "Testing laptop",
            "category_id": category_id,
            "price": 50000,
            "is_active": True,
        },
    )

    assert product_response.status_code == 201

    data = product_response.json()

    assert data["sku"] == "LAP-001"
    assert data["name"] == "Test Laptop"
    assert data["category_id"] == category_id
    assert data["is_active"] is True


def test_list_products(client):
    admin_register(client)

    token = admin_login(client)

    response = client.get(
        "/api/products",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)