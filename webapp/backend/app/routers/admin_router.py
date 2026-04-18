"""
AcademIA — Admin & internal endpoints
Admin dashboard + XP triggers for exam/promotion.
"""

import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from ..auth import get_current_user, require_admin
from .. import database as db

logger = logging.getLogger("academie-api.admin")

router = APIRouter()

INTERNAL_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "REDACTED_INTERNAL_API_TOKEN")


# ── XP triggers (internal, called by n8n) ────────────────

class ExamResultRequest(BaseModel):
    username: str
    passed: bool
    score: float
    niveau_from: str
    niveau_to: str | None = None


@router.post("/internal/exam-result")
async def exam_result(req: ExamResultRequest, x_internal_token: str = Header(None)):
    """Award XP on exam pass (+200) and promotion (+500). Called by n8n after exam scoring."""
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT u.id FROM users u JOIN eleves e ON u.eleve_id = e.id WHERE e.username = $1",
            req.username)
        if not user:
            raise HTTPException(status_code=404, detail=f"User '{req.username}' not found")

        user_id = user["id"]
        xp_earned = 0

        if req.passed:
            await conn.execute(
                "INSERT INTO xp_log (user_id, amount, reason, agent_name) VALUES ($1, 200, 'exam_pass', 'teacher')",
                user_id)
            xp_earned += 200
            logger.info("XP +200 exam_pass for %s (score=%.0f)", req.username, req.score)

            if req.niveau_to and req.niveau_to != req.niveau_from:
                await conn.execute(
                    "INSERT INTO xp_log (user_id, amount, reason, agent_name) VALUES ($1, 500, 'promotion', 'teacher')",
                    user_id)
                xp_earned += 500
                logger.info("XP +500 promotion for %s (%s → %s)", req.username, req.niveau_from, req.niveau_to)

    return {"xp_earned": xp_earned, "passed": req.passed}


# ── Admin dashboard ──────────────────────────────────────

@router.get("/api/admin/users")
async def list_users(domain: str = "en", admin: dict = Depends(require_admin)):
    """List all users with stats for admin dashboard. Profile stats scoped to `domain` (ISO)."""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                u.id, u.username, u.display_name, u.is_admin, u.exam_access, u.created_at,
                p.niveau_global, p.derniere_session, p.mode_apprentissage,
                s.current_streak, s.longest_streak, s.total_sessions,
                COALESCE(xp.total_xp, 0) as total_xp,
                u.last_seen_at
            FROM users u
            LEFT JOIN eleves e ON u.eleve_id = e.id
            LEFT JOIN profils_eleves p ON e.id = p.eleve_id AND p.domain = $1
            LEFT JOIN streaks s ON u.id = s.user_id
            LEFT JOIN (SELECT user_id, SUM(amount) as total_xp FROM xp_log GROUP BY user_id) xp ON u.id = xp.user_id
            ORDER BY u.last_seen_at DESC NULLS LAST
        """, domain)

    return [
        {
            "id": r["id"],
            "username": r["username"],
            "display_name": r["display_name"],
            "is_admin": r["is_admin"],
            "exam_access": r["exam_access"],
            "created_at": str(r["created_at"]) if r["created_at"] else None,
            "niveau": r["niveau_global"],
            "derniere_session": str(r["derniere_session"]) if r["derniere_session"] else None,
            "mode": r["mode_apprentissage"],
            "current_streak": r["current_streak"] or 0,
            "longest_streak": r["longest_streak"] or 0,
            "total_sessions": r["total_sessions"] or 0,
            "total_xp": r["total_xp"],
            "online": r["last_seen_at"] is not None and (datetime.now() - r["last_seen_at"]).total_seconds() < 900,
            "last_seen": str(r["last_seen_at"]) if r["last_seen_at"] else None,
        }
        for r in rows
    ]


@router.post("/api/admin/reset-profile/{username}")
async def reset_profile(username: str, admin: dict = Depends(require_admin)):
    """Reset a student — full wipe. Works even if no eleve record exists."""
    async with db.pool.acquire() as conn:
        user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
        if not user_row:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        new_dify_id = str(uuid.uuid4())
        async with conn.transaction():
            eleve = await conn.fetchrow("SELECT id FROM eleves WHERE username = $1", username)
            if eleve:
                await conn.execute("DELETE FROM profils_eleves WHERE eleve_id = $1", eleve["id"])
                await conn.execute("DELETE FROM error_log WHERE eleve_id = $1", eleve["id"])
                await conn.execute("DELETE FROM snapshots_session WHERE eleve_id = $1", eleve["id"])

            await conn.execute("DELETE FROM xp_log WHERE user_id = $1", user_row["id"])
            await conn.execute("DELETE FROM streaks WHERE user_id = $1", user_row["id"])
            await conn.execute("DELETE FROM user_sessions WHERE user_id = $1", user_row["id"])
            await conn.execute(
                "UPDATE users SET dify_user_id = $1 WHERE username = $2",
                new_dify_id, username)

    logger.info("Profile reset for %s by admin %s (new dify_id=%s)", username, admin["username"], new_dify_id)
    return {"ok": True, "message": f"Profile reset for {username}"}


@router.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """Delete a user and all related data."""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    async with db.pool.acquire() as conn:
        user = await conn.fetchrow("SELECT username, eleve_id FROM users WHERE id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        async with conn.transaction():
            eleve_id = user["eleve_id"]
            if eleve_id:
                await conn.execute("DELETE FROM error_log WHERE eleve_id = $1", eleve_id)
                await conn.execute("DELETE FROM snapshots_session WHERE eleve_id = $1", eleve_id)
                await conn.execute("DELETE FROM profils_eleves WHERE eleve_id = $1", eleve_id)

            await conn.execute("DELETE FROM streaks WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM xp_log WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM user_sessions WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)

            if eleve_id:
                await conn.execute("DELETE FROM eleves WHERE id = $1", eleve_id)

    logger.info("User %s (id=%d) deleted by admin %s", user["username"], user_id, admin["username"])
    return {"ok": True, "message": f"User {user['username']} deleted"}
