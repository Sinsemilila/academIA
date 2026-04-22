"""Session 41 — C1/C2 scenario extension for Teacher EN oracle corpus.

Based on CEFR 2020 Companion descriptors + existing rubrics/en.yaml C1/C2
sections + common FR→EN high-level error patterns from the research
agent (8 patterns identified, 5 picked for V1).

Each scenario uses curriculum_en.yaml concept_keys present at C1 or C2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "scenarios" / "teacher_en"

C1_C2_SPECS = [
    # (id, cefr, tier, category, fla, text, errors, style)
    ("c1_t3_false_friend_assister_001", "C1", "T3", "vocabulary", "low",
     "I assisted the presentation to the conference this morning and learned a lot.",
     ["LEX:FALSE"], "direct"),
    ("c1_t3_conditional_mix_001", "C1", "T3", "conditional", "mid",
     "If I would have known about the meeting earlier, I would have prepared differently.",
     ["V:COND"], "direct"),
    ("c1_t3_register_drift_001", "C1", "T3", "vocabulary", "mid",
     "Honestly, I don't give a damn about their recommendation, but the policy remains quite important.",
     ["REG:LEVEL"], "direct"),
    ("c2_t3_subjunctive_suggest_001", "C2", "T3", "verb_usage", "low",
     "We suggest that the policy is revised before next quarter to avoid further issues.",
     ["V:MOOD"], "direct"),
    ("c2_t3_passive_overuse_001", "C2", "T3", "vocabulary", "low",
     "It is believed that the economy will recover; it is said that inflation is decreasing; it is hoped that unemployment drops.",
     ["REG:LEVEL", "LEX:COLLOC"], "direct"),
]


def _default_dims_c1c2(cefr: str, target_tier: str) -> dict:
    """Policy matrix for C1/C2 — tight L2 ratio, metalinguistic acceptable,
    mini-lesson allowed at C1+ (rubric explicitly permits 'metalinguistic
    + alternative phrasings')."""
    if cefr == "C1":
        acceptable = ["elicitation", "metalinguistic", "partial_recast", "clarification_request"]
        forbidden = []
        l2_band = [0.95, 1.0]
        max_lines = 7
        mini_lesson_allowed = True
    else:  # C2
        acceptable = ["elicitation", "metalinguistic", "partial_recast"]
        forbidden = ["full_recast"]  # too light at C2
        l2_band = [0.97, 1.0]
        max_lines = 7
        mini_lesson_allowed = True
    return {
        "cf_move_set_valid": {"mode": "set_membership",
                              "acceptable": acceptable, "forbidden": forbidden},
        "scaffolding_flags_honored": {"mode": "all_required", "l2_ratio_band": l2_band},
        "register_cefr_alignment": {"mode": "within_sublevel",
                                    "target": cefr, "tolerance": 1},
        "recast_saliency_and_dosage": {"mode": "structural",
                                       "max_lines": max_lines, "max_questions": 2,
                                       "error_form_isolated": True,
                                       "mini_lesson_allowed": mini_lesson_allowed},
        "semantic_fidelity_pairwise": {"mode": "llm_pairwise", "vs_golden": True},
    }


def build() -> list[dict]:
    out = []
    for id_, cefr, tier, cat, fla, text, errs, style in C1_C2_SPECS:
        out.append({
            "id": id_,
            "source": "handcrafted_c1c2_session41",
            "scenario_key": {
                "agent": "teacher_en",
                "cefr": cefr, "target_tier": tier,
                "error_category": cat, "fla": fla,
                "style_profile": style,
            },
            "multi_turn": False,
            "turns": [{"role": "learner", "text": text, "turn_number": 8,
                       "expected_errors": errs}],
            "expected_dimensions": _default_dims_c1c2(cefr, tier),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    scenarios = build()
    print(f"▶ {len(scenarios)} C1/C2 scenarios ready")
    for sc in scenarios:
        k = sc["scenario_key"]
        print(f"  {sc['id']:<45} [{k['cefr']}/{k['target_tier']}/{k['fla']}]")
    if not args.apply:
        print("\n▶ DRY-RUN. --apply to write.")
        return 0
    for sc in scenarios:
        (OUT_DIR / f"{sc['id']}.yaml").write_text(
            yaml.safe_dump(sc, sort_keys=False, allow_unicode=True))
    print(f"▶ wrote {len(scenarios)} → {OUT_DIR.relative_to(ROOT.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
