import asyncio
import json
import logging
import os
import httpx
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..models import ChatRequest
from ..auth import get_current_user
from ..rate_limit import limiter
from .. import database as db
from academie_core.taxonomy.rules import ERROR_CODE_TO_FAMILY
from ..openai_reconcile import reconcile_openai_usage
from academie_core.pedagogy.teacher_prompt import PromptContext
from academie_core.domain.language import LanguageDomain
import yaml
import tiktoken
from pathlib import Path

logger = logging.getLogger("academie-api.chat_router")

# ── Daily token budget for gpt-4o-mini (free tier protection) ──
_GPT4O_DAILY_LIMIT = 1_500_000
# Display safety margin: /admin shows tokens × 1.10 to stay above OpenAI dashboard.
# Auto-switch threshold (`exceeded`) uses the same inflated value, so the model
# bascule fires a touch early — protective bias.
_DISPLAY_SAFETY_MARGIN = 1.10
# Lazy reconciliation against OpenAI Usage API: skip if last reconcile is fresher
# than this (seconds).
_RECONCILE_STALENESS_S = 15 * 60
_gpt4o_token_counter = {"date": "", "tokens": 0, "loaded": False}
_tiktoken_enc = tiktoken.encoding_for_model("gpt-4o-mini")

# Sprint 5 — Multi-domain registry.
# Each agent maps to a (domain_db_string, LanguageDomain) pair.
# Domain string uses ISO-639-1 codes for languages ("en", "es"), free strings
# for non-language domains ("python", "cybersec"). Adding a new language =
# one line here + YAML data files + env var.
_DOMAIN_REGISTRY: dict[str, tuple[str, LanguageDomain]] = {
    "teacher": ("en", LanguageDomain("en")),
}

# Sprint 5 Phase 4 — Maestro ES activation behind feature flag.
# Requires: (1) ENABLE_MAESTRO env var = "true", (2) content pack YAMLs
# (rubrics/fewshots/l1_transfer/concept_hints/cefr_diagnostics for es),
# (3) DIFY_KEY_MAESTRO env var set, (4) frontend config.ts `maestro.available=true`,
# (5) native-speaker validation of the content pack.
# Drafted YAMLs ship with the codebase but activation is gated to prevent
# accidental exposure of unvetted ES content.
if os.environ.get("ENABLE_MAESTRO", "false").lower() in ("1", "true", "yes"):
    try:
        _DOMAIN_REGISTRY["maestro"] = ("es", LanguageDomain("es"))
    except Exception as _e:
        import logging
        logging.getLogger("chat").error(
            "ENABLE_MAESTRO=true but LanguageDomain('es') failed to initialize: %s", _e
        )
    # "professore": ("it", LanguageDomain("it")),  # Sprint 6 — Italian
    # "lehrer": ("de", LanguageDomain("de")),      # Sprint 7 — German
    # "sensei": ("ja", LanguageDomain("ja")),      # Sprint 8 — Japanese


def _get_domain(agent: str) -> tuple[str, LanguageDomain]:
    """Resolve agent name to (domain, LanguageDomain). Raises 404 if unknown."""
    entry = _DOMAIN_REGISTRY.get(agent)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Agent '{agent}' non disponible")
    return entry


def _is_openai_billable(name: str | None) -> bool:
    """Same OpenAI billing pool: gpt-4o-mini base + every ft:gpt-4o-mini-* derivative.
    Used to compute the headline `base_tokens` that drives /admin display + auto-switch."""
    if not name:
        return False
    return name == "gpt-4o-mini" or name.startswith("ft:gpt-4o-mini-")


def _count_tokens(text: str) -> int:
    return len(_tiktoken_enc.encode(text)) if text else 0


