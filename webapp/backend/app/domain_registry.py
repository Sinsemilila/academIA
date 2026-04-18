"""Shared domain ↔ agent mapping. Avoids circular imports from routers
that don't need the full LanguageDomain instances (chat_router.py).

Source of truth remains `chat_router._DOMAIN_REGISTRY` — this module is a
read-only reverse mapping for routers generating UI-facing URLs like
`/chat/{agent_slug}`.

Sprint 5 D1 — domains use ISO-639-1 codes ("en"/"es"/...) for languages,
free strings for non-language domains ("python"/"cybersec").
"""
from __future__ import annotations

# domain (ISO) → agent slug
AGENT_BY_DOMAIN: dict[str, str] = {
    "en": "teacher",
    # "es": "maestro",       # Sprint 5-ES
    # "it": "professore",
    # "de": "lehrer",
    # "ja": "sensei",
    # "python": "pymentor",
    # "cybersec": "cybermentor",
}


def get_agent_for_domain(domain: str) -> str:
    """Return agent slug for a domain (ISO code). Falls back to 'teacher'."""
    return AGENT_BY_DOMAIN.get(domain, "teacher")


def chat_url_for_domain(domain: str) -> str:
    """Return the SPA chat route for a given domain."""
    return f"/chat/{get_agent_for_domain(domain)}"
