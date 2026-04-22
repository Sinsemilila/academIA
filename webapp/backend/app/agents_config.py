"""Session 42 — single source of truth for agent definitions + availability.

Replaces scattered `ENABLE_MAESTRO / ENABLE_PROFESSORE` gates with a single
CSV env var `AVAILABLE_AGENTS`. Backward-compat : if `AVAILABLE_AGENTS` is
unset, falls back to reading per-agent `ENABLE_{SLUG}` flags (teacher is
always available by default).

Source of truth for :
  - chat_router._DOMAIN_REGISTRY
  - chat_router.DIFY_APP_KEYS
  - domain_registry.AGENT_BY_DOMAIN
  - /api/agents endpoint (frontend availability fetch)
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentDef:
    slug: str
    language: str          # ISO code (en, es, it, ...)
    env_key_name: str      # DIFY_KEY_* env var
    display_name: str      # UI label (used when frontend doesn't have its own metadata)


# All agents the platform CAN support (whether currently active or not).
# Adding a new one = add entry here + flip AVAILABLE_AGENTS CSV.
ALL_AGENTS: list[AgentDef] = [
    AgentDef("teacher",     "en",       "DIFY_KEY_TEACHER",     "Teacher — English"),
    AgentDef("maestro",     "es",       "DIFY_KEY_MAESTRO",     "Maestro — Spanish"),
    AgentDef("professore",  "it",       "DIFY_KEY_PROFESSORE",  "Professore — Italian"),
    AgentDef("lehrer",      "de",       "DIFY_KEY_LEHRER",      "Lehrer — German"),
    AgentDef("sensei",      "ja",       "DIFY_KEY_SENSEI",      "Sensei — Japanese"),
    AgentDef("pymentor",    "python",   "DIFY_KEY_PYMENTOR",    "PyMentor — Python"),
    AgentDef("cybermentor", "cybersec", "DIFY_KEY_CYBERMENTOR", "CyberMentor — Cybersec"),
]


def _active_slugs() -> set[str]:
    """Resolve which agent slugs should be active at runtime.

    Order of precedence :
      1. `AVAILABLE_AGENTS=teacher,maestro` CSV — canonical, post Session 42.
      2. Backward-compat fallback : per-agent `ENABLE_{SLUG}` env vars
         (so deployments still honoring `ENABLE_MAESTRO=true` keep working
         while we migrate).
      3. Hardcoded default : teacher always active.
    """
    raw = os.environ.get("AVAILABLE_AGENTS", "").strip()
    if raw:
        return {s.strip() for s in raw.split(",") if s.strip()}
    # Fallback : ENABLE_{SLUG}
    out = {"teacher"}
    for a in ALL_AGENTS:
        if a.slug == "teacher":
            continue
        env_name = f"ENABLE_{a.slug.upper()}"
        if os.environ.get(env_name, "false").lower() in ("1", "true", "yes"):
            out.add(a.slug)
    return out


def active_agents() -> list[AgentDef]:
    """Return the AgentDef list restricted to currently-active agents."""
    slugs = _active_slugs()
    return [a for a in ALL_AGENTS if a.slug in slugs]


def active_slug_set() -> set[str]:
    """Shortcut when the caller only needs to check membership."""
    return _active_slugs()


def active_domains() -> set[str]:
    """Return set of active domain ISO codes (teacher → 'en', etc.)."""
    return {a.language for a in active_agents()}


def agent_for_slug(slug: str) -> AgentDef | None:
    for a in ALL_AGENTS:
        if a.slug == slug:
            return a
    return None


def agent_for_domain(domain: str) -> AgentDef | None:
    for a in ALL_AGENTS:
        if a.language == domain:
            return a
    return None
