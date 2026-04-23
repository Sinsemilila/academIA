#!/usr/bin/env python3
"""
Admin CLI — backfill age_attestation_at for existing accounts (Phase A6).

Usage :
  # Backfill all accounts with current timestamp (assumes admin OK with self-attest)
  docker exec academie-api python /app/scripts/sprint8/07_age_attestation_admin.py --all

  # Backfill one specific user
  docker exec academie-api python /app/scripts/sprint8/07_age_attestation_admin.py --user sinse

  # Show current state
  docker exec academie-api python /app/scripts/sprint8/07_age_attestation_admin.py --status
"""
import argparse
import asyncio
import os
import sys

import asyncpg


async def main():
    parser = argparse.ArgumentParser(description="Backfill users.age_attestation_at (Phase A6)")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="Backfill all NULL rows with NOW()")
    g.add_argument("--user", help="Backfill a specific username with NOW()")
    g.add_argument("--status", action="store_true", help="Show counts and recent attestations")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL") or "postgresql://sinse:sinse@postgres-academie:5432/academie_db"
    conn = await asyncpg.connect(dsn)
    try:
        if args.status:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            attested = await conn.fetchval("SELECT COUNT(*) FROM users WHERE age_attestation_at IS NOT NULL")
            print(f"Users total: {total}")
            print(f"Attested:    {attested}")
            print(f"Pending:     {total - attested}")
            return

        if args.all:
            n = await conn.execute(
                "UPDATE users SET age_attestation_at = NOW() WHERE age_attestation_at IS NULL"
            )
            print(f"Backfilled: {n}")
            return

        if args.user:
            row = await conn.fetchrow(
                "UPDATE users SET age_attestation_at = NOW() WHERE username = $1 RETURNING id, age_attestation_at",
                args.user,
            )
            if not row:
                print(f"User '{args.user}' not found", file=sys.stderr)
                sys.exit(1)
            print(f"Attested user_id={row['id']} at {row['age_attestation_at']}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
