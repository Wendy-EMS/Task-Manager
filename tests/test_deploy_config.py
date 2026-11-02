import pytest
from pydantic import ValidationError
from starlette.requests import Request

from app.config import Settings
from app.limiter import client_address


def _settings(**values):
    return Settings(_env_file=None, jwt_secret="test-secret-long-enough-for-jwt", **values)


@pytest.mark.parametrize(
    "url",
    [
        "postgres://u:p@hote/base?sslmode=require",
        "postgresql://u:p@hote/base?sslmode=require",
        "postgresql+psycopg://u:p@hote/base?sslmode=require",
    ],
)
def test_database_url_utilise_psycopg(url):
    settings = _settings(database_url=url)
    assert settings.database_url == "postgresql+psycopg://u:p@hote/base?sslmode=require"


def test_sqlite_refuse_sur_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        _settings()


def _request(headers):
    return Request(
        {
            "type": "http",
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
            "client": ("10.0.0.1", 1234),
        }
    )


def test_adresse_client_ignore_les_entetes_hors_vercel(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    request = _request({"x-forwarded-for": "1.2.3.4"})
    assert client_address(request) == "10.0.0.1"


def test_adresse_client_derriere_le_proxy_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    assert client_address(_request({"x-real-ip": "5.6.7.8"})) == "5.6.7.8"
    assert client_address(_request({"x-forwarded-for": "1.2.3.4, 10.0.0.2"})) == "1.2.3.4"
