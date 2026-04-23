"""Helpers for E2E consolidation test (Session 36 follow-up).

⚠️  Refactor 2026-H2 Phase A1-cleanup (2026-04-23) — JWT auth removed in
favour of opaque Redis sessions. `forge_access_token()` is now a stub that
raises NotImplementedError. To revive these helpers, refactor to use
sessions.create_session() directly (bypasses login, returns cookies dict)
or call /api/auth/login with a real password and capture Set-Cookie.

Reusable utilities to seed a test user, reset DB scope, seed pending
consolidation state, build scripted mini-exam answers, and assert final
DB state. Designed to be imported from 05_e2e_consolidation_test.py and
run inside the academie-api container (DATABASE_URL available in env).
"""
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import asyncpg
import httpx

# ── Config ─────────────────────────────────────────────────────────────

DATABASE_URL = os.environ["DATABASE_URL"]
API_BASE = os.environ.get("E2E_API_BASE", "http://localhost:8000")

TEST_USER_USERNAME = "e2e_consolidation_bot"
TEST_USER_ELEVE_ID = 99999   # fixed high ID to avoid collisions
# Dummy bcrypt hash (never used — we forge JWTs directly).
DUMMY_BCRYPT = "$2b$12$" + "x" * 53

AGENT_TO_DOMAIN = {"teacher": "en", "maestro": "es"}


# ── DB pool ────────────────────────────────────────────────────────────

_pool: asyncpg.Pool | None = None


async def pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=4)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ── Auth forge (NEEDS REFACTOR — see module docstring) ─────────────────

def forge_access_token(user_id: int, username: str) -> str:
    """A1-cleanup : JWT auth dropped. Refactor to sessions.create_session()
    + return cookies dict, then update all callers to pass cookies+CSRF
    instead of Authorization Bearer header. Until then, this file's
    networked tests are effectively skipped."""
    raise NotImplementedError(
        "forge_access_token: JWT auth removed in A1 (2026-04-23). "
        "Refactor to cookie-session — see module docstring."
    )


# ── Test user lifecycle ────────────────────────────────────────────────

async def ensure_test_user() -> tuple[int, int]:
    """Create test eleve + user if missing. Returns (user_id, eleve_id)."""
    p = await pool()
    async with p.acquire() as conn:
        # Upsert eleve row with fixed id
        await conn.execute(
            """INSERT INTO eleves (id, username) VALUES ($1, $2)
               ON CONFLICT (id) DO NOTHING""",
            TEST_USER_ELEVE_ID, TEST_USER_USERNAME,
        )
        # Upsert user row linked to that eleve
        user_row = await conn.fetchrow(
            """INSERT INTO users (username, password_hash, eleve_id, is_admin, exam_access)
               VALUES ($1, $2, $3, FALSE, FALSE)
               ON CONFLICT (username) DO UPDATE
                 SET eleve_id = EXCLUDED.eleve_id
               RETURNING id, eleve_id""",
            TEST_USER_USERNAME, DUMMY_BCRYPT, TEST_USER_ELEVE_ID,
        )
        return int(user_row["id"]), int(user_row["eleve_id"])


async def teardown_test_user() -> None:
    p = await pool()
    async with p.acquire() as conn:
        user_id = await conn.fetchval(
            "SELECT id FROM users WHERE username = $1", TEST_USER_USERNAME)
        await conn.execute(
            "DELETE FROM consolidation_events WHERE eleve_id = $1", TEST_USER_ELEVE_ID)
        if user_id:
            await conn.execute(
                "DELETE FROM user_sessions WHERE user_id = $1", user_id)
            await conn.execute(
                "DELETE FROM streaks WHERE user_id = $1", user_id)
            await conn.execute(
                "DELETE FROM xp_log WHERE user_id = $1", user_id)
        await conn.execute(
            "DELETE FROM profils_eleves WHERE eleve_id = $1", TEST_USER_ELEVE_ID)
        await conn.execute(
            "DELETE FROM learner_profiles WHERE eleve_id = $1", TEST_USER_ELEVE_ID)
        await conn.execute(
            "DELETE FROM error_log WHERE eleve_id = $1", TEST_USER_ELEVE_ID)
        await conn.execute(
            "DELETE FROM users WHERE username = $1", TEST_USER_USERNAME)
        await conn.execute(
            "DELETE FROM eleves WHERE id = $1", TEST_USER_ELEVE_ID)


