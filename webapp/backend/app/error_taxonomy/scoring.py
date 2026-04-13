"""
AcademIA Error Taxonomy — Scoring engine (Phase 2)
Aggregates error_log by family, applies tolerance matrix, produces error profiles.
"""

import yaml
import logging
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger("academie-api.scoring")

# Load tolerance matrix at module level
_MATRIX_PATH = Path(__file__).parent.parent / "config" / "tolerance_matrix.yaml"
_matrix = None


def _load_matrix():
    global _matrix
    if _matrix is None:
        with open(_MATRIX_PATH) as f:
            _matrix = yaml.safe_load(f)
    return _matrix


def get_family_for_code(error_code: str) -> str | None:
    """Map a detection code to its family key. Returns None if unknown."""
    m = _load_matrix()
    for family_key, family_def in m["families"].items():
        if error_code in family_def["codes"]:
            return family_key
    return None


def get_band_for_level(niveau_global: str) -> str:
    """Map CEFR level string to band. Defaults to intermediate."""
    m = _load_matrix()
    bands = m["cefr_bands"]
    # Handle variations: "B1", "b1", "B1+", etc.
    level = niveau_global.strip().upper().rstrip("+")
    return bands.get(level, "intermediate")


def compute_error_profile(error_rows: list[dict], niveau_global: str) -> dict:
    """
    Compute error profile from raw error_log rows.

    Args:
        error_rows: list of dicts with keys: error_code, turn_number, session_id
        niveau_global: CEFR level string (e.g. "B1")

    Returns:
        {
            "band": "intermediate",
            "niveau": "B1",
            "families": {
                "verb_tense": {
                    "label": "Temps & conjugaison",
                    "count": 12,
                    "tier": "noted",
                    "weight": 0.3,
                    "score": 3.6,
                    "feedback": "À travailler",
                    "color": "orange",
                    "mode": "active",
                    "top_codes": [("V:TENSE", 8), ("V:SVA", 3), ("V:FORM", 1)]
                },
                ...
            },
            "summary": {
                "total_errors": 45,
                "active_errors": 38,
                "shadow_errors": 7,
                "sessions_analyzed": 5,
                "high_priority": ["verb_tense", "word_order"],
                "work_on": ["noun_det", "pronoun"],
                "normal": ["sentence", "morphology", "surface"]
            }
        }
    """
    m = _load_matrix()
    band = get_band_for_level(niveau_global)
    weights = m["weights"]
    max_per_turn = m.get("max_errors_per_turn", 3)

    # Aggregate errors by family
    family_counts = defaultdict(lambda: defaultdict(int))
    sessions = set()
    turn_error_count = defaultdict(int)  # (session_id, turn) → count

    for row in error_rows:
        code = row["error_code"]
        session_id = row.get("session_id", "")
        turn = row.get("turn_number", 0)
        sessions.add(session_id)

        # Apply max errors per turn cap
        turn_key = (session_id, turn)
        if turn_error_count[turn_key] >= max_per_turn:
            continue
        turn_error_count[turn_key] += 1

        family_key = get_family_for_code(code)
        if family_key:
            family_counts[family_key][code] += 1

    # Build profile per family
    families_result = {}
    high_priority = []
    work_on = []
    normal = []
    total_errors = 0
    active_errors = 0
    shadow_errors = 0

    for family_key, family_def in m["families"].items():
        counts = family_counts.get(family_key, {})
        count = sum(counts.values())
        total_errors += count

        mode = family_def["mode"]
        tier = m["matrix"][family_key][band]
        weight = weights.get(tier, 0.0)
        score = round(count * weight, 1)

        # Top codes sorted by frequency
        top_codes = sorted(counts.items(), key=lambda x: -x[1])[:5]

        # Feedback label
        feedback_info = m["feedback_labels"].get(tier, {})
        feedback = feedback_info.get("fr", "")
        color = feedback_info.get("color", "gray")

        if mode == "shadow":
            shadow_errors += count
            feedback = ""
            color = "hidden"
        else:
            active_errors += count
            if tier == "penalized" and count > 0:
                high_priority.append(family_key)
            elif tier == "noted" and count > 0:
                work_on.append(family_key)
            elif count > 0:
                normal.append(family_key)

        families_result[family_key] = {
            "label": family_def["label"],
            "label_en": family_def["label_en"],
            "count": count,
            "tier": tier,
            "weight": weight,
            "score": score,
            "feedback": feedback,
            "color": color,
            "mode": mode,
            "top_codes": top_codes,
        }

    return {
        "band": band,
        "niveau": niveau_global,
        "families": families_result,
        "summary": {
            "total_errors": total_errors,
            "active_errors": active_errors,
            "shadow_errors": shadow_errors,
            "sessions_analyzed": len(sessions),
            "high_priority": high_priority,
            "work_on": work_on,
            "normal": normal,
        },
    }
