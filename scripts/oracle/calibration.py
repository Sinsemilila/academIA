"""Session 40 Phase C — Cohen's κ calibration vs Sinse manual scores.

Reads /tmp/oracle_sinse_scores.yaml (template from export_for_manual.py)
and the latest oracle baseline run, computes κ per LLM-judged dim.

Gates :
  - κ ≥ 0.6 → dim production-ready, stays active.
  - κ ∈ [0.4, 0.6) → borderline. ALERT Sinse, do not auto-drop.
  - κ < 0.4 → drop (append to config.yaml::dropped_dims), log reason.

Usage :
  python3 scripts/oracle/calibration.py \
    --manual /tmp/oracle_sinse_scores.yaml \
    --oracle /tmp/oracle_nf_run_1.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

LLM_DIMS = ["cf_move_set_valid", "register_cefr_alignment", "semantic_fidelity_pairwise"]


def _binary(verdict: str) -> int | None:
    if verdict == "pass":
        return 1
    if verdict == "fail":
        return 0
    return None


def cohens_kappa(rater_a: list[int], rater_b: list[int]) -> float:
    """Cohen's κ for binary classification."""
    if not rater_a or len(rater_a) != len(rater_b):
        return 0.0
    n = len(rater_a)
    agree = sum(1 for a, b in zip(rater_a, rater_b, strict=True) if a == b)
    p_o = agree / n
    p_a1 = sum(rater_a) / n
    p_b1 = sum(rater_b) / n
    p_e = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)
    if p_e == 1.0:
        return 1.0
    return round((p_o - p_e) / (1 - p_e), 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manual", required=True)
    ap.add_argument("--oracle", required=True, help="oracle run JSON (baseline)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report κ only, do NOT auto-drop dims in config.yaml "
                         "(use for exploratory calibration e.g. Opus super-judge)")
    args = ap.parse_args()

    manual = yaml.safe_load(Path(args.manual).read_text())["scores"]
    oracle = json.loads(Path(args.oracle).read_text())

    # Build oracle-verdict lookup : {scenario_id: {dim: verdict}}
    oracle_v: dict[str, dict[str, str]] = {}
    for res in oracle["results"]:
        oracle_v[res["scenario_id"]] = {d["dim"]: d["verdict"] for d in res.get("dims", [])}

    per_dim_kappa = {}
    for dim in LLM_DIMS:
        pairs_o, pairs_m = [], []
        for sid, dims in manual.items():
            mv = _binary(dims.get(dim, "unknown"))
            ov = _binary(oracle_v.get(sid, {}).get(dim, "unknown"))
            if mv is None or ov is None:
                continue
            pairs_o.append(ov)
            pairs_m.append(mv)
        kappa = cohens_kappa(pairs_o, pairs_m)
        per_dim_kappa[dim] = {"kappa": kappa, "n_pairs": len(pairs_o)}

    print("▶ Cohen's κ per LLM-judged dim\n")
    decisions = []
    for dim, stats in per_dim_kappa.items():
        kappa = stats["kappa"]
        n = stats["n_pairs"]
        if kappa >= 0.6:
            decision = "KEEP"
        elif kappa >= 0.4:
            decision = "BORDERLINE — alert Sinse"
        else:
            decision = "DROP"
        print(f"  {dim:<35} κ={kappa:>5}  (n={n})  → {decision}")
        decisions.append((dim, kappa, decision))

    # Update config.yaml::dropped_dims if any DROP (skip in dry-run)
    to_drop = [d for d, k, dec in decisions if dec == "DROP"]
    if to_drop and not args.dry_run:
        cfg_path = ROOT / "config.yaml"
        cfg = yaml.safe_load(cfg_path.read_text())
        cfg["dropped_dims"] = list(set((cfg.get("dropped_dims") or []) + to_drop))
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        print(f"\n▶ Dropped dims appended to config: {to_drop}")
    elif to_drop:
        print(f"\n▶ Would drop (dry-run, config NOT modified): {to_drop}")

    Path("/tmp/oracle_calibration.json").write_text(json.dumps(per_dim_kappa, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
