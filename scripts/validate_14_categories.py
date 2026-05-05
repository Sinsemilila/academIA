#!/usr/bin/env python3
"""
Validate 14 categories — calls Groq directly (bypasses LiteLLM cooldown).
Tests the diff engine + rules + LLM classification logic in-process.
"""

import sys, os, json, requests, time, re
from collections import defaultdict
from dataclasses import dataclass

# ── Config ──
# Use LiteLLM → ollama-cloud (no rate limit issues)
API_URL = "http://localhost:4000/v1/chat/completions"
API_MODEL = "ollama-cloud"

CORRECTION_SYSTEM = """You correct a French speaker's English. Fix ALL errors: grammar, spelling, capitalization, punctuation, word choice, word order. Minimal changes only. Output: TURN N: corrected text. One line per message. No explanations.
Key French errors: have 25 years→am 25, since 5 years→for 5 years, depend of→on, confort→comfort, have been+last summer→went, dont→don't, i→I, aswell→as well."""

CLASSIFY_SYSTEM = """You classify English learner errors. The learner is French.
Reply with ONLY the code per line.

Codes: V:TENSE V:SVA V:FORM N:NUM ART PREP PREP:CALQUE WO LEX:CHOICE SPELL SPELL:COGNATE ORTH:CASE ORTH:SPACE PUNCT:APOST OTHER"""

# ── Import our rules + differ (add to path) ──
sys.path.insert(0, "/opt/academia/webapp/backend")
from academie_core.taxonomy.differ import extract_edits
from academie_core.taxonomy.rules import classify_edits
from academie_core.taxonomy.categories import TIER1_CATEGORIES

# ── Test cases: 1 per category + 4 multi-error ──
CASES = [
    ("I have been to Japan last summer", ["V:TENSE"]),
    ("She have a beautiful car", ["V:SVA"]),
    ("I enjoy to swim in the ocean", ["V:FORM"]),
    ("Can you give me some informations about the hotel", ["N:NUM"]),
    ("The life is beautiful when you travel", ["ART"]),
    ("I arrived to London at five in the morning", ["PREP"]),
    ("She speaks very well English after living abroad", ["WO"]),
    ("i went to the store and bought some milk", ["ORTH:CASE"]),
    ("She is a good listener aswell as a singer", ["ORTH:SPACE"]),
    ("I would definately recommend this restaurant", ["SPELL"]),
    ("I dont think thats a good idea for us", ["PUNCT:APOST"]),
    ("She said me that the meeting was cancelled", ["LEX:CHOICE"]),
    ("My success depends of how hard I work", ["PREP:CALQUE"]),
    ("I need more confort in my new appartment", ["SPELL:COGNATE"]),
    # Multi-error
    ("i have 25 years and i cant find a good appartment", ["ORTH:CASE", "LEX:CHOICE", "PUNCT:APOST", "SPELL:COGNATE"]),
    ("She have alot of informations about the gouvernment", ["V:SVA", "ORTH:SPACE", "N:NUM", "SPELL:COGNATE"]),
    ("Yesterday i have visited london and it was beautifull", ["ORTH:CASE", "V:TENSE", "SPELL"]),
    ("He depend of his parents since he lost his job", ["V:SVA", "PREP:CALQUE"]),
]


def call_llm(system: str, user: str, max_tokens: int = 500) -> str:
    for attempt in range(3):
        r = requests.post(API_URL, headers={"Content-Type": "application/json"}, json={
            "model": API_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.1,
            "max_tokens": max_tokens
        }, timeout=30)
        if r.status_code == 429:
            wait = min(10 * (attempt + 1), 30)
            print(f"\n    ⏳ Rate limited — waiting {wait}s (attempt {attempt+1}/3)...", end=" ", flush=True)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise Exception("Rate limit — 3 retries exhausted")


def get_corrections(cases):
    """Step 1: Get corrections. Splits into batches of 4 for ollama-cloud compatibility."""
    corrections = {}
    BATCH = 4
    for batch_start in range(0, len(cases), BATCH):
        batch = cases[batch_start:batch_start + BATCH]
        transcript = ""
        for i, (text, _) in enumerate(batch, batch_start + 1):
            transcript += f"--- Turn {i} ---\nUSER: {text}\nTEACHER: Good try!\n\n"

        content = call_llm(CORRECTION_SYSTEM, f"Correct each USER message:\n\n{transcript}")
        content = content.strip().strip('"').strip("'")
        for line in content.strip().split("\n"):
            line = line.strip().strip('"').strip("'")
            if line.upper().startswith("TURN "):
                try:
                    rest = line[5:]
                    colon_idx = rest.index(":")
                    turn_num = int(rest[:colon_idx].strip())
                    corrected = rest[colon_idx + 1:].strip()
                    if corrected:
                        corrections[turn_num] = corrected
                except (ValueError, IndexError):
                    continue
        time.sleep(1)  # courtesy between batches
    return corrections


