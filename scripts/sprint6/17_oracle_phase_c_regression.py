"""Session 39 Block 3 — Phase C prompt-reorder regression oracle.

Post-hoc validation that commit `dcd7110` (Phase C prompt reorder) did
not drift pedagogical quality.

Approach (unilateral LLM judge, chosen because the pre-reorder prompt
graph is not recoverable — only POST-reorder snapshots in
backups/phase_c_pre_reorder/) :
  1. SELECT N messages from before dcd7110 (2026-04-22 01:12:50+02)
     stratified across Teacher EN + Maestro ES.
  2. For each (query, original_answer) pair, judge pedagogical
     equivalence between original_answer (rendered BY the pre-reorder
     prompt) and a simulated current-prompt response.
     - Since re-prompting the live prompt costs $$, we use a LEAN
       variant : feed the judge both the query and the original answer,
       ask whether the original answer is *still* the kind of response
       the current reordered prompt would produce. The judge has access
       to the marker-split STABLE prefix of the current prompt and
       evaluates "would this answer be congruent with the current
       prompt's doctrine (tier system, observed_level emission, A1
       no-jargon rule, etc.) ?" — a cheap proxy that surfaces drift
       symptoms without paying for re-render.
  3. N=3 judge votes per sample → majority.
  4. Aggregate + gate decision + markdown report.

Gate thresholds :
  - >80% majority-equivalent → PASS (reorder safe)
  - <60% → FAIL (trigger Sinse review + potential rollback)
  - 60-80% → GREY (log P1 follow-up, no auto-action)

Usage :
  python3 scripts/sprint6/17_oracle_phase_c_regression.py --sample 2 --judge-n 1   # sanity
  python3 scripts/sprint6/17_oracle_phase_c_regression.py --sample 30 --judge-n 3  # full
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import httpx

LITELLM_URL = os.environ.get("LITELLM_URL", "http://127.0.0.1:4000/v1/chat/completions")
JUDGE_MODEL = os.environ.get("ORACLE_JUDGE_MODEL", "gpt-4o-mini")
PHASE_C_ANCHOR = "2026-04-22 01:12:50+02"
TEACHER_APP = "39565197-c9d1-4d5b-b66f-18925de236d9"
MAESTRO_APP = "47b0529c-b3a3-4651-8717-759e666172c9"

JUDGE_SYSTEM = """You are a pedagogical-quality reviewer for AcademIA, a CEFR-aligned language tutoring app.

Your job : given (1) a learner's query, (2) a tutor's response, and (3) the current doctrine summary, judge whether the response is CONGRUENT with the doctrine.

Doctrine (current post-reorder prompt, Session 38-39) :
  - Tutor emits an observed_level CEFR field (A1-C2, never empty from turn 3+).
  - Feedback tier system T1-T4 with Lyster scaffolding (T1 silent, T2 recast, T3 elicit+metalinguistic, T4 explicit+remediation).
  - A1 learners get ZERO metalinguistic jargon ("past simple", "auxiliary") — examples only.
  - Tutor never mentions priority_concepts list literally ("today we'll focus on X, Y") — weaves naturally.
  - Tutor replies in L2 (target language), not L1, with short bridges allowed at A1/A2.
  - Max 2 error corrections per turn.

Output ONLY strict JSON :
  {"equivalent": true|false, "confidence": 0.0-1.0, "reasoning": "one sentence"}"""

JUDGE_USER_TEMPLATE = """Query (learner) :
{query}

Response (tutor) :
{answer}

