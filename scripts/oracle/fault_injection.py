"""Session 40 Phase D — Fault injection validation (LiteLLM-bypass approach).

V1 ORIGINAL PLAN was to clone Teacher EN Dify app per fault and run the
oracle against the clone. That path was too slow in practice (Dify
placeholder resolution hangs without a real conversation state, >30
min wall time per fault on 24 scenarios). See docs §Phase D pivot.

**V1 pivot** : skip Dify entirely for fault injection. Extract the
Teacher EN system prompt via JSONB SELECT, apply the fault via string
substitution, call LiteLLM gpt-4o-mini directly with
(patched_system_prompt + learner_turn) → bot response. Score via
the same oracle judges used against goldens.

This measures the oracle's ability to detect prompt-content regressions,
which is what the 5 faults encode. Workflow-level issues (broken
placeholders, node crashes) are out of scope for V1 oracle anyway.

Required gates for V1 ship :
  detection_rate ≥ 0.90 avg across 5 faults
  false_alarm_rate ≤ 0.10 on unchanged prompt

Budget : 5 faults × 24 scenarios × 1 bot call + 3 dim judges × N=1 =
~480 calls ≈ 240K tokens. Plus 24 × 4 = 96 calls for clean baseline =
~288K tokens total (~19% daily quota).

Usage :
  python3 scripts/oracle/fault_injection.py --apply
  python3 scripts/oracle/fault_injection.py --apply --only force_long_response
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from oracle.judges import deterministic, llm_pairwise  # noqa: E402
from oracle.judges.dify_client import _agent_config  # noqa: E402
from oracle.lint import run_lint  # noqa: E402
from oracle.schemas import ScenarioSchema  # noqa: E402

ROOT = Path(__file__).resolve().parent


# 5 fault patches — each is a {from_str: to_str} dict applied via
# string replace on the extracted prompt. from_str MUST appear in the
# current prompt (verified via _validate_faults at startup).
FAULTS = {
    "force_long_response": {
        "Max 5 lignes par réponse (8 si mini-leçon)":
            "Max 20 lignes par réponse (toujours détaillé)",
    },
    "remove_one_question_rule": {
        "UNE seule question par message":
            "Pose plusieurs questions par message",
    },
    "swap_implicit_to_explicit": {
        "IMPLICIT_RECAST (reformule inline, pas de pause)":
            "EXPLICIT (annonce 'c'est faux, la réponse correcte est X' puis continue)",
    },
    "force_metalinguistic_always": {
        "ELICITATION ↔ METALINGUISTIC (alterner — diversity rule appliquée par le système)":
            "TOUJOURS METALINGUISTIC — explique la règle grammaticale à chaque erreur, peu importe le niveau",
    },
    "disable_self_answer_rule": {
        "Tu ne donnes JAMAIS la réponse à ta propre question":
            "Tu donnes TOUJOURS la réponse à ta propre question immédiatement",
    },
}


def _extract_prompt(agent: str) -> str:
    """Pull the llm_session system prompt from the current workflow of `agent`."""
    workflow_id = _agent_config(agent)["workflow_id"]
    sql = (
        "SELECT n->'data'->'prompt_template'->0->>'text' "
        f"FROM workflows, jsonb_array_elements(graph::jsonb->'nodes') n "
        f"WHERE id='{workflow_id}' "
        f"AND n->'data'->>'type'='llm' "
        f"AND n->'data'->>'title' ~* 'session' LIMIT 1;"
    )
    raw = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return raw


def _stub_placeholders(prompt: str, cefr: str, style: str = "direct", agent: str = "teacher_en") -> str:
    """Replace Dify placeholders with stubs that force the bot into a
    realistic tutoring posture when fed directly to gpt-4o-mini.

    agent (teacher_en | maestro_es) picks the L2 target language."""
    if agent == "teacher_en":
        language = "English"
        lang_target_prof = "d'anglais"
    elif agent == "maestro_es":
        language = "Spanish"
        lang_target_prof = "d'espagnol"
    else:
        language = "English"
        lang_target_prof = "d'anglais"
    return (prompt
            .replace("{{#code_turn_check.lang_target_prof#}}", lang_target_prof)
            .replace("{{#code_turn_check.rubric_for_level#}}",
                     f"Niveau cible CEFR : {cefr}. Style : {style}. "
                     f"ALWAYS reply to the learner IN {language.upper()} "
                     f"(L2 target language), never in French.")
            .replace("{{#code_turn_check.promotion_msg#}}", "")
            .replace("{{#code_profil_check.profil_text#}}",
                     f"Profil apprenant : CEFR {cefr}, FR-native. "
                     f"Style : {style}. L2 cible : {language}. "
                     f"Reply IN {language.upper()} always.")
            .replace("{{#conversation.session_snapshot#}}",
                     f"Tour conversation 5-7. Learner niveau {cefr}.")
            .replace("{{#code_turn_check.error_feedback#}}",
                     "Aucune erreur pré-détectée (live analysis only).")
            .replace("{{#code_turn_check.scaffolding_block#}}",
                     f"Apply CEFR {cefr} scaffolding policy standard.")
            .replace("{{#code_turn_check.micro_lesson_block#}}", "")
            .replace("{{#code_turn_check.priority_concepts_block#}}", ""))


def _validate_faults(base_prompt: str) -> list[str]:
    """Return list of faults whose from_str isn't in the current prompt."""
    missing = []
    for fault_name, patches in FAULTS.items():
        for from_str in patches:
            if from_str not in base_prompt:
                missing.append(f"{fault_name}: {from_str[:60]!r}")
    return missing


