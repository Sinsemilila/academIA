#!/usr/bin/env python3
"""
Phase 1b — Synthetic error detection test suite
Generates conversations with intentional errors for all 15 Tier 1 categories.
Runs them through the /internal/analyze-errors endpoint.
Reports precision/recall per category.
"""

import json
import requests
import time
from collections import defaultdict

ENDPOINT = "http://localhost:8000/internal/analyze-errors"

# ══════════════════════════════════════════════════════════════
# TEST CASES: (turn_text, expected_codes)
# Each test case is a user utterance with known errors.
# expected_codes = list of error codes that SHOULD be detected.
# ══════════════════════════════════════════════════════════════

TEST_CASES = [
    # ── V:TENSE (5 cases) ──
    ("I have been to Japan last summer", ["V:TENSE"]),
    ("I lived in Paris since 5 years", ["V:TENSE", "PREP:CALQUE"]),
    ("I already visited Paris three times", ["V:TENSE"]),
    ("Yesterday I have eaten a pizza", ["V:TENSE"]),
    ("When I was young I have played football every day", ["V:TENSE"]),

    # ── V:SVA (3 cases) ──
    ("She have a beautiful car", ["V:SVA"]),
    ("My friends was very happy to see me", ["V:SVA"]),
    ("The team are working hard on this project", ["V:SVA"]),

    # ── V:FORM (3 cases) ──
    ("I enjoy to swim in the ocean", ["V:FORM"]),
    ("After to eat dinner we went for a walk", ["V:FORM"]),
    ("I look forward to meet you next week", ["V:FORM"]),

    # ── N:NUM (4 cases) ──
    ("I need to buy many furniture for my new house", ["N:NUM"]),
    ("She gave me a lot of good advices", ["N:NUM"]),
    ("Another pros would be managing your own time", ["N:NUM"]),
    ("I want to make some gift for my friends", ["N:NUM"]),

    # ── ART (3 cases) ──
    ("I bought car yesterday at the dealership", ["ART"]),
    ("The life is beautiful when you travel", ["ART"]),
    ("I like the music very much especially rock", ["ART"]),

    # ── PREP (3 cases) ──
    ("I arrived to London at 5 in the morning", ["PREP"]),
    ("She is good in mathematics and science", ["PREP"]),
    ("We discussed about the new project yesterday", ["PREP"]),

    # ── WO (2 cases) ──
    ("I very much like this restaurant near my house", ["WO"]),
    ("He drives always too fast on the highway", ["WO"]),

    # ── ORTH:CASE (3 cases) ──
    ("i went to the store and bought some milk", ["ORTH:CASE"]),
    ("last monday i visited my grandmother in lyon", ["ORTH:CASE"]),
    ("we traveled to japan and china last summer", ["ORTH:CASE"]),

    # ── ORTH:SPACE (3 cases) ──
    ("My friend is a good cook aswell as a great singer", ["ORTH:SPACE"]),
    ("I have alot of work to do before the weekend", ["ORTH:SPACE"]),
    ("She was tired but she came to the party atleast", ["ORTH:SPACE"]),

    # ── SPELL (3 cases) ──
    ("I dont know wether or not I should go there", ["SPELL", "PUNCT:APOST"]),
    ("She recieved a beautifull gift from her friend", ["SPELL"]),
    ("The goverment should take more responsability", ["SPELL"]),

    # ── PUNCT:APOST (3 cases) ──
    ("Its the best restaurant in the city", ["PUNCT:APOST"]),
    ("I dont think thats a good idea for us", ["PUNCT:APOST"]),
    ("Shes been working here for five years now", ["PUNCT:APOST"]),

    # ── LEX:CHOICE (3 cases) ──
    ("I was traveling along Europe for three months", ["LEX:CHOICE"]),
    ("Can you say me what time the movie starts", ["LEX:CHOICE"]),
    ("I made a big travel to South America last year", ["LEX:CHOICE"]),

    # ── LEX:CALQUE (4 cases) ──
    ("It makes three years that I work here now", ["LEX:CALQUE"]),
    ("I have 25 years and I live in Paris", ["LEX:CALQUE"]),
    ("I want to profit of this beautiful weather today", ["LEX:CALQUE"]),
    ("She opened the light because it was too dark", ["LEX:CALQUE"]),

    # ── PREP:CALQUE (4 cases) ──
    ("It depends of the weather if we go outside", ["PREP:CALQUE"]),
    ("I am very interested by this new technology", ["PREP:CALQUE"]),
    ("She is married with a famous musician", ["PREP:CALQUE"]),
    ("He is good in cooking Italian food at home", ["PREP:CALQUE"]),

    # ── SPELL:COGNATE (3 cases) ──
    ("I need more confort in my new appartment", ["SPELL:COGNATE"]),
    ("Please send the documents to my adress", ["SPELL:COGNATE"]),
    ("The gouvernment made an important developement", ["SPELL:COGNATE"]),

    # ── Multi-error sentences (5 cases) ──
    ("i have went to the store for informations yesterday", ["ORTH:CASE", "V:TENSE", "N:NUM"]),
    ("Its alot of work but i think its worth it", ["PUNCT:APOST", "ORTH:SPACE", "ORTH:CASE"]),
    ("She depend of her parents and live in paris since 3 years", ["PREP:CALQUE", "V:SVA", "ORTH:CASE", "V:TENSE"]),
    ("I have 30 years and i work here since five years", ["LEX:CALQUE", "ORTH:CASE", "PREP:CALQUE"]),
    ("My friend dont know wether he should go in england", ["PUNCT:APOST", "SPELL", "PREP", "ORTH:CASE"]),
]


