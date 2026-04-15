import json
import os
import httpx
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..models import ChatRequest
from ..auth import get_current_user
from ..rate_limit import limiter
from .. import database as db
from ..error_taxonomy.rules import detect_errors, ERROR_CODE_TO_FAMILY
import yaml
import tiktoken
from pathlib import Path

# ── Daily token budget for gpt-4o-mini (free tier protection) ──
_GPT4O_DAILY_LIMIT = 1_500_000
_gpt4o_token_counter = {"date": "", "tokens": 0, "loaded": False}
_tiktoken_enc = tiktoken.encoding_for_model("gpt-4o-mini")


def _count_tokens(text: str) -> int:
    return len(_tiktoken_enc.encode(text)) if text else 0


async def _load_daily_tokens() -> None:
    """Load today's token count from DB on first call."""
    if _gpt4o_token_counter["loaded"] and _gpt4o_token_counter["date"] == date.today().isoformat():
        return
    today = date.today().isoformat()
    try:
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT tokens_used FROM token_usage_daily WHERE usage_date = $1",
                date.today())
            _gpt4o_token_counter["tokens"] = row["tokens_used"] if row else 0
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
    """Aggregate today's spend from LiteLLM_SpendLogs by model_group.
    Returns None if LiteLLM DB is unavailable (caller should fall back to local estimate)."""
    if db.litellm_pool is None:
        return None
    try:
        async with db.litellm_pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT model_group AS name,
                          COALESCE(SUM(prompt_tokens + completion_tokens), 0)::bigint AS tokens,
                          COALESCE(SUM(spend), 0)::float AS cost_usd
                   FROM "LiteLLM_SpendLogs"
                   WHERE "startTime"::date = CURRENT_DATE
                     AND model_group IS NOT NULL
                   GROUP BY model_group
                   ORDER BY tokens DESC""")
            return [dict(r) for r in rows]
    except Exception:
        return None


async def get_gpt4o_usage() -> dict:
    """Return current daily token usage. Source: LiteLLM SpendLogs (truth, batched ~30-60s).
    Fallback: local tiktoken counter (real-time, used for auto-switch decisions)."""
    await _load_daily_tokens()
    local_estimate = _gpt4o_token_counter["tokens"]
    today = _gpt4o_token_counter["date"]

    litellm_rows = await _fetch_litellm_usage()
    if litellm_rows is None:
        # Fallback: local tiktoken estimate
        return {
            "date": today,
            "tokens": local_estimate,
            "limit": _GPT4O_DAILY_LIMIT,
            "pct": round(local_estimate / _GPT4O_DAILY_LIMIT * 100, 1),
            "exceeded": local_estimate >= _GPT4O_DAILY_LIMIT,
            "models": [],
            "source": "estimate",
            "local_estimate": local_estimate,
        }

    base_tokens = next((r["tokens"] for r in litellm_rows if r["name"] == "gpt-4o-mini"), 0)
    return {
        "date": today,
        "tokens": base_tokens,
        "limit": _GPT4O_DAILY_LIMIT,
        "pct": round(base_tokens / _GPT4O_DAILY_LIMIT * 100, 1),
        "exceeded": base_tokens >= _GPT4O_DAILY_LIMIT,
        "models": litellm_rows,
        "source": "litellm",
        "local_estimate": local_estimate,
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


# Load tolerance matrix once at import
_TOLERANCE_MATRIX = {}
_tm_path = Path(__file__).parent.parent / "config" / "tolerance_matrix.yaml"
if _tm_path.exists():
    with open(_tm_path) as f:
        _tm = yaml.safe_load(f)
        _TOLERANCE_MATRIX = _tm.get("matrix", {})

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
    # Future agents via env vars: DIFY_KEY_MAESTRO, DIFY_KEY_SENSEI, etc.
}


def get_dify_key(agent: str) -> str:
    key = DIFY_APP_KEYS.get(agent)
    if not key:
        raise HTTPException(status_code=404, detail=f"Agent '{agent}' non disponible")
    return key


@router.post("/api/chat/send")
async def chat_send(req: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """Stream a chat message through Dify API."""
    # Rate limit: 30 messages per minute per IP
    limiter.check(request, max_requests=30, window_seconds=60)
    dify_key = get_dify_key(req.agent)
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
    detections = detect_errors(req.message)
    niveau = ""
    eleve_id = user.get("eleve_id")
    if eleve_id and detections:
        try:
            async with db.pool.acquire() as conn:
                niveau = await conn.fetchval(
                    "SELECT niveau_global FROM profils_eleves WHERE eleve_id = $1 AND domaine = 'anglais'",
                    eleve_id) or ""
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
