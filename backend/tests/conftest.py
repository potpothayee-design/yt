"""Test fixtures: isolated env, app client, registered user."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="studio-test-"))

# Configure environment BEFORE any app module reads settings
os.environ["SECRET_KEY"] = "test-secret-key-" + "x" * 32
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["MEDIA_ROOT"] = str(_TMP / "media")
os.environ["JOB_CALLBACK_SECRET"] = "test-callback-secret"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def user_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "tester@example.com", "name": "Tester", "password": "supersecret1"},
    )
    assert resp.status_code in (201, 409), resp.text
    if resp.status_code == 409:
        resp = client.post("/api/v1/auth/login",
                           json={"email": "tester@example.com", "password": "supersecret1"})
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(user_token: str) -> dict:
    return {"Authorization": f"Bearer {user_token}"}


TEST_MEDIA_ROOT = _TMP / "media"
