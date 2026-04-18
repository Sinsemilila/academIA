"""Language data loader — loads rubrics, fewshots, l1_transfer per lang_target.

Caches at module level via @lru_cache (loaded once per process).
Same pattern as scoring.py tolerance matrix loading.
"""
from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent


@lru_cache(maxsize=16)
def load_rubrics(lang: str) -> dict[str, str] | None:
    """Load rubrics for a target language. Returns None if no YAML found."""
    path = _DATA_DIR / "rubrics" / f"{lang}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("rubrics") if data else None


@lru_cache(maxsize=16)
def load_fewshots(lang: str) -> list[dict] | None:
    """Load fewshot bank for a target language. Returns None if no YAML found."""
    path = _DATA_DIR / "fewshots" / f"{lang}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("fewshots") if data else None


@lru_cache(maxsize=1)
def load_l1_names() -> dict[str, str]:
    """Load ISO-639-1 → English language name mapping."""
    path = _DATA_DIR / "l1_transfer" / "l1_names.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("names", {}) if data else {}


def load_l1_transfers(l1: str, target: str) -> list[tuple[str, float, str]]:
    """Load transfer patterns for a specific L1→target pair.

    Returns a list of (family, multiplier, description) tuples.
    """
    path = _DATA_DIR / "l1_transfer" / f"{l1}_to_{target}.yaml"
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "transfers" not in data:
        return []
    return [
        (t["family"], t["multiplier"], t["description"])
        for t in data["transfers"]
    ]


# Sprint 5 Phase 3 — unified language-tutor shell support
# Extracts concept hints + CEFR diagnostics from per-language YAMLs so the Dify
# chatflow can render them via {{#start.concept_hints_block#}} inputs instead
# of hardcoding EN dicts in its JS code.

@lru_cache(maxsize=16)
def load_concept_hints(lang: str) -> dict[str, str]:
    """Load concept_key → hint mapping for a target language. Empty if missing."""
    path = _DATA_DIR / "concept_hints" / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data or {}


@lru_cache(maxsize=16)
def load_cefr_diagnostics(lang: str) -> dict:
    """Load CEFR diagnostic question examples (paliers + microtasks + persona labels)
    for a target language. Empty dict if no YAML."""
    path = _DATA_DIR / "cefr_diagnostics" / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data or {}


def build_concept_hints_block(lang: str, concept_keys: list[str]) -> str:
    """Render a concept_hints block for the Dify chatflow `code_turn_check` node.

    Returns lines like:
        present_perfect_simple: have/has + past participle (I have visited)
        conditional_2: if + past → would (If I had money, I would travel)

    Filtered to the concepts actually selected for the session (concept_keys).
    Used as {{#start.concept_hints_block#}} input — replaces the hardcoded
    concept_hint_map dict that used to live in the JS code node.
    """
    hints = load_concept_hints(lang)
    lines = []
    for key in concept_keys:
        if key in hints:
            lines.append(f"{key}: {hints[key]}")
    return "\n".join(lines)


def build_cefr_diagnostics_block(lang: str) -> str:
    """Render the full CEFR diagnostic reference block for `llm_onboarding`.

    Includes:
      - First-question map (palier selection based on self-evaluation)
      - Palier reference (for subsequent question choice)
      - Microtask examples

    Used as {{#start.cefr_diagnostics_block#}} input — replaces the hardcoded
    EN example questions embedded in the onboarding system prompt.
    """
    data = load_cefr_diagnostics(lang)
    if not data:
        return ""
    parts = []

    fq = data.get("paliers_first_question", {})
    if fq:
        parts.append("=== PREMIERE QUESTION selon auto-evaluation ===")
        for key, example in fq.items():
            label = key.replace("_", " ")
            parts.append(f"- {label} → {example}")

    pr = data.get("paliers_reference", {})
    if pr:
        parts.append("")
        parts.append("=== PALIERS DE REFERENCE (exemples par niveau) ===")
        for palier, example in pr.items():
            parts.append(f"Palier {palier} : {example}")

    mt = data.get("microtasks", [])
    if mt:
        parts.append("")
        parts.append("=== MICRO-TACHES (obligatoire au 4e ou 5e echange) ===")
        for m in mt:
            parts.append(f'  - "{m}"')

    return "\n".join(parts)


def get_persona_label(lang: str, field: str = "target_prof", default: str = "") -> str:
    """Return a persona label string for a language (e.g., "d'anglais" or "Anglais").

    Falls back to the default if the language or field is missing.
    Used by chat_router to build the persona line passed to Dify LLM nodes.
    """
    data = load_cefr_diagnostics(lang)
    persona = data.get("persona", {}) if data else {}
    return persona.get(field, default)
