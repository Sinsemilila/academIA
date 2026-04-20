"""Onboarding QCM pre-chat router.

4 endpoints:
  GET  /api/onboarding/content/{domain}   — compiled YAML for modal render
  GET  /api/learner-profile/{domain}      — 404 if absent (gate modal) | 200 if present
  POST /api/learner-profile/{domain}      — submit QCM, validate, persist + derive
  PATCH /api/learner-profile/{domain}     — partial update (OLM negotiability)

Design doc : docs/00-project/onboarding-research-2026-04-20/vague2-qcm-design.md
Plan       : /root/.claude/plans/atomic-beaming-alpaca.md
"""
from __future__ import annotations

import json
import os
import re
import statistics
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from ..auth import get_current_user
from .. import database as db

router = APIRouter(tags=["onboarding"])


ENABLE_QCM_ONBOARDING = os.environ.get("ENABLE_QCM_ONBOARDING", "false").lower() in (
    "1", "true", "yes",
)

# CEFR ladder used for min/max ordering
_CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ── Pydantic schemas ─────────────────────────────────────────────────

CEFR = Literal["A1", "A2", "B1", "B2", "C1", "C2"]


class UniversalBlock(BaseModel):
    self_efficacy: int = Field(..., ge=1, le=5)
    mindset: Literal["fixed", "growth"]
    goal_text: str = Field(..., min_length=10, max_length=200)
    autonomy_pref: Literal["guided", "semi_autonomous", "autonomous"]
    engagement_pattern: Literal[
        "daily_short", "weekly_long", "opportunistic", "daily_intense"
    ]


class DomainLevelSubmit(BaseModel):
    cefr_comprehension: CEFR
    cefr_production: CEFR
    probe_answer: str | None = None  # None if user skipped or probe not shown


class DomainMotivationSubmit(BaseModel):
    ideal_l2_self_tags: list[str] = Field(..., min_length=1, max_length=2)
    fla_items_raw: dict[str, int] = Field(
        ...,
        description="Keys fla_a, fla_b, fla_c — each Likert 1-5",
    )

    @model_validator(mode="after")
    def check_fla(self):
        required = {"fla_a", "fla_b", "fla_c"}
        if set(self.fla_items_raw.keys()) != required:
            raise ValueError(f"fla_items_raw must have exactly keys {required}")
        for v in self.fla_items_raw.values():
            if not isinstance(v, int) or not (1 <= v <= 5):
                raise ValueError("fla item values must be int 1-5")
        return self


class LearnerProfileSubmit(BaseModel):
    universal_block: UniversalBlock
    domain_level: DomainLevelSubmit
    domain_motivation: DomainMotivationSubmit


class LearnerProfilePatch(BaseModel):
    """Partial update — OLM negotiability. Only CEFR for now (most likely re-adjust).

    Extendable later for the rest of the profile.
    """
    cefr_comprehension: CEFR | None = None
    cefr_production: CEFR | None = None


# ── Helpers : scoring + derivation ───────────────────────────────────

_VAGUE_VERBS = {
    "progresser", "améliorer", "ameliorer", "apprendre", "maîtriser",
    "maitriser", "parler mieux", "avancer",
}
_TEMPORAL_MARKERS = re.compile(
    r"\b(avant|en\s+\w+|d'ici|pour\s+\w+|en\s+\d+\s+mois|d'ici\s+\w+)\b",
    re.IGNORECASE,
)
_NAMED_ENTITY_HINTS = re.compile(
    r"\b(DELE|TOEFL|IELTS|Cambridge|Netflix|YouTube|VO|B2|C1|exam|examen|concours|entretien)\b",
    re.IGNORECASE,
)
_CONTEXT_WORDS = re.compile(
    r"\b(voyage|voyager|travail|boulot|études|etudes|ami|amis|famille|collègue|collegue|partenaire|boss|belle-famille)\b",
    re.IGNORECASE,
)


def _score_goal_specificity(text: str) -> int:
    """Heuristic Locke-Latham 0-3 scoring on goal text.

    0 — vague single verb ("progresser") or < 10 chars
    1 — contextual but generic ("parler avec des amis")
    2 — concrete + named entity/domain ("comprendre les séries Netflix en VO")
    3 — concrete + named entity + temporal marker
    """
    t = text.strip().lower()
    if len(t) < 10:
        return 0
    words = set(re.findall(r"[a-zà-ÿ]+", t))
    if words.issubset(_VAGUE_VERBS) or all(w in _VAGUE_VERBS for w in words if len(w) > 3):
        return 0
    has_temporal = bool(_TEMPORAL_MARKERS.search(text))
    has_entity = bool(_NAMED_ENTITY_HINTS.search(text))
    has_context = bool(_CONTEXT_WORDS.search(text))
    if has_entity and has_temporal:
        return 3
    if has_entity:
        return 2
    if has_context:
        return 1
    return 1  # default : some content but no specific marker