async def _load_daily_tokens() -> None:
    """Load today's token count from DB on first call.
    Seeds the in-memory counter with MAX(local, litellm_snapshot, openai_snapshot)
    so the auto-switch decision never undercounts external sources of truth."""
    if _gpt4o_token_counter["loaded"] and _gpt4o_token_counter["date"] == date.today().isoformat():
        return
    today = date.today().isoformat()
    try:
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT tokens_used,
                          COALESCE(litellm_tokens, 0) AS lt,
                          COALESCE(openai_tokens, 0) AS ot
                     FROM token_usage_daily WHERE usage_date = $1""",
                date.today())
            if row:
                _gpt4o_token_counter["tokens"] = max(row["tokens_used"], row["lt"], row["ot"])
            else:
                _gpt4o_token_counter["tokens"] = 0
    except Exception:
        _gpt4o_token_counter["tokens"] = 0
    _gpt4o_token_counter["date"] = today
    _gpt4o_token_counter["loaded"] = True


async def _track_gpt4o_tokens(input_tokens: int, output_tokens: int) -> None:
    """Track daily gpt-4o-mini token usage in DB. Resets at midnight + restores gpt-4o-mini."""
    today = date.today().isoformat()
    if _gpt4o_token_counter["date"] != today:
        _gpt4o_token_counter["date"] = today
        _gpt4o_token_counter["tokens"] = 0
        _gpt4o_token_counter["loaded"] = True
        if _current_dify_model != "gpt-4o-mini":
            await _switch_dify_model("gpt-4o-mini")
    added = input_tokens + output_tokens
    _gpt4o_token_counter["tokens"] += added
    try:
        async with db.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO token_usage_daily (usage_date, tokens_used)
                   VALUES (CURRENT_DATE, $1)
                   ON CONFLICT (usage_date) DO UPDATE SET tokens_used = token_usage_daily.tokens_used + $1""",
                added)
    except Exception:
        pass


async def _gpt4o_budget_exceeded() -> bool:
    await _load_daily_tokens()
    return _gpt4o_token_counter["tokens"] >= _GPT4O_DAILY_LIMIT


async def _fetch_litellm_usage() -> list[dict] | None:
    """Aggregate today's spend from LiteLLM_SpendLogs.
    Bucket name = model_group when present, else falls back to model itself
    (covers config quirks where LiteLLM didn't tag a model_group on the row).
    Returns None if LiteLLM DB is unavailable (caller should fall back to local estimate)."""
    if db.litellm_pool is None:
        return None
    try:
        async with db.litellm_pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT
                       COALESCE(NULLIF(model_group, ''), model) AS name,
                       COALESCE(SUM(prompt_tokens + completion_tokens), 0)::bigint AS tokens,
                       COALESCE(SUM(spend), 0)::float AS cost_usd
                   FROM "LiteLLM_SpendLogs"
                   WHERE "startTime"::date = CURRENT_DATE
                   GROUP BY COALESCE(NULLIF(model_group, ''), model)
                   ORDER BY tokens DESC""")
            return [dict(r) for r in rows]
    except Exception:
        return None


async def _do_reconcile_and_save(litellm_total: int) -> None:
    """Background task: hit OpenAI Usage API, UPSERT snapshot into token_usage_daily,
    and bump in-memory counter to MAX of all sources. Best-effort, swallows errors."""
    try:
        openai_total = await reconcile_openai_usage()
        async with db.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO token_usage_daily
                       (usage_date, tokens_used, litellm_tokens, openai_tokens, reconciled_at)
                   VALUES (CURRENT_DATE, 0, $1, $2, NOW())
                   ON CONFLICT (usage_date) DO UPDATE SET
                       litellm_tokens = EXCLUDED.litellm_tokens,
                       openai_tokens = EXCLUDED.openai_tokens,
                       reconciled_at = NOW()""",
                int(litellm_total),
                int(openai_total) if openai_total is not None else 0,
            )
        # Bump in-memory counter so auto-switch sees the new ceiling immediately.
        candidates = [_gpt4o_token_counter["tokens"], int(litellm_total)]
        if openai_total is not None:
            candidates.append(int(openai_total))
        _gpt4o_token_counter["tokens"] = max(candidates)
    except Exception as e:
        logger.warning("_do_reconcile_and_save failed: %s", e)


