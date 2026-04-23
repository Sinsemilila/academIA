"""Integration test — admin reset_profile domain-scoped (Session 37 Fix 1).

⚠️  Refactor 2026-H2 Phase A1-cleanup (2026-04-23) : JWT auth removed.
This test needs a full refactor to cookie-session before it runs again
(Authorization Bearer headers must be replaced by Set-Cookie + X-CSRF-Token).
Marked obsolete; kept as reference for future port.

Verifies the P0 data-loss bug fix: calling reset_profile with ?domain=en must
leave ES rows intact, and calling without domain must wipe everything.

Runs via: docker exec academie-api python3 /tmp/test_admin_reset_scoping.py
Requires live DB + backend container (uses DATABASE_URL env).
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

import asyncpg
import httpx

DATABASE_URL = os.environ["DATABASE_URL"]
API_BASE = os.environ.get("E2E_API_BASE", "http://localhost:8000")

TEST_USERNAME = "admin_reset_scoping_bot"
TEST_ELEVE_ID = 99998
ADMIN_USERNAME = "admin_reset_scoping_adm"


def _forge_token(user_id: int, username: str) -> str:
    """A1-cleanup : JWT removed, this test needs cookie-session refactor."""
    raise NotImplementedError(
        "_forge_token: JWT auth removed in A1 (2026-04-23). Refactor required."
    )


async def _cleanup(conn):
    """Best-effort cleanup of both users and all their data."""
    for un in (TEST_USERNAME, ADMIN_USERNAME):
        uid = await conn.fetchval("SELECT id FROM users WHERE username = $1", un)
        if uid:
            for tbl in ("consolidation_events", "xp_log", "streaks", "user_sessions"):
                col = "eleve_id" if tbl == "consolidation_events" else "user_id"
                # consolidation_events uses eleve_id, others user_id
            await conn.execute("DELETE FROM consolidation_events WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM spaced_retrieval_queue WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM learner_profiles WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM profils_eleves WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM error_log WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM snapshots_session WHERE eleve_id = $1", TEST_ELEVE_ID)
            await conn.execute("DELETE FROM user_sessions WHERE user_id = $1", uid)
            await conn.execute("DELETE FROM xp_log WHERE user_id = $1", uid)
            await conn.execute("DELETE FROM streaks WHERE user_id = $1", uid)
            await conn.execute("DELETE FROM users WHERE id = $1", uid)
    await conn.execute("DELETE FROM eleves WHERE id = $1", TEST_ELEVE_ID)


async def _seed_both_domains(conn, eleve_id: int, user_id: int):
    """Seed learner with data in both `en` and `es` domains."""
    for dom in ("en", "es"):
        await conn.execute(
            "INSERT INTO profils_eleves (eleve_id, domain, niveau_global) VALUES ($1, $2, 'A1') "
            "ON CONFLICT (eleve_id, domain) DO NOTHING",
            eleve_id, dom,
        )
        await conn.execute(
            "INSERT INTO learner_profiles (eleve_id, domain, target_language, universal_block, domain_level, domain_motivation, derived_tutor_hints, schema_version) "
            "VALUES ($1, $2, $2, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'v1') "
            "ON CONFLICT DO NOTHING",
            eleve_id, dom,
        )
    await conn.execute(
        "INSERT INTO xp_log (user_id, amount, reason, agent_name) VALUES ($1, 100, 'test_seed', 'teacher')",
        user_id,
    )


async def _counts(conn, eleve_id: int, user_id: int) -> dict:
    async def c(sql, *a):
        return await conn.fetchval(sql, *a)
    return {
        "profils_en":        await c("SELECT COUNT(*) FROM profils_eleves WHERE eleve_id = $1 AND domain = 'en'", eleve_id),
        "profils_es":        await c("SELECT COUNT(*) FROM profils_eleves WHERE eleve_id = $1 AND domain = 'es'", eleve_id),
        "learner_profile_en":await c("SELECT COUNT(*) FROM learner_profiles WHERE eleve_id = $1 AND domain = 'en'", eleve_id),
        "learner_profile_es":await c("SELECT COUNT(*) FROM learner_profiles WHERE eleve_id = $1 AND domain = 'es'", eleve_id),
        "xp_log":            await c("SELECT COUNT(*) FROM xp_log WHERE user_id = $1", user_id),
    }


async def main():
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=2)
    async with pool.acquire() as conn:
        await _cleanup(conn)

        # Create admin + test user
        await conn.execute(
            "INSERT INTO eleves (id, username) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            TEST_ELEVE_ID, TEST_USERNAME,
        )
        test_uid = await conn.fetchval(
            "INSERT INTO users (username, password_hash, eleve_id, is_admin, exam_access) "
            "VALUES ($1, $2, $3, FALSE, FALSE) ON CONFLICT (username) DO UPDATE SET eleve_id = EXCLUDED.eleve_id RETURNING id",
            TEST_USERNAME, "$2b$12$" + "x" * 53, TEST_ELEVE_ID,
        )
        admin_uid = await conn.fetchval(
            "INSERT INTO users (username, password_hash, is_admin, exam_access) "
            "VALUES ($1, $2, TRUE, FALSE) ON CONFLICT (username) DO UPDATE SET is_admin = TRUE RETURNING id",
            ADMIN_USERNAME, "$2b$12$" + "y" * 53,
        )

        admin_token = _forge_token(admin_uid, ADMIN_USERNAME)

        # ─── Test 1: domain-scoped reset (en only, ES must survive) ───
        await _seed_both_domains(conn, TEST_ELEVE_ID, test_uid)
        before = await _counts(conn, TEST_ELEVE_ID, test_uid)
        assert before["profils_en"] == 1 and before["profils_es"] == 1, before

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{API_BASE}/api/admin/reset-profile/{TEST_USERNAME}?domain=en",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert r.status_code == 200, r.text

        after1 = await _counts(conn, TEST_ELEVE_ID, test_uid)
        assert after1["profils_en"] == 0, f"EN not wiped: {after1}"
        assert after1["profils_es"] == 1, f"ES wiped (BUG): {after1}"
        assert after1["learner_profile_en"] == 0, f"learner_profile EN not wiped: {after1}"
        assert after1["learner_profile_es"] == 1, f"learner_profile ES wiped (BUG): {after1}"
        assert after1["xp_log"] == 1, f"xp_log wiped (BUG, should stay on per-domain reset): {after1}"
        print("✓ Test 1: domain=en reset scoped correctly; ES + xp_log intact")

        # ─── Test 2: global reset (no domain) wipes everything ───
        await _seed_both_domains(conn, TEST_ELEVE_ID, test_uid)
        before = await _counts(conn, TEST_ELEVE_ID, test_uid)
        # After re-seeding, EN should be back
        assert before["profils_en"] == 1 and before["profils_es"] == 1, before

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{API_BASE}/api/admin/reset-profile/{TEST_USERNAME}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert r.status_code == 200, r.text

        after2 = await _counts(conn, TEST_ELEVE_ID, test_uid)
        assert after2["profils_en"] == 0 and after2["profils_es"] == 0, f"Global reset failed: {after2}"
        assert after2["learner_profile_en"] == 0 and after2["learner_profile_es"] == 0, after2
        assert after2["xp_log"] == 0, f"xp_log not wiped on global reset: {after2}"
        print("✓ Test 2: global reset (no domain) wiped all tables incl. xp_log")

        # ─── Test 3: invalid domain rejected ───
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{API_BASE}/api/admin/reset-profile/{TEST_USERNAME}?domain=en123",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert r.status_code == 422, f"invalid domain should 422: {r.status_code}"
        print("✓ Test 3: invalid domain code rejected 422")

        await _cleanup(conn)
    await pool.close()
    print("\n3/3 passed")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
