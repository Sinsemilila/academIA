"""
AcademIA — Unified Progression Scoring Engine
Aggregates error_log by family, applies tolerance matrix, computes progression + recommendations.
"""

import os
import yaml
import logging
from pathlib import Path
from collections import defaultdict, Counter

logger = logging.getLogger("academie-api.scoring")

_CONFIG_DIR = Path(__file__).parent.parent / "data" / "tolerance_matrix"
_USE_V2 = os.getenv("USE_V2_TOLERANCE", "false").lower() in ("1", "true", "yes")
# Sprint 2 B2 — read tier from error_log row (v2) vs derive from matrix (v1 default).
_USE_V2_SCORING = os.getenv("USE_V2_SCORING", "false").lower() in ("1", "true", "yes")
_MATRIX_PATH = _CONFIG_DIR / ("tolerance_matrix_v2.yaml" if _USE_V2 else "tolerance_matrix.yaml")
_matrix = None


def _load_matrix():
    global _matrix
    if _matrix is None:
        with open(_MATRIX_PATH) as f:
            _matrix = yaml.safe_load(f)
        # Manual overrides (only meaningful when v2 active)
        if _USE_V2:
            ov_path = _CONFIG_DIR / "tolerance_matrix_v2_overrides.yaml"
            if ov_path.exists():
                with open(ov_path) as f:
                    ov_doc = yaml.safe_load(f) or {}
                applied = []
                for fam, bands in (ov_doc.get("overrides") or {}).items():
                    if fam in _matrix.get("matrix", {}):
                        _matrix["matrix"][fam].update(bands)
                        applied.append(f"{fam}={bands}")
                if applied:
                    logger.info("Applied %d overrides from %s: %s",
                                len(applied), ov_path.name, applied)
        logger.info(
            "Loaded tolerance matrix: %s (v2=%s)",
            _MATRIX_PATH.name, _USE_V2,
        )
    return _matrix


def get_family_for_code(error_code: str) -> str | None:
    m = _load_matrix()
    for family_key, family_def in m["families"].items():
        if error_code in family_def["codes"]:
            return family_key
    return None


def get_band_for_level(niveau_global: str) -> str:
    m = _load_matrix()
    level = niveau_global.strip().upper().rstrip("+")
    return m["cefr_bands"].get(level, "intermediate")


def get_code_label(code: str) -> str:
    m = _load_matrix()
    return m.get("code_labels", {}).get(code, code)


def get_concept_label(concept: str) -> str:
    m = _load_matrix()
    return m.get("concept_labels", {}).get(concept, concept.replace("_", " ").title())


def get_concept_family(concept: str) -> str | None:
    m = _load_matrix()
    return m.get("concept_families", {}).get(concept)


# ── Sprint 2 Phase B2 — error_log v2 fields enrichment ──

# Map v1 tier vocabulary to T-codes used in DB CHECK constraint (T0..T4).
_TIER_LABEL_TO_CODE = {
    "ignored": "T1",
    "noted": "T2",
    "penalized": "T3",
    "regressive": "T4",
    "shadow": "T0",
}
_TIER_CODE_TO_LABEL = {v: k for k, v in _TIER_LABEL_TO_CODE.items()}

_NULL_ENRICHMENT = {
    "tier": None,
    "gravity_linguistic": None,
    "gravity_communicative": None,
    "gravity_social": None,
    "criterial_level_emergence": None,
    "criterial_level_mastery": None,
}


