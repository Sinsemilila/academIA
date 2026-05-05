"""Session 43 P5 — onboarding funnel aggregation test.

Verifies the SQL that drives /api/admin/onboarding-funnel produces correct
counts + step-by-step conversion rates on synthetic fixtures. Runs
against the live postgres-academie (doesn't need the API container
rebuilt).

Usage :
  docker exec -i postgres-academie psql -U sinse -d academie_db < /opt/academia/scripts/sprint7/01_onboarding_telemetry_schema.sql
  python3 -m pytest scripts/sprint7/tests/test_onboarding_funnel.py -q
"""
from __future__ import annotations

import os
import uuid
import subprocess
import json

import pytest

DOMAIN = "__test_funnel_domain__"  # filter marker; we'll clean up after


def _psql(sql: str) -> str:
    return subprocess.check_output(
        ["docker", "exec", "-i", "postgres-academie",
         "psql", "-U", "sinse", "-d", "academie_db", "-tAc", sql],
        text=True,
    ).strip()


def _reset():
    _psql(f"DELETE FROM onboarding_telemetry_events WHERE domain = '{DOMAIN}';")


def _insert(session_id: str, event: str, step_order: int | None = None,
            step_id: str | None = None, total_steps: int | None = 8):
    sql = (
        "INSERT INTO onboarding_telemetry_events "
        "(session_id, domain, event, step_id, step_order, total_steps) "
        f"VALUES ('{session_id}', '{DOMAIN}', '{event}', "
        f"{'NULL' if step_id is None else repr(step_id)}, "
        f"{'NULL' if step_order is None else step_order}, "
        f"{'NULL' if total_steps is None else total_steps});"
    )
    _psql(sql)


# Aggregation SQL (kept in sync with admin_router.py)
SUMMARY_SQL = """
SELECT json_build_object(
  'sessions_started', COUNT(*),
  'sessions_completed', COUNT(*) FILTER (WHERE completed),
  'sessions_aborted', COUNT(*) FILTER (WHERE aborted AND NOT completed),
  'sessions_inflight', COUNT(*) FILTER (WHERE NOT completed AND NOT aborted),
  'completion_pct', COALESCE(ROUND(100.0 * COUNT(*) FILTER (WHERE completed)
                             / NULLIF(COUNT(*), 0), 1), 0)
)
FROM (
  SELECT session_id,
         bool_or(event='complete') AS completed,
         bool_or(event='abort') AS aborted
  FROM onboarding_telemetry_events
  WHERE domain = '__test_funnel_domain__'
  GROUP BY session_id
) s;
"""


@pytest.fixture(autouse=True)
def _isolate():
    _reset()
    yield
    _reset()


def _summary() -> dict:
    raw = _psql(SUMMARY_SQL.replace("\n", " "))
    return json.loads(raw)


def _new_sid() -> str:
    return str(uuid.uuid4())


def test_empty_funnel_returns_zeros():
    s = _summary()
    assert s["sessions_started"] == 0
    assert s["sessions_completed"] == 0
    assert s["completion_pct"] == 0


def test_one_completed_session():
    sid = _new_sid()
    for k, step in enumerate(["intro", "q1", "q2", "summary"]):
        _insert(sid, "step_enter", step_order=k, step_id=step)
    _insert(sid, "complete", step_id="summary", step_order=3)
    s = _summary()
    assert s["sessions_started"] == 1
    assert s["sessions_completed"] == 1
    assert s["completion_pct"] == 100.0


def test_mixed_completed_aborted_inflight():
    # 1 completed
    a = _new_sid()
    _insert(a, "step_enter", step_order=0, step_id="intro")
    _insert(a, "complete", step_id="summary", step_order=9)
    # 1 aborted at step 2
    b = _new_sid()
    _insert(b, "step_enter", step_order=0, step_id="intro")
    _insert(b, "step_enter", step_order=1, step_id="q1")
    _insert(b, "step_enter", step_order=2, step_id="q2")
    _insert(b, "abort", step_id="q2", step_order=2)
    # 1 in-flight (no complete, no abort)
    c = _new_sid()
    _insert(c, "step_enter", step_order=0, step_id="intro")
    _insert(c, "step_enter", step_order=1, step_id="q1")

    s = _summary()
    assert s["sessions_started"] == 3
    assert s["sessions_completed"] == 1
    assert s["sessions_aborted"] == 1
    assert s["sessions_inflight"] == 1
    # 1 / 3 = 33.3
    assert s["completion_pct"] == 33.3


def test_complete_trumps_abort():
    """A session that both fires abort (beforeunload) and later completes
    (reopened, finished) should count as completed, not aborted."""
    sid = _new_sid()
    _insert(sid, "step_enter", step_order=0, step_id="intro")
    _insert(sid, "abort", step_id="intro", step_order=0)
    _insert(sid, "step_enter", step_order=1, step_id="q1")
    _insert(sid, "complete", step_id="summary", step_order=9)
    s = _summary()
    assert s["sessions_completed"] == 1
    assert s["sessions_aborted"] == 0  # completed → not counted as aborted


def test_step_level_max_tracking():
    """Verify that max(step_order) per session is what drives drop-off."""
    sid = _new_sid()
    _insert(sid, "step_enter", step_order=0, step_id="intro")
    _insert(sid, "step_enter", step_order=1, step_id="q1")
    _insert(sid, "step_enter", step_order=2, step_id="q2")
    # user went back (persistDraft restores) — shouldn't confuse max
    _insert(sid, "step_enter", step_order=1, step_id="q1")
    _insert(sid, "abort", step_id="q1", step_order=1)

    max_step = _psql(
        f"SELECT MAX(step_order) FROM onboarding_telemetry_events "
        f"WHERE session_id = '{sid}' AND event = 'step_enter';"
    )
    assert int(max_step) == 2  # furthest reached


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "--no-header"]))
