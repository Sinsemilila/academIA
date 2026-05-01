"""AccountingDomain — first non-language Domain instance (S57+).

Tutor pour Marie en formation Studi RNCP41653 "Pré-Graduate Assistant Comptable".
Architecture cible : domaine "fermé" (réponse exacte vs production libre langues),
détection rules-first 80% / LLM 20%, authority anchor mono-source (PCG ANC + BOFiP +
RNCP41653 référentiel + programme Studi).

Phase 1 Mode B (assistant Q&A side-chat) : stub minimal — le chatflow Dify
"maitre_comptable_assistant" est autonome (knowledge base RAG + system prompt
+ few-shots Lyster + multimodal vision pour screenshots Marie). Pas besoin du
pipeline `build_dynamic_sections` riche utilisé par `LanguageDomain`.

Phase 2 Mode A (lessons / pratique guidée) : à étoffer avec :
- detect_errors() : rules_compta.py (partie double, calcul TVA, classification PCG)
- score_tier() : tier_to_feedback_compta mapping (axes technical/fiscal_legal/professional)
- pedagogical_feedback() : Lyster CF moves transposés

Voir `docs/03-domain/comptabilite.md` + `docs/05-decisions/ADR-017-accounting-domain-scope.md`.
"""
from __future__ import annotations


class AccountingDomain:
    """Concrete Domain for accounting tutoring (FR).

    Phase 1 Mode B = stub. Phase 2 Mode A étoffera avec rules_compta.py, scoring,
    feedback Lyster transposé compta.

    Parameters
    ----------
    variant : str
        Variant code, par convention "compta_fr" pour FR. Cohérent agents_config
        AgentDef.language ("compta_fr" pour Maître Comptable).
    """

    def __init__(self, variant: str = "compta_fr"):
        self.id = f"accounting:{variant}"
        self.variant = variant
        self.lang_target = variant  # alias for chat_router compatibility (treats domain ISO key)

    # === Taxonomy layer — Phase 2 Mode A ===

    def detect_errors(self, user_input: str, context=None) -> list:
        """Phase 2 : rules_compta.py (partie double, calcul TVA, classification PCG).
        Phase 1 stub : pas de détection backend (Mode B = Q&A Dify autonome)."""
        return []

    def score_tier(self, error_code: str, level: str) -> dict:
        """Phase 2 : tier_to_feedback_compta mapping (axes technical/fiscal_legal/professional)."""
        return {"tier": "T1", "error_code": error_code, "level": level}

    def compute_progression(
        self,
        error_log_rows: list,
        level: str,
        concept_keys: list,
        scores_confiance: dict,
    ) -> dict:
        """Phase 2+ : per-concept progress profile from error_log."""
        return {}

    # === Pedagogy layer — Phase 1 Mode B stub ===

    def build_dynamic_sections(self, context) -> dict:
        """Phase 1 stub — Mode B chatflow Dify "maitre_comptable_assistant" est
        autonome (knowledge base RAG + system prompt fixe + few-shots Lyster
        + multimodal vision). Pas de blocs dynamiques injectés.

        Phase 2 Mode A pourra populate :
          - rubric_for_level : règles N0/N1/N2/N3 par bloc RNCP
          - fewshots_block : exemples Lyster transposés compta
          - dosage_block : working memory cap ≤2 erreurs/leçon
          - level_reminder_inject : "tu es N1 sur BC1.4 TVA"
          - drift_validation_request : anti-drift Pak 2025 toutes 5-10 turns
          - module_context_inject : module en cours via dropdown α
          - output_schema_block : format réponse attendu
        """
        # Returns dict avec keys 8-section pour compat pipeline existant.
        # Toutes vides Phase 1 — chatflow Dify ignore les inputs non-référencés.
        return {
            "rubric_for_level": "",
            "fewshots_block": "",
            "dosage_block": "",
            "level_reminder_inject": "",
            "drift_validation_request": "",
            "module_context_inject": "",  # Phase 2 : module sélectionné dropdown α
            "output_schema_block": "",
            "concept_hints_json": "[]",
        }

    def parse_response(self, raw_text: str) -> dict:
        """Phase 1 : passthrough. Phase 2 Mode A pourrait extraire écritures
        structurées depuis la réponse Maître Comptable (format `<output>JSON</output>`
        si on le décide design Mode A)."""
        return {"raw": raw_text}

    def pedagogical_feedback(self, errors: list, level: str) -> dict:
        """Phase 2 Mode A : arbitrate dosage + map tier→Lyster CF move (recast/
        partial_recast/explicit_correction/prompt_plus_remediation/metalinguistic/
        clarification_request) transposés compta.

        Phase 1 stub : Mode B side-chat n'évalue pas les écritures backend."""
        return {
            "to_correct": [],
            "silenced": [],
            "dosage_budget": 0,
            "feedback_types": {},
        }

    # === Not yet implemented ===

    def build_system_prompt(self, context) -> str:
        """Phase 1 : empty (chatflow Dify assemble system_prompt côté Dify).
        Phase G+ si on migre vers LLM call direct."""
        return ""

    def snapshot(self, session, context) -> dict:
        """Phase 3+ — snapshot module Marie (modules complétés, niveaux atteints,
        FSRS due cards). Pas Phase 1 Mode B."""
        raise NotImplementedError("snapshot() deferred to Phase 3+")
