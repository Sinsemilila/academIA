"""
AcademIA Error Taxonomy — Detect-then-Classify pipeline
Called by n8n dify-snapshot workflow (async, non-blocking).

Pipeline:
  Step 1: LLM corrects text (Groq, simple prompt)
  Step 2: Diff engine extracts edit spans (deterministic)
  Step 3: Rules classify spans (deterministic, high precision)
  Step 4: LLM fallback classifies ambiguous spans (Groq, focused prompt)
  Store: all classified errors → error_log table
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from .. import database as db
from ..error_taxonomy.llm import get_corrections, classify_spans_batch, ANALYSIS_MODEL
from ..error_taxonomy.differ import extract_edits
from ..error_taxonomy.rules import classify_edits, ClassifiedError
from ..error_taxonomy.categories import is_valid_code

logger = logging.getLogger("academie-api.error-analysis")

router = APIRouter()


class AnalyzeRequest(BaseModel):
    username: str
    domaine: str = "anglais"
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
async def analyze_errors(req: AnalyzeRequest):
    """
    Detect-then-classify error analysis pipeline.
    """
    # Resolve eleve_id
    eleve_id = await db.pool.fetchval(
        "SELECT id FROM eleves WHERE username = $1", req.username
    )
    if not eleve_id:
        raise HTTPException(status_code=404, detail=f"Student '{req.username}' not found")

    # Extract user messages from transcript
    user_turns = _extract_user_turns(req.transcript)
    if not user_turns:
        return AnalyzeResponse(status="ok", errors_detected=0, rule_errors=0, llm_errors=0, turns_analyzed=0)

    # ══ Step 1: LLM corrects text ══
    try:
        corrections = await get_corrections(req.transcript)
    except Exception:
        logger.exception("Step 1 (LLM correction) failed for session %s", req.session_id)
        return AnalyzeResponse(status="llm_error", errors_detected=0, rule_errors=0, llm_errors=0, turns_analyzed=0)

    all_errors: list[dict] = []
    rule_count = 0
    llm_count = 0
    # Collect unclassified spans across all turns for batch LLM call
    pending_llm: list[tuple[int, str, str, str]] = []  # (turn, orig, corr, context)

    for turn_num, original_text in user_turns:
        corrected = corrections.get(turn_num)
        if not corrected or corrected.strip().lower() == original_text.strip().lower():
            continue  # No corrections = no errors

        # ══ Step 2: Diff ══
        edits = extract_edits(original_text, corrected)
        if not edits:
            continue

        # ══ Step 3: Rules classify ══
        classified, unclassified = classify_edits(edits, original_text)

        for err in classified:
            if is_valid_code(err.error_code):
                all_errors.append(_to_row(
                    eleve_id, req.session_id, turn_num, err, req.snapshot_id
                ))
                rule_count += 1

        # Collect unclassified for batch LLM
        for span in unclassified:
            if span.original or span.corrected:
                pending_llm.append((turn_num, span.original, span.corrected, span.context))

    # ══ Step 4: Batch LLM fallback ══
    if pending_llm:
        try:
            batch_input = [(orig, corr, ctx) for _, orig, corr, ctx in pending_llm]
            codes = await classify_spans_batch(batch_input)
            for (turn_num, orig, corr, _), code in zip(pending_llm, codes):
                if code and is_valid_code(code):
                    all_errors.append({
                        "eleve_id": eleve_id,
                        "session_id": req.session_id,
                        "turn_number": turn_num,
                        "error_code": code,
                        "original_text": orig,
                        "suggested_correction": corr,
                        "llm_reasoning": f"LLM fallback: '{orig}' → '{corr}'",
                        "analysis_model": ANALYSIS_MODEL,
                        "snapshot_id": req.snapshot_id,
                    })
                    llm_count += 1
        except Exception:
            logger.exception("Batch LLM fallback failed for session %s", req.session_id)

    # ══ Store ══
    if all_errors:
        async with db.pool.acquire() as conn:
            await conn.executemany(
                """INSERT INTO error_log
                   (eleve_id, session_id, turn_number, error_code, original_text,
                    suggested_correction, llm_reasoning, analysis_model, snapshot_id)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                [
                    (
                        e["eleve_id"], e["session_id"], e["turn_number"],
                        e["error_code"], e["original_text"],
                        e["suggested_correction"], e["llm_reasoning"],
                        e["analysis_model"], e["snapshot_id"],
                    )
                    for e in all_errors
                ],
            )

    total = len(all_errors)
    logger.info(
        "Analyzed session %s for %s: %d errors (rules=%d, llm-fallback=%d, turns=%d)",
        req.session_id, req.username, total, rule_count, llm_count, len(user_turns),
    )

    return AnalyzeResponse(
        status="ok",
        errors_detected=total,
        rule_errors=rule_count,
        llm_errors=llm_count,
        turns_analyzed=len(user_turns),
    )


def _to_row(eleve_id: int, session_id: str, turn: int, err: ClassifiedError, snapshot_id: int | None) -> dict:
    return {
        "eleve_id": eleve_id,
        "session_id": session_id,
        "turn_number": turn,
        "error_code": err.error_code,
        "original_text": err.original_text,
        "suggested_correction": err.suggested_correction,
        "llm_reasoning": err.reasoning,
        "analysis_model": err.source if err.source != "rules" else "rules",
        "snapshot_id": snapshot_id,
    }


def _extract_user_turns(transcript: str) -> list[tuple[int, str]]:
    """Parse transcript into (turn_number, user_text) tuples."""
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
    """Quick heuristic: skip messages that are entirely French/meta."""
    french_markers = [
        "salut", "bonjour", "allons-y", "allez", "on y va", "on bosse",
        "mode structure", "mode libre", "directement", "par curiosité",
        "juste pour", "escalade", "quiz", "question suivante",
    ]
    text_lower = text.lower().strip()
    return any(text_lower.startswith(m) for m in french_markers)