async def _maybe_schedule_reconcile(litellm_total: int) -> dict:
    """Check if reconciliation is stale (>15 min) and schedule a fire-and-forget
    background task. Returns a dict with the latest stored snapshot."""
    snapshot = {"litellm_tokens": 0, "openai_tokens": 0, "reconciled_at": None}
    try:
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT litellm_tokens, openai_tokens, reconciled_at
                     FROM token_usage_daily WHERE usage_date = CURRENT_DATE""")
            if row:
                snapshot = {
                    "litellm_tokens": row["litellm_tokens"],
                    "openai_tokens": row["openai_tokens"],
                    "reconciled_at": row["reconciled_at"],
                }
    except Exception:
        pass

    last = snapshot["reconciled_at"]
    stale = last is None or (datetime.utcnow() - last).total_seconds() > _RECONCILE_STALENESS_S
    if stale:
        asyncio.create_task(_do_reconcile_and_save(litellm_total))
    return snapshot


async def get_gpt4o_usage() -> dict:
    """Return current daily token usage. Sources combined for safety:
      1. local tiktoken counter (real-time, sub-second auto-switch decisions)
      2. LiteLLM SpendLogs (~30-60s lag, includes ft:gpt-4o-mini-* fine-tunes)
      3. OpenAI Usage API (authoritative, lazily refreshed every 15 min in background)
    Headline `tokens` = max(all three) × +10% safety margin, so /admin always shows
    a value >= what OpenAI dashboard reports."""
    await _load_daily_tokens()
    local_estimate = _gpt4o_token_counter["tokens"]
    today = _gpt4o_token_counter["date"]

    litellm_rows = await _fetch_litellm_usage()
    if litellm_rows is None:
        # Fallback: local tiktoken estimate (no LiteLLM DB available)
        margin_tokens = int(local_estimate * _DISPLAY_SAFETY_MARGIN)
        return {
            "date": today,
            "tokens": margin_tokens,
            "tokens_raw": local_estimate,
            "safety_margin_pct": int((_DISPLAY_SAFETY_MARGIN - 1) * 100),
            "limit": _GPT4O_DAILY_LIMIT,
            "pct": round(margin_tokens / _GPT4O_DAILY_LIMIT * 100, 1),
            "exceeded": margin_tokens >= _GPT4O_DAILY_LIMIT,
            "models": [],
            "source": "estimate",
            "local_estimate": local_estimate,
            "openai_snapshot": None,
            "reconciled_at": None,
        }

    # A: include base gpt-4o-mini + all ft:gpt-4o-mini-* (same OpenAI billing pool)
    litellm_base = sum(r["tokens"] for r in litellm_rows if _is_openai_billable(r["name"]))
    # C+D: lazy reconcile + take max of all sources for the headline
    snapshot = await _maybe_schedule_reconcile(litellm_base)
    raw_tokens = max(local_estimate, litellm_base, snapshot["openai_tokens"])
    margin_tokens = int(raw_tokens * _DISPLAY_SAFETY_MARGIN)

    return {
        "date": today,
        "tokens": margin_tokens,
        "tokens_raw": raw_tokens,
        "safety_margin_pct": int((_DISPLAY_SAFETY_MARGIN - 1) * 100),
        "limit": _GPT4O_DAILY_LIMIT,
        "pct": round(margin_tokens / _GPT4O_DAILY_LIMIT * 100, 1),
        "exceeded": margin_tokens >= _GPT4O_DAILY_LIMIT,
        "models": litellm_rows,
        "source": "litellm+openai" if snapshot["reconciled_at"] else "litellm",
        "local_estimate": local_estimate,
        "litellm_total": litellm_base,
        "openai_snapshot": snapshot["openai_tokens"] or None,
        "reconciled_at": snapshot["reconciled_at"].isoformat() if snapshot["reconciled_at"] else None,
    }


_current_dify_model = "gpt-4o-mini"


async def _switch_dify_model(target_model: str):
    """Switch all Teacher LLM nodes in Dify to a different model."""
    global _current_dify_model
    if _current_dify_model == target_model:
        return
    try:
        async with db.pool.acquire() as conn:
            for wf_id in ['c52a451f-e381-46f1-a23a-077197b0fccb', 'ed0d1c91-8c9a-48ad-9c3a-063981f8da87']:
                await conn.execute(
                    "UPDATE workflows SET graph = replace(graph::text, "
                    f"'\"name\": \"{_current_dify_model}\"', '\"name\": \"{target_model}\"')::json, "
                    "updated_at = NOW() WHERE id = $1", wf_id)
        _current_dify_model = target_model
        import logging
        logging.getLogger("chat").info("Dify model switched to %s", target_model)
    except Exception as e:
        import logging
        logging.getLogger("chat").error("Failed to switch Dify model: %s", e)


# Load tolerance matrix once at import. Selection via USE_V2_TOLERANCE env var.
import logging as _logging
_TOLERANCE_MATRIX = {}
_use_v2 = os.getenv("USE_V2_TOLERANCE", "false").lower() in ("1", "true", "yes")
_config_dir = Path(__file__).parent.parent / "config"
_tm_path = _config_dir / (
    "tolerance_matrix_v2.yaml" if _use_v2 else "tolerance_matrix.yaml"
)
if _tm_path.exists():
    with open(_tm_path) as f:
        _tm = yaml.safe_load(f)
        _TOLERANCE_MATRIX = _tm.get("matrix", {})
    # Apply manual overrides (v2 only) — same logic as scoring._load_matrix
    if _use_v2:
        _ov_path = _config_dir / "tolerance_matrix_v2_overrides.yaml"
        if _ov_path.exists():
            with open(_ov_path) as f:
                _ov = yaml.safe_load(f) or {}
            _applied = []
            for _fam, _bands in (_ov.get("overrides") or {}).items():
                if _fam in _TOLERANCE_MATRIX:
                    _TOLERANCE_MATRIX[_fam].update(_bands)
                    _applied.append(f"{_fam}={_bands}")
            if _applied:
                _logging.getLogger("chat").info(
                    "Applied %d overrides: %s", len(_applied), _applied)
    _logging.getLogger("chat").info("Loaded tolerance matrix: %s (v2=%s)", _tm_path.name, _use_v2)

_NIVEAU_TO_BAND = {"A1": "beginner", "A2": "beginner", "B1": "intermediate",
                    "B2": "upper", "C1": "advanced", "C2": "advanced"}


def _get_error_tier(error_code: str, niveau: str) -> str:
    """Get tolerance tier for an error code at a CECRL level."""
    family = ERROR_CODE_TO_FAMILY.get(error_code)
    if not family:
        return "noted"  # unknown family → show it
    band = _NIVEAU_TO_BAND.get(niveau, "intermediate")
    return _TOLERANCE_MATRIX.get(family, {}).get(band, "noted")

router = APIRouter(tags=["chat"])

# Dify API config — internal Docker network
DIFY_API_URL = os.environ.get("DIFY_API_URL", "http://dify-api:5001/v1")
DIFY_APP_KEYS = {
    "teacher": os.environ.get("DIFY_KEY_TEACHER", ""),
}
# Sprint 5 Phase 4 — Maestro ES Dify app key (gated by ENABLE_MAESTRO).
if os.environ.get("ENABLE_MAESTRO", "false").lower() in ("1", "true", "yes"):
    DIFY_APP_KEYS["maestro"] = os.environ.get("DIFY_KEY_MAESTRO", "")
# Future agents: DIFY_KEY_PROFESSORE (IT), DIFY_KEY_LEHRER (DE), DIFY_KEY_SENSEI (JP)


def get_dify_key(agent: str) -> str:
    key = DIFY_APP_KEYS.get(agent)
    if not key:
        raise HTTPException(status_code=404, detail=f"Agent '{agent}' non disponible")
    return key


# ── Phase 7 — Spaced retrieval (feature-flagged) ─────────────────────
# Flag gating: OFF by default (ENABLE by setting SPACED_RETRIEVAL_ENABLED=true).
# When OFF, pre-turn skip queue read + post-turn skip enqueue/complete → runtime
# identical to Phase 6. When ON, silenced-for-spaced-retrieval errors are queued
# for revisit at J+1; items due inject into PROMPT_SESSION_V2 via `spaced_retrieval_today`.
SPACED_RETRIEVAL_ENABLED = os.environ.get("SPACED_RETRIEVAL_ENABLED", "false").lower() in ("1", "true", "yes")
_SPACED_RETRIEVAL_INTERVAL_DAYS = 1  # MVP — fixed J+1. FSRS ladder is post-MVP.
_SPACED_RETRIEVAL_MAX_DUE = 3  # surface at most 3 items/turn to avoid prompt bloat


async def _fetch_due_retrieval_items(eleve_id: int, domain: str = "en") -> list[dict]:
    """Return items due for spaced retrieval now. Empty list when flag OFF or none due."""
    if not SPACED_RETRIEVAL_ENABLED or not eleve_id:
        return []
    try:
        async with db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT id, concept_key, error_code
                   FROM spaced_retrieval_queue
                   WHERE eleve_id = $1 AND domain = $2
                     AND completed_at IS NULL
                     AND scheduled_at <= NOW()
                   ORDER BY scheduled_at ASC
                   LIMIT $3""",
                eleve_id, domain, _SPACED_RETRIEVAL_MAX_DUE,
            )
    except Exception as e:
        logger.warning("spaced_retrieval fetch failed: %s", e)
        return []
    return [
        {
            "queue_id": r["id"],
            "concept_key": r["concept_key"] or (r["error_code"] or "review"),
            "error_code": r["error_code"],
            "last_error_summary": r["error_code"] or "review needed",
        }
        for r in rows
    ]