def _score_probe(answer: str | None, overlay_probe: dict | None) -> tuple[int, bool]:
    """Regex-based probe scoring (0-3) + confidence flag.

    Returns (score, regex_hit). If regex_hit is False and overlay has
    fallback_judge.enabled=true, caller should optionally invoke LLM judge async.
    """
    if not answer or not overlay_probe:
        return 0, False
    a = answer.strip()
    if len(a) == 0:
        return 0, False
    variants = overlay_probe.get("accepted_variants_regex") or {}
    for tier, score in [("strong", 3), ("medium", 2), ("weak", 1)]:
        pat = variants.get(tier)
        if pat and re.search(pat, a):
            return score, True
    return 0, False


def _cefr_min(a: str, b: str) -> str:
    return a if _CEFR_ORDER.index(a) < _CEFR_ORDER.index(b) else b


def _cefr_max(a: str, b: str) -> str:
    return a if _CEFR_ORDER.index(a) > _CEFR_ORDER.index(b) else b


def _cefr_step(level: str, steps: int) -> str:
    idx = _CEFR_ORDER.index(level)
    idx = max(0, min(len(_CEFR_ORDER) - 1, idx + steps))
    return _CEFR_ORDER[idx]


def _compute_fla_category(fla_score: float) -> str:
    if fla_score <= 2.33:
        return "low"
    if fla_score <= 3.66:
        return "moderate"
    return "high"


def _compute_derivations(
    submit: LearnerProfileSubmit,
    overlay_probe: dict | None,
) -> dict[str, Any]:
    """Compute all derived fields at POST time. Deterministic, side-effect-free."""
    ub = submit.universal_block
    dl = submit.domain_level
    dm = submit.domain_motivation

    goal_specificity_score = _score_goal_specificity(ub.goal_text)

    # Probe scoring
    probe_score, probe_regex_hit = _score_probe(dl.probe_answer, overlay_probe)

    # CEFR baseline and final
    cefr_baseline = _cefr_min(dl.cefr_comprehension, dl.cefr_production)
    cefr_max = _cefr_max(dl.cefr_comprehension, dl.cefr_production)
    cefr_final = cefr_baseline
    probe_flag = False
    if dl.probe_answer is not None:
        # Probe révèle sous-estimation : score 2+ malgré baseline < B1
        if probe_score >= 2 and _CEFR_ORDER.index(cefr_baseline) < _CEFR_ORDER.index("B1"):
            cefr_final = "B1"
        # Probe révèle surestimation : score ≤ 1 malgré baseline >= B2 (Dunning-Kruger)
        if probe_score <= 1 and _CEFR_ORDER.index(cefr_baseline) >= _CEFR_ORDER.index("B2"):
            cefr_final = "B1"
            probe_flag = True
    # Conservative placement : production -0.5 palier (asymétrie d'erreur)
    cefr_placement = _cefr_step(cefr_final, -1) if cefr_final != "A1" else "A1"

    # FLA
    fla_items = dm.fla_items_raw
    fla_score = round(statistics.mean(fla_items.values()), 2)
    fla_category = _compute_fla_category(fla_score)

    derived_domain_level = {
        "probe_score": probe_score,
        "probe_regex_hit": probe_regex_hit,
        "probe_flag": probe_flag,
        "cefr_baseline": cefr_baseline,
        "cefr_max": cefr_max,
        "cefr_final": cefr_final,
        "cefr_placement": cefr_placement,
    }
    derived_domain_motivation = {
        "fla_score": fla_score,
        "fla_category": fla_category,
    }
    derived_universal = {
        "goal_specificity_score": goal_specificity_score,
    }
    return {
        "universal": derived_universal,
        "domain_level": derived_domain_level,
        "domain_motivation": derived_domain_motivation,
    }


