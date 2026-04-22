"""Session 42 P2 — tests for dormancy regression watch activation.

Pure-function tests on `should_activate_dormancy_watch` — no DB mocking,
no async. Covers 6 cases from the decision tree.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from academie_core.pedagogy.consolidation import should_activate_dormancy_watch

_NOW = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("case,niveau_status,watch_active,validated_days_ago,last_seen_days_ago,expected", [
    # Happy path : validated 30+ days ago + silence ≥ 7 days → activate
    ("dormant_validated_returns", "validé", False, 45, 10, True),
    # Not yet validated → no watch
    ("provisoire", "provisoire", False, 45, 10, False),
    # Already in calibration → no watch
    ("calibration_already", "calibration_en_cours", False, 45, 10, False),
    # Already watching → don't re-activate
    ("already_watching", "validé", True, 45, 10, False),
    # Validated < 30d ago → too fresh to worry about dormancy
    ("too_recent_validation", "validé", False, 10, 10, False),
    # Actively chatting (last_seen < 7 days) → not dormant
    ("recently_active", "validé", False, 45, 2, False),
    # Validated 30+ days ago, never seen (edge case) → activate
    ("never_seen_after_validation", "validé", False, 45, None, True),
])
def test_dormancy_activation_cases(case, niveau_status, watch_active,
                                   validated_days_ago, last_seen_days_ago, expected):
    validated_at = _NOW - timedelta(days=validated_days_ago)
    last_seen = _NOW - timedelta(days=last_seen_days_ago) if last_seen_days_ago is not None else None
    got = should_activate_dormancy_watch(
        niveau_status=niveau_status,
        regression_watch_active=watch_active,
        niveau_validated_at=validated_at,
        last_seen_at=last_seen,
        now=_NOW,
    )
    assert got is expected, f"{case}: expected {expected}, got {got}"


def test_dormancy_no_validation_date():
    """If niveau_validated_at is None, don't activate."""
    assert not should_activate_dormancy_watch(
        niveau_status="validé",
        regression_watch_active=False,
        niveau_validated_at=None,
        last_seen_at=_NOW - timedelta(days=45),
        now=_NOW,
    )


def test_dormancy_custom_threshold():
    """threshold_days kwarg overrides the default 30."""
    validated_at = _NOW - timedelta(days=10)
    # 10 days ago — not dormant at default 30d, but dormant at 7d threshold
    assert should_activate_dormancy_watch(
        niveau_status="validé",
        regression_watch_active=False,
        niveau_validated_at=validated_at,
        last_seen_at=_NOW - timedelta(days=8),
        now=_NOW,
        threshold_days=7,
    )