async def _persist_spaced_retrieval(
    eleve_id: int,
    domain: str,
    silenced_codes: list[str],
    addressed_keys: list[str],
) -> None:
    """Enqueue newly-silenced errors (J+1) and mark addressed items complete.

    Idempotent-ish: enqueue ON CONFLICT by (eleve_id, error_code, completed_at IS NULL)
    is not enforced by a unique index, so a learner repeating the same mistake two
    turns in a row will accumulate multiple queue rows — we tolerate this as the
    queue is polled with LIMIT 3 and duplicates surface as a single bullet
    (`concept_key` is used for display). Cleanup cron can dedupe post-MVP.
    """
    if not SPACED_RETRIEVAL_ENABLED or not eleve_id:
        return
    try:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                for code in silenced_codes or []:
                    if not isinstance(code, str) or not code.strip():
                        continue
                    family = ERROR_CODE_TO_FAMILY.get(code) or code
                    await conn.execute(
                        """INSERT INTO spaced_retrieval_queue
                           (eleve_id, domain, concept_key, error_code, scheduled_at, created_at)
                           VALUES ($1, $2, $3, $4, NOW() + ($5 || ' days')::INTERVAL, NOW())""",
                        eleve_id, domain, family, code, str(_SPACED_RETRIEVAL_INTERVAL_DAYS),
                    )
                if addressed_keys:
                    await conn.execute(
                        """UPDATE spaced_retrieval_queue
                           SET completed_at = NOW(), outcome = 'addressed'
                           WHERE eleve_id = $1 AND domain = $2
                             AND completed_at IS NULL
                             AND (concept_key = ANY($3::text[]) OR error_code = ANY($3::text[]))""",
                        eleve_id, domain, list(addressed_keys),
                    )
    except Exception as e:
        logger.warning("spaced_retrieval persist failed: %s", e)


