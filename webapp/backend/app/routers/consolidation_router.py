"""CEFR consolidation router (Session 36).

Endpoints:
  GET  /api/consolidation/state/{domain}              — current state + pending decision
  POST /api/consolidation/mini-exam/start/{domain}    — return 8 items for suspected level
  POST /api/consolidation/mini-exam/submit/{domain}   — submit answers, auto-score, compute outcome
  POST /api/consolidation/decide/{domain}             — user chose accept_new | stay_current

Doctrine : docs/01-pedagogy/cefr-consolidation-policy.md
Plan     : /root/.claude/plans/zazzy-dreaming-kahan.md
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import get_current_user
from .. import database as db

router = APIRouter(tags=["consolidation"])

_CONSOLIDATION_ENABLED = os.environ.get("CONSOLIDATION_ENABLED", "true").lower() in (
    "1", "true", "yes",
)


# ── YAML bank loader ──────────────────────────────────────────────────
# Resolve path from the installed academie_core package so it works in
# both host and container runtimes.
import academie_core as _ac
_BANK_ROOT = Path(_ac.__file__).parent / "data" / "mini_exam"


def _load_bank(lang: str, level: str) -> dict:
    path = _BANK_ROOT / f"{lang}_{level}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No mini-exam bank for {lang}/{level}")
    import yaml
    with path.open() as f:
        return yaml.safe_load(f)


# ── Schemas ──────────────────────────────────────────────────────────

class MiniExamAnswer(BaseModel):
    id: str
    answer: str = Field(..., max_length=500)


class MiniExamSubmission(BaseModel):
    target_level: Literal["A1", "A2", "B1", "B2", "C1"]
    answers: list[MiniExamAnswer]


class ConsolidationDecision(BaseModel):
    choice: Literal["accept_new", "stay_current"]


# ── GET /state/{domain} ───────────────────────────────────────────────

@router.get("/api/consolidation/state/{domain}")
async def get_consolidation_state(domain: str, user: dict = Depends(get_current_user)) -> dict:
    """Return niveau_status + pending decision + mini-exam target if any."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"niveau_status": "provisoire", "pending": None}
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT niveau_global, niveau_status, niveau_validated_at,
                      consolidation_decision_pending
               FROM profils_eleves
               WHERE eleve_id = $1 AND domain = $2""",
            eleve_id, domain,
        )
    if not row:
        return {"niveau_status": "provisoire", "pending": None}
    pending = row["consolidation_decision_pending"]
    if isinstance(pending, str):
        pending = json.loads(pending) if pending else None
    return {
        "niveau_global": row["niveau_global"],
        "niveau_status": row["niveau_status"] or "provisoire",
        "niveau_validated_at": row["niveau_validated_at"].isoformat() if row["niveau_validated_at"] else None,
        "pending": pending,
    }


# ── POST /mini-exam/start/{domain} ────────────────────────────────────

@router.post("/api/consolidation/mini-exam/start/{domain}")
async def mini_exam_start(domain: str, user: dict = Depends(get_current_user)) -> dict:
    """Return 8-item mini-exam for the learner's pending target level."""
    if not _CONSOLIDATION_ENABLED:
        raise HTTPException(status_code=503, detail="Consolidation disabled")
    state = await get_consolidation_state(domain, user)
    pending = state.get("pending")
    if not pending:
        raise HTTPException(status_code=404, detail="No pending consolidation")
    target_level = pending.get("mini_exam_target_level") or pending.get("observed")
    if not target_level:
        raise HTTPException(status_code=400, detail="No target level in pending decision")
    bank = _load_bank(domain, target_level)
    # Strip regex + llm_judge_hint before sending to frontend (avoid leaking grading logic)
    items_public = []
    for it in bank["items"]:
        items_public.append({
            "id": it["id"],
            "type": it["type"],
            "prompt": it["prompt"],
            "options": it.get("options"),
            "concept_code": it.get("concept_code"),
        })
    return {"target_level": target_level, "items": items_public,
            "total": len(items_public)}


# ── POST /mini-exam/submit/{domain} ───────────────────────────────────

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


