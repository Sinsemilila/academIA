"""LanguageDomain — concrete Domain implementation for language tutoring (CEFR).

Wraps taxonomy (rules + scoring) + pedagogy (Lyster prompts + dosage + L1 watch +
spaced retrieval) for a given target language. Protocol-compatible (runtime-checkable)
with academie_core.domain.base.Domain — duck typing on method names.

Sprint 4 Phase D — uses legacy PromptContext/TeacherResponse types from
academie_core.pedagogy.teacher_prompt (not the new base.py types). Unification
deferred to Sprint 5+ when Spanish Maestro imposes the structure.

Usage :
  >>> from academie_core.domain.language import LanguageDomain
  >>> en = LanguageDomain("en")
  >>> errs = en.detect_errors("I have went to Paris yesterday")
  >>> sections = en.build_dynamic_sections(PromptContext(level="B1", turn_count=3))
"""
from __future__ import annotations

from ..pedagogy.teacher_prompt import (
    LanguageData,
    PromptContext,
    TeacherResponse,
    build_dynamic_sections as _build_sections,
    parse_teacher_response as _parse,
    arbitrate_dosage,
    tier_to_feedback_type,
)
from ..taxonomy.rules import detect_errors as _detect, RuleDetection
from ..taxonomy.scoring import enrich_error_fields, compute_error_profile


class LanguageDomain:
    """Concrete Domain for language tutoring.

    Parameters
    ----------
    lang_target : str
        ISO-639-1 code of the target language (e.g., "en", "es", "de").
    """

    def __init__(self, lang_target: str = "en"):
        self.id = f"lang:{lang_target}"
        self.lang_target = lang_target
        self._lang_data = LanguageData.for_lang(lang_target)

    # === Taxonomy layer (delegates to academie_core.taxonomy) ===

    def detect_errors(self, user_input: str, context=None) -> list[RuleDetection]:
        """Run rules layer on the user input. Returns a list of RuleDetection."""
        return _detect(user_input, lang=self.lang_target)

    def score_tier(self, error_code: str, level: str) -> dict:
        """Get tier + gravity axes for an error_code at a CEFR level."""
        return enrich_error_fields(error_code, level)

    def compute_progression(
        self,
        error_log_rows: list,
        level: str,
        concept_keys: list,
        scores_confiance: dict,
    ) -> dict:
        """Per-concept progress profile from error_log."""
        return compute_error_profile(error_log_rows, level, concept_keys, scores_confiance)

    # === Pedagogy layer (delegates to academie_core.pedagogy) ===

    def build_dynamic_sections(self, context: PromptContext) -> dict:
        """8 dynamic sections for PROMPT_SESSION_V2 (rubric/fewshots/dosage/
        level_reminder/drift/l1_watch/spaced/output_schema)."""
        return _build_sections(context, lang_data=self._lang_data)

    def parse_response(self, raw_text: str) -> TeacherResponse:
        """Extract `<output>JSON</output>` from LLM response. Fallback graceful."""
        return _parse(raw_text)

    def pedagogical_feedback(self, errors: list[dict], level: str) -> dict:
        """Arbitrate dosage + map tier→feedback_type for each to-correct error.

        Returns a plan dict :
            {
              "to_correct": [...errors...],
              "silenced": [...errors...],
              "dosage_budget": int,
              "feedback_types": {error_code: type_str, ...},
            }
        """
        decision = arbitrate_dosage(level, errors)
        types_map = {}
        for e in decision.to_correct:
            family = e.get("family", "?")
            tier = e.get("tier", "T1")
            gravity = {
                "linguistic": e.get("gravity_linguistic", 0),
                "communicative": e.get("gravity_communicative", 0),
                "social": e.get("gravity_social", 0),
            }
            types_map[e.get("error_code", "?")] = tier_to_feedback_type(
                tier, family, gravity=gravity, level=level,
            )
        return {
            "to_correct": decision.to_correct,
            "silenced": decision.silenced_for_spaced_retrieval,
            "dosage_budget": decision.budget,
            "feedback_types": types_map,
        }

    # === Not yet implemented ===

    def build_system_prompt(self, context: PromptContext) -> str:
        """Returns empty in v1 — Dify template assembles the system prompt from
        individual sections passed as dify_inputs. Phase G/Sprint 5+ will
        implement if we move to a non-Dify LLM call path."""
        return ""

    def snapshot(self, session, context) -> dict:
        """Not implemented v1 — snapshots_session is populated by n8n async.
        Phase 7.3+ when snapshot generation unifies."""
        raise NotImplementedError("snapshot() deferred to v3+")
