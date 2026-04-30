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
    # 10-class enum aligned with cf-taxonomy.yaml (Lyster 2007 extracted) + AcademIA convention
    # Schema 11-value enum drops `explicit_recast` here (data starvation in fewshots —
    # handled via step 2 generator metadata, see docs/01-pedagogy/cf-taxonomy-gap-2026-04-29.md).
    # `silent` = no-CF policy decision (deliberate pedagogical choice), is_cf: false in schema.
    "silent", "implicit_recast", "full_recast", "partial_recast",
    "clarification_request", "repetition", "metalinguistic",
    "elicitation", "prompt_plus_remediation", "explicit_correction",
]

CF_MOVE_PROMPT = """You classify a tutor's corrective feedback move using Lyster's 10-move taxonomy + AcademIA `silent` policy.

# DECISION TREE — apply step by step

**Step 1 — Does the tutor EXPLICITLY flag the learner's utterance as wrong?**
   Explicit flagging signals : "No", "Wrong", "Instead of X", "It should be", "Almost", "Not quite",
   "The correct form is", "*X* is the right word", phonological stress on the error part.
   - YES + tutor provides correct form → likely `explicit_correction` (or `prompt_plus_remediation` if also has a prompt before)
   - YES + tutor asks learner to repair → likely `metalinguistic` / `elicitation` / `clarification_request`
   - NO → continue Step 2 (recast family)

**Step 2 — Did the tutor reformulate the utterance silently (no flagging)?**
   - Reformulates the WHOLE utterance, often paraphrasing for register → `full_recast`
   - Reformulates ONLY the erroneous fragment, often embedded in a follow-up question → `partial_recast`
   - Embeds the corrected form in a confirmation/expansion ("Yes, you went to Paris!") without isolating it → `implicit_recast`
   - Reformulates a CORRECT learner utterance (no error) → `repetition` (NOT corrective ; non_cf)
   - Did not say anything corrective at all → `silent`

**Step 3 — Did the tutor sequence multiple moves (Lyster T4 escalation pattern, Doughty & Varela 1998)?**
   - Prompt (clarification / repetition / metalinguistic / elicitation) followed by a recast or explicit correction → `prompt_plus_remediation`
   - This subsumes "Almost — past tense?" + "It's 'went'." sequences

# CRITICAL DISAMBIGUATION : explicit_correction vs full_recast

These are the most-confused pair. Decisive cue = **EXPLICIT FLAGGING**.

| Cue | explicit_correction | full_recast |
|---|---|---|
| Says "It should be / Instead of / No / Almost" | YES | NO |
| Provides correct form | YES | YES |
| Reformulates whole utterance | sometimes | YES (defining feature) |
| Tutor's stance | "you erred, here's the truth" | "let me confirm and expand" |

**Few-shot examples (study these before classifying)** :

EX1 — Learner: "If I would have known earlier, I would have prepared."
     Tutor: "Almost there! Instead of 'If I would have known', you should say 'If I had known'. The correct form is..."
     → MOVE: explicit_correction
     → reasoning: tutor explicitly flags error ("Instead of X") and provides correct form with metalinguistic comment.

EX2 — Learner: "the magnets they're not pushing"
     Tutor: "OK so when they were facing one way, you felt the magnets attract and stick together. When you turn one of the magnets around you felt it... repelling, or pushing away."
     → MOVE: full_recast
     → reasoning: tutor reformulates whole utterance with academic register shift, NO explicit flag of error (Lyster 2007 p.94, Gibbons 2003).

EX3 — Learner: "I goed to the cinema."
     Tutor: "Oh you *went* to the cinema! What movie did you see?"
     → MOVE: partial_recast
     → reasoning: tutor isolates and corrects only the erroneous fragment, embedded in a follow-up question (Lyster taxonomy canonical).

EX4 — Learner: "She is interested on learning French."
     Tutor: "Yes, she's interested *in* learning French — which subject does she like most?"
     → MOVE: partial_recast (NOT implicit_recast, because the correction is salient via stress/positioning + follow-up Q).

EX5 — Learner: "If I would have more money, I will travel."
     Tutor: "Almost — in 'if'-sentences about unreal situations, which tense comes after 'if'? Try: 'If I had more money, I would travel.'"
     → MOVE: prompt_plus_remediation
     → reasoning: sequences metalinguistic question ("which tense after 'if'?") + recast model ("Try: ...") — Lyster T4 escalation, Doughty & Varela 1998.

EX6 — Learner: "I want to buy car for my wife."
     Tutor: "Oh, you want to buy *a car*! What kind of car do you want?"
     → MOVE: partial_recast
     → reasoning: isolates 'a car', embeds in confirmation + follow-up question.

EX7 — Learner: "It have mixed colors."
     Tutor: "It has mixed colors."
     → MOVE: implicit_recast
     → reasoning: silent reformulation of whole utterance, no flagging, ambiguous as positive evidence (Mackey, Gass & McDonough 2000).

# Now classify

Learner utterance : "{learner}"
Tutor response : "{tutor}"

Apply Step 1 → 2 → 3. Pay close attention to explicit flagging language.

Output strict JSON :
{{"move": "<one of: silent | implicit_recast | full_recast | partial_recast | clarification_request | repetition | metalinguistic | elicitation | prompt_plus_remediation | explicit_correction>", "confidence": 0.0-1.0, "reasoning": "Step 1 verdict + decisive cue. One sentence."}}"""

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
    client: httpx.AsyncClient,
    cfg: dict,
    messages: list[dict],
    model_override: str | None = None,
) -> dict | None:
    """Single judge call.

    model_override : if set, use this LiteLLM model_name instead of
    cfg["judge"]["model"]. Used by panel mode (Phase 2) where each
    panel member is queried in turn.
    """
    jcfg = cfg["judge"]
    payload = {
        "model": model_override or jcfg["model"],
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
    client: httpx.AsyncClient,
    cfg: dict,
    messages: list[dict],
    n: int,
    model_override: str | None = None,
) -> list[dict]:
    """Collect N votes from a single judge model.

    Each vote dict tagged with `_judge_model` for downstream panel
    breakdown / AC2 cross-judge analysis.
    """
    model = model_override or cfg["judge"]["model"]
    results = []
    for _ in range(n):
        r = await _call_judge(client, cfg, messages, model_override=model)
        if r:
            r["_judge_model"] = model
            results.append(r)
    return results


