"""Session 42 D3 — centralized domain validation.

Replaces per-router duplicated `_validate_domain()` logic. Two modes :

  1. `validate_domain_format(domain: str) -> None` — format-only check
     (2-16 lowercase letters). Raises 422 if malformed. For public
     endpoints where the domain is not yet known to be active.

  2. `validate_active_domain(domain: str) -> None` — format + active
     membership. Raises 422 if the domain isn't in the active set
     (cf. `agents_config.active_domains()`). For endpoints that
     require the domain to be runtime-enabled.

Both are sync helpers designed to be called at the top of a FastAPI
handler (not as `Depends()` — path params + query params are
heterogeneous, simpler to call inline).

Convenience : `valid_domains_set()` for UI/admin listing.
"""
from __future__ import annotations

import re

from fastapi import HTTPException

from .agents_config import active_domains

_DOMAIN_RE = re.compile(r"^[a-z]{2,16}$")


def validate_domain_format(domain: str) -> None:
    """Format check only. Raises HTTPException 422 if invalid shape."""
    if not domain or not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=422, detail="invalid domain code")


def validate_active_domain(domain: str) -> None:
    """Format + active check. Raises HTTPException 422 if domain isn't
    currently in AVAILABLE_AGENTS (via agents_config)."""
    validate_domain_format(domain)
    active = active_domains()
    if domain not in active:
        raise HTTPException(
            status_code=422,
            detail=f"domain '{domain}' not in active set ({sorted(active)})",
        )


def valid_domains_set() -> set[str]:
    """Return current set of active domain codes. Thin wrapper for callers
    that need membership testing without raising."""
    return active_domains()
