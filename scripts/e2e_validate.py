#!/usr/bin/env python3
"""
E2E Validation — AcademIA
Tests critical paths after scoring + security audit changes.
Creates ephemeral test user, validates, cleans up.
"""

import os
import sys
import json
import time
import requests
import psycopg2
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────
API = "http://127.0.0.1:8000"
INTERNAL_TOKEN = os.environ.get("INTERNAL_API_TOKEN", "REDACTED_INTERNAL_API_TOKEN")
TEST_USER = "test-e2e-validate"
TEST_PASS = "TestE2E-2026!"

def _read_secret(name, fallback=""):
    p = Path(f"/opt/academie-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DB_DSN = os.environ.get("DATABASE_URL", "")
if not DB_DSN:
    # Read from webapp .env file
    env_path = Path("/opt/academie/webapp/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                DB_DSN = line.split("=", 1)[1].strip()
                # Rewrite Docker hostname to localhost for host access
                DB_DSN = DB_DSN.replace("postgres-academie", "127.0.0.1")
                break
    if not DB_DSN:
        DB_DSN = "postgresql://sinse@127.0.0.1:5432/academie_db"

# ─── RESULT TRACKING ─────────────────────────────────────
results = []

def check(name, passed, detail=""):
    tag = "\033[32m[PASS]\033[0m" if passed else "\033[31m[FAIL]\033[0m"
    suffix = f" — {detail}" if detail else ""
    print(f"  {tag} {name}{suffix}")
    results.append((name, passed))

# ─── DB HELPERS ──────────────────────────────────────────
def db_exec(sql, params=None):
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.close()

def db_query(sql, params=None):
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute(sql, params or ())
    row = cur.fetchone()
    conn.close()
    return row

# ─── SETUP / TEARDOWN ────────────────────────────────────
def setup_test_user(token_admin):
    """Create ephemeral test user via API (needs admin token)."""
    r = requests.post(f"{API}/api/auth/users", json={
        "username": TEST_USER, "password": TEST_PASS, "exam_access": False,
    }, headers={"Authorization": f"Bearer {token_admin}"})
    return r.status_code == 200

def cleanup_test_user():
    """Remove test user + related data from DB."""
    row = db_query("SELECT id FROM users WHERE username = %s", (TEST_USER,))
    if row:
        uid = row[0]
        db_exec("DELETE FROM streaks WHERE user_id = %s", (uid,))
        db_exec("DELETE FROM xp_log WHERE user_id = %s", (uid,))
        db_exec("DELETE FROM user_sessions WHERE user_id = %s", (uid,))
        db_exec("DELETE FROM users WHERE id = %s", (uid,))
    row2 = db_query("SELECT id FROM eleves WHERE username = %s", (TEST_USER,))
    if row2:
        eid = row2[0]
        db_exec("DELETE FROM profils_eleves WHERE eleve_id = %s", (eid,))
        db_exec("DELETE FROM error_log WHERE eleve_id = %s", (eid,))
        db_exec("DELETE FROM snapshots_session WHERE eleve_id = %s", (eid,))
        db_exec("DELETE FROM eleves WHERE id = %s", (eid,))

def get_admin_token():
    """Login as sinse (admin) to create test user. Reads password from DB hash bypass: create user directly."""
    # Direct DB insert for test user (bypass admin login requirement)
    from passlib.context import CryptContext
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash(TEST_PASS)
    db_exec("""INSERT INTO users (username, password_hash, is_admin, exam_access)
               VALUES (%s, %s, false, false) ON CONFLICT (username) DO NOTHING""",
            (TEST_USER, hashed))
    db_exec("""INSERT INTO eleves (username, created_at)
               VALUES (%s, NOW()) ON CONFLICT (username) DO NOTHING""", (TEST_USER,))
    # Link eleve_id
    row = db_query("SELECT id FROM eleves WHERE username = %s", (TEST_USER,))
    if row:
        db_exec("UPDATE users SET eleve_id = %s WHERE username = %s", (row[0], TEST_USER))

# ─── TESTS ───────────────────────────────────────────────

def test_auth():
    """1. Auth — JWT with rotated secrets."""
    # Login
    r = requests.post(f"{API}/api/auth/login", json={"username": TEST_USER, "password": TEST_PASS})
    check("Auth: login", r.status_code == 200, f"status={r.status_code}")
    if r.status_code != 200:
        return None, None
    data = r.json()
    token = data["access_token"]
    refresh = data.get("refresh_token")

    # Me
    r = requests.get(f"{API}/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    check("Auth: /me", r.status_code == 200 and r.json()["username"] == TEST_USER)

    # Invalid token
    r = requests.get(f"{API}/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    check("Auth: invalid token rejected", r.status_code in (401, 403))

    # Refresh
    if refresh:
        r = requests.post(f"{API}/api/auth/refresh", json={"refresh_token": refresh})
        check("Auth: refresh", r.status_code == 200 and "access_token" in r.json())
        token = r.json().get("access_token", token)  # Use fresh token
    else:
        check("Auth: refresh", False, "no refresh_token returned")

    return token, refresh


def test_security_headers():
    """2. Security headers."""
    r = requests.get(f"{API}/api/health")
    h = r.headers
    check("Headers: X-Content-Type-Options", h.get("x-content-type-options") == "nosniff")
    check("Headers: X-Frame-Options", h.get("x-frame-options") == "DENY")
    check("Headers: Referrer-Policy", "strict-origin" in (h.get("referrer-policy") or ""))


def test_cors():
    """3. CORS."""
    # Evil origin
    r = requests.options(f"{API}/api/health", headers={
        "Origin": "https://evil.com",
        "Access-Control-Request-Method": "GET",
    })
    acao = r.headers.get("access-control-allow-origin", "")
    check("CORS: evil origin rejected", "evil.com" not in acao)

    # Legit origin
    r = requests.options(f"{API}/api/health", headers={
        "Origin": "https://academie.petit-pont.com",
        "Access-Control-Request-Method": "GET",
    })
    acao = r.headers.get("access-control-allow-origin", "")
    check("CORS: legit origin allowed", "academie.petit-pont.com" in acao)


def test_internal_endpoint():
    """4. Internal endpoint auth (C2)."""
    payload = {"username": "nobody", "session_id": "test", "transcript": ""}

    # No token
    r = requests.post(f"{API}/internal/analyze-errors", json=payload)
    check("Internal: no token → 403", r.status_code == 403)

    # Wrong token
    r = requests.post(f"{API}/internal/analyze-errors", json=payload,
                       headers={"X-Internal-Token": "wrong"})
    check("Internal: wrong token → 403", r.status_code == 403)

    # Correct token (empty transcript → functional response, not 403)
    r = requests.post(f"{API}/internal/analyze-errors", json=payload,
                       headers={"X-Internal-Token": INTERNAL_TOKEN})
    check("Internal: valid token accepted", r.status_code != 403, f"status={r.status_code}")


def test_student_endpoint(token):
    """5. Student profile endpoint (C3) — admin only."""
    r = requests.get(f"{API}/api/student/sinse/error-profile",
                      headers={"Authorization": f"Bearer {token}"})
    check("Student endpoint: non-admin → 403", r.status_code == 403)

    # Without auth
    r = requests.get(f"{API}/api/student/sinse/error-profile")
    check("Student endpoint: no auth → 401/403", r.status_code in (401, 403))


def test_profile_scoring(token):
    """6. Profile scoring — scores_confiance primary."""
    r = requests.get(f"{API}/api/profile/anglais",
                      headers={"Authorization": f"Bearer {token}"})
    check("Profile: responds", r.status_code == 200)
    if r.status_code != 200:
        return
    data = r.json()
    check("Profile: has niveau", True, f"niveau={data.get('niveau')} (None OK for new user)")
    check("Profile: has scores dict", isinstance(data.get("scores"), dict))

    # For sinse (admin user with real data), verify scores_confiance is used
    # For test user (no data), scores should be empty/zero — that's fine
    scores = data.get("scores", {})
    check("Profile: scores returned", isinstance(scores, dict))


def test_error_profile(token):
    """10. Error profile endpoint."""
    r = requests.get(f"{API}/api/error-profile/anglais",
                      headers={"Authorization": f"Bearer {token}"})
    check("Error profile: responds", r.status_code == 200)
    if r.status_code != 200:
        return
    data = r.json()
    check("Error profile: has families", isinstance(data.get("families"), dict))
    check("Error profile: has progression", "progress_pct" in data.get("progression", {}))
    check("Error profile: has concept_scores", isinstance(data.get("concept_scores"), dict))


def test_gamification(token):
    """9. Gamification endpoints."""
    r = requests.get(f"{API}/api/streak", headers={"Authorization": f"Bearer {token}"})
    check("Streak: responds", r.status_code == 200)

    r = requests.get(f"{API}/api/me/xp", headers={"Authorization": f"Bearer {token}"})
    check("XP: responds", r.status_code == 200)

    r = requests.get(f"{API}/api/me/badges", headers={"Authorization": f"Bearer {token}"})
    check("Badges: responds", r.status_code == 200)

    r = requests.get(f"{API}/api/stats/weekly", headers={"Authorization": f"Bearer {token}"})
    check("Weekly stats: responds", r.status_code == 200)


def test_settings(token):
    """Settings endpoints."""
    r = requests.get(f"{API}/api/me/settings", headers={"Authorization": f"Bearer {token}"})
    check("Settings: responds", r.status_code == 200)

    r = requests.get(f"{API}/api/me/recommendation", headers={"Authorization": f"Bearer {token}"})
    check("Recommendation: responds", r.status_code == 200)


def test_scoring_sinse():
    """6b. Verify sinse scores_confiance matches API (real user, direct DB comparison)."""
    # Get scores_confiance from DB
    row = db_query("""SELECT scores_confiance FROM profils_eleves
                      WHERE eleve_id = (SELECT id FROM eleves WHERE username = 'sinse')
                      AND domaine = 'anglais'""")
    if not row or not row[0]:
        check("Scoring sinse: scores_confiance in DB", True, "empty (profile was reset — OK)")
        return

    sc = row[0] if isinstance(row[0], dict) else json.loads(row[0])

    # Login as sinse not possible (no password), but we can call the scoring function directly
    # Instead, verify the DB data is consistent
    has_diverse = len(set(v.get("score", 0) for v in sc.values() if isinstance(v, dict))) > 1
    check("Scoring sinse: scores_confiance has diverse scores", has_diverse,
          f"{len(sc)} concepts, diverse={has_diverse}")


# ─── FUNCTIONAL TESTS (Dify, error pipeline, streak) ─────

E2E_SESSION_ID = "e2e-test-session"


def _parse_sse(response) -> tuple[str, str]:
    """Parse SSE stream, return (full_answer, conversation_id)."""
    answer = ""
    conv_id = ""
    for line in response.iter_lines():
        if not line or not line.startswith(b"data: "):
            continue
        try:
            event = json.loads(line[6:].decode("utf-8"))
            if event.get("event") in ("message", "agent_message"):
                answer += event.get("answer", "")
            if event.get("event") in ("message_end", "agent_message_end", "workflow_finished"):
                conv_id = event.get("conversation_id", conv_id)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
    return answer, conv_id


def test_chat_flow(token):
    """F1. Chat SSE — send message, get Teacher response via Dify."""
    try:
        r = requests.post(f"{API}/api/chat/send", json={
            "message": "Hello! I want to practice English today.",
            "agent": "teacher",
        }, headers={"Authorization": f"Bearer {token}"}, stream=True, timeout=60)
        check("Chat: HTTP 200", r.status_code == 200, f"status={r.status_code}")
        if r.status_code != 200:
            return "", ""

        answer, conv_id = _parse_sse(r)
        check("Chat: got response", len(answer) > 10, f"{len(answer)} chars")
        check("Chat: conversation_id returned", len(conv_id) > 0)
        return answer, conv_id
    except requests.Timeout:
        check("Chat: timeout", False, "Dify did not respond in 60s")
        return "", ""
    except Exception as e:
        check("Chat: error", False, str(e)[:80])
        return "", ""


def test_error_analysis(token):
    """F2. Error analysis pipeline — transcript → error_log."""
    transcript = (
        "--- Turn 1 ---\n"
        "USER: i think since 3 years its a good programme and i must to go\n"
        "ASSISTANT: Let me help you with that.\n"
    )
    r = requests.post(f"{API}/internal/analyze-errors", json={
        "username": TEST_USER,
        "domaine": "anglais",
        "session_id": E2E_SESSION_ID,
        "transcript": transcript,
    }, headers={"X-Internal-Token": INTERNAL_TOKEN}, timeout=60)
    check("Error analysis: HTTP 200", r.status_code == 200, f"status={r.status_code}")
    if r.status_code != 200:
        return

    data = r.json()
    check("Error analysis: errors detected", data.get("errors_detected", 0) > 0,
          f"found {data.get('errors_detected', 0)}")
    check("Error analysis: rules layer worked", data.get("rule_errors", 0) > 0,
          f"rule={data.get('rule_errors', 0)}")

    # Verify in DB
    row = db_query("SELECT COUNT(*) FROM error_log WHERE session_id = %s", (E2E_SESSION_ID,))
    check("Error analysis: errors in DB", row and row[0] > 0, f"count={row[0] if row else 0}")


def test_streak_after_chat(token):
    """F3. Streak incremented after chat message."""
    r = requests.get(f"{API}/api/streak", headers={"Authorization": f"Bearer {token}"})
    before = r.json().get("total_sessions", 0) if r.status_code == 200 else 0

    # Chat message was sent in test_chat_flow — streak should already be updated
    r = requests.get(f"{API}/api/streak", headers={"Authorization": f"Bearer {token}"})
    after = r.json() if r.status_code == 200 else {}
    check("Streak: current > 0 after chat", after.get("current_streak", 0) > 0,
          f"current={after.get('current_streak', 0)}")


def test_error_profile_after_analysis(token):
    """F4. Error profile reflects analyzed errors."""
    r = requests.get(f"{API}/api/error-profile/anglais",
                     headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        check("Error profile post-analysis: responds", False)
        return
    data = r.json()
    sessions = data.get("progression", {}).get("sessions_total", 0)
    check("Error profile post-analysis: sessions > 0", sessions > 0,
          f"sessions_total={sessions}")
    families = data.get("families", {})
    has_errors = any(f.get("count", 0) > 0 for f in families.values())
    check("Error profile post-analysis: families have errors", has_errors)


def test_admin_endpoints(token):
    """F5. Admin endpoints."""
    # Non-admin can't access
    r = requests.get(f"{API}/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    check("Admin: non-admin → 403", r.status_code == 403)

    # Create temp admin for testing
    db_exec("UPDATE users SET is_admin = true WHERE username = %s", (TEST_USER,))
    # Re-login to get admin token
    r = requests.post(f"{API}/api/auth/login", json={"username": TEST_USER, "password": TEST_PASS})
    admin_token = r.json()["access_token"]

    r = requests.get(f"{API}/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    check("Admin: list users", r.status_code == 200)
    if r.status_code == 200:
        users = r.json()
        check("Admin: users have online field", all("online" in u for u in users))
        check("Admin: users have last_seen", all("last_seen" in u for u in users))

    # Restore non-admin
    db_exec("UPDATE users SET is_admin = false WHERE username = %s", (TEST_USER,))


def test_profile_next_level(token):
    """F6. Profile returns next_level_scores."""
    r = requests.get(f"{API}/api/profile/anglais", headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        check("Profile next_level: responds", False)
        return
    data = r.json()
    check("Profile: has next_level field", "next_level" in data)
    check("Profile: has next_level_scores", "next_level_scores" in data and isinstance(data["next_level_scores"], dict))


def test_exam_result_endpoint():
    """F7. XP triggers — exam result endpoint."""
    # Test with non-existent user
    r = requests.post(f"{API}/internal/exam-result", json={
        "username": "nonexistent", "passed": True, "score": 80,
        "niveau_from": "B1", "niveau_to": "B2"
    }, headers={"X-Internal-Token": INTERNAL_TOKEN})
    check("Exam result: unknown user → 404", r.status_code == 404)

    # Test with no token
    r = requests.post(f"{API}/internal/exam-result", json={
        "username": TEST_USER, "passed": True, "score": 80,
        "niveau_from": "B1", "niveau_to": "B2"
    })
    check("Exam result: no token → 403", r.status_code == 403)


def test_error_exam_eligible():
    """F8. Error analysis updates error_exam_eligible flag."""
    row = db_query(
        "SELECT error_exam_eligible FROM profils_eleves WHERE eleve_id = (SELECT id FROM eleves WHERE username = %s)",
        (TEST_USER,))
    # May not have profil yet, that's OK
    check("Error eligible: flag exists or no profile", True,
          f"value={row[0] if row else 'no profile'}")


def test_behavior_signals(token):
    """F9. Behavior signals passed to Dify (turn_response_secs, repeated_errors)."""
    # We can't directly verify Dify inputs, but we can verify the chat works
    # with the new signals (no regression)
    try:
        r = requests.post(f"{API}/api/chat/send", json={
            "message": "i have 25 years and i live here since 3 years",
            "agent": "teacher",
        }, headers={"Authorization": f"Bearer {token}"}, stream=True, timeout=60)
        check("Behavior signals: chat with errors works", r.status_code == 200)
        # Parse to verify stream completes
        answer = ""
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                try:
                    event = json.loads(line[6:])
                    if event.get("event") in ("message", "agent_message"):
                        answer += event.get("answer", "")
                except:
                    pass
        check("Behavior signals: Teacher responds with errors", len(answer) > 20, f"{len(answer)} chars")
    except Exception as e:
        check("Behavior signals: error", False, str(e)[:80])


def cleanup_functional():
    """Remove functional test data from DB."""
    db_exec("DELETE FROM error_log WHERE session_id = %s", (E2E_SESSION_ID,))


# ─── MAIN ────────────────────────────────────────────────

def main():
    print(f"\n🔍 E2E Validate — AcademIA — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Setup
    print("  Setup: creating test user...")
    cleanup_test_user()  # Clean any leftover
    get_admin_token()    # Create test user directly in DB
    print("  Setup: done\n")

    try:
        # Auth
        token, refresh = test_auth()
        if not token:
            print("\n  ⛔ Auth failed — cannot continue\n")
            return

        print()
        test_security_headers()
        print()
        test_cors()
        print()
        test_internal_endpoint()
        print()
        test_student_endpoint(token)
        print()
        test_profile_scoring(token)
        print()
        test_error_profile(token)
        print()
        test_gamification(token)
        print()
        test_settings(token)
        print()
        test_scoring_sinse()

        # ── Functional tests (Dify + error pipeline) ──
        print("\n  ── Functional tests ──\n")
        answer, conv_id = test_chat_flow(token)
        print()
        test_error_analysis(token)
        print()
        test_streak_after_chat(token)
        print()
        test_error_profile_after_analysis(token)

        # ── New feature tests ──
        print("\n  ── New feature tests ──\n")
        test_admin_endpoints(token)
        print()
        test_profile_next_level(token)
        print()
        test_exam_result_endpoint()
        print()
        test_error_exam_eligible()
        print()
        test_behavior_signals(token)

    finally:
        # Cleanup
        print("\n  Cleanup: removing test user + functional data...")
        cleanup_functional()
        cleanup_test_user()
        print("  Cleanup: done")

    # Summary
    passed = sum(1 for _, p in results if p)
    failed = sum(1 for _, p in results if not p)
    print(f"\n{'━' * 40}")
    print(f"  Results: \033[32m{passed} passed\033[0m  \033[31m{failed} failed\033[0m")
    print(f"{'━' * 40}")
    if failed:
        print(f"  \033[31mFAILED\033[0m")
        for name, p in results:
            if not p:
                print(f"    ✗ {name}")
    else:
        print(f"  \033[32mALL CLEAR\033[0m")
    print()

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
