"""Domain Protocol v2 (post-Sprint 3 ré-analyse).

Interface abstraite pour un domaine d'apprentissage (langue, code, cybersec, …).
Protocol = duck-typed : toute classe qui expose ces méthodes est un Domain valide.

Cette version v2 intègre les 3 méthodes manquantes identifiées en Sprint 4 ré-analyse
(cf. docs/00-project/sprint4_preimpl_review.md §4) :
  - build_dynamic_sections
  - build_system_prompt
  - parse_response

Orchestration contract :
  - Domain = pure logic (compose prompt, parse response, décide pédagogie)
  - Webapp = tient le httpx + streaming Dify, persist error_log + queue
  - Services orthogonaux (ex : SpacedRetrievalService) — partagés cross-Domain

Aucune implémentation à cette Phase A. Les stubs `...` permettent juste de valider
l'import + fournir la signature à qui va implémenter Phase B-D.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


# ── Data types partagés ────────────────────────────────────────────


@dataclass(frozen=True)
class GravityAxes:
    """Axes de gravité (Corder/James)."""
    linguistic: float = 0.0       # 0..1
    communicative: float = 0.0    # 0..1
    social_pragmatic: float = 0.0  # 0..1


@dataclass(frozen=True)
class Tier:
    """Tier de sévérité d'erreur (T0..T4)."""
    id: Literal["T0", "T1", "T2", "T3", "T4"]
    weight: float                  # 0..1 calibré empiriquement
    display: bool                  # affiché à l'user ou silencieux


@dataclass(frozen=True)
class Error:
    """Erreur détectée + metadata."""
    code: str                      # ex : "V:TENSE", "N:DET", "PREP"
    family: str                    # ex : "verb_tense", "preposition"
    span: tuple[int, int]          # char offsets dans l'user input
    reasoning: str
    detected_by: Literal["rules", "llm", "hybrid"]
    gravity: GravityAxes = field(default_factory=GravityAxes)


@dataclass
class UserContext:
    """Contexte user au moment du turn."""
    user_id: int
    eleve_id: int | None
    level: str                     # "A1"..."C2" (langues) ou custom autre domain
    domain_id: str                 # "lang:en", "code:python", ...
    prerequisite_profile: dict[str, Any] = field(default_factory=dict)  # ex {"L1":"fr"}
    scores_confiance: dict[str, float] = field(default_factory=dict)
    recent_correct_uses: dict[str, int] = field(default_factory=dict)


@dataclass
class PromptContext:
    """Contexte de composition du system prompt pour un turn.

    Super-set de UserContext + état de la session + erreurs détectées ce turn.
    """
    user_context: UserContext
    turn_count: int
    errors_detected: list[Error] = field(default_factory=list)
    last_feedback_per_family: dict[str, list[str]] = field(default_factory=dict)
    spaced_retrieval_due: list[dict[str, Any]] = field(default_factory=list)
    target_lang: str = "en"  # pour LanguageDomain uniquement


@dataclass
class FeedbackPlan:
    """Plan pédagogique pour le turn entier (pas par erreur)."""
    to_correct: list[Error]
    silenced: list[Error]
    dosage_budget: int
    feedback_types: dict[str, str]  # error_code → feedback_type


@dataclass
class StructuredResponse:
    """Réponse Teacher parsée depuis `<output>JSON</output>`."""
    feedback: str
    reasoning: str = ""
    tier_applied: list[str] = field(default_factory=list)
    feedback_types: list[str] = field(default_factory=list)
    error_codes: list[str] = field(default_factory=list)
    silenced_for_spaced_retrieval: list[str] = field(default_factory=list)
    spaced_retrieval_addressed: list[str] = field(default_factory=list)
    drift_self_grade: Literal["compliant", "drift_detected", "not_checked"] = "not_checked"
    level_reinjected: bool = False
    parse_ok: bool = True
    raw_text: str = ""


@dataclass
class Progression:
    """Scores + mastery + niveau estimé d'un user dans le domaine."""
    concept_scores: dict[str, float] = field(default_factory=dict)
    mastery_probabilities: dict[str, float] = field(default_factory=dict)
    estimated_level: str = ""


@dataclass
class Snapshot:
    """Snapshot JSONB persistable d'une session."""
    session_id: int
    domain_id: str
    payload: dict[str, Any]        # structure libre par Domain


# ── Protocol Domain v2 ────────────────────────────────────────────


@runtime_checkable
class Domain(Protocol):
    """Protocol abstrait. Toute classe qui implémente ces méthodes est un Domain valide."""

    id: str                        # "lang:en", "code:python"

    # === Taxonomy layer ===
    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]:
        """Rules + LLM fusion → liste d'erreurs structurées."""
        ...

    def score_tier(self, error: Error, context: UserContext) -> Tier:
        """Applique tier(error, context) empirique (yaml tolerance matrix + gravity)."""
        ...

    # === Pedagogy layer (Sprint 3 Teacher V2 reality) ===
    def build_dynamic_sections(self, context: PromptContext) -> dict[str, str]:
        """Produit les blocs dynamiques à injecter dans le chatflow Dify.

        Keys typiques (LanguageDomain) : rubric_for_level, fewshots_block,
        dosage_block, level_reminder_inject, drift_validation_request,
        l1_watch, spaced_retrieval_today, output_schema_block.
        """
        ...

    def build_system_prompt(self, context: PromptContext) -> str:
        """Compose le system prompt complet. Webapp l'envoie à Dify."""
        ...

    def parse_response(self, raw_text: str) -> StructuredResponse:
        """Extrait `<output>JSON</output>` + fallback gracieux sur malformé."""
        ...

    def pedagogical_feedback(
        self,
        errors: list[Error],
        context: UserContext,
    ) -> FeedbackPlan:
        """Décide pour tout le turn : quel tier→feedback_type, dosage, diversity_rule."""
        ...

    # === Progression / session layer ===
    def compute_progression(
        self,
        error_log: list[Error],
        context: UserContext,
    ) -> Progression:
        """Scores de confiance + mastery probabilities + niveau estimé."""
        ...

    def snapshot(
        self,
        session: Any,                # Session type défini dans academie_core.session v3+
        context: UserContext,
    ) -> Snapshot:
        """Génère snapshot JSONB persistable."""
        ...
