"""Session 40 Phase C — Noise floor measurement.

Runs the oracle K times on the unchanged prompt and measures per-dim
verdict instability. A dim with high instability is unreliable as a
regression gate regardless of calibration.

Budget-aware : K=2 catches most noise (sufficient to flag dims that
flip verdicts across runs). K=5 per design doc is ideal but costs
~780K tokens ; K=2 ~312K, acceptable one-shot.

Output : updates `scripts/oracle/config.yaml::noise_floor` per dim,
logs per-scenario-per-dim stability to /tmp/oracle_noise_floor.json.

Usage :
  python3 scripts/oracle/noise_floor.py --runs 2 --mode full
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--mode", default="full")
    ap.add_argument("--agent", default="teacher_en")
    args = ap.parse_args()

    print(f"▶ noise floor — agent={args.agent} mode={args.mode} runs={args.runs}")
    runs_data = []
    for i in range(args.runs):
        out = f"/tmp/oracle_nf_run_{i+1}.json"
        print(f"  run {i+1}/{args.runs} → {out}")
        subprocess.run(
            ["python3", str(ROOT / "harness.py"),
             "--agent", args.agent, "--mode", args.mode,
             "--gate-mode", "relaxed", "--out", out],
            check=True,
        )
        runs_data.append(json.loads(Path(out).read_text()))

    # Compute per-(scenario, dim) verdict across runs
    # shape: verdicts[scenario_id][dim] = [verdict_run1, verdict_run2, ...]
    verdicts: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for run in runs_data:
        for res in run["results"]:
            sid = res["scenario_id"]
            for dv in res.get("dims", []):
                verdicts[sid][dv["dim"]].append(dv["verdict"])

    # FPR per dim = fraction of (scenario, dim) cells where verdicts disagree
    dim_totals: dict[str, int] = defaultdict(int)
    dim_disagree: dict[str, int] = defaultdict(int)
    for _sid, dims in verdicts.items():
        for dim, vlist in dims.items():
            if len(vlist) < args.runs:
                continue
            dim_totals[dim] += 1
            if len(set(vlist)) > 1:
                dim_disagree[dim] += 1

    noise_floor = {
        d: round(dim_disagree[d] / max(dim_totals[d], 1), 3)
        for d in dim_totals
    }

    print("\n▶ Noise floor per dim (FPR = fraction scenarios with flip)")
    for d, f in sorted(noise_floor.items()):
        print(f"  {d:<40} {f}  ({dim_disagree[d]}/{dim_totals[d]})")

    # Update config.yaml
    cfg_path = ROOT / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    cfg["noise_floor"] = {**cfg.get("noise_floor", {}), **noise_floor}
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"\n▶ wrote noise_floor to {cfg_path.relative_to(ROOT.parent.parent)}")

    Path("/tmp/oracle_noise_floor.json").write_text(json.dumps({
        "runs": args.runs,
        "verdicts": {k: dict(v) for k, v in verdicts.items()},
        "noise_floor": noise_floor,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
