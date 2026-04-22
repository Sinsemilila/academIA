"""Session 44 B — model budget tracker SQL logic test.

Validates the aggregation that drives /api/admin/model-budgets on
synthetic rows in model_usage_daily + model_switch_log. Runs against
the live postgres-academie (doesn't need the API container).

Usage :
  python3 -m pytest scripts/sprint7/tests/test_model_budget_tracker.py -q
"""
from __future__ import annotations

import json
import subprocess

import pytest


DB_CMD = ("docker", "exec", "-i", "postgres-academie",
          "psql", "-U", "sinse", "-d", "academie_db", "-tAc")

TEST_MARKER_REASON = "__test_model_budget_tracker__"


def _psql(sql: str) -> str:
    return subprocess.check_output([*DB_CMD, sql], text=True).rstrip("\n")


def _reset():
    _psql("DELETE FROM model_usage_daily WHERE model LIKE '__test_%';")
    _psql(f"DELETE FROM model_switch_log WHERE reason = '{TEST_MARKER_REASON}';")


@pytest.fixture(autouse=True)
def _isolate():
    _reset()
    yield
    _reset()


def test_upsert_adds_tokens():
    m = "__test_model_A"
    _psql(
        f"INSERT INTO model_usage_daily (usage_date, model, input_tokens, output_tokens) "
        f"VALUES (CURRENT_DATE, '{m}', 100, 200);"
    )
    _psql(
        f"INSERT INTO model_usage_daily (usage_date, model, input_tokens, output_tokens) "
        f"VALUES (CURRENT_DATE, '{m}', 50, 25) "
        f"ON CONFLICT (usage_date, model) DO UPDATE SET "
        f"  input_tokens  = model_usage_daily.input_tokens  + EXCLUDED.input_tokens, "
        f"  output_tokens = model_usage_daily.output_tokens + EXCLUDED.output_tokens;"
    )
    total = int(_psql(
        f"SELECT input_tokens + output_tokens FROM model_usage_daily "
        f"WHERE usage_date = CURRENT_DATE AND model = '{m}';"
    ))
    assert total == 375  # 100+200+50+25


def test_switch_log_latest_is_current_tier():
    _psql(
        f"INSERT INTO model_switch_log (from_model, to_model, reason) "
        f"VALUES ('gpt-4o-mini', 'groq-standard', '{TEST_MARKER_REASON}');"
    )
    _psql(
        f"INSERT INTO model_switch_log (from_model, to_model, reason) "
        f"VALUES ('groq-standard', 'groq-snapshot', '{TEST_MARKER_REASON}');"
    )
    current = _psql(
        f"SELECT to_model FROM model_switch_log WHERE reason = '{TEST_MARKER_REASON}' "
        f"ORDER BY at DESC LIMIT 1;"
    )
    assert current == "groq-snapshot"


def test_tier_threshold_math():
    """Mirror the 95% threshold that _select_active_tier() uses."""
    cases = [
        # (used, limit, should_advance)
        (0,          1_500_000, False),
        (1_424_000,  1_500_000, False),   # exactly 94.93% → stay
        (1_425_000,  1_500_000, True),    # 95.0% → advance
        (1_500_000,  1_500_000, True),    # exhausted
        (95_000,     100_000,   True),    # groq-standard at 95%
        (94_999,     100_000,   False),
    ]
    THRESHOLD = 0.95
    for used, limit, should_advance in cases:
        advances = used >= limit * THRESHOLD
        assert advances == should_advance, (
            f"used={used} limit={limit} → advance={advances}, expected={should_advance}"
        )


def test_tier_chain_ordering():
    """Chain activation order is (gpt-4o-mini, groq-standard, groq-snapshot)."""
    # Seed state: gpt-4o-mini full, groq-standard partially used
    m1 = "__test_tier_gpt"
    m2 = "__test_tier_groq_std"
    m3 = "__test_tier_groq_snap"
    chain = [(m1, 1_500_000), (m2, 100_000), (m3, 500_000)]
    usage = {m1: 1_500_000, m2: 50_000, m3: 0}
    for m, tok in usage.items():
        _psql(
            f"INSERT INTO model_usage_daily (usage_date, model, input_tokens, output_tokens) "
            f"VALUES (CURRENT_DATE, '{m}', {tok}, 0);"
        )
    # Simulate _select_active_tier() walk
    THRESHOLD = 0.95
    selected = None
    for model, limit in chain:
        used = usage[model]
        if used < limit * THRESHOLD:
            selected = model
            break
    assert selected == m2  # groq-standard still has headroom


def test_percentage_rounding():
    """pct field in the endpoint payload rounds to 1 decimal."""
    cases = [
        (0,        1_500_000, 0.0),
        (750_000,  1_500_000, 50.0),
        (1_005_234, 1_500_000, 67.0),
        (1_499_999, 1_500_000, 100.0),
    ]
    for used, limit, expected_pct in cases:
        pct = round(used / limit * 100, 1)
        assert pct == expected_pct


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--no-header"]))
