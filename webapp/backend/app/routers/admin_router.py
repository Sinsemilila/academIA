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

# Fail-fast: must be set via webapp/.env.sops, no guessable fallback.
INTERNAL_TOKEN = os.environ["INTERNAL_API_TOKEN"]


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


# ── Per-domain tables (must ALL be DELETE-scoped when `domain` is specified) ──
# When adding a new table with a `domain` column, extend this list + the
# per-domain DELETE block below. Also mirror it in delete_user() for consistency.
#   profils_eleves (Sprint 5)
#   error_log (Sprint 5)
#   snapshots_session (Sprint 5)
#   learner_profiles (Sprint 5 Phase 5 QCM)
#   consolidation_events (Sprint 6 Session 36)
#   spaced_retrieval_queue (Sprint 5)
# User-global tables (never scoped by domain — reset globally):
#   xp_log, streaks, user_sessions


@router.post("/api/admin/reset-profile/{username}")
async def reset_profile(
    username: str,
    domain: str | None = None,
    admin: dict = Depends(require_admin),
):
    """Reset a student profile.

    - `?domain=en` (or es/…) → scope DELETE to that domain only on per-domain
      tables. User-global tables (xp_log, streaks, user_sessions) are LEFT
      INTACT so the learner keeps their activity history cross-domains.
    - No `domain` query param → legacy global wipe: every per-domain table
      purged for all domains + user-global tables reset.

    Works even if no eleve record exists.
    """
    if domain is not None and not domain.isalpha():
        raise HTTPException(status_code=422, detail="invalid domain code")

    async with db.pool.acquire() as conn:
        user_row = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
        if not user_row:
            raise HTTPException(status_code=404, detail=f"User '{username}' not found")

        new_dify_id = str(uuid.uuid4())
        async with conn.transaction():
            eleve = await conn.fetchrow("SELECT id FROM eleves WHERE username = $1", username)
            if eleve:
                eid = eleve["id"]
                if domain:
                    # Per-domain wipe
                    await conn.execute(
                        "DELETE FROM profils_eleves WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    await conn.execute(
                        "DELETE FROM error_log WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    await conn.execute(
                        "DELETE FROM snapshots_session WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    await conn.execute(
                        "DELETE FROM learner_profiles WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    await conn.execute(
                        "DELETE FROM consolidation_events WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    await conn.execute(
                        "DELETE FROM spaced_retrieval_queue WHERE eleve_id = $1 AND domain = $2",
                        eid, domain)
                    # User-global tables untouched when domain specified
                else:
                    # Global wipe: all domains on per-domain tables + user-global tables
                    await conn.execute("DELETE FROM profils_eleves WHERE eleve_id = $1", eid)
                    await conn.execute("DELETE FROM error_log WHERE eleve_id = $1", eid)
                    await conn.execute("DELETE FROM snapshots_session WHERE eleve_id = $1", eid)
                    await conn.execute("DELETE FROM learner_profiles WHERE eleve_id = $1", eid)
                    await conn.execute("DELETE FROM consolidation_events WHERE eleve_id = $1", eid)
                    await conn.execute("DELETE FROM spaced_retrieval_queue WHERE eleve_id = $1", eid)

            if not domain:
                # Only reset user-global tables on global wipe
                await conn.execute("DELETE FROM xp_log WHERE user_id = $1", user_row["id"])
                await conn.execute("DELETE FROM streaks WHERE user_id = $1", user_row["id"])
                await conn.execute("DELETE FROM user_sessions WHERE user_id = $1", user_row["id"])
                await conn.execute(
                    "UPDATE users SET dify_user_id = $1 WHERE username = $2",
                    new_dify_id, username)

    scope_label = f"domain={domain}" if domain else "global (all domains + user data)"
    logger.info(
        "Profile reset for %s by admin %s (%s%s)",
        username, admin["username"], scope_label,
        f", new dify_id={new_dify_id}" if not domain else "",
    )
    return {
        "ok": True,
        "domain": domain,
        "message": f"Profile reset for {username} ({scope_label})",
    }


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


