"""Pluggable AI provider system.

Capabilities: text | image | video | voice | music.
Every provider implements an interface from ``base.py`` and registers itself
in ``registry.py``. The pipeline only talks to the interfaces, so swapping a
provider never changes pipeline code.
"""

from app.services.providers.registry import (  # noqa: F401
    ProviderRegistry,
    get_provider,
    provider_catalog,
)
