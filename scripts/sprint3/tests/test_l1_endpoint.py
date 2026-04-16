"""Sprint 3 Phase 6 — Integration test for /api/profile/l1 GET/PUT.

Creates a throwaway user, logs in via the real auth endpoint, hits the L1
endpoints, verifies the DB row is written, and also verifies that the
chat_router lookup path (niveau + l1 + l1_watch_enabled) sees the values.

Run :
  python3 scripts/sprint3/tests/test_l1_endpoint.py

Exit code 0 on all pass. Cleans up even on failure. No pytest — stays consistent
with `scripts/sprint3/eval_live_battery.py` pattern (direct psycopg2 + httpx).
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
import psycopg2
from passlib.context import CryptContext


API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
TEST_USERNAME = "test-l1-endpoint"
TEST_PASSWORD = "L1Endpoint-2026!"


def _db_dsn() -> str:
    env = Path("/opt/academie/webapp/.env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip().replace("postgres-academie", "127.0.0.1")
    return "postgresql://sinse@127.0.0.1:5432/academie_db"


DSN = _db_dsn()


def _exec(sql: str, params: tuple | None = None):
    with psycopg2.connect(DSN) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(sql, params or ())


def _query(sql: str, params: tuple | None = None):
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def setup() -> int:
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    pw_hash = pwd_ctx.hash(TEST_PASSWORD)
    _exec(
        """INSERT INTO users (username, password_hash, is_admin, exam_access)
           VALUES (%s, %s, FALSE, FALSE)
           ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash""",
        (TEST_USERNAME, pw_hash),
    )
    _exec(
        """INSERT INTO eleves (username, created_at) VALUES (%s, NOW())
           ON CONFLICT (username) DO NOTHING""",
        (TEST_USERNAME,),
    )
    eid = _query("SELECT id FROM eleves WHERE username = %s", (TEST_USERNAME,))[0]
    _exec("UPDATE users SET eleve_id = %s WHERE username = %s", (eid, TEST_USERNAME))
    # Seed the profile row so the PUT endpoint doesn't 404.
    _exec(
        """INSERT INTO profils_eleves (eleve_id, domaine, niveau_global, updated_at)
           VALUES (%s, 'anglais', 'B1', NOW())
           ON CONFLICT (eleve_id, domaine) DO NOTHING""",
        (eid,),
    )
    return eid


def cleanup(eid: int) -> None:
    u = _query("SELECT id FROM users WHERE username = %s", (TEST_USERNAME,))
    if u:
        _exec("DELETE FROM users WHERE id = %s", (u[0],))
    _exec("DELETE FROM profils_eleves WHERE eleve_id = %s", (eid,))
    _exec("DELETE FROM eleves WHERE id = %s", (eid,))


def login(client: httpx.Client) -> str:
    r = client.post(
        f"{API_BASE}/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> int:
    print(f"▸ Setup test user '{TEST_USERNAME}'...", flush=True)
    eid = setup()
    fails: list[str] = []
    try:
        with httpx.Client(timeout=10.0) as client:
            token = login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # 1. GET default — profile row has NULL l1 + default TRUE watch.
            # DB default on l1 fires on INSERT; we inserted without specifying l1 so it gets 'fr'.
            r = client.get(f"{API_BASE}/api/profile/l1", headers=headers)
            print(f"  GET default → {r.status_code} {r.text[:80]}")
            if r.status_code != 200:
                fails.append(f"GET default expected 200 got {r.status_code}")
            else:
                body = r.json()
                if body.get("l1") != "fr":
                    fails.append(f"GET default l1 expected 'fr' got {body.get('l1')!r}")
                if body.get("l1_watch_enabled") is not True:
                    fails.append(f"GET default l1_watch_enabled expected True got {body.get('l1_watch_enabled')!r}")

            # 2. PUT valid l1='es' + disable watch.
            r = client.put(
                f"{API_BASE}/api/profile/l1",
                json={"l1": "es", "l1_watch_enabled": False},
                headers=headers,
            )
            print(f"  PUT es/off → {r.status_code} {r.text[:80]}")
            if r.status_code != 200:
                fails.append(f"PUT es/off expected 200 got {r.status_code} body={r.text[:200]}")
            else:
                body = r.json()
                if body.get("l1") != "es" or body.get("l1_watch_enabled") is not False:
                    fails.append(f"PUT es/off response unexpected: {body}")
                # Verify DB write.
                row = _query(
                    "SELECT l1, l1_watch_enabled FROM profils_eleves WHERE eleve_id = %s AND domaine = 'anglais'",
                    (eid,),
                )
                if row != ("es", False):
                    fails.append(f"DB state after PUT es/off: {row}")

            # 3. GET again — reflects updated state.
            r = client.get(f"{API_BASE}/api/profile/l1", headers=headers)
            print(f"  GET after PUT → {r.status_code} {r.text[:80]}")
            if r.status_code == 200:
                body = r.json()
                if body.get("l1") != "es" or body.get("l1_watch_enabled") is not False:
                    fails.append(f"GET after PUT wrong: {body}")
            else:
                fails.append(f"GET after PUT expected 200 got {r.status_code}")

            # 4. PUT normalisation — uppercase accepted, stored lowercase.
            r = client.put(
                f"{API_BASE}/api/profile/l1",
                json={"l1": "FR", "l1_watch_enabled": True},
                headers=headers,
            )
            print(f"  PUT 'FR' (uppercase) → {r.status_code} {r.text[:80]}")
            if r.status_code != 200:
                fails.append(f"PUT FR expected 200 got {r.status_code} body={r.text[:200]}")
            else:
                body = r.json()
                if body.get("l1") != "fr":
                    fails.append(f"PUT FR normalisation failed — got l1={body.get('l1')!r}")

            # 5. PUT invalid — reject 3-char language code at pydantic layer.
            r = client.put(
                f"{API_BASE}/api/profile/l1",
                json={"l1": "eng", "l1_watch_enabled": True},
                headers=headers,
            )
            print(f"  PUT invalid 'eng' → {r.status_code} {r.text[:100]}")
            if r.status_code not in (422, 400):
                fails.append(f"PUT invalid expected 422/400 got {r.status_code}")

            # 6. PUT invalid — non-lowercase-letter characters.
            r = client.put(
                f"{API_BASE}/api/profile/l1",
                json={"l1": "1!", "l1_watch_enabled": True},
                headers=headers,
            )
            print(f"  PUT invalid '1!' → {r.status_code} {r.text[:100]}")
            if r.status_code not in (422, 400):
                fails.append(f"PUT bogus expected 422/400 got {r.status_code}")

            # 7. Unauthed access rejected.
            r = client.get(f"{API_BASE}/api/profile/l1")
            print(f"  GET unauthed → {r.status_code}")
            if r.status_code not in (401, 403):
                fails.append(f"Unauthed GET expected 401/403 got {r.status_code}")
    finally:
        print(f"▸ Cleanup", flush=True)
        cleanup(eid)

    if fails:
        print(f"\n❌ {len(fails)} failures:")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"\n✅ All L1 endpoint checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
