"""Unit tests for the security helpers."""

from app.core.security import (
    create_access_token,
    decode_access_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    mask_secret,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed.startswith("pbkdf2$")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_jwt_roundtrip():
    token = create_access_token("42")
    payload = decode_access_token(token)
    assert payload and payload["sub"] == "42"
    assert decode_access_token("not.a.token") is None


def test_secret_encryption():
    cipher = encrypt_secret("sk-super-secret-1234")
    assert cipher != "sk-super-secret-1234"
    assert decrypt_secret(cipher) == "sk-super-secret-1234"
    assert decrypt_secret("garbage") == ""


def test_mask_secret():
    assert mask_secret("sk-abcdefghijklmnop").startswith("sk-a")
    assert mask_secret("sk-abcdefghijklmnop").endswith("mnop")
    assert mask_secret("") == ""
