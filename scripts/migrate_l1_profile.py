"""Sprint 3 Phase 6 — Add L1 columns to profils_eleves + seed l1_transfer_observations.

Adds:
  - profils_eleves.l1 VARCHAR(2) DEFAULT 'fr'  (ISO-639-1)
  - profils_eleves.l1_watch_enabled BOOLEAN NOT NULL DEFAULT true
  - 5 seed rows in l1_transfer_observations for fr→en (articles 1.5, prepositions 1.4,
    false_friends 1.3, modals 1.2, word_order_questions 1.1)

Idempotent — safe to re-run. Mirrors the content of L1_TRANSFER_SEED in
webapp/backend/app/teacher_prompt.py so the DB is the runtime source of truth
(teacher_prompt.py still uses the in-code seed as a fallback).

Sprint 3 Phase 6 — replaces the hardcoded `l1="fr"` in chat_router.py by a per-profile lookup.
"""
from __future__ import annotations

import asyncio
import sys

import asyncpg


PG_PASSWORD_FILE = "/opt/academie-shared/secrets/pg-password"
DB_NAME = "academie_db"
DB_USER = "sinse"
DB_HOST = "127.0.0.1"
DB_PORT = 5432


# Source: docs/01-pedagogy/sprint3_design.md §6 + teacher_prompt.py L1_TRANSFER_SEED.
L1_FR_EN_SEED = [
    # (source_profile, target_profile, error_family, multiplier)
    ("fr", "en", "articles", 1.5),
    ("fr", "en", "prepositions", 1.4),
    ("fr", "en", "false_friends", 1.3),
    ("fr", "en", "modals", 1.2),
    ("fr", "en", "word_order_questions", 1.1),
]


def _read_password() -> str:
    with open(PG_PASSWORD_FILE) as f:
        return f.read().strip()


async def _migrate(conn: asyncpg.Connection) -> None:
    await conn.execute("""
        ALTER TABLE profils_eleves
        ADD COLUMN IF NOT EXISTS l1 VARCHAR(2) DEFAULT 'fr'
    """)
    await conn.execute("""
        ALTER TABLE profils_eleves
        ADD COLUMN IF NOT EXISTS l1_watch_enabled BOOLEAN NOT NULL DEFAULT TRUE
    """)
    # Backfill NULLs for rows that may pre-date the DEFAULT.
    await conn.execute("UPDATE profils_eleves SET l1 = 'fr' WHERE l1 IS NULL")

    for source, target, family, mult in L1_FR_EN_SEED:
        await conn.execute(
            """INSERT INTO l1_transfer_observations
               (source_profile, target_profile, error_family, n_observations, n_expected, multiplier, last_updated)
               VALUES ($1, $2, $3, 0, 0, $4, NOW())
               ON CONFLICT (source_profile, target_profile, error_family)
               DO UPDATE SET multiplier = EXCLUDED.multiplier, last_updated = NOW()""",
            source, target, family, mult,
        )


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
            WHERE table_name = 'profils_eleves' AND column_name IN ('l1', 'l1_watch_enabled')
            ORDER BY ordinal_position
        """)
        print("profils_eleves new columns:")
        for r in rows:
            print(f"  {r['column_name']:20s} {r['data_type']:15s} nullable={r['is_nullable']} default={r['column_default']}")
        seeds = await conn.fetch("""
            SELECT source_profile, target_profile, error_family, multiplier
            FROM l1_transfer_observations
            WHERE source_profile = 'fr' AND target_profile = 'en'
            ORDER BY multiplier DESC
        """)
        print(f"l1_transfer_observations fr→en rows ({len(seeds)}):")
        for r in seeds:
            print(f"  {r['error_family']:25s} ×{r['multiplier']}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
