"""
AcademIA Error Taxonomy — Monolithic analysis endpoint
Rules layer (surface errors) + LLM monolithic (grammar/lexical).
Called by n8n dify-snapshot workflow.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from ..auth import get_current_user
from pydantic import BaseModel
from .. import database as db

INTERNAL_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "REDACTED_INTERNAL_API_TOKEN")
from academie_core.taxonomy.rules import detect_errors, RuleDetection
from academie_core.taxonomy.llm import analyze_transcript, ANALYSIS_MODEL
from academie_core.taxonomy.categories import is_valid_code
from academie_core.taxonomy.scoring import enrich_error_fields
from ..domain_registry import chat_url_for_domain

logger = logging.getLogger("academie-api.error-analysis")

router = APIRouter()


class AnalyzeRequest(BaseModel):
    username: str
    domain: str = "en"
    session_id: str
    transcript: str
    snapshot_id: int | None = None


class AnalyzeResponse(BaseModel):
    status: str
    errors_detected: int
    rule_errors: int
    llm_errors: int
    turns_analyzed: int


@router.post("/internal/analyze-errors", response_model=AnalyzeResponse)
async def analyze_errors(req: AnalyzeRequest, x_internal_token: str = Header(None)):
    """
    Rules (surface) + LLM monolithic (grammar/lexical).
    Protected by internal token header (called by n8n on Docker network).
    """
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Input validation
    if not req.transcript or not req.transcript.strip():
        return AnalyzeResponse(status="empty_transcript", errors_detected=0, rule_errors=0, llm_errors=0, turns_analyzed=0)
    if not req.session_id or not req.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")

    # Resolve Dify UUID to real username if needed
    eleve_id = await db.pool.fetchval(
        """SELECT COALESCE(
            (SELECT e.id FROM users u JOIN eleves e ON u.eleve_id = e.id WHERE u.dify_user_id = $1 LIMIT 1),
            (SELECT id FROM eleves WHERE username = $1)
        )""", req.username
    )
    if not eleve_id:
        raise HTTPException(status_code=404, detail=f"Student '{req.username}' not found")

    # Sprint 2 B2: fetch CEFR level once for v2 field enrichment (None safe)
    niveau_global = await db.pool.fetchval(
        "SELECT niveau_global FROM profils_eleves WHERE eleve_id=$1 AND domain=$2",
        eleve_id, req.domain,
    )

    user_turns = _extract_user_turns(req.transcript)
    if not user_turns:
        return AnalyzeResponse(status="no_user_turns", errors_detected=0, rule_errors=0, llm_errors=0, turns_analyzed=0)

    all_errors: list[dict] = []

    # ── Layer 1: Rules (deterministic, surface errors) ──
    for turn_num, text in user_turns:
        for det in detect_errors(text):
            all_errors.append({
                "eleve_id": eleve_id,
                "session_id": req.session_id,
                "turn_number": turn_num,
                "error_code": det.error_code,
                "original_text": det.original_text,
                "suggested_correction": det.suggested_correction,
                "llm_reasoning": det.reasoning,
                "analysis_model": "rules",
                "snapshot_id": req.snapshot_id,
                **enrich_error_fields(det.error_code, niveau_global),
            })

    rule_count = len(all_errors)

    # ── Layer 2: LLM monolithic (grammar/lexical) ──
    llm_count = 0
    llm_failed = False
    try:
        result = await analyze_transcript(req.transcript, lang=req.domain)
        for error in result.errors:
            for code in error.codes:
                # Deduplicate with rules layer
                already = any(
                    e["turn_number"] == error.turn and e["error_code"] == code
                    for e in all_errors
                )
                if not already and is_valid_code(code):
                    all_errors.append({
                        "eleve_id": eleve_id,
                        "session_id": req.session_id,
                        "turn_number": error.turn,
                        "error_code": code,
                        "original_text": error.original,
                        "suggested_correction": error.correction,
                        "llm_reasoning": error.reasoning,
                        "analysis_model": ANALYSIS_MODEL,
                        "snapshot_id": req.snapshot_id,
                        **enrich_error_fields(code, niveau_global),
                    })
                    llm_count += 1
    except Exception:
        logger.exception("LLM analysis failed for session %s — rules-only results saved", req.session_id)
        llm_failed = True

    # ── Store ── Sprint 5 D1: domain column added to error_log (16th column)
    if all_errors:
        async with db.pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO error_log
                   (eleve_id, session_id, turn_number, error_code, original_text,
                    suggested_correction, llm_reasoning, analysis_model, snapshot_id,
                    tier, gravity_linguistic, gravity_communicative, gravity_social,
                    criterial_level_emergence, criterial_level_mastery, domain)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9,
                           $10, $11, $12, $13, $14, $15, $16)""",
                [
                    (e["eleve_id"], e["session_id"], e["turn_number"],
                     e["error_code"], e["original_text"],
                     e["suggested_correction"], e["llm_reasoning"],
                     e["analysis_model"], e["snapshot_id"],
                     e["tier"], e["gravity_linguistic"], e["gravity_communicative"],
                     e["gravity_social"], e["criterial_level_emergence"],
                     e["criterial_level_mastery"], req.domain)
                    for e in all_errors
                ],
            )

    total = len(all_errors)
    logger.info(
        "Analyzed session %s for %s: %d errors (rules=%d, llm=%d, turns=%d)",
        req.session_id, req.username, total, rule_count, llm_count, len(user_turns),
    )

    # Update error-based exam eligibility flag in profils_eleves
    try:
        profile = await _build_error_profile(eleve_id, req.domain)
        eligible = profile.get("progression", {}).get("eligible_for_exam", False)
        async with db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE profils_eleves SET error_exam_eligible = $1 WHERE eleve_id = $2 AND domain = $3",
                eligible, eleve_id, req.domain)
    except Exception:
        logger.warning("Could not update error_exam_eligible for %s", req.username)

    status = "rules_only" if llm_failed else "ok"
    return AnalyzeResponse(
        status=status, errors_detected=total,
        rule_errors=rule_count, llm_errors=llm_count,
        turns_analyzed=len(user_turns),
    )


