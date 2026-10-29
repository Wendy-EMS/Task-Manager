def _create_task(auth_client, title, priority="medium", done=None):
    payload = {"title": title, "priority": priority}
    if done is not None:
        payload["done"] = done
    return auth_client.post("/tasks", json=payload)


def test_get_tasks_returns_200_and_empty_list(auth_client):
    response = auth_client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_post_task_returns_201_with_done_false(auth_client):
    response = _create_task(auth_client, "Apprendre FastAPI", "medium")

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Apprendre FastAPI"
    assert body["done"] is False
    assert body["priority"] == "medium"
    assert isinstance(body["id"], int)


def test_get_task_by_id_returns_200(auth_client):
    created = _create_task(auth_client, "Lire une tâche").json()

    response = auth_client.get("/tasks/{0}".format(created["id"]))

    assert response.status_code == 200
    assert response.json() == created


def test_put_task_returns_200_and_keeps_id(auth_client):
    created = _create_task(auth_client, "Avant").json()

    response = auth_client.put(
        "/tasks/{0}".format(created["id"]),
        json={"title": "Apprendre FastAPI", "done": True, "priority": "medium"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Apprendre FastAPI"
    assert body["done"] is True
    assert body["priority"] == "medium"


def test_delete_task_returns_204_then_get_returns_404(auth_client):
    created = _create_task(auth_client, "À supprimer").json()
    url = "/tasks/{0}".format(created["id"])

    deleted = auth_client.delete(url)
    missing = auth_client.get(url)

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Tâche introuvable"


def test_get_tasks_done_true_returns_only_finished(auth_client):
    _create_task(auth_client, "Ouverte", done=False)
    finished = _create_task(auth_client, "Terminée", done=True).json()

    response = auth_client.get("/tasks", params={"done": True})

    assert response.status_code == 200
    assert response.json() == [finished]


def test_get_tasks_skip_0_limit_1_returns_one_task(auth_client):
    first = _create_task(auth_client, "Première").json()
    _create_task(auth_client, "Deuxième")

    response = auth_client.get("/tasks", params={"skip": 0, "limit": 1})

    assert response.status_code == 200
    assert response.json() == [first]


def test_post_empty_title_returns_422(auth_client):
    response = _create_task(auth_client, "")

    assert response.status_code == 422


def test_post_title_of_101_characters_returns_422(auth_client):
    response = _create_task(auth_client, "a" * 101)

    assert response.status_code == 422


def test_post_unknown_priority_returns_422(auth_client):
    response = auth_client.post(
        "/tasks",
        json={"title": "Apprendre FastAPI", "priority": "urgent"},
    )

    assert response.status_code == 422


def test_post_missing_priority_returns_422(auth_client):
    response = auth_client.post("/tasks", json={"title": "Apprendre FastAPI"})

    assert response.status_code == 422


def test_put_missing_done_returns_422(auth_client):
    created = _create_task(auth_client, "À remplacer").json()

    response = auth_client.put(
        "/tasks/{0}".format(created["id"]),
        json={"title": "Apprendre FastAPI", "priority": "medium"},
    )

    assert response.status_code == 422


def test_non_integer_id_returns_422(auth_client):
    for method in (auth_client.get, auth_client.put, auth_client.delete):
        kwargs = {}
        if method is auth_client.put:
            kwargs["json"] = {
                "title": "Apprendre FastAPI",
                "done": True,
                "priority": "medium",
            }
        response = method("/tasks/abc", **kwargs)
        assert response.status_code == 422


def test_missing_task_returns_404(auth_client):
    payload = {"title": "Apprendre FastAPI", "done": True, "priority": "medium"}

    read = auth_client.get("/tasks/999")
    replaced = auth_client.put("/tasks/999", json=payload)
    deleted = auth_client.delete("/tasks/999")

    for response in (read, replaced, deleted):
        assert response.status_code == 404
        assert response.json()["detail"] == "Tâche introuvable"


def test_invalid_pagination_returns_422(auth_client):
    assert auth_client.get("/tasks", params={"skip": -1}).status_code == 422
    assert auth_client.get("/tasks", params={"limit": 0}).status_code == 422
    assert auth_client.get("/tasks", params={"limit": 101}).status_code == 422


def test_title_of_1_and_100_characters_returns_201(auth_client):
    short = _create_task(auth_client, "a")
    long = _create_task(auth_client, "b" * 100)

    assert short.status_code == 201
    assert short.json()["title"] == "a"
    assert long.status_code == 201
    assert long.json()["title"] == "b" * 100


def test_priorities_low_medium_high_return_201(auth_client):
    for priority in ("low", "medium", "high"):
        response = _create_task(auth_client, priority, priority)
        assert response.status_code == 201
        assert response.json()["priority"] == priority


def test_limit_100_returns_200(auth_client):
    response = auth_client.get("/tasks", params={"limit": 100})

    assert response.status_code == 200
    assert response.json() == []
