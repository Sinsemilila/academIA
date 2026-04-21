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
    # Session 37 extensions (default values = no-op for backward compat)
    scaffolding_intensity: Literal["low", "medium", "high"] = "medium"
    prefer_written_first: bool = False     # fla_a (speaking) high → prefer written tasks
    no_explicit_correction: bool = False   # fla_b (mockery) high → recast only, no "wrong"
    provide_chunks_ahead: bool = False     # fla_c (freeze) high → pre-chunk memorable forms


# Base matrix — (cefr_band, distance) → PolicyRow. FLA=low baseline.
# FLA=high applies a distance-shift (close→medium, medium→distant)
# via `_shift_distance_for_fla` before lookup.
_L1_USES_MINIMAL = ("meta_instructions", "brief_gloss_new_item")
_L1_USES_MEDIUM = ("meta_instructions", "brief_gloss_new_item", "grammar_explanation")
_L1_USES_FULL = ("meta_instructions", "brief_gloss_new_item",
                 "grammar_explanation", "reassurance", "cultural_note")

POLICY_MATRIX: dict[tuple[CefrBand, Distance], PolicyRow] = {
    # A1 strict — L1 scaffolding increases with distance (intensity high)
    ("A1", "close"):   PolicyRow(90, _L1_USES_MINIMAL, sandwich=True,  reassurance_l1=False, scaffolding_intensity="high"),
    ("A1", "medium"):  PolicyRow(85, _L1_USES_MEDIUM,  sandwich=True,  reassurance_l1=False, scaffolding_intensity="high"),
    ("A1", "distant"): PolicyRow(55, _L1_USES_FULL,    sandwich=True,  reassurance_l1=True,  scaffolding_intensity="high"),
    # A2 — lighter scaffolding (intensity medium)
    ("A2", "close"):   PolicyRow(95, (),               sandwich=False, reassurance_l1=False, scaffolding_intensity="medium"),
    ("A2", "medium"):  PolicyRow(90, _L1_USES_MINIMAL, sandwich=True,  reassurance_l1=False, scaffolding_intensity="medium"),
    ("A2", "distant"): PolicyRow(80, _L1_USES_MEDIUM,  sandwich=True,  reassurance_l1=False, scaffolding_intensity="medium"),
    # B1+ — essentially L2-only (intensity low)
    ("B1+", "close"):   PolicyRow(100, (),               sandwich=False, reassurance_l1=False, scaffolding_intensity="low"),
    ("B1+", "medium"):  PolicyRow(100, (),               sandwich=False, reassurance_l1=False, scaffolding_intensity="low"),
    ("B1+", "distant"): PolicyRow(95, _L1_USES_MINIMAL, sandwich=False, reassurance_l1=False, scaffolding_intensity="low"),
}

# Intensity ladder for shift operations (Fix 3A)
_INTENSITY_LADDER = ["low", "medium", "high"]


def _shift_intensity(current: str, delta: int) -> str:
    idx = _INTENSITY_LADDER.index(current) if current in _INTENSITY_LADDER else 1
    idx = max(0, min(len(_INTENSITY_LADDER) - 1, idx + delta))
    return _INTENSITY_LADDER[idx]


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