def build_transcript(cases: list[tuple[str, list[str]]], batch_start: int = 0) -> str:
    """Build a fake transcript from test cases."""
    lines = []
    for i, (text, _) in enumerate(cases):
        turn = batch_start + i + 1
        lines.append(f"--- Turn {turn} ---")
        lines.append(f"USER: {text}")
        lines.append(f"TEACHER: Good try! Let me help you with that.")
        lines.append("")
    return "\n".join(lines)


def run_test(cases: list[tuple[str, list[str]]], batch_name: str, session_suffix: str):
    """Run a batch of test cases through the endpoint."""
    transcript = build_transcript(cases)
    payload = {
        "username": "sinse",
        "session_id": f"phase1b-{session_suffix}",
        "transcript": transcript,
    }
    try:
        r = requests.post(ENDPOINT, json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [ERR] {batch_name}: {e}")
        return None


def analyze_results(cases, session_suffix):
    """Query DB and compare detected vs expected."""
    import subprocess
    sql = f"""SELECT turn_number, error_code, analysis_model, original_text
              FROM error_log
              WHERE session_id = 'phase1b-{session_suffix}'
              ORDER BY turn_number, error_code;"""
    r = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-A", "-F", "|||", "-c", sql],
        capture_output=True, text=True
    )
    rows = [line.split("|||") for line in r.stdout.strip().split("\n") if line.strip()]

    # Build detected map: turn -> set of codes
    detected_by_turn = defaultdict(set)
    detected_models = defaultdict(list)
    for row in rows:
        if len(row) >= 3:
            turn = int(row[0]) if row[0] else 0
            code = row[1]
            model = row[2]
            detected_by_turn[turn].add(code)
            detected_models[turn].append((code, model))

    # Compare with expected
    per_category = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    total_tp = 0
    total_fn = 0
    total_fp = 0
    details = []

    for i, (text, expected_codes) in enumerate(cases):
        turn = i + 1
        detected = detected_by_turn.get(turn, set())
        expected = set(expected_codes)

        tp = detected & expected
        fn = expected - detected
        fp = detected - expected

        total_tp += len(tp)
        total_fn += len(fn)
        total_fp += len(fp)

        for code in tp:
            per_category[code]["tp"] += 1
        for code in fn:
            per_category[code]["fn"] += 1
        for code in fp:
            per_category[code]["fp"] += 1

        status = "✅" if not fn and not fp else ("⚠️" if tp else "❌")
        if fn or fp:
            detail = f"  {status} T{turn}: \"{text[:60]}...\""
            if fn:
                detail += f"\n     MISSED: {', '.join(sorted(fn))}"
            if fp:
                detail += f"\n     FALSE+: {', '.join(sorted(fp))}"
            details.append(detail)

    return per_category, total_tp, total_fn, total_fp, details


