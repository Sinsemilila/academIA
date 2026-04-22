"""Session 40 Phase C — Export 24 scenarios to a manual-scoring template.

Generates a markdown document Sinse fills in with per-dim verdicts, then
`calibration.py` computes Cohen's κ vs the oracle's majority verdicts.
This is the ONLY pure-human step in the oracle pipeline.

Usage :
  python3 scripts/oracle/export_for_manual.py > /tmp/oracle_manual_scoring.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def _load_scenarios(agent: str) -> list[dict]:
    sc_dir = ROOT / "scenarios" / agent
    sc = []
    for f in sorted(sc_dir.glob("*.yaml")):
        sc.append(yaml.safe_load(f.read_text()))
    return sc


def _load_golden(agent: str, sid: str) -> str:
    p = ROOT / "scenarios" / agent / "golden" / f"{sid}.json"
    if not p.exists():
        return "(no golden recorded)"
    return json.loads(p.read_text()).get("response", "")


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="teacher_en")
    args = ap.parse_args()
    scenarios = _load_scenarios(args.agent)
    out = []
    out.append("# Oracle V1 — Manual scoring template (Sinse)")
    out.append("")
    out.append("Pour chaque scenario, remplis les 3 dims LLM-jugés avec `pass`/`fail`/`unknown`.")
    out.append("Un champ `reasoning` optionnel — important surtout pour les `fail` (comprendre le disagreement avec l'oracle).")
    out.append("")
    out.append("Le YAML résultat se colle tel quel dans `/tmp/oracle_sinse_scores.yaml` → `calibration.py` le lit.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("```yaml")
    out.append("# Generated template — fill `verdict` cells and save as /tmp/oracle_sinse_scores.yaml")
    out.append("scores:")
    for sc in scenarios:
        sid = sc["id"]
        ckey = sc["scenario_key"]
        learner = next((t for t in sc["turns"] if t["role"] == "learner"), {})
        golden = _load_golden(args.agent, sid)
        out.append(f"  {sid}:")
        out.append(f"    # learner [{ckey['cefr']}/{ckey['target_tier']}/{ckey['fla']}]: {learner.get('text', '')[:80]}")
        out.append(f"    # bot: {golden[:120].replace(chr(10), ' ')}")
        out.append(f"    cf_move_set_valid: unknown       # pass | fail | unknown")
        out.append(f"    register_cefr_alignment: unknown")
        out.append(f"    semantic_fidelity_pairwise: unknown")
    out.append("```")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
