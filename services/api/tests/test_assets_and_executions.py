def test_assets_crud(client):
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "change-me"}).status_code == 200

    created = client.post(
        "/assets",
        json={"hostname": "web-01", "ip": "10.0.0.10", "owner": "platform", "tags": ["prod"], "metadata": {}},
    )
    assert created.status_code == 201
    asset = created.json()

    listed = client.get("/assets")
    assert listed.status_code == 200
    assert any(a["id"] == asset["id"] for a in listed.json())

    updated = client.patch(f"/assets/{asset['id']}", json={"owner": "platform-team"})
    assert updated.status_code == 200
    assert updated.json()["owner"] == "platform-team"


def test_create_execution_action_in_test_env_does_not_fail(client):
    # ENVIRONMENT=test causes /executions to skip Celery enqueue.
    assert client.post("/auth/login", json={"email": "admin@example.com", "password": "change-me"}).status_code == 200
    res = client.post("/executions", json={"execution_type": "action", "action": "CORRELATE_ALERTS", "params": {"threshold": 2}})
    assert res.status_code == 201
    assert res.json()["status"] in {"queued", "requires_approval"}

