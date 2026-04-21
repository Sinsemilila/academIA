"""L1/L2 scaffolding policy — level × typological-distance × FLA.

Implements the matrix documented in
`docs/01-pedagogy/l1-l2-scaffolding-policy.md`.

Grounded in Butzkamm & Caldwell 2009 (bilingual principle, sandwich technique),
Cook 2001, Macaro "optimal position" 2005, Hall & Cook 2012, Ringbom 2007,
and the CEFR 2020 Companion Volume's plurilingual turn.

Output: a short directive block injected as Dify Start input
`scaffolding_block`, referenced in llm_onboarding/llm_session prompts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .typological_distance import Distance

CefrBand = Literal["A1", "A2", "B1+"]
FlaBand = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class PolicyRow:
    l2_ratio_pct: int          # target percentage of L2 output
    l1_uses: tuple[str, ...]   # permitted L1 functions (empty = L2 only)
    sandwich: bool             # use Butzkamm sandwich on new items
    reassurance_l1: bool       # allow 1 L1 reassurance sentence turn 1


# Base matrix — (cefr_band, distance) → PolicyRow. FLA=low baseline.
# FLA=high applies a distance-shift (close→medium, medium→distant)
# via `_shift_distance_for_fla` before lookup.
_L1_USES_MINIMAL = ("meta_instructions", "brief_gloss_new_item")
_L1_USES_MEDIUM = ("meta_instructions", "brief_gloss_new_item", "grammar_explanation")
_L1_USES_FULL = ("meta_instructions", "brief_gloss_new_item",
                 "grammar_explanation", "reassurance", "cultural_note")

POLICY_MATRIX: dict[tuple[CefrBand, Distance], PolicyRow] = {
    # A1 strict — L1 scaffolding increases with distance
    ("A1", "close"):   PolicyRow(90, _L1_USES_MINIMAL, sandwich=True,  reassurance_l1=False),
    ("A1", "medium"):  PolicyRow(85, _L1_USES_MEDIUM,  sandwich=True,  reassurance_l1=False),
    ("A1", "distant"): PolicyRow(55, _L1_USES_FULL,    sandwich=True,  reassurance_l1=True),
    # A2 — lighter scaffolding
    ("A2", "close"):   PolicyRow(95, (),                           sandwich=False, reassurance_l1=False),
    ("A2", "medium"):  PolicyRow(90, _L1_USES_MINIMAL,            sandwich=True,  reassurance_l1=False),
    ("A2", "distant"): PolicyRow(80, _L1_USES_MEDIUM,             sandwich=True,  reassurance_l1=False),
    # B1+ — essentially L2-only, except JP/RU/AR still need occasional gloss
    ("B1+", "close"):   PolicyRow(100, (),                sandwich=False, reassurance_l1=False),
    ("B1+", "medium"):  PolicyRow(100, (),                sandwich=False, reassurance_l1=False),
    ("B1+", "distant"): PolicyRow(95, _L1_USES_MINIMAL,  sandwich=False, reassurance_l1=False),
}


def _band_cefr(cefr_placement: str) -> CefrBand:
    """Collapse A1/A1+/A2/A2+/B1/B1+/B2/C1/C2 into 3 bands."""
    lvl = (cefr_placement or "").upper().strip()
    if lvl in ("A1", "A1+"):
        return "A1"
    if lvl in ("A2", "A2+"):
        return "A2"
    return "B1+"


def _shift_distance_for_fla(distance: Distance, fla: FlaBand) -> Distance:
    """FLA high → more L1 scaffolding (shift +1 band)."""
    if fla != "high":
        return distance
    return {"close": "medium", "medium": "distant", "distant": "distant"}[distance]


def resolve_policy(cefr_placement: str, distance: Distance, fla: FlaBand) -> PolicyRow:
    band = _band_cefr(cefr_placement)
    effective_distance = _shift_distance_for_fla(distance, fla)
    return POLICY_MATRIX[(band, effective_distance)]


# Human-readable L1 use descriptions (rendered into the prompt block)
_L1_USE_LABELS = {
    "meta_instructions": "task instructions (e.g. 'your turn: write a sentence describing…')",
    "brief_gloss_new_item": "brief gloss on a brand-new vocab/grammar item the learner has not yet seen",
    "grammar_explanation": "grammar explanation when L2-only explanation would be unclear",
    "reassurance": "affective reassurance (e.g. 'on y va tranquille, pas de stress')",
    "cultural_note": "short cultural note when indispensable for comprehension",
}


def build_scaffolding_block(
    cefr_placement: str,
    distance: Distance,
    fla: FlaBand,
    target_lang_name: str,
    l1_name: str = "français",
    turn_count: int = 1,
) -> str:
    """Render the L1/L2 policy directive injected into the LLM prompt.

    Empty string when the effective policy is 100% L2 (no-op block).
    Falls back to an empty string defensively on unknown inputs.
    """
    try:
        policy = resolve_policy(cefr_placement, distance, fla)
    except KeyError:
        return ""

    # 100% L2 no-op
    if policy.l2_ratio_pct >= 100 and not policy.l1_uses:
        return ""

    lines = [
        "=== L1/L2 MIX POLICY (this turn) ===",
        f"Target output ratio: ~{policy.l2_ratio_pct}% {target_lang_name}"
        f" / ~{100 - policy.l2_ratio_pct}% {l1_name}.",
    ]

    if policy.l1_uses:
        lines.append(f"Use {l1_name} ONLY for:")
        for use in policy.l1_uses:
            lines.append(f"  - {_L1_USE_LABELS.get(use, use)}")
    else:
        lines.append(f"Do not use {l1_name} in your reply.")

    if policy.sandwich and turn_count <= 6:
        lines.extend([
            "",
            f"SANDWICH technique (Butzkamm) when introducing anything brand-new:",
            f"  1) say it in {target_lang_name},",
            f"  2) add a short {l1_name} gloss between parentheses,",
            f"  3) repeat it in {target_lang_name}.",
            "This preserves L2 exposure while guaranteeing comprehension.",
        ])

    if policy.reassurance_l1 and turn_count <= 2:
        lines.extend([
            "",
            f"This turn, you MAY open with one short {l1_name} sentence of reassurance"
            f" before the first {target_lang_name} utterance.",
        ])

    lines.append(
        f"NEVER use {l1_name} for greetings, small talk, or items the learner"
        " already encountered.")
    lines.append("=== END L1/L2 MIX POLICY ===")
    return "\n".join(lines)


def _normalize_fla(raw: str | None) -> FlaBand:
    v = (raw or "").lower().strip()
    if v in ("low", "medium", "high"):
        return v  # type: ignore[return-value]
    return "medium"
