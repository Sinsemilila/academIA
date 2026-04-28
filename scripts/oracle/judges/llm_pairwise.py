"""Session 40 Phase B1 — LLM pairwise dim scoring via LiteLLM proxy.

3 LLM-judged dims for V1 :
  - cf_move_set_valid_llm : classify the bot's CF move, verify in acceptable set
  - register_cefr_alignment : classify register CEFR level of bot turn
  - semantic_fidelity_pairwise : pairwise vs golden → equivalent / divergent

N-majority vote per dim. Temperature=0. gpt-4o-mini self-vendor (see §3b
of corpus-oracle-v1-design.md). Swap `config.judge.model` to switch.

Each call ~400-500 tokens in, ~100 tokens out. 3 dims × N=3 votes × 24 scenarios
= ~216 calls = ~108K tokens for a full run.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import Counter

import httpx

from ..schemas import DimVerdict, ScenarioSchema

_log = logging.getLogger("oracle.llm_judge")

CF_MOVES = [
    "full_recast", "partial_recast", "clarification_request",
    "metalinguistic", "elicitation", "repetition", "explicit_correction",
]

CF_MOVE_PROMPT = """You classify a tutor's corrective feedback move using Lyster's 7-move taxonomy.

Moves :
- full_recast : tutor repeats learner's utterance with the error silently corrected, no commentary
- partial_recast : tutor corrects only the erroneous fragment
- clarification_request : tutor asks learner to rephrase ("What do you mean?", "Could you say that again?")
- metalinguistic : tutor names/explains the grammar rule ("past simple uses -ed")
- elicitation : tutor prompts learner to produce the correct form ("Almost — what's the past of go?")
- repetition : tutor repeats the erroneous part with rising intonation, no correction
- explicit_correction : tutor flags the error AND provides the correct form ("No, it's 'went', not 'goed'")

Learner utterance : "{learner}"
Tutor response : "{tutor}"

Output strict JSON : {{"move": "<one of the 7>", "confidence": 0.0-1.0, "reasoning": "one sentence"}}"""

CEFR_REGISTER_PROMPT = """You classify the CEFR level that a tutor's response is pitched at.

CEFR descriptors (simplified) :
- A1 : very simple words, short sentences, present simple, concrete vocab
- A2 : past simple, simple conjunctions, everyday topics
- B1 : present perfect, conditional 1, opinion, longer sentences
- B2 : nuance, modal verbs, hypothetical, arguments
- C1/C2 : idiomatic, abstract, full range

Tutor response : "{tutor}"

What CEFR level is this response pitched at ? Output strict JSON :
{{"level": "A1"|"A2"|"B1"|"B2"|"C1"|"C2", "reasoning": "one sentence"}}"""

PAIRWISE_PROMPT = """You judge pedagogical equivalence between two tutor responses to the same learner utterance.

Two responses are EQUIVALENT if :
- They address the same error(s) with a comparable corrective feedback type
- They aim at the same CEFR level
- They pitch the same tier (silent / recast / elicit / explicit)
- Stylistic differences (tone, word choice) are acceptable

They are DIVERGENT if :
- One corrects a different error than the other
- One uses a materially different CF type (e.g., recast vs metalinguistic)
- One is pitched at a materially different CEFR level
- One exhibits a doctrinal violation (A1 metalinguistic, priority leak, etc.) that the other does not

Learner : "{learner}"
Response A (bot) : "{response_a}"
Response B (golden) : "{response_b}"

