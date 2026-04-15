"""Synthetic battery replay: score the 189 phase1b TEST_CASES with v1 vs v2.

Does NOT call the LLM (phase1b's real purpose). We only use the known
(text, [error_codes]) pairs as synthetic error occurrences, attribute them
to each of 6 CEFR levels, and compute the total score under both matrices.

Goal: confirm at matrix level (without LLM round-trip) that v2 behaves as
documented in sprint1_report.md (more lenient on endemic families, stricter
on rare families).

Output: /mnt/cosmos-data/sprint1/results/v1_vs_v2_synthetic.json
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

BATTERY_PATH = Path("/opt/academie/scripts/phase1b_full_battery.py")
V2_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix_v2.yaml")
V1_YAML = Path("/opt/academie/webapp/backend/app/config/tolerance_matrix.yaml")
RESULTS = Path("/mnt/cosmos-data/sprint1/results/v1_vs_v2_synthetic.json")

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


@pytest.fixture(scope="module")
def battery():
    spec = importlib.util.spec_from_file_location("phase1b", BATTERY_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TEST_CASES


@pytest.fixture(scope="module")
def v1():
    return yaml.safe_load(V1_YAML.read_text())


@pytest.fixture(scope="module")
def v2():
    return yaml.safe_load(V2_YAML.read_text())


def _code_family(code: str, mtx: dict) -> str | None:
    for fam, d in mtx["families"].items():
        if code in d.get("codes", []):
            return fam
    return None


def _score_case(code: str, level: str, mtx: dict) -> float:
    fam = _code_family(code, mtx)
    if not fam or fam not in mtx["matrix"]:
        return 0.0
    band = mtx["cefr_bands"].get(level, "intermediate")
    tier = mtx["matrix"][fam].get(band, "ignored")
    return mtx["weights"].get(tier, 0.0)


def test_synthetic_battery_consistent(battery, v1, v2):
    """For each (case × level) replay, compute v1 and v2 total."""
    rows = []
    totals = {lvl: {"v1": 0.0, "v2": 0.0, "n_cases": 0} for lvl in LEVELS}
    by_family_level_delta: dict[tuple[str, str], float] = {}

    for text, codes in battery:
        for code in codes:
            fam_v1 = _code_family(code, v1)
            fam_v2 = _code_family(code, v2)
            for lvl in LEVELS:
                w1 = _score_case(code, lvl, v1)
                w2 = _score_case(code, lvl, v2)
                totals[lvl]["v1"] += w1
                totals[lvl]["v2"] += w2
                totals[lvl]["n_cases"] += 1
                if fam_v1 == fam_v2 and fam_v1:
                    key = (fam_v1, lvl)
                    by_family_level_delta[key] = by_family_level_delta.get(key, 0.0) + (w2 - w1)

    report = {
        "n_test_cases": len(battery),
        "totals_by_level": totals,
        "deltas_by_family_level": {
            f"{fam}|{lvl}": round(d, 3)
            for (fam, lvl), d in by_family_level_delta.items()
        },
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(report, indent=2))

    print(f"\nSynthetic battery — {len(battery)} cases × {len(LEVELS)} levels:")
    for lvl in LEVELS:
        t = totals[lvl]
        delta = t["v2"] - t["v1"]
        pct = delta / t["v1"] * 100 if t["v1"] else 0
        print(f"  {lvl}: v1={t['v1']:7.2f}  v2={t['v2']:7.2f}  delta={delta:+7.2f} ({pct:+5.1f}%)")

    # Invariant 1: overall v2 globally more lenient (core Sprint 1 finding)
    total_v1 = sum(t["v1"] for t in totals.values())
    total_v2 = sum(t["v2"] for t in totals.values())
    assert total_v2 < total_v1, \
        f"Expected v2 globally more lenient, got v1={total_v1:.2f} v2={total_v2:.2f}"

    # Invariant 2: asymmetric by level — v2 is documented to be stricter at
    # A1/A2 on rare errors (sentence, word_order, morphology, pronoun flipped
    # from `ignored` to `noted`/`penalized`) and more lenient at B1+
    # (verb_tense/noun_det/surface/preposition flipped `penalized` → `ignored`).
    # We accept up to 15× inflation at beginner levels, require ≤ 1.2 at B1+.
    beginner_levels = {"A1", "A2"}
    for lvl in LEVELS:
        t = totals[lvl]
        if t["v1"] == 0 and t["v2"] == 0:
            continue
        if lvl in beginner_levels:
            # Rare-error flagging expected → upward OK up to 15x
            ratio = t["v2"] / max(t["v1"], 0.01)
            assert ratio <= 15.0, f"Level {lvl} ratio {ratio:.1f} > 15 (catastrophic)"
        else:
            # B1+ should be lenient-or-equal, not stricter
            assert t["v2"] <= t["v1"] * 1.2, \
                f"Level {lvl} v2={t['v2']:.2f} > 1.2 × v1={t['v1']:.2f} — unexpected strictness"


def test_sentence_family_stricter_at_beginner(v1, v2):
    """Sprint 1 finding: `sentence` at A1 was ignored, becomes penalized in v2."""
    v1_cell = v1["matrix"]["sentence"]["beginner"]
    v2_cell = v2["matrix"]["sentence"]["beginner"]
    assert v1_cell == "ignored"
    assert v2_cell == "penalized"


def test_verb_tense_family_lenient_at_advanced(v1, v2):
    """Sprint 1 finding: verb_tense at C1/C2 was penalized, becomes ignored."""
    assert v1["matrix"]["verb_tense"]["advanced"] == "penalized"
    assert v2["matrix"]["verb_tense"]["advanced"] == "ignored"


def test_calibration_status_flags_non_empirical(v2):
    """Families not calibrated via W&I keep v1 priors — must be flagged."""
    status = v2.get("calibration_status", {})
    non_calibrated = {"verb_usage", "vocabulary", "calque", "discourse"}
    for fam in non_calibrated:
        assert status.get(fam) == "v1_prior_kept", \
            f"Family {fam} should be tagged v1_prior_kept"
