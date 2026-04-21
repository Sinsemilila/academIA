import pytest

from academie_core.pedagogy.consolidation import (
    ObservationHint, ErrorDistribution,
    evaluate_trigger, majority_vote_observed_level, infer_level_from_errors,
    reconcile_observations, clamp_single_step, decide_consolidation,
    msg_validation, msg_upgrade, msg_downgrade, pick_message,
    N_TURNS_CONSOLIDATION, MIN_ERROR_LOG_ENTRIES_TRIGGER,
    SOFT_REPROMPT_TURNS_AFTER_REFUSAL,
)


# ── Trigger evaluation ────────────────────────────────────────────────

def test_trigger_early_return_below_n_turns_and_error_threshold():
    dec = evaluate_trigger(
        message_count=3, error_log_count=5, niveau_status="provisoire",
        last_consolidation_turn=0, regression_watch_active=False,
        regression_watch_started_turn=None,
    )
    assert dec.should_trigger is False
    assert dec.skip_reason == "insufficient_signal"


def test_trigger_fires_at_n_turns():
    dec = evaluate_trigger(
        message_count=N_TURNS_CONSOLIDATION, error_log_count=0,
        niveau_status="provisoire", last_consolidation_turn=0,
        regression_watch_active=False, regression_watch_started_turn=None,
    )
    assert dec.should_trigger is True
    assert dec.reason == "n_turns"


def test_trigger_fires_at_error_threshold():
    dec = evaluate_trigger(
        message_count=3, error_log_count=MIN_ERROR_LOG_ENTRIES_TRIGGER,
        niveau_status="provisoire", last_consolidation_turn=0,
        regression_watch_active=False, regression_watch_started_turn=None,
    )
    assert dec.should_trigger is True
    assert dec.reason == "error_threshold"


def test_cooldown_prevents_re_trigger():
    dec = evaluate_trigger(
        message_count=15, error_log_count=30, niveau_status="provisoire",
        last_consolidation_turn=10,  # only 5 turns ago
        regression_watch_active=False, regression_watch_started_turn=None,
    )
    assert dec.should_trigger is False
    assert dec.skip_reason == "cooldown"


def test_validated_locks_out_unless_regression_watch():
    dec = evaluate_trigger(
        message_count=50, error_log_count=100, niveau_status="validé",
        last_consolidation_turn=20, regression_watch_active=False,
        regression_watch_started_turn=None,
    )
    assert dec.should_trigger is False
    assert dec.skip_reason == "already_validated"


def test_calibration_en_cours_awaits_user():
    dec = evaluate_trigger(
        message_count=20, error_log_count=50, niveau_status="calibration_en_cours",
        last_consolidation_turn=10, regression_watch_active=False,
        regression_watch_started_turn=None,
    )
    assert dec.should_trigger is False
    assert dec.skip_reason == "awaiting_user_decision"


def test_stabilisation_volontaire_requires_wait():
    dec = evaluate_trigger(
        message_count=15, error_log_count=40, niveau_status="stabilisation_volontaire",
        last_consolidation_turn=10, regression_watch_active=False,
        regression_watch_started_turn=None,
    )
    assert dec.should_trigger is False
    assert dec.skip_reason == "stabilisation_cooldown"


def test_stabilisation_reprompt_after_enough_turns():
    dec = evaluate_trigger(
        message_count=10 + SOFT_REPROMPT_TURNS_AFTER_REFUSAL + 1, error_log_count=40,
        niveau_status="stabilisation_volontaire", last_consolidation_turn=10,
        regression_watch_active=False, regression_watch_started_turn=None,
    )
    assert dec.should_trigger is True


def test_regression_watch_fires_trigger():
    dec = evaluate_trigger(
        message_count=52, error_log_count=5, niveau_status="validé",
        last_consolidation_turn=50, regression_watch_active=True,
        regression_watch_started_turn=50,
    )
    assert dec.should_trigger is True
    assert dec.reason == "dormancy_regression"


# ── Aggregation ───────────────────────────────────────────────────────

def test_majority_vote_observed_level():
    hints = [
        ObservationHint(1, "A2"), ObservationHint(2, ""),
        ObservationHint(3, "A2"), ObservationHint(4, "B1"),
        ObservationHint(5, "A2"),
    ]
    assert majority_vote_observed_level(hints) == "A2"


def test_majority_vote_all_empty_returns_empty():
    hints = [ObservationHint(i, "") for i in range(5)]
    assert majority_vote_observed_level(hints) == ""


def test_infer_level_from_errors_dominant_level():
    dist = ErrorDistribution(per_level={"A1": 1, "A2": 8, "B1": 1})
    assert infer_level_from_errors(dist) == "A2"