Output strict JSON : {{"equivalent": true|false, "confidence": 0.0-1.0, "reasoning": "one sentence"}}"""


def _extract_json(text: str | None) -> dict | None:
    # Defensive : Gemini 2.5 Flash returns content=None when thinking
    # tokens consume the whole max_tokens budget — don't crash on that.
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.MULTILINE)
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


async def _call_judge(
    client: httpx.AsyncClient, cfg: dict, messages: list[dict]
) -> dict | None:
    jcfg = cfg["judge"]
    payload = {
        "model": jcfg["model"],
        "messages": messages,
        "temperature": jcfg.get("temperature", 0.0),
        "max_tokens": jcfg.get("max_tokens", 200),
    }
    # Session 44 — Gemini 2.5 Flash judges need reasoning suppressed,
    # otherwise thinking tokens consume the entire max_tokens budget
    # and the actual JSON verdict comes back empty. Optional pass-through.
    if jcfg.get("reasoning_effort"):
        payload["reasoning_effort"] = jcfg["reasoning_effort"]
    master = os.environ.get("LITELLM_MASTER_KEY", "")
    headers = {"Content-Type": "application/json"}
    if master:
        headers["Authorization"] = f"Bearer {master}"
    # Session 51 P0.2 — retry on 429 / ReadTimeout with exponential backoff.
    # Free-tier judge LLMs (Groq gemini-3-1-flash-lite) burst-limit on full
    # battery (78 calls × 26 scenarios × 3 votes). Without retry, many dims
    # fall back to None verdict → divergent-by-default semantic_fidelity_pairwise.
    timeout_s = jcfg.get("timeout_s", 30)
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            r = await client.post(
                cfg["litellm"]["proxy_url"], json=payload, headers=headers,
                timeout=timeout_s,
            )
            if r.status_code == 429 and attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            choice = r.json().get("choices", [{}])[0]
            text = (choice.get("message") or {}).get("content")
            result = _extract_json(text)
            if result is None:
                _log.warning(
                    "judge returned no parseable JSON "
                    "(content_empty=%s, finish_reason=%s)",
                    not text, choice.get("finish_reason"),
                )
            return result
        except httpx.ReadTimeout:
            if attempt < max_attempts - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            _log.warning("judge call failed: ReadTimeout after %d attempts", max_attempts)
            return None
        except httpx.HTTPStatusError as e:
            # 429 fallthrough on final attempt OR non-retryable status.
            _log.warning("judge call failed: HTTPStatusError (%s)", e)
            return None
        except Exception as e:
            _log.warning("judge call failed: %s (%s)", type(e).__name__, e)
            return None
    return None


async def _vote_n(
    client: httpx.AsyncClient, cfg: dict, messages: list[dict], n: int,
) -> list[dict]:
    results = []
    for _ in range(n):
        r = await _call_judge(client, cfg, messages)
        if r:
            results.append(r)
    return results


def _majority_move(votes: list[dict]) -> tuple[str | None, float]:
    """Returns (winner, agreement_ratio). ratio = winner_count / total_valid_votes."""
    moves = [v.get("move") for v in votes if v.get("move")]
    if not moves:
        return None, 0.0
    winner, count = Counter(moves).most_common(1)[0]
    return winner, count / len(moves)


def _majority_bool(votes: list[dict], key: str) -> tuple[bool | None, float]:
    vals = [v.get(key) for v in votes if isinstance(v.get(key), bool)]
    if not vals:
        return None, 0.0
    winner, count = Counter(vals).most_common(1)[0]
    return winner, count / len(vals)


def _majority_level(votes: list[dict]) -> tuple[str | None, float]:
    lvls = [v.get("level") for v in votes if v.get("level")]
    if not lvls:
        return None, 0.0
    winner, count = Counter(lvls).most_common(1)[0]
    return winner, count / len(lvls)


CEFR_ORDER = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}


async def _score_cf_move(client, cfg, scenario: ScenarioSchema, bot: str, n: int) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("cf_move_set_valid") or {}
    acceptable = set(spec.get("acceptable", []))
    forbidden = set(spec.get("forbidden", []))
    learner = next((t.text for t in scenario.turns if t.role == "learner"), "")
    msgs = [
        {"role": "system", "content": "You are a Lyster CF-move classifier. Output JSON only."},
        {"role": "user", "content": CF_MOVE_PROMPT.format(learner=learner, tutor=bot)},
    ]
    votes = await _vote_n(client, cfg, msgs, n)
    move, ratio = _majority_move(votes)
    if not move:
        return DimVerdict(dim="cf_move_set_valid", verdict="unknown",
                          reasoning="no consensus", judge_votes=votes)
    fail_thr = cfg.get("judge_fail_threshold", 0.7)
    is_forbidden = forbidden and move in forbidden
    is_unacceptable = acceptable and move not in acceptable
    if (is_forbidden or is_unacceptable) and ratio < fail_thr:
        # Session 51 Tier 1 — borderline judge consensus, don't certify fail.
        return DimVerdict(dim="cf_move_set_valid", verdict="unknown",
                          reasoning=f"move={move} ({ratio:.2f} < {fail_thr}) low confidence",
                          judge_votes=votes)
    if is_forbidden:
        return DimVerdict(dim="cf_move_set_valid", verdict="fail",
                          reasoning=f"move={move} in forbidden set ({ratio:.2f})", judge_votes=votes)
    if is_unacceptable:
        return DimVerdict(dim="cf_move_set_valid", verdict="fail",
                          reasoning=f"move={move} not in acceptable set {sorted(acceptable)} ({ratio:.2f})",
                          judge_votes=votes)
    return DimVerdict(dim="cf_move_set_valid", verdict="pass",
                      reasoning=f"move={move} ({ratio:.2f})", judge_votes=votes)


async def _score_cefr_register(client, cfg, scenario: ScenarioSchema, bot: str, n: int) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("register_cefr_alignment") or {}
    target = spec.get("target") or scenario.scenario_key.cefr
    tolerance = spec.get("tolerance", 1)
    msgs = [
        {"role": "system", "content": "You classify CEFR register. Output JSON only."},
        {"role": "user", "content": CEFR_REGISTER_PROMPT.format(tutor=bot)},
    ]
    votes = await _vote_n(client, cfg, msgs, n)
    level, ratio = _majority_level(votes)
    if not level:
        return DimVerdict(dim="register_cefr_alignment", verdict="unknown",
                          reasoning="no consensus", judge_votes=votes)
    diff = abs(CEFR_ORDER.get(level, 0) - CEFR_ORDER.get(target, 0))
    if diff <= tolerance:
        return DimVerdict(dim="register_cefr_alignment", verdict="pass",
                          reasoning=f"observed={level}, target={target} ({ratio:.2f})",
                          judge_votes=votes)
    fail_thr = cfg.get("judge_fail_threshold", 0.7)
    if ratio < fail_thr:
        return DimVerdict(dim="register_cefr_alignment", verdict="unknown",
                          reasoning=f"observed={level} vs target={target} ({ratio:.2f} < {fail_thr}) low confidence",
                          judge_votes=votes)
    return DimVerdict(dim="register_cefr_alignment", verdict="fail",
                      reasoning=f"observed={level} vs target={target} (±{tolerance}, {ratio:.2f})",
                      judge_votes=votes)


async def _score_pairwise(client, cfg, scenario: ScenarioSchema, bot: str, golden: str, n: int) -> DimVerdict:
    if not golden:
        return DimVerdict(dim="semantic_fidelity_pairwise", verdict="unknown",
                          reasoning="no golden recorded")
    learner = next((t.text for t in scenario.turns if t.role == "learner"), "")
    msgs = [
        {"role": "system", "content": "You judge pedagogical equivalence. Output JSON only."},
        {"role": "user", "content": PAIRWISE_PROMPT.format(
            learner=learner, response_a=bot, response_b=golden)},
    ]
    votes = await _vote_n(client, cfg, msgs, n)
    eq, ratio = _majority_bool(votes, "equivalent")
    if eq is None:
        return DimVerdict(dim="semantic_fidelity_pairwise", verdict="unknown",
                          reasoning="no consensus", judge_votes=votes)
    if eq:
        return DimVerdict(dim="semantic_fidelity_pairwise", verdict="pass",
                          reasoning=f"majority equivalent ({ratio:.2f})", judge_votes=votes)
    fail_thr = cfg.get("judge_fail_threshold", 0.7)
    if ratio < fail_thr:
        return DimVerdict(dim="semantic_fidelity_pairwise", verdict="unknown",
                          reasoning=f"divergent ({ratio:.2f} < {fail_thr}) low confidence",
                          judge_votes=votes)
    return DimVerdict(dim="semantic_fidelity_pairwise", verdict="fail",
                      reasoning=f"majority divergent ({ratio:.2f})", judge_votes=votes)


def score_all(scenario: ScenarioSchema, response: str, golden: str, cfg: dict, n: int = 3) -> list[DimVerdict]:
    """Sync wrapper — runs the 3 LLM-judged dims concurrently via gather."""
    async def _run():
        async with httpx.AsyncClient() as client:
            return list(await asyncio.gather(
                _score_cf_move(client, cfg, scenario, response, n),
                _score_cefr_register(client, cfg, scenario, response, n),
                _score_pairwise(client, cfg, scenario, response, golden, n),
            ))
    return asyncio.run(_run())
