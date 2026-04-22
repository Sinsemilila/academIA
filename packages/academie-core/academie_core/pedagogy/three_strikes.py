"""Three-strikes detector for proactive micro-lessons (Session 38).

When a learner fails 3× in a row on the same error_family within a short window,
return the family so the tutor can inject a one-shot micro-lesson. Includes a
3-day dedup so the same family isn't re-lectured back-to-back.

Grounded in :
  - Sheen (2008), Rassaei (2023) — FLA × corrective-feedback type interactions.
  - Spada & Lightbown (2008) — isolated form-focused instruction beats
    integrated-only on delayed post-tests.
  - Heift (2010), VanLehn (2011) — 3-strike escalation is the ITS convention
    for help escalation after repeated failure on the same item.

Design decisions (Sinse validation, Session 38) :
  - Detection granularity = `error_family` (from `ERROR_CODE_TO_FAMILY` in
    `taxonomy/rules.py`). Finer per-concept_key is a V2 concern.
  - Window = last 10 errors (not turns — concentrates on recent signal).
  - Threshold = 3 consecutive errors on the same family within that window.
  - Dedup = 3 days per (eleve, domain, family) via `micro_lesson_log` table.
  - Gates beyond these (FLA, structure whitelist, CEFR-gate) deliberately
    dropped for MVP — the CEFR variant lives inside the YAML template.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg  # noqa: F401


async def detect_three_strikes_family(
    conn,
    eleve_id: int,
    domain: str,
    *,
    window_errors: int = 10,
    threshold: int = 3,
    dedup_days: int = 3,
    bypass_dedup: bool = False,
) -> str | None:
    """Return the error_family on which the learner just triggered a 3-strikes,
    or None if no family qualifies.

    An error_family qualifies iff :
      - the most recent `threshold` errors in the last `window_errors` rows
        of `error_log` for this (eleve, domain) all share the same family
      - AND no micro-lesson has been injected for that (eleve, domain, family)
        in the last `dedup_days` days.

    The family is derived live from `error_code` via `ERROR_CODE_TO_FAMILY`
    — `error_log` doesn't store a `family` column.
    """
    from academie_core.taxonomy.rules import ERROR_CODE_TO_FAMILY

    rows = await conn.fetch(
        """
        SELECT error_code
        FROM error_log
        WHERE eleve_id = $1 AND domain = $2
        ORDER BY created_at DESC
        LIMIT $3
        """,
        eleve_id, domain, window_errors,
    )
    if len(rows) < threshold:
        return None

    families = [
        ERROR_CODE_TO_FAMILY.get(r["error_code"], "unknown")
        for r in rows[:threshold]
    ]
    if len(set(families)) != 1:
        return None
    family = families[0]
    if family == "unknown":
        return None

    # Dedup — skip if we already injected this family recently.
    # bypass_dedup=True lets dogfood sessions replay the same 3-strikes
    # scenario without waiting 3 days (see THREE_STRIKES_DEDUP_BYPASS).
    if bypass_dedup:
        return family

    recent = await conn.fetchval(
        """
        SELECT 1 FROM micro_lesson_log
        WHERE eleve_id = $1 AND domain = $2 AND family = $3
          AND injected_at > NOW() - ($4 || ' days')::interval
        LIMIT 1
        """,
        eleve_id, domain, family, str(dedup_days),
    )
    if recent:
        return None

    return family


async def log_micro_lesson_injection(
    conn,
    eleve_id: int,
    domain: str,
    family: str,
    cefr_band: str,
) -> None:
    """Persist an injection so the dedup window applies next turn."""
    await conn.execute(
        """
        INSERT INTO micro_lesson_log (eleve_id, domain, family, cefr_band)
        VALUES ($1, $2, $3, $4)
        """,
        eleve_id, domain, family, cefr_band,
    )


def cefr_band(level: str) -> str:
    """Map a raw CEFR string (A1, A1+, A2, B1, B2, C1, C2) to the 3-bucket
    band used by micro-lesson YAML : A1 / A2 / B1 (for B1 and above).

    The A1 bucket deliberately gets example-only templates ; A2 short rule ;
    B1+ full metalinguistic. Validated by Sprint 3 battery at 97.4% and by
    the institutional consensus on progressive metalanguage (PCIC, Goethe,
    Alliance Française, ACTFL 2021).
    """
    if not level:
        return "B1"
    head = level.strip().upper().rstrip("+")[:2]
    if head == "A1":
        return "A1"
    if head == "A2":
        return "A2"
    return "B1"  # B1, B2, C1, C2 all share the fullest template
