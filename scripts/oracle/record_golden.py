"""Session 40/41 — record golden responses from Dify per scenario, agent-agnostic.

For every scenario in scripts/oracle/scenarios/{agent}/*.yaml, call the
Dify public API with the first learner turn, store response + metadata
as scenarios/{agent}/golden/{id}.json.

This is the frozen-SHA snapshot. Regenerating = explicit `doctrine_change`
commit (design doc §12).

Usage :
  python3 scripts/oracle/record_golden.py --agent teacher_en          # dry-run
  python3 scripts/oracle/record_golden.py --agent maestro_es --apply
  python3 scripts/oracle/record_golden.py --agent teacher_en --only <id_substring>
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
from oracle.judges.dify_client import call_agent, _agent_config, _cfg  # noqa: E402
from oracle.schemas import GoldenFile, ScenarioSchema  # noqa: E402

ROOT = Path(__file__).resolve().parent


def _current_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd="/opt/academie",
            capture_output=True, text=True, check=True,
        ).stdout.strip()[:12]
    except Exception:
        return "unknown"


def record_one(client: httpx.Client, agent: str, key: str, scenario: ScenarioSchema, sha: str) -> GoldenFile | None:
    first_learner = next((t for t in scenario.turns if t.role == "learner"), None)
    if not first_learner:
        return None
    cfg = _cfg()
    url = cfg["dify"]["public_api_base"] + cfg["dify"].get("public_api_path", "/v1/chat-messages")
    try:
        r = client.post(url, json={
            "query": first_learner.text, "inputs": {},
            "user": f"oracle-{scenario.id}", "response_mode": "blocking",
            "conversation_id": "",
        }, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
           timeout=90)
        r.raise_for_status()
        resp = r.json()
    except Exception as e:
        print(f"  ERROR {scenario.id}: {e}", file=sys.stderr)
        return None
    return GoldenFile(
        scenario_id=scenario.id,
        sha=sha,
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        response=(resp.get("answer") or "").strip(),
        dify_conversation_id=resp.get("conversation_id"),
        dify_message_id=resp.get("message_id"),
        usage=(resp.get("metadata") or {}).get("usage"),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="teacher_en")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="substring match on scenario id")
    args = ap.parse_args()

    ac = _agent_config(args.agent)
    key = os.environ.get(ac["env_key_name"], "")
    if not key:
        print(f"ERROR: {ac['env_key_name']} not in env", file=sys.stderr)
        return 2

    scenarios_dir = ROOT / "scenarios" / args.agent
    golden_dir = scenarios_dir / "golden"
    sha = _current_sha()
    scenarios = []
    for f in sorted(scenarios_dir.glob("*.yaml")):
        raw = yaml.safe_load(f.read_text())
        sc = ScenarioSchema.model_validate(raw)
        if args.only and args.only not in sc.id:
            continue
        scenarios.append(sc)

    print(f"▶ {len(scenarios)} scenarios to record (agent={args.agent} sha={sha})")
    if not args.apply:
        print("▶ DRY-RUN. Re-run with --apply to call Dify + save goldens.")
        return 0

    golden_dir.mkdir(parents=True, exist_ok=True)
    ok = 0
    with httpx.Client() as client:
        for i, sc in enumerate(scenarios, 1):
            print(f"  [{i}/{len(scenarios)}] {sc.id}…", flush=True)
            golden = record_one(client, args.agent, key, sc, sha)
            if not golden:
                continue
            out = golden_dir / f"{sc.id}.json"
            out.write_text(json.dumps(golden.model_dump(), indent=2, ensure_ascii=False))
            ok += 1
            time.sleep(0.5)
    print(f"▶ recorded {ok}/{len(scenarios)} goldens → {golden_dir.relative_to(ROOT.parent.parent)}")
    return 0 if ok == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
