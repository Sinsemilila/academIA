"""Derive tolerance_matrix weights from GLMM posterior.

Mapping strategy (retained) — "relative to T1 baseline" :

    p_tier = sigmoid(beta_0 + beta_tier[t])        # probability of an error at tier t
    weight[t] = 1 - (p_tier[t] / p_tier[T1])        # 0 at T1, grows toward 1 as tier becomes rarer

Rationale: preserves the product semantic "T1 errors are endemic at this level
→ free pass (weight 0)" while using β_tier to scale T2/T3/T4 empirically.

Also writes the alternative "absolute sigmoid" mapping for reference:

    weight_abs[t] = 1 - p_tier[t]

Input  : /mnt/cosmos-data/sprint1/results/glmm_posterior.nc
Output : /mnt/cosmos-data/sprint1/results/weights_from_posterior.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import arviz as az
import numpy as np

RESULTS = Path("/mnt/cosmos-data/sprint1/results")
TIERS = ["T1_ignored", "T2_noted", "T3_penalized", "T4_regressive"]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def main() -> int:
    idata = az.from_netcdf(RESULTS / "glmm_posterior.nc")
    beta_0 = idata.posterior["beta_0"].values.reshape(-1)            # (n_samples,)
    beta_tier = idata.posterior["beta_tier"].values.reshape(-1, 4)   # (n_samples, 4)

    # p_tier per sample, shape (n_samples, 4)
    p_tier = sigmoid(beta_0[:, None] + beta_tier)

    # Primary mapping: relative to T1
    # weight = 1 - p[t]/p[T1]  (T1 normalized to weight 0)
    p_T1 = p_tier[:, 0]
    rel = p_tier / p_T1[:, None]
    w_rel = np.clip(1.0 - rel, 0.0, 1.0)        # (n_samples, 4)

    # Absolute mapping: weight = 1 - p
    w_abs = np.clip(1.0 - p_tier, 0.0, 1.0)

    # Posterior stats
    def _stats(arr: np.ndarray) -> dict:
        return {
            "mean": [float(v) for v in arr.mean(axis=0)],
            "hdi_low": [float(v) for v in np.quantile(arr, 0.025, axis=0)],
            "hdi_high": [float(v) for v in np.quantile(arr, 0.975, axis=0)],
        }

    weights_relative = _stats(w_rel)
    weights_absolute = _stats(w_abs)
    p_tier_stats = _stats(p_tier)

    # Monotonicity check on posterior means
    w_rel_mean = weights_relative["mean"]
    monotone_rel = all(w_rel_mean[i] <= w_rel_mean[i + 1] for i in range(3))
    monotone_abs = all(weights_absolute["mean"][i] <= weights_absolute["mean"][i + 1] for i in range(3))

    out = {
        "tiers": TIERS,
        "p_error_per_tier": p_tier_stats,
        "weights_relative_to_T1": weights_relative,
        "weights_absolute_sigmoid": weights_absolute,
        "monotone_relative": bool(monotone_rel),
        "monotone_absolute": bool(monotone_abs),
        "chosen_for_v2_draft": "weights_relative_to_T1",
        "recommended_values": {
            "ignored": round(weights_relative["mean"][0], 3),
            "noted": round(weights_relative["mean"][1], 3),
            "penalized": round(weights_relative["mean"][2], 3),
            "regressive": round(weights_relative["mean"][3], 3),
            "shadow": 0.0,
        },
    }

    (RESULTS / "weights_from_posterior.json").write_text(json.dumps(out, indent=2))
    print(f"weights_from_posterior.json saved.\n")

    def _row(label, vals, ci_lo, ci_hi):
        lo_str = [f"{v:+.3f}" for v in ci_lo]
        hi_str = [f"{v:+.3f}" for v in ci_hi]
        return f"  {label:20s}  " + "   ".join(
            f"{v:+.3f} [{lo_str[i]}, {hi_str[i]}]" for i, v in enumerate(vals)
        )

    print("Tier order:", "   ".join(f"{t:17s}" for t in TIERS))
    print(_row("p(error|tier)",
               p_tier_stats["mean"],
               p_tier_stats["hdi_low"], p_tier_stats["hdi_high"]))
    print(_row("weight_relative_T1",
               weights_relative["mean"],
               weights_relative["hdi_low"], weights_relative["hdi_high"]))
    print(_row("weight_absolute",
               weights_absolute["mean"],
               weights_absolute["hdi_low"], weights_absolute["hdi_high"]))
    print()
    print(f"Monotone T1→T4 (relative)  : {monotone_rel}")
    print(f"Monotone T1→T4 (absolute)  : {monotone_abs}")
    print()
    print("=> For v2_draft.yaml (retained mapping = relative):")
    for k, v in out["recommended_values"].items():
        print(f"     {k}: {v}")
    return 0 if monotone_rel else 2


if __name__ == "__main__":
    sys.exit(main())
