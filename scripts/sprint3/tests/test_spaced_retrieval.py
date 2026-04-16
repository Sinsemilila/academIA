"""Sprint 3 Phase 7 — Integration test for spaced retrieval queue helpers.

Exercises chat_router._fetch_due_retrieval_items + _persist_spaced_retrieval
against a live postgres, with the module flag forced ON. Covers :
  1. Enqueue on silenced errors — 2 rows inserted with scheduled_at = NOW()+1d
  2. Fetch before due date — empty (row is in the future)
  3. Backdate scheduled_at — fetch returns the item
  4. Persist `addressed=[concept_key]` — row marked completed
  5. Fetch after completion — empty again
  6. Flag OFF short-circuits both fetch and persist

Run :
  # copies itself into the academie-api container and execs there (deps are inside)
  python3 scripts/sprint3/tests/test_spaced_retrieval.py
  # OR directly inside the container:
  docker exec -e RUN_MODE=inner academie-api python3 /tmp/test_spaced_retrieval.py

Exit code 0 on all pass. Cleans up throw-away user even on failure.
No pytest — stays consistent with other sprint3 tests.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys

import asyncpg


TEST_USERNAME = "test-spaced-retrieval"


async def _exec_sql(conn, sql: str, *args):
    return await conn.execute(sql, *args)


async def _fetch_sql(conn, sql: str, *args):
    return await conn.fetch(sql, *args)


async def setup(conn) -> int:
    await conn.execute(
        """INSERT INTO users (username, password_hash, is_admin, exam_access)
           VALUES ($1, 'unused', FALSE, FALSE)
           ON CONFLICT (username) DO NOTHING""",
        TEST_USERNAME,
    )
    await conn.execute(
        """INSERT INTO eleves (username, created_at) VALUES ($1, NOW())
           ON CONFLICT (username) DO NOTHING""",
        TEST_USERNAME,
    )
    eid = await conn.fetchval("SELECT id FROM eleves WHERE username = $1", TEST_USERNAME)
    await conn.execute("UPDATE users SET eleve_id = $1 WHERE username = $2", eid, TEST_USERNAME)
    await conn.execute(
        """INSERT INTO profils_eleves (eleve_id, domaine, niveau_global, updated_at)
           VALUES ($1, 'anglais', 'B1', NOW())
           ON CONFLICT (eleve_id, domaine) DO NOTHING""",
        eid,
    )
    await conn.execute("DELETE FROM spaced_retrieval_queue WHERE eleve_id = $1", eid)
    return eid


async def cleanup(conn, eid: int) -> None:
    for sql in (
        "DELETE FROM spaced_retrieval_queue WHERE eleve_id = $1",
        "DELETE FROM profils_eleves WHERE eleve_id = $1",
    ):
        await conn.execute(sql, eid)
    uid = await conn.fetchval("SELECT id FROM users WHERE username = $1", TEST_USERNAME)
    if uid:
        await conn.execute("DELETE FROM users WHERE id = $1", uid)
    await conn.execute("DELETE FROM eleves WHERE id = $1", eid)


async def _inner() -> int:
    """Runs inside the academie-api container (has fastapi, asyncpg, app modules)."""
    import datetime as _dt

    # Force flag ON before import — module reads env at load time.
    os.environ["SPACED_RETRIEVAL_ENABLED"] = "true"
    sys.path.insert(0, "/app")
    from app import database as app_db
    from app.routers import chat_router

    chat_router.SPACED_RETRIEVAL_ENABLED = True  # belt-and-braces

    dsn = os.environ["DATABASE_URL"]
    app_db.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=3)
    fails: list[str] = []
    async with app_db.pool.acquire() as conn:
        eid = await setup(conn)

    try:
        # 1. Persist silenced — expect 2 rows enqueued at NOW()+1d.
        await chat_router._persist_spaced_retrieval(
            eid, "anglais",
            silenced_codes=["V:TENSE", "PREP"],
            addressed_keys=[],
        )
        async with app_db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT concept_key, error_code, scheduled_at, completed_at, outcome
                   FROM spaced_retrieval_queue
                   WHERE eleve_id = $1 ORDER BY error_code""", eid,
            )
        print(f"  1. After persist(silenced=[V:TENSE,PREP]): {len(rows)} rows")
        for r in rows:
            print(f"     concept={r['concept_key']!s:20s} code={r['error_code']!s:10s} "
                  f"sched={r['scheduled_at']} done={r['completed_at']}")
        if len(rows) != 2:
            fails.append(f"Step 1: expected 2 rows, got {len(rows)}")
        codes = {r["error_code"] for r in rows}
        if codes != {"V:TENSE", "PREP"}:
            fails.append(f"Step 1: error_codes={codes}")
        now = _dt.datetime.now(_dt.timezone.utc)
        for r in rows:
            if r["scheduled_at"] <= now:
                fails.append(f"Step 1: scheduled_at {r['scheduled_at']} not in future")
            if r["completed_at"] is not None:
                fails.append(f"Step 1: completed_at should be NULL, got {r['completed_at']}")

        # 2. Fetch before due — must be empty (scheduled_at > NOW()).
        due_now = await chat_router._fetch_due_retrieval_items(eid, "anglais")
        print(f"  2. Fetch now (items due): {len(due_now)} — expect 0")
        if due_now:
            fails.append(f"Step 2: expected 0 due items, got {len(due_now)}")

        # 3. Backdate scheduled_at → fetch returns items.
        async with app_db.pool.acquire() as conn:
            await conn.execute(
                "UPDATE spaced_retrieval_queue SET scheduled_at = NOW() - INTERVAL '1 hour' "
                "WHERE eleve_id = $1", eid,
            )
        due = await chat_router._fetch_due_retrieval_items(eid, "anglais")
        print(f"  3. After backdate — fetch: {len(due)} items")
        for item in due:
            print(f"     {item}")
        if len(due) != 2:
            fails.append(f"Step 3: expected 2 due items, got {len(due)}")
        concept_keys = {it["concept_key"] for it in due}
        # ERROR_CODE_TO_FAMILY maps V:TENSE→verb_tense, PREP→preposition
        if not concept_keys.issuperset({"verb_tense", "preposition"}):
            fails.append(f"Step 3: concept_keys={concept_keys}")

        # 4. Persist addressed={concept_key} → row completed.
        await chat_router._persist_spaced_retrieval(
            eid, "anglais",
            silenced_codes=[],
            addressed_keys=["verb_tense"],
        )
        async with app_db.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT concept_key, error_code, completed_at, outcome
                   FROM spaced_retrieval_queue
                   WHERE eleve_id = $1 ORDER BY error_code""", eid,
            )
        print(f"  4. After addressed=[verb_tense]:")
        for r in rows:
            print(f"     concept={r['concept_key']!s:20s} code={r['error_code']!s:10s} "
                  f"done={r['completed_at']} outcome={r['outcome']}")
        vt_rows = [r for r in rows if r["concept_key"] == "verb_tense"]
        prep_rows = [r for r in rows if r["concept_key"] == "preposition"]
        if not vt_rows or vt_rows[0]["completed_at"] is None:
            fails.append(f"Step 4: verb_tense row should be completed: {vt_rows}")
        if vt_rows and vt_rows[0]["outcome"] != "addressed":
            fails.append(f"Step 4: verb_tense outcome expected 'addressed', got {vt_rows[0]['outcome']!r}")
        if not prep_rows or prep_rows[0]["completed_at"] is not None:
            fails.append(f"Step 4: preposition row should still be NULL-completed: {prep_rows}")

        # 5. Fetch after completion — only preposition remains.
        due = await chat_router._fetch_due_retrieval_items(eid, "anglais")
        print(f"  5. Fetch after completion: {len(due)} items (expect 1: preposition)")
        if len(due) != 1 or due[0]["concept_key"] != "preposition":
            fails.append(f"Step 5: expected [preposition], got {due}")

        # 6. Flag OFF short-circuits fetch + persist.
        chat_router.SPACED_RETRIEVAL_ENABLED = False
        due_off = await chat_router._fetch_due_retrieval_items(eid, "anglais")
        print(f"  6. Flag OFF — fetch: {len(due_off)} (expect 0)")
        if due_off:
            fails.append(f"Step 6: flag OFF should short-circuit, got {due_off}")
        await chat_router._persist_spaced_retrieval(
            eid, "anglais", silenced_codes=["V:SVA"], addressed_keys=[]
        )
        async with app_db.pool.acquire() as conn:
            n = await conn.fetchval(
                "SELECT COUNT(*) FROM spaced_retrieval_queue WHERE eleve_id = $1 AND error_code = 'V:SVA'",
                eid,
            )
        if n != 0:
            fails.append(f"Step 6: flag OFF should skip persist, got {n} rows")
    finally:
        print(f"▸ Cleanup", flush=True)
        async with app_db.pool.acquire() as conn:
            await cleanup(conn, eid)
        await app_db.pool.close()

    if fails:
        print(f"\n❌ {len(fails)} failures:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"\n✅ All spaced retrieval checks passed.")
    return 0


def main() -> int:
    if os.environ.get("RUN_MODE") == "inner":
        return asyncio.run(_inner())
    # Outer mode: copy self into container, exec, forward exit code.
    host_path = os.path.abspath(__file__)
    container_path = "/tmp/test_spaced_retrieval.py"
    subprocess.run(["docker", "cp", host_path, f"academie-api:{container_path}"], check=True)
    res = subprocess.run(
        ["docker", "exec", "-e", "RUN_MODE=inner", "academie-api",
         "python3", container_path],
        check=False,
    )
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
