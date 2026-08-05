"""YouTube OAuth 2.0 flow + credential persistence.

User grants access on Google's consent screen; we store the resulting token
JSON encrypted (Fernet) in the ``provider_settings`` table under capability
``youtube``. Refresh tokens are used for subsequent uploads so the user only
authorizes once.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.core.security import decrypt_secret, encrypt_secret
from app.models.setting import ProviderSetting


def configured() -> bool:
    s = get_settings()
    return bool(s.YOUTUBE_CLIENT_ID and s.YOUTUBE_CLIENT_SECRET)


def build_auth_url(state: str) -> str:
    """Google consent URL. Raises if OAuth client is not configured."""
    from google_auth_oauthlib.flow import Flow

    s = get_settings()
    flow = Flow.from_client_config(
        _client_config(), scopes=s.youtube_scope_list, redirect_uri=s.YOUTUBE_REDIRECT_URI
    )
    url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent", state=state
    )
    return url


def exchange_code(code: str) -> dict[str, Any]:
    from google_auth_oauthlib.flow import Flow

    s = get_settings()
    flow = Flow.from_client_config(
        _client_config(), scopes=s.youtube_scope_list, redirect_uri=s.YOUTUBE_REDIRECT_URI
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
    }


def store_credentials(db, user_id: int, creds_json: dict[str, Any]) -> None:
    row = (
        db.query(ProviderSetting)
        .filter_by(user_id=user_id, capability="youtube")
        .one_or_none()
    )
    payload = encrypt_secret(json.dumps(creds_json))
    if row is None:
        row = ProviderSetting(user_id=user_id, capability="youtube", provider="youtube")
        db.add(row)
    row.api_key_encrypted = payload
    db.commit()


def load_credentials(db, user_id: int) -> dict[str, Any] | None:
    row = (
        db.query(ProviderSetting)
        .filter_by(user_id=user_id, capability="youtube")
        .one_or_none()
    )
    if not row or not row.api_key_encrypted:
        return None
    raw = decrypt_secret(row.api_key_encrypted)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def disconnect(db, user_id: int) -> None:
    row = (
        db.query(ProviderSetting)
        .filter_by(user_id=user_id, capability="youtube")
        .one_or_none()
    )
    if row:
        db.delete(row)
        db.commit()


def _client_config() -> dict:
    s = get_settings()
    return {
        "web": {
            "client_id": s.YOUTUBE_CLIENT_ID,
            "client_secret": s.YOUTUBE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
