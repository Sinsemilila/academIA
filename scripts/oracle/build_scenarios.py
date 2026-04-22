"""Session 40 Phase B2 — scenario generator.

Generates 24 YAML scenarios covering the V1 stratification :
  - 4 error_log-seeded (A1-T2, the only cell with real data)
  - 16 handcrafted covering A2/B1/B2/C1 × T2/T3 × low/mid/high FLA
  - 4 multi-turn scripted (turn-1 error + turn-2 uptake/no-uptake)

Writes to scripts/oracle/scenarios/teacher_en/*.yaml.

Usage :
  python3 scripts/oracle/build_scenarios.py          # dry-run (stdout diff)
  python3 scripts/oracle/build_scenarios.py --apply  # write files
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "scenarios" / "teacher_en"


def _psql(sql: str) -> list[str]:
    return subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n").split("\n")


# ── Error-log seeded scenarios (4, all A1-T2 per census) ──

def fetch_error_log_rows() -> list[dict]:
    raw = _psql(
        """SELECT el.id, replace(el.original_text, '|', ':PIPE:') AS text,
                  el.error_code, el.tier, pe.niveau_global
           FROM error_log el
           JOIN profils_eleves pe ON pe.eleve_id = el.eleve_id AND pe.domain = el.domain
           WHERE el.domain = 'en'
             AND el.tier = 'T2'
             AND pe.niveau_global = 'A1'
             AND length(el.original_text) >= 5
             AND length(el.original_text) < 200
           ORDER BY length(el.original_text) DESC LIMIT 4;"""
    )
    rows = []
    for line in raw:
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        rows.append({
            "id": parts[0],
            "text": parts[1].replace(":PIPE:", "|"),
            "error_code": parts[2],
            "tier": parts[3],
            "niveau_global": parts[4],
        })
    return rows


def _category_for_code(code: str) -> str:
    mapping = {
        "V:TENSE": "verb_tense", "V:SVA": "verb_tense", "V:FORM": "verb_tense",
        "V:INFL": "verb_tense", "V:AUX": "verb_tense", "V:MODAL": "verb_usage",
        "V:COND": "conditional",
        "ART": "articles", "N:NUM": "number", "N:DET": "articles",
        "PREP": "preposition", "WO": "word_order",
        "SPELL": "surface",
    }
    return mapping.get(code, "misc")


def build_error_log_scenarios(rows: list[dict]) -> list[dict]:
    scenarios = []
    for i, r in enumerate(rows, 1):
        cat = _category_for_code(r["error_code"])
        scenarios.append({
            "id": f"el_a1_t2_{cat}_{i:03d}",
            "source": f"error_log_row_{r['id']}",
            "scenario_key": {
                "agent": "teacher_en",
                "cefr": "A1",
                "target_tier": "T2",
                "error_category": cat,
                "fla": "low",
                "style_profile": "direct",
            },
            "multi_turn": False,
            "turns": [{
                "role": "learner",
                "text": r["text"],
                "turn_number": 5,
                "expected_errors": [r["error_code"]],
            }],
            "expected_dimensions": _default_dims(cefr="A1", target_tier="T2"),
        })
    return scenarios


# ── Handcrafted scenarios (16) ──

HANDCRAFTED_SPECS = [
    # A2 tier
    ("a2_t2_past_simple_001", "A2", "T2", "verb_tense", "low",
     "Last weekend I goed to the cinema and I taked many photos.", ["V:INFL"]),
    ("a2_t3_articles_midfla_001", "A2", "T3", "articles", "mid",
     "I want to buy car for my wife. The house where we live is very small.", ["ART"]),
    ("a2_t2_plural_high_fla_001", "A2", "T2", "number", "high",
     "The childrens play with dogs in the gardens every days.", ["N:NUM"]),
    # B1 tier
    ("b1_t2_articles_001", "B1", "T2", "articles", "low",
     "I went to school yesterday and learned about history of Europe.", ["ART:GEN"]),
    ("b1_t3_conditional_midfla_001", "B1", "T3", "conditional",
     "mid", "If I would have more money, I will travel to Japan.", ["V:COND"]),
    ("b1_t3_present_perfect_001", "B1", "T3", "verb_tense", "mid",
     "I have seen this film yesterday and it was really good.", ["V:TENSE"]),
    ("b1_edge_t2t3_prepositions_001", "B1", "T2", "preposition", "low",
     "She is interested on learning French and in playing piano.", ["PREP"]),
    # B2 tier
    ("b2_t3_passive_001", "B2", "T3", "verb_usage", "low",
     "The report was finish by my colleague before the deadline was expired.", ["V:PASS"]),
    ("b2_t3_modal_deduction_001", "B2", "T3", "verb_usage", "mid",
     "He must have been forgot the meeting, he always is so responsible.", ["V:MODAL"]),
    ("b2_t2_collocations_001", "B2", "T2", "vocabulary", "low",
     "She makes her homework every evening before she does dinner.", ["LEX:COLLOC"]),
    # C1
    ("c1_t3_subjunctive_001", "C1", "T3", "verb_usage", "low",
     "It is essential that he is present at the meeting tomorrow.", ["V:MODAL"]),
    # High-risk failure scenarios (design §10.2)
    ("risk_priority_leak_b1_001", "B1", "T2", "misc", "low",
     "Tell me about your weekend please.", []),  # innocuous; tests bot doesn't leak priorities
    ("risk_a1_metalinguistic_leak_001", "A1", "T2", "verb_tense", "low",
     "I no understand this.", ["V:AUX"]),  # A1 low FLA should NOT lecture grammar
    ("risk_l1_drift_a1_001", "A1", "T2", "articles", "mid",
     "I eat apple this morning for breakfast.", ["ART"]),  # should stay L2
    ("risk_t4_regression_a2_001", "A2", "T4", "verb_tense", "high",
     "I go at the park yesterday.", ["V:TENSE", "PREP"]),  # acquired A1 form regressed
    ("risk_gravity_comm_breakdown_001", "B1", "T4", "misc", "mid",
     "The thing that was doing of the person for the reason.", ["SENT:COHER"]),  # incomprehensible
]

MULTI_TURN_SPECS = [
    ("multi_a1_verb_no_uptake_001", "A1", "T2", "verb_tense", "low",
     "Yesterday I go to the park with my mum.", "Yes I go there many time.",
     "no"),
    ("multi_a2_art_uptake_001", "A2", "T2", "articles", "mid",
     "I bought car last week.", "Yes I bought the car last week and I love it.",
     "yes"),
    ("multi_b1_cond_partial_001", "B1", "T3", "conditional", "mid",
     "If I would win the lottery, I buy a house.", "If I won the lottery, I will buy a house.",
     "partial"),
    ("multi_b2_modal_no_uptake_001", "B2", "T3", "verb_usage", "low",
     "He must have been forgot the meeting.", "Yes he must have been forgot because he never come late.",
     "no"),
]


def _default_dims(cefr: str, target_tier: str) -> dict:
    """Reasonable defaults per CEFR × tier — authors can override in YAMLs."""
    if cefr == "A1":
        acceptable = ["full_recast", "partial_recast", "clarification_request"]
        forbidden = ["metalinguistic", "explicit_correction"]
        l2_band = [0.7, 0.98]
        max_lines = 5
    elif cefr == "A2":
        acceptable = ["full_recast", "partial_recast", "elicitation", "clarification_request"]
        forbidden = ["explicit_correction"] if target_tier in ("T1", "T2") else []
        l2_band = [0.85, 1.0]
        max_lines = 5
    elif cefr == "B1":
        acceptable = ["partial_recast", "elicitation", "metalinguistic", "clarification_request"]
        forbidden = ["explicit_correction"] if target_tier == "T2" else []
        l2_band = [0.9, 1.0]
        max_lines = 6
    elif cefr == "B2":
        acceptable = ["elicitation", "metalinguistic", "partial_recast", "clarification_request"]
        forbidden = []
        l2_band = [0.95, 1.0]
        max_lines = 6
    else:  # C1/C2
        acceptable = ["elicitation", "metalinguistic", "partial_recast"]
        forbidden = []
        l2_band = [0.95, 1.0]
        max_lines = 7
    return {
        "cf_move_set_valid": {
            "mode": "set_membership",
            "acceptable": acceptable,
            "forbidden": forbidden,
        },
        "scaffolding_flags_honored": {
            "mode": "all_required",
            "l2_ratio_band": l2_band,
        },
        "register_cefr_alignment": {
            "mode": "within_sublevel",
            "target": cefr,
            "tolerance": 1,
        },
        "recast_saliency_and_dosage": {
            "mode": "structural",
            "max_lines": max_lines,
            "max_questions": 2,
            "error_form_isolated": True,
            "mini_lesson_allowed": False,
        },
        "semantic_fidelity_pairwise": {
            "mode": "llm_pairwise",
            "vs_golden": True,
        },
    }


def build_handcrafted() -> list[dict]:
    scenarios = []
    for id_, cefr, tier, cat, fla, text, errs in HANDCRAFTED_SPECS:
        scenarios.append({
            "id": id_,
            "source": "handcrafted",
            "scenario_key": {
                "agent": "teacher_en",
                "cefr": cefr,
                "target_tier": tier,
                "error_category": cat,
                "fla": fla,
                "style_profile": "direct",
            },
            "multi_turn": False,
            "turns": [{
                "role": "learner",
                "text": text,
                "turn_number": 5,
                "expected_errors": errs,
            }],
            "expected_dimensions": _default_dims(cefr, tier),
        })
    return scenarios


def build_multi_turn() -> list[dict]:
    scenarios = []
    for id_, cefr, tier, cat, fla, t1, t2, uptake in MULTI_TURN_SPECS:
        scenarios.append({
            "id": id_,
            "source": "handcrafted",
            "scenario_key": {
                "agent": "teacher_en",
                "cefr": cefr,
                "target_tier": tier,
                "error_category": cat,
                "fla": fla,
                "style_profile": "direct",
            },
            "multi_turn": True,
            "turns": [
                {"role": "learner", "text": t1, "turn_number": 5},
                {"role": "learner", "text": t2, "turn_number": 7, "uptake": uptake},
            ],
            "expected_dimensions": _default_dims(cefr, tier),
        })
    return scenarios


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    el_rows = fetch_error_log_rows()
    scenarios = (
        build_error_log_scenarios(el_rows)
        + build_handcrafted()
        + build_multi_turn()
    )

    print(f"▶ {len(scenarios)} scenarios ready")
    for sc in scenarios:
        cefr = sc["scenario_key"]["cefr"]
        tier = sc["scenario_key"]["target_tier"]
        fla = sc["scenario_key"]["fla"]
        print(f"  {sc['id']:<45} [{cefr}/{tier}/{fla}] {sc['source']}")

    if not args.apply:
        print("\n▶ DRY-RUN. Re-run with --apply to write files.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for sc in scenarios:
        path = OUT_DIR / f"{sc['id']}.yaml"
        path.write_text(yaml.safe_dump(sc, sort_keys=False, allow_unicode=True))
    print(f"▶ wrote {len(scenarios)} scenarios to {OUT_DIR.relative_to(ROOT.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
