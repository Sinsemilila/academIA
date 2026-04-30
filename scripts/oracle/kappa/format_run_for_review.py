"""Format an oracle harness run JSON into a human-readable markdown for
manual super-judge review (Opus in-chat or Sinse spot-check).

For each scenario : learner utterance + Teacher response + acceptable_set
+ panel verdict + per-judge votes breakdown.

Usage
-----
    python3 -m scripts.oracle.kappa.format_run_for_review \\
        /tmp/baseline-panel-2026-04-30.json \\
        --out /tmp/panel-review-template.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def _load_scenario_yaml(scenario_id: str, agent: str = "teacher_en") -> dict | None:
    """Load YAML scenario file to enrich review with learner utterance + spec."""
    import yaml
    base = Path("scripts/oracle/scenarios") / agent
    candidate = base / f"{scenario_id}.yaml"
    if not candidate.exists():
        # Try _examples/, etc.
        for alt in base.rglob(f"{scenario_id}.yaml"):
            candidate = alt
            break
    if not candidate.exists():
        return None
    return yaml.safe_load(candidate.read_text())


def _load_golden(scenario_id: str, agent: str = "teacher_en") -> str | None:
    """Load golden response text if recorded."""
    p = Path("scripts/oracle/scenarios") / agent / "golden" / f"{scenario_id}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        return d.get("response") or d.get("text") or ""
    except Exception:
        return None


def _format_per_judge_votes(votes: list[dict]) -> str:
    """Group votes by _judge_model and format compact."""
    by_judge: dict[str, list[dict]] = {}
    for v in votes:
        m = v.get("_judge_model", "?")
        by_judge.setdefault(m, []).append(v)
    out = []
    for judge, jvotes in by_judge.items():
        # Strip _judge_model + reasoning for compactness
        compact = []
        for v in jvotes:
            v2 = {k: vv for k, vv in v.items() if not k.startswith("_") and k != "reasoning"}
            compact.append(v2)
        out.append(f"    - **{judge}** ({len(jvotes)}): {compact}")
    return "\n".join(out) if out else "    (no votes)"


def format_run(run_path: Path, agent: str) -> str:
    run = json.loads(run_path.read_text())
    panel = run.get("panel")
    n_votes = run.get("n_votes")
    judge_model = run.get("judge_model")
    results = run.get("results", [])

    md: list[str] = []
    md.append(f"# Oracle run review — {run.get('agent', agent)} / {run.get('mode')}")
    md.append("")
    md.append(f"- **Panel members** : {panel or '_(single judge: ' + (judge_model or '?') + ')_'}")
    md.append(f"- **n_votes per judge** : {n_votes}")
    md.append(f"- **Total scenarios** : {len(results)}")
    md.append("")
    md.append("> Manual super-judge instructions :")
    md.append("> 1. Read the learner utterance + Teacher response")
    md.append("> 2. For each LLM-judged dim, give your verdict : `pass` / `fail` / `unknown`")
    md.append("> 3. Note discrepancies with panel verdict for κ computation")
    md.append("")
    md.append("---")
    md.append("")

    for r in results:
        sid = r.get("scenario_id")
        scenario = _load_scenario_yaml(sid, agent) or {}
        golden = _load_golden(sid, agent) or "(no golden recorded)"
        learner_turns = [t for t in scenario.get("turns", []) if t.get("role") == "learner"]
        learner_text = learner_turns[-1].get("text", "") if learner_turns else "(unavailable)"
        scenario_key = scenario.get("scenario_key", {})
        cefr = scenario_key.get("cefr", "?")
        tier = scenario_key.get("target_tier", "?")
        err_cat = scenario_key.get("error_category", "?")

        md.append(f"## {sid}")
        md.append("")
        md.append(f"**Context** : {cefr} / {tier} / {err_cat}")
        md.append("")
        md.append(f"**Learner** : `{learner_text}`")
        md.append("")
        teacher_response = r.get("response_text")
        if teacher_response:
            md.append("**Teacher response (Dify, this run)** :")
            md.append("```")
            md.append(teacher_response)
            md.append("```")
        else:
            md.append("_(Teacher response not in run JSON — pre-Phase-2-harness-edit. Using golden as proxy.)_")
        md.append("")
        md.append("**Golden response (reference)** :")
        md.append("```")
        md.append(golden[:800] + ("..." if len(golden) > 800 else ""))
        md.append("```")
        md.append("")

        # Each LLM-judged dim
        for dv in r.get("dims", []):
            dim = dv.get("dim", "?")
            verdict = dv.get("verdict", "?")
            reasoning = dv.get("reasoning", "")
            votes = dv.get("judge_votes", [])
            if not votes:  # deterministic dim, skip
                continue

            md.append(f"### dim: `{dim}`")
            spec = (scenario.get("expected_dimensions") or {}).get(dim, {})
            if spec:
                md.append(f"- **Spec** : `{spec}`")
            md.append(f"- **Panel verdict** : `{verdict}` — {reasoning}")
            md.append(f"- **Per-judge votes** :")
            md.append(_format_per_judge_votes(votes))
            md.append("")
            md.append(f"- [ ] **My verdict (super-judge)** : `pass` / `fail` / `unknown`")
            md.append("- **Notes** : ___")
            md.append("")

        md.append(f"**Overall** : `{r.get('overall', '?')}`")
        md.append("")
        md.append("---")
        md.append("")

    return "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser(description="Format oracle run JSON for manual review")
    ap.add_argument("run_json", type=Path)
    ap.add_argument("--agent", default="teacher_en")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    md = format_run(args.run_json, args.agent)
    if args.out:
        args.out.write_text(md)
        print(f"Review template written to {args.out}", file=sys.stderr)
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
