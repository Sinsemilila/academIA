#!/usr/bin/env python3
"""
Phase 1b v2 — Confirmation battery
New test cases (no overlap with v1) to confirm per-category accuracy.
"""

import json
import requests
import time
import subprocess
from collections import defaultdict

ENDPOINT = "http://localhost:8000/internal/analyze-errors"

TEST_CASES = [
    # ── V:TENSE (5) ──
    ("I have seen him at the party last night", ["V:TENSE"]),
    ("She has lived in London for two years before moving to Paris", ["V:TENSE"]),
    ("We have went to the beach three days ago", ["V:TENSE"]),
    ("I work here since January and I love it", ["V:TENSE", "PREP:CALQUE"]),
    ("He told me he has finished the project yesterday evening", ["V:TENSE"]),

    # ── V:SVA (3) ──
    ("The children plays in the park every afternoon", ["V:SVA"]),
    ("There is many reasons to learn English today", ["V:SVA"]),
    ("Everyone have their own opinion about politics", ["V:SVA"]),

    # ── V:FORM (3) ──
    ("She suggested me to take the train instead", ["V:FORM"]),
    ("I am looking forward to see you next month", ["V:FORM"]),
    ("He avoided to answer the difficult question", ["V:FORM"]),

    # ── N:NUM (4) ──
    ("Can you give me some informations about the hotel", ["N:NUM"]),
    ("I have too many homeworks to finish tonight", ["N:NUM"]),
    ("She bought new furnitures for the living room", ["N:NUM"]),
    ("All the equipments are ready for the presentation", ["N:NUM"]),

    # ── ART (3) ──
    ("I need to go to hospital because I feel sick", ["ART"]),
    ("The happiness is the most important thing in life", ["ART"]),
    ("She plays piano very well since she was young", ["ART"]),

    # ── PREP (3) ──
    ("I will arrive at home before eight tonight", ["PREP"]),
    ("We need to discuss about this problem urgently", ["PREP"]),
    ("She explained me the rules of the game clearly", ["PREP"]),

    # ── WO (4 — extra focus) ──
    ("She speaks very well English after living abroad", ["WO"]),
    ("I always have wanted to visit Japan someday", ["WO"]),
    ("He gave to his mother a beautiful present", ["WO"]),
    ("They were enough tired to go home early", ["WO"]),

    # ── ORTH:CASE (3) ──
    ("my brother moved to london last january for work", ["ORTH:CASE"]),
    ("i think english is easier than french honestly", ["ORTH:CASE"]),
    ("on saturday we visited the eiffel tower in paris", ["ORTH:CASE"]),

    # ── ORTH:SPACE (3) ──
    ("I think this idea is good eventhough its expensive", ["ORTH:SPACE", "PUNCT:APOST"]),
    ("There are noone at the office this morning", ["ORTH:SPACE"]),
    ("We should help eachother more in this team", ["ORTH:SPACE"]),

    # ── SPELL (3) ──
    ("The enviroment needs to be protected urgently", ["SPELL"]),
    ("I would definately recommend this restaurant to you", ["SPELL"]),
    ("His pronounciation has improved alot this semester", ["SPELL", "ORTH:SPACE"]),

    # ── PUNCT:APOST (3) ──
    ("I cant believe hes already left without us", ["PUNCT:APOST"]),
    ("Theyre planning to visit us next weekend hopefully", ["PUNCT:APOST"]),
    ("Whos going to drive if youve been drinking tonight", ["PUNCT:APOST"]),

    # ── LEX:CHOICE (3) ──
    ("She said me that the meeting was cancelled today", ["LEX:CHOICE"]),
    ("I did a long travel across South America last year", ["LEX:CHOICE"]),
    ("He won a lot of money at the lottery last week", ["LEX:CHOICE"]),

    # ── LEX:CHOICE — French calques (4) ──
    ("I have 30 years old and I am a software developer", ["LEX:CHOICE"]),
    ("She closed the television before going to bed tonight", ["LEX:CHOICE"]),
    ("We assisted at a concert in the park last weekend", ["LEX:CHOICE"]),
    ("I passed my driving exam on the first attempt", ["LEX:CHOICE"]),

    # ── PREP:CALQUE (4) ──
    ("My success depends of how hard I work every day", ["PREP:CALQUE"]),
    ("She is responsible of the marketing department here", ["PREP:CALQUE"]),
    ("I am habituated to wake up early every morning", ["PREP:CALQUE"]),
    ("He congratulated me for my new job at the company", ["PREP:CALQUE"]),

    # ── SPELL:COGNATE (4 — extra focus) ──
    ("The appartment is very confortable and well situated", ["SPELL:COGNATE"]),
    ("We need to ameliorate our communication in the team", ["SPELL:COGNATE"]),
    ("She works in a differente departement in the company", ["SPELL:COGNATE"]),
    ("The programme of the conference was very interessant", ["SPELL:COGNATE"]),

    # ── Multi-error (5) ──
    ("i have 25 years and i cant find a good appartment", ["ORTH:CASE", "LEX:CHOICE", "PUNCT:APOST", "SPELL:COGNATE"]),
    ("She have alot of informations about the gouvernment", ["V:SVA", "ORTH:SPACE", "N:NUM", "SPELL:COGNATE"]),
    ("Yesterday i have visited london and it was beautifull", ["ORTH:CASE", "V:TENSE", "SPELL"]),
    ("He depend of his parents since he lost his job", ["V:SVA", "PREP:CALQUE"]),
    ("i enjoy to swim and i always have wanted to travel", ["ORTH:CASE", "V:FORM", "WO"]),
]