def print_report(per_category, total_tp, total_fn, total_fp, details):
    """Print the scorecard."""
    print("\n" + "=" * 60)
    print("PHASE 1b — ERROR TAXONOMY SCORECARD")
    print("=" * 60)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nOverall: TP={total_tp} FN={total_fn} FP={total_fp}")
    print(f"Precision: {precision:.0%}  Recall: {recall:.0%}  F1: {f1:.0%}")

    print(f"\n{'Category':<16} {'TP':>3} {'FN':>3} {'FP':>3} {'Prec':>6} {'Rec':>6}")
    print("-" * 48)

    all_cats = sorted(set(list(per_category.keys()) +
        ["V:TENSE", "V:SVA", "V:FORM", "N:NUM", "ART", "PREP", "WO",
         "ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST",
         "LEX:CHOICE", "LEX:CALQUE", "PREP:CALQUE", "SPELL:COGNATE"]))

    for cat in all_cats:
        d = per_category.get(cat, {"tp": 0, "fn": 0, "fp": 0})
        p = d["tp"] / (d["tp"] + d["fp"]) if (d["tp"] + d["fp"]) > 0 else 0
        r = d["tp"] / (d["tp"] + d["fn"]) if (d["tp"] + d["fn"]) > 0 else 0
        icon = "✅" if r >= 0.7 else ("⚠️" if r >= 0.4 else "❌")
        print(f"{icon} {cat:<14} {d['tp']:>3} {d['fn']:>3} {d['fp']:>3} {p:>5.0%} {r:>5.0%}")

    if details:
        print(f"\n{'─' * 60}")
        print("ISSUES:")
        for d in details:
            print(d)


if __name__ == "__main__":
    # Clean previous test data
    import subprocess
    subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-c", "DELETE FROM error_log WHERE session_id LIKE 'phase1b-%';"],
        capture_output=True
    )

    # Split into batches to avoid token limits
    BATCH_SIZE = 12
    batches = []
    for i in range(0, len(TEST_CASES), BATCH_SIZE):
        batches.append(TEST_CASES[i:i + BATCH_SIZE])

    print(f"Running {len(TEST_CASES)} test cases in {len(batches)} batches...")

    for bi, batch in enumerate(batches):
        suffix = f"batch{bi}"
        print(f"\n  Batch {bi + 1}/{len(batches)} ({len(batch)} cases)...", end=" ", flush=True)
        result = run_test(batch, f"Batch {bi + 1}", suffix)
        if result:
            print(f"→ {result['errors_detected']} errors (rules={result['rule_errors']}, llm={result['llm_errors']})")
        time.sleep(15)  # Groq free tier via LiteLLM: needs spacing to avoid cooldown cascade

    # Analyze all batches together
    all_per_cat = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    all_tp = all_fn = all_fp = 0
    all_details = []

    for bi, batch in enumerate(batches):
        suffix = f"batch{bi}"
        per_cat, tp, fn, fp, details = analyze_results(batch, suffix)
        all_tp += tp
        all_fn += fn
        all_fp += fp
        all_details.extend(details)
        for cat, counts in per_cat.items():
            all_per_cat[cat]["tp"] += counts["tp"]
            all_per_cat[cat]["fn"] += counts["fn"]
            all_per_cat[cat]["fp"] += counts["fp"]

    print_report(all_per_cat, all_tp, all_fn, all_fp, all_details)