def _load_scenarios(agent: str) -> list[ScenarioSchema]:
    sc_dir = ROOT / "scenarios" / agent
    out = []
    for f in sorted(sc_dir.glob("*.yaml")):
        out.append(ScenarioSchema.model_validate(yaml.safe_load(f.read_text())))
    return out


def _load_golden(agent: str, sid: str) -> str:
    p = ROOT / "scenarios" / agent / "golden" / f"{sid}.json"
    if not p.exists():
        return ""
    return json.loads(p.read_text()).get("response", "")


def _apply_patch(prompt: str, patches: dict[str, str]) -> str:
    out = prompt
    for k, v in patches.items():
        out = out.replace(k, v)
    return out


def _call_litellm(client: httpx.Client, system: str, user: str, cfg: dict) -> str | None:
    payload = {
        "model": cfg["judge"]["model"],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.2,
        "max_tokens": 350,
    }
    master = os.environ.get("LITELLM_MASTER_KEY", "")
    headers = {"Content-Type": "application/json"}
    if master:
        headers["Authorization"] = f"Bearer {master}"
    try:
        r = client.post(cfg["litellm"]["proxy_url"], json=payload,
                        headers=headers, timeout=45)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  litellm error: {e}", file=sys.stderr)
        return None


def _score(agent: str, scenario: ScenarioSchema, response: str, cfg: dict) -> bool:
    """True if oracle flags regression.

    IMPORTANT — methodological note :
    Goldens were recorded via Dify public API (full workflow executes).
    Fault injection calls LiteLLM directly with stubbed placeholders
    (no Dify workflow). The two call paths produce materially different
    response distributions even on IDENTICAL prompts. So `semantic_fidelity_pairwise`
    (which compares response to golden) would flag ALL clean-baseline
    responses as 'divergent' simply because of call-pattern mismatch,
    not because of any regression.

    Fault injection therefore scores on :
      - lint (JSON wrapper, A1 no-jargon, priority leak, observed_level)
      - deterministic (recast_saliency line/? count, scaffolding_l2_ratio,
        cf_move_partial regex)
      - cf_move_set_valid (LLM classifier — doesn't compare to golden)
      - register_cefr_alignment (LLM classifier — doesn't compare to golden)

    We exclude semantic_fidelity_pairwise from fault injection gating.
    For full-mode regression testing against goldens (via harness.py),
    pairwise stays in play because the bot is called via the SAME Dify
    path the goldens were recorded from.
    """
    if not response:
        return False
    if any(not r.passed for r in run_lint(scenario, response)):
        return True
    if any(d.verdict == "fail" for d in deterministic.score_all(scenario, response)):
        return True
    # Only the classifier LLM dims, not pairwise-vs-golden
    llm_all = llm_pairwise.score_all(scenario, response, "", cfg, n=1)
    llm_classifier_only = [d for d in llm_all if d.dim != "semantic_fidelity_pairwise"]
    return any(d.verdict == "fail" for d in llm_classifier_only)


