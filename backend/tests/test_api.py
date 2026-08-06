"""API integration tests (auth, projects, settings control)."""

from fastapi.testclient import TestClient


def test_health(client: TestClient):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert "ffmpeg" in body


def test_auth_required(client: TestClient):
    assert client.get("/api/v1/projects").status_code == 401


def test_register_login_me(client: TestClient, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"
    assert resp.json()["is_admin"] is True  # first user


def test_project_crud(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/projects", headers=auth_headers,
        json={"topic": "ABCs", "params": {"topic": "ABCs", "target_age": "3-6",
                                          "length_seconds": 30, "voice": "female",
                                          "language": "en", "aspect_ratio": "16:9"}},
    )
    assert create.status_code == 201, create.text
    project = create.json()
    assert project["status"] == "draft"

    listed = client.get("/api/v1/projects", headers=auth_headers).json()
    assert any(p["id"] == project["id"] for p in listed)

    detail = client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["topic"] == "ABCs"

    deleted = client.delete(f"/api/v1/projects/{project['id']}", headers=auth_headers)
    assert deleted.status_code == 204


def test_provider_settings_flow(client: TestClient, auth_headers):
    resp = client.get("/api/v1/settings/providers", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["capabilities"]) == {"text", "image", "video", "voice", "music"}
    assert body["capabilities"]["text"]["selected"] == "local"

    # switch to openai with a test key (won't be used unless generation runs)
    upd = client.put("/api/v1/settings/providers/text", headers=auth_headers,
                     json={"provider": "openai", "api_key": "sk-test-1234567890"})
    assert upd.status_code == 200
    assert upd.json()["has_key"] is True
    assert "sk-t" in upd.json()["masked_key"]

    # local providers always pass the test
    tested = client.post("/api/v1/settings/providers/image/test", headers=auth_headers)
    assert tested.status_code == 200

    # unknown provider rejected
    bad = client.put("/api/v1/settings/providers/text", headers=auth_headers,
                     json={"provider": "nonexistent"})
    assert bad.status_code == 422


def test_upload_requires_confirmation(client: TestClient, auth_headers):
    create = client.post("/api/v1/projects", headers=auth_headers, json={"topic": "Fruits"})
    pid = create.json()["id"]
    resp = client.post(f"/api/v1/projects/{pid}/uploads", headers=auth_headers,
                       json={"confirm": False})
    assert resp.status_code == 422  # explicit approval gate
    resp = client.post(f"/api/v1/projects/{pid}/uploads", headers=auth_headers,
                       json={"confirm": True})
    assert resp.status_code == 422  # no final video yet


def test_meta_endpoints(client: TestClient):
    catalog = client.get("/api/v1/meta/provider-catalog").json()
    capabilities = {c["capability"] for c in catalog}
    assert capabilities == {"text", "image", "video", "voice", "music"}
    steps = client.get("/api/v1/meta/pipeline-steps").json()
    assert [s["name"] for s in steps][:3] == ["research", "script", "storyboard"]
    ideas = client.get("/api/v1/meta/topic-ideas").json()
    assert len(ideas) >= 8


def test_delete_project_removes_media_and_404s(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/projects", headers=auth_headers,
        json={"topic": "DeleteMe", "params": {"topic": "DeleteMe",
                                              "target_age": "3-6", "length_seconds": 15}},
    )
    assert create.status_code == 201
    pid = create.json()["id"]

    # simulate generated media on disk
    from tests.conftest import TEST_MEDIA_ROOT
    media_dir = TEST_MEDIA_ROOT / "projects" / str(pid)
    media_dir.mkdir(parents=True)
    (media_dir / "final.mp4").write_bytes(b"fake")

    resp = client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert resp.status_code == 204
    assert not media_dir.exists(), "media folder should be wiped"

    gone = client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert gone.status_code == 404
    again = client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert again.status_code == 404
