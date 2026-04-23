"""
Refactor 2026-H2 Phase A5 — pytest fixtures for cross-user isolation tests.

Run via :
    docker exec academie-api python -m pytest /app/tests/ -v
"""
from __future__ import annotations

import os
import secrets
import asyncio
from typing import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio


DSN = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DSN:
    raise RuntimeError("TEST_DATABASE_URL or DATABASE_URL must be set in env")


@pytest_asyncio.fixture(scope="function")
async def pg_pool() -> AsyncIterator[asyncpg.Pool]:
    pool = await asyncpg.create_pool(DSN, min_size=1, max_size=2)
    try:
        yield pool
    finally:
        await pool.close()


async def _make_user(pool: asyncpg.Pool, prefix: str) -> dict:
    """Create a unique throwaway user + linked eleves row + a fake learner_profile.
    Returns a dict shaped like get_current_user output."""
    suffix = secrets.token_hex(4)
    username = f"test_{prefix}_{suffix}"
    dify_user_id = f"test-dify-{suffix}"
    async with pool.acquire() as conn:
        async with conn.transaction():
            user_row = await conn.fetchrow(
                """INSERT INTO users (username, password_hash, dify_user_id, display_name, is_admin, exam_access)
                   VALUES ($1, 'pwd_unused_in_tests', $2, $3, false, false)
                   RETURNING *""",
                username, dify_user_id, prefix.capitalize(),
            )
            eleve_row = await conn.fetchrow(
                """INSERT INTO eleves (username, created_at)
                   VALUES ($1, NOW())
                   RETURNING id""",
                username,
            )
            await conn.execute(
                "UPDATE users SET eleve_id = $1 WHERE id = $2",
                eleve_row["id"], user_row["id"],
            )
            await conn.execute(
                """INSERT INTO learner_profiles
                   (eleve_id, domain, target_language, universal_block, domain_level, domain_motivation)
                   VALUES ($1, 'en', 'en', $2::jsonb, $3::jsonb, $4::jsonb)""",
                eleve_row["id"],
                f'{{"goal_text": "{prefix} secret learner goal {suffix}"}}',
                '{"cefr_placement": "B1"}',
                '{"motivation_score": 7}',
            )
    return {
        "id": user_row["id"],
        "username": username,
        "dify_user_id": dify_user_id,
        "eleve_id": eleve_row["id"],
        "display_name": user_row["display_name"],
        "is_admin": False,
        "exam_access": False,
        "_unique_marker": f"{prefix} secret learner goal {suffix}",
    }


async def _delete_user(pool: asyncpg.Pool, user: dict) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            for table in ("xp_log", "streaks", "user_sessions", "active_sessions", "user_totp"):
                await conn.execute(f"DELETE FROM {table} WHERE user_id = $1", user["id"])
            if user.get("eleve_id"):
                for table in (
                    "onboarding_telemetry_events", "spaced_retrieval_queue",
                    "consolidation_events", "snapshots_session", "error_log",
                    "learner_profiles", "profils_eleves",
                ):
                    await conn.execute(f"DELETE FROM {table} WHERE eleve_id = $1", user["eleve_id"])
                await conn.execute("UPDATE users SET eleve_id = NULL WHERE id = $1", user["id"])
                await conn.execute("DELETE FROM eleves WHERE id = $1", user["eleve_id"])
            await conn.execute("DELETE FROM users WHERE id = $1", user["id"])


@pytest_asyncio.fixture(scope="function")
async def alice_and_bob(pg_pool: asyncpg.Pool):
    alice = await _make_user(pg_pool, "alice")
    bob = await _make_user(pg_pool, "bob")
    try:
        yield alice, bob
    finally:
        await _delete_user(pg_pool, alice)
        await _delete_user(pg_pool, bob)
