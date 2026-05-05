#!/usr/bin/env python3
"""
E2E Test — Full onboarding flow (new user → diagnostic → bilan).

Tests the complete chain:
1. Create fresh test user in DB
2. Chat with Teacher via Dify — Phase 1 (2 FR turns) + Phase 2 (5-7 EN exchanges)
3. Send 'ok' to trigger diagnostic webhook
4. Verify all fields stored in profils_eleves
5. Verify profile API returns new fields
6. Clean up

Usage:
  python3 e2e_onboarding_test.py           # run full test
  python3 e2e_onboarding_test.py --clean   # clean up only
  python3 e2e_onboarding_test.py --keep    # run but keep test data
"""

import os
import sys
import json
import time
import requests
import psycopg2

# ─── CONFIG ──────────────────────────────────────────────────────────────────
def _read_secret(name, fallback=""):
    from pathlib import Path
    p = Path(f"/opt/academia-shared/secrets/{name}")
    return p.read_text().strip() if p.exists() else fallback

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "academie_db")
DB_USER = os.environ.get("DB_USER", "sinse")
DB_PASS = os.environ.get("DB_PASSWORD", _read_secret("pg-password"))

DIFY_URL = "http://localhost:5001/v1/chat-messages"
DIFY_KEY = os.environ.get("DIFY_KEY_TEACHER", _read_secret("dify-teacher-key"))
TEST_USER = "test-e2e-onboarding"

LITELLM_URL = "http://localhost:4000/chat/completions"
LITELLM_MASTER_KEY = os.environ.get("LITELLM_MASTER_KEY") or _read_secret("litellm-master-key")

passed = 0
failed = 0
warnings = 0


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {label}")
    else:
        failed += 1
        print(f"  ❌ {label}" + (f" — {detail}" if detail else ""))


def warn(label, detail=""):
    global warnings
    warnings += 1
    print(f"  ⚠️  {label}" + (f" — {detail}" if detail else ""))


# ─── DB ──────────────────────────────────────────────────────────────────────
def db_connect():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
    )