# ── Phase D v2 — cache stats dashboard ────────────────────

@router.get("/api/admin/cache-stats")
async def cache_stats(hours: int = 24, admin: dict = Depends(require_admin)):
    """Aggregate OpenAI prompt-caching telemetry from the litellm_cache_stats
    sidecar. Returns summary + per-hour time series + per-model breakdown.
    Feeds the /admin dashboard cache section (Phase D v2)."""
    hours = max(1, min(hours, 24 * 30))  # clamp [1h, 30d]
    async with db.pool.acquire() as conn:
        summary = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS requests,
              COALESCE(SUM(prompt_tokens), 0)::int AS prompt_tokens,
              COALESCE(SUM(cached_tokens), 0)::int AS cached_tokens,
              COALESCE((SUM(cached_tokens)::float / NULLIF(SUM(prompt_tokens), 0) * 100)::int, 0) AS cache_pct
            FROM litellm_cache_stats
            WHERE started_at > NOW() - ($1 || ' hours')::interval
            """,
            str(hours),
        )
        by_hour = await conn.fetch(
            """
            SELECT
              date_trunc('hour', started_at) AS bucket,
              COUNT(*)::int AS requests,
              COALESCE(SUM(prompt_tokens), 0)::int AS prompt_tokens,
              COALESCE(SUM(cached_tokens), 0)::int AS cached_tokens
            FROM litellm_cache_stats
            WHERE started_at > NOW() - ($1 || ' hours')::interval
            GROUP BY bucket
            ORDER BY bucket
            """,
            str(hours),
        )
        by_model = await conn.fetch(
            """
            SELECT
              model,
              COUNT(*)::int AS requests,
              COALESCE(SUM(prompt_tokens), 0)::int AS prompt_tokens,
              COALESCE(SUM(cached_tokens), 0)::int AS cached_tokens,
              COALESCE((SUM(cached_tokens)::float / NULLIF(SUM(prompt_tokens), 0) * 100)::int, 0) AS cache_pct
            FROM litellm_cache_stats
            WHERE started_at > NOW() - ($1 || ' hours')::interval
            GROUP BY model
            ORDER BY prompt_tokens DESC
            """,
            str(hours),
        )
        # Session 41 Phase D v3 — alerting on hit rate drop vs rolling 7d baseline
        alerts = []
        try:
            baseline = await conn.fetchrow(
                """
                SELECT
                  COALESCE((SUM(cached_tokens)::float / NULLIF(SUM(prompt_tokens), 0) * 100)::int, 0) AS cache_pct,
                  COUNT(*) AS requests
                FROM litellm_cache_stats
                WHERE started_at > NOW() - INTERVAL '7 days'
                  AND started_at <= NOW() - ($1 || ' hours')::interval
                """,
                str(hours),
            )
            current_pct = (summary or {}).get("cache_pct") or 0
            baseline_pct = (baseline or {}).get("cache_pct") or 0
            baseline_req = (baseline or {}).get("requests") or 0
            # Only alert when baseline has enough samples (statistical significance)
            if baseline_req >= 20 and baseline_pct >= 10:
                delta = current_pct - baseline_pct
                if delta <= -20:
                    alerts.append({
                        "level": "critical",
                        "code": "cache_hit_drop",
                        "message": (
                            f"Cache hit rate dropped {abs(delta)}pp vs rolling 7d baseline "
                            f"({baseline_pct}% → {current_pct}%). Possible prompt drift."
                        ),
                        "baseline_pct": baseline_pct,
                        "current_pct": current_pct,
                        "delta_pp": delta,
                    })
                elif delta <= -10:
                    alerts.append({
                        "level": "warning",
                        "code": "cache_hit_soft_drop",
                        "message": (
                            f"Cache hit rate soft-dropped {abs(delta)}pp vs 7d baseline "
                            f"({baseline_pct}% → {current_pct}%). Monitor."
                        ),
                        "baseline_pct": baseline_pct,
                        "current_pct": current_pct,
                        "delta_pp": delta,
                    })
            # No requests recently (cache telemetry quiet) — soft signal
            if (summary or {}).get("requests", 0) == 0:
                alerts.append({
                    "level": "info",
                    "code": "no_traffic",
                    "message": f"No LiteLLM requests in last {hours}h. Cache telemetry quiet.",
                })
        except Exception as e:
            # Alerting is best-effort; never break the dashboard
            logger.warning("cache-stats alert compute failed: %s", e)

    return {
        "hours": hours,
        "summary": dict(summary or {}),
        "by_hour": [dict(r) for r in by_hour],
        "by_model": [dict(r) for r in by_model],
        "alerts": alerts,
    }


# ── Session 42 P3 — consolidation events analytics ────────────────────

@router.get("/api/admin/consolidation-events")
async def consolidation_events_stats(domain: str = "en", hours: int = 168,
                                     admin: dict = Depends(require_admin)):
    """Session 42 P3 — aggregate consolidation_events for admin dashboard.

    Returns summary (pending count, closed count, mini_exam pass rate),
    by_decision (GROUP BY user_decision), by_user (top 10 event count)
    over a configurable window (default 7 days).
    """
    hours = max(1, min(hours, 24 * 90))
    async with db.pool.acquire() as conn:
        # Summary
        summary = await conn.fetchrow(
            """
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE user_decision IS NULL) AS pending,
              COUNT(*) FILTER (WHERE user_decision IS NOT NULL) AS closed,
              COUNT(*) FILTER (WHERE mini_exam_triggered = true) AS mini_exam_count,
              COALESCE(AVG(mini_exam_score_pct) FILTER (WHERE mini_exam_score_pct IS NOT NULL), 0)::int AS avg_mini_exam_score,
              COUNT(*) FILTER (WHERE mini_exam_score_pct >= 75) AS mini_exam_pass,
              COUNT(*) FILTER (WHERE mini_exam_score_pct IS NOT NULL AND mini_exam_score_pct < 75) AS mini_exam_fail
            FROM consolidation_events
            WHERE domain = $1
              AND triggered_at > NOW() - ($2 || ' hours')::interval
            """,
            domain, str(hours),
        )

        # By decision
        by_decision = await conn.fetch(
            """
            SELECT
              COALESCE(user_decision, '(pending)') AS decision,
              COUNT(*)::int AS count,
              COALESCE(AVG(mini_exam_score_pct) FILTER (WHERE mini_exam_score_pct IS NOT NULL), 0)::int AS avg_score
            FROM consolidation_events
            WHERE domain = $1
              AND triggered_at > NOW() - ($2 || ' hours')::interval
            GROUP BY user_decision
            ORDER BY count DESC
            """,
            domain, str(hours),
        )

        # Top users by event count
        by_user = await conn.fetch(
            """
            SELECT
              u.username,
              COUNT(ce.id)::int AS event_count,
              COUNT(*) FILTER (WHERE ce.user_decision IS NULL)::int AS pending_count,
              MAX(ce.triggered_at) AS latest_event
            FROM consolidation_events ce
            LEFT JOIN eleves e ON e.id = ce.eleve_id
            LEFT JOIN users u ON u.eleve_id = e.id
            WHERE ce.domain = $1
              AND ce.triggered_at > NOW() - ($2 || ' hours')::interval
            GROUP BY u.username
            ORDER BY event_count DESC
            LIMIT 10
            """,
            domain, str(hours),
        )

        # By trigger reason
        by_trigger = await conn.fetch(
            """
            SELECT
              COALESCE(trigger_reason, '(unknown)') AS reason,
              COUNT(*)::int AS count
            FROM consolidation_events
            WHERE domain = $1
              AND triggered_at > NOW() - ($2 || ' hours')::interval
            GROUP BY trigger_reason
            ORDER BY count DESC
            """,
            domain, str(hours),
        )

    return {
        "domain": domain,
        "hours": hours,
        "summary": dict(summary or {}),
        "by_decision": [dict(r) for r in by_decision],
        "by_user": [
            {**dict(r), "latest_event": r["latest_event"].isoformat() if r["latest_event"] else None}
            for r in by_user
        ],
        "by_trigger": [dict(r) for r in by_trigger],
    }


# ── Session 42 O2 — oracle runs analytics ─────────────────────────────

@router.get("/api/admin/oracle-runs")
async def oracle_runs_stats(agent: str = "teacher_en", hours: int = 168,
                            admin: dict = Depends(require_admin)):
    """Session 42 O2b — aggregate oracle_run_log for dashboard.

    Returns :
      - summary : total runs, scenarios-rows, per-mode counts
      - recent_runs : 10 latest run_hash groups
      - by_dim : pass/fail/unknown counts per dim (LLM + lint) over window
      - by_verdict_day : time-series GROUP BY day for trend sparkline

    Scoped by agent + window (default 168h/7d).
    """
    hours = max(1, min(hours, 24 * 90))
    async with db.pool.acquire() as conn:
        summary = await conn.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total_rows,
              COUNT(DISTINCT run_hash)::int AS total_runs,
              COUNT(DISTINCT scenario_id)::int AS scenarios_touched
            FROM oracle_run_log
            WHERE agent = $1
              AND started_at > NOW() - ($2 || ' hours')::interval
            """,
            agent, str(hours),
        )
        recent_runs = await conn.fetch(
            """
            SELECT
              run_hash,
              MAX(started_at) AS started_at,
              mode,
              sha,
              COUNT(*)::int AS rows,
              COUNT(*) FILTER (WHERE verdict = 'pass')::int AS pass_count,
              COUNT(*) FILTER (WHERE verdict = 'fail')::int AS fail_count,
              COUNT(*) FILTER (WHERE verdict = 'unknown')::int AS unknown_count
            FROM oracle_run_log
            WHERE agent = $1
              AND started_at > NOW() - ($2 || ' hours')::interval
            GROUP BY run_hash, mode, sha
            ORDER BY MAX(started_at) DESC
            LIMIT 10
            """,
            agent, str(hours),
        )
        by_dim = await conn.fetch(
            """
            SELECT
              dim,
              COUNT(*)::int AS total,
              COUNT(*) FILTER (WHERE verdict = 'pass')::int AS pass,
              COUNT(*) FILTER (WHERE verdict = 'fail')::int AS fail,
              COUNT(*) FILTER (WHERE verdict = 'unknown')::int AS unknown,
              COALESCE((COUNT(*) FILTER (WHERE verdict = 'pass')::float
                        / NULLIF(COUNT(*), 0) * 100)::int, 0) AS pass_pct
            FROM oracle_run_log
            WHERE agent = $1
              AND started_at > NOW() - ($2 || ' hours')::interval
            GROUP BY dim
            ORDER BY total DESC
            """,
            agent, str(hours),
        )
    return {
        "agent": agent,
        "hours": hours,
        "summary": dict(summary or {}),
        "recent_runs": [
            {**dict(r), "started_at": r["started_at"].isoformat() if r["started_at"] else None}
            for r in recent_runs
        ],
        "by_dim": [dict(r) for r in by_dim],
    }