def run_condition(agent: str, label: str, prompt: str, scenarios: list[ScenarioSchema], cfg: dict) -> tuple[int, int]:
    flagged = 0
    with httpx.Client(timeout=60) as client:
        for i, sc in enumerate(scenarios, 1):
            learner = next((t for t in sc.turns if t.role == "learner"), None)
            if not learner:
                continue
            system = _stub_placeholders(prompt, sc.scenario_key.cefr,
                                        sc.scenario_key.style_profile, agent=agent)
            response = _call_litellm(client, system, learner.text, cfg)
            is_flagged = _score(agent, sc, response or "", cfg) if response else True
            marker = "⚠" if is_flagged else "·"
            print(f"  [{label}][{i}/{len(scenarios)}] {marker} {sc.id}")
            if is_flagged:
                flagged += 1
    return flagged, len(scenarios)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="teacher_en")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    base_prompt = _extract_prompt(args.agent)
    print(f"▶ Extracted {args.agent} prompt : {len(base_prompt)} chars")

    missing = _validate_faults(base_prompt)
    if missing:
        print("ERROR: fault from_strs not in current prompt:")
        for m in missing:
            print(f"  - {m}")
        return 2

    scenarios = _load_scenarios(args.agent)
    print(f"▶ {len(scenarios)} scenarios loaded")

    if not args.apply:
        print("DRY-RUN. Use --apply to run fault injection.")
        return 0

    results = {}

    # Clean baseline
    print("\n━━━ CLEAN BASELINE ━━━")
    fl, tot = run_condition(args.agent, "clean", base_prompt, scenarios, cfg)
    results["clean"] = {"flagged": fl, "total": tot, "rate": fl / tot}
    print(f"  false_alarm_rate = {fl}/{tot} = {fl/tot:.1%}")

    faults_to_run = {args.only: FAULTS[args.only]} if args.only else FAULTS

    for name, patches in faults_to_run.items():
        print(f"\n━━━ FAULT : {name} ━━━")
        patched = _apply_patch(base_prompt, patches)
        assert patched != base_prompt, f"patch {name} made no change"
        fl, tot = run_condition(args.agent, name, patched, scenarios, cfg)
        results[name] = {"flagged": fl, "total": tot, "rate": fl / tot}
        print(f"  detection_rate = {fl}/{tot} = {fl/tot:.1%}")

    # Summary
    print("\n━━━ SUMMARY ━━━")
    fault_rates = [v["rate"] for k, v in results.items() if k != "clean" and "rate" in v]
    mean_det = sum(fault_rates) / max(len(fault_rates), 1)
    fa = results.get("clean", {}).get("rate", 1.0)
    print(f"  false_alarm_rate : {fa:.1%}")
    print(f"  mean detection   : {mean_det:.1%}")
    for name in faults_to_run:
        r = results.get(name, {})
        print(f"    {name:<35} {r.get('rate', 0):.1%} ({r.get('flagged')}/{r.get('total')})")
    Path("/tmp/oracle_fault_injection.json").write_text(json.dumps(results, indent=2))

    gate = mean_det >= 0.9 and fa <= 0.1
    print(f"\n  GATE (≥90% detect / ≤10% false alarm) : {'✅ PASS' if gate else '❌ FAIL'}")
    return 0 if gate else 1


if __name__ == "__main__":
    sys.exit(main())
