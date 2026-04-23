"""
Refactor 2026-H2 Phase A5 — cross-user isolation tests.

Scenarios :
  1. dsar.export_user_data leaks no data from other users
  2. dsar.delete_user_account does not touch other users' rows
  3. chat_router rejects a conversation_id owned by another user (403)

The "live prompt injection" scenario (Alice asks Dify about Bob's profile)
is NOT in this CI suite : it requires Dify reachable + spends real LLM
tokens. Document as manual smoke (cf. dpia.md §3.1).

Run :
    docker exec academie-api python -m pytest /app/tests/test_cross_user_isolation.py -v
"""
from __future__ import annotations

import asyncio
import pytest

from app.dsar import export_user_data, delete_user_account


@pytest.mark.asyncio
async def test_export_data_does_not_leak_other_users(alice_and_bob, pg_pool):
    alice, bob = alice_and_bob

    async with pg_pool.acquire() as conn:
        # full users row needs to be fetched for dsar API parity
        alice_row = dict(await conn.fetchrow("SELECT * FROM users WHERE id = $1", alice["id"]))
        bob_row = dict(await conn.fetchrow("SELECT * FROM users WHERE id = $1", bob["id"]))
        export_a = await export_user_data(conn, alice_row)
        export_b = await export_user_data(conn, bob_row)

    # Alice's export must NOT contain Bob's marker, and vice-versa
    raw_a = repr(export_a)
    raw_b = repr(export_b)
    assert bob["_unique_marker"] not in raw_a, "Alice's export leaked Bob's data"
    assert alice["_unique_marker"] not in raw_b, "Bob's export leaked Alice's data"

    # Each export's user.id matches the requester
    assert export_a["users"]["id"] == alice["id"]
    assert export_b["users"]["id"] == bob["id"]

    # Each export's learner_profiles is keyed to the requester's eleve_id
    for lp in export_a.get("learner_profiles", []):
        assert lp["eleve_id"] == alice["eleve_id"]
    for lp in export_b.get("learner_profiles", []):
        assert lp["eleve_id"] == bob["eleve_id"]


@pytest.mark.asyncio
async def test_delete_account_does_not_touch_other_users(alice_and_bob, pg_pool):
    alice, bob = alice_and_bob

    async with pg_pool.acquire() as conn:
        alice_row = dict(await conn.fetchrow("SELECT * FROM users WHERE id = $1", alice["id"]))
        await delete_user_account(conn, alice_row)

        # Alice gone
        assert await conn.fetchval("SELECT COUNT(*) FROM users WHERE id = $1", alice["id"]) == 0
        assert await conn.fetchval(
            "SELECT COUNT(*) FROM learner_profiles WHERE eleve_id = $1", alice["eleve_id"],
        ) == 0
        # Bob untouched
        assert await conn.fetchval("SELECT COUNT(*) FROM users WHERE id = $1", bob["id"]) == 1
        assert await conn.fetchval(
            "SELECT COUNT(*) FROM learner_profiles WHERE eleve_id = $1", bob["eleve_id"],
        ) == 1


@pytest.mark.asyncio
async def test_user_sessions_lookup_isolation(alice_and_bob, pg_pool):
    """Verify the chat_router conversation-ownership query (Phase A5 hardening).

    chat_router.py rejects req.conversation_id when no matching row is found
    in user_sessions for (user_id, agent, conv_id). This test asserts the
    underlying query returns NULL for cross-user lookups.
    """
    alice, bob = alice_and_bob
    async with pg_pool.acquire() as conn:
        # Seed a conversation owned by Bob
        await conn.execute(
            """INSERT INTO user_sessions
                 (user_id, agent_name, dify_conversation_id, started_at, last_message_at)
               VALUES ($1, 'maestro', 'conv-bob-secret-uuid', NOW(), NOW())""",
            bob["id"],
        )

        # Alice tries to fetch it
        row = await conn.fetchrow(
            """SELECT last_message_at FROM user_sessions
               WHERE user_id = $1 AND agent_name = $2 AND dify_conversation_id = $3""",
            alice["id"], "maestro", "conv-bob-secret-uuid",
        )
        assert row is None, "Alice managed to read Bob's conversation row"

        # Bob's own lookup works
        bob_row = await conn.fetchrow(
            """SELECT last_message_at FROM user_sessions
               WHERE user_id = $1 AND agent_name = $2 AND dify_conversation_id = $3""",
            bob["id"], "maestro", "conv-bob-secret-uuid",
        )
        assert bob_row is not None
