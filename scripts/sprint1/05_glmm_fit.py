"""Hierarchical logistic GLMM for tier calibration (NumPyro NUTS).

Model:
  y_i ~ Bernoulli(sigmoid(β_0 + β_tier[tier_i] + u_learner[i] + v_family[i]))
  T1 held as baseline (β_tier[0] = 0) for identifiability.
  Random effects non-centered.

Input  : glmm_dataset.parquet (29,412 rows)
Output : glmm_posterior.nc (full posterior, arviz InferenceData)
         glmm_summary.json  (β_0, β_tier[T1..T4], σ_u, σ_v + R-hat + ESS)
         trace_plots.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import arviz as az
import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np
import numpyro
import numpyro.distributions as dist
import pandas as pd  # noqa: E402
from numpyro.infer import MCMC, NUTS

PROC = Path("/mnt/cosmos-data/sprint1/data/processed")
RESULTS = Path("/mnt/cosmos-data/sprint1/results")
FIG = RESULTS / "figures"
FIG.mkdir(parents=True, exist_ok=True)

TIERS_ORDERED = ["T1_ignored", "T2_noted", "T3_penalized", "T4_regressive"]


def glmm_model(tier_idx, learner_idx, family_idx, n_learners, n_families, y=None):
    sigma_u = numpyro.sample("sigma_u", dist.HalfNormal(2.0))
    sigma_v = numpyro.sample("sigma_v", dist.HalfNormal(2.0))

    beta_0 = numpyro.sample("beta_0", dist.Normal(0.0, 3.0))
    beta_tier_raw = numpyro.sample("beta_tier_raw", dist.Normal(0.0, 3.0).expand([3]))
    beta_tier = jnp.concatenate([jnp.zeros(1), beta_tier_raw])   # T1 = 0
    numpyro.deterministic("beta_tier", beta_tier)

    u_std = numpyro.sample("u_std", dist.Normal(0.0, 1.0).expand([n_learners]))
    v_std = numpyro.sample("v_std", dist.Normal(0.0, 1.0).expand([n_families]))
    u = u_std * sigma_u
    v = v_std * sigma_v

    logit_p = beta_0 + beta_tier[tier_idx] + u[learner_idx] + v[family_idx]

    with numpyro.plate("obs", len(y)):
        numpyro.sample("y", dist.Bernoulli(logits=logit_p), obs=y)


def main() -> int:
    df = pd.read_parquet(PROC / "glmm_dataset.parquet")

    # Encode categorical indices
    tier_cat = pd.Categorical(df["tier_assigned"], categories=TIERS_ORDERED, ordered=True)
    if tier_cat.isna().any():
        raise ValueError("Unknown tier value; expected T1..T4")
    tier_idx = jnp.array(tier_cat.codes, dtype=jnp.int32)

    learner_cat = pd.Categorical(df["learner_id"])
    family_cat = pd.Categorical(df["academie_family"])
    learner_idx = jnp.array(learner_cat.codes, dtype=jnp.int32)
    family_idx = jnp.array(family_cat.codes, dtype=jnp.int32)
    y = jnp.array(df["y"].values, dtype=jnp.int32)

    n_learners = int(len(learner_cat.categories))
    n_families = int(len(family_cat.categories))
    print(f"Data: {len(y):,} obs, {n_learners:,} learners, {n_families} families")

    nuts = NUTS(glmm_model, target_accept_prob=0.9)
    mcmc = MCMC(
        nuts,
        num_warmup=500,
        num_samples=1000,
        num_chains=2,
        chain_method="parallel",
        progress_bar=True,
    )
    rng_key = jax.random.PRNGKey(42)
    mcmc.run(
        rng_key,
        tier_idx=tier_idx,
        learner_idx=learner_idx,
        family_idx=family_idx,
        n_learners=n_learners,
        n_families=n_families,
        y=y,
    )

    idata = az.from_numpyro(mcmc,
                             coords={"tier": TIERS_ORDERED,
                                     "family": family_cat.categories.tolist()},
                             dims={"beta_tier": ["tier"], "v_std": ["family"]})
    idata.to_netcdf(RESULTS / "glmm_posterior.nc")
    print(f"\nPosterior saved: {RESULTS / 'glmm_posterior.nc'}")

    # Diagnostics — scalar params + beta_tier
    params = ["beta_0", "beta_tier", "sigma_u", "sigma_v"]
    # arviz ≥1.0 uses ci_prob; older versions used hdi_prob — fallback.
    try:
        summary = az.summary(idata, var_names=params, ci_prob=0.95)
    except TypeError:
        summary = az.summary(idata, var_names=params, hdi_prob=0.95)
    print("\n=== Posterior summary ===")
    print(summary)

    # Extract key numbers for JSON
    beta_tier_samples = idata.posterior["beta_tier"].values  # (chains, draws, 4)
    beta_tier_flat = beta_tier_samples.reshape(-1, 4)
    beta_0_flat = idata.posterior["beta_0"].values.reshape(-1)

    results = {
        "model": "hierarchical_logistic_glmm_T1_baseline",
        "n_obs": int(len(y)),
        "n_learners": n_learners,
        "n_families": n_families,
        "n_samples": int(beta_tier_flat.shape[0]),
        "beta_0": {
            "mean": float(beta_0_flat.mean()),
            "hdi_low": float(np.quantile(beta_0_flat, 0.025)),
            "hdi_high": float(np.quantile(beta_0_flat, 0.975)),
        },
        "beta_tier": {
            tier: {
                "mean": float(beta_tier_flat[:, i].mean()),
                "hdi_low": float(np.quantile(beta_tier_flat[:, i], 0.025)),
                "hdi_high": float(np.quantile(beta_tier_flat[:, i], 0.975)),
            }
            for i, tier in enumerate(TIERS_ORDERED)
        },
        "sigma_u_mean": float(idata.posterior["sigma_u"].mean()),
        "sigma_v_mean": float(idata.posterior["sigma_v"].mean()),
        # T1 baseline is fixed at 0 (NaN diagnostics) — exclude from aggregates.
        "r_hat_max": float(pd.to_numeric(summary["r_hat"], errors="coerce").max()),
        "ess_bulk_min": float(pd.to_numeric(summary["ess_bulk"], errors="coerce").min()),
        "n_divergences": int(mcmc.get_extra_fields().get("diverging", jnp.zeros(1)).sum()),
    }
    (RESULTS / "glmm_summary.json").write_text(json.dumps(results, indent=2))
    print(f"\nSummary saved: {RESULTS / 'glmm_summary.json'}")

    # Convergence quick check
    max_rhat = results["r_hat_max"]
    min_ess = results["ess_bulk_min"]
    if max_rhat > 1.01:
        print(f"⚠️ R-hat max = {max_rhat:.3f} > 1.01 — convergence suboptimal")
    else:
        print(f"✅ R-hat max = {max_rhat:.3f}")
    if min_ess < 400:
        print(f"⚠️ ESS bulk min = {min_ess:.0f} < 400 — consider more samples")
    else:
        print(f"✅ ESS bulk min = {min_ess:.0f}")

    # Trace plots
    axes = az.plot_trace(idata, var_names=params, compact=False)
    # plot_trace in arviz 1.x returns a figure-like; save the parent figure
    try:
        fig = axes.ravel()[0].figure if hasattr(axes, "ravel") else axes[0][0].figure
    except Exception:
        fig = plt.gcf()
    fig.suptitle("MCMC trace — Sprint 1.5 GLMM", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "trace_plots.png", dpi=100, bbox_inches="tight")
    plt.close("all")

    # β_tier posterior histogram
    fig, axs = plt.subplots(1, 4, figsize=(14, 3), sharey=True)
    for i, tier in enumerate(TIERS_ORDERED):
        axs[i].hist(beta_tier_flat[:, i], bins=40, color=f"C{i}", alpha=0.85)
        axs[i].set_title(f"{tier}\nmean={results['beta_tier'][tier]['mean']:.2f}")
        axs[i].axvline(results["beta_tier"][tier]["mean"], color="k", lw=1)
        axs[i].set_xlabel("β_tier (log-odds)")
    fig.suptitle("Posterior β_tier — T1=0 baseline (T2/T3/T4 should be negative)")
    fig.tight_layout()
    fig.savefig(FIG / "beta_tier_posterior.png", dpi=100)
    plt.close(fig)

    print("\nFigures saved to:", FIG)
    return 0 if max_rhat <= 1.01 and min_ess >= 400 else 2


if __name__ == "__main__":
    sys.exit(main())