@router.get("/api/student/{username}/error-profile")
async def get_error_profile(username: str, domain: str = "en", user: dict = Depends(get_current_user)):
    """Returns a student's error profile. Requires auth (admin only)."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    return await _build_error_profile_by_username(username, domain)


@router.get("/api/error-profile/{domain}")
async def get_my_error_profile(domain: str = "en", user: dict = Depends(get_current_user)):
    """Returns the authenticated user's error profile. Used by the frontend."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"band": "intermediate", "niveau": "B1", "families": {}, "concepts_by_family": {},
                "progression": {"progress_pct": 0, "penalized_total": 0, "penalized_clean": 0,
                                "eligible_for_exam": False, "sessions_total": 0, "sessions_required": 5},
                "recommendation": {"type": "start", "message": "Commence une session !", "action": chat_url_for_domain(domain), "label": "Commencer"},
                "summary": {"total_errors": 0, "active_errors": 0, "shadow_errors": 0, "sessions_analyzed": 0,
                            "high_priority": [], "work_on": [], "normal": []}}
    return await _build_error_profile(eleve_id, domain)


async def _build_error_profile(eleve_id: int, domain: str):
    """Build error profile for a student. Shared by both endpoints."""
    import json as _json
    from academie_core.taxonomy.scoring import compute_error_profile

    async with db.pool.acquire() as conn:
        profil = await conn.fetchrow(
            "SELECT niveau_global, scores_confiance FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
            eleve_id, domain)
        niveau = profil["niveau_global"] if profil and profil["niveau_global"] else "B1"
        sc_raw = profil["scores_confiance"] if profil else None
        scores_confiance = sc_raw if isinstance(sc_raw, dict) else _json.loads(sc_raw or "{}") if sc_raw else {}

        rows = await conn.fetch(
            """SELECT error_code, turn_number, session_id, tier FROM error_log
               WHERE eleve_id = $1 AND session_id NOT LIKE 'full-battery%%'
               AND session_id NOT LIKE 'phase1b-%%' ORDER BY created_at""", eleve_id)

        ck_row = await conn.fetchval(
            "SELECT concept_keys FROM curriculums WHERE domain = $1 AND niveau = $2",
            domain, niveau)
        concept_keys = ck_row if isinstance(ck_row, list) else _json.loads(ck_row or "[]")

    return compute_error_profile([dict(r) for r in rows], niveau, concept_keys, scores_confiance)


async def _build_error_profile_by_username(username: str, domain: str):
    """Resolve username → eleve_id then build profile."""
    async with db.pool.acquire() as conn:
        eleve = await conn.fetchrow("SELECT id FROM eleves WHERE username = $1", username)
        if not eleve:
            raise HTTPException(status_code=404, detail=f"Student '{username}' not found")
    return await _build_error_profile(eleve["id"], domain)


def _extract_user_turns(transcript: str) -> list[tuple[int, str]]:
    turns = []
    current_turn = 0
    for line in transcript.split("\n"):
        line = line.strip()
        if line.startswith("--- Turn "):
            try:
                current_turn = int(line.split("Turn ")[1].split(" ")[0].rstrip("-"))
            except (ValueError, IndexError):
                current_turn += 1
        elif line.startswith("USER: "):
            text = line[6:].strip()
            if text and len(text) > 2 and not _is_french_only(text):
                turns.append((current_turn, text))
    return turns


def _is_french_only(text: str) -> bool:
    french_markers = [
        "salut", "bonjour", "allons-y", "allez", "on y va", "on bosse",
        "mode structure", "mode libre", "directement", "par curiosité",
        "juste pour", "escalade", "quiz", "question suivante",
    ]
    return any(text.lower().strip().startswith(m) for m in french_markers)