@router.post("/api/chat/send")
async def chat_send(req: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """Stream a chat message through Dify API."""
    # Rate limit: 30 messages per minute per IP
    limiter.check(request, max_requests=30, window_seconds=60)
    dify_key = get_dify_key(req.agent)
    domain, lang = _get_domain(req.agent)
    # Use existing Dify UUID if set, otherwise generate a stable ID
    dify_user = user.get("dify_user_id") or f"user_{user['id']}"

    # Calculate timing signals
    minutes_since_last = 0
    turn_response_secs = 0
    if req.conversation_id:
        async with db.pool.acquire() as conn:
            last_msg = await conn.fetchval(
                """SELECT last_message_at FROM user_sessions
                   WHERE user_id = $1 AND agent_name = $2 AND dify_conversation_id = $3""",
                user["id"], req.agent, req.conversation_id,
            )
            if last_msg:
                delta = datetime.now() - last_msg
                minutes_since_last = int(delta.total_seconds() / 60)
                turn_response_secs = int(delta.total_seconds())

    # Build Dify inputs
    dify_inputs = {
        "minutes_since_last": str(minutes_since_last),
        "turn_response_secs": str(turn_response_secs),
    }
    if req.mock_exam:
        dify_inputs["mock_exam"] = req.mock_exam
    if req.mode_override:
        dify_inputs["mode_override"] = req.mode_override

    # Real-time error feedback (rules layer only, zero LLM cost)
    # Filtered by tolerance_matrix: shadow errors are hidden, noted/penalized are tagged
    detections = lang.detect_errors(req.message)
    niveau = ""
    profile_l1: str | None = "fr"  # default familial (Phase 6)
    l1_watch_on: bool = True
    eleve_id = user.get("eleve_id")
    if eleve_id:
        try:
            # Sprint 5 D2: L1 is now user-global (eleves.l1), l1_watch stays per-profile
            async with db.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """SELECT p.niveau_global, e.l1, p.l1_watch_enabled
                       FROM profils_eleves p JOIN eleves e ON e.id = p.eleve_id
                       WHERE p.eleve_id = $1 AND p.domain = $2""",
                    eleve_id, domain)
            if row:
                niveau = row["niveau_global"] or ""
                profile_l1 = row["l1"] or "fr"
                l1_watch_on = bool(row["l1_watch_enabled"]) if row["l1_watch_enabled"] is not None else True
        except Exception:
            pass

    if detections:
        lines = []
        for d in detections:
            tier = _get_error_tier(d.error_code, niveau) if niveau else "noted"
            if tier == "shadow":
                continue  # don't show to student — they're not ready
            tag = ""
            if tier == "penalized":
                tag = " [PRIORITE]"
            elif tier == "noted":
                tag = " [a travailler]"
            lines.append(f"- \"{d.original_text}\" → \"{d.suggested_correction}\" ({d.reasoning}){tag}")
        dify_inputs["error_feedback"] = "\n".join(lines) if lines else ""

        # Check for repeated errors (same codes seen in last 7 days) — non-critical
        try:
            current_codes = list({d.error_code for d in detections})
            eleve_id = user.get("eleve_id")
            if eleve_id and current_codes:
                async with db.pool.acquire() as conn:
                    recent = await conn.fetch(
                        """SELECT DISTINCT error_code FROM error_log
                           WHERE eleve_id = $1 AND created_at > NOW() - INTERVAL '7 days'
                           AND error_code = ANY($2::text[])""",
                        eleve_id, current_codes)
                    repeated = [r["error_code"] for r in recent]
                    if repeated:
                        dify_inputs["repeated_errors"] = ", ".join(repeated)
        except Exception:
            pass  # Informational signal, chat must not fail on this
    else:
        dify_inputs["error_feedback"] = ""

    # ── Sprint 3 V2 dynamic sections (Lyster + dosing + anti-drift) ──
    # Computed every request even when V1 prompt is active in Dify — the start
    # node accepts these inputs unconditionally (forward compat). When V2 prompt
    # is wired in patch_graph, the prompt references them; when V1 is wired,
    # they're ignored. No-op risk = zero.
    try:
        # Build error context with full v2 enrichment (tier + gravity axes)
        v2_errors = []
        if niveau:
            for d in detections:
                enriched = lang.score_tier(d.error_code, niveau)
                if not enriched.get("tier"):
                    continue
                v2_errors.append({
                    "error_code": d.error_code,
                    "family": ERROR_CODE_TO_FAMILY.get(d.error_code, "unknown"),
                    "tier": enriched["tier"],
                    "gravity_linguistic": enriched.get("gravity_linguistic") or 0,
                    "gravity_communicative": enriched.get("gravity_communicative") or 0,
                    "gravity_social": enriched.get("gravity_social") or 0,
                })
        # Turn count: best-effort from session history. Phase 4 MVP defaults to 1
        # so anti-drift triggers (turn % 5/10) won't fire mid-conversation; full
        # turn-counter integration is Phase 5+ tuning.
        turn_count = 1
        if req.conversation_id and eleve_id:
            try:
                async with db.pool.acquire() as conn:
                    msg_count = await conn.fetchval(
                        """SELECT COALESCE(message_count, 0) FROM user_sessions
                           WHERE user_id = $1 AND agent_name = $2 AND dify_conversation_id = $3""",
                        user["id"], req.agent, req.conversation_id,
                    )
                    if msg_count is not None:
                        turn_count = int(msg_count) + 1
            except Exception:
                pass

        # Phase 7 — query items due for spaced retrieval (flag-gated, empty when OFF)
        spaced_due = await _fetch_due_retrieval_items(eleve_id, domain) if eleve_id else []
        ctx = PromptContext(
            level=niveau or "B1",
            turn_count=turn_count,
            errors_detected=v2_errors,
            last_feedback_per_family={},  # Phase 5+ once teacher_response_log exists
            # Phase 6 : l1 & toggle sourced from profils_eleves + eleves. When toggle off,
            # pass None so build_l1_watch returns empty (block absent from prompt).
            l1=profile_l1 if l1_watch_on else None,
            spaced_retrieval_due=spaced_due,
            target_lang=lang.lang_target,
        )
        sections = lang.build_dynamic_sections(ctx)
        for key, val in sections.items():
            if key.startswith("_"):
                continue
            if isinstance(val, str):
                dify_inputs[key] = val

        # Sprint 5 Phase 3 — lang-specific inputs for the unified language-tutor chatflow.
        # Replaces hardcoded EN dicts (concept_hint_map + CEFR diagnostic examples) that
        # used to live inside Dify JS/prompts. Backend ships the full per-lang content
        # as Dify Start inputs so the chatflow stays language-agnostic.
        try:
            import json as _json
            from academie_core.data.loader import (
                load_concept_hints as _load_hints,
                build_cefr_diagnostics_block as _build_cefr,
                get_persona_label as _persona,
            )
            dify_inputs["concept_hints_json"] = _json.dumps(_load_hints(lang.lang_target))
            dify_inputs["cefr_diagnostics_block"] = _build_cefr(lang.lang_target)
            dify_inputs["lang_target_name"] = _persona(lang.lang_target, "target_name", "Anglais")
            dify_inputs["lang_target_prof"] = _persona(lang.lang_target, "target_prof", "d'anglais")
        except Exception as e:
            import logging
            logging.getLogger("chat").warning("Sprint 5 Phase 3 lang inputs build failed: %s", e)
            dify_inputs.setdefault("concept_hints_json", "{}")
            dify_inputs.setdefault("cefr_diagnostics_block", "")
            dify_inputs.setdefault("lang_target_name", "Anglais")
            dify_inputs.setdefault("lang_target_prof", "d'anglais")
    except Exception as e:
        import logging
        logging.getLogger("chat").warning("Sprint 3 dynamic sections build failed: %s", e)
        # Empty defaults so Dify start node doesn't reject unknown inputs
        for key in (
            "rubric_for_level", "fewshots_block", "dosage_block",
            "level_reminder_inject", "drift_validation_request",
            "l1_watch", "spaced_retrieval_today", "output_schema_block",
            # Sprint 5 Phase 3 — unified language-tutor inputs
            "concept_hints_json", "cefr_diagnostics_block",
            "lang_target_name", "lang_target_prof",
        ):
            dify_inputs.setdefault(key, "")

    # ── GPT-4o-mini daily token budget check ──
    input_token_est = _count_tokens(req.message) + 2000  # system prompt + history overhead
    if await _gpt4o_budget_exceeded():
        import logging
        logging.getLogger("chat").warning(
            "gpt-4o-mini daily budget exceeded (%d/%d). Switching Dify to groq-standard.",
            _gpt4o_token_counter["tokens"], _GPT4O_DAILY_LIMIT)
        await _switch_dify_model("groq-standard")

    payload = {
        "inputs": dify_inputs,
        "query": req.message,
        "user": dify_user,
        "response_mode": "streaming",
        "conversation_id": req.conversation_id or "",
    }

    collected_answer = []

    async def stream():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{DIFY_API_URL}/chat-messages",
                json=payload,
                headers={"Authorization": f"Bearer {dify_key}"},
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_data = json.dumps({"event": "error", "message": body.decode()})
                    yield f"data: {error_data}\n\n"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line}\n\n"
                        # Track output tokens from answer chunks
                        try:
                            evt = json.loads(line[6:])
                            if "answer" in evt:
                                collected_answer.append(evt["answer"])
                        except Exception:
                            pass

    # Track gpt-4o-mini tokens (input estimate before stream, output after)
    await _track_gpt4o_tokens(input_token_est, 0)  # pre-track input

    # Update streak on chat activity
    await _update_streak(user["id"])

    # Track session + XP trigger
    xp_earned = 0
    if req.conversation_id:
        xp_earned = await _update_session(user["id"], req.agent, req.conversation_id)

    # Wrap stream to append XP event if earned + track output tokens
    async def stream_with_xp():
        async for chunk in stream():
            yield chunk
        # Track output tokens after stream completes
        full_answer = "".join(collected_answer)
        output_tokens = _count_tokens(full_answer)
        await _track_gpt4o_tokens(0, output_tokens)
        # Phase 7 — parse Teacher JSON, enqueue silenced + complete addressed.
        # Flag-gated (no-op when off). Best-effort: never crash the stream on parse error.
        if SPACED_RETRIEVAL_ENABLED and eleve_id:
            try:
                parsed = lang.parse_response(full_answer)
                if parsed.parse_ok:
                    await _persist_spaced_retrieval(
                        eleve_id, domain,
                        parsed.silenced_for_spaced_retrieval,
                        parsed.spaced_retrieval_addressed,
                    )
            except Exception as e:
                logger.warning("spaced_retrieval post-turn persist skipped: %s", e)
        if xp_earned > 0:
            xp_event = json.dumps({"event": "xp_earned", "amount": xp_earned, "reason": "session"})
            yield f"data: {xp_event}\n\n"

    return StreamingResponse(stream_with_xp(), media_type="text/event-stream")


