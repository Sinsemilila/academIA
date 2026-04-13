#!/usr/bin/env python3
"""
Cron snapshot safety net.

Detects conversations with unsnapshot messages (inactive 2h+)
and triggers n8n dify-snapshot for each.

Run via crontab every hour:
  0 * * * * /usr/bin/python3 /opt/academie/scripts/cron_snapshot_safety.py >> /var/log/academie-snapshot-cron.log 2>&1

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
    "teacher": "anglais",
    "maestro": "espagnol",
    "sensei": "japonais",
    "lehrer": "allemand",
    "professore": "italien",
    "pymentor": "python",
    "cybermentor": "cybersec",
}


async def run():
    conn = await asyncpg.connect(DB_DSN)
    try:
        rows = await conn.fetch("""
            SELECT us.id, us.dify_conversation_id, us.agent_name,
                   us.message_count, u.username
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
                domaine = AGENT_DOMAIN.get(row["agent_name"], "anglais")
                payload = {
                    "username": row["username"],
                    "domaine": domaine,
                    "conversation_id": row["dify_conversation_id"],
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
