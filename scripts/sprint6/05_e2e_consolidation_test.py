"""E2E test — CEFR consolidation pipeline (Session 36 follow-up).

Run 8 seeded scenarios covering {teacher,maestro} × {A1,A2,B1,B2} with varied
consolidation paths (auto_validate, mini-exam pass/fail, anti-whiplash clamp),
plus an optional organic scenario where an LLM-as-learner simulates a real
chat session until trigger fires naturally.

Usage (inside academie-api container):
  docker exec academie-api python3 /tmp/05_e2e_consolidation_test.py --mode seeded
  docker exec academie-api python3 /tmp/05_e2e_consolidation_test.py --mode both --include-organic

Outputs a JSON report to /tmp/consolidation_e2e_<ts>.json with per-scenario
status, DB state, and event trail.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Make helpers importable whether file is /tmp/ or scripts/sprint6/
sys.path.insert(0, str(Path(__file__).parent))
import _e2e_helpers as H


# ── Matrix definition ─────────────────────────────────────────────────

# Each scenario: (id, agent, domain, qcm_level, observed_seed, mini_exam_mode,
#                 decide_choice, expected_final, expected_status, description)
# mini_exam_mode: "auto"   → auto_validate path, no mini-exam call
#                 "pass"   → submit correct answers
#                 "fail"   → submit wrong answers
# decide_choice:  "accept_new" | "stay_current" | None (when auto/fail)
# expected_final: final niveau_global after all steps
MATRIX = [
    ("S1", "teacher", "en", "A1", "A1", "auto", None,         "A1", "validé",
     "match: QCM=A1 obs=A1 → auto_validate"),
    ("S2", "teacher", "en", "A2", "B1", "pass", "accept_new", "B1", "validé",
     "upgrade A2→B1, exam pass, accept new"),
    ("S3", "teacher", "en", "B1", "A2", "fail", None,         "B1", "validé",
     "downgrade B1→A2 proposed, exam fails → keep QCM"),
    ("S4", "teacher", "en", "A1", "B2", "pass", "accept_new", "A2", "validé",
     "clamp ±1: QCM=A1 obs=B2 → clamped A2, exam pass, accept new"),
    ("S5", "maestro", "es", "A1", "A1", "auto", None,         "A1", "validé",
     "match ES: QCM=A1 obs=A1 → auto_validate"),
    ("S6", "maestro", "es", "A2", "A1", "pass", "accept_new", "A1", "validé",
     "downgrade A2→A1, exam pass, accept new"),
    ("S7", "maestro", "es", "B1", "B1", "auto", None,         "B1", "validé",
     "match ES: QCM=B1 obs=B1 → auto_validate"),
    ("S8", "maestro", "es", "B2", "B1", "fail", None,         "B2", "validé",
     "downgrade B2→B1 proposed, exam fails → keep QCM"),
]


# ── Scenario runner ───────────────────────────────────────────────────

async def run_scenario(
    sid: str, agent: str, domain: str, qcm: str, observed: str,
    mini_exam_mode: str, decide_choice: str | None,
    expected_final: str, expected_status: str, description: str,
    user_id: int, eleve_id: int, token: str,
) -> dict:
    """Execute one scenario end-to-end, return result dict."""
    t0 = time.time()
    result = {
        "id": sid, "agent": agent, "domain": domain, "qcm": qcm,
        "observed_seed": observed, "mini_exam_mode": mini_exam_mode,
        "decide_choice": decide_choice, "description": description,
        "expected_final": expected_final, "expected_status": expected_status,
        "actual_final": None, "actual_status": None,
        "passed": False, "errors": [], "steps": [],
    }

    try:
        # 1. Reset scope
        await H.reset_scenario(eleve_id, domain)
        result["steps"].append("reset")

        # 2. QCM submit via API
        qcm_resp = await H.submit_qcm(token, domain, qcm)
        assert qcm_resp.get("cefr_placement") == qcm, f"QCM placement mismatch: {qcm_resp}"
        result["steps"].append(f"qcm_submit({qcm})")

        # 3. Seed profils_eleves row (simulates what first chat turn would do)
        await H.seed_profils_eleves(eleve_id, domain, qcm)
        result["steps"].append("seed_profil")

        # 4. Seed pending decision (simulates _consolidation_post_turn firing
        #    after N=8 turns with observed_level=observed). For "auto" scenarios
        #    this directly writes niveau_status='validé' via auto_validate.
        outcome = await H.seed_pending_decision(eleve_id, domain, qcm, observed)
        result["steps"].append(f"seed_pending({outcome.kind},{outcome.observed_level})")
        result["decide_outcome_kind"] = outcome.kind
        result["clamped_observed"] = outcome.observed_level

        if mini_exam_mode == "auto":
            # Expect auto_validate path — no mini-exam, no decide call
            assert outcome.kind == "auto_validate", \
                f"Expected auto_validate, got {outcome.kind}"
        else:
            # Expect propose_mini_exam, then run mini-exam + maybe decide
            assert outcome.kind == "propose_mini_exam", \
                f"Expected propose_mini_exam, got {outcome.kind} (obs after clamp={outcome.observed_level})"

            # 5. Check state shows pending
            state = await H.get_state(token, domain)
            assert state.get("pending") is not None, f"No pending in state: {state}"
            assert state["niveau_status"] == "calibration_en_cours", \
                f"Expected calibration_en_cours, got {state['niveau_status']}"
            result["steps"].append("state_pending_ok")

            # 6. Start mini-exam
            start_resp = await H.start_mini_exam(token, domain)
            target = start_resp["target_level"]
            assert target == outcome.observed_level, \
                f"Target level mismatch: {target} vs {outcome.observed_level}"
            assert len(start_resp["items"]) == 8
            result["steps"].append(f"mini_exam_start(target={target})")

            # 7. Submit scripted answers
            answers = H.answers_for(domain, target, mini_exam_mode)
            submit_resp = await H.submit_mini_exam(token, domain, target, answers)
            result["mini_exam_score_pct"] = submit_resp.get("score_pct")
            result["mini_exam_outcome"] = submit_resp.get("outcome")
            result["steps"].append(
                f"mini_exam_submit({mini_exam_mode},score={submit_resp.get('score_pct')},"
                f"outcome={submit_resp.get('outcome')})")

            if mini_exam_mode == "fail":
                assert submit_resp["outcome"] == "auto_validate", \
                    f"Expected auto_validate on fail, got {submit_resp['outcome']}"
            else:  # pass
                assert submit_resp["outcome"] == "awaiting_user_decision", \
                    f"Expected awaiting_user_decision on pass, got {submit_resp['outcome']}"
                # 8. Decide
                decide_resp = await H.decide(token, domain, decide_choice)
                result["steps"].append(
                    f"decide({decide_choice},final={decide_resp.get('final_level')})")

        # 9. Final DB assertions
        final = await H.fetch_final_state(eleve_id, domain)
        profil = final["profil"]
        assert profil is not None, "No profils_eleves row"
        result["actual_final"] = profil["niveau_global"]
        result["actual_status"] = profil["niveau_status"]
        result["events_count"] = len(final["events"])

        assert profil["niveau_status"] == expected_status, \
            f"Status: {profil['niveau_status']} != {expected_status}"
        assert profil["niveau_global"] == expected_final, \
            f"Final: {profil['niveau_global']} != {expected_final}"
        assert profil["niveau_validated_at"] is not None, "No validated_at"
        assert profil["consolidation_decision_pending"] is None, \
            f"Pending not cleared: {profil['consolidation_decision_pending']}"

        result["passed"] = True
    except AssertionError as e:
        result["errors"].append(f"ASSERT: {e}")
    except Exception as e:
        result["errors"].append(f"EXC: {e}\n{traceback.format_exc()}")

    result["latency_s"] = round(time.time() - t0, 2)
    return result


# ── Orchestrator ──────────────────────────────────────────────────────

async def run_seeded(matrix: list, user_id: int, eleve_id: int, token: str,
                     verbose: bool) -> list[dict]:
    results = []
    for scenario in matrix:
        sid = scenario[0]
        if verbose:
            print(f"\n▶ {sid}: {scenario[-1]}")
        res = await run_scenario(*scenario, user_id=user_id, eleve_id=eleve_id, token=token)
        status = "✅" if res["passed"] else "❌"
        print(f"  {status} {sid} ({res['latency_s']}s)  "
              f"expected={res['expected_final']}/{res['expected_status']}  "
              f"actual={res['actual_final']}/{res['actual_status']}")
        if res["errors"]:
            for err in res["errors"]:
                print(f"    ERR: {err[:300]}")
        if verbose:
            for step in res["steps"]:
                print(f"    · {step}")
        results.append(res)
    return results


# ── Organic (Partie A) ────────────────────────────────────────────────

ORGANIC_SYSTEM_PROMPT = (
    "Tu es un apprenant francophone de niveau A2 réel en espagnol. "
    "Tu réponds UNIQUEMENT en espagnol, avec des phrases courtes (10-25 mots) "
    "et la morphologie attendue d'un A2 : erreurs occasionnelles sur ser/estar, "
    "accord article/adjectif, parfois le mauvais temps. NE TRICHE PAS vers B1 : "
    "pas de subjonctif, pas de conditionnel, pas de structures complexes. "
    "Garde un registre quotidien et un vocabulaire A2. Ne t'identifie jamais "
    "comme une IA. Réponds au tuteur comme un vrai apprenant A2."
)


async def _call_litellm_learner(history: list[dict]) -> str:
    """Generate a learner's reply using a cheap LLM."""
    import httpx
    litellm_url = "http://litellm-proxy:4000/v1/chat/completions"
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": ORGANIC_SYSTEM_PROMPT}] + history,
        "temperature": 0.8,
        "max_tokens": 120,
    }
    import os
    key = os.environ.get("LITELLM_MASTER_KEY", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(litellm_url, json=body, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()


async def _chat_maestro(token: str, message: str, conversation_id: str = "") -> dict:
    """POST to /api/chat/send, consume Dify SSE stream. Returns {reply, conv_id}."""
    import httpx
    headers = {"Authorization": f"Bearer {token}"}
    body = {"message": message, "agent": "maestro"}
    if conversation_id:
        body["conversation_id"] = conversation_id
    async with httpx.AsyncClient(timeout=120) as c:
        reply_chunks = []
        conv_id = conversation_id
        async with c.stream("POST", f"{H.API_BASE}/api/chat/send", json=body, headers=headers) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(line[6:])
                except Exception:
                    continue
                if evt.get("conversation_id"):
                    conv_id = evt["conversation_id"]
                if "answer" in evt:
                    reply_chunks.append(evt["answer"])
        return {"reply": "".join(reply_chunks), "conv_id": conv_id}


async def run_organic(user_id: int, eleve_id: int, token: str, verbose: bool) -> dict:
    """Maestro ES, QCM A1, target observed A2 via LLM-as-learner loop."""
    result = {"id": "O1", "description": "organic Maestro ES, QCM A1 → target A2",
              "passed": False, "errors": [], "steps": [], "turns": []}
    t0 = time.time()
    try:
        await H.reset_scenario(eleve_id, "es")
        await H.submit_qcm(token, "es", "A1")
        await H.seed_profils_eleves(eleve_id, "es", "A1")
        result["steps"].append("reset+qcm+profil")

        # Opening prompt from learner
        history = [{"role": "user", "content": "Hola. Soy un estudiante francés y quiero mejorar mi español."}]
        conv_id = ""
        for i in range(10):
            # Send learner message to Maestro
            msg = history[-1]["content"] if history[-1]["role"] == "user" else None
            if msg is None:
                learner_reply = await _call_litellm_learner(history)
                history.append({"role": "user", "content": learner_reply})
                msg = learner_reply
            resp = await _chat_maestro(token, msg, conv_id)
            conv_id = resp["conv_id"] or conv_id
            reply = resp["reply"][:200]
            history.append({"role": "assistant", "content": resp["reply"][:400]})
            result["turns"].append({"turn": i + 1, "user_msg": msg[:120], "maestro": reply})
            if verbose:
                print(f"  turn {i+1}: user={msg[:60]!r} maestro={reply[:60]!r}")
            # Poll state — trigger fires around turn 8+
            state = await H.get_state(token, "es")
            if state.get("pending"):
                result["steps"].append(f"pending@turn{i+1}: {state['pending']}")
                break
            # Generate next learner message
            learner_reply = await _call_litellm_learner(history)
            history.append({"role": "user", "content": learner_reply})
        else:
            result["errors"].append("No pending after 10 turns")
            return result

        state = await H.get_state(token, "es")
        target = state["pending"].get("mini_exam_target_level") or state["pending"].get("observed")
        # Submit mini-exam with scripted pass answers
        answers = H.answers_for("es", target, "pass")
        submit_resp = await H.submit_mini_exam(token, "es", target, answers)
        result["mini_exam"] = submit_resp
        if submit_resp["outcome"] == "awaiting_user_decision":
            await H.decide(token, "es", "accept_new")
            result["steps"].append("decide(accept_new)")
        final = await H.fetch_final_state(eleve_id, "es")
        result["final"] = final["profil"]
        assert final["profil"]["niveau_status"] == "validé"
        result["passed"] = True
    except Exception as e:
        result["errors"].append(f"EXC: {e}\n{traceback.format_exc()}")
    result["latency_s"] = round(time.time() - t0, 2)
    return result


# ── Main ──────────────────────────────────────────────────────────────

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["seeded", "organic", "both"], default="seeded")
    ap.add_argument("--matrix", default="all", help="'all' or scenario id like S1")
    ap.add_argument("--include-organic", action="store_true")
    ap.add_argument("--keep-user", action="store_true",
                    help="don't teardown test user after run")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args()

    print(f"🧪 E2E consolidation test — {datetime.utcnow().isoformat()}")
    print(f"   API: {H.API_BASE}")

    try:
        # Seed test user
        user_id, eleve_id = await H.ensure_test_user()
        token = H.forge_access_token(user_id, H.TEST_USER_USERNAME)
        print(f"   Test user: id={user_id} eleve_id={eleve_id}")

        # Select matrix
        if args.matrix == "all":
            matrix = MATRIX
        else:
            matrix = [s for s in MATRIX if s[0] == args.matrix]
            if not matrix:
                print(f"No scenario {args.matrix}"); return 1

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "mode": args.mode, "seeded": [], "organic": None,
        }

        if args.mode in ("seeded", "both"):
            print(f"\n━━━ Partie B (seeded, {len(matrix)} scenarios) ━━━")
            report["seeded"] = await run_seeded(matrix, user_id, eleve_id, token, args.verbose)
            passed = sum(1 for r in report["seeded"] if r["passed"])
            print(f"\n   Seeded: {passed}/{len(report['seeded'])} passed")

        if args.mode in ("organic", "both") or args.include_organic:
            print(f"\n━━━ Partie A (organic) ━━━")
            report["organic"] = await run_organic(user_id, eleve_id, token, args.verbose)
            print(f"   Organic: {'✅' if report['organic']['passed'] else '❌'} "
                  f"({report['organic'].get('latency_s', '?')}s)")

        # Archive report
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        out = Path(f"/tmp/consolidation_e2e_{ts}.json")
        out.write_text(json.dumps(report, indent=2, default=str))
        print(f"\n📄 Report: {out}")

        # Exit code
        seeded_pass = all(r["passed"] for r in report["seeded"]) if report["seeded"] else True
        organic_pass = (not report["organic"]) or report["organic"]["passed"]
        return 0 if (seeded_pass and organic_pass) else 1
    finally:
        if not args.keep_user:
            await H.teardown_test_user()
        await H.close_pool()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