@router.get("/api/chat/token-usage")
async def token_usage(user: dict = Depends(get_current_user)):
    """Current daily gpt-4o-mini token usage."""
    usage = await get_gpt4o_usage()
    usage["model"] = _current_dify_model
    return usage


@router.get("/api/chat/conversations")
async def chat_conversations(agent: str = "teacher", user: dict = Depends(get_current_user)):
    """List conversations for a user/agent from Dify."""
    dify_key = get_dify_key(agent)
    dify_user = user.get("dify_user_id") or f"user_{user['id']}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(
            f"{DIFY_API_URL}/conversations",
            params={"user": dify_user, "limit": 20},
            headers={"Authorization": f"Bearer {dify_key}"},
        )
    if res.status_code != 200:
        return {"data": []}

    data = res.json()
    return data


@router.get("/api/chat/messages")
async def chat_messages(
    conversation_id: str,
    agent: str = "teacher",
    user: dict = Depends(get_current_user),
):
    """Get message history for a conversation from Dify."""
    dify_key = get_dify_key(agent)
    dify_user = user.get("dify_user_id") or f"user_{user['id']}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(
            f"{DIFY_API_URL}/messages",
            params={
                "user": dify_user,
                "conversation_id": conversation_id,
                "limit": 100,
            },
            headers={"Authorization": f"Bearer {dify_key}"},
        )
    if res.status_code != 200:
        return {"data": []}

    return res.json()


