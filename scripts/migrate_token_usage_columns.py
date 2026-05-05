"""Add reconciliation columns to token_usage_daily.

Adds litellm_tokens (snapshot from LiteLLM_SpendLogs at last reconcile),
openai_tokens (snapshot from OpenAI Usage API at last reconcile), and
reconciled_at (timestamp of last reconcile). All idempotent — safe to re-run.

Used by chat_router.get_gpt4o_usage to seed the in-memory token counter
with MAX(local, litellm, openai) so the auto-switch decision never undercounts
real OpenAI usage (Sprint Token-tracking ABCD, Session 19).
"""
from __future__ import annotations

import asyncio
import os
import sys

import asyncpg


PG_PASSWORD_FILE = "/opt/academia-shared/secrets/pg-password"
DB_NAME = "academie_db"
DB_USER = "sinse"
DB_HOST = "127.0.0.1"
DB_PORT = 5432


def _read_password() -> str:
    with open(PG_PASSWORD_FILE) as f:
        return f.read().strip()


async def _migrate(conn: asyncpg.Connection) -> None:
    # 1. Add litellm_tokens (snapshot at last reconcile)
    await conn.execute("""
        ALTER TABLE token_usage_daily
        ADD COLUMN IF NOT EXISTS litellm_tokens BIGINT NOT NULL DEFAULT 0
    """)
    # 2. Add openai_tokens (snapshot at last reconcile)
    await conn.execute("""
        ALTER TABLE token_usage_daily
        ADD COLUMN IF NOT EXISTS openai_tokens BIGINT NOT NULL DEFAULT 0
    """)
    # 3. Add reconciled_at (null until first reconciliation)
    await conn.execute("""
        ALTER TABLE token_usage_daily
        ADD COLUMN IF NOT EXISTS reconciled_at TIMESTAMP
    """)


async def main() -> int:
    pw = _read_password()
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=pw, database=DB_NAME,
    )
    try:
        await _migrate(conn)
        rows = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'token_usage_daily'
            ORDER BY ordinal_position
        """)
        print("token_usage_daily schema after migration:")
        for r in rows:
            print(f"  {r['column_name']:20s} {r['data_type']:30s} nullable={r['is_nullable']} default={r['column_default']}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
