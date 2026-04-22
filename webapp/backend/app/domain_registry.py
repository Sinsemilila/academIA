"""Shared domain ↔ agent mapping. Session 42 — dynamic derivation from
`agents_config.active_agents()` (which reads AVAILABLE_AGENTS CSV / legacy
ENABLE_* fallback).

Source of truth : `agents_config.ALL_AGENTS`. This module is a read-only
reverse mapping for routers generating UI-facing URLs like `/chat/{slug}`.
"""
from __future__ import annotations

from .agents_config import ALL_AGENTS, active_slug_set


# Static reverse map domain → slug (independent of runtime availability,
# used to resolve URLs even for disabled agents — UI will gate separately).
AGENT_BY_DOMAIN: dict[str, str] = {a.language: a.slug for a in ALL_AGENTS}


def get_agent_for_domain(domain: str) -> str:
    """Return agent slug for a domain (ISO code). Falls back to 'teacher'."""
    return AGENT_BY_DOMAIN.get(domain, "teacher")


def chat_url_for_domain(domain: str) -> str:
    """Return the SPA chat route for a given domain."""
    return f"/chat/{get_agent_for_domain(domain)}"


def is_active_agent(slug: str) -> bool:
    """True if the agent slug is currently enabled at runtime."""
    return slug in active_slug_set()
