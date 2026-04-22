"""Session 42 — GET /api/agents. Returns active agents at runtime.

Frontend (config.ts) fetches this on startup to flip `available: boolean`
on its static agent metadata list. Avoids hardcoding availability at
frontend build time.
"""
from __future__ import annotations

from fastapi import APIRouter

from ..agents_config import ALL_AGENTS, active_slug_set

router = APIRouter()


@router.get("/api/agents")
async def list_agents():
    """Return per-agent availability flags. Frontend merges with its own
    static metadata (flags, colors, labels)."""
    active = active_slug_set()
    return {
        "agents": [
            {
                "slug": a.slug,
                "language": a.language,
                "available": a.slug in active,
            }
            for a in ALL_AGENTS
        ],
        "active_slugs": sorted(active),
        "active_domains": sorted({a.language for a in ALL_AGENTS if a.slug in active}),
    }
