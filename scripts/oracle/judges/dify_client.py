"""Session 40 Phase B2/C — Dify public API client.

Calls Teacher EN (or any app keyed by DIFY_KEY_{AGENT}) with a learner
query, returns the bot's plain-text answer.

Used by :
  - harness.py (mode full/smoke) to get live bot response per scenario
  - fault_injection.py (Phase D) to call a cloned app with a patched prompt
"""
from __future__ import annotations

import os

import httpx

DIFY_URL = os.environ.get("DIFY_PUBLIC_API", "http://127.0.0.1:5001/v1/chat-messages")


def call_teacher_en(query: str, conv_seed: str | None = None, api_key: str | None = None) -> str:
    """POST to Dify public API. conv_seed is the `user` field (used for
    dedup + conv attribution). Returns the bot's plain-text answer."""
    key = api_key or os.environ.get("DIFY_KEY_TEACHER", "")
    if not key:
        raise RuntimeError("no DIFY_KEY_TEACHER in env and no api_key passed")
    payload = {
        "query": query,
        "inputs": {},
        "user": f"oracle-{conv_seed or 'unknown'}",
        "response_mode": "blocking",
        "conversation_id": "",
    }
    with httpx.Client(timeout=90) as c:
        r = c.post(DIFY_URL, json=payload, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })
        r.raise_for_status()
        return (r.json().get("answer") or "").strip()
