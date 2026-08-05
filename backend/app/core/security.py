"""Security helpers: password hashing, JWT issuance and API-key encryption.

* Passwords  -> PBKDF2-HMAC-SHA256 (stdlib, 600k iterations, per-password salt)
* Tokens     -> short-lived JWT (HS256)
* API keys   -> symmetric encryption with Fernet (AES-128-CBC + HMAC) so they
  are never stored in plaintext in the database.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings

_PBKDF2_ITERATIONS = 600_000
_ALGO = "HS256"


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password as ``pbkdf2$iterations$salt_hex$hash_hex``."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iters, salt_hex, hash_hex = stored.split("$")
        if scheme != "pbkdf2":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.effective_secret_key, algorithm=_ALGO)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.effective_secret_key, algorithms=[_ALGO])
    except jwt.PyJWTError:
        return None


# ---------------------------------------------------------------------------
# API key encryption (Fernet over a key derived from SECRET_KEY)
# ---------------------------------------------------------------------------

def _fernet() -> Fernet:
    settings = get_settings()
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.effective_secret_key.encode()).digest()
    )
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        return ""


def mask_secret(plaintext: str) -> str:
    """Return a display-safe masked secret, e.g. ``sk-...••••1234``."""
    if not plaintext:
        return ""
    if len(plaintext) <= 8:
        return "•" * len(plaintext)
    return f"{plaintext[:4]}…{plaintext[-4:]}"
