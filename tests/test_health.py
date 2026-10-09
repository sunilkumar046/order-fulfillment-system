def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "Order Fulfillment" in data["message"]


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["status"] == "healthy"