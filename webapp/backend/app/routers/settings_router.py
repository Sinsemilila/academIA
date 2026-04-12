"""Profile settings, password change, active sessions, recommendations."""

import json
import secrets
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from ..models import UpdateProfileRequest, ChangePasswordRequest, ModeChangeRequest
from ..auth import get_current_user, verify_password, hash_password
from ..rate_limit import limiter
from .. import database as db

router = APIRouter(tags=["settings"])


# ── Profile update ────────────────────────────────────
@router.patch("/api/me/profile")
async def update_profile(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    """Update display name, avatar color, theme, daily goal."""
    updates = []
    values = []
    idx = 1

    for field in ["display_name", "avatar_color", "theme", "daily_goal_minutes"]:
        val = getattr(req, field, None)
        if val is not None:
            updates.append(f"{field} = ${idx}")
            values.append(val)
            idx += 1

    if not updates:
        return {"ok": True}

    values.append(user["id"])
    sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ${idx}"

    async with db.pool.acquire() as conn:
        await conn.execute(sql, *values)

    return {"ok": True}


# ── Mode change ──────────────────────────────────────
@router.patch("/api/me/mode")
async def change_mode(req: ModeChangeRequest, user: dict = Depends(get_current_user)):
    """Change learning mode (structure/libre) — takes effect immediately."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        raise HTTPException(status_code=400, detail="Pas de profil eleve")

    async with db.pool.acquire() as conn:
        await conn.execute(
            """UPDATE profils_eleves SET mode_apprentissage = $1
               WHERE eleve_id = $2 AND domaine = 'anglais'""",
            req.mode, eleve_id,
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
async def get_settings(user: dict = Depends(get_current_user)):
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


# ── Recommendation engine ────────────────────────────
@router.get("/api/me/recommendation")
async def get_recommendation(domain: str = "anglais", user: dict = Depends(get_current_user)):
    """Return a single contextual recommendation for the dashboard."""
    eleve_id = user.get("eleve_id")
    if not eleve_id:
        return {"type": "start", "message": "Commence ta premiere session pour debloquer ton profil !",
                "action": "/chat/teacher", "label": "Commencer"}

    async with db.pool.acquire() as conn:
        # Profile data
        row = await conn.fetchrow(
            """SELECT niveau_global, scores_confiance, derniere_session,
                      mode_apprentissage, dernier_examen
               FROM profils_eleves WHERE eleve_id = $1 AND domaine = $2""",
            eleve_id, domain,
        )
        if not row or not row["niveau_global"]:
            return {"type": "start", "message": "Commence ta premiere session pour debloquer ton profil !",
                    "action": "/chat/teacher", "label": "Commencer"}

        niveau = row["niveau_global"]
        derniere = row["derniere_session"]
        scores_raw = row["scores_confiance"] or {}
        if isinstance(scores_raw, str):
            scores_raw = json.loads(scores_raw)

        # Parse scores
        scores = {}
        for k, v in scores_raw.items():
            scores[k] = v.get("score", 0) if isinstance(v, dict) else v

        # Get concept_keys for this level
        ck_row = await conn.fetchval(
            "SELECT concept_keys FROM curriculums WHERE domaine = $1 AND niveau = $2",
            domain, niveau,
        )
        concept_keys = ck_row if isinstance(ck_row, list) else json.loads(ck_row or "[]")

        # Streak data
        streak_row = await conn.fetchrow(
            "SELECT current_streak, freeze_count FROM streaks WHERE user_id = $1",
            user["id"],
        )

    # Decision logic
    today = date.today()

    # 1. Days since last session
    days_absent = 0
    if derniere:
        days_absent = (today - derniere.date()).days if isinstance(derniere, datetime) else 0

    # 2. Weakest concept
    weakest_concept = None
    weakest_score = 100
    for k in concept_keys:
        s = scores.get(k, 0)
        if 0 < s < weakest_score:
            weakest_score = s
            weakest_concept = k

    # 3. Untested count
    untested = [k for k in concept_keys if scores.get(k, 0) == 0]
    tested = [k for k in concept_keys if scores.get(k, 0) > 0]
    mastered = [k for k in concept_keys if scores.get(k, 0) >= 80]

    # 4. Exam eligibility
    all_tested = len(untested) == 0 and len(concept_keys) > 0
    pct_mastered = len(mastered) / len(concept_keys) * 100 if concept_keys else 0

    # Priority-based recommendation
    if days_absent >= 3:
        return {
            "type": "comeback",
            "message": f"Ca fait {days_absent} jours ! On reprend en douceur ?",
            "action": "/chat/teacher",
            "label": "Reprendre",
        }

    if all_tested and pct_mastered >= 80:
        return {
            "type": "exam",
            "message": f"Tu maitrises {len(mastered)}/{len(concept_keys)} concepts. Pret pour l'examen ?",
            "action": "/chat/teacher",
            "label": "Passer l'examen",
        }

    if weakest_concept and weakest_score < 50:
        pretty = weakest_concept.replace("_", " ").title()
        return {
            "type": "weakness",
            "message": f"Focus recommande : {pretty} (score {weakest_score}%)",
            "action": "/chat/teacher",
            "label": "Travailler ce concept",
        }

    if len(untested) > 0:
        return {
            "type": "explore",
            "message": f"Il reste {len(untested)} concept{'s' if len(untested) > 1 else ''} a decouvrir en {niveau}",
            "action": "/chat/teacher",
            "label": "Explorer",
        }

    return {
        "type": "continue",
        "message": "Continue ta progression, tu avances bien !",
        "action": "/chat/teacher",
        "label": "Continuer",
    }


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
async def get_weekly_recap(domain: str = "anglais", user: dict = Depends(get_current_user)):
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
        # Total minutes this week
        total_sec = await conn.fetchval(
            "SELECT COALESCE(SUM(duration_seconds), 0) FROM user_sessions WHERE user_id = $1 AND started_at >= $2",
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
        # Concepts improved (compare snapshots?)
        concepts_worked = 0
        if eleve_id:
            snap_count = await conn.fetchval(
                "SELECT COUNT(*) FROM snapshots_session WHERE eleve_id = $1 AND created_at >= $2",
                eleve_id, week_ago,
            )
            concepts_worked = snap_count or 0

    return {
        "sessions": sessions or 0,
        "minutes": (total_sec or 0) // 60,
        "xp": xp_week or 0,
        "streak": streak_row["current_streak"] if streak_row else 0,
        "longest_streak": streak_row["longest_streak"] if streak_row else 0,
        "concepts_worked": concepts_worked,
    }
