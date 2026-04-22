"""Session 41 — curriculum_en.yaml drift diagnostic.

Compare the 98 concept_keys in the DB (`curriculums` table) to the 53
in `packages/academie-core/academie_core/data/curriculum_en.yaml` and
produce a merge proposal for Sinse review.

Output :
  /tmp/curriculum_en_drift_proposal.md — side-by-side diff per CEFR
    level + proposed merged YAML with each DB-only concept tagged
    "NEW — PROPOSED WEIGHT X min, GROUP Y" for Sinse to review.

Usage :
  python3 scripts/sprint6/18_curriculum_en_drift_report.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
YAML_PATH = Path("/opt/academie/packages/academie-core/academie_core/data/curriculum_en.yaml")
OUT_PATH = Path("/tmp/curriculum_en_drift_proposal.md")


def _db_concepts() -> dict[str, list[str]]:
    out = {}
    for lvl in LEVELS:
        raw = subprocess.run(
            ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
             "-d", "academie_db", "-t", "-A", "-c",
             f"SELECT concept_keys FROM curriculums WHERE domain='en' AND niveau='{lvl}';"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        out[lvl] = json.loads(raw) if raw else []
    return out


def _yaml_concepts() -> dict[str, list[str]]:
    y = yaml.safe_load(YAML_PATH.read_text())
    return {lvl: y.get(lvl, {}).get("concept_keys", []) for lvl in LEVELS}


def _propose_weight(concept: str) -> int:
    """Heuristic weight in minutes based on linguistic complexity signals."""
    heavy = ["perfect", "conditional", "subjunctive", "passive",
             "reported", "inversion", "causative", "phrasal",
             "gerund_vs_infinitive", "relative_clauses_complex",
             "emphatic", "cleft", "idiom"]
    light = ["pronouns", "articles", "plural", "numbers",
             "demonstratives", "imperative", "question_tags",
             "frequency", "cardinal", "ordinal", "short_answers"]
    low = concept.lower()
    if any(h in low for h in heavy):
        return 8
    if any(l in low for l in light):
        return 3
    return 5


def _propose_group(concept: str) -> str:
    """Heuristic group assignment."""
    low = concept.lower()
    if any(v in low for v in ["to_be", "to_have", "present_simple", "present_continuous",
                               "past_simple", "past_continuous", "past_perfect",
                               "future", "present_perfect", "subjunctive", "modal",
                               "conditional", "passive", "reported"]):
        return "verb_tenses"
    if any(n in low for n in ["plural", "article", "noun", "demonstrative", "possessive"]):
        return "nouns_articles"
    if any(p in low for p in ["pronoun"]):
        return "pronouns"
    if any(p in low for p in ["prepositions", "conjunctions"]):
        return "connectors"
    if any(q in low for q in ["question", "wh_", "inversion"]):
        return "questions"
    if any(c in low for c in ["comparative", "superlative", "adjective", "adverb"]):
        return "modifiers"
    if any(c in low for c in ["relative_clause"]):
        return "relative_clauses"
    if any(c in low for c in ["phrasal", "idiom", "collocation", "false_friend", "lex"]):
        return "vocabulary"
    if any(c in low for c in ["register", "discourse"]):
        return "discourse"
    return "misc"


def main() -> int:
    db = _db_concepts()
    ym = _yaml_concepts()

    lines = [
        "# curriculum_en.yaml drift proposal",
        "",
        f"_Generated from DB `curriculums` table (98 total concepts) vs "
        f"`packages/academie-core/.../curriculum_en.yaml` (53 total)._",
        "",
        "## TL;DR",
        "",
        "The drift is not just additive — the two sources use **different naming conventions** for similar concepts :",
        "- YAML uses `present_simple_basic` ; DB uses `to_be_forms` + `to_have_got` + `present_simple` (3 granular concepts)",
        "- YAML uses `personal_pronouns` ; DB uses `subject_pronouns` + `object_pronouns` (split by function)",
        "- etc.",
        "",
        "So merging requires deciding per-concept whether to :",
        "- **adopt** the DB name (more granular, aligned with error_log taxonomy)",
        "- **keep** the YAML name (simpler, aggregated)",
        "- **add both** (DB in YAML + keep YAML alias as aggregate)",
        "",
        "## Summary",
        "",
        "| Level | DB | YAML | In DB not YAML | In YAML not DB |",
        "|---|---|---|---|---|",
    ]
    total_new = 0
    per_level_new: dict[str, list[str]] = {}
    per_level_yaml_only: dict[str, list[str]] = {}
    for lvl in LEVELS:
        db_set = set(db[lvl])
        yml_set = set(ym[lvl])
        missing = sorted(db_set - yml_set)
        yaml_only = sorted(yml_set - db_set)
        per_level_new[lvl] = missing
        per_level_yaml_only[lvl] = yaml_only
        total_new += len(missing)
        lines.append(f"| {lvl} | {len(db[lvl])} | {len(ym[lvl])} | {len(missing)} | {len(yaml_only)} |")
    lines.append(f"| **Total** | **98** | **53** | **{total_new}** | **{sum(len(v) for v in per_level_yaml_only.values())}** |")
    lines.append("")
    lines.append("## Per-level proposal")
    lines.append("")
    lines.append("For each missing concept, the script proposes a weight (min) and a group "
                 "based on heuristics. **Sinse validates/overrides each row.**")
    lines.append("")

    for lvl in LEVELS:
        missing = per_level_new[lvl]
        yaml_only = per_level_yaml_only[lvl]
        if not missing and not yaml_only:
            lines.append(f"### {lvl} — no drift")
            lines.append("")
            continue

        lines.append(f"### {lvl}")
        lines.append("")

        if missing:
            lines.append(f"#### DB-only — {len(missing)} concepts (add to YAML?)")
            lines.append("")
            lines.append("| Concept | Proposed weight | Proposed group | Action |")
            lines.append("|---|---|---|---|")
            for c in missing:
                w = _propose_weight(c)
                g = _propose_group(c)
                lines.append(f"| `{c}` | {w} | `{g}` | |")
            lines.append("")
            lines.append("_Action legend : `ADD` = integrate as-is / `ADD-RENAME=xxx` = add with different key / `DROP` = DB value was bad, remove from DB_")
            lines.append("")

        if yaml_only:
            lines.append(f"#### YAML-only — {len(yaml_only)} concepts (remove from YAML?)")
            lines.append("")
            lines.append("| Concept | Action |")
            lines.append("|---|---|")
            for c in yaml_only:
                lines.append(f"| `{c}` | |")
            lines.append("")
            lines.append("_Action legend : `KEEP` = YAML canonical / `REPLACE-BY=xxx` = superseded by a DB concept / `DROP` = obsolete_")
            lines.append("")

    lines.append("## What to do")
    lines.append("")
    lines.append("1. Review each row. Mark `✅` keep, `❌` drop. If keep, correct weight/group if my heuristic guess is wrong.")
    lines.append("2. Run `python3 scripts/sprint6/19_curriculum_en_merge_apply.py --manual /tmp/curriculum_en_review.md` (Session 42) to merge your corrections into curriculum_en.yaml.")
    lines.append("3. Re-run `pytest packages/academie-core/tests/test_yaml_schema.py` — must pass.")
    lines.append("4. Run `python3 scripts/inject_curriculum.py --domain en --force` to push to DB.")
    lines.append("5. Commit `[data] Session X — curriculum_en.yaml drift merged (XX new concepts from DB)`.")

    OUT_PATH.write_text("\n".join(lines))
    print(f"▶ Proposal written : {OUT_PATH}")
    print(f"▶ Total new concepts : {total_new} across {len([l for l in LEVELS if per_level_new[l]])} levels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
