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


def build_oracle_profile(scenario, agent: str) -> tuple[str, str]:
    """Session 42 O1 — shared helper (was in record_golden.py) so harness.py
    can inject the same learner_profile_summary + learner_profile_json and
    keep call-path parity with recorded goldens.

    Without this, harness.py calls Dify with empty inputs → Dify routes
    via llm_onboarding (fresh conversation fallback), whereas goldens
    were recorded via llm_session with injected profile. The mismatch
    produces artifactual noise in every dim measurement."""
    import json as _json
    k = scenario.scenario_key
    lang = "anglais" if agent == "teacher_en" else "espagnol"
    nl_summary = (
        f"[ORACLE TEST SIMULATION] Apprenant·e FR-native niveau CEFR {k.cefr}. "
        f"Style préféré : {k.style_profile}. FLA : {k.fla}. "
        f"Langue cible : {lang}. Turn conversation : {scenario.turns[0].turn_number}. "
        f"Bot doit répondre en {lang} (L2) selon la doctrine du niveau {k.cefr}."
    )
    lp_json = _json.dumps({
        "universal": {"self_efficacy": 3, "autonomy_pref": "guided"},
        "level": {"cefr_placement": k.cefr},
        "motivation": {
            "fla_category": k.fla,
            "fla_items_raw": {"fla_a": 3, "fla_b": 3, "fla_c": 3},
        },
        "hints": {"nl_summary": nl_summary},
    }, ensure_ascii=False)
    return nl_summary, lp_json


def build_full_dify_inputs(scenario, agent: str) -> dict:
    """Session 51 — prod-aligned harness inputs.

    Mirrors what `chat_router.py` populates per request : the 11 dynamic
    sections produced by `LanguageDomain.build_dynamic_sections(ctx)` plus
    the oracle profile pair. Without this, the harness measures a
    Teacher EN stripped of `rubric_for_level`, `fewshots_block`,
    `output_schema_block`, `dosage_block`, etc. — divergent from prod scope.
    """
    import sys as _sys
    from pathlib import Path as _Path
    _PKG = _Path("/opt/academie/packages/academie-core")
    if str(_PKG) not in _sys.path:
        _sys.path.insert(0, str(_PKG))
    from academie_core.domain.language import LanguageDomain
    from academie_core.pedagogy.teacher_prompt import PromptContext
    from academie_core.taxonomy.rules import ERROR_CODE_TO_FAMILY

    ac = _agent_config(agent)
    target_lang = ac.get("language", "en")
    nl_summary, lp_json = build_oracle_profile(scenario, agent)

    learner = next((t for t in scenario.turns if t.role == "learner"), None)
    learner_text = learner.text if learner else ""
    turn_count = getattr(learner, "turn_number", 1) if learner else 1

    lang = LanguageDomain(target_lang)
    detections = lang.detect_errors(learner_text)
    sk = scenario.scenario_key
    level = sk.cefr

    # Mirror chat_router.py:837-850 v2_errors enrichment
    v2_errors: list[dict] = []
    for d in detections:
        enriched = lang.score_tier(d.error_code, level)
        if not enriched.get("tier"):
            continue
        v2_errors.append({
            "error_code": d.error_code,
            "family": ERROR_CODE_TO_FAMILY.get(d.error_code, "unknown"),
            "tier": enriched["tier"],
            "gravity_linguistic": enriched.get("gravity_linguistic") or 0,
            "gravity_communicative": enriched.get("gravity_communicative") or 0,
            "gravity_social": enriched.get("gravity_social") or 0,
        })

    target_lang_name = {"en": "English", "es": "Español"}.get(target_lang, target_lang.upper())
    target_lang_prof = {"en": "d'anglais", "es": "d'espagnol"}.get(target_lang, "")

    ctx = PromptContext(
        level=level,
        turn_count=turn_count,
        errors_detected=v2_errors,
        l1="fr",
        target_lang=target_lang,
        target_lang_name=target_lang_name,
        l1_name="français",
        fla_category=getattr(sk, "fla", None),
        self_efficacy=3,
        autonomy_pref="guided",
        post_qcm_welcome=False,
    )
    sections = lang.build_dynamic_sections(ctx)

    inputs: dict = {
        "learner_profile_summary": nl_summary,
        "learner_profile_json": lp_json,
        "lang_target_name": target_lang_name,
        "lang_target_prof": target_lang_prof,
        "concept_hints_json": "{}",
        "cefr_diagnostics_block": "",
    }
    for k, v in sections.items():
        if k.startswith("_"):
            continue
        inputs[k] = v if isinstance(v, str) else ""
    return inputs


def call_agent(agent: str, query: str, conv_seed: str | None = None,
               api_key: str | None = None, scenario=None) -> str:
    """POST to Dify public API for the given agent. Returns bot's plain-text answer.

    If `scenario` is passed, builds prod-aligned inputs via
    `build_full_dify_inputs` (Session 51 — was 2-input lobotomized scope before).
    Falls back to the minimal 2-input profile-only path on any builder failure
    so battery still runs even if academie_core import fails."""
    cfg = _cfg()
    ac = _agent_config(agent, cfg)
    key = api_key or os.environ.get(ac["env_key_name"], "")
    if not key:
        raise RuntimeError(f"env var {ac['env_key_name']} empty and no api_key passed")
    url = cfg["dify"]["public_api_base"] + cfg["dify"].get("public_api_path", "/v1/chat-messages")
    inputs: dict = {}
    if scenario is not None:
        try:
            inputs = build_full_dify_inputs(scenario, agent)
        except Exception as e:
            import logging
            logging.getLogger("oracle.dify_client").warning(
                "build_full_dify_inputs failed (%s) — falling back to 2-input profile-only", e,
            )
            nl_summary, lp_json = build_oracle_profile(scenario, agent)
            inputs = {
                "learner_profile_summary": nl_summary,
                "learner_profile_json": lp_json,
            }
    payload = {
        "query": query,
        "inputs": inputs,
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
        raw = (r.json().get("answer") or "").strip()
    # Session 51 — unwrap <output>{JSON}</output> if present so judges
    # see the feedback prose, not the structured-output dump (output_schema_block
    # is now injected via build_full_dify_inputs → LLM may return JSON-wrapped).
    # Idempotent on plain-text responses.
    if "<output>" in raw and "</output>" in raw:
        try:
            import sys as _sys
            from pathlib import Path as _Path
            _PKG = _Path("/opt/academie/packages/academie-core")
            if str(_PKG) not in _sys.path:
                _sys.path.insert(0, str(_PKG))
            from academie_core.pedagogy.teacher_prompt import parse_teacher_response
            parsed = parse_teacher_response(raw)
            if parsed.parse_ok and parsed.feedback:
                return parsed.feedback.strip()
        except Exception:
            pass
    return raw


# Backward-compat alias — older code expects call_teacher_en
def call_teacher_en(query: str, conv_seed: str | None = None, api_key: str | None = None) -> str:
    return call_agent("teacher_en", query, conv_seed, api_key)


# Legacy import target used in parts of the harness — kept as module constant
DIFY_URL = (_cfg()["dify"]["public_api_base"]
            + _cfg()["dify"].get("public_api_path", "/v1/chat-messages"))