async def reset_scenario(eleve_id: int, domain: str, user_id: int | None = None) -> None:
    """Wipe scope to make scenario re-runnable. Keeps eleve + user rows intact."""
    p = await pool()
    async with p.acquire() as conn:
        if user_id is None:
            user_id = await conn.fetchval(
                "SELECT id FROM users WHERE eleve_id = $1", eleve_id)
        await conn.execute(
            "DELETE FROM consolidation_events WHERE eleve_id=$1 AND domain=$2",
            eleve_id, domain)
        if user_id:
            await conn.execute(
                "DELETE FROM user_sessions WHERE user_id=$1 AND agent_name = ANY($2::text[])",
                user_id, _agents_for_domain(domain))
        await conn.execute(
            "DELETE FROM profils_eleves WHERE eleve_id=$1 AND domain=$2",
            eleve_id, domain)
        await conn.execute(
            "DELETE FROM learner_profiles WHERE eleve_id=$1 AND domain=$2",
            eleve_id, domain)
        await conn.execute(
            "DELETE FROM error_log WHERE eleve_id=$1 AND domain=$2",
            eleve_id, domain)


def _agents_for_domain(domain: str) -> list[str]:
    return {"en": ["teacher"], "es": ["maestro"]}.get(domain, [])


# ── Seeding ────────────────────────────────────────────────────────────

_CEFR_LADDER = ["A1", "A2", "B1", "B2", "C1", "C2"]


def _qcm_input_for_placement(placement: str) -> str:
    """Onboarding applies conservative -1 step (except A1 stays A1). Invert that
    so the returned cefr_placement equals the requested value."""
    if placement == "A1":
        return "A1"
    idx = _CEFR_LADDER.index(placement)
    return _CEFR_LADDER[idx + 1]


async def submit_qcm(token: str, domain: str, qcm_level: str) -> dict:
    """Submit QCM via API — creates learner_profiles row with cefr_placement=qcm_level."""
    level_input = _qcm_input_for_placement(qcm_level)
    payload = {
        "universal_block": {
            "self_efficacy": 3,
            "mindset": "growth",
            "goal_text": "Améliorer mon niveau pour voyager et parler au quotidien",
            "autonomy_pref": "semi_autonomous",
            "engagement_pattern": "daily_short",
        },
        "domain_level": {
            "cefr_comprehension": level_input,
            "cefr_production": level_input,
            "probe_answer": None,
        },
        "domain_motivation": {
            "ideal_l2_self_tags": ["travel"],
            "fla_items_raw": {"fla_a": 2, "fla_b": 2, "fla_c": 2},
        },
    }
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{API_BASE}/api/learner-profile/{domain}", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()


async def seed_profils_eleves(eleve_id: int, domain: str, niveau_global: str) -> None:
    """Create profils_eleves row with status=provisoire (mimic what first chat turn would do)."""
    p = await pool()
    async with p.acquire() as conn:
        await conn.execute(
            """INSERT INTO profils_eleves (eleve_id, domain, niveau_global, niveau_status)
               VALUES ($1, $2, $3, 'provisoire')
               ON CONFLICT (eleve_id, domain) DO UPDATE
                 SET niveau_global = EXCLUDED.niveau_global,
                     niveau_status = 'provisoire',
                     niveau_validated_at = NULL,
                     consolidation_decision_pending = NULL,
                     last_consolidation_turn = NULL""",
            eleve_id, domain, niveau_global,
        )


