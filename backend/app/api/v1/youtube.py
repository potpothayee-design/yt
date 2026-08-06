"""YouTube OAuth connection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import AppError
from app.core.logging import log_event
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.youtube import oauth as yt_oauth

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.get("/status")
def youtube_status(user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)) -> dict:
    creds = yt_oauth.load_credentials(db, user.id)
    channel = ""
    if creds:
        try:
            from app.services.youtube.client import YouTubeClient
            channel = YouTubeClient(creds).channel_title()
        except Exception:
            channel = "(connected)"
    return {
        "configured": yt_oauth.configured(),
        "connected": bool(creds),
        "channel": channel,
    }


@router.post("/disconnect")
def youtube_disconnect(user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)) -> dict:
    yt_oauth.disconnect(db, user.id)
    log_event(db, "INFO", "YouTube disconnected")
    return {"ok": True}


@router.get("/connect")
def youtube_connect(user: User = Depends(get_current_user),
                    db: Session = Depends(get_db),
                    email: str = Query("", max_length=254)) -> dict:
    """Return the Google consent URL for this user.

    ``email`` (optional) becomes Google's ``login_hint`` so the account picker
    preselects the Gmail that owns the target channel instead of whichever
    account the browser defaults to.
    """
    if not yt_oauth.configured():
        raise AppError(
            "YouTube OAuth is not configured on the server. Set "
            "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET (see docs/YOUTUBE_SETUP.md).",
            422,
        )
    hint = email.strip()
    if hint and ("@" not in hint or " " in hint):
        raise AppError("That doesn't look like an email address.", 422)
    from app.core.security import create_access_token
    state = create_access_token(str(user.id))  # JWT doubles as OAuth state
    return {"auth_url": yt_oauth.build_auth_url(state, login_hint=hint or None)}


@router.get("/callback")
def youtube_callback(code: str = Query(...), state: str = Query(""),
                     db: Session = Depends(get_db)) -> HTMLResponse:
    """Google redirects here after consent (public endpoint by design)."""
    payload = decode_access_token(state) if state else None
    if not payload:
        raise HTTPException(401, "invalid oauth state — restart the connection flow")
    user_id = int(payload["sub"])
    creds = yt_oauth.exchange_code(code)
    yt_oauth.store_credentials(db, user_id, creds)
    log_event(db, "INFO", "YouTube channel connected", context={"user_id": user_id})
    return HTMLResponse(_SUCCESS_HTML)


_SUCCESS_HTML = """
<!doctype html><html><head><title>Connected</title>
<style>body{font-family:system-ui;background:#0f172a;color:#e2e8f0;display:flex;
align-items:center;justify-content:center;height:100vh;margin:0}
.card{background:#1e293b;padding:2.5rem 3rem;border-radius:1rem;text-align:center;
box-shadow:0 10px 40px rgba(0,0,0,.4)}h1{color:#4ade80}</style></head>
<body><div class="card"><h1>✔ YouTube connected!</h1>
<p>Your channel is linked. You can close this tab and return to the studio.</p>
<p><a href="/settings" style="color:#60a5fa">Back to Settings</a></p></div></body></html>
"""
