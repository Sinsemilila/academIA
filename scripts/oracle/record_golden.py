"""Session 40 Phase B2 — record golden responses from Dify for each scenario.

For every scenario in scripts/oracle/scenarios/teacher_en/*.yaml, call the
current Dify Teacher EN app with the first learner turn as `query`, and
store the response + metadata as scenarios/teacher_en/golden/{id}.json.

This is the frozen-SHA snapshot. Future oracle runs compare against these
goldens to detect regression.

Commit the goldens. Regenerating = explicit `doctrine_change` commit
(see corpus-oracle-v1-design.md §12 Corpus drift management).

Usage :
  python3 scripts/oracle/record_golden.py         # dry-run
  python3 scripts/oracle/record_golden.py --apply # actually call API + save

Env required : DIFY_KEY_TEACHER (read from webapp/.env at invocation time).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oracle.schemas import GoldenFile, ScenarioSchema  # noqa: E402

ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "scenarios" / "teacher_en"
GOLDEN_DIR = SCENARIOS_DIR / "golden"

DIFY_URL = "http://127.0.0.1:5001/v1/chat-messages"


def _current_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd="/opt/academie",
            capture_output=True, text=True, check=True,
        ).stdout.strip()[:12]
    except Exception:
        return "unknown"


def call_dify(client: httpx.Client, key: str, query: str, conv_seed: str) -> dict:
    r = client.post(
        DIFY_URL,
        json={
            "query": query,
            "inputs": {},
            "user": f"oracle-{conv_seed}",
            "response_mode": "blocking",
            "conversation_id": "",
        },
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def record_one(client: httpx.Client, key: str, scenario: ScenarioSchema, sha: str) -> GoldenFile | None:
    first_learner = next((t for t in scenario.turns if t.role == "learner"), None)
    if not first_learner:
        return None
    try:
        resp = call_dify(client, key, first_learner.text, scenario.id)
    except Exception as e:
        print(f"  ERROR {scenario.id}: {e}", file=sys.stderr)
        return None
    answer = resp.get("answer", "").strip()
    return GoldenFile(
        scenario_id=scenario.id,
        sha=sha,
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        response=answer,
        dify_conversation_id=resp.get("conversation_id"),
        dify_message_id=resp.get("message_id"),
        usage=(resp.get("metadata") or {}).get("usage"),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="substring match on scenario id")
    args = ap.parse_args()

    key = os.environ.get("DIFY_KEY_TEACHER", "")
    if not key:
        print("ERROR: DIFY_KEY_TEACHER not in env", file=sys.stderr)
        return 2

    sha = _current_sha()
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.yaml")):
        raw = yaml.safe_load(f.read_text())
        sc = ScenarioSchema.model_validate(raw)
        if args.only and args.only not in sc.id:
            continue
        scenarios.append(sc)

    print(f"▶ {len(scenarios)} scenarios to record (sha={sha})")
    if not args.apply:
        print("▶ DRY-RUN. Re-run with --apply to call Dify + save goldens.")
        return 0

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    ok = 0
    with httpx.Client() as client:
        for i, sc in enumerate(scenarios, 1):
            print(f"  [{i}/{len(scenarios)}] {sc.id}…", flush=True)
            golden = record_one(client, key, sc, sha)
            if not golden:
                continue
            out = GOLDEN_DIR / f"{sc.id}.json"
            out.write_text(json.dumps(golden.model_dump(), indent=2, ensure_ascii=False))
            ok += 1
            time.sleep(0.5)  # be nice to Dify
    print(f"▶ recorded {ok}/{len(scenarios)} goldens → {GOLDEN_DIR.relative_to(ROOT.parent.parent)}")
    return 0 if ok == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