def resolve_policy(
    cefr_placement: str,
    distance: Distance,
    fla: FlaBand,
    *,
    self_efficacy: int | None = None,
    autonomy_pref: str | None = None,
    fla_items_raw: dict[str, int] | None = None,
) -> PolicyRow:
    """Resolve policy cell. Session 37 extends with self_efficacy + autonomy_pref
    (for intensity shift) and fla_items_raw (for granular pedagogical flags).

    Backward-compatible: all new kwargs are optional. Called without them,
    returns the pure CEFR × distance × FLA policy as before.
    """
    band = _band_cefr(cefr_placement)
    effective_distance = _shift_distance_for_fla(distance, fla)
    base = POLICY_MATRIX[(band, effective_distance)]

    # Intensity shift from self_efficacy + autonomy_pref
    intensity = base.scaffolding_intensity
    if self_efficacy is not None:
        if self_efficacy <= 2:
            intensity = _shift_intensity(intensity, +1)
        elif self_efficacy >= 4 and autonomy_pref == "autonomous":
            intensity = _shift_intensity(intensity, -1)

    # Granular FLA item flags
    items = fla_items_raw or {}
    prefer_written  = int(items.get("fla_a", 0) or 0) >= 4
    no_correction   = int(items.get("fla_b", 0) or 0) >= 4
    provide_chunks  = int(items.get("fla_c", 0) or 0) >= 4

    return PolicyRow(
        l2_ratio_pct=base.l2_ratio_pct,
        l1_uses=base.l1_uses,
        sandwich=base.sandwich,
        reassurance_l1=base.reassurance_l1,
        scaffolding_intensity=intensity,
        prefer_written_first=prefer_written,
        no_explicit_correction=no_correction,
        provide_chunks_ahead=provide_chunks,
    )


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
    *,
    self_efficacy: int | None = None,
    autonomy_pref: str | None = None,
    fla_items_raw: dict[str, int] | None = None,
) -> str:
    """Render the L1/L2 + anxiety-routing policy directive.

    Session 37: accepts self_efficacy/autonomy_pref/fla_items_raw for fine-grained
    intensity shifts and per-item pedagogical flags. All optional — called without
    them, behavior is identical to Session 35.

    Returns empty string when policy is a pure 100%-L2 no-op AND no anxiety flags.
    """
    try:
        policy = resolve_policy(
            cefr_placement, distance, fla,
            self_efficacy=self_efficacy,
            autonomy_pref=autonomy_pref,
            fla_items_raw=fla_items_raw,
        )
    except KeyError:
        return ""

    # Pure no-op: 100% L2 + no L1 uses + no anxiety flags
    anxiety_flags = (policy.prefer_written_first or policy.no_explicit_correction
                     or policy.provide_chunks_ahead)
    if policy.l2_ratio_pct >= 100 and not policy.l1_uses and not anxiety_flags:
        return ""

    lines = [
        "=== L1/L2 MIX POLICY (this turn) ===",
        f"Target output ratio: ~{policy.l2_ratio_pct}% {target_lang_name}"
        f" / ~{100 - policy.l2_ratio_pct}% {l1_name}.",
        f"Scaffolding intensity: {policy.scaffolding_intensity}.",
    ]

    if policy.l1_uses:
        lines.append(f"Use {l1_name} ONLY for:")
        for use in policy.l1_uses:
            lines.append(f"  - {_L1_USE_LABELS.get(use, use)}")
    elif policy.l2_ratio_pct >= 100:
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

    # Session 37 — per-item FLA pedagogical routing
    if anxiety_flags:
        lines.append("")
        lines.append("=== ANXIETY ROUTING (per-item FLA signals) ===")
        if policy.prefer_written_first:
            lines.append(
                "• Stress élevé sur le speaking à froid (fla_a ≥ 4) → privilégie"
                " d'abord des tâches écrites ou des chunks préparés avant toute"
                " production orale. Évite de demander 'dis-moi à l'oral…' les"
                " premiers turns."
            )
        if policy.no_explicit_correction:
            lines.append(
                "• Peur forte des corrections publiques (fla_b ≥ 4) → uniquement"
                " des recasts implicites, jamais de 'non, c'est X' ou 'tu as fait"
                " une erreur'. Reformule l'énoncé correct sans étiqueter l'erreur."
            )
        if policy.provide_chunks_ahead:
            lines.append(
                "• Freeze mémoriel sous pression (fla_c ≥ 4) → fournis des chunks"
                " complets utilisables tels quels (ex: 'tu peux dire : ___')"
                " plutôt que de demander la production ex nihilo. Réduis la"
                " charge mnésique."
            )

    lines.append("")
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