async def seed_pending_decision(
    eleve_id: int, domain: str, qcm: str, observed: str,
    trigger_reason: str = "n_turns", n_turns: int = 8,
) -> None:
    """Directly write consolidation_decision_pending to simulate _consolidation_post_turn
    having fired with a mismatch outcome. Also inserts the 'pending' audit row.
    """
    from academie_core.pedagogy.consolidation import (
        clamp_single_step, decide_consolidation, ObservationHint,
        ErrorDistribution,
    )
    # Build synthetic hints matching desired observed level
    hints = [ObservationHint(turn=i + 1, observed_level=observed) for i in range(8)]
    outcome = decide_consolidation(
        qcm_level=qcm,
        observation_hints=hints,
        error_distribution=ErrorDistribution(per_level={}),
        message_count=n_turns,
        trigger_reason=trigger_reason,
    )
    p = await pool()
    async with p.acquire() as conn:
        if outcome.kind == "propose_mini_exam":
            await conn.execute(
                """UPDATE profils_eleves
                   SET niveau_status='calibration_en_cours',
                       consolidation_decision_pending=$1::jsonb,
                       last_consolidation_turn=$2
                   WHERE eleve_id=$3 AND domain=$4""",
                json.dumps(outcome.decision_payload), n_turns, eleve_id, domain,
            )
            await conn.execute(
                """INSERT INTO consolidation_events
                   (eleve_id, domain, trigger_reason, qcm_level, observed_level,
                    mini_exam_triggered, user_decision)
                   VALUES ($1,$2,$3,$4,$5,true,'pending')""",
                eleve_id, domain, trigger_reason, outcome.qcm_level, outcome.observed_level,
            )
        elif outcome.kind == "auto_validate":
            await conn.execute(
                """UPDATE profils_eleves
                   SET niveau_global=$1, niveau_status='validé',
                       niveau_validated_at=NOW(), last_consolidation_turn=$2,
                       consolidation_decision_pending=NULL
                   WHERE eleve_id=$3 AND domain=$4""",
                outcome.qcm_level, n_turns, eleve_id, domain,
            )
            await conn.execute(
                """INSERT INTO consolidation_events
                   (eleve_id, domain, trigger_reason, qcm_level, observed_level,
                    mini_exam_triggered, user_decision, final_level)
                   VALUES ($1,$2,$3,$4,$5,false,'auto_validate',$4)""",
                eleve_id, domain, trigger_reason, outcome.qcm_level, outcome.observed_level,
            )
    return outcome


# ── Mini-exam answer tables ────────────────────────────────────────────
# Hand-curated correct answers per bank. PASS path uses these; FAIL path uses
# empty strings or nonsense.

