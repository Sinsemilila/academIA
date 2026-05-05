"""Quick A/B test : v2 cf_move prompt vs v1 baseline on the 9 'unknown' scenarios
where cerebras-llama-3.1-8b misclassified explicit_correction as full_recast.

Calls cerebras-judge-fast (the weak link) directly via LiteLLM proxy with the
NEW v2 prompt. Compares classification vs Lyster ground truth.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, "/opt/academia")
from scripts.oracle.judges.llm_pairwise import CF_MOVE_PROMPT, _call_judge

# 9 scenarios where panel had 'unknown' verdict + Opus identifies correct move per Lyster
SCENARIOS = [
    ("b2_t3_modal_deduction_001", "explicit_correction"),
    ("b2_t3_passive_001", "explicit_correction"),
    ("c1_t3_conditional_mix_001", "explicit_correction"),
    ("c1_t3_false_friend_assister_001", "explicit_correction"),  # has metalinguistic component
    ("el_a1_t2_misc_001", "clarification_request"),  # judges miss this, golden has "Can you finish your thought?"
    ("el_a1_t2_misc_002", "implicit_recast"),  # "Oh I see you want to say..." embedded
    ("el_a1_t2_misc_003", "explicit_correction"),  # need to verify
    ("multi_b2_modal_no_uptake_001", "prompt_plus_remediation"),  # Lyster T4 sequence
    ("risk_priority_leak_b1_001", "full_recast"),  # need to verify based on golden
]

CFG = {
    "judge": {
        "model": "cerebras-judge-fast",
        "temperature": 0.0,
        "max_tokens": 800,  # v2 prompt longer, more reasoning needed
        "timeout_s": 30,
    },
    "litellm": {"proxy_url": "http://127.0.0.1:4000/v1/chat/completions"},
}


def load_scenario(sid):
    base = Path("/opt/academia/scripts/oracle/scenarios/teacher_en")
    spath = base / f"{sid}.yaml"
    if not spath.exists():
        for alt in base.rglob(f"{sid}.yaml"):
            spath = alt
            break
    return yaml.safe_load(spath.read_text())


def load_golden(sid):
    p = Path(f"/opt/academia/scripts/oracle/scenarios/teacher_en/golden/{sid}.json")
    return json.loads(p.read_text()).get("response", "")


async def classify_one(client, learner, tutor):
    msgs = [
        {"role": "system", "content": "You are a Lyster CF-move classifier. Output JSON only."},
        {"role": "user", "content": CF_MOVE_PROMPT.format(learner=learner, tutor=tutor)},
    ]
    return await _call_judge(client, CFG, msgs, model_override="cerebras-judge-fast")


async def main():
    n_votes = 3
    print("\n=== A/B test cf_move prompt v2 on cerebras-judge-fast ===")
    print(f"n_votes per scenario : {n_votes}")
    print(f"scenarios : {len(SCENARIOS)}")
    print()

    correct = 0
    total = 0
    misclass = []

    async with httpx.AsyncClient() as client:
        for sid, expected in SCENARIOS:
            scenario = load_scenario(sid)
            learner = next((t["text"] for t in scenario["turns"] if t["role"] == "learner"), "")
            tutor = load_golden(sid)
            votes = []
            for _ in range(n_votes):
                v = await classify_one(client, learner, tutor)
                if v:
                    votes.append(v.get("move", "?"))
            from collections import Counter
            top = Counter(votes).most_common(1)
            classified = top[0][0] if top else "?"
            total += n_votes
            agree = sum(1 for v in votes if v == expected)
            correct += agree
            status = "✅" if classified == expected else "❌"
            print(f"{status} {sid:<40} expected={expected:<25} got={classified:<22} all={votes}")
            if classified != expected:
                misclass.append((sid, expected, classified, votes))

    print()
    print(f"Total : {correct}/{total} votes correct ({100*correct/total:.1f}%)")
    print(f"Top-vote correct : {len(SCENARIOS) - len(misclass)}/{len(SCENARIOS)}")
    if misclass:
        print("\nMisclassifications :")
        for sid, exp, got, votes in misclass:
            print(f"  {sid} → expected={exp}, got={got} (votes: {votes})")


if __name__ == "__main__":
    asyncio.run(main())