async def _vote_panel(
    client: httpx.AsyncClient,
    cfg: dict,
    messages: list[dict],
    n_per_judge: int,
    panel_models: list[str],
) -> list[dict]:
    """Collect votes from multiple judge models (panel mode).

    Each model contributes n_per_judge votes. Returns flat list of vote
    dicts, each tagged with `_judge_model`. Order preserved per panel
    member ordering.
    """
    flat: list[dict] = []
    for model in panel_models:
        votes = await _vote_n(client, cfg, messages, n_per_judge, model_override=model)
        flat.extend(votes)
    return flat


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


def _group_by_judge(votes: list[dict]) -> dict[str, list[dict]]:
    """Group flat panel votes by `_judge_model` tag."""
    grouped: dict[str, list[dict]] = {}
    for v in votes:
        m = v.get("_judge_model", "<unknown>")
        grouped.setdefault(m, []).append(v)
    return grouped


def _cross_judge_majority(
    votes: list[dict], majority_fn
) -> tuple[object, float]:
    """Aggregate panel votes : intra-judge majority per model → cross-judge
    majority across models.

    majority_fn(votes) -> (winner, intra_ratio) — pass _majority_move,
    _majority_level, or partial (_majority_bool, key=...).

    Returns (cross_winner, cross_ratio) where cross_ratio = max_count /
    n_judges_with_signal. If no judge produced a verdict, returns (None, 0.0).
    """
    by_judge = _group_by_judge(votes)
    intra_winners: list[object] = []
    for _, jvotes in by_judge.items():
        winner, _ratio = majority_fn(jvotes)
        if winner is not None:
            intra_winners.append(winner)
    if not intra_winners:
        return None, 0.0
    cross_winner, cross_count = Counter(intra_winners).most_common(1)[0]
    return cross_winner, cross_count / len(intra_winners)


async def _score_cf_move(
    client, cfg, scenario: ScenarioSchema, bot: str, n: int,
    panel_models: list[str] | None = None,
) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("cf_move_set_valid") or {}
    acceptable = set(spec.get("acceptable", []))
    forbidden = set(spec.get("forbidden", []))
    learner = next((t.text for t in scenario.turns if t.role == "learner"), "")
    msgs = [
        {"role": "system", "content": "You are a Lyster CF-move classifier. Output JSON only."},
        {"role": "user", "content": CF_MOVE_PROMPT.format(learner=learner, tutor=bot)},
    ]
    if panel_models:
        votes = await _vote_panel(client, cfg, msgs, n, panel_models)
        move, ratio = _cross_judge_majority(votes, _majority_move)
    else:
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


async def _score_cefr_register(
    client, cfg, scenario: ScenarioSchema, bot: str, n: int,
    panel_models: list[str] | None = None,
) -> DimVerdict:
    spec = (scenario.expected_dimensions or {}).get("register_cefr_alignment") or {}
    target = spec.get("target") or scenario.scenario_key.cefr
    tolerance = spec.get("tolerance", 1)
    msgs = [
        {"role": "system", "content": "You classify CEFR register. Output JSON only."},
        {"role": "user", "content": CEFR_REGISTER_PROMPT.format(tutor=bot)},
    ]
    if panel_models:
        votes = await _vote_panel(client, cfg, msgs, n, panel_models)
        level, ratio = _cross_judge_majority(votes, _majority_level)
    else:
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


async def _score_pairwise(
    client, cfg, scenario: ScenarioSchema, bot: str, golden: str, n: int,
    panel_models: list[str] | None = None,
) -> DimVerdict:
    if not golden:
        return DimVerdict(dim="semantic_fidelity_pairwise", verdict="unknown",
                          reasoning="no golden recorded")
    learner = next((t.text for t in scenario.turns if t.role == "learner"), "")
    msgs = [
        {"role": "system", "content": "You judge pedagogical equivalence. Output JSON only."},
        {"role": "user", "content": PAIRWISE_PROMPT.format(
            learner=learner, response_a=bot, response_b=golden)},
    ]
    if panel_models:
        votes = await _vote_panel(client, cfg, msgs, n, panel_models)
        eq, ratio = _cross_judge_majority(
            votes, lambda vs: _majority_bool(vs, "equivalent"),
        )
    else:
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


def score_all(
    scenario: ScenarioSchema, response: str, golden: str, cfg: dict,
    n: int = 3, panel_models: list[str] | None = None,
) -> list[DimVerdict]:
    """Sync wrapper — runs the 3 LLM-judged dims concurrently via gather.

    panel_models : if provided, cross-provider panel mode. Each member
    queried n times, intra-judge majority, then cross-judge majority for
    final verdict. judge_fail_threshold applies to cross_ratio.

    Single-judge mode preserved (panel_models=None) for backward compat.
    """
    async def _run():
        async with httpx.AsyncClient() as client:
            return list(await asyncio.gather(
                _score_cf_move(client, cfg, scenario, response, n, panel_models),
                _score_cefr_register(client, cfg, scenario, response, n, panel_models),
                _score_pairwise(client, cfg, scenario, response, golden, n, panel_models),
            ))
    return asyncio.run(_run())
