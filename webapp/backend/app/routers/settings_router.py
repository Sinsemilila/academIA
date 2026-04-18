"""Profile settings, password change, active sessions, recommendations."""

import json
import secrets
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from ..models import UpdateProfileRequest, ChangePasswordRequest, ModeChangeRequest
from ..auth import get_current_user, verify_password, hash_password
from ..rate_limit import limiter
from ..domain_registry import chat_url_for_domain
from .. import database as db

router = APIRouter(tags=["settings"])


# ── Profile update ────────────────────────────────────
@router.patch("/api/me/profile")
async def update_profile(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    """Update display name, avatar color, theme, daily goal, and personality prefs."""
    updates = []
    values = []
    idx = 1

    for field in ["display_name", "avatar_color", "theme", "daily_goal_minutes"]:
        val = getattr(req, field, None)
        if val is not None:
            updates.append(f"{field} = ${idx}")
            values.append(val)
            idx += 1

    async with db.pool.acquire() as conn:
        if updates:
            values.append(user["id"])
            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ${idx}"
            await conn.execute(sql, *values)

        # Personality fields → profils_eleves.personnalite (JSONB)
        eleve_id = user.get("eleve_id")
        if eleve_id:
            perso_updates = {}
            if req.centres_interet is not None:
                perso_updates["centres_interet"] = req.centres_interet
            if req.style_correction is not None:
                perso_updates["style_correction"] = req.style_correction
            domain = req.domain or "en"
            for key, val in perso_updates.items():
                await conn.execute(
                    "UPDATE profils_eleves SET personnalite = jsonb_set("
                    "COALESCE(personnalite, '{}'::jsonb), $1, $2::jsonb"
                    ") WHERE eleve_id = $3 AND domain = $4",
                    [key], json.dumps(val), eleve_id, domain,
                )

    return {"ok": True}


# ── Mode change ──────────────────────────────────────
@router.patch("/api/me/mode")
async def change_mode(req: ModeChangeRequest, user: dict = Depends(get_current_user)):
    """Change learning mode (structure/libre) — takes effect immediately."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=400, detail="Pas de profil eleve")

    domain = req.domain or "en"
    async with db.pool.acquire() as conn:
        await conn.execute(
            """UPDATE profils_eleves SET mode_apprentissage = $1
               WHERE eleve_id = $2 AND domain = $3""",
            req.mode, eleve_id, domain,
        )

    return {"ok": True, "mode": req.mode}


# ── Password change ───────────────────────────────────
@router.post("/api/me/password")
async def change_password(
    req: ChangePasswordRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    limiter.check(request, max_requests=5, window_seconds=300)

    if not verify_password(req.current_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

    new_hash = hash_password(req.new_password)
    async with db.pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET password_hash = $1 WHERE id = $2",
            new_hash, user["id"],
        )

    return {"ok": True, "message": "Mot de passe mis a jour"}


# ── Full user settings (for profile page load) ───────
@router.get("/api/me/settings")
async def get_settings(domain: str = "en", user: dict = Depends(get_current_user)):
    # Read personality from profils_eleves (scoped to domain)
    centres_interet = ""
    style_correction = ""
    eleve_id = user.get("eleve_id")
    if eleve_id:
        async with db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT personnalite FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
                eleve_id, domain,
            )
            if row and row["personnalite"]:
                perso = row["personnalite"] if isinstance(row["personnalite"], dict) else json.loads(row["personnalite"])
                centres_interet = perso.get("centres_interet", "")
                style_correction = perso.get("style_correction", "")

    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "avatar_color": user.get("avatar_color", "#3b82f6"),
        "theme": user.get("theme", "dark"),
        "daily_goal_minutes": user.get("daily_goal_minutes", 15),
        "is_admin": user.get("is_admin", False),
        "created_at": str(user.get("created_at", "")),
        "centres_interet": centres_interet,
        "style_correction": style_correction,
    }


# ── Active sessions ──────────────────────────────────
@router.get("/api/me/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, device_info, ip_address, last_active, created_at
               FROM active_sessions WHERE user_id = $1
               ORDER BY last_active DESC""",
            user["id"],
        )
    return {
        "sessions": [
            {
                "id": r["id"],
                "device": r["device_info"],
                "ip": r["ip_address"],
                "last_active": r["last_active"].isoformat() if r["last_active"] else None,
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
    }


@router.delete("/api/me/sessions/{session_id}")
async def revoke_session(session_id: int, user: dict = Depends(get_current_user)):
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM active_sessions WHERE id = $1 AND user_id = $2",
            session_id, user["id"],
        )
    return {"ok": True}


@router.delete("/api/me/sessions")
async def revoke_all_sessions(user: dict = Depends(get_current_user)):
    async with db.pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM active_sessions WHERE user_id = $1",
            user["id"],
        )
    return {"ok": True}


