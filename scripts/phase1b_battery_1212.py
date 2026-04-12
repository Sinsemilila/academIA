#!/usr/bin/env python3
"""
Phase 1b — Full 1212-case battery from fine-tuning training+val data.
Reads /tmp/train_v2.jsonl + /tmp/val_v2.jsonl, sends through API, measures F1.
"""

import json
import re
import requests
import subprocess
import time
from collections import defaultdict

ENDPOINT = "http://localhost:8000/internal/analyze-errors"
BATCH_SIZE = 12


def load_cases(path):
    """Load JSONL fine-tuning data → list of (text, [expected_codes])."""
    cases = []
    with open(path) as f:
        for line in f:
            row = json.loads(line)
            msgs = row["messages"]
            # Extract USER text from user message
            user_msg = msgs[1]["content"]
            match = re.search(r"USER: (.+?)(?:\n|$)", user_msg)
            if not match:
                continue
            text = match.group(1).strip()
            # Extract expected codes from assistant response
            assistant_content = msgs[2]["content"]
            try:
                parsed = json.loads(assistant_content)
                codes = set()
                for err in parsed.get("errors", []):
                    for c in err.get("codes", []):
                        codes.add(c)
                if codes:
                    cases.append((text, sorted(codes)))
            except json.JSONDecodeError:
                continue
    return cases


def build_transcript(cases):
    lines = []
    for i, (text, _) in enumerate(cases):
        turn = i + 1
        lines.append(f"--- Turn {turn} ---")
        lines.append(f"USER: {text}")
        lines.append(f"TEACHER: Good try! Let me explain.")
        lines.append("")
    return "\n".join(lines)


def run_batch(cases, batch_id):
    transcript = build_transcript(cases)
    payload = {"username": "sinse", "session_id": f"phase1b-1212-batch{batch_id}", "transcript": transcript}
    try:
        start = time.time()
        r = requests.post(ENDPOINT, json=payload, timeout=60)
        elapsed = time.time() - start
        r.raise_for_status()
        result = r.json()
        return result, elapsed
    except requests.exceptions.Timeout:
        return "TIMEOUT", 0
    except Exception as e:
        return f"ERR: {e}", 0


def analyze_batch(cases, batch_id):
    sql = f"""SELECT turn_number, error_code
              FROM error_log WHERE session_id = 'phase1b-1212-batch{batch_id}'
              ORDER BY turn_number, error_code;"""
    r = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-A", "-F", "|||", "-c", sql],
        capture_output=True, text=True
    )
    detected_by_turn = defaultdict(set)
    for line in r.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("|||")
        if len(parts) >= 2:
            turn = int(parts[0]) if parts[0] else 0
            detected_by_turn[turn].add(parts[1])
    return detected_by_turn


def main():
    # Load all cases
    train_cases = load_cases("/tmp/train_v2.jsonl")
    val_cases = load_cases("/tmp/val_v2.jsonl")
    all_cases = train_cases + val_cases
    print(f"Loaded {len(train_cases)} train + {len(val_cases)} val = {len(all_cases)} total cases\n")

    # Clean old results
    subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-c", "DELETE FROM error_log WHERE session_id LIKE 'phase1b-1212-%';"],
        capture_output=True
    )

    # Run in batches
    batches = [all_cases[i:i+BATCH_SIZE] for i in range(0, len(all_cases), BATCH_SIZE)]
    print(f"Running {len(all_cases)} cases in {len(batches)} batches...\n")

    completed = 0
    aborted = False
    for bi, batch in enumerate(batches):
        print(f"  Batch {bi+1}/{len(batches)} ({len(batch)} cases)...", end=" ", flush=True)
        result, elapsed = run_batch(batch, bi)
        if isinstance(result, str):
            print(f"→ {result} [{elapsed:.0f}s]")
            if "TIMEOUT" in str(result):
                aborted = True
                break
        else:
            print(f"→ {result['errors_detected']} errors [{elapsed:.0f}s]")
            completed += 1

    print(f"\nCompleted {completed}/{len(batches)} batches\n")

    # Analyze all results
    per_cat = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    total_tp = total_fn = total_fp = 0
    issues = []
    case_offset = 0

    for bi, batch in enumerate(batches):
        detected_map = analyze_batch(batch, bi)
        for i, (text, expected_codes) in enumerate(batch):
            turn = i + 1
            detected = detected_map.get(turn, set())
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
                d = f"  {'⚠️' if tp else '❌'} #{case_offset+i+1}: \"{text[:60]}...\""
                if fn: d += f"\n     MISSED: {', '.join(sorted(fn))}"
                if fp: d += f"\n     FALSE+: {', '.join(sorted(fp))}"
                issues.append(d)
        case_offset += len(batch)

    # Report
    prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

    print("=" * 60)
    print(f"FULL 1212-CASE BATTERY — FINE-TUNE v2")
    print("=" * 60)
    print(f"\nOverall: TP={total_tp} FN={total_fn} FP={total_fp}")
    print(f"Precision: {prec:.0%}  Recall: {rec:.0%}  F1: {f1:.0%}")

    # Per-category sorted by recall
    cats = sorted(per_cat.keys())
    ok = sum(1 for c in cats if per_cat[c]["tp"] / (per_cat[c]["tp"] + per_cat[c]["fn"]) >= 0.7 if (per_cat[c]["tp"] + per_cat[c]["fn"]) > 0)
    bad = sum(1 for c in cats if per_cat[c]["tp"] / (per_cat[c]["tp"] + per_cat[c]["fn"]) < 0.4 if (per_cat[c]["tp"] + per_cat[c]["fn"]) > 0)
    print(f"\nCategories >=70% recall: {ok}/{len(cats)}")
    print(f"Categories <40% recall: {bad}/{len(cats)}")

    print(f"\n{'Category':<18} {'TP':>4} {'FN':>4} {'FP':>4} {'Prec':>6} {'Rec':>6}")
    print("-" * 52)
    for cat in cats:
        d = per_cat[cat]
        p = d["tp"] / (d["tp"] + d["fp"]) if (d["tp"] + d["fp"]) > 0 else 0
        r = d["tp"] / (d["tp"] + d["fn"]) if (d["tp"] + d["fn"]) > 0 else 0
        icon = "✅" if r >= 0.7 else ("⚠️" if r >= 0.4 else "❌")
        print(f"{icon} {cat:<16} {d['tp']:>4} {d['fn']:>4} {d['fp']:>4} {p:>5.0%} {r:>5.0%}")

    print(f"\nIssues: {len(issues)} (showing first 30)")
    for d in issues[:30]:
        print(d)
    if len(issues) > 30:
        print(f"  ... and {len(issues)-30} more")


if __name__ == "__main__":
    main()