def classify_batch_groq(spans):
    """Step 4: Batch classify unclassified spans via Groq."""
    if not spans:
        return []
    lines = []
    for i, (orig, corr, ctx) in enumerate(spans, 1):
        lines.append(f'{i}. Wrong: "{orig}" → Correct: "{corr}" (in: "{ctx[:80]}")')

    content = call_llm(CLASSIFY_SYSTEM, "\n".join(lines), max_tokens=200)
    results = [None] * len(spans)
    for line in content.split("\n"):
        m = re.match(r"(\d+)[.\s:]+(\S+)", line.strip())
        if m:
            idx = int(m.group(1)) - 1
            code = m.group(2).strip().rstrip(".")
            if 0 <= idx < len(spans) and code != "OTHER":
                results[idx] = code
    return results


def run_pipeline(cases):
    """Run the full detect-then-classify pipeline."""
    print("Step 1: Groq correction...", end=" ", flush=True)
    t1 = time.time()
    corrections = get_corrections(cases)
    print(f"{time.time()-t1:.1f}s — {len(corrections)} turns corrected")

    all_errors = defaultdict(set)  # turn -> set of codes
    pending_llm = []

    for i, (original, _) in enumerate(cases, 1):
        corrected = corrections.get(i)
        if not corrected or corrected.strip().lower() == original.strip().lower():
            continue

        edits = extract_edits(original, corrected)
        classified, unclassified = classify_edits(edits, original)

        for err in classified:
            if err.error_code in TIER1_CATEGORIES:
                all_errors[i].add(err.error_code)

        for span in unclassified:
            if span.original or span.corrected:
                pending_llm.append((i, span.original, span.corrected, span.context))

    if pending_llm:
        print(f"Step 2-3: Diff+Rules done. {sum(len(v) for v in all_errors.values())} rule detections, {len(pending_llm)} pending LLM")
        print("Step 4: Groq batch classify...", end=" ", flush=True)
        t4 = time.time()
        batch_input = [(orig, corr, ctx) for _, orig, corr, ctx in pending_llm]
        codes = classify_batch_groq(batch_input)
        print(f"{time.time()-t4:.1f}s")
        for (turn, _, _, _), code in zip(pending_llm, codes):
            if code and code in TIER1_CATEGORIES:
                all_errors[turn].add(code)

    return all_errors


def score(cases, detected):
    per_cat = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    tp = fn = fp = 0

    print(f"\n{'#':<3} {'Expected':<16} {'Detected':<24} {'':>3}  Sentence")
    print("-" * 80)

    for i, (text, expected) in enumerate(cases, 1):
        exp = set(expected)
        det = detected.get(i, set())
        hits = det & exp
        misses = exp - det
        extras = det - exp
        tp += len(hits); fn += len(misses); fp += len(extras)
        for c in hits: per_cat[c]["tp"] += 1
        for c in misses: per_cat[c]["fn"] += 1
        for c in extras: per_cat[c]["fp"] += 1

        icon = "✅" if hits and not misses else ("⚠️" if hits else "❌")
        det_str = ", ".join(sorted(det)) or "(none)"
        exp_str = ", ".join(sorted(exp))
        print(f"{i:<3} {exp_str:<16} {det_str:<24} {icon}  {text[:45]}")

    prec = tp/(tp+fp) if tp+fp else 0
    rec = tp/(tp+fn) if tp+fn else 0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0

    print(f"\n{'='*60}")
    print(f"Precision: {prec:.0%}  Recall: {rec:.0%}  F1: {f1:.0%}")
    print(f"TP={tp} FN={fn} FP={fp}")

    cats = sorted(TIER1_CATEGORIES)
    print(f"\n{'Category':<16} {'TP':>3} {'FN':>3} {'FP':>3} {'Prec':>6} {'Rec':>6}")
    print("-" * 48)
    for cat in cats:
        d = per_cat.get(cat, {"tp": 0, "fn": 0, "fp": 0})
        p = d["tp"]/(d["tp"]+d["fp"]) if d["tp"]+d["fp"] else 0
        r = d["tp"]/(d["tp"]+d["fn"]) if d["tp"]+d["fn"] else 0
        icon = "✅" if r >= 0.7 else ("⚠️" if r >= 0.4 else "❌")
        print(f"{icon} {cat:<14} {d['tp']:>3} {d['fn']:>3} {d['fp']:>3} {p:>5.0%} {r:>5.0%}")


if __name__ == "__main__":
    print(f"Validating 14 categories — {len(CASES)} test cases")
    print(f"Model: {API_MODEL} (via LiteLLM)\n")

    total_start = time.time()
    detected = run_pipeline(CASES)
    total = time.time() - total_start
    print(f"\nTotal pipeline: {total:.1f}s")

    score(CASES, detected)
