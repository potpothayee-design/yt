from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderInfo(BaseModel):
    """Describes one selectable provider in the catalog."""

    name: str
    label: str
    capability: str
    requires_key: bool
    is_local: bool
    description: str


class ProviderSettingUpdate(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    api_key: str | None = Field(default=None, max_length=400)
    options: dict | None = None


class ProviderSettingOut(BaseModel):
    capability: str
    provider: str
    masked_key: str
    has_key: bool
    options: dict | None


class ProviderTestResult(BaseModel):
    ok: bool
    message: str
