"""Session 42 P4 — shared LLM judge helper.

Factored out of consolidation_router._llm_judge_item so onboarding probe
+ future callers can reuse. Thin async wrapper over LiteLLM proxy
(gpt-4.1-mini) with strict PASS/FAIL or granular 0-3 scoring modes.

Safe-by-default : any exception returns a conservative fallback (False /
0) rather than propagating. Telemetry caller should never see LLM
calls break the request path.
"""
from __future__ import annotations

import os

import httpx

LITELLM_URL = "http://litellm-proxy:4000/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"  # Session 42 P4 — LiteLLM proxy has gpt-4o-mini configured, not gpt-4.1-mini


async def judge_passfail(prompt: str, learner_answer: str, hint: str,
                         model: str = DEFAULT_MODEL, timeout_s: float = 8.0) -> bool:
    """Grade PASS/FAIL for short answers. Returns False on any failure."""
    try:
        # Session 42 : auth not required from docker-internal network, but
        # send key if present (for future proxy-side auth enforcement).
        api_key = os.environ.get("LITELLM_MASTER_KEY") or os.environ.get("LITELLM_API_KEY", "")
        sys = (
            "You grade short language-learning exercises. Answer ONLY 'PASS' or 'FAIL'. "
            "Be strict but fair: accept minor typos, reject substantive errors. "
            f"Teacher's expectation: {hint}"
        )
        msg = f"Prompt: {prompt}\nLearner answer: {learner_answer}\nYour verdict:"
        async with httpx.AsyncClient(timeout=timeout_s) as c:
            r = await c.post(LITELLM_URL,
                             headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                             json={
                                 "model": model,
                                 "messages": [{"role": "system", "content": sys},
                                              {"role": "user", "content": msg}],
                                 "max_tokens": 8, "temperature": 0.0,
                             })
            r.raise_for_status()
            verdict = r.json()["choices"][0]["message"]["content"].strip().upper()
            return verdict.startswith("PASS")
    except Exception:
        return False


async def judge_probe_score(learner_answer: str, target_sentence: str | None,
                            target_structure: str | None, target_gold: list[str] | None,
                            model: str = DEFAULT_MODEL, timeout_s: float = 10.0) -> int:
    """Grade the onboarding probe (B1+ discriminant, 3rd conditional etc.) on
    a 0-3 scale. Returns 0 on any failure (conservative — no partial credit
    without signal).

    Scoring anchors :
      3 = target structure used correctly, gold-equivalent
      2 = target structure present but minor form error
      1 = partial / recognisable attempt
      0 = off-topic, wrong, empty
    """
    try:
        api_key = os.environ.get("LITELLM_MASTER_KEY") or os.environ.get("LITELLM_API_KEY", "")
        gold_block = ""
        if target_gold:
            gold_block = "\n".join(f"  - {g}" for g in target_gold)
        sys = (
            "You grade a single short learner translation on a 0-3 scale :\n"
            "  3 = target structure used correctly, matches a gold answer\n"
            "  2 = target structure present, minor form errors\n"
            "  1 = partial / recognisable attempt at the structure\n"
            "  0 = off-topic, wrong, or structure absent\n"
            "Reply with a single digit 0/1/2/3 — nothing else."
        )
        user_parts = []
        if target_sentence:
            user_parts.append(f"Source sentence (FR) : {target_sentence}")
        if target_structure:
            user_parts.append(f"Target structure : {target_structure}")
        if target_gold:
            user_parts.append(f"Gold answers :\n{gold_block}")
        user_parts.append(f"Learner answer : {learner_answer or '(empty)'}")
        user_parts.append("Score (0-3) :")
        async with httpx.AsyncClient(timeout=timeout_s) as c:
            r = await c.post(LITELLM_URL,
                             headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                             json={
                                 "model": model,
                                 "messages": [{"role": "system", "content": sys},
                                              {"role": "user", "content": "\n".join(user_parts)}],
                                 "max_tokens": 4, "temperature": 0.0,
                             })
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"].strip()
            # First char should be 0/1/2/3
            if raw and raw[0].isdigit():
                v = int(raw[0])
                return max(0, min(3, v))
            return 0
    except Exception:
        return 0