async def _update_streak(user_id: int):
    """Update streak: if last_active was yesterday → increment, else reset to 1."""
    today = date.today()
    async with db.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT last_active_date, current_streak, longest_streak, freeze_count FROM streaks WHERE user_id = $1 FOR UPDATE",
                user_id,
            )
            if not row:
                await conn.execute(
                    """INSERT INTO streaks (user_id, current_streak, longest_streak, last_active_date, total_sessions)
                       VALUES ($1, 1, 1, $2, 1) ON CONFLICT (user_id) DO NOTHING""",
                    user_id, today,
                )
                return

            last = row["last_active_date"]
            current = row["current_streak"]
            longest = row["longest_streak"]

            if last == today:
                return  # Already counted today

            freeze_count = row.get("freeze_count", 0) if "freeze_count" in row.keys() else 0

            if last and (today - last).days == 1:
                new_streak = current + 1
            elif last and (today - last).days == 2 and freeze_count > 0:
                new_streak = current + 1
                await conn.execute(
                    "UPDATE streaks SET freeze_count = freeze_count - 1, freeze_used_date = $1 WHERE user_id = $2",
                    last + timedelta(days=1), user_id,
                )
            else:
                new_streak = 1

            if new_streak > 0 and new_streak % 7 == 0 and freeze_count < 2:
                await conn.execute(
                    "UPDATE streaks SET freeze_count = LEAST(freeze_count + 1, 2) WHERE user_id = $1",
                    user_id,
                )

            new_longest = max(longest, new_streak)
            await conn.execute(
                """UPDATE streaks SET current_streak = $1, longest_streak = $2,
                   last_active_date = $3, total_sessions = total_sessions + 1
                   WHERE user_id = $4""",
                new_streak, new_longest, today, user_id,
            )


async def _update_session(user_id: int, agent: str, conversation_id: str) -> int:
    """Track session activity in user_sessions. Returns XP earned (0 or 50)."""
    xp_earned = 0
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, message_count FROM user_sessions
               WHERE user_id = $1 AND agent_name = $2 AND dify_conversation_id = $3""",
            user_id, agent, conversation_id,
        )
        if row:
            new_count = row["message_count"] + 1
            await conn.execute(
                """UPDATE user_sessions SET last_message_at = NOW(), message_count = $1
                   WHERE id = $2""",
                new_count, row["id"],
            )
            # XP trigger: exactly at 10 messages
            if new_count == 10:
                await conn.execute(
                    """INSERT INTO xp_log (user_id, amount, reason, agent_name)
                       VALUES ($1, 50, 'session_10msg', $2)""",
                    user_id, agent,
                )
                xp_earned = 50
        else:
            await conn.execute(
                """INSERT INTO user_sessions (user_id, agent_name, dify_conversation_id, last_message_at, message_count)
                   VALUES ($1, $2, $3, NOW(), 1)""",
                user_id, agent, conversation_id,
            )
    return xp_earned
