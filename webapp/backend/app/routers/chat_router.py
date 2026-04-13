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
from ..error_taxonomy.rules import detect_errors

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
    detections = detect_errors(req.message)
    if detections:
        lines = [f"- \"{d.original_text}\" → \"{d.suggested_correction}\" ({d.reasoning})" for d in detections]
        dify_inputs["error_feedback"] = "\n".join(lines)

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

    payload = {
        "inputs": dify_inputs,
        "query": req.message,
        "user": dify_user,
        "response_mode": "streaming",
        "conversation_id": req.conversation_id or "",
    }

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

    # Update streak on chat activity
    await _update_streak(user["id"])

    # Track session + XP trigger
    xp_earned = 0
    if req.conversation_id:
        xp_earned = await _update_session(user["id"], req.agent, req.conversation_id)

    # Wrap stream to append XP event if earned
    async def stream_with_xp():
        async for chunk in stream():
            yield chunk
        if xp_earned > 0:
            xp_event = json.dumps({"event": "xp_earned", "amount": xp_earned, "reason": "session"})
            yield f"data: {xp_event}\n\n"

    return StreamingResponse(stream_with_xp(), media_type="text/event-stream")


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