async def _llm_judge_item(prompt: str, learner_answer: str, hint: str) -> bool:
    """Fallback judge for fuzzy items (produce_short, paraphrases).

    Uses the existing LiteLLM proxy (gpt-4.1-mini). Returns True/False.
    Safe default on any failure: False.
    """
    try:
        import httpx
        api_key = os.environ.get("LITELLM_MASTER_KEY") or os.environ.get("LITELLM_API_KEY", "")
        if not api_key:
            return False
        sys = (
            "You grade short language-learning exercises. Answer ONLY 'PASS' or 'FAIL'. "
            "Be strict but fair: accept minor typos, reject substantive errors. "
            f"Teacher's expectation: {hint}"
        )
        msg = f"Prompt: {prompt}\nLearner answer: {learner_answer}\nYour verdict:"
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.post(
                "http://litellm-proxy:4000/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4.1-mini",
                    "messages": [{"role": "system", "content": sys},
                                 {"role": "user", "content": msg}],
                    "max_tokens": 8, "temperature": 0.0,
                },
            )
            r.raise_for_status()
            verdict = r.json()["choices"][0]["message"]["content"].strip().upper()
            return verdict.startswith("PASS")
    except Exception:
        return False


@router.post("/api/consolidation/mini-exam/submit/{domain}")
async def mini_exam_submit(
    domain: str, body: MiniExamSubmission, user: dict = Depends(get_current_user),
) -> dict:
    """Grade answers, record score, return outcome (decision pending or auto-validate)."""
    if not _CONSOLIDATION_ENABLED:
        raise HTTPException(status_code=503, detail="Consolidation disabled")
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=401)

    from academie_core.pedagogy.consolidation import (
        MINI_EXAM_PASS_THRESHOLD, pick_message, ConsolidationOutcome,
        N_TURNS_CONSOLIDATION,
    )

    bank = _load_bank(domain, body.target_level)
    answer_by_id = {a.id: a.answer for a in body.answers}
    correct = 0
    details = []
    for item in bank["items"]:
        learner = _normalize(answer_by_id.get(item["id"], ""))
        if not learner:
            details.append({"id": item["id"], "ok": False, "reason": "empty"})
            continue
        # Regex first
        regex = item.get("expected_regex", "")
        ok = False
        if regex and regex != ".*":
            try:
                if re.fullmatch(regex, learner, flags=re.IGNORECASE):
                    ok = True
            except re.error:
                pass
        # LLM judge fallback if regex miss or produce_short type
        if not ok and item.get("llm_judge_hint"):
            ok = await _llm_judge_item(item["prompt"], learner, item["llm_judge_hint"])
        if ok:
            correct += 1
        details.append({"id": item["id"], "ok": ok})

    total = len(bank["items"])
    score_pct = round(100 * correct / total) if total else 0
    passed = correct / total >= MINI_EXAM_PASS_THRESHOLD

    # Load pending for QCM + observed context
    state = await get_consolidation_state(domain, user)
    pending = state.get("pending") or {}
    qcm = pending.get("qcm") or state.get("niveau_global") or ""
    observed = pending.get("observed") or body.target_level
    n_turns = pending.get("n_turns") or N_TURNS_CONSOLIDATION

    # If exam fails → drop proposal, stay at QCM (auto-validate QCM since observation didn't confirm)
    if not passed:
        from academie_core.pedagogy.consolidation import (
            msg_validation_after_failed_exam, bubble_template,
        )
        # Session 37 — fetch L1 for bubble template localization
        async with db.pool.acquire() as conn:
            l1 = await conn.fetchval(
                "SELECT l1 FROM eleves WHERE id = $1", eleve_id,
            ) or "fr"
        bubble_msg = bubble_template(
            "auto_validate_after_failed_exam", l1,
            level=qcm, tested_level=body.target_level,
        )
        async with db.pool.acquire() as conn:
            await conn.execute(
                """UPDATE profils_eleves
                   SET niveau_global = COALESCE(niveau_global, $1),
                       niveau_status = 'validé',
                       niveau_validated_at = NOW(),
                       consolidation_decision_pending = NULL
                   WHERE eleve_id = $2 AND domain = $3""",
                qcm, eleve_id, domain,
            )
            await conn.execute(
                """INSERT INTO consolidation_events
                   (eleve_id, domain, trigger_reason, qcm_level, observed_level,
                    mini_exam_triggered, mini_exam_score_pct, mini_exam_level,
                    user_decision, final_level, notes)
                   VALUES ($1,$2,'mini_exam_failed',$3,$4,true,$5,$6,'auto_validate',$3,$7)""",
                eleve_id, domain, qcm, observed, score_pct, body.target_level,
                bubble_msg,
            )
        return {
            "passed": False, "score_pct": score_pct, "correct": correct, "total": total,
            "outcome": "auto_validate", "final_level": qcm,
            # Session 37 Fix B — distinct "failed exam" message replaces the
            # misleading "tes auto-évaluations étaient justes" msg_validation.
            "message": msg_validation_after_failed_exam(n_turns, qcm, body.target_level),
            "details": details,
        }

    # Exam confirms observed ≠ qcm → present decision
    outcome = ConsolidationOutcome(
        kind="propose_mini_exam",
        qcm_level=qcm, observed_level=observed,
        decision_payload={"qcm": qcm, "observed": observed, "n_turns": n_turns,
                          "mini_exam_score_pct": score_pct, "awaiting_user": True},
    )
    async with db.pool.acquire() as conn:
        await conn.execute(
            """UPDATE profils_eleves
               SET consolidation_decision_pending = $1::jsonb
               WHERE eleve_id = $2 AND domain = $3""",
            json.dumps(outcome.decision_payload), eleve_id, domain,
        )
    return {
        "passed": True, "score_pct": score_pct, "correct": correct, "total": total,
        "outcome": "awaiting_user_decision",
        "qcm_level": qcm, "observed_level": observed,
        "message": pick_message(outcome, n_turns),
        "details": details,
    }


