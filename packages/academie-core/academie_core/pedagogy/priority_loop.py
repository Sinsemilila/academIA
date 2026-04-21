"""Priority concept selection for proactive coverage (Session 37).

Given a learner's `scores_confiance` (per-concept {score, last_seen, days_seen})
+ the curriculum `concept_keys` + `concept_weights`, compute the top-N concepts
the tutor should re-surface in the coming turns.

Priority formula (Ebbinghaus-inspired forgetting curve × pedagogical weight) :

    priority(c) = weight_norm(c) × time_factor(c) × deficit(c)

where :

    weight_norm(c)  = concept_weights[c] / max(concept_weights)  (0..1)
                      fallback 0.5 if c has no weight
    time_factor(c)  = 1 + sqrt(days_since_last_seen / 7)
                      = 1.0    when last_seen is today or None (untested)
                      = 2.0    at J+7
                      = 3.0    at J+28
                      ≈ 4.78   at J+100 (asymptotic growth)
    deficit(c)      = (100 - score) / 100   (0..1, max for untested)

Grounded in Ebbinghaus 1885 forgetting curve + Cepeda et al. 2006 spacing
effect literature. Differs from `spaced_retrieval_queue` (error-driven J+1)
by being coverage-driven : concepts that get stale without being errored
still resurface, which the spaced_retrieval system misses.

This helper is language-agnostic — same formula for Teacher EN, Maestro ES,
future Wave 2-4 agents. Per-L1 presentation lives downstream in
teacher_prompt.build_priority_concepts_block().
"""
from __future__ import annotations

import math
from datetime import date
from typing import TypedDict


class PriorityConcept(TypedDict):
    concept_key: str
    priority_score: float        # 0..~2.5, higher = more urgent
    score: int                    # 0..100 from scores_confiance (0 for untested)
    days_since_last_seen: int | None  # None if never seen
    weight: int                   # minutes from concept_weights, 0 if missing
    reason: str                   # human-readable short explanation


def _days_since(last_seen: str | None, today: date) -> int | None:
    """Parse ISO date string, return days elapsed. None if input is None/invalid."""
    if not last_seen:
        return None
    try:
        last = date.fromisoformat(str(last_seen)[:10])
        return max(0, (today - last).days)
    except (ValueError, TypeError):
        return None


def _time_factor(days: int | None) -> float:
    """Ebbinghaus-like time urgency multiplier. Concepts unseen longer weigh more."""
    if days is None or days <= 0:
        return 1.0
    return 1.0 + math.sqrt(days / 7.0)


def _build_reason(
    score: int, days: int | None, weight: int, weight_norm: float,
) -> str:
    """Concise human-readable explanation for the priority ranking."""
    bits = []
    if days is None:
        bits.append("pas encore vu")
    elif days == 0:
        bits.append("vu aujourd'hui")
    elif days == 1:
        bits.append("vu hier")
    elif days >= 14:
        bits.append(f"pas revu depuis {days} jours")
    else:
        bits.append(f"{days}j depuis la dernière revue")
    if score == 0 and days is not None:
        bits.append("score 0")
    elif 0 < score < 50:
        bits.append(f"score faible {score}/100")
    elif 50 <= score < 80:
        bits.append(f"score médian {score}/100")
    if weight >= 8:
        bits.append("concept central")
    elif weight_norm == 0.5 and weight == 0:
        bits.append("poids non défini")
    return ", ".join(bits) or "à re-travailler"


def compute_priority_concepts(
    scores_confiance: dict,
    concept_keys: list[str],
    concept_weights: dict,
    today: date | None = None,
    limit: int = 3,
) -> list[PriorityConcept]:
    """Return up to `limit` highest-priority concepts for the tutor to re-surface.

    Args :
      scores_confiance : {concept: {"score": int, "last_seen": iso, "days_seen": int}}
      concept_keys : canonical list from curriculums for the learner's niveau.
      concept_weights : {concept: minutes} from curriculums.
      today : override for reproducible tests.
      limit : default 3 — cap what we show to the LLM (don't overwhelm).

    Returns : list of PriorityConcept sorted DESC by priority_score.
    Empty if concept_keys is empty.
    """
    if not concept_keys:
        return []
    today = today or date.today()

    # Normalize weights : 0..1 scale. Default 0.5 if weight missing.
    max_w = max((int(v) for v in concept_weights.values() if isinstance(v, (int, float))), default=0)

    items: list[PriorityConcept] = []
    for ck in concept_keys:
        entry = scores_confiance.get(ck) or {}
        if isinstance(entry, dict):
            score = int(entry.get("score") or 0)
            last_seen = entry.get("last_seen")
        else:
            # Legacy format : entry is a bare number
            score = int(entry or 0)
            last_seen = None

        raw_weight = int(concept_weights.get(ck) or 0)
        weight_norm = (raw_weight / max_w) if (max_w and raw_weight) else 0.5

        days = _days_since(last_seen, today)
        tf = _time_factor(days)
        deficit = max(0.0, min(1.0, (100 - score) / 100.0))
        priority = weight_norm * tf * deficit

        items.append({
            "concept_key": ck,
            "priority_score": round(priority, 3),
            "score": score,
            "days_since_last_seen": days,
            "weight": raw_weight,
            "reason": _build_reason(score, days, raw_weight, weight_norm),
        })

    # Sort DESC by priority_score (ties broken by score ASC then weight DESC)
    items.sort(key=lambda x: (-x["priority_score"], x["score"], -x["weight"]))

    # Filter out trivially-zero-priority items (score=100 + recently seen)
    items = [i for i in items if i["priority_score"] > 0.05]

    return items[:limit]
