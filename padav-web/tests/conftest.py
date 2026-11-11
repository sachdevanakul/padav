import os
import tempfile
from pathlib import Path

# Configure *before* the app is imported: settings are read at import time.
_DB = Path(tempfile.mkdtemp()) / "test.db"
os.environ.update(
    ENVIRONMENT="development",
    DATABASE_URL=f"sqlite:///{_DB}",
    SECRET_KEY="test-secret-key-that-is-definitely-longer-than-32-chars",
    DEBUG="false",
    SEED_ON_STARTUP="false",
    BCRYPT_ROUNDS="10",
    RATE_LIMIT_ENABLED="true",
    LOGIN_MAX_FAILURES="5",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401
from app.core.rate_limit import reset_rate_limits  # noqa: E402
from app.database.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture(autouse=True)
def fresh_state():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    reset_rate_limits()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def register(client, email="user@example.com", password=PASSWORD, name="Test User"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": name})
    assert r.status_code == 200, r.text
    return r.json()


def auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def user(client):
    tokens = register(client)
    return {"tokens": tokens, "headers": auth_headers(tokens)}


@pytest.fixture
def other_user(client):
    tokens = register(client, email="other@example.com")
    return {"tokens": tokens, "headers": auth_headers(tokens)}
