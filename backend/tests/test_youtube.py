"""YouTube OAuth connect endpoint: account hint + picker behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_connect_includes_account_picker_and_login_hint(client: TestClient, auth_headers):
    resp = client.get(
        "/api/v1/youtube/connect?email=creator%40gmail.com", headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    url = resp.json()["auth_url"]
    assert "accounts.google.com" in url
    assert "select_account" in url  # account picker always shown
    assert "consent" in url  # refresh token guarantee kept
    assert "access_type=offline" in url
    assert "login_hint=creator" in url


def test_connect_without_email_has_no_login_hint(client: TestClient, auth_headers):
    resp = client.get("/api/v1/youtube/connect", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    url = resp.json()["auth_url"]
    assert "select_account" in url
    assert "login_hint" not in url


def test_connect_rejects_malformed_email(client: TestClient, auth_headers):
    resp = client.get("/api/v1/youtube/connect?email=not-an-email", headers=auth_headers)
    assert resp.status_code == 422


def test_connect_requires_auth(client: TestClient):
    resp = client.get("/api/v1/youtube/connect")
    assert resp.status_code in (401, 403)


def test_status_reports_configured(client: TestClient, auth_headers):
    resp = client.get("/api/v1/youtube/status", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True  # dummy env creds set in conftest
    assert body["connected"] is False