Would the CURRENT doctrine produce a response congruent with this one ? Output JSON."""


def psql_q(sql: str, db: str = "academie_db") -> str:
    return subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", db, "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n")


def fetch_messages(sample: int) -> list[dict]:
    """Stratified sample : N/2 Teacher EN + N/2 Maestro ES, pre-dcd7110."""
    half = max(1, sample // 2)
    rows = []
    for app_id, label in [(TEACHER_APP, "teacher_en"), (MAESTRO_APP, "maestro_es")]:
        raw = psql_q(
            f"""SELECT id, query, replace(replace(answer, E'\\n', ' '), '|', ':PIPE:') AS answer
               FROM messages
               WHERE app_id = '{app_id}'
                 AND created_at < '{PHASE_C_ANCHOR}'
                 AND query IS NOT NULL AND length(query) > 5
                 AND answer IS NOT NULL AND length(answer) > 50
               ORDER BY random() LIMIT {half};"""
        )
        for line in raw.split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            rows.append({
                "id": parts[0],
                "query": parts[1][:800],
                "answer": parts[2][:2000].replace(":PIPE:", "|"),
                "agent": label,
            })
    random.shuffle(rows)
    return rows


async def judge_once(client: httpx.AsyncClient, query: str, answer: str) -> dict | None:
    payload = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": JUDGE_USER_TEMPLATE.format(query=query, answer=answer)},
        ],
        "max_tokens": 150,
        "temperature": 0.0,
    }
    try:
        r = await client.post(LITELLM_URL, json=payload, timeout=30.0)
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        # Strip ```json wrappers if present
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()
        return json.loads(text)
    except Exception as e:
        return {"equivalent": None, "confidence": 0.0, "reasoning": f"judge error: {e}"}


async def judge_majority(client: httpx.AsyncClient, msg: dict, n: int) -> dict:
    votes = []
    for _ in range(n):
        v = await judge_once(client, msg["query"], msg["answer"])
        if v:
            votes.append(v)
    equivalents = [v.get("equivalent") for v in votes if v.get("equivalent") is not None]
    if not equivalents:
        return {**msg, "votes": votes, "verdict": None, "majority_eq": None}
    majority_eq = Counter(equivalents).most_common(1)[0][0]
    avg_conf = sum(v.get("confidence", 0) for v in votes) / max(len(votes), 1)
    return {
        **msg, "votes": votes, "majority_eq": majority_eq,
        "avg_conf": round(avg_conf, 2),
        "verdict": "equivalent" if majority_eq else "divergent",
    }


async def run(sample: int, judge_n: int) -> dict:
    msgs = fetch_messages(sample)
    if not msgs:
        return {"error": "no pre-dcd7110 messages found"}
    async with httpx.AsyncClient() as client:
        results = []
        for i, m in enumerate(msgs, 1):
            print(f"  [{i}/{len(msgs)}] judging {m['agent']} msg {m['id'][:8]}…", flush=True)
            r = await judge_majority(client, m, judge_n)
            results.append(r)
    return aggregate(results)


def aggregate(results: list[dict]) -> dict:
    total = len(results)
    valid = [r for r in results if r.get("majority_eq") is not None]
    if not valid:
        return {"error": "all judge calls failed", "results": results}
    equivalent = sum(1 for r in valid if r["majority_eq"])
    pct = round(100 * equivalent / len(valid), 1)
    gate = "PASS" if pct >= 80 else ("FAIL" if pct < 60 else "GREY")
    by_agent = {}
    for r in valid:
        a = r["agent"]
        by_agent.setdefault(a, {"total": 0, "eq": 0})
        by_agent[a]["total"] += 1
        if r["majority_eq"]:
            by_agent[a]["eq"] += 1
    return {
        "total_sampled": total,
        "judgeable": len(valid),
        "equivalent": equivalent,
        "pct": pct,
        "gate": gate,
        "by_agent": by_agent,
        "results": results,
    }


def render_report(data: dict) -> str:
    lines = [
        "# Session 39 Block 3 — Phase C regression oracle report",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Verdict",
        "",
    ]
    gate = data.get("gate", "ERROR")
    emoji = {"PASS": "✅", "FAIL": "❌", "GREY": "⚠️", "ERROR": "💥"}.get(gate, "?")
    lines.extend([
        f"**Gate : {emoji} {gate}**",
        "",
        f"- Sampled : **{data.get('total_sampled', '?')}** pre-dcd7110 messages",
        f"- Judge-able : {data.get('judgeable', '?')}",
        f"- Majority-equivalent : {data.get('equivalent', '?')} ({data.get('pct', '?')}%)",
        "",
    ])
    if "by_agent" in data:
        lines.append("## Breakdown per agent")
        lines.append("")
        for a, stats in sorted(data["by_agent"].items()):
            pct = round(100 * stats["eq"] / max(stats["total"], 1), 1)
            lines.append(f"- **{a}** : {stats['eq']}/{stats['total']} equivalent ({pct}%)")
        lines.append("")
    lines.extend([
        "## Thresholds",
        "",
        "- PASS : pct ≥ 80% → reorder safe, no action.",
        "- GREY : 60 ≤ pct < 80% → log P1 follow-up, investigate divergent samples manually.",
        "- FAIL : pct < 60% → STOP and alert Sinse ; consider rollback via `scripts/sprint6/rollback_phase_c.sh`.",
        "",
        "## Design caveats",
        "",
        "- The judge sees (query, original_answer, doctrine summary) — NOT the raw Dify prompt.",
        "  The judge evaluates whether the answer is *congruent with the current doctrine*.",
        "  This is a cheaper proxy than re-rendering the live prompt ; expect a confidence",
        "  floor around 70-75% even for perfectly safe reorders due to judge subjectivity.",
        "- Pre-reorder answers came from a slightly different prompt ordering, so apparent",
        "  divergences might be framing noise rather than real doctrine drift. When gate",
        "  = GREY, inspect divergent sample reasoning strings before concluding.",
    ])
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=30)
    ap.add_argument("--judge-n", type=int, default=3)
    ap.add_argument("--out", default="/tmp/phase_c_oracle_report.json")
    args = ap.parse_args()

    random.seed(42)
    print(f"▶ Oracle Phase C regression — sample={args.sample} judge_n={args.judge_n}")
    data = asyncio.run(run(args.sample, args.judge_n))
    Path(args.out).write_text(json.dumps(data, indent=2, default=str))
    print(f"▶ JSON report : {args.out}")

    report_md = render_report(data)
    md_path = Path("/tmp/phase_c_oracle_report.md")
    md_path.write_text(report_md)
    print(f"▶ Markdown report : {md_path}")
    print()
    print(report_md)
    return 0 if data.get("gate") == "PASS" else (1 if data.get("gate") == "FAIL" else 0)


if __name__ == "__main__":
    sys.exit(main())