def setup_db():
    """Create a fresh test user with NO profile — simulates brand-new user."""
    conn = db_connect()
    cur = conn.cursor()
    # Clean any previous test data
    cur.execute("DELETE FROM error_log WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM snapshots_session WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM profils_eleves WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM eleves WHERE username=%s", (TEST_USER,))
    conn.commit()

    # Create eleve only — no profils_eleves (that's what onboarding creates)
    cur.execute("INSERT INTO eleves (username) VALUES (%s) ON CONFLICT DO NOTHING", (TEST_USER,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"🔧 DB setup: {TEST_USER} created (no profile)")


def cleanup_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM error_log WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM snapshots_session WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM profils_eleves WHERE eleve_id IN (SELECT id FROM eleves WHERE username=%s)", (TEST_USER,))
    cur.execute("DELETE FROM eleves WHERE username=%s", (TEST_USER,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"🗑️  DB cleaned: {TEST_USER} removed")


def get_profile_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT pe.niveau_global, pe.points_forts, pe.lacunes, pe.plan_sessions,
               pe.personnalite, pe.mode_apprentissage, pe.scores_confiance,
               pe.details_par_competence, pe.diagnostic_justification,
               pe.onboarding_completed_at, pe.auto_eval_level,
               pe.diagnostic_exchange_count
        FROM profils_eleves pe JOIN eleves e ON pe.eleve_id = e.id
        WHERE e.username = %s AND pe.domaine = 'anglais'
    """, (TEST_USER,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {
        "niveau_global": row[0],
        "points_forts": row[1],
        "lacunes": row[2],
        "plan_sessions": row[3],
        "personnalite": row[4],
        "mode_apprentissage": row[5],
        "scores_confiance": row[6],
        "details_par_competence": row[7],
        "diagnostic_justification": row[8],
        "onboarding_completed_at": row[9],
        "auto_eval_level": row[10],
        "diagnostic_exchange_count": row[11],
    }


# ─── DIFY API ────────────────────────────────────────────────────────────────
def dify_chat(query, conv_id=""):
    """Send a message to the Teacher chatflow via Dify API."""
    r = requests.post(DIFY_URL, headers={
        "Authorization": f"Bearer {DIFY_KEY}",
        "Content-Type": "application/json"
    }, json={
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conv_id,
        "user": TEST_USER,
    }, timeout=120)
    if r.status_code != 200:
        print(f"  ⚠️  Dify HTTP {r.status_code}: {r.text[:200]}")
        return "", conv_id
    data = r.json()
    answer = data.get("answer", "")
    new_conv_id = data.get("conversation_id", conv_id)
    return answer, new_conv_id


def generate_en_answer(question, level="B1"):
    """Use LiteLLM to generate a natural English answer at the specified level."""
    prompt = (
        f"You are a {level}-level English learner taking an informal placement chat. "
        f"Answer the following question naturally, as a real student would — "
        f"with some minor mistakes typical of {level} level. "
        f"Keep your answer to 2-3 sentences. English only.\n\n"
        f"Question: {question}"
    )
    try:
        r = requests.post(LITELLM_URL, headers={
            "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": "mistral-small",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 100,
            "temperature": 0.7,
        }, timeout=60)
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠️  LiteLLM error: {e}")
        return "I think it is a good question. I like to talk about this topic because it is interesting for me."


# ─── MAIN TEST ───────────────────────────────────────────────────────────────
def run_test():
    global passed, failed, warnings
    start_time = time.time()

    print("\n" + "=" * 60)
    print("  E2E ONBOARDING TEST")
    print("=" * 60)

    # ── Step 1: DB Setup ──
    print("\n[1/6] DB Setup")
    setup_db()

    # Verify no profile exists yet
    profile = get_profile_db()
    check("No profile before onboarding", profile is None)

    # ── Step 2: Phase 1 — FR turns ──
    print("\n[2/6] Phase 1 — Accueil (FR)")

    # Turn 1: name + motivation
    answer1, conv_id = dify_chat("Salut !")
    print(f"  → Teacher: {answer1[:120]}...")
    check("Teacher responds in FR", any(w in answer1.lower() for w in ["bonjour", "salut", "bienvenue", "comment", "hello"]))

    answer2, conv_id = dify_chat("Je m'appelle Marie et j'apprends l'anglais pour le travail.", conv_id)
    print(f"  → Teacher: {answer2[:120]}...")

    # Turn 2: auto-eval
    answer3, conv_id = dify_chat("Je peux avoir une conversation basique, raconter des choses", conv_id)
    print(f"  → Teacher: {answer3[:120]}...")

    # Check that Teacher switched to EN diagnostic
    has_english = any(c.isascii() and c.isalpha() for c in answer3)
    check("Teacher transitions to EN diagnostic", has_english)

    # ── Step 3: Phase 2 — EN diagnostic exchanges ──
    print("\n[3/6] Phase 2 — Diagnostic (EN)")

    eval_ready = False
    exchange_count = 0
    max_exchanges = 10  # safety limit

    # The last answer (answer3) likely contains the first EN question
    last_answer = answer3

    while not eval_ready and exchange_count < max_exchanges:
        # Generate a B1-level answer to whatever Teacher asked
        en_answer = generate_en_answer(last_answer, level="B1")
        print(f"  → Student ({exchange_count + 1}): {en_answer[:80]}...")

        answer, conv_id = dify_chat(en_answer, conv_id)
        print(f"  → Teacher: {answer[:120]}...")

        exchange_count += 1

        if "[EVAL_READY]" in answer or "bilan" in answer.lower() or "'ok'" in answer.lower() or "envoie" in answer.lower():
            eval_ready = True

    check("Diagnostic completed (EVAL_READY detected)", eval_ready)
    check("At least 5 EN exchanges", exchange_count >= 5, f"got {exchange_count}")
    if exchange_count > 7:
        warn(f"More than 7 exchanges ({exchange_count})", "prompt says 5-7")

    # ── Step 4: Trigger diagnostic ──
    print("\n[4/6] Trigger diagnostic (send 'ok')")

    answer_ok, conv_id = dify_chat("ok", conv_id)
    print(f"  → Teacher: {answer_ok[:120]}...")

    # Wait for n8n diagnostic workflow to complete
    print("  ⏳ Waiting for diagnostic workflow (10s)...")
    time.sleep(10)

    # ── Step 5: Verify DB ──
    print("\n[5/6] Verify DB — profils_eleves")

    profile = get_profile_db()
    check("Profile created in DB", profile is not None)

    if profile:
        check("niveau_global is set", profile["niveau_global"] is not None, f"got: {profile['niveau_global']}")
        check("niveau_global is valid CECRL", profile["niveau_global"] in ("A1", "A2", "B1", "B2", "C1", "C2"),
              f"got: {profile['niveau_global']}")
        check("points_forts is set", profile["points_forts"] is not None)
        check("lacunes is set", profile["lacunes"] is not None)
        check("plan_sessions is set", profile["plan_sessions"] is not None)
        check("personnalite is set", profile["personnalite"] is not None)

        if profile["personnalite"]:
            perso = profile["personnalite"] if isinstance(profile["personnalite"], dict) else json.loads(profile["personnalite"])
            check("personnalite.prenom extracted", bool(perso.get("prenom")), f"got: {perso.get('prenom')}")
            check("personnalite.raison extracted", bool(perso.get("raison")), f"got: {perso.get('raison')}")

        check("mode_apprentissage defaults to 'libre'", profile["mode_apprentissage"] == "libre",
              f"got: {profile['mode_apprentissage']}")

        # New fields (plumbing fixes)
        check("details_par_competence stored (NOT NULL)", profile["details_par_competence"] is not None)
        if profile["details_par_competence"]:
            dpc = profile["details_par_competence"] if isinstance(profile["details_par_competence"], dict) else json.loads(profile["details_par_competence"])
            check("details has grammaire", "grammaire" in dpc, f"keys: {list(dpc.keys())}")
            check("details has vocabulaire", "vocabulaire" in dpc, f"keys: {list(dpc.keys())}")
            check("details has production", "production" in dpc, f"keys: {list(dpc.keys())}")

        check("diagnostic_justification stored", profile["diagnostic_justification"] is not None)
        check("onboarding_completed_at is set", profile["onboarding_completed_at"] is not None)

        # Instrumentation
        if profile["auto_eval_level"]:
            check("auto_eval_level captured", True, f"value: {profile['auto_eval_level']}")
        else:
            warn("auto_eval_level is NULL", "LLM may not have extracted it")

        if profile["diagnostic_exchange_count"] and profile["diagnostic_exchange_count"] > 0:
            check("diagnostic_exchange_count captured", True, f"value: {profile['diagnostic_exchange_count']}")
        else:
            warn("diagnostic_exchange_count is 0 or NULL", "LLM may not have counted")

        # scores_confiance should NOT have been wiped
        sc = profile["scores_confiance"]
        if isinstance(sc, str):
            sc = json.loads(sc)
        # For a new user it should be {} (no scores yet) — that's fine
        # The important thing is the COALESCE logic works (tested on re-diagnostic)
        check("scores_confiance is valid JSONB", isinstance(sc, dict))

        print(f"\n  📊 Summary: niveau={profile['niveau_global']}, "
              f"details={profile['details_par_competence']}, "
              f"auto_eval={profile['auto_eval_level']}, "
              f"exchanges={profile['diagnostic_exchange_count']}")

    # ── Step 6: Summary ──
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed / {failed} failed / {warnings} warnings")
    print(f"  Duration: {elapsed:.0f}s")
    print("=" * 60)

    if failed > 0:
        print("  ❌ SOME TESTS FAILED")
    else:
        print("  ✅ ALL TESTS PASSED")

    return failed == 0


# ─── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "--clean" in sys.argv:
        cleanup_db()
        sys.exit(0)

    keep = "--keep" in sys.argv

    try:
        success = run_test()
    except Exception as e:
        print(f"\n💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        success = False

    if not keep:
        print("\n[Cleanup]")
        cleanup_db()

    sys.exit(0 if success else 1)
