"""Session 40/41 — Dify public API client, agent-agnostic.

Dispatch by `agent` key in `scripts/oracle/config.yaml::agents`. Reads
`env_key_name` env var at call time. Used by harness (live bot response)
+ record_golden (golden capture) + fault_injection (not yet — uses
LiteLLM bypass there).
"""
from __future__ import annotations

import os
from pathlib import Path

import httpx
import yaml

_CFG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


def _cfg() -> dict:
    return yaml.safe_load(_CFG_PATH.read_text())


def _agent_config(agent: str, cfg: dict | None = None) -> dict:
    cfg = cfg or _cfg()
    agents = cfg.get("agents") or {}
    if agent not in agents:
        raise KeyError(f"unknown agent {agent!r} in oracle/config.yaml::agents")
    return agents[agent]


def call_agent(agent: str, query: str, conv_seed: str | None = None, api_key: str | None = None) -> str:
    """POST to Dify public API for the given agent. Returns bot's plain-text answer."""
    cfg = _cfg()
    ac = _agent_config(agent, cfg)
    key = api_key or os.environ.get(ac["env_key_name"], "")
    if not key:
        raise RuntimeError(f"env var {ac['env_key_name']} empty and no api_key passed")
    url = cfg["dify"]["public_api_base"] + cfg["dify"].get("public_api_path", "/v1/chat-messages")
    payload = {
        "query": query,
        "inputs": {},
        "user": f"oracle-{conv_seed or 'unknown'}",
        "response_mode": "blocking",
        "conversation_id": "",
    }
    with httpx.Client(timeout=90) as c:
        r = c.post(url, json=payload, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        })
        r.raise_for_status()
        return (r.json().get("answer") or "").strip()


# Backward-compat alias — older code expects call_teacher_en
def call_teacher_en(query: str, conv_seed: str | None = None, api_key: str | None = None) -> str:
    return call_agent("teacher_en", query, conv_seed, api_key)


# Legacy import target used in parts of the harness — kept as module constant
DIFY_URL = (_cfg()["dify"]["public_api_base"]
            + _cfg()["dify"].get("public_api_path", "/v1/chat-messages"))