def enrich_error_fields(error_code: str, niveau_global: str | None) -> dict:
    """Compute v2 fields (tier, gravity, criterial) for one error occurrence.

    Used by error_analysis_router to populate error_log columns added in
    Sprint 2 Phase A. Pure deterministic lookup against the loaded matrix
    (override applied automatically when v2 active).

    Returns a dict matching error_log v2 column names. Values may be None
    if the family is unknown or yaml sections missing.
    """
    m = _load_matrix()
    fam = get_family_for_code(error_code)
    if not fam:
        return dict(_NULL_ENRICHMENT)
    band = get_band_for_level(niveau_global or "B1")
    tier_label = m.get("matrix", {}).get(fam, {}).get(band, "ignored")
    tier_code = _TIER_LABEL_TO_CODE.get(tier_label)
    gravity = m.get("gravity_per_family", {}).get(fam, {})
    criterial = m.get("criterial_per_family", {}).get(fam, {})
    return {
        "tier": tier_code,
        "gravity_linguistic": gravity.get("linguistic"),
        "gravity_communicative": gravity.get("communicative"),
        "gravity_social": gravity.get("social"),
        "criterial_level_emergence": criterial.get("emergence"),
        "criterial_level_mastery": criterial.get("mastery"),
    }


def compute_error_profile(error_rows: list[dict], niveau_global: str,
                          concept_keys: list[str] | None = None,
                          scores_confiance: dict | None = None) -> dict:
    """
    Compute unified error profile with progression.

    Args:
        error_rows: list of dicts with keys: error_code, turn_number, session_id
        niveau_global: CEFR level string (e.g. "B1")
        concept_keys: list of concept keys for the current level (from curriculums table)
        scores_confiance: optional per-concept scores from profils_eleves (n8n LLM eval)

    Returns complete profile with families, progression, and recommendation.
    """
    m = _load_matrix()
    band = get_band_for_level(niveau_global)
    weights = m["weights"]
    prog = m.get("progression", {})
    max_per_turn = prog.get("max_errors_per_turn", 3)
    max_error_rate = prog.get("max_error_rate", 1.0)
    min_sessions = prog.get("min_sessions", 5)
    # ── Aggregate errors by family + concept ──
    family_errors = defaultdict(lambda: defaultdict(int))   # family → {code: count}
    family_sessions = defaultdict(set)                       # family → set of session_ids
    family_tier_codes = defaultdict(list)                    # family → [stored T-codes] (v2)
    concept_errors_direct = defaultdict(int)                 # concept_key → error count (turn-capped)
    concept_sessions_direct = defaultdict(set)               # concept_key → set of session_ids
    all_sessions = set()
    turn_cap = defaultdict(int)

    for row in error_rows:
        code = row["error_code"]
        session_id = row.get("session_id", "")
        turn = row.get("turn_number", 0)
        all_sessions.add(session_id)

        turn_key = (session_id, turn)
        if turn_cap[turn_key] >= max_per_turn:
            continue
        turn_cap[turn_key] += 1

        family_key = get_family_for_code(code)
        if family_key:
            family_errors[family_key][code] += 1
            family_sessions[family_key].add(session_id)
            stored_tier = row.get("tier")
            if stored_tier:
                family_tier_codes[family_key].append(stored_tier)

        # session_id format: "Q3/10:concept_key:MODE" — extract concept
        parts = session_id.split(":")
        if len(parts) >= 3:
            concept_key = parts[1]
            concept_errors_direct[concept_key] += 1
            concept_sessions_direct[concept_key].add(session_id)

    total_sessions = len(all_sessions)

    # ── Build family profiles ──
    families_result = {}
    total_errors = 0
    active_errors = 0
    shadow_errors = 0
    penalized_families = []
    penalized_clean = []

    for family_key, family_def in m["families"].items():
        codes_counts = family_errors.get(family_key, {})
        count = sum(codes_counts.values())
        total_errors += count

        mode = family_def["mode"]
        tier = m["matrix"][family_key][band]
        # Sprint 2 B3 — when flag active, prefer the tier stored on error_log rows
        # (enriched at insert time). Majority wins; fall back to matrix lookup if
        # no rows carried a tier (e.g. legacy rows pre-backfill or NULL tiers).
        if _USE_V2_SCORING:
            stored = family_tier_codes.get(family_key)
            if stored:
                top_code = Counter(stored).most_common(1)[0][0]
                tier = _TIER_CODE_TO_LABEL.get(top_code, tier)
        weight = weights.get(tier, 0.0)

        sessions_appeared = len(family_sessions.get(family_key, set()))
        error_rate = count / sessions_appeared if sessions_appeared > 0 else 0.0
        is_clean = error_rate <= max_error_rate and sessions_appeared >= min_sessions

        # Top codes with human labels
        top_codes = []
        for code, cnt in sorted(codes_counts.items(), key=lambda x: -x[1])[:5]:
            top_codes.append({
                "code": code,
                "label": get_code_label(code),
                "count": cnt,
            })

        # Feedback
        feedback_info = m["feedback_labels"].get(tier, {})
        feedback = feedback_info.get("fr", "")
        color = feedback_info.get("color", "gray")

        # Shadow = either mode is shadow OR tier is shadow at this band
        is_shadow = (mode == "shadow") or (tier == "shadow")

        if is_shadow:
            shadow_errors += count
            feedback = ""
            color = "hidden"
        else:
            active_errors += count
            # Track families that matter for progression (noted or penalized)
            if tier in ("penalized", "noted"):
                penalized_families.append(family_key)
                if is_clean:
                    penalized_clean.append(family_key)

        families_result[family_key] = {
            "label": family_def["label"],
            "label_en": family_def["label_en"],
            "count": count,
            "tier": tier,
            "weight": weight,
            "error_rate": round(error_rate, 2),
            "sessions_appeared": sessions_appeared,
            "is_clean": is_clean,
            "feedback": feedback,
            "color": color,
            "mode": "shadow" if is_shadow else "active",
            "top_codes": top_codes,
        }

    # ── Progression ──
    # Exam eligibility: all tracked families clean + enough sessions
    eligible_for_exam = (
        len(penalized_families) > 0
        and len(penalized_clean) == len(penalized_families)
        and total_sessions >= min_sessions
    )

    # Progress bar: scores_confiance (n8n LLM) primary, error-profile fallback
    concept_scores = []
    concept_scores_map = {}  # concept_key → score (exposed in return)
    sc = scores_confiance or {}
    if concept_keys:
        for ck in concept_keys:
            # Primary: scores_confiance from n8n LLM evaluation
            sc_entry = sc.get(ck)
            if isinstance(sc_entry, dict) and "score" in sc_entry:
                score = sc_entry["score"]
            else:
                # Fallback: error-based scoring (session_id concept data or family)
                score = _score_concept(
                    ck, concept_errors_direct, concept_sessions_direct,
                    families_result, max_error_rate, min_sessions,
                )
            concept_scores.append(score)
            concept_scores_map[ck] = score

    total_concepts = len(concept_scores) or 1
    progress_pct = round(sum(concept_scores) / total_concepts)

    # For beginner band (A1-A2): if no tracked families, base eligibility on sessions
    if band == "beginner" and not penalized_families:
        eligible_for_exam = total_sessions >= min_sessions

    # ── Concepts for current level ──
    concepts_by_family = defaultdict(list)
    if concept_keys:
        for ck in concept_keys:
            fam = get_concept_family(ck)
            if fam:
                concepts_by_family[fam].append({
                    "key": ck,
                    "label": get_concept_label(ck),
                    "family": fam,
                })

    # ── Recommendation ──
    recommendation = _compute_recommendation(
        families_result, penalized_families, penalized_clean,
        total_sessions, min_sessions, eligible_for_exam, niveau_global
    )

    # ── Build summary lists ──
    high_priority = [fk for fk in penalized_families if not families_result[fk]["is_clean"] and families_result[fk]["count"] > 0]
    work_on = [fk for fk, fd in families_result.items() if fd["mode"] == "active" and fd["tier"] == "noted" and fd["count"] > 0]
    normal = [fk for fk, fd in families_result.items() if fd["mode"] == "active" and fd["tier"] == "ignored" and fd["count"] > 0]

    return {
        "band": band,
        "niveau": niveau_global,
        "families": families_result,
        "concepts_by_family": dict(concepts_by_family),
        "concept_scores": concept_scores_map,
        "progression": {
            "progress_pct": progress_pct,
            "penalized_total": len(penalized_families),
            "penalized_clean": len(penalized_clean),
            "eligible_for_exam": eligible_for_exam,
            "sessions_total": total_sessions,
            "sessions_required": min_sessions,
        },
        "recommendation": recommendation,
        "summary": {
            "total_errors": total_errors,
            "active_errors": active_errors,
            "shadow_errors": shadow_errors,
            "sessions_analyzed": total_sessions,
            "high_priority": high_priority,
            "work_on": work_on,
            "normal": normal,
        },
    }