CORRECT_ANSWERS: dict[str, dict[str, str]] = {
    "en_A1": {
        # Not needed for matrix but kept for completeness if added later
    },
    "en_A2": {
        "en_a2_01": "went",
        "en_a2_02": "did she see him?",
        "en_a2_03": "been to",
        "en_a2_04": "since",
        "en_a2_05": "Paris is bigger than Lyon.",
        "en_a2_06": "am going to travel",
        "en_a2_07": "Last weekend I went to the park and played football with friends. We had lunch together and then I watched a movie at home.",
        "en_a2_08": "mustn't",
    },
    "en_B1": {
        "en_b1_01": "rains , will stay",
        "en_b1_02": "The bridge was built by them in 1990.",
        "en_b1_03": "have been waiting",
        "en_b1_04": "she was tired.",
        "en_b1_05": "used to",
        "en_b1_06": "had",
        "en_b1_07": "In my opinion remote work should be an option for everyone. It could improve work-life balance and might reduce commute stress, although some teams could suffer from less face-to-face contact.",
        "en_b1_08": "who",
    },
    "en_B2": {
        "en_b2_01": "had known , would have helped",
        "en_b2_02": "This bug should be fixed.",
        "en_b2_03": "had studied / would have had",
        "en_b2_04": "where she had gone.",
        "en_b2_05": "have I seen",
        "en_b2_06": "Although",
        "en_b2_07": "Although artificial intelligence is often presented as a threat to employment, many routine tasks will be automated and new jobs will be created. Despite these changes, workers should be retrained so that human skills can still be valued in the labour market.",
        "en_b2_08": "my car repaired",
    },
    "es_A1": {
        "es_a1_01": "soy",
        "es_a1_02": "llamas",
        "es_a1_03": "La",
        "es_a1_04": "los libros rojos",
        "es_a1_05": "veinticinco",
        "es_a1_06": "vivimos",
        "es_a1_07": "Me llamo Juan, tengo treinta años y soy francés.",
        "es_a1_08": "dónde",
    },
    "es_A2": {},  # not exercised in matrix
    "es_B1": {
        "es_b1_01": "vengas",
        "es_b1_02": "gustaría",
        "es_b1_03": "caminaba / vi",
        "es_b1_04": "es",
        "es_b1_05": "iba a estudiar",
        "es_b1_06": "desde hace",
        "es_b1_07": "Creo que el teletrabajo es útil, aunque es importante que las empresas organicen encuentros presenciales para que el equipo mantenga la cohesión.",
        "es_b1_08": "haría",
    },
    "es_B2": {},  # not exercised in matrix
}


def answers_for(domain: str, level: str, mode: str = "pass") -> list[dict]:
    """Build answers list for mini_exam/submit body. mode='pass' uses correct
    table; mode='fail' uses nonsense (all wrong)."""
    bank_key = f"{domain}_{level}"
    if bank_key not in CORRECT_ANSWERS or not CORRECT_ANSWERS[bank_key]:
        raise ValueError(f"No answer table for {bank_key}")
    table = CORRECT_ANSWERS[bank_key]
    if mode == "pass":
        return [{"id": iid, "answer": ans} for iid, ans in table.items()]
    # fail: empty or nonsense
    return [{"id": iid, "answer": "xxx" if i % 2 == 0 else ""}
            for i, iid in enumerate(table.keys())]


# ── API helpers ────────────────────────────────────────────────────────

async def get_state(token: str, domain: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{API_BASE}/api/consolidation/state/{domain}", headers=headers)
        r.raise_for_status()
        return r.json()


async def start_mini_exam(token: str, domain: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{API_BASE}/api/consolidation/mini-exam/start/{domain}", headers=headers)
        r.raise_for_status()
        return r.json()


async def submit_mini_exam(token: str, domain: str, target_level: str, answers: list[dict]) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    body = {"target_level": target_level, "answers": answers}
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(
            f"{API_BASE}/api/consolidation/mini-exam/submit/{domain}",
            json=body, headers=headers)
        r.raise_for_status()
        return r.json()


async def decide(token: str, domain: str, choice: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    body = {"choice": choice}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            f"{API_BASE}/api/consolidation/decide/{domain}", json=body, headers=headers)
        r.raise_for_status()
        return r.json()


# ── Assertions ─────────────────────────────────────────────────────────

async def fetch_final_state(eleve_id: int, domain: str) -> dict:
    p = await pool()
    async with p.acquire() as conn:
        profil = await conn.fetchrow(
            """SELECT niveau_global, niveau_status, niveau_validated_at,
                      consolidation_decision_pending
               FROM profils_eleves WHERE eleve_id=$1 AND domain=$2""",
            eleve_id, domain,
        )
        events = await conn.fetch(
            """SELECT trigger_reason, qcm_level, observed_level, mini_exam_triggered,
                      mini_exam_score_pct, user_decision, final_level
               FROM consolidation_events WHERE eleve_id=$1 AND domain=$2
               ORDER BY triggered_at""",
            eleve_id, domain,
        )
    return {
        "profil": dict(profil) if profil else None,
        "events": [dict(e) for e in events],
    }
