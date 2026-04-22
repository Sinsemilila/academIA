"""Session 40 Phase A — Oracle V1 harness (skeleton).

Entry point. Loads scenarios, runs lint layer, stubs LLM-judged dims
(filled in Phase B). Output : JSON + markdown report.

Usage :
  python3 scripts/oracle/harness.py --agent teacher_en --mode lint
  python3 scripts/oracle/harness.py --agent teacher_en --mode smoke
  python3 scripts/oracle/harness.py --agent teacher_en --mode full
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/ on path

from oracle.lint import run_lint  # noqa: E402
from oracle.schemas import ScenarioResult, ScenarioSchema  # noqa: E402

_log = logging.getLogger("oracle.harness")

ROOT = Path(__file__).resolve().parent


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def discover_scenarios(agent: str, mode: str, cfg: dict) -> list[ScenarioSchema]:
    """Scan scripts/oracle/scenarios/{agent}/*.yaml → ScenarioSchema list.
    Excludes _examples/ subdir (reference only). Applies mode-specific count."""
    base = ROOT / "scenarios" / agent
    if not base.exists():
        return []
    files = sorted([p for p in base.glob("*.yaml") if not p.parent.name == "_examples"])
    scenarios = []
    for f in files:
        try:
            raw = yaml.safe_load(f.read_text())
            scenarios.append(ScenarioSchema.model_validate(raw))
        except Exception as e:
            _log.warning("skipping %s: %s", f.name, e)
    if mode == "smoke":
        scenarios = scenarios[: cfg["modes"]["smoke"]["scenario_count"]]
    return scenarios


def load_golden(scenario: ScenarioSchema, agent: str) -> str | None:
    """Load golden response if already recorded. None = not yet recorded."""
    if scenario.golden and scenario.golden.response:
        return scenario.golden.response
    golden_path = ROOT / "scenarios" / agent / "golden" / f"{scenario.id}.json"
    if not golden_path.exists():
        return None
    try:
        data = json.loads(golden_path.read_text())
        return data.get("response")
    except Exception as e:
        _log.warning("golden load failed for %s: %s", scenario.id, e)
        return None


def fetch_current_response(scenario: ScenarioSchema, agent: str) -> str | None:
    """Call Dify public API to get the current bot response for this scenario's
    first learner turn. Returns None if --mode lint (lint uses golden only)."""
    # Phase B2 fills this. For Phase A skeleton, stub with a placeholder.
    # Deferred import so lint mode doesn't require httpx.
    from oracle.judges.dify_client import call_teacher_en  # type: ignore
    first_learner = next((t for t in scenario.turns if t.role == "learner"), None)
    if not first_learner:
        return None
    return call_teacher_en(first_learner.text, scenario.id)


def score_scenario(scenario: ScenarioSchema, agent: str, mode: str, cfg: dict) -> ScenarioResult:
    """Single-scenario scoring. Lint always runs ; LLM dims only in smoke/full."""
    result = ScenarioResult(scenario_id=scenario.id, mode=mode)

    # For lint mode on a scenario that has a golden recorded, use golden
    # as the "response under test" (it validates that the recorded golden
    # itself is structurally sound).
    if mode == "lint":
        response = load_golden(scenario, agent) or ""
        if not response:
            _log.info("lint skip: no golden yet for %s", scenario.id)
            result.overall = "skip"
            return result
        result.lint = run_lint(scenario, response)
        result.overall = "pass" if all(r.passed for r in result.lint) else "fail"
        return result

    # smoke / full : fetch live bot response + score all dims
    try:
        response = fetch_current_response(scenario, agent)
    except Exception as e:
        _log.warning("fetch failed for %s: %s", scenario.id, e)
        result.overall = "skip"
        return result

    if not response:
        result.overall = "skip"
        return result

    result.lint = run_lint(scenario, response)

    # Stub — Phase B1 fills with real dim scoring
    from oracle.judges import deterministic, llm_pairwise  # type: ignore
    golden = load_golden(scenario, agent) or ""
    result.dims = (
        deterministic.score_all(scenario, response)
        + llm_pairwise.score_all(scenario, response, golden, cfg, n=cfg["modes"][mode]["n_votes"])
    )

    # Aggregate : fail if any lint fails OR any dim is fail
    lint_ok = all(r.passed for r in result.lint)
    dims_ok = all(d.verdict != "fail" for d in result.dims)
    result.overall = "pass" if (lint_ok and dims_ok) else "fail"
    return result


def render_report(results: list[ScenarioResult], mode: str, agent: str) -> str:
    passed = sum(1 for r in results if r.overall == "pass")
    failed = sum(1 for r in results if r.overall == "fail")
    skipped = sum(1 for r in results if r.overall == "skip")
    lines = [
        f"# Oracle V1 run — {agent} — mode={mode}",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        f"**Scorecard** : {passed} passed / {failed} failed / {skipped} skipped / {len(results)} total",
        "",
    ]
    for r in results:
        icon = {"pass": "✅", "fail": "❌", "skip": "⏭️"}.get(r.overall, "?")
        lines.append(f"- {icon} **{r.scenario_id}**")
        for lr in r.lint:
            if not lr.passed:
                lines.append(f"    - lint `{lr.check}` : {lr.detail}")
        for dv in r.dims:
            if dv.verdict == "fail":
                lines.append(f"    - dim `{dv.dim}` : {dv.reasoning[:120]}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="teacher_en")
    ap.add_argument("--mode", choices=["lint", "smoke", "full"], default="lint")
    ap.add_argument("--gate-mode", choices=["strict", "relaxed"], default="strict",
                    help="strict = exit 1 on any fail ; relaxed = always exit 0 (warn only)")
    ap.add_argument("--out", default="/tmp/oracle_run.json")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    cfg = load_config()
    scenarios = discover_scenarios(args.agent, args.mode, cfg)
    if not scenarios:
        print(f"no scenarios found for {args.agent}", file=sys.stderr)
        return 0 if args.gate_mode == "relaxed" else 1

    print(f"▶ Oracle {args.mode} — {args.agent} — {len(scenarios)} scenarios", flush=True)
    results = []
    for s in scenarios:
        results.append(score_scenario(s, args.agent, args.mode, cfg))

    # Write JSON (full structured output)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(
        {"mode": args.mode, "agent": args.agent,
         "results": [r.model_dump() for r in results]},
        indent=2,
    ))

    # Markdown report + stdout
    report = render_report(results, args.mode, args.agent)
    print(report)
    print(f"\nJSON : {out_path}")

    failed = sum(1 for r in results if r.overall == "fail")
    return 0 if (failed == 0 or args.gate_mode == "relaxed") else 1


if __name__ == "__main__":
    sys.exit(main())
