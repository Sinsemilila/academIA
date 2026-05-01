"""Phase 2 — multi-judge panel cross-provider tests.

Mocks `_call_judge` to return predictable votes per panel member.
Validates :
- Cross-judge majority logic (3/3 unanimous, 2/3 majority, split)
- Vote tagging with `_judge_model`
- Failure mode : 1 provider returns None for all votes → degraded 2/3
- Backward compat : single-judge mode unchanged when panel_models=None
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from scripts.oracle.judges import llm_pairwise as lp

# ── Cross-judge majority unit tests ─────────────────────────────────


def test_cross_judge_unanimous():
    """All 3 judges agree on `full_recast` → cross_ratio = 1.0."""
    votes = [
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j2", "move": "full_recast"},
        {"_judge_model": "j2", "move": "full_recast"},
        {"_judge_model": "j3", "move": "full_recast"},
        {"_judge_model": "j3", "move": "full_recast"},
    ]
    winner, ratio = lp._cross_judge_majority(votes, lp._majority_move)
    assert winner == "full_recast"
    assert ratio == 1.0


def test_cross_judge_2_of_3_majority():
    """2 judges say `recast`, 1 says `elicitation` → cross_ratio = 2/3."""
    votes = [
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j2", "move": "full_recast"},
        {"_judge_model": "j2", "move": "elicitation"},  # j2 split, majority recast
        {"_judge_model": "j3", "move": "elicitation"},
        {"_judge_model": "j3", "move": "elicitation"},
    ]
    winner, ratio = lp._cross_judge_majority(votes, lp._majority_move)
    assert winner == "full_recast"
    assert ratio == pytest.approx(2 / 3, abs=1e-6)


def test_cross_judge_one_judge_fails():
    """j2 returned no parseable votes → degraded mode 2 active judges."""
    votes = [
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j1", "move": "full_recast"},
        # j2 absent (provider 429 or empty)
        {"_judge_model": "j3", "move": "full_recast"},
        {"_judge_model": "j3", "move": "elicitation"},  # j3 split, majority recast
    ]
    winner, ratio = lp._cross_judge_majority(votes, lp._majority_move)
    assert winner == "full_recast"
    # Only 2 judges with signal → 2/2
    assert ratio == 1.0


def test_cross_judge_no_signal():
    """All judges returned no parseable verdicts → (None, 0.0)."""
    votes: list = []
    winner, ratio = lp._cross_judge_majority(votes, lp._majority_move)
    assert winner is None
    assert ratio == 0.0


def test_cross_judge_three_way_split():
    """3 judges, each says different move → arbitrary winner, ratio=1/3."""
    votes = [
        {"_judge_model": "j1", "move": "full_recast"},
        {"_judge_model": "j2", "move": "elicitation"},
        {"_judge_model": "j3", "move": "metalinguistic"},
    ]
    winner, ratio = lp._cross_judge_majority(votes, lp._majority_move)
    assert winner in {"full_recast", "elicitation", "metalinguistic"}
    assert ratio == pytest.approx(1 / 3, abs=1e-6)


def test_group_by_judge():
    """Vote grouping by `_judge_model` tag."""
    votes = [
        {"_judge_model": "a", "x": 1},
        {"_judge_model": "b", "x": 2},
        {"_judge_model": "a", "x": 3},
    ]
    grouped = lp._group_by_judge(votes)
    assert set(grouped.keys()) == {"a", "b"}
    assert len(grouped["a"]) == 2
    assert len(grouped["b"]) == 1


# ── Bool variant (for semantic_fidelity_pairwise) ───────────────────


def test_cross_judge_bool_majority():
    """Bool key partial via lambda, 2/3 say equivalent=True."""
    votes = [
        {"_judge_model": "j1", "equivalent": True},
        {"_judge_model": "j1", "equivalent": True},
        {"_judge_model": "j2", "equivalent": False},
        {"_judge_model": "j3", "equivalent": True},
    ]
    winner, ratio = lp._cross_judge_majority(
        votes, lambda vs: lp._majority_bool(vs, "equivalent"),
    )
    assert winner is True
    assert ratio == pytest.approx(2 / 3, abs=1e-6)


# ── Backward compat : single-judge mode unchanged ───────────────────


def test_single_judge_majority_unchanged():
    """When panel_models=None, _majority_move on flat list still works."""
    votes = [
        {"move": "full_recast"},
        {"move": "full_recast"},
        {"move": "elicitation"},
    ]
    winner, ratio = lp._majority_move(votes)
    assert winner == "full_recast"
    assert ratio == pytest.approx(2 / 3, abs=1e-6)


# ── _vote_panel integration test (mocked _call_judge) ───────────────


def test_vote_panel_tags_each_vote():
    """_vote_panel calls _call_judge per model, tags vote with _judge_model."""
    panel_models = ["judge_a", "judge_b", "judge_c"]
    n_per_judge = 2

    call_count = {"i": 0}

    async def fake_call_judge(client, cfg, messages, model_override=None):
        call_count["i"] += 1
        # Return distinct votes so we can verify tagging
        return {"move": f"move_from_{model_override}"}

    async def run():
        with patch.object(lp, "_call_judge", side_effect=fake_call_judge):
            return await lp._vote_panel(
                client=None, cfg={"judge": {"model": "default"}},
                messages=[], n_per_judge=n_per_judge, panel_models=panel_models,
            )

    votes = asyncio.run(run())
    # 3 models × 2 votes = 6 calls
    assert call_count["i"] == 6
    assert len(votes) == 6
    # Each vote tagged with its model
    by_model = lp._group_by_judge(votes)
    assert set(by_model.keys()) == set(panel_models)
    for model in panel_models:
        assert len(by_model[model]) == 2
        assert all(v["move"] == f"move_from_{model}" for v in by_model[model])


def test_vote_panel_drops_failed_judge():
    """If _call_judge returns None for a model, no vote tagged with that model."""
    panel_models = ["judge_a", "judge_b"]

    async def fake_call_judge(client, cfg, messages, model_override=None):
        if model_override == "judge_b":
            return None  # provider 429 or parse failure
        return {"move": "elicitation"}

    async def run():
        with patch.object(lp, "_call_judge", side_effect=fake_call_judge):
            return await lp._vote_panel(
                client=None, cfg={"judge": {"model": "default"}},
                messages=[], n_per_judge=3, panel_models=panel_models,
            )

    votes = asyncio.run(run())
    by_model = lp._group_by_judge(votes)
    assert by_model.get("judge_a", []) and len(by_model["judge_a"]) == 3
    assert "judge_b" not in by_model  # all calls returned None