# ── POST /decide/{domain} ─────────────────────────────────────────────

@router.post("/api/consolidation/decide/{domain}")
async def consolidation_decide(
    domain: str, body: ConsolidationDecision, user: dict = Depends(get_current_user),
) -> dict:
    """Persist user's choice and close the pending consolidation."""
    if not _CONSOLIDATION_ENABLED:
        raise HTTPException(status_code=503, detail="Consolidation disabled")
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=401)
    state = await get_consolidation_state(domain, user)
    pending = state.get("pending")
    if not pending:
        raise HTTPException(status_code=404, detail="No pending decision")
    qcm = pending.get("qcm", "")
    observed = pending.get("observed", "")

    if body.choice == "accept_new":
        final_level = observed
        new_status = "validé"
    else:  # stay_current
        final_level = qcm
        new_status = "stabilisation_volontaire"

    # Session 37 — resolve L1-indexed bubble kind based on direction + choice
    from academie_core.pedagogy.consolidation import bubble_template, CEFR_INDEX
    async with db.pool.acquire() as conn:
        l1 = await conn.fetchval(
            "SELECT l1 FROM eleves WHERE id = $1", eleve_id,
        ) or "fr"

    if body.choice == "accept_new":
        is_upgrade = CEFR_INDEX.get(observed, 0) > CEFR_INDEX.get(qcm, 0)
        bubble_kind = "upgrade_accepted" if is_upgrade else "downgrade_accepted"
    else:
        bubble_kind = "stay_current"
    bubble_msg = bubble_template(bubble_kind, l1, level=final_level)

    async with db.pool.acquire() as conn:
        await conn.execute(
            """UPDATE profils_eleves
               SET niveau_global = $1,
                   niveau_status = $2,
                   niveau_validated_at = NOW(),
                   consolidation_decision_pending = NULL
               WHERE eleve_id = $3 AND domain = $4""",
            final_level, new_status, eleve_id, domain,
        )
        await conn.execute(
            """INSERT INTO consolidation_events
               (eleve_id, domain, trigger_reason, qcm_level, observed_level,
                mini_exam_triggered, user_decision, final_level, notes)
               VALUES ($1,$2,'user_decided',$3,$4,true,$5,$6,$7)""",
            eleve_id, domain, qcm, observed, body.choice, final_level, bubble_msg,
        )
    return {"ok": True, "final_level": final_level, "niveau_status": new_status}


# ── GET /events/{domain} ──────────────────────────────────────────────

@router.get("/api/consolidation/events/{domain}")
async def get_consolidation_events(
    domain: str, user: dict = Depends(get_current_user),
) -> list[dict]:
    """Return closed consolidation events with bubble messages for this user+domain.

    Session 37 — feeds the frontend "system bubble" rendering in the chat thread.
    Filters out 'pending' rows (no decision yet) and rows without a bubble_message.
    Ordered ASC by triggered_at for easy interleaving with Dify messages.
    """
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return []
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT triggered_at, final_level, user_decision, notes
               FROM consolidation_events
               WHERE eleve_id = $1 AND domain = $2
                 AND user_decision != 'pending'
                 AND notes IS NOT NULL
               ORDER BY triggered_at ASC""",
            eleve_id, domain,
        )
    return [
        {
            "triggered_at": r["triggered_at"].isoformat(),
            "final_level": r["final_level"],
            "user_decision": r["user_decision"],
            "bubble_message": r["notes"],
        }
        for r in rows
    ]
