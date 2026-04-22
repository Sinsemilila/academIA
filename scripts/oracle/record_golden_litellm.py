"""Session 41 — Record goldens via LiteLLM bypass (for fault injection validation).

This complements `record_golden.py` (which calls Dify public API). The
fault injection script calls LiteLLM directly with stubbed placeholders
— using Dify-recorded goldens there creates a call-path mismatch that
makes the clean baseline flag 100% of scenarios.

Fix : record a parallel set of goldens captured via the SAME LiteLLM
bypass path fault_injection uses. Those live under
scripts/oracle/scenarios/{agent}/golden_litellm/ (separate dir so
Dify goldens stay intact for harness full-mode).

Usage :
  python3 scripts/oracle/record_golden_litellm.py --agent teacher_en --apply
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oracle.judges.dify_client import _agent_config, _cfg  # noqa: E402
from oracle.schemas import GoldenFile, ScenarioSchema  # noqa: E402

ROOT = Path(__file__).resolve().parent


def _current_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd="/opt/academie",
            capture_output=True, text=True, check=True,
        ).stdout.strip()[:12]
    except Exception:
        return "unknown"


def _extract_prompt(agent: str) -> str:
    workflow_id = _agent_config(agent)["workflow_id"]
    sql = (
        "SELECT n->'data'->'prompt_template'->0->>'text' "
        f"FROM workflows, jsonb_array_elements(graph::jsonb->'nodes') n "
        f"WHERE id='{workflow_id}' AND n->'data'->>'type'='llm' "
        f"AND n->'data'->>'title' ~* 'session' LIMIT 1;"
    )
    return subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _stub_placeholders(prompt: str, cefr: str, style: str = "direct", agent: str = "teacher_en") -> str:
    """Shared stub with fault_injection.py — forces L2-reply mode per agent."""
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


def _call_litellm(client: httpx.Client, system: str, user: str, cfg: dict) -> str:
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
    r = client.post(cfg["litellm"]["proxy_url"], json=payload,
                    headers=headers, timeout=45)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="teacher_en")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    cfg = _cfg()
    base_prompt = _extract_prompt(args.agent)
    print(f"▶ Extracted {args.agent} prompt : {len(base_prompt)} chars")

    scenarios_dir = ROOT / "scenarios" / args.agent
    golden_dir = scenarios_dir / "golden_litellm"
    sha = _current_sha()

    scenarios = []
    for f in sorted(scenarios_dir.glob("*.yaml")):
        sc = ScenarioSchema.model_validate(yaml.safe_load(f.read_text()))
        scenarios.append(sc)

    print(f"▶ {len(scenarios)} scenarios to record (agent={args.agent} sha={sha})")
    if not args.apply:
        print("DRY-RUN. Use --apply.")
        return 0

    golden_dir.mkdir(parents=True, exist_ok=True)
    ok = 0
    with httpx.Client(timeout=60) as client:
        for i, sc in enumerate(scenarios, 1):
            learner = next((t for t in sc.turns if t.role == "learner"), None)
            if not learner:
                continue
            system = _stub_placeholders(base_prompt, sc.scenario_key.cefr,
                                        sc.scenario_key.style_profile, agent=args.agent)
            try:
                response = _call_litellm(client, system, learner.text, cfg)
            except Exception as e:
                print(f"  [{i}/{len(scenarios)}] {sc.id}: ERROR {e}")
                continue
            g = GoldenFile(
                scenario_id=sc.id,
                sha=sha,
                recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                response=response,
            )
            (golden_dir / f"{sc.id}.json").write_text(
                json.dumps(g.model_dump(), indent=2, ensure_ascii=False))
            ok += 1
            print(f"  [{i}/{len(scenarios)}] {sc.id}: ok ({len(response)} chars)")
    print(f"▶ recorded {ok}/{len(scenarios)} → {golden_dir.relative_to(ROOT.parent.parent)}")
    return 0 if ok == len(scenarios) else 1


if __name__ == "__main__":
    sys.exit(main())
