"""Prepare Bernoulli-per-(essay, family) dataset for the GLMM.

Input:
  /mnt/cosmos-data/sprint1/data/processed/errors_long.parquet
  /mnt/cosmos-data/sprint1/data/processed/tier_assignments_external.parquet

Output:
  /mnt/cosmos-data/sprint1/data/processed/glmm_dataset.parquet
    columns: essay_id, learner_id, cefr_level, academie_family,
             tier_assigned, y
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROC = Path("/mnt/cosmos-data/sprint1/data/processed")
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
FAMILIES = [
    "verb_tense", "noun_det", "preposition", "pronoun",
    "word_order", "morphology", "surface", "sentence", "verb_usage",
]


def main() -> int:
    err = pd.read_parquet(PROC / "errors_long.parquet")
    tier = pd.read_parquet(PROC / "tier_assignments_external.parquet")

    # Keep mapped errors at the 6 CEFR levels (drop N = native)
    err_m = err[(err["status"] == "mapped") & (err["cefr_level"].isin(LEVELS))].copy()

    # Build essay catalog with one row per essay (text_id, learner_id, cefr_level)
    essays = (
        err_m[["text_id", "learner_id", "cefr_level"]]
        .drop_duplicates(subset=["text_id"])
        .rename(columns={"text_id": "essay_id"})
        .reset_index(drop=True)
    )

    # Cartesian product essays × families
    essays["_key"] = 1
    fam_df = pd.DataFrame({"academie_family": FAMILIES, "_key": 1})
    full = essays.merge(fam_df, on="_key").drop(columns="_key")

    # Join tier_assigned per (family, cefr_level) — tier_empirical from step 4
    tier_lookup = tier[["academie_family", "cefr_level", "tier_empirical"]].rename(
        columns={"tier_empirical": "tier_assigned"}
    )
    full = full.merge(tier_lookup, on=["academie_family", "cefr_level"], how="left")

    # y = 1 if essay has ≥1 error of that family (from err_m)
    pos = (
        err_m.groupby(["text_id", "academie_family"]).size().reset_index(name="n")
    ).rename(columns={"text_id": "essay_id"})
    full = full.merge(pos[["essay_id", "academie_family", "n"]],
                      on=["essay_id", "academie_family"], how="left")
    full["y"] = (full["n"].fillna(0) > 0).astype(int)
    full = full.drop(columns=["n"])

    # Drop rows where tier lookup missing (shouldn't happen, sanity)
    missing = full["tier_assigned"].isna().sum()
    if missing:
        print(f"⚠️ {missing} rows with missing tier_assigned — dropping")
        full = full.dropna(subset=["tier_assigned"])

    full.to_parquet(PROC / "glmm_dataset.parquet", index=False, compression="zstd")

    # Report
    print(f"glmm_dataset.parquet : {len(full):,} rows")
    print(f"  positives (y=1): {full['y'].sum():,}  ({100 * full['y'].mean():.1f}%)")
    print(f"  learners       : {full['learner_id'].nunique():,}")
    print(f"  essays         : {full['essay_id'].nunique():,}")
    print(f"  families       : {full['academie_family'].nunique()}")
    print()
    print("Crosstab y × tier_assigned:")
    print(pd.crosstab(full["y"], full["tier_assigned"], margins=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
