#!/usr/bin/env python3
"""Phase A audit — measure prompt-caching potential on llm_session Teacher/Maestro.

For each Dify app :
  1. Fetch the live system prompt template from workflows.graph
  2. Split it into literal segments + placeholder slots ({{#code_turn_check.X#}})
  3. Classify each segment STABLE / SEMI / VOLATILE
  4. Estimate tokens per segment :
      - literal text : tiktoken o200k_base direct
      - placeholder : realistic value size (loaded or proxy)
  5. Report :
      - Total prompt tokens
      - Current cacheable prefix (contiguous from byte 0 until first VOLATILE)
      - Optimal cacheable prefix (if reordered : all STABLE + SEMI)
      - $ saving per 2100-turn month at gpt-4o-mini prices

No mutation — read-only audit.

Run : docker exec academie-api python3 /tmp/12_audit_prompt_caching.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import tiktoken

ENCODER = tiktoken.get_encoding("o200k_base")


def tk(text: str) -> int:
    return len(ENCODER.encode(text)) if text else 0


# Classification of each placeholder seen in the llm_session template.
#   STABLE = doesn't vary across consecutive turns for the same user
#   SEMI   = changes occasionally (e.g., across CEFR consolidation)
#   VOLATILE = changes every turn
PLACEHOLDER_CLASS = {
    "code_turn_check.learner_profile_summary": "VOLATILE",  # scaffolding appended w/ priority+microlesson
    "code_turn_check.plan_prefix": "VOLATILE",
    "code_turn_check.lang_target_prof": "STABLE",
    "code_turn_check.rubric_for_level": "SEMI",  # changes only on level shift
    "code_profil_check.profil_text": "SEMI",
    "conversation.session_snapshot": "VOLATILE",
    "code_turn_check.error_feedback": "VOLATILE",
    "code_turn_check.tour": "VOLATILE",
    "code_turn_check.dosage_block": "VOLATILE",
    "code_turn_check.selected_concepts": "SEMI",
    "code_turn_check.focus_concept": "VOLATILE",
    "code_turn_check.focus_mode": "VOLATILE",
    "code_turn_check.transition_instruction": "VOLATILE",
    "code_turn_check.level_reminder_inject": "VOLATILE",
    "code_turn_check.drift_validation_request": "VOLATILE",
    "code_turn_check.l1_watch": "SEMI",
    "code_turn_check.spaced_retrieval_today": "VOLATILE",
    "code_turn_check.turn_response_secs": "VOLATILE",
    "code_turn_check.repeated_errors": "VOLATILE",
    "code_turn_check.fewshots_block": "SEMI",
    "code_turn_check.output_schema_block": "STABLE",
    "code_turn_check.promotion_msg": "VOLATILE",
    "code_turn_check.lang_target_name": "STABLE",
}

# Realistic token budgets per placeholder, sourced from live YAMLs / measurements
# (2025-Q2 sample of 474 Teacher + 43 Maestro messages).
PLACEHOLDER_TOKEN_EST = {
    "code_turn_check.learner_profile_summary": 500,  # profile + scaffolding + priority + micro_lesson
    "code_turn_check.plan_prefix": 20,
    "code_turn_check.lang_target_prof": 4,
    "code_turn_check.rubric_for_level": 600,
    "code_profil_check.profil_text": 250,
    "conversation.session_snapshot": 100,
    "code_turn_check.error_feedback": 80,
    "code_turn_check.tour": 4,
    "code_turn_check.dosage_block": 180,
    "code_turn_check.selected_concepts": 30,
    "code_turn_check.focus_concept": 15,
    "code_turn_check.focus_mode": 6,
    "code_turn_check.transition_instruction": 40,
    "code_turn_check.level_reminder_inject": 60,  # 0 most turns, 200 on multiples of 5
    "code_turn_check.drift_validation_request": 30,
    "code_turn_check.l1_watch": 120,
    "code_turn_check.spaced_retrieval_today": 70,
    "code_turn_check.turn_response_secs": 4,
    "code_turn_check.repeated_errors": 20,
    "code_turn_check.fewshots_block": 500,
    "code_turn_check.output_schema_block": 380,
    "code_turn_check.promotion_msg": 10,
    "code_turn_check.lang_target_name": 3,
}

PLACEHOLDER_RE = re.compile(r"\{\{#([a-zA-Z_0-9.]+)#\}\}")


def fetch_template(workflow_id: str) -> str:
    """Pull llm_session system prompt text.

    Prefer a pre-fetched file at /tmp/prompt_tpl_{id}.txt (host path) so the
    script runs equally inside the container (which has no docker CLI).
    Fallback to docker exec for host invocation.
    """
    cached = Path(f"/tmp/prompt_tpl_{workflow_id}.txt")
    if cached.exists():
        return cached.read_text()
    sql = f"""
    SELECT n->'data'->'prompt_template'->0->>'text'
    FROM workflows, jsonb_array_elements(graph::jsonb->'nodes') n
    WHERE id='{workflow_id}' AND n->'data'->>'type'='llm'
      AND n->'data'->>'title' ~* 'session';
    """
    out = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d",
         "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout
    return out.strip()


def split_segments(template: str) -> list[tuple[str, str]]:
    """Return [(kind, content)] where kind is 'text' or 'placeholder'."""
    segments = []
    pos = 0
    for m in PLACEHOLDER_RE.finditer(template):
        if m.start() > pos:
            segments.append(("text", template[pos:m.start()]))
        segments.append(("placeholder", m.group(1)))
        pos = m.end()
    if pos < len(template):
        segments.append(("text", template[pos:]))
    return segments


def classify(seg_kind: str, seg_content: str) -> str:
    if seg_kind == "text":
        return "STABLE"
    return PLACEHOLDER_CLASS.get(seg_content, "UNKNOWN")


def tokens_for(seg_kind: str, seg_content: str) -> int:
    if seg_kind == "text":
        return tk(seg_content)
    return PLACEHOLDER_TOKEN_EST.get(seg_content, 50)


def analyse(workflow_id: str, label: str) -> dict:
    tpl = fetch_template(workflow_id)
    if not tpl:
        return {"label": label, "error": "template empty"}

    segs = split_segments(tpl)
    rows = []
    current_prefix_tokens = 0
    prefix_broken = False
    total = 0
    stable_total = 0
    for kind, content in segs:
        cls = classify(kind, content)
        toks = tokens_for(kind, content)
        total += toks
        rows.append({
            "kind": kind,
            "content": content[:60].replace("\n", "\\n") if kind == "text" else content,
            "class": cls,
            "tokens": toks,
        })
        # Current cacheable prefix = contiguous STABLE+SEMI from start until first VOLATILE
        if not prefix_broken:
            if cls == "VOLATILE":
                prefix_broken = True
            else:
                current_prefix_tokens += toks
        # Optimal = sum of all STABLE + SEMI tokens (if we reorder)
        if cls in ("STABLE", "SEMI"):
            stable_total += toks

    return {
        "label": label,
        "workflow_id": workflow_id,
        "rows": rows,
        "total_tokens": total,
        "current_cacheable_prefix_tokens": current_prefix_tokens,
        "optimal_cacheable_prefix_tokens": stable_total,
    }


def project_monthly_cost(total: int, cacheable: int, turns_per_month: int = 2100) -> dict:
    """Project monthly cost with given cacheable prefix, at gpt-4o-mini prices.
    Cached input discount : $0.075/M vs $0.15/M normal. Output $0.60/M unchanged.
    """
    uncached_in = total - cacheable
    # Assumption : output ~150 tokens/turn (midpoint Teacher 111 / Maestro 204)
    out_per_turn = 150
    in_cost = (uncached_in * turns_per_month) / 1_000_000 * 0.15
    cached_in_cost = (cacheable * turns_per_month) / 1_000_000 * 0.075
    out_cost = (out_per_turn * turns_per_month) / 1_000_000 * 0.60
    return {
        "in_uncached": round(in_cost, 3),
        "in_cached": round(cached_in_cost, 3),
        "out": round(out_cost, 3),
        "total": round(in_cost + cached_in_cost + out_cost, 3),
    }


def report(result: dict) -> None:
    print(f"\n{'='*70}")
    print(f"  {result['label']} (workflow {result['workflow_id']})")
    print(f"{'='*70}")
    # Segment breakdown
    print(f"{'#':>3} | {'CLASS':<9} | {'TOKENS':>6} | KIND / CONTENT")
    print("-" * 70)
    for i, r in enumerate(result["rows"]):
        label = r["content"] if r["kind"] == "placeholder" else f'"{r["content"]}..."'
        print(f"{i:>3} | {r['class']:<9} | {r['tokens']:>6} | {label}")

    total = result["total_tokens"]
    cur = result["current_cacheable_prefix_tokens"]
    opt = result["optimal_cacheable_prefix_tokens"]
    print("-" * 70)
    print(f"  Total prompt tokens            : {total:>6}")
    print(f"  Current cacheable prefix       : {cur:>6}  ({cur/total*100:5.1f}%)")
    print(f"  Optimal cacheable prefix       : {opt:>6}  ({opt/total*100:5.1f}%)")
    print(f"  Gain potentiel en cache        : +{opt-cur:>5} tokens ({(opt-cur)/total*100:+5.1f} pp)")

    # Cost projection (monthly, 1h/day × 30 days = 2100 turns)
    print("\n  Coût mensuel 1h/jour × 30j (gpt-4o-mini) :")
    for mode_label, cache in [("Sans cache (theorique)", 0),
                              ("Cache actuel", cur),
                              ("Cache optimal", opt)]:
        proj = project_monthly_cost(total, cache)
        print(f"    {mode_label:<25}: ${proj['total']:.3f}  "
              f"(in_uncached=${proj['in_uncached']:.3f}, "
              f"in_cached=${proj['in_cached']:.3f}, "
              f"out=${proj['out']:.3f})")


TARGETS = [
    ("006cba2d-08b0-449c-91ed-0dda79d414ce", "Teacher EN (published)"),
    ("d3df0ef0-a28f-4850-9396-d4d1cf6c0e21", "Maestro ES (published)"),
]


if __name__ == "__main__":
    all_results = []
    for wf_id, label in TARGETS:
        try:
            result = analyse(wf_id, label)
            all_results.append(result)
            report(result)
        except Exception as e:
            print(f"ERROR on {label}: {e}")

    # Write machine-readable JSON for future diffs
    out_path = Path("/tmp/prompt_cache_audit.json")
    out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\nJSON report: {out_path}")
