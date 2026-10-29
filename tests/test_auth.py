def _token(client, email):
    registered = client.post(
        "/auth/register",
        json={"email": email, "password": "motdepasse"},
    )
    assert registered.status_code == 201
    assert "password" not in registered.json()
    assert "password_hash" not in registered.json()
    assert "motdepasse" not in registered.text
    login = client.post(
        "/auth/login",
        json={"email": email, "password": "motdepasse"},
    )
    assert login.status_code == 200
    return {"Authorization": "Bearer " + login.json()["access_token"]}


def test_register_response_has_no_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "Wendy@Example.com", "password": "motdepasse"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "wendy@example.com"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()
    assert "motdepasse" not in response.text


def test_bad_password_matches_unknown_email(client):
    client.post(
        "/auth/register",
        json={"email": "wendy@example.com", "password": "motdepasse"},
    )
    wrong = client.post(
        "/auth/login",
        json={"email": "wendy@example.com", "password": "mauvaismot"},
    )
    unknown = client.post(
        "/auth/login",
        json={"email": "inconnu@example.com", "password": "mauvaismot"},
    )

    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["detail"] == "Identifiants invalides"
    assert unknown.json()["detail"] == "Identifiants invalides"


def test_other_user_task_is_invisible(client):
    owner = _token(client, "owner@example.com")
    created = client.post(
        "/tasks",
        headers=owner,
        json={"title": "Privée", "priority": "high"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    other = _token(client, "other@example.com")
    payload = {"title": "Privée", "done": True, "priority": "high"}

    assert client.get("/tasks", headers=other).json() == []
    read = client.get("/tasks/{0}".format(task_id), headers=other)
    replaced = client.put("/tasks/{0}".format(task_id), headers=other, json=payload)
    deleted = client.delete("/tasks/{0}".format(task_id), headers=other)

    for response in (read, replaced, deleted):
        assert response.status_code == 404
        assert response.json()["detail"] == "Tâche introuvable"


def test_allowed_origin_receives_cors_header(client):
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_unknown_origin_has_no_cors_header(client):
    response = client.get("/health", headers={"Origin": "http://evil.example"})

    assert response.headers.get("access-control-allow-origin") is None


def test_sixth_login_returns_429(client):
    payload = {"email": "inconnu@example.com", "password": "motdepasse"}
    for _ in range(5):
        assert client.post("/auth/login", json=payload).status_code == 401

    assert client.post("/auth/login", json=payload).status_code == 429


def test_password_over_72_bytes_returns_422(client):
    password = "a" * 73
    response = client.post(
        "/auth/register",
        json={"email": "long@example.com", "password": password},
    )

    assert response.status_code == 422
    assert password not in response.text


def test_tasks_without_token_return_401(client):
    assert client.get("/tasks").status_code == 401
    assert client.post(
        "/tasks",
        json={"title": "Apprendre FastAPI", "priority": "medium"},
    ).status_code == 401
