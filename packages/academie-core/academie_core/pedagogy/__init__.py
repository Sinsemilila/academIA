"""Pedagogy layer — rubrics, fewshots, dosage, anti-drift, L1 watch, spaced retrieval.

Ported to academie-core in Sprint 4 Phase C (2026-04-16). Previously lived at
`webapp/backend/app/teacher_prompt.py`. Shim in webapp keeps old imports working.

Public re-exports — importers can also target the submodule directly.
"""
from .teacher_prompt import (  # noqa: F401
    # Dataclasses
    PromptContext,
    TeacherResponse,
    DosageDecision,
    # Constants
    LEVELS,
    TIERS,
    FEEDBACK_TYPES,
    DOSAGE_BUDGET,
    DOSAGE_HARD_CAP,
    TIER_TO_FEEDBACK_DEFAULT,
    L1_NAMES,
    L1_TRANSFER_SEED,
    RUBRICS,
    FEWSHOT_BANK,
    OUTPUT_SCHEMA_BLOCK,
    # Main entry points
    build_dynamic_sections,
    parse_teacher_response,
    # Helpers
    rubric_for_level,
    compute_dosage_budget,
    arbitrate_dosage,
    tier_to_feedback_type,
    should_inject_level_reminder,
    should_request_drift_check,
    build_level_reminder,
    build_drift_check_request,
    build_l1_watch,
    build_spaced_retrieval_block,
    select_fewshots,
    render_fewshots_block,
    update_feedback_history,
)
