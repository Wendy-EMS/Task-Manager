import os

os.environ.setdefault("JWT_SECRET", "test-secret-long-enough-for-jwt")
os.environ.setdefault(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.limiter import limiter
from app.main import app
from app.models import Task, User


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def db_session(tmp_path):
    database_path = tmp_path / "tasks_test.db"
    if database_path.name == "tasks.db":
        raise RuntimeError("La base de test ne doit pas être tasks.db")

    url = "sqlite:///" + database_path.as_posix()
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    session.execute(delete(Task))
    session.execute(delete(User))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_client(client):
    registered = client.post(
        "/auth/register",
        json={"email": "wendy@example.com", "password": "motdepasse"},
    )
    assert registered.status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": "wendy@example.com", "password": "motdepasse"},
    )
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}

    class _Client(object):
        def request(self, method, url, **kwargs):
            merged = dict(headers)
            extra = kwargs.pop("headers", None) or {}
            merged.update(extra)
            return client.request(method, url, headers=merged, **kwargs)

        def get(self, url, **kwargs):
            return self.request("GET", url, **kwargs)

        def post(self, url, **kwargs):
            return self.request("POST", url, **kwargs)

        def put(self, url, **kwargs):
            return self.request("PUT", url, **kwargs)

        def delete(self, url, **kwargs):
            return self.request("DELETE", url, **kwargs)

    return _Client()
