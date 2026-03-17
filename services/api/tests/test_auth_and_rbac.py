def test_bootstrap_admin_login_and_me(client):
    res = client.post("/auth/login", json={"email": "admin@example.com", "password": "change-me"})
    assert res.status_code == 200
    assert res.json()["role"] == "admin"

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"


def test_viewer_cannot_create_assets(client):
    # Login as admin and create viewer user
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "change-me"}).status_code == 200
    created = client.post(
        "/users",
        json={"email": "viewer@example.com", "password": "viewerpass1", "role": "viewer"},
    )
    assert created.status_code == 201

    # Login as viewer
    assert client.post("/auth/logout").status_code == 200
    assert client.post("/auth/login", json={"email": "viewer@example.com", "password": "viewerpass1"}).status_code == 200

    # Should be forbidden
    res = client.post("/assets", json={"hostname": "web-01", "ip": "10.0.0.10", "owner": None, "tags": [], "metadata": {}})
    assert res.status_code == 403

