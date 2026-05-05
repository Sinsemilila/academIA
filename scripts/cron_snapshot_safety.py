#!/usr/bin/env python3
"""
Cron snapshot safety net.

Detects conversations with unsnapshot messages (inactive 2h+)
and triggers n8n dify-snapshot for each.

Run via crontab every hour:
  0 * * * * /usr/bin/python3 /opt/academia/scripts/cron_snapshot_safety.py >> /var/log/academie-snapshot-cron.log 2>&1

When no stale sessions exist, does nothing (idle).
"""

import os
import asyncio
import asyncpg
import httpx
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [snapshot-cron] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
log = logging.getLogger(__name__)

DB_DSN = os.environ.get("DATABASE_URL", "postgresql://sinse@127.0.0.1:5432/academie_db")
N8N_SNAPSHOT_URL = "http://127.0.0.1:5678/webhook/dify-snapshot"
STALE_HOURS = 2

AGENT_DOMAIN = {
    "teacher": "en",
    "maestro": "espagnol",
    "sensei": "japonais",
    "lehrer": "allemand",
    "professore": "italien",
    "pymentor": "python",
    "cybermentor": "cybersec",
}

# Session 37 — Dify app-scoped keys per agent for public API calls.
# Workflow reads `dify_app_key` from webhook body. Populated from env at cron
# launch time so rotation is transparent (just update webapp/.env).
AGENT_TO_KEY_ENV = {
    "teacher": "DIFY_KEY_TEACHER",
    "maestro": "DIFY_KEY_MAESTRO",
    # Wave 2+ : add sensei / lehrer / professore when activated
}


async def run():
    conn = await asyncpg.connect(DB_DSN)
    try:
        # Session 37 — add u.dify_user_id for public-API `user=` param.
        # Coalesce with legacy `user_{id}` pattern for rows where dify_user_id
        # hasn't been set yet (pre-Sprint-5 accounts).
        rows = await conn.fetch("""
            SELECT us.id, us.dify_conversation_id, us.agent_name,
                   us.message_count, u.username,
                   COALESCE(u.dify_user_id, 'user_' || u.id::text) AS dify_user_id
            FROM user_sessions us
            JOIN users u ON u.id = us.user_id
            WHERE us.last_message_at > COALESCE(us.last_snapshot_at, '1970-01-01'::timestamptz)
              AND us.last_message_at < NOW() - INTERVAL '2 hours'
              AND us.dify_conversation_id IS NOT NULL
              AND us.message_count > 0
        """)

        if not rows:
            log.info("Idle — no stale sessions.")
            return

        log.info(f"{len(rows)} stale session(s) found.")

        async with httpx.AsyncClient(timeout=120.0) as client:
            for row in rows:
                domain = AGENT_DOMAIN.get(row["agent_name"], "en")
                # Session 37 — resolve app-scoped Dify key per agent
                app_key_env = AGENT_TO_KEY_ENV.get(row["agent_name"])
                dify_app_key = os.environ.get(app_key_env, "") if app_key_env else ""
                if not dify_app_key:
                    log.warning(f"  SKIP {row['username']}/{row['agent_name']}: no app key in env ({app_key_env})")
                    continue
                payload = {
                    "username": row["username"],
                    "domain": domain,
                    "conversation_id": row["dify_conversation_id"],
                    # Session 37 — Dify public API auth + user param
                    "dify_user_id": row["dify_user_id"],
                    "dify_app_key": dify_app_key,
                }
                label = f"{row['username']}/{row['agent_name']} ({row['message_count']} msgs)"

                try:
                    res = await client.post(N8N_SNAPSHOT_URL, json=payload)
                    if res.status_code == 200:
                        await conn.execute(
                            "UPDATE user_sessions SET last_snapshot_at = NOW() WHERE id = $1",
                            row["id"],
                        )
                        log.info(f"  OK  {label}")
                    else:
                        log.warning(f"  FAIL {label} — n8n {res.status_code}: {res.text[:200]}")
                except Exception as e:
                    log.error(f"  ERR  {label} — {e}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
