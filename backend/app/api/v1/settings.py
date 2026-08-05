"""Provider settings + API key management (the Settings / API Keys pages)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import decrypt_secret, encrypt_secret, mask_secret
from app.db.session import get_db
from app.models.setting import ProviderSetting
from app.models.user import User
from app.schemas.settings import (
    ProviderSettingOut,
    ProviderSettingUpdate,
    ProviderTestResult,
)
from app.services.providers import get_provider, provider_catalog
from app.services.providers.registry import _REGISTRY

router = APIRouter(prefix="/settings", tags=["settings"])

_CAPABILITIES = ("text", "image", "video", "voice", "music")


@router.get("/providers")
def get_provider_settings(user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> dict:
    """Catalog + current selection + masked key status per capability."""
    settings = get_settings()
    rows = {r.capability: r for r in
            db.query(ProviderSetting).filter(ProviderSetting.user_id == user.id)}
    by_capability: dict[str, dict] = {}
    for capability in _CAPABILITIES:
        row = rows.get(capability)
        env_default = getattr(settings, f"{capability.upper()}_PROVIDER")
        selected = (row.provider if row else env_default) or "local"
        key_plain = decrypt_secret(row.api_key_encrypted) if row else ""
        env_key = settings.provider_key(selected)
        by_capability[capability] = {
            "selected": selected,
            "has_key": bool(key_plain or env_key),
            "masked_key": mask_secret(key_plain or env_key),
            "options": (row.options if row else {}) or {},
            "available": [
                {"name": name, "label": label, "requires_key": requires_key,
                 "description": desc}
                for name, (_m, _c, label, requires_key, desc) in
                _REGISTRY[capability].items()
            ],
        }
    youtube_row = db.query(ProviderSetting).filter_by(
        user_id=user.id, capability="youtube").one_or_none()
    return {
        "capabilities": by_capability,
        "youtube": {"connected": bool(youtube_row and youtube_row.api_key_encrypted)},
        "catalog": provider_catalog(),
    }


@router.put("/providers/{capability}", response_model=ProviderSettingOut)
def update_provider_setting(
    capability: str,
    body: ProviderSettingUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProviderSettingOut:
    if capability not in _CAPABILITIES:
        raise AppError(f"unknown capability '{capability}'", 404)
    if body.provider not in _REGISTRY.get(capability, {}):
        raise AppError(f"unknown provider '{body.provider}' for {capability}", 422)
    row = db.query(ProviderSetting).filter_by(
        user_id=user.id, capability=capability).one_or_none()
    if row is None:
        row = ProviderSetting(user_id=user.id, capability=capability)
        db.add(row)
    row.provider = body.provider
    if body.api_key is not None:
        row.api_key_encrypted = encrypt_secret(body.api_key.strip())
    if body.options is not None:
        row.options = body.options
    db.commit()
    key_plain = decrypt_secret(row.api_key_encrypted)
    return ProviderSettingOut(
        capability=capability, provider=row.provider,
        masked_key=mask_secret(key_plain), has_key=bool(key_plain),
        options=row.options or {},
    )


@router.post("/providers/{capability}/test", response_model=ProviderTestResult)
def test_provider(capability: str, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)) -> ProviderTestResult:
    """Instantiate the provider and run the cheapest possible validation."""
    if capability not in _CAPABILITIES:
        raise AppError(f"unknown capability '{capability}'", 404)
    row = db.query(ProviderSetting).filter_by(
        user_id=user.id, capability=capability).one_or_none()
    provider_name = row.provider if row else getattr(
        get_settings(), f"{capability.upper()}_PROVIDER")
    api_key = decrypt_secret(row.api_key_encrypted) if row else None
    provider = get_provider(capability, provider_name, api_key)
    probe = getattr(provider, "probe", None)
    if callable(probe):
        ok, message = probe()
        return ProviderTestResult(ok=ok, message=message)
    if not getattr(provider, "requires_key", False):
        return ProviderTestResult(ok=True, message=f"'{provider.label}' works offline — no key needed.")
    ok, message = _ping_external(capability, provider_name, api_key or
                                 get_settings().provider_key(provider_name))
    return ProviderTestResult(ok=ok, message=message)


def _ping_external(capability: str, provider: str, api_key: str) -> tuple[bool, str]:
    if not api_key:
        return False, "no API key stored — add it on the API Keys page"
    import httpx
    checks = {
        "openai": ("GET", "https://api.openai.com/v1/models",
                   {"Authorization": f"Bearer {api_key}"}),
        "openai-tts": ("GET", "https://api.openai.com/v1/models",
                       {"Authorization": f"Bearer {api_key}"}),
        "anthropic": ("GET", "https://api.anthropic.com/v1/models",
                      {"x-api-key": api_key, "anthropic-version": "2023-06-01"}),
        "elevenlabs": ("GET", "https://api.elevenlabs.io/v1/user",
                       {"xi-api-key": api_key}),
        "stability": ("GET", "https://api.stability.ai/v1/user/balance",
                      {"Authorization": f"Bearer {api_key}"}),
        "google-tts": ("GET", f"https://texttospeech.googleapis.com/v1/voices?key={api_key}", {}),
    }
    spec = checks.get(provider)
    if not spec:
        return True, f"key saved for '{provider}' (validated on first use)"
    method, url, headers = spec
    try:
        resp = httpx.request(method, url, headers=headers, timeout=15)
        if resp.status_code < 300:
            return True, "connection OK ✔"
        if resp.status_code in (401, 403):
            return False, f"key rejected (HTTP {resp.status_code}) — check the key"
        return False, f"provider responded HTTP {resp.status_code}"
    except httpx.HTTPError as exc:
        return False, f"network error: {exc}"
