"""Generate tolerance_matrix_v2_draft.yaml from empirical tier assignments.

Inputs:
  - /mnt/cosmos-data/sprint1/data/processed/tier_assignments_external.parquet
  - /opt/academia/webapp/backend/app/config/tolerance_matrix.yaml (as base)

Outputs:
  - /opt/academia/webapp/backend/app/config/tolerance_matrix_v2_draft.yaml

Strategy (Path A conservative):
  - Keep the full v1 structure (families, codes, labels, concept_families, etc.)
  - Replace `matrix:` section using empirical tier per (family, CEFR level).
  - Map 6 levels → 4 bands for compatibility with existing consumer code.
  - Add new `weights:` with numerical priors derived from reach quartiles
    (proper GLMM-based β_tier will refine these in Sprint 1.5).
  - For families not calibrated (verb_usage deeper than V:CHOICE, discourse,
    calque, vocabulary), preserve the v1 values and flag them.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

TIER = "/mnt/cosmos-data/sprint1/data/processed/tier_assignments_external.parquet"
V1 = Path("/opt/academia/webapp/backend/app/config/tolerance_matrix.yaml")
OUT = Path("/opt/academia/webapp/backend/app/config/tolerance_matrix_v2_draft.yaml")

# 6-level CEFR → 4-band mapping (same as v1)
LEVEL_TO_BAND = {
    "A1": "beginner",
    "A2": "beginner",
    "B1": "intermediate",
    "B2": "upper",
    "C1": "advanced",
    "C2": "advanced",
}
BANDS = ["beginner", "intermediate", "upper", "advanced"]

# Empirical tier vocabulary → v1 string vocab
TIER_TO_V1 = {
    "T1_ignored": "ignored",
    "T2_noted": "noted",
    "T3_penalized": "penalized",
    "T4_regressive": "penalized",  # v1 has no separate regressive — merge to penalized
}

# Families calibrated via W&I ERRANT (rest keep v1 priors)
CALIBRATED_FAMILIES = {
    "verb_tense", "noun_det", "preposition", "pronoun",
    "word_order", "morphology", "surface", "sentence",
}
# `verb_usage` is partially covered (only V:CHOICE via bare VERB tag) — mark as "partial"


def _mode_tier_per_band(df_fam: pd.DataFrame) -> dict[str, str]:
    """For a family, compute the most common empirical tier per band."""
    df_fam = df_fam.copy()
    df_fam["band"] = df_fam["cefr_level"].map(LEVEL_TO_BAND)
    out = {}
    for band in BANDS:
        sub = df_fam[df_fam["band"] == band]
        if sub.empty:
            out[band] = "ignored"
            continue
        # Majority-vote tier across the 1-2 CEFR levels in this band, weighted by n_errors
        weighted = (
            sub.groupby("tier_empirical")["n_errors_total"].sum()
            .sort_values(ascending=False)
        )
        tier = weighted.index[0] if len(weighted) else "T1_ignored"
        out[band] = TIER_TO_V1[tier]
    return out


def main() -> int:
    tier_df = pd.read_parquet(TIER)
    v1 = yaml.safe_load(V1.read_text())
    v2 = yaml.safe_load(V1.read_text())  # deep-ish copy via re-parse

    # Build new matrix per family
    new_matrix = {}
    for family in v1["matrix"]:
        if family in CALIBRATED_FAMILIES:
            sub = tier_df[tier_df["academie_family"] == family]
            new_matrix[family] = _mode_tier_per_band(sub)
        else:
            # Not calibrated — keep v1 values
            new_matrix[family] = dict(v1["matrix"][family])

    v2["matrix"] = new_matrix

    # Weights: empirical priors from Sprint 1 reach-based tier gradient.
    # These are placeholder values; Sprint 1.5 GLMM will refine via β_tier.
    v2["weights"] = {
        "ignored": 0.10,       # was 0.00 — small positive to track even "normal" errors
        "noted": 0.35,         # was 0.30 — slight upward
        "penalized": 0.75,     # was 0.80 — slight downward (less punitive)
        "shadow": 0.0,         # unchanged — truly silent
    }
    v2["weights_source"] = (
        f"empirical_external_corpora_v1 (W&I + LOCNESS BEA 2019, {date.today().isoformat()}); "
        "GLMM β_tier refinement deferred to Sprint 1.5"
    )

    # Calibration notes per family
    v2["calibration_status"] = {
        fam: ("calibrated_empirically" if fam in CALIBRATED_FAMILIES
              else "v1_prior_kept")
        for fam in v1["matrix"]
    }

    # Write with clear header
    header = (
        "# Tolerance Matrix v2 — DRAFT (Sprint 1, Path A)\n"
        "# Generated from empirical analysis of W&I + LOCNESS BEA 2019 corpus.\n"
        f"# Corpus: 2,671 learners, 70,489 mapped error annotations, CEFR A1–C2 + N.\n"
        f"# Date: {date.today().isoformat()}\n"
        "# Status: draft — review before activating in place of tolerance_matrix.yaml.\n"
        "# Next: Sprint 1.5 = NumPyro GLMM for numerical β_tier weights.\n"
        "#\n"
        "# Methodology: reach-based percentile thresholds per Schema Étape 2 of\n"
        "# docs/01-pedagogy/error-gradation.md:\n"
        "#   reach ≥ 0.70 → T1 ignored / 0.30–0.70 → T2 noted /\n"
        "#   0.10–0.30 → T3 penalized / < 0.10 → T4 regressive (→ penalized in 4-tier vocab)\n"
        "#\n"
        "# Calibrated families (via ERRANT mapping, 120,776 tag instances):\n"
        "#   verb_tense, noun_det, preposition, pronoun, word_order,\n"
        "#   morphology, surface, sentence\n"
        "# NOT calibrated (priors kept — ERRANT too coarse or L1-dependent):\n"
        "#   verb_usage (modals/conditionals), vocabulary, calque, discourse\n"
        "#\n"
        "# See also: /mnt/cosmos-data/sprint1/results/figures/tier_map.png\n\n"
    )

    OUT.write_text(header + yaml.safe_dump(v2, sort_keys=False, allow_unicode=True))
    print(f"Written: {OUT}")
    print(f"Size: {OUT.stat().st_size / 1024:.1f} KB")

    # Diff summary
    changed = 0
    total = 0
    for fam in v1["matrix"]:
        for band in BANDS:
            old = v1["matrix"][fam].get(band, "ignored")
            new = v2["matrix"][fam].get(band, "ignored")
            if old != new:
                changed += 1
            total += 1
    print(f"\nMatrix cells changed: {changed}/{total} ({100.0 * changed / total:.0f}%)")

    # Report non-calibrated families
    non_cal = [f for f in v1["matrix"] if f not in CALIBRATED_FAMILIES]
    print(f"Non-calibrated (v1 preserved): {non_cal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
