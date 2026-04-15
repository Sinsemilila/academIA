"""EDA: per-family × per-level statistics + tier definition empirique.

Computes for each (family, cefr_level):
  - incidence  : total errors / 1000 tokens across learners at that level
  - reach      : proportion of learners at that level with ≥1 error in this family
  - n_learners : denominator (learners at that level)

Then applies the percentile rules from docs/01-pedagogy/error-gradation.md § Étape 2:
  reach ≥ 0.70  → T1 ignored     (error is normal at this level)
  0.30-0.70     → T2 noted
  0.10-0.30     → T3 penalized
  reach < 0.10  → T4 regressive   (aberrant — should be flagged)

Outputs:
  /mnt/cosmos-data/sprint1/data/processed/tier_assignments_external.parquet
  /mnt/cosmos-data/sprint1/results/figures/*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

DATA = Path("/mnt/cosmos-data/sprint1/data/processed")
FIG = Path("/mnt/cosmos-data/sprint1/results/figures")
FIG.mkdir(parents=True, exist_ok=True)

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
# N = native English — used as ceiling reference but not a learner CEFR level


def reach_to_tier(reach: float) -> str:
    if reach >= 0.70:
        return "T1_ignored"
    if reach >= 0.30:
        return "T2_noted"
    if reach >= 0.10:
        return "T3_penalized"
    return "T4_regressive"


def main() -> int:
    err = pd.read_parquet(DATA / "errors_long.parquet")
    learners = pd.read_parquet(DATA / "learners.parquet")

    # Keep only mapped errors for family-level analysis
    err_m = err[err["status"] == "mapped"].copy()
    err_m = err_m[err_m["cefr_level"].isin(LEVELS)]

    # Denominator per level: distinct learners who PRODUCED at least one essay at that level.
    # We read this from err_m directly (covers multi-level authors), falling back to
    # learners.parquet modal level for coverage completeness.
    learners_per_level = (
        err_m.groupby("cefr_level")["learner_id"].nunique()
    )
    # Include learners from learners.parquet whose modal matches but who had 0 mapped errors
    for lvl in LEVELS:
        lvl_count_modal = (learners["cefr_level_modal"] == lvl).sum()
        learners_per_level[lvl] = max(
            int(learners_per_level.get(lvl, 0)),
            int(lvl_count_modal),
        )

    # For each (family, level), count distinct learners with at least one error
    learner_x_family = (
        err_m.groupby(["academie_family", "cefr_level"])["learner_id"]
        .nunique()
        .reset_index(name="n_learners_with_error")
    )

    stats_rows = []
    for family, level in [
        (f, l) for f in err_m["academie_family"].unique() for l in LEVELS
    ]:
        rec = learner_x_family[
            (learner_x_family["academie_family"] == family)
            & (learner_x_family["cefr_level"] == level)
        ]
        n_with = int(rec["n_learners_with_error"].iloc[0]) if len(rec) else 0
        n_total = int(learners_per_level.get(level, 0))
        reach = n_with / n_total if n_total else 0.0

        # Incidence: total errors this family at this level / total tokens (learner-level sum)
        family_errors = err_m[
            (err_m["academie_family"] == family)
            & (err_m["cefr_level"] == level)
        ].shape[0]
        total_tokens_level = learners[
            learners["cefr_level_modal"] == level
        ]["n_tokens"].sum()
        incidence_per_1k = (
            1000.0 * family_errors / total_tokens_level if total_tokens_level else 0.0
        )

        stats_rows.append({
            "academie_family": family,
            "cefr_level": level,
            "n_learners_total": n_total,
            "n_learners_with_error": n_with,
            "reach": reach,
            "n_errors_total": family_errors,
            "incidence_per_1k_tokens": incidence_per_1k,
            "tier_empirical": reach_to_tier(reach),
        })

    df_tier = pd.DataFrame(stats_rows)
    df_tier.to_parquet(DATA / "tier_assignments_external.parquet", index=False, compression="zstd")
    print("tier_assignments_external.parquet saved.\n")
    print(df_tier.pivot(index="academie_family", columns="cefr_level", values="tier_empirical"))
    print()

    # Bootstrap CI on reach (for uncertainty reporting in Sprint 1 report)
    rng = np.random.default_rng(42)
    boot_ci = []
    for _, row in df_tier.iterrows():
        fam, lvl, n_with, n_total = (
            row["academie_family"], row["cefr_level"],
            row["n_learners_with_error"], row["n_learners_total"],
        )
        if n_total == 0:
            boot_ci.append((np.nan, np.nan))
            continue
        draws = rng.binomial(n_total, n_with / max(n_total, 1), size=1000) / n_total
        boot_ci.append((np.quantile(draws, 0.025), np.quantile(draws, 0.975)))
    df_tier["reach_ci_lo"], df_tier["reach_ci_hi"] = zip(*boot_ci)
    df_tier.to_parquet(DATA / "tier_assignments_external.parquet", index=False, compression="zstd")

    # === Figures ===
    sns.set_theme(style="whitegrid")

    # 1. Reach heatmap
    pivot_reach = df_tier.pivot(index="academie_family", columns="cefr_level", values="reach")
    pivot_reach = pivot_reach[LEVELS]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot_reach, annot=True, fmt=".2f", cmap="RdYlGn_r",
                vmin=0, vmax=1, ax=ax, cbar_kws={"label": "Reach (proportion of learners)"})
    ax.set_title("Reach per family × CEFR level — W&I + LOCNESS (Sprint 1)")
    ax.set_xlabel("CEFR level")
    ax.set_ylabel("AcademIA family")
    fig.tight_layout()
    fig.savefig(FIG / "reach_heatmap.png", dpi=100)
    plt.close(fig)

    # 2. Incidence heatmap
    pivot_inc = df_tier.pivot(index="academie_family", columns="cefr_level", values="incidence_per_1k_tokens")
    pivot_inc = pivot_inc[LEVELS]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(pivot_inc, annot=True, fmt=".1f", cmap="rocket_r", ax=ax,
                cbar_kws={"label": "Errors / 1000 tokens"})
    ax.set_title("Error incidence per family × level — W&I + LOCNESS")
    fig.tight_layout()
    fig.savefig(FIG / "incidence_heatmap.png", dpi=100)
    plt.close(fig)

    # 3. Tier map (categorical)
    tier_order = ["T1_ignored", "T2_noted", "T3_penalized", "T4_regressive"]
    tier_colors = {"T1_ignored": 0, "T2_noted": 1, "T3_penalized": 2, "T4_regressive": 3}
    pivot_tier = df_tier.pivot(index="academie_family", columns="cefr_level", values="tier_empirical")
    pivot_tier = pivot_tier[LEVELS]
    pivot_tier_num = pivot_tier.replace(tier_colors).astype(float)
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = sns.color_palette(["#2ecc71", "#f39c12", "#e74c3c", "#8e44ad"])
    sns.heatmap(pivot_tier_num, annot=pivot_tier, fmt="", cmap=cmap, vmin=0, vmax=3,
                ax=ax, cbar_kws={"label": "Tier empirical",
                                  "ticks": [0.4, 1.2, 2.0, 2.8]})
    cbar = ax.collections[0].colorbar
    cbar.set_ticklabels(tier_order)
    ax.set_title("Empirical tier assignment (reach-based) — W&I + LOCNESS")
    fig.tight_layout()
    fig.savefig(FIG / "tier_map.png", dpi=100)
    plt.close(fig)

    # Print comparison with current AcademIA matrix (read tolerance_matrix.yaml)
    print("=" * 70)
    print("Comparison with current tolerance_matrix.yaml")
    print("=" * 70)
    import yaml
    tol = yaml.safe_load(open("/opt/academie/webapp/backend/app/config/tolerance_matrix.yaml"))
    band_by_level = tol["cefr_bands"]
    matrix = tol["matrix"]
    print(f"\n{'Family':<15} {'Level':<5} {'Emp.tier':<15} {'Current':<15} {'Match':<6}")
    for _, row in df_tier.sort_values(["academie_family", "cefr_level"]).iterrows():
        fam, lvl = row["academie_family"], row["cefr_level"]
        emp_tier = row["tier_empirical"]
        band = band_by_level.get(lvl)
        if fam in matrix and band in matrix[fam]:
            current = matrix[fam][band]
            # Convert emp_tier to current-matrix vocabulary
            emp_simplified = {
                "T1_ignored": "ignored",
                "T2_noted": "noted",
                "T3_penalized": "penalized",
                "T4_regressive": "penalized",  # regressive treated as penalized in current matrix
            }[emp_tier]
            match = "✓" if emp_simplified == current else "✗"
            print(f"{fam:<15} {lvl:<5} {emp_tier:<15} {current:<15} {match:<6}")

    print(f"\nFigures saved to: {FIG}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