def test_infer_level_from_errors_no_dominant():
    dist = ErrorDistribution(per_level={"A1": 3, "A2": 3, "B1": 4})
    assert infer_level_from_errors(dist) == ""  # no 50%+


def test_infer_level_from_errors_too_few_samples():
    dist = ErrorDistribution(per_level={"A2": 2, "B1": 1})
    assert infer_level_from_errors(dist) == ""


def test_reconcile_both_empty_returns_empty():
    assert reconcile_observations("", "", "A2") == ""


def test_reconcile_one_empty():
    assert reconcile_observations("B1", "", "A2") == "B1"
    assert reconcile_observations("", "A2", "A2") == "A2"


def test_reconcile_disagree_picks_lower():
    assert reconcile_observations("B1", "A2", "A2") == "A2"
    assert reconcile_observations("A1", "A2", "A1") == "A1"


def test_reconcile_agree():
    assert reconcile_observations("B1", "B1", "A2") == "B1"


def test_clamp_single_step_upgrade_limited():
    # QCM A1, observed B2 → must clamp to A2
    assert clamp_single_step("A1", "B2") == "A2"


def test_clamp_single_step_downgrade_limited():
    # QCM B2, observed A1 → must clamp to B1
    assert clamp_single_step("B2", "A1") == "B1"


def test_clamp_single_step_within_one_step_unchanged():
    assert clamp_single_step("A2", "B1") == "B1"
    assert clamp_single_step("B1", "A2") == "A2"


# ── Decision ──────────────────────────────────────────────────────────

def test_decide_auto_validate_when_obs_equals_qcm():
    hints = [ObservationHint(i, "A2") for i in range(5)]
    dist = ErrorDistribution(per_level={"A2": 10})
    outcome = decide_consolidation(
        qcm_level="A2", observation_hints=hints, error_distribution=dist,
        message_count=8, trigger_reason="n_turns",
    )
    assert outcome.kind == "auto_validate"
    assert outcome.qcm_level == "A2"
    assert outcome.observed_level == "A2"


def test_decide_propose_mini_exam_when_obs_differs():
    hints = [ObservationHint(i, "B1") for i in range(5)]
    dist = ErrorDistribution(per_level={"B1": 10})
    outcome = decide_consolidation(
        qcm_level="A2", observation_hints=hints, error_distribution=dist,
        message_count=8, trigger_reason="n_turns",
    )
    assert outcome.kind == "propose_mini_exam"
    assert outcome.decision_payload["mini_exam_target_level"] == "B1"


def test_decide_noop_on_insufficient_signal():
    outcome = decide_consolidation(
        qcm_level="A2", observation_hints=[ObservationHint(1, "")],
        error_distribution=ErrorDistribution(per_level={}),
        message_count=8, trigger_reason="n_turns",
    )
    assert outcome.kind == "noop"


def test_decide_respects_clamp_on_big_jump():
    hints = [ObservationHint(i, "C1") for i in range(5)]
    dist = ErrorDistribution(per_level={"C1": 10})
    outcome = decide_consolidation(
        qcm_level="A1", observation_hints=hints, error_distribution=dist,
        message_count=8, trigger_reason="n_turns",
    )
    # A1 + obs C1 → clamped to A2
    assert outcome.observed_level == "A2"


# ── Messages ──────────────────────────────────────────────────────────

def test_msg_validation_includes_level_and_n():
    m = msg_validation(8, "A2")
    assert "8 échanges" in m
    assert "A2" in m
    assert "validé" in m


def test_msg_upgrade_mentions_both_levels_and_choice():
    m = msg_upgrade(8, "A2", "B1")
    assert "A2" in m and "B1" in m
    assert "Deux options" in m
    assert "consolider" in m


def test_msg_downgrade_is_bienveillant():
    m = msg_downgrade(8, "B1", "A2")
    assert "B1" in m and "A2" in m
    # Tone markers: formulations bienveillantes, pas "tu es nul"
    assert "tout à fait normal" in m
    assert "c'est toi qui décides" in m


def test_pick_message_dispatches_correctly():
    from academie_core.pedagogy.consolidation import ConsolidationOutcome
    auto = ConsolidationOutcome("auto_validate", "A2", "A2", {})
    up = ConsolidationOutcome("propose_mini_exam", "A2", "B1", {})
    down = ConsolidationOutcome("propose_mini_exam", "B1", "A2", {})

    assert "validé" in pick_message(auto, 8)
    assert "Félicitations" in pick_message(up, 8)
    assert "tout à fait normal" in pick_message(down, 8)
    assert pick_message(ConsolidationOutcome("noop", "", "", {}), 0) == ""
