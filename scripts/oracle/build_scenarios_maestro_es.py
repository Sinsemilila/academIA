"""Session 41 B2 — Maestro ES scenario generator.

24 scenarios, 100% handcrafted (ES error_log has only 8 rows none T2+).
Coverage : ser/estar, por/para, subjuntivo, concordancia, a-personal,
gustar inversion, pretérito regular+irregular, imperfect vs preterite,
+ risk scenarios (priority leak, A1 metalinguistic, L1 drift, T4,
comm breakdown) + 4 multi-turn.

Usage :
  python3 scripts/oracle/build_scenarios_maestro_es.py          # dry-run
  python3 scripts/oracle/build_scenarios_maestro_es.py --apply  # write files
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "scenarios" / "maestro_es"

# (id, cefr, target_tier, error_category, fla, text, expected_errors, style?)
HANDCRAFTED_ES = [
    # A1 — basics + ser/estar
    ("a1_t2_ser_estar_state_001", "A1", "T2", "V:SER_ESTAR", "low",
     "Yo soy cansado hoy porque trabajé mucho.", ["V:SER_ESTAR"]),
    ("a1_t2_ser_estar_loc_001", "A1", "T2", "V:SER_ESTAR", "low",
     "Mi casa es en Madrid, cerca del parque.", ["V:SER_ESTAR"]),
    ("a1_t2_art_prof_001", "A1", "T2", "ART:PROF", "mid",
     "Voy a hablar con Dr. García esta tarde.", ["ART:PROF"]),
    ("a1_t2_concord_gender_001", "A1", "T2", "concordancia", "low",
     "La problema es muy difícil y el solución no es clara.", ["CONCORD:GEN"]),
    ("a1_t2_hay_tener_001", "A1", "T2", "verb_usage", "low",
     "En mi ciudad tiene muchos parques y museos.", ["V:HAY_TENER"]),
    # A2 — preterite + preps
    ("a2_t2_preterite_001", "A2", "T2", "verb_tense", "low",
     "Ayer yo fue al cine y veí una película muy buena.", ["V:PRET"]),
    ("a2_t3_por_para_001", "A2", "T3", "PREP:POR_PARA", "mid",
     "Estudio español para tres años y necesito hablar por mi trabajo.", ["PREP:POR_PARA"]),
    ("a2_t2_a_personal_001", "A2", "T2", "preposition", "low",
     "Veo mi amigo todos los días en la escuela.", ["PREP:A_PERSONAL"]),
    # B1 — subjuntivo + gustar
    ("b1_t3_subjuntivo_pres_001", "B1", "T3", "V:SUBJ", "mid",
     "Espero que mi hermano viene a la fiesta este fin de semana.", ["V:SUBJ"]),
    ("b1_t3_gustar_subj_001", "B1", "T3", "V:GUSTAR_SUBJECT", "low",
     "Yo gusto mucho la música clásica y los libros de historia.", ["V:GUSTAR_SUBJECT"]),
    ("b1_t2_quantifier_001", "B1", "T2", "QUANT:MUY_MUCHO", "low",
     "La fiesta fue mucho divertida pero yo estaba muy cansada después.", ["QUANT:MUY_MUCHO"]),
    # B2 — imperfecto vs pretérito + modales
    ("b2_t3_imperfecto_pret_001", "B2", "T3", "V:ASPECT", "low",
     "Cuando estaba niño, jugaba mucho con mis primos hasta que nos mudábamos a otra ciudad.", ["V:ASPECT"]),
    ("b2_t3_condicional_001", "B2", "T3", "conditional", "mid",
     "Si tuviera más tiempo, iba a estudiar un idioma nuevo cada año.", ["V:COND"]),
    ("b2_t2_false_friend_001", "B2", "T2", "vocabulary", "low",
     "Actualmente estoy embarazada con este proyecto y tengo muchos compromisos.",
     ["LEX:FALSE"]),
    # C1 — subjuntivo imperfecto + complex
    ("c1_t3_subjuntivo_imp_001", "C1", "T3", "V:SUBJ", "low",
     "Me alegré mucho de que tú viniste a la cena ayer por la noche.", ["V:SUBJ"]),
    # Risk scenarios (5)
    ("risk_priority_leak_b1_es_001", "B1", "T2", "misc", "low",
     "Cuéntame algo sobre tu fin de semana por favor.", []),
    ("risk_a1_metalinguistic_leak_es_001", "A1", "T2", "V:SER_ESTAR", "low",
     "No entiendo, mi español es malo.", []),
    ("risk_l1_drift_a1_es_001", "A1", "T2", "articles", "mid",
     "Yo quiero un café con leche por favor.", []),
    ("risk_t4_regression_a2_es_001", "A2", "T4", "V:SER_ESTAR", "high",
     "Soy en mi casa ahora y estoy muy feliz.", ["V:SER_ESTAR"]),
    ("risk_comm_breakdown_b1_es_001", "B1", "T4", "misc", "mid",
     "La cosa que hacía de la persona por la razón del tiempo.", ["SENT:COHER"]),
]

MULTI_TURN_ES = [
    ("multi_a1_ser_estar_no_uptake_001", "A1", "T2", "V:SER_ESTAR", "low",
     "Yo soy cansado hoy.", "Sí, yo soy cansado todo el tiempo cuando trabajo.", "no"),
    ("multi_a2_por_para_uptake_001", "A2", "T2", "PREP:POR_PARA", "mid",
     "Necesito aprender español por mi trabajo.", "Ah sí, necesito aprender español para mi trabajo.", "yes"),
    ("multi_b1_subj_partial_001", "B1", "T3", "V:SUBJ", "mid",
     "Quiero que tú vienes mañana.", "Quiero que tú vengas mañana si puedes.", "partial"),
    ("multi_b2_imperfecto_no_uptake_001", "B2", "T3", "V:ASPECT", "low",
     "Cuando estaba niño jugué mucho.", "Sí, jugué mucho con mis primos también.", "no"),
]


def _default_dims_es(cefr: str, target_tier: str) -> dict:
    """Same policy matrix as Teacher EN, ES-tagged for future divergence."""
    if cefr == "A1":
        acceptable = ["full_recast", "partial_recast", "clarification_request"]
        forbidden = ["metalinguistic", "explicit_correction"]
        l2_band = [0.85, 1.0]
        max_lines = 5
    elif cefr == "A2":
        acceptable = ["full_recast", "partial_recast", "elicitation", "clarification_request"]
        forbidden = ["explicit_correction"] if target_tier in ("T1", "T2") else []
        l2_band = [0.9, 1.0]
        max_lines = 5
    elif cefr == "B1":
        acceptable = ["partial_recast", "elicitation", "metalinguistic", "clarification_request"]
        forbidden = ["explicit_correction"] if target_tier == "T2" else []
        l2_band = [0.95, 1.0]
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
        "cf_move_set_valid": {"mode": "set_membership",
                              "acceptable": acceptable, "forbidden": forbidden},
        "scaffolding_flags_honored": {"mode": "all_required", "l2_ratio_band": l2_band},
        "register_cefr_alignment": {"mode": "within_sublevel",
                                    "target": cefr, "tolerance": 1},
        "recast_saliency_and_dosage": {"mode": "structural",
                                       "max_lines": max_lines, "max_questions": 2,
                                       "error_form_isolated": True,
                                       "mini_lesson_allowed": False},
        "semantic_fidelity_pairwise": {"mode": "llm_pairwise", "vs_golden": True},
    }


def build() -> list[dict]:
    out = []
    for tup in HANDCRAFTED_ES:
        id_, cefr, tier, cat, fla, text, errs = tup[:7]
        out.append({
            "id": id_,
            "source": "handcrafted",
            "scenario_key": {
                "agent": "maestro_es",
                "cefr": cefr, "target_tier": tier,
                "error_category": cat, "fla": fla,
                "style_profile": "direct",
            },
            "multi_turn": False,
            "turns": [{"role": "learner", "text": text, "turn_number": 5,
                       "expected_errors": errs}],
            "expected_dimensions": _default_dims_es(cefr, tier),
        })
    for id_, cefr, tier, cat, fla, t1, t2, uptake in MULTI_TURN_ES:
        out.append({
            "id": id_,
            "source": "handcrafted",
            "scenario_key": {
                "agent": "maestro_es",
                "cefr": cefr, "target_tier": tier,
                "error_category": cat, "fla": fla,
                "style_profile": "direct",
            },
            "multi_turn": True,
            "turns": [
                {"role": "learner", "text": t1, "turn_number": 5},
                {"role": "learner", "text": t2, "turn_number": 7, "uptake": uptake},
            ],
            "expected_dimensions": _default_dims_es(cefr, tier),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    scenarios = build()
    print(f"▶ {len(scenarios)} ES scenarios ready")
    for sc in scenarios:
        k = sc["scenario_key"]
        print(f"  {sc['id']:<45} [{k['cefr']}/{k['target_tier']}/{k['fla']}]")
    if not args.apply:
        print("\n▶ DRY-RUN. Re-run with --apply to write files.")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for sc in scenarios:
        (OUT_DIR / f"{sc['id']}.yaml").write_text(
            yaml.safe_dump(sc, sort_keys=False, allow_unicode=True))
    print(f"▶ wrote {len(scenarios)} scenarios → {OUT_DIR.relative_to(ROOT.parent.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