# ── Session 43 P5 — Onboarding funnel analytics ───────────────────────

@router.get("/api/admin/onboarding-funnel")
async def onboarding_funnel_stats(
    domain: str = "en", hours: int = 720,
    admin: dict = Depends(require_admin),
):
    """Aggregate onboarding_telemetry_events into a step-by-step funnel.

    For each distinct session_id : max step_order reached via step_enter +
    completion flag. Conversion rates computed between consecutive step
    orders. Returns headline counts (started / completed / aborted),
    the funnel table, and the 10 most recent aborts for inspection.

    Sessions are scoped by `domain` and time window `hours` (default 720h / 30d).
    """
    hours = max(1, min(hours, 24 * 365))
    async with db.pool.acquire() as conn:
        summary = await conn.fetchrow(
            """
            WITH scoped AS (
              SELECT session_id, event, step_order
              FROM onboarding_telemetry_events
              WHERE domain = $1
                AND created_at > NOW() - ($2 || ' hours')::interval
            ),
            per_session AS (
              SELECT
                session_id,
                bool_or(event = 'complete') AS completed,
                bool_or(event = 'abort') AS aborted,
                MAX(step_order) FILTER (WHERE event = 'step_enter') AS max_step
              FROM scoped
              GROUP BY session_id
            )
            SELECT
              COUNT(*)::int AS sessions_started,
              COUNT(*) FILTER (WHERE completed)::int AS sessions_completed,
              COUNT(*) FILTER (WHERE aborted AND NOT completed)::int AS sessions_aborted,
              COUNT(*) FILTER (WHERE NOT completed AND NOT aborted)::int AS sessions_inflight,
              COALESCE(ROUND(100.0 * COUNT(*) FILTER (WHERE completed)
                             / NULLIF(COUNT(*), 0), 1), 0) AS completion_pct
            FROM per_session
            """,
            domain, str(hours),
        )
        by_step = await conn.fetch(
            """
            WITH scoped AS (
              SELECT session_id, step_order, step_id, total_steps
              FROM onboarding_telemetry_events
              WHERE event = 'step_enter'
                AND domain = $1
                AND created_at > NOW() - ($2 || ' hours')::interval
            ),
            session_max AS (
              SELECT session_id, MAX(step_order) AS max_step FROM scoped GROUP BY session_id
            ),
            per_step AS (
              SELECT
                s.step_order,
                MAX(s.step_id) AS step_id,
                COUNT(DISTINCT s.session_id)::int AS entered
              FROM scoped s
              GROUP BY s.step_order
            )
            SELECT
              p.step_order,
              p.step_id,
              p.entered,
              (SELECT COUNT(*)::int FROM session_max sm WHERE sm.max_step = p.step_order) AS dropped_off
            FROM per_step p
            ORDER BY p.step_order
            """,
            domain, str(hours),
        )
        recent_aborts = await conn.fetch(
            """
            SELECT
              a.session_id, a.created_at, a.step_id, a.step_order,
              (SELECT MIN(e.created_at) FROM onboarding_telemetry_events e
                 WHERE e.session_id = a.session_id) AS started_at
            FROM onboarding_telemetry_events a
            WHERE a.event = 'abort'
              AND a.domain = $1
              AND a.created_at > NOW() - ($2 || ' hours')::interval
            ORDER BY a.created_at DESC
            LIMIT 10
            """,
            domain, str(hours),
        )

    # Conversion next from row i to row i+1
    by_step_list = [dict(r) for r in by_step]
    for i, row in enumerate(by_step_list):
        nxt = by_step_list[i + 1]["entered"] if i + 1 < len(by_step_list) else None
        row["entered_next"] = nxt
        if nxt is not None and row["entered"]:
            row["conversion_next_pct"] = round(100.0 * nxt / row["entered"], 1)
        else:
            row["conversion_next_pct"] = None

    def _iso(x):
        return x.isoformat() if x else None

    return {
        "domain": domain,
        "hours": hours,
        "summary": dict(summary or {}),
        "by_step": by_step_list,
        "recent_aborts": [
            {
                **{k: v for k, v in dict(r).items() if k not in ("created_at", "started_at")},
                "created_at": _iso(r["created_at"]),
                "started_at": _iso(r["started_at"]),
                "duration_ms": int((r["created_at"] - r["started_at"]).total_seconds() * 1000)
                    if r["started_at"] and r["created_at"] else None,
            }
            for r in recent_aborts
        ],
    }