def _score_concept(
    concept_key: str,
    concept_errors_direct: dict,
    concept_sessions_direct: dict,
    families_result: dict,
    max_error_rate: float,
    min_sessions: int,
) -> int:
    """Score a single concept: per-concept data first, family fallback."""
    sessions = concept_sessions_direct.get(concept_key, set())
    if sessions:
        n_sessions = len(sessions)
        n_errors = concept_errors_direct.get(concept_key, 0)
        error_rate = n_errors / n_sessions
        is_clean = error_rate <= max_error_rate and n_sessions >= min_sessions
        if is_clean:
            return 85
        elif error_rate <= 1.5:
            return 60
        else:
            return 30
    # Fallback: family-level
    fam_key = get_concept_family(concept_key)
    if fam_key and fam_key in families_result:
        fam = families_result[fam_key]
        if fam.get("is_clean") and fam.get("sessions_appeared", 0) >= min_sessions:
            return 85
        elif fam.get("count", 0) > 0 and fam.get("error_rate", 0) <= 1.5:
            return 60
        elif fam.get("count", 0) > 0:
            return 30
        elif fam.get("sessions_appeared", 0) > 0:
            return 70
    return 0


def _compute_recommendation(
    families: dict, penalized: list, penalized_clean: list,
    total_sessions: int, min_sessions: int,
    eligible: bool, niveau: str,
) -> dict:
    """Priority-based recommendation for the student."""
    level_order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    niveau_upper = niveau.strip().upper().rstrip("+")
    next_level = None
    if niveau_upper in level_order:
        idx = level_order.index(niveau_upper)
        if idx < len(level_order) - 1:
            next_level = level_order[idx + 1]

    # 1. Exam eligible
    if eligible and next_level:
        return {
            "type": "exam",
            "message": f"Tous les modules prioritaires sont maîtrisés. Prêt pour l'examen {next_level} ?",
            "action": "/chat/teacher",
            "label": "Passer l'examen",
        }

    # 2. High priority — penalized family with high error rate
    not_clean = [fk for fk in penalized if fk not in penalized_clean]
    for fk in not_clean:
        fam = families[fk]
        if fam["count"] > 0:
            return {
                "type": "weakness",
                "message": f"Focus recommandé : {fam['label']} ({fam['count']} erreurs, {fam['error_rate']}/session)",
                "action": "/chat/teacher",
                "label": "Travailler ce module",
            }

    # 3. Explore — penalized family not seen enough (anti-avoidance)
    for fk in penalized:
        fam = families[fk]
        if fam["sessions_appeared"] < min_sessions:
            return {
                "type": "explore",
                "message": f"Pratique davantage : {fam['label']} (vu dans {fam['sessions_appeared']}/{min_sessions} sessions)",
                "action": "/chat/teacher",
                "label": "Pratiquer",
            }

    # 4. Work on — noted families with errors
    for fk, fam in families.items():
        if fam["tier"] == "noted" and fam["count"] > 0 and fam["mode"] == "active":
            return {
                "type": "improve",
                "message": f"Continue à travailler : {fam['label']}",
                "action": "/chat/teacher",
                "label": "Continuer",
            }

    # 5. Default
    return {
        "type": "continue",
        "message": "Tu progresses bien, continue !",
        "action": "/chat/teacher",
        "label": "Continuer",
    }
