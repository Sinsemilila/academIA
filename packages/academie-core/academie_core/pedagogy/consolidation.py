"""CEFR level consolidation (Session 36).

After N chat turns, reconcile QCM-declared level vs. observation:
- OBS == QCM → auto-validate (badge provisoire → validé)
- OBS != QCM → trigger mini-exam; present bienveillant choice to learner

Grounded in Bull & Kay (2016) Open Learner Model negotiability principle +
Ross (1998) self-assessment correlation literature + CEFR 2020 Companion
Volume mediation descriptors.

See `docs/01-pedagogy/cefr-consolidation-policy.md` for the full doctrine.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter
from typing import Literal, Optional

# ── Constants (tuneable) ───────────────────────────────────────────────
N_TURNS_CONSOLIDATION = 8
MIN_ERROR_LOG_ENTRIES_TRIGGER = 20
CONSOLIDATION_COOLDOWN_TURNS = 10
DORMANCY_THRESHOLD_DAYS = 30
REGRESSION_WATCH_TURNS = 5
MINI_EXAM_ITEMS = 8
MINI_EXAM_PASS_THRESHOLD = 0.75   # 6/8 correct
SOFT_REPROMPT_TURNS_AFTER_REFUSAL = 20

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
CEFR_INDEX = {lvl: i for i, lvl in enumerate(CEFR_ORDER)}

NiveauStatus = Literal[
    "provisoire", "calibration_en_cours", "validé",
    "stabilisation_volontaire", "a_recalibrer",
]

TriggerReason = Literal["n_turns", "error_threshold", "dormancy_regression"]


# ── Dormancy regression activation ────────────────────────────────────

def should_activate_dormancy_watch(
    niveau_status: NiveauStatus,
    regression_watch_active: bool,
    niveau_validated_at,
    last_seen_at,
    now,
    threshold_days: int = DORMANCY_THRESHOLD_DAYS,
) -> bool:
    """Session 42 P2 — pure decision : should we flip regression_watch_active=true
    because the learner validated their level ≥ threshold_days ago and is
    returning after a dormant window ?

    Inputs are datetimes OR None. If niveau_validated_at is None or the
    status isn't 'validé', no watch. If watch is already active, no-op
    (caller shouldn't re-activate).
    """
    if regression_watch_active:
        return False
    if niveau_status != "validé":
        return False
    if niveau_validated_at is None:
        return False
    # Gap since validation — learner must have been "stable validated" for long enough
    gap_days = (now - niveau_validated_at).days
    if gap_days < threshold_days:
        return False
    # Last seen gap — only fire if there's been silence recently (dormant)
    # (prevents re-firing when learner chats daily after validation)
    if last_seen_at is not None:
        silence_days = (now - last_seen_at).days
        if silence_days < 7:  # active recently → not dormant
            return False
    return True


# ── Domain types ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ObservationHint:
    turn: int
    observed_level: str   # CEFR string, "" if uncertain


@dataclass(frozen=True)
class ErrorDistribution:
    # maps CEFR level → number of errors at that criterial level in window
    per_level: dict[str, int]

    def total(self) -> int:
        return sum(self.per_level.values())


@dataclass(frozen=True)
class TriggerDecision:
    should_trigger: bool
    reason: Optional[TriggerReason] = None
    skip_reason: str = ""


@dataclass(frozen=True)
class ConsolidationOutcome:
    kind: Literal["auto_validate", "propose_mini_exam", "noop"]
    qcm_level: str
    observed_level: str
    decision_payload: dict      # snapshot to store in consolidation_decision_pending


# ── Trigger evaluation ────────────────────────────────────────────────

def evaluate_trigger(
    message_count: int,
    error_log_count: int,
    niveau_status: NiveauStatus,
    last_consolidation_turn: int,
    regression_watch_active: bool,
    regression_watch_started_turn: Optional[int],
) -> TriggerDecision:
    """Decide whether to run a consolidation pass on this turn.

    Early returns when status locks us out, cooldown not elapsed, or not enough
    signal yet. Dormancy regression watch opens its own trigger window.
    """
    # Lock-out states (no consolidation while already engaged or settled hard)
    if niveau_status in ("calibration_en_cours",):
        return TriggerDecision(False, skip_reason="awaiting_user_decision")
    if niveau_status == "validé" and not regression_watch_active:
        return TriggerDecision(False, skip_reason="already_validated")
    if niveau_status == "stabilisation_volontaire":
        # Soft re-prompt allowed after enough extra turns since the refusal
        if message_count - last_consolidation_turn < SOFT_REPROMPT_TURNS_AFTER_REFUSAL:
            return TriggerDecision(False, skip_reason="stabilisation_cooldown")
        # else fall through and re-trigger

    # Regression watch path
    if regression_watch_active and regression_watch_started_turn is not None:
        if message_count - regression_watch_started_turn <= REGRESSION_WATCH_TURNS:
            return TriggerDecision(True, reason="dormancy_regression")
        # window expired — caller should clear the flag

    # Cooldown (avoid re-evaluating every turn once we've started)
    if last_consolidation_turn and message_count - last_consolidation_turn < CONSOLIDATION_COOLDOWN_TURNS:
        return TriggerDecision(False, skip_reason="cooldown")

    # Signal thresholds — fire if either hits
    if message_count >= N_TURNS_CONSOLIDATION:
        return TriggerDecision(True, reason="n_turns")
    if error_log_count >= MIN_ERROR_LOG_ENTRIES_TRIGGER:
        return TriggerDecision(True, reason="error_threshold")

    return TriggerDecision(False, skip_reason="insufficient_signal")


# ── Observation aggregation ───────────────────────────────────────────

def majority_vote_observed_level(hints: list[ObservationHint]) -> str:
    """Return the most-common non-empty observed_level, empty string if none."""
    filtered = [h.observed_level for h in hints if h.observed_level]
    if not filtered:
        return ""
    counter = Counter(filtered)
    return counter.most_common(1)[0][0]


def infer_level_from_errors(dist: ErrorDistribution) -> str:
    """Heuristic: the level where ≥60% of errors accumulate = the learner's current working level.

    Interpretation: if most of the learner's errors are tagged as A2 emergence,
    they are struggling at A2 → A2 is their current level (haven't mastered it yet).
    Returns "" if no dominant level or insufficient data.
    """
    total = dist.total()
    if total < 5:
        return ""
    # find argmax
    top_level, top_count = "", 0
    for lvl, cnt in dist.per_level.items():
        if cnt > top_count:
            top_level, top_count = lvl, cnt
    if top_level and (top_count / total) >= 0.5:
        return top_level
    return ""


def reconcile_observations(obs_llm: str, obs_errors: str, qcm_level: str) -> str:
    """Conservative consensus between LLM hint and error distribution.

    - If both agree → return their consensus.
    - If disagree by 1 step → return the *lower* of the two (conservative).
    - If one is empty → return the other.
    - If both empty → return "" (no signal; caller decides — typically noop).
    """
    if not obs_llm and not obs_errors:
        return ""
    if not obs_llm:
        return obs_errors
    if not obs_errors:
        return obs_llm
    if obs_llm == obs_errors:
        return obs_llm
    # Disagree: pick the lower (conservative — avoid declaring user higher than they demonstrably are)
    ia, ie = CEFR_INDEX.get(obs_llm, 2), CEFR_INDEX.get(obs_errors, 2)
    return obs_llm if ia < ie else obs_errors


def clamp_single_step(qcm_level: str, observed_level: str) -> str:
    """Limit CEFR jumps to max ±1 per episode (anti-whiplash, recommendation #6)."""
    if not qcm_level or not observed_level:
        return observed_level
    qi = CEFR_INDEX.get(qcm_level)
    oi = CEFR_INDEX.get(observed_level)
    if qi is None or oi is None:
        return observed_level
    if oi > qi + 1:
        return CEFR_ORDER[qi + 1]
    if oi < qi - 1:
        return CEFR_ORDER[qi - 1]
    return observed_level


# ── Main decision ─────────────────────────────────────────────────────

def decide_consolidation(
    qcm_level: str,
    observation_hints: list[ObservationHint],
    error_distribution: ErrorDistribution,
    message_count: int,
    trigger_reason: TriggerReason,
) -> ConsolidationOutcome:
    """Produce the outcome of a consolidation pass.

    Returns one of:
    - auto_validate : OBS == QCM → write niveau_global, flip status to validé
    - propose_mini_exam : OBS ≠ QCM → snapshot pending decision, frontend opens modal
    - noop : insufficient signal (shouldn't happen if evaluate_trigger returned True,
                                  but guard anyway)
    """
    obs_llm = majority_vote_observed_level(observation_hints)
    obs_errors = infer_level_from_errors(error_distribution)
    raw_observed = reconcile_observations(obs_llm, obs_errors, qcm_level)

    if not raw_observed:
        return ConsolidationOutcome(
            kind="noop", qcm_level=qcm_level, observed_level="",
            decision_payload={},
        )

    observed = clamp_single_step(qcm_level, raw_observed)

    if observed == qcm_level:
        return ConsolidationOutcome(
            kind="auto_validate",
            qcm_level=qcm_level, observed_level=observed,
            decision_payload={
                "qcm": qcm_level, "observed": observed,
                "n_turns": message_count, "trigger_reason": trigger_reason,
            },
        )

    # Mismatch → mini-exam proposal
    return ConsolidationOutcome(
        kind="propose_mini_exam",
        qcm_level=qcm_level, observed_level=observed,
        decision_payload={
            "qcm": qcm_level,
            "observed": observed,
            "n_turns": message_count,
            "trigger_reason": trigger_reason,
            "mini_exam_target_level": observed,
        },
    )


# ── Bienveillant messages (prof Alliance Française) ───────────────────

def msg_validation(n_turns: int, level: str) -> str:
    return (
        f"Après ces {n_turns} échanges, j'ai pu confirmer ton niveau {level}. "
        f"Tes auto-évaluations étaient justes — bravo pour cette lucidité, "
        f"c'est un vrai atout d'apprenant·e. Ton badge passe de *provisoire* "
        f"à *validé*. On continue sur cette lancée."
    )


def msg_upgrade(n_turns: int, qcm_level: str, observed_level: str) -> str:
    return (
        f"J'ai observé tes productions sur les {n_turns} derniers échanges et, "
        f"après ce petit test de consolidation, je constate que tu manies déjà "
        f"les structures du niveau {observed_level}. Félicitations, tu as "
        f"progressé plus vite que tu ne le pensais ! Deux options s'offrent à "
        f"toi : on passe officiellement en {observed_level} et on attaque les "
        f"objectifs de ce niveau, ou on reste un peu en {qcm_level} pour "
        f"consolider certaines bases avant de monter. Qu'est-ce qui te semble "
        f"le plus juste ?"
    )


def msg_downgrade(n_turns: int, qcm_level: str, observed_level: str) -> str:
    return (
        f"J'ai observé tes productions sur les {n_turns} derniers échanges et "
        f"j'ai remarqué que certaines structures du niveau {qcm_level} ne sont "
        f"pas encore totalement acquises — c'est tout à fait normal, la "
        f"progression n'est jamais linéaire. Je te propose deux options : soit "
        f"on repart sur {observed_level} pour renforcer ces fondations avant "
        f"de remonter (mon conseil, mais c'est toi qui décides), soit on "
        f"continue en {qcm_level} et on travaille les points faibles au fil "
        f"de l'eau. Qu'est-ce que tu préfères ?"
    )


def msg_validation_after_failed_exam(
    n_turns: int, qcm_level: str, tested_level: str
) -> str:
    """Session 37 Fix B : distinct message for auto_validate path following
    a failed mini-exam.

    Session 36 reused `msg_validation` here, congratulating the learner on
    "accurate self-assessment" — inappropriate when they were actually
    observed higher, tested, and failed. This message instead acknowledges
    the test + reassures about staying at QCM level.
    """
    return (
        f"Après ces {n_turns} échanges, j'ai proposé un petit test "
        f"{tested_level} pour voir si tu étais prêt·e à passer. Les structures "
        f"de ce niveau ne sont pas tout à fait stables — c'est normal, ça se "
        f"consolide avec la pratique. On reste en {qcm_level} sans pression, "
        f"les bases bien installées, le reste viendra naturellement."
    )


def pick_message(outcome: ConsolidationOutcome, n_turns: int) -> str:
    """Dispatch to the right bienveillant message based on outcome."""
    if outcome.kind == "auto_validate":
        return msg_validation(n_turns, outcome.qcm_level)
    if outcome.kind == "propose_mini_exam":
        qi = CEFR_INDEX.get(outcome.qcm_level, 0)
        oi = CEFR_INDEX.get(outcome.observed_level, 0)
        if oi > qi:
            return msg_upgrade(n_turns, outcome.qcm_level, outcome.observed_level)
        return msg_downgrade(n_turns, outcome.qcm_level, outcome.observed_level)
    return ""


# ── Session 37 Fix C — L1-indexed bubble templates for persistent thread UX ──
# Outcome kinds for the chat thread system bubbles (persisted via
# consolidation_events.notes) :
#   auto_validate_match            — QCM matched observations, no exam
#   auto_validate_after_failed_exam — mini-exam failed, stay at QCM
#   upgrade_accepted               — user accepted observed > qcm
#   downgrade_accepted             — user accepted observed < qcm
#   stay_current                   — user refused proposed change
#
# Templates are L1-indexed (read in learner's native language, regardless of
# target). FR is the baseline — all other L1s fall back to FR until explicit
# translations are added. Wave 2+: when EN/IT/DE-native learners appear, add
# a new top-level key to _BUBBLE_TEMPLATES_BY_L1 with the 5 kinds translated.

BubbleKind = Literal[
    "auto_validate_match",
    "auto_validate_after_failed_exam",
    "upgrade_accepted",
    "downgrade_accepted",
    "stay_current",
]

# Each template callable takes keyword args; all unused kwargs ignored via **_.
_BUBBLE_TEMPLATES_BY_L1: dict[str, dict[BubbleKind, callable]] = {
    "fr": {
        "auto_validate_match": lambda *, level, **_: (
            f"✓ Niveau **{level}** confirmé. On continue sur cette lancée."
        ),
        "auto_validate_after_failed_exam": lambda *, level, tested_level, **_: (
            f"✓ On reste en **{level}** pour installer tranquillement les bases "
            f"de {tested_level}. Pas de pression."
        ),
        "upgrade_accepted": lambda *, level, **_: (
            f"✓ On passe en **{level}** — je vais intégrer progressivement des "
            f"structures plus riches."
        ),
        "downgrade_accepted": lambda *, level, **_: (
            f"✓ On se pose en **{level}** pour renforcer les fondations. Les "
            f"bases d'abord, le reste viendra."
        ),
        "stay_current": lambda *, level, **_: (
            f"✓ On consolide **{level}** encore un peu. Tu retentes l'ascension "
            f"quand tu veux."
        ),
    },
    # Wave 2+: add "en": {...}, "it": {...}, ... when non-FR learners arrive.
}


def bubble_template(
    kind: BubbleKind,
    l1: str | None,
    *,
    level: str,
    tested_level: str = "",
    **_: object,
) -> str:
    """Return the short system-bubble message for the chat thread, in the
    learner's L1. Falls back to FR for any L1 not in `_BUBBLE_TEMPLATES_BY_L1`.
    `tested_level` is only used by `auto_validate_after_failed_exam`.
    """
    l1_key = (l1 or "fr").lower()
    templates = _BUBBLE_TEMPLATES_BY_L1.get(l1_key) or _BUBBLE_TEMPLATES_BY_L1["fr"]
    fn = templates.get(kind)
    if fn is None:
        return ""
    return fn(level=level, tested_level=tested_level)