def build_transcript(cases, batch_start=0):
    lines = []
    for i, (text, _) in enumerate(cases):
        turn = i + 1
        lines.append(f"--- Turn {turn} ---")
        lines.append(f"USER: {text}")
        lines.append(f"TEACHER: Good try! Let me explain.")
        lines.append("")
    return "\n".join(lines)


def run_test(cases, suffix):
    transcript = build_transcript(cases)
    payload = {"username": "sinse", "session_id": f"phase1b-v2-{suffix}", "transcript": transcript}
    try:
        r = requests.post(ENDPOINT, json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


def analyze_results(cases, suffix):
    sql = f"""SELECT turn_number, error_code, analysis_model
              FROM error_log WHERE session_id = 'phase1b-v2-{suffix}'
              ORDER BY turn_number, error_code;"""
    r = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-A", "-F", "|||", "-c", sql],
        capture_output=True, text=True
    )
    rows = [line.split("|||") for line in r.stdout.strip().split("\n") if line.strip()]
    detected_by_turn = defaultdict(set)
    for row in rows:
        if len(row) >= 2:
            turn = int(row[0]) if row[0] else 0
            detected_by_turn[turn].add(row[1])

    per_cat = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    total_tp = total_fn = total_fp = 0
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
        for c in tp: per_cat[c]["tp"] += 1
        for c in fn: per_cat[c]["fn"] += 1
        for c in fp: per_cat[c]["fp"] += 1
        if fn or fp:
            d = f"  {'⚠️' if tp else '❌'} T{turn}: \"{text[:65]}...\""
            if fn: d += f"\n     MISSED: {', '.join(sorted(fn))}"
            if fp: d += f"\n     FALSE+: {', '.join(sorted(fp))}"
            details.append(d)

    return per_cat, total_tp, total_fn, total_fp, details


def print_report(per_cat, tp, fn, fp, details):
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

    print("\n" + "=" * 60)
    print("PHASE 1b v2 — CONFIRMATION SCORECARD")
    print("=" * 60)
    print(f"\nOverall: TP={tp} FN={fn} FP={fp}")
    print(f"Precision: {prec:.0%}  Recall: {rec:.0%}  F1: {f1:.0%}")

    cats = ["V:TENSE", "V:SVA", "V:FORM", "N:NUM", "ART", "PREP", "WO",
            "ORTH:CASE", "ORTH:SPACE", "SPELL", "PUNCT:APOST",
            "LEX:CHOICE", "PREP:CALQUE", "SPELL:COGNATE"]

    print(f"\n{'Category':<16} {'TP':>3} {'FN':>3} {'FP':>3} {'Prec':>6} {'Rec':>6}")
    print("-" * 48)
    for cat in cats:
        d = per_cat.get(cat, {"tp": 0, "fn": 0, "fp": 0})
        p = d["tp"] / (d["tp"] + d["fp"]) if (d["tp"] + d["fp"]) > 0 else 0
        r = d["tp"] / (d["tp"] + d["fn"]) if (d["tp"] + d["fn"]) > 0 else 0
        icon = "✅" if r >= 0.7 else ("⚠️" if r >= 0.4 else "❌")
        print(f"{icon} {cat:<14} {d['tp']:>3} {d['fn']:>3} {d['fp']:>3} {p:>5.0%} {r:>5.0%}")

    # Any extra codes detected not in our list
    extra = set(per_cat.keys()) - set(cats)
    for cat in sorted(extra):
        d = per_cat[cat]
        print(f"🔵 {cat:<14} {d['tp']:>3} {d['fn']:>3} {d['fp']:>3}  (unexpected)")

    if details:
        print(f"\n{'─' * 60}")
        print("ISSUES:")
        for d in details:
            print(d)


if __name__ == "__main__":
    subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-c", "DELETE FROM error_log WHERE session_id LIKE 'phase1b-v2-%';"],
        capture_output=True
    )

    BATCH_SIZE = 12
    batches = [TEST_CASES[i:i+BATCH_SIZE] for i in range(0, len(TEST_CASES), BATCH_SIZE)]
    print(f"Running {len(TEST_CASES)} NEW test cases in {len(batches)} batches...\n")

    for bi, batch in enumerate(batches):
        print(f"  Batch {bi+1}/{len(batches)} ({len(batch)} cases)...", end=" ", flush=True)
        result = run_test(batch, f"batch{bi}")
        if result:
            print(f"→ {result['errors_detected']} errors (rules={result['rule_errors']}, llm={result['llm_errors']})")
        time.sleep(15)  # Groq free tier via LiteLLM: needs spacing to avoid cooldown cascade

    all_pc = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    all_tp = all_fn = all_fp = 0
    all_det = []
    for bi, batch in enumerate(batches):
        pc, tp, fn, fp, det = analyze_results(batch, f"batch{bi}")
        all_tp += tp; all_fn += fn; all_fp += fp
        all_det.extend(det)
        for c, v in pc.items():
            all_pc[c]["tp"] += v["tp"]; all_pc[c]["fn"] += v["fn"]; all_pc[c]["fp"] += v["fp"]

    print_report(all_pc, all_tp, all_fn, all_fp, all_det)