# ── Recommendation engine (unified — error-based) ─────
@router.get("/api/me/recommendation")
async def get_recommendation(domain: str = "en", user: dict = Depends(get_current_user)):
    """Return a single contextual recommendation based on error profile."""
    chat_url = chat_url_for_domain(domain)
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"type": "start", "message": "Commence ta premiere session pour debloquer ton profil !",
                "action": chat_url, "label": "Commencer"}

    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT niveau_global, derniere_session FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
            eleve_id, domain)
        if not row or not row["niveau_global"]:
            return {"type": "start", "message": "Commence ta premiere session pour debloquer ton profil !",
                    "action": chat_url, "label": "Commencer"}
        derniere = row["derniere_session"]

    # Days since last session — still useful as top priority
    today = date.today()
    days_absent = 0
    if derniere:
        days_absent = (today - derniere.date()).days if isinstance(derniere, datetime) else 0

    if days_absent >= 3:
        return {
            "type": "comeback",
            "message": f"Ca fait {days_absent} jours ! On reprend en douceur ?",
            "action": chat_url,
            "label": "Reprendre",
        }

    # Delegate to error profile recommendation
    from .error_analysis_router import _build_error_profile
    profile = await _build_error_profile(eleve_id, domain)
    return profile.get("recommendation", {
        "type": "continue",
        "message": "Continue ta progression, tu avances bien !",
        "action": chat_url,
        "label": "Continuer",
    })


# ── Daily progress (for goal tracking) ───────────────
@router.get("/api/me/daily-progress")
async def get_daily_progress(user: dict = Depends(get_current_user)):
    """Return today's practice time vs daily goal."""
    today = date.today()
    goal = user.get("daily_goal_minutes", 15)

    async with db.pool.acquire() as conn:
        # Sum today's session durations
        total_seconds = await conn.fetchval(
            """SELECT COALESCE(SUM(duration_seconds), 0) FROM user_sessions
               WHERE user_id = $1 AND started_at::date = $2""",
            user["id"], today,
        )

    minutes_done = total_seconds // 60
    return {
        "goal_minutes": goal,
        "done_minutes": minutes_done,
        "pct": min(round(minutes_done / goal * 100), 100) if goal > 0 else 0,
        "completed": minutes_done >= goal,
    }


# ── Weekly recap ──────────────────────────────────────
@router.get("/api/me/weekly-recap")
async def get_weekly_recap(domain: str = "en", user: dict = Depends(get_current_user)):
    """Return a weekly summary card."""
    eleve_id = user.get("eleve_id")
    user_id = user["id"]
    week_ago = datetime.now() - timedelta(days=7)

    async with db.pool.acquire() as conn:
        # Sessions this week
        sessions = await conn.fetchval(
            "SELECT COUNT(*) FROM user_sessions WHERE user_id = $1 AND started_at >= $2",
            user_id, week_ago,
        )
        # Total minutes this week (from actual session timestamps)
        total_sec = await conn.fetchval(
            """SELECT COALESCE(SUM(EXTRACT(EPOCH FROM (last_message_at - started_at))::int), 0)
               FROM user_sessions WHERE user_id = $1 AND started_at >= $2""",
            user_id, week_ago,
        )
        # XP this week
        xp_week = await conn.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM xp_log WHERE user_id = $1 AND created_at >= $2",
            user_id, week_ago,
        )
        # Streak
        streak_row = await conn.fetchrow(
            "SELECT current_streak, longest_streak FROM streaks WHERE user_id = $1",
            user_id,
        )
        # Concepts with score > 0 this week
        concepts_worked = 0
        if eleve_id:
            row = await conn.fetchrow(
                "SELECT scores_confiance FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
                eleve_id, domain,
            )
            if row and row["scores_confiance"]:
                sc = row["scores_confiance"]
                if isinstance(sc, str):
                    import json as _json
                    sc = _json.loads(sc)
                concepts_worked = sum(1 for v in sc.values()
                    if (v.get("score", 0) if isinstance(v, dict) else v) > 0)

    return {
        "sessions": sessions or 0,
        "minutes": (total_sec or 0) // 60,
        "xp": xp_week or 0,
        "streak": streak_row["current_streak"] if streak_row else 0,
        "longest_streak": streak_row["longest_streak"] if streak_row else 0,
        "concepts_worked": concepts_worked,
    }