def _compute_tutor_hints(submit: LearnerProfileSubmit, derived: dict) -> dict[str, Any]:
    """Compute the 'derived_tutor_hints' used by the LLM to adapt its style."""
    ub = submit.universal_block
    fla_cat = derived["domain_motivation"]["fla_category"]
    cefr_placement = derived["domain_level"]["cefr_placement"]

    scaffolding_level = {
        (1, 2): "high",
        (3,): "medium",
        (4, 5): "low",
    }
    scaffolding = next(
        v for k, v in scaffolding_level.items() if ub.self_efficacy in k
    )
    if fla_cat == "high":
        # Boost scaffold one step up if anxious
        scaffolding = {"low": "medium", "medium": "high", "high": "high"}[scaffolding]

    feedback_framing = "growth" if ub.mindset == "growth" else "gentle"
    if fla_cat == "high":
        feedback_framing = "gentle"

    session_length_target_min = {
        "daily_short": 10,
        "weekly_long": 35,
        "opportunistic": 20,
        "daily_intense": 35,
    }[ub.engagement_pattern]

    tutor_style = {
        "guided": "prescriptive",
        "semi_autonomous": "collaborative",
        "autonomous": "adaptive",
    }[ub.autonomy_pref]

    allow_speaking_day1 = fla_cat != "high"

    return {
        "scaffolding_level": scaffolding,
        "feedback_framing": feedback_framing,
        "session_length_target_min": session_length_target_min,
        "tutor_style": tutor_style,
        "allow_speaking_day1": allow_speaking_day1,
        "cefr_placement": cefr_placement,
        "fla_category": fla_cat,
    }


def _render_nl_summary(
    submit: LearnerProfileSubmit,
    derived: dict,
    hints: dict,
    target_language_fr: str | None,
) -> str:
    """≤ 200 words FR summary for LLM system prompt injection."""
    ub = submit.universal_block
    dl = submit.domain_level
    dm = submit.domain_motivation
    lang = target_language_fr or "la langue cible"
    mindset_fr = "growth" if ub.mindset == "growth" else "fixed"
    autonomy_fr = {
        "guided": "préfère un cadre guidé",
        "semi_autonomous": "préfère un cadre semi-autonome",
        "autonomous": "préfère définir ses objectifs",
    }[ub.autonomy_pref]
    engagement_fr = {
        "daily_short": "quelques minutes par jour",
        "weekly_long": "sessions longues 2-3 fois par semaine",
        "opportunistic": "1-2 fois par semaine",
        "daily_intense": "tous les jours 30 min+",
    }[ub.engagement_pattern]
    tags_fr = ", ".join(dm.ideal_l2_self_tags)
    fla_cat = derived["domain_motivation"]["fla_category"]
    cefr_placement = derived["domain_level"]["cefr_placement"]

    return (
        f"Profil apprenant ({lang}) : niveau placement {cefr_placement} "
        f"(auto-éval compréhension {dl.cefr_comprehension}, production {dl.cefr_production}). "
        f"Objectif : {ub.goal_text!r}. "
        f"Mindset {mindset_fr}, self-efficacy {ub.self_efficacy}/5, {autonomy_fr}. "
        f"S'entraîne {engagement_fr}. "
        f"Motivation dominante : {tags_fr}. "
        f"Anxiété langagière (FLA) : {fla_cat}. "
        f"Style tuteur recommandé : scaffold={hints['scaffolding_level']}, "
        f"framing={hints['feedback_framing']}, "
        f"speaking jour 1={'OK' if hints['allow_speaking_day1'] else 'à éviter'}."
    )


# ── Endpoints ────────────────────────────────────────────────────────

def _validate_domain(domain: str) -> None:
    """Reject unknown domains early (keeps Dify/loader consistent)."""
    if not re.match(r"^[a-z]{2,16}$", domain):
        raise HTTPException(status_code=422, detail="invalid domain code")


@router.get("/api/onboarding/content/{domain}")
async def get_onboarding_content(domain: str, user: dict = Depends(get_current_user)):
    """Return the compiled YAML that drives the QCM modal render."""
    _validate_domain(domain)
    from academie_core.data.loader import load_onboarding_content
    content = load_onboarding_content(domain)
    if not content.get("items"):
        raise HTTPException(status_code=404, detail=f"No onboarding content for domain {domain!r}")
    return content


