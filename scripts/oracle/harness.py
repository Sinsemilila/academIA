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
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # scripts/ on path

from oracle.lint import run_lint  # noqa: E402
from oracle.schemas import ScenarioResult, ScenarioSchema  # noqa: E402

_log = logging.getLogger("oracle.harness")

ROOT = Path(__file__).resolve().parent


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def _persist_run_to_db(agent: str, mode: str, results: list) -> None:
    """Session 42 O2 — INSERT one row per (scenario, dim) into oracle_run_log.

    Groups rows by a run_hash = sha1(agent + mode + started_at iso). Lint
    rows use dim='lint_<check>' for per-check granularity. Swallow errors
    in caller ; this function may raise on connection issues.
    """
    import hashlib
    import subprocess
    from datetime import datetime

    started_at = datetime.now(UTC).isoformat()
    run_hash = hashlib.sha1(f"{agent}|{mode}|{started_at}".encode()).hexdigest()[:16]

    # Git SHA at run time (best-effort)
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd="/opt/academia",
            capture_output=True, text=True, check=True,
        ).stdout.strip()[:12]
    except Exception:
        sha = ""

    # Build multi-row INSERT
    rows: list[tuple] = []
    for r in results:
        scenario_id = r.scenario_id
        # Lint rows (structural check verdicts)
        for lr in r.lint:
            verdict = "pass" if lr.passed else "fail"
            rows.append((run_hash, started_at, agent, mode, scenario_id,
                         f"lint_{lr.check}", verdict, None, None, lr.detail or "", sha))
        # LLM dim rows
        for dv in r.dims:
            votes_json = json.dumps(dv.judge_votes) if dv.judge_votes else None
            rows.append((run_hash, started_at, agent, mode, scenario_id,
                         dv.dim, dv.verdict, dv.score, votes_json, dv.reasoning or "", sha))

    if not rows:
        return

    # psycopg lazy import (harness lint mode doesn't need DB)
    try:
        import psycopg2
    except Exception:
        # psycopg2 not installed — skip persistence silently in minimal envs
        return

    dsn = os.environ.get("DATABASE_URL", "").replace("postgres-academie", "127.0.0.1")
    if not dsn:
        return
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO oracle_run_log
                  (run_hash, started_at, agent, mode, scenario_id, dim,
                   verdict, score, judge_votes, reasoning, sha)
                VALUES (%s, %s::timestamptz, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                """,
                rows,
            )
    _log.info("oracle_run_log : inserted %d rows (run_hash=%s)", len(rows), run_hash)


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
    first learner turn. Returns None if --mode lint (lint uses golden only).

    Session 42 O1 : passes `scenario` to call_agent → injects learner profile
    inputs → Dify routes to llm_session (same path as record_golden.py), NOT
    llm_onboarding. Without this, noise floor measurement picks up
    onboarding-flow bot replies while goldens are session-flow replies —
    call-path mismatch that produces artifactual noise on every dim."""
    from oracle.judges.dify_client import call_agent
    first_learner = next((t for t in scenario.turns if t.role == "learner"), None)
    if not first_learner:
        return None
    return call_agent(agent, first_learner.text, scenario.id, scenario=scenario)


def score_scenario(
    scenario: ScenarioSchema, agent: str, mode: Literal["lint", "smoke", "full"], cfg: dict,
    panel_models: list[str] | None = None,
) -> ScenarioResult:
    """Single-scenario scoring. Lint always runs ; LLM dims only in smoke/full."""
    result = ScenarioResult(scenario_id=scenario.id, mode=mode)
    response: str | None = None

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

    # Phase 2 Sprint Oracle EN cohérence — persist response for super-judge review
    # via format_run_for_review.py. ScenarioResult is _Lax so extra fields ok.
    result.response_text = response

    result.lint = run_lint(scenario, response)

    # Stub — Phase B1 fills with real dim scoring
    from oracle.judges import deterministic, llm_pairwise
    golden = load_golden(scenario, agent) or ""
    result.dims = (
        deterministic.score_all(scenario, response)
        + llm_pairwise.score_all(
            scenario, response, golden, cfg,
            n=cfg["modes"][mode]["n_votes"],
            panel_models=panel_models,
        )
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
    ap.add_argument("--panel", choices=["off", "cross-provider"], default="off",
                    help="off = single judge (default) ; cross-provider = "
                         "multi-judge panel from config.yaml panel.members")
    ap.add_argument("--cache", choices=["on", "off"], default=None,
                    help="override cfg.cache.enabled (default config.yaml value). "
                         "on = enable verdict cache hash-indexed by content. "
                         "off = bypass for noise floor / fault injection runs.")
    ap.add_argument("--out", default="/tmp/oracle_run.json")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    cfg = load_config()
    scenarios = discover_scenarios(args.agent, args.mode, cfg)
    if not scenarios:
        print(f"no scenarios found for {args.agent}", file=sys.stderr)
        return 0 if args.gate_mode == "relaxed" else 1

    # Phase 6 — cache override via CLI flag
    if args.cache is not None:
        cfg.setdefault("cache", {})["enabled"] = (args.cache == "on")

    panel_models: list[str] | None = None
    if args.panel == "cross-provider":
        panel_cfg = cfg.get("panel") or {}
        members = panel_cfg.get("members") or []
        if not members:
            print("--panel cross-provider but config.panel.members empty",
                  file=sys.stderr)
            return 2
        panel_models = list(members)

    print(f"▶ Oracle {args.mode} — {args.agent} — {len(scenarios)} scenarios"
          f"{' [panel: ' + ','.join(panel_models) + ']' if panel_models else ''}",
          flush=True)
    results = []
    for s in scenarios:
        results.append(score_scenario(s, args.agent, args.mode, cfg, panel_models))

    # Write JSON (full structured output)
    out_path = Path(args.out)
    out_path.write_text(json.dumps(
        {"mode": args.mode, "agent": args.agent,
         "panel": panel_models,
         "judge_model": cfg["judge"]["model"] if not panel_models else None,
         "n_votes": cfg["modes"][args.mode].get("n_votes"),
         "results": [r.model_dump() for r in results]},
        indent=2,
    ))

    # Session 42 O2 — persist run to oracle_run_log sidecar for dashboard trends.
    # Best-effort : any DB error is logged and swallowed so the harness itself
    # never fails because of telemetry.
    try:
        _persist_run_to_db(args.agent, args.mode, results)
    except Exception as e:
        _log.warning("oracle_run_log persist failed (non-fatal): %s", e)

    # Markdown report + stdout
    report = render_report(results, args.mode, args.agent)
    print(report)
    print(f"\nJSON : {out_path}")

    failed = sum(1 for r in results if r.overall == "fail")
    return 0 if (failed == 0 or args.gate_mode == "relaxed") else 1


if __name__ == "__main__":
    sys.exit(main())
