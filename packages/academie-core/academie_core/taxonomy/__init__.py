"""Taxonomy layer — rules, scoring, gravity, transfer, LLM detection.

Ported to academie-core in Sprint 4 Phase B (2026-04-16). Previously lived at
`webapp/backend/app/error_taxonomy/`. Shims in webapp keep old imports working.

Public re-exports for convenience (importers can also target submodules directly) :
"""
from .categories import TIER1_CATEGORIES, TIER1_DOMAINS, is_valid_code  # noqa: F401