@router.get("/api/learner-profile/{domain}")
async def get_learner_profile(domain: str, user: dict = Depends(get_current_user)):
    """Return the learner's QCM profile for a domain. 404 if absent → modal gate."""
    _validate_domain(domain)
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=404, detail="No learner bound to user")
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, eleve_id, domain, target_language,
                      universal_block, domain_level, domain_motivation,
                      derived_tutor_hints, schema_version,
                      completed_at, updated_at
               FROM learner_profiles
               WHERE eleve_id = $1 AND domain = $2
               ORDER BY completed_at DESC LIMIT 1""",
            eleve_id, domain,
        )
    if not row:
        raise HTTPException(status_code=404, detail="No learner profile yet")

    def _parse(col):
        v = row[col]
        return json.loads(v) if isinstance(v, str) else v

    return {
        "id": row["id"],
        "eleve_id": row["eleve_id"],
        "domain": row["domain"],
        "target_language": row["target_language"],
        "universal_block": _parse("universal_block"),
        "domain_level": _parse("domain_level"),
        "domain_motivation": _parse("domain_motivation"),
        "derived_tutor_hints": _parse("derived_tutor_hints"),
        "schema_version": row["schema_version"],
        "completed_at": row["completed_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


@router.post("/api/learner-profile/{domain}")
async def submit_learner_profile(
    domain: str,
    payload: LearnerProfileSubmit,
    user: dict = Depends(get_current_user),
):
    """Submit QCM → validate, compute derived + tutor hints + NL summary, persist."""
    _validate_domain(domain)
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=400, detail="No learner bound to user")

    from academie_core.data.loader import load_onboarding_content
    content = load_onboarding_content(domain)
    overlay_probe = content.get("probe")
    target_language = content.get("target_language")
    target_language_fr = content.get("language_display_fr")

    derived = _compute_derivations(payload, overlay_probe)
    hints = _compute_tutor_hints(payload, derived)
    nl_summary = _render_nl_summary(payload, derived, hints, target_language_fr)

    universal_block = payload.universal_block.model_dump()
    universal_block.update(derived["universal"])

    domain_level = payload.domain_level.model_dump()
    domain_level.update(derived["domain_level"])

    domain_motivation = payload.domain_motivation.model_dump()
    domain_motivation.update(derived["domain_motivation"])

    derived_tutor_hints = dict(hints)
    derived_tutor_hints["nl_summary"] = nl_summary

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO learner_profiles
                   (eleve_id, domain, target_language,
                    universal_block, domain_level, domain_motivation,
                    derived_tutor_hints, schema_version)
               VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb, $8)
               ON CONFLICT (eleve_id, domain, target_language) DO UPDATE SET
                   universal_block = EXCLUDED.universal_block,
                   domain_level = EXCLUDED.domain_level,
                   domain_motivation = EXCLUDED.domain_motivation,
                   derived_tutor_hints = EXCLUDED.derived_tutor_hints,
                   schema_version = EXCLUDED.schema_version,
                   updated_at = NOW()
               RETURNING id, completed_at""",
            eleve_id, domain, target_language,
            json.dumps(universal_block),
            json.dumps(domain_level),
            json.dumps(domain_motivation),
            json.dumps(derived_tutor_hints),
            "v1",
        )

    return {
        "id": row["id"],
        "completed_at": row["completed_at"].isoformat(),
        "cefr_placement": hints["cefr_placement"],
        "tutor_style": hints["tutor_style"],
    }


@router.patch("/api/learner-profile/{domain}")
async def patch_learner_profile(
    domain: str,
    payload: LearnerProfilePatch,
    user: dict = Depends(get_current_user),
):
    """Partial update — OLM negotiability (user re-corrects CEFR at turn 2+)."""
    _validate_domain(domain)
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=400, detail="No learner bound to user")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="nothing to update")

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT domain_level FROM learner_profiles
               WHERE eleve_id = $1 AND domain = $2
               ORDER BY completed_at DESC LIMIT 1""",
            eleve_id, domain,
        )
        if not row:
            raise HTTPException(status_code=404, detail="No learner profile to patch")

        current = row["domain_level"]
        current = json.loads(current) if isinstance(current, str) else dict(current)
        current.update(updates)

        # Re-derive CEFR baseline/final/placement from the patched values.
        comp = current.get("cefr_comprehension")
        prod = current.get("cefr_production")
        if comp and prod:
            baseline = _cefr_min(comp, prod)
            current["cefr_baseline"] = baseline
            current["cefr_final"] = baseline  # PATCH re-trust user, skip probe re-apply
            current["cefr_placement"] = _cefr_step(baseline, -1) if baseline != "A1" else "A1"

        await conn.execute(
            """UPDATE learner_profiles
               SET domain_level = $1::jsonb, updated_at = NOW()
               WHERE eleve_id = $2 AND domain = $3""",
            json.dumps(current), eleve_id, domain,
        )
    return {"ok": True, "domain_level": current}
