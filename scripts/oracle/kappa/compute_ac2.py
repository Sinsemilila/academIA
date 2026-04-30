"""Compute Gwet's AC2 from one or more oracle harness run JSON outputs.

Two modes :

1. Inter-run (DEFAULT, ≥2 run files) — compare per-scenario × dim verdicts
   across runs. Measures TRUE reproducibility : if same Teacher response
   gets pass in run 1 and fail in run 2, AC2 captures that disagreement.

2. Intra-run inter-rater (1 run file, --mode intra) — re-derive (n_pass,
   n_fail) from `judge_votes` based on dim semantics (cf_move_set_valid,
   booleans). Less robust than inter-run because vote semantics vary by
   dim. Use as supplementary signal.

Output : JSON with per-dim AC2 + global AC2 + bootstrap 95% CI.

Usage
-----
    # Inter-run (recommended, primary metric)
    python3 -m scripts.oracle.kappa.compute_ac2 \\
        /tmp/run_a.json /tmp/run_b.json /tmp/run_c.json \\
        --out /tmp/ac2_report.json

    # Intra-run (single run, supplementary)
    python3 -m scripts.oracle.kappa.compute_ac2 \\
        /tmp/run.json --mode intra --out /tmp/ac2_intra.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from scripts.oracle.kappa.ac2 import (
    aggregate_global,
    aggregate_per_dim,
)


def _load_run(path: Path) -> dict:
    return json.loads(path.read_text())


def _verdict_to_int(verdict: str) -> int | None:
    """Map oracle verdict to binary. unknown/skip → None (excluded)."""
    if verdict == "pass":
        return 1
    if verdict == "fail":
        return 0
    return None  # unknown / skip → excluded


def collect_inter_run(
    runs: list[dict],
) -> dict[str, list[tuple[int, int]]]:
    """Pivot N runs to (n_pass, n_fail) per (scenario, dim).

    Returns dict {dim_name: [(n_pass, n_fail), ...]} where each tuple is
    one (scenario × dim) item with vote count = N (number of runs that
    produced a pass/fail verdict ; unknown/skip excluded).
    """
    # {(scenario_id, dim): [verdict_int, ...]}
    pivot: dict[tuple[str, str], list[int]] = defaultdict(list)
    for run in runs:
        for r in run.get("results", []):
            sid = r.get("scenario_id") or r.get("id")
            for dv in r.get("dims", []):
                v = _verdict_to_int(dv.get("verdict", ""))
                if v is not None:
                    pivot[(sid, dv["dim"])].append(v)

    by_dim: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for (_sid, dim), verdicts in pivot.items():
        if len(verdicts) < 2:
            continue  # need ≥2 votes per item for AC2
        n_pass = sum(verdicts)
        n_fail = len(verdicts) - n_pass
        by_dim[dim].append((n_pass, n_fail))
    return dict(by_dim)


def collect_intra_run(run: dict) -> dict[str, list[tuple[int, int]]]:
    """Pivot single run to (n_pass, n_fail) using judge_votes per dim.

    This is best-effort : different dims have different vote payloads.
    For binary booleans (`flags_honored`, `is_valid`) → direct count.
    For categorical (move, level) → use the final dim verdict as a proxy
    fallback : count votes whose final aggregation matches verdict.
    """
    by_dim: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for r in run.get("results", []):
        for dv in r.get("dims", []):
            votes = dv.get("judge_votes") or []
            dim = dv["dim"]
            if not votes:
                continue
            # Heuristic : if vote dicts have a single bool key → use it
            n_pass = 0
            n_fail = 0
            for v in votes:
                if isinstance(v, dict):
                    bools = [val for val in v.values() if isinstance(val, bool)]
                    if bools:
                        # majority of bool keys = vote
                        if sum(bools) > len(bools) / 2:
                            n_pass += 1
                        else:
                            n_fail += 1
                        continue
                # Fallback : assume vote agrees with final dim verdict
                if dv.get("verdict") == "pass":
                    n_pass += 1
                elif dv.get("verdict") == "fail":
                    n_fail += 1
            if n_pass + n_fail >= 2:
                by_dim[dim].append((n_pass, n_fail))
    return dict(by_dim)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compute Gwet's AC2 from oracle harness run JSON files."
    )
    ap.add_argument(
        "runs",
        nargs="+",
        type=Path,
        help="Oracle run JSON files (≥2 for inter-run mode)",
    )
    ap.add_argument(
        "--mode",
        choices=["inter", "intra"],
        default="inter",
        help="inter-run reproducibility (default) or intra-run inter-rater",
    )
    ap.add_argument("--out", type=Path, default=None, help="Write JSON report")
    ap.add_argument("--n-boot", type=int, default=1000, help="Bootstrap resamples")
    ap.add_argument("--seed", type=int, default=42, help="Bootstrap seed")
    args = ap.parse_args()

    if args.mode == "inter" and len(args.runs) < 2:
        print("inter mode needs ≥2 run files", file=sys.stderr)
        return 2

    runs = [_load_run(p) for p in args.runs]
    if args.mode == "inter":
        by_dim = collect_inter_run(runs)
    else:
        by_dim = collect_intra_run(runs[0])

    if not by_dim:
        print("no usable verdicts found", file=sys.stderr)
        return 1

    per_dim = aggregate_per_dim(by_dim, n_boot=args.n_boot, seed=args.seed)
    global_res = aggregate_global(by_dim, n_boot=args.n_boot, seed=args.seed)

    report = {
        "mode": args.mode,
        "n_runs": len(args.runs),
        "per_dim": {
            dim: {
                "ac2": round(res.ac2, 4),
                "ci_low": round(res.ci_low, 4),
                "ci_high": round(res.ci_high, 4),
                "n_items": res.n_items,
                "n_raters": res.n_raters,
            }
            for dim, res in per_dim.items()
        },
        "global": {
            "ac2": round(global_res.ac2, 4),
            "ci_low": round(global_res.ci_low, 4),
            "ci_high": round(global_res.ci_high, 4),
            "n_items": global_res.n_items,
            "n_raters": global_res.n_raters,
        },
    }

    output = json.dumps(report, indent=2)
    if args.out:
        args.out.write_text(output)
        print(f"AC2 report written to {args.out}", file=sys.stderr)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
