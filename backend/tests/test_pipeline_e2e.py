"""Full offline pipeline end-to-end test.

Runs the complete 12-step production workflow with the built-in providers at
draft quality — validates that a topic becomes a real, watchable MP4 with
narration, captions, music, thumbnails and metadata.

Marked slow; excluded from the quick suite with ``-m "not slow"``.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.rendering.ffmpeg_utils import probe_duration

pytestmark = pytest.mark.slow

SOURCE = Path(__file__).parent / ".." / "app" / "services" / "rendering" / "__init__.py"


def test_full_pipeline_end_to_end(client: TestClient, auth_headers):
    create = client.post(
        "/api/v1/projects", headers=auth_headers,
        json={"topic": "Colors",
              "params": {"topic": "Colors", "target_age": "3-6",
                         "length_seconds": 15, "voice": "female", "language": "en",
                         "music_mood": "cheerful", "aspect_ratio": "16:9",
                         "quality": "draft", "style": "3D Cartoon"}},
    )
    assert create.status_code == 201, create.text
    pid = create.json()["id"]

    gen = client.post(f"/api/v1/projects/{pid}/generate", headers=auth_headers)
    assert gen.status_code == 202, gen.text
    job = gen.json()
    assert len(job["steps"]) >= 12
    assert job["steps"][-1]["name"] == "upload"
    assert job["steps"][-1]["status"] == "pending"  # Pending Approval

    # poll until done (draft 480p should be quick)
    deadline = time.time() + 600
    status = "running"
    final_state = None
    while time.time() < deadline:
        state = client.get(f"/api/v1/projects/{pid}", headers=auth_headers).json()
        status = state["status"]
        final_state = state
        if status in ("ready_for_review", "failed"):
            break
        time.sleep(3)
    assert status == "ready_for_review", final_state.get("error")

    # structured artifacts present
    assert final_state["knowledge"]["learning_objectives"]
    assert final_state["script"]["scenes"]
    assert final_state["storyboard"]
    assert final_state["prompts"]["character_sheet"]["name"]
    assert final_state["video_metadata"]["tags"]
    assert final_state["final_video_url"]

    # real media on disk with sensible duration
    media = Path(final_state["final_video_url"].replace("/media/", ""))
    from tests.conftest import TEST_MEDIA_ROOT
    final_path = TEST_MEDIA_ROOT / media
    assert final_path.exists()
    duration = probe_duration(str(final_path))
    assert 10 < duration < 120

    # assets registered
    kinds = {a["kind"] for a in final_state["assets"]}
    assert {"image", "video_clip", "voice", "music", "captions",
            "thumbnail", "final_video"}.issubset(kinds)

    # captions file exists and has karaoke ASS
    cap = next(a for a in final_state["assets"]
               if a["kind"] == "captions" and a["path"].endswith(".ass"))
    cap_file = TEST_MEDIA_ROOT / cap["path"].replace("/media/", "")
    assert "{\\k" in cap_file.read_text()

    # upload without confirm still refused
    refused = client.post(f"/api/v1/projects/{pid}/uploads", headers=auth_headers,
                          json={"confirm": False})
    assert refused.status_code == 422

    # partial regeneration: thumbnail
    regen = client.post(f"/api/v1/projects/{pid}/regenerate", headers=auth_headers,
                        json={"target": "thumbnail"})
    assert regen.status_code == 202, regen.text
    deadline = time.time() + 120
    while time.time() < deadline:
        state = client.get(f"/api/v1/projects/{pid}", headers=auth_headers).json()
        if state["status"] == "ready_for_review":
            break
        time.sleep(2)
    assert state["status"] == "ready_for_review"
