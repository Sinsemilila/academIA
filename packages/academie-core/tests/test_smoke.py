"""Smoke test for academie-core Sprint 4 Phase A scaffold.

Valide que la structure du package est cohérente :
  - imports top-level OK
  - dataclasses instantiables
  - Protocol v2 runtime-checkable sur une implémentation bidon
  - Sub-packages (taxonomy, pedagogy, psychometrics) importables (stubs vides)

Pas de logique business testée ici — Phase B/C/D auront leurs propres tests.
"""
from __future__ import annotations


def test_import_version():
    import academie_core
    assert academie_core.__version__ == "0.1.0"


def test_import_domain_base():
    from academie_core.domain.base import (
        Domain, Error, GravityAxes, Tier, UserContext, PromptContext,
        FeedbackPlan, StructuredResponse, Progression, Snapshot,
    )
    assert Domain is not None
    assert Error is not None


def test_gravity_axes_defaults():
    from academie_core.domain.base import GravityAxes
    g = GravityAxes()
    assert g.linguistic == 0.0
    assert g.communicative == 0.0
    assert g.social_pragmatic == 0.0


def test_tier_dataclass():
    from academie_core.domain.base import Tier
    t = Tier(id="T3", weight=0.394, display=True)
    assert t.id == "T3"
    assert 0 <= t.weight <= 1


def test_error_instantiation():
    from academie_core.domain.base import Error, GravityAxes
    e = Error(
        code="V:TENSE", family="verb_tense", span=(10, 14),
        reasoning="past simple expected", detected_by="rules",
        gravity=GravityAxes(linguistic=0.6, communicative=0.4),
    )
    assert e.code == "V:TENSE"
    assert e.gravity.linguistic == 0.6


def test_user_context_defaults():
    from academie_core.domain.base import UserContext
    ctx = UserContext(
        user_id=1, eleve_id=1, level="B1", domain_id="lang:en",
    )
    assert ctx.level == "B1"
    assert ctx.prerequisite_profile == {}
    assert ctx.scores_confiance == {}


def test_prompt_context_composition():
    from academie_core.domain.base import PromptContext, UserContext
    uctx = UserContext(user_id=1, eleve_id=1, level="B1", domain_id="lang:en")
    pctx = PromptContext(user_context=uctx, turn_count=3)
    assert pctx.turn_count == 3
    assert pctx.errors_detected == []


def test_structured_response_parse_fail_shape():
    from academie_core.domain.base import StructuredResponse
    sr = StructuredResponse(feedback="fallback text", parse_ok=False, raw_text="oops")
    assert sr.parse_ok is False
    assert sr.feedback == "fallback text"
    # Default lists must be empty + distinct instances (frozen dataclass trap sanity)
    sr2 = StructuredResponse(feedback="x")
    assert sr.tier_applied is not sr2.tier_applied


def test_protocol_runtime_checkable():
    """Toute classe qui expose les méthodes est un Domain valide (duck-typed)."""
    from academie_core.domain.base import Domain, PromptContext, UserContext

    class StubDomain:
        id = "stub:test"

        def detect_errors(self, user_input, context):
            return []

        def score_tier(self, error, context):
            from academie_core.domain.base import Tier
            return Tier(id="T1", weight=0.1, display=False)

        def build_dynamic_sections(self, context):
            return {}

        def build_system_prompt(self, context):
            return ""

        def parse_response(self, raw_text):
            from academie_core.domain.base import StructuredResponse
            return StructuredResponse(feedback="", raw_text=raw_text)

        def pedagogical_feedback(self, errors, context):
            from academie_core.domain.base import FeedbackPlan
            return FeedbackPlan(to_correct=[], silenced=[], dosage_budget=0, feedback_types={})

        def compute_progression(self, error_log, context):
            from academie_core.domain.base import Progression
            return Progression()

        def snapshot(self, session, context):
            from academie_core.domain.base import Snapshot
            return Snapshot(session_id=0, domain_id=self.id, payload={})

    stub = StubDomain()
    assert isinstance(stub, Domain)


def test_submodules_importable():
    import academie_core.taxonomy  # noqa: F401
    import academie_core.pedagogy  # noqa: F401
    import academie_core.psychometrics  # noqa: F401
