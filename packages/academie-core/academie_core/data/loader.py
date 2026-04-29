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


@lru_cache(maxsize=16)
def load_anti_patterns(lang: str) -> list[dict] | None:
    """Session 45 P2c — load the anti-pattern bank (what NOT to do).
    Schema per entry : id, level, wrong_type, learner, wrong_teacher,
    why_wrong, correct_teacher. Used to contrast-train the LLM out of
    forbidden CF moves at A1/A2 when rubric-level bans alone aren't
    enough. Returns None when no entry is defined."""
    path = _DATA_DIR / "fewshots" / f"{lang}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return (data.get("anti_patterns") or None) if data else None


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

@lru_cache(maxsize=64)
def load_extracted(book_slug: str, extraction_name: str) -> dict | None:
    """Load structured knowledge extracted from a canonical book (ADR-014 Layer 1.5).

    Path : data/extracted/<book_slug>/<extraction_name>.yaml
    Returns None if extraction not yet created (lazy pattern — extraction
    triggered when first code-work consumer lands, not anticipated batch).

    See docs/05-decisions/ADR-014-structured-knowledge-extraction.md.
    """
    path = _DATA_DIR / "extracted" / book_slug / f"{extraction_name}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


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
def load_micro_lessons(lang: str) -> dict[str, dict[str, str]]:
    """Load 3-strikes micro-lesson templates per error_family per CEFR band.

    Returns {family: {"A1": str, "A2": str, "B1": str}}. Empty if YAML absent.
    See `pedagogy/three_strikes.py` + docs/01-pedagogy doctrine on progressive
    metalanguage (A1 example-only, A2 short rule, B1+ full metalinguistic).
    """
    path = _DATA_DIR / "micro_lessons" / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data or {}


@lru_cache(maxsize=16)
def load_functions(lang: str) -> dict:
    """Load communicative functions per CEFR level for a target language.

    Phase D1 (Session 53) scope : Functions dimension scaffold. New top-level
    dimension complementing structural curriculum_*.yaml (CEFR Companion 2020
    organizes by Reception/Production/Interaction/Mediation modes ; PCIC has
    13 inventarios including Funciones — communicative goals).

    Returns full dict (domain + per-level functions). Empty if YAML absent.
    Schema : `data/schemas.py:FunctionsPack`. See ADR-016 authority anchor strategy.
    """
    path = _DATA_DIR / "functions" / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data or {}


def build_functions_block(lang: str, level: str) -> str:
    """Render functions block for a given CEFR level. Used by Dify chatflow.

    Format :
        Category : Function — Exponents
    Example output for ES A1 :
        Identificar : Yo soy..., Mi nombre es...
        Pedir información : ¿Cómo te llamas? ¿Dónde vives?

    Returns empty string if no functions defined for lang/level.
    """
    data = load_functions(lang)
    if not data:
        return ""
    level_block = data.get(level, {})
    funcs = level_block.get("functions", [])
    if not funcs:
        return ""
    lines = []
    for f in funcs:
        category = f.get("category", "")
        function = f.get("function", "")
        exponents = f.get("exponents", [])
        exp_str = " / ".join(exponents[:3])  # first 3 exponents max
        lines.append(f"{category} → {function} : {exp_str}")
    return "\n".join(lines)


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


# ── Onboarding QCM content (Sprint 5 Phase 5) ────────────────────────
# Compiles core.yaml + domains/{kind}.yaml + overlays/{lang}.yaml into a
# single dict the frontend can render directly. See
# docs/00-project/onboarding-research-2026-04-20/vague2-qcm-design.md §4.

@lru_cache(maxsize=16)
def _load_onboarding_core() -> dict:
    path = _DATA_DIR / "onboarding" / "core.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=16)
def _load_onboarding_domain(domain_kind: str) -> dict:
    path = _DATA_DIR / "onboarding" / "domains" / f"{domain_kind}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=16)
def _load_onboarding_overlay(lang: str) -> dict:
    path = _DATA_DIR / "onboarding" / "overlays" / f"{lang}.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# Map domain code → which domains/*.yaml applies.
# Every language code maps to "language"; non-langue domains (pymentor, …)
# map to themselves.
_LANGUAGE_CODES = {"en", "es", "it", "de", "ja", "ru"}


def load_onboarding_content(domain: str) -> dict:
    """Compile onboarding YAML for a domain code (e.g., "en", "es", "pymentor").

    Returns:
        {
          "version": str,
          "domain": str,
          "target_language": str | None,
          "language_display_fr": str | None,
          "probe": dict | None,
          "items": [<core items>, <domain items>],
        }

    The items list is the ordered union of core + domain items (order field
    respected). Overlay probe is merged into the probe item if present.
    Returns {"items": []} if domain unknown.
    """
    core = _load_onboarding_core()
    if domain in _LANGUAGE_CODES:
        overlay = _load_onboarding_overlay(domain)
        domain_kind = overlay.get("domain") or "language"
        dom = _load_onboarding_domain(domain_kind)
        target_language = overlay.get("language_code", domain)
        language_display_fr = overlay.get("language_display_fr")
        probe = overlay.get("probe")
    else:
        overlay = {}
        dom = _load_onboarding_domain(domain)
        target_language = None
        language_display_fr = None
        probe = None

    core_items = list(core.get("items", []))
    domain_items = list(dom.get("items", []))
    all_items = sorted(core_items + domain_items, key=lambda it: it.get("order", 0))

    # Inject language_display_fr placeholder rendering for language items
    if language_display_fr:
        for it in all_items:
            if "prompt" in it and isinstance(it["prompt"].get("fr"), str):
                it["prompt"]["fr"] = it["prompt"]["fr"].replace(
                    "{{language_display_fr}}", language_display_fr
                )
            if "prompt_group" in it and isinstance(it["prompt_group"].get("fr"), str):
                it["prompt_group"]["fr"] = it["prompt_group"]["fr"].replace(
                    "{{language_display_fr}}", language_display_fr
                )

    return {
        "version": core.get("version", "1.0.0"),
        "domain": domain,
        "target_language": target_language,
        "language_display_fr": language_display_fr,
        "probe": probe,
        "items": all_items,
    }
