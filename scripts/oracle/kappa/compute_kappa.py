"""Compute pairwise Cohen's κ across 6 LLM judges on κ calibration set.

Judges :
  - claude                (Anthropic, via human-typed here)
  - gemini_pro_web        (Google, user paste web chat)
  - chatgpt_free_web      (OpenAI, user paste web chat)
  - gpt4omini             (OpenAI via LiteLLM — current Oracle judge)
  - groq_llama70b         (Meta, via LiteLLM groq-standard)
  - mistral_small         (Mistral, via LiteLLM)

Produces :
  - pairwise κ matrix per dim (cf_move_set_valid, register_cefr_alignment)
  - majority-vote per scenario (proxy ground truth)
  - per-dim summary: how each judge agrees with majority
  - actionable read: which dims are robust, which are subjective
"""
from __future__ import annotations

import json
from pathlib import Path
from itertools import combinations
from collections import Counter

DIR = Path(__file__).parent
DIMS = ["cf_move_set_valid", "register_cefr_alignment"]
JUDGES = {
    "claude":             "scores_claude.json",
    "gemini_pro":         "scores_gemini_pro_web.json",
    "gemini_flash":       "scores_gemini_flash_litellm.json",
    "chatgpt":            "scores_chatgpt_free_web.json",
    "gpt4o_mini":         "scores_gpt4omini.json",
    "groq_llama70b":      "scores_groq_llama70b.json",
    "mistral_small":      "scores_mistral_small.json",
}


def load(judge: str) -> dict[str, dict[str, str]]:
    """Return {scenario_id → {dim → verdict}}."""
    raw = json.loads((DIR / JUDGES[judge]).read_text())
    out = {}
    for item in raw.get("scores", []):
        sid = item["scenario_id"]
        out[sid] = {d: item.get(d, "?") for d in DIMS}
    return out


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's κ for two same-length verdict lists over {pass, fail}."""
    assert len(a) == len(b)
    n = len(a)
    if n == 0:
        return float("nan")
    # observed agreement
    agree = sum(1 for x, y in zip(a, b) if x == y)
    po = agree / n
    # expected agreement under independence
    labels = {"pass", "fail"}
    pe = 0.0
    for lbl in labels:
        pa = sum(1 for x in a if x == lbl) / n
        pb = sum(1 for x in b if x == lbl) / n
        pe += pa * pb
    if pe == 1.0:
        return float("nan")  # no variance
    return (po - pe) / (1 - pe)


def interpret(k: float) -> str:
    if k != k:  # NaN
        return "undefined (no variance)"
    if k < 0:    return f"{k:+.2f}  negative (worse than chance)"
    if k < 0.20: return f"{k:+.2f}  slight"
    if k < 0.40: return f"{k:+.2f}  fair"
    if k < 0.60: return f"{k:+.2f}  moderate"
    if k < 0.80: return f"{k:+.2f}  substantial ✓"
    return f"{k:+.2f}  almost perfect ★"


# ── Load all judges ──────────────────────────────────────────────────
verdicts = {name: load(name) for name in JUDGES}
scenario_ids = sorted(next(iter(verdicts.values())).keys())
print(f"Loaded {len(verdicts)} judges × {len(scenario_ids)} scenarios × {len(DIMS)} dims\n")

# ── Pairwise κ per dim ───────────────────────────────────────────────
for dim in DIMS:
    print(f"══ {dim} ══")
    names = list(JUDGES.keys())
    for a, b in combinations(names, 2):
        va = [verdicts[a][sid][dim] for sid in scenario_ids]
        vb = [verdicts[b][sid][dim] for sid in scenario_ids]
        k = cohen_kappa(va, vb)
        print(f"  {a:<15} ↔ {b:<15}  κ = {interpret(k)}")
    print()

# ── Majority vote proxy ground truth ────────────────────────────────
print("══ Majority vote (6 judges) vs each judge ══")
for dim in DIMS:
    print(f"\n  [{dim}]")
    majority = {}
    for sid in scenario_ids:
        c = Counter(verdicts[name][sid][dim] for name in JUDGES)
        majority[sid], _ = c.most_common(1)[0]
    for name in JUDGES:
        mine = [verdicts[name][sid][dim] for sid in scenario_ids]
        mv   = [majority[sid] for sid in scenario_ids]
        k = cohen_kappa(mine, mv)
        print(f"    {name:<15} vs majority  κ = {interpret(k)}")

# ── Per-scenario disagreement heatmap (which scenarios split judges?) ──
print("\n══ Most-contested scenarios (where judges split) ══")
for dim in DIMS:
    print(f"\n  [{dim}]")
    splits = []
    for sid in scenario_ids:
        c = Counter(verdicts[name][sid][dim] for name in JUDGES)
        # contested = minority count / total
        most_common_count = c.most_common(1)[0][1]
        split = len(JUDGES) - most_common_count
        if split >= 2:  # at least 2 dissenting
            splits.append((split, sid, dict(c)))
    splits.sort(reverse=True)
    for split, sid, c in splits[:8]:
        print(f"    {sid:<40} split={split} verdicts={c}")

# ── cf_move_used (what CF move did each judge SEE) ──────────────────
print("\n══ cf_move_used classification consensus ══")
moves_by_scen = {}
for sid in scenario_ids:
    moves = {}
    for name in JUDGES:
        data = json.loads((DIR / JUDGES[name]).read_text())
        for item in data["scores"]:
            if item["scenario_id"] == sid:
                moves[name] = item.get("cf_move_used", "?")
                break
    moves_by_scen[sid] = moves

print("\nScenarios with move disagreement :")
for sid, moves in moves_by_scen.items():
    uniq = set(moves.values())
    if len(uniq) > 1:
        print(f"  {sid:<40} {moves}")
