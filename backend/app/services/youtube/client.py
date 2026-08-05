"""YouTube Data API v3 client: resumable uploads with retries + metadata.

Design notes
------------
* Uploads are ALWAYS initiated explicitly by the user (the API layer enforces
  ``confirm=True`` before this client is ever called).
* Default privacy is ``private`` — videos land as drafts; scheduling uses
  ``status.publishAt`` with privacy ``private``.
* Retries use exponential backoff on resumable transport failures.
* Kids audience settings (``madeForKids`` /
  ``selfDeclaredMadeForKids``) are always set for this product's content.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any

from app.core.errors import AppError


class YouTubeClient:
    def __init__(self, creds_info: dict[str, Any]):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials(
            token=creds_info["token"],
            refresh_token=creds_info.get("refresh_token"),
            token_uri=creds_info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_info.get("client_id"),
            client_secret=creds_info.get("client_secret"),
            scopes=creds_info.get("scopes") or None,
        )
        self.creds = creds
        self.youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    # ------------------------------------------------------------------
    def channel_title(self) -> str:
        resp = self.youtube.channels().list(part="snippet", mine=True).execute()
        items = resp.get("items") or []
        return items[0]["snippet"]["title"] if items else ""

    # ------------------------------------------------------------------
    def upload(
        self,
        video_path: str,
        *,
        title: str,
        description: str,
        tags: list[str],
        privacy: str = "private",
        made_for_kids: bool = True,
        scheduled_at: str | None = None,
        thumbnail_path: str | None = None,
        progress: Callable[[float], None] | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        """Resumable upload with exponential backoff. Returns video resource."""
        from googleapiclient.errors import HttpError
        from googleapiclient.http import MediaFileUpload

        status_body: dict[str, Any] = {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
            "madeForKids": made_for_kids,
        }
        if scheduled_at:
            # scheduled publish requires private until publishAt
            status_body["privacyStatus"] = "private"
            status_body["publishAt"] = scheduled_at

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags[:30],
                "categoryId": "27",  # Education
                "defaultLanguage": "en",
            },
            "status": status_body,
        }
        media = MediaFileUpload(video_path, chunksize=8 * 1024 * 1024, resumable=True,
                                mimetype="video/mp4")
        request = self.youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        response = None
        retry = 0
        while response is None:
            try:
                status, response = request.next_chunk()
                if status and progress:
                    progress(float(status.progress()))
            except HttpError as exc:
                if exc.resp.status in (500, 502, 503, 504) and retry < max_retries:
                    retry += 1
                    time.sleep(min(2 ** retry + random.random(), 60))
                    continue
                raise AppError(f"YouTube upload failed: {exc}", 502) from exc
            except Exception as exc:  # transport-level hiccup -> resume
                if retry < max_retries:
                    retry += 1
                    time.sleep(min(2 ** retry + random.random(), 60))
                    continue
                raise AppError(f"YouTube upload failed: {exc}", 502) from exc

        video_id = response.get("id", "")
        if thumbnail_path and video_id:
            try:
                thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                self.youtube.thumbnails().set(
                    videoId=video_id, media_body=thumb_media
                ).execute()
            except Exception:
                pass  # thumbnail failure must not fail the upload
        return response

    # ------------------------------------------------------------------
    def video_status(self, video_id: str) -> dict[str, Any]:
        resp = self.youtube.videos().list(
            part="status,processingDetails,snippet", id=video_id
        ).execute()
        items = resp.get("items") or []
        if not items:
            return {"found": False}
        item = items[0]
        return {
            "found": True,
            "privacy": item["status"].get("privacyStatus"),
            "upload_status": item["status"].get("uploadStatus"),
            "processing": item.get("processingDetails", {}).get("processingStatus"),
            "publish_at": item["status"].get("publishAt"),
            "made_for_kids": item["status"].get("madeForKids"),
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
