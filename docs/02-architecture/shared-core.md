---
title: academie-core — package Python partagé
status: authoritative
last_reviewed: 2026-04-16
---

# academie-core — package Python partagé

> Détail de [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md). Package Python interne qui porte la logique pédagogique + psychométrique + d'abstraction Domain.

## Objectifs

1. **Découpler** la logique pédagogique du webapp FastAPI (actuellement couplée dans `webapp/backend/app/error_taxonomy/`)
2. **Réutiliser** cette logique depuis plusieurs composants : webapp, scripts d'admin, futurs handlers n8n, futurs microservices
3. **Tester** indépendamment (pytest + coverage)
4. **Versionner** (`academie-core==1.2.0` permet rollback sans toucher le webapp)

## Organisation cible

```
academie-core/
├── pyproject.toml
├── README.md
├── academie_core/
│   ├── __init__.py
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── base.py                 # interface Domain (Protocol)
│   │   ├── language.py             # LanguageDomain (CECRL)
│   │   ├── code.py                 # CodeDomain (futur)
│   │   └── cybersec.py             # CyberSecDomain (futur)
│   │
│   ├── taxonomy/
│   │   ├── __init__.py
│   │   ├── tiers.py                # T0..T4 enum + functions
│   │   ├── matrix.py               # load/query tolerance matrix
│   │   ├── gravity.py              # James axes (linguistic/communicative/social)
│   │   ├── rules.py                # rules layer (port depuis webapp)
│   │   ├── scoring.py              # scoring engine (port depuis webapp)
│   │   └── transfer.py             # L1/prerequisite transfer multipliers
│   │
│   ├── psychometrics/
│   │   ├── __init__.py
│   │   ├── irt.py                  # GRM, IRT helpers (girth wrapper)
│   │   ├── kt.py                   # BKT (pyBKT wrapper), PFA
│   │   ├── sr.py                   # spaced repetition (FSRS wrapper)
│   │   └── calibration.py          # GLMM, Cox PH (lifelines wrapper)
│   │
│   ├── pedagogy/
│   │   ├── __init__.py
│   │   ├── feedback.py             # tier → Lyster feedback mapping
│   │   ├── dosage.py               # corrections/tour selon niveau
│   │   └── templates.py            # phrasings multi-langues
│   │
│   └── data/
│       ├── tolerance_matrix/
│       │   ├── en.yaml
│       │   ├── es.yaml              # futur
│       │   └── ...
│       ├── cefr_criterial_features/
│       │   ├── en.yaml              # depuis EGP
│       │   └── ...
│       ├── l1_transfer_multipliers.yaml
│       └── errant_to_family.yaml   # Sprint 5+
│
├── tests/
│   ├── test_tiers.py
│   ├── test_rules_layer.py
│   ├── test_scoring.py
│   ├── test_gravity_composition.py
│   ├── test_transfer.py
│   └── fixtures/
│       └── ...
│
└── scripts/
    ├── calibrate_from_corpus.py    # GLMM + Cox sur dump
    └── import_errant_corpus.py     # Sprint 5+
```

## Interface Domain (v2 post-Sprint 3)

> **Note** : v1 était la proposition initiale (5 méthodes, décision 2026-04-15). Sprint 3 Teacher V2 (Lyster : dosage, anti-drift, L1 watch, spaced retrieval, JSON schema) a révélé 3 méthodes manquantes. v2 ci-dessous reflète la réalité production — voir [sprint4_preimpl_review.md](../00-project/sprint4_preimpl_review.md) §3-4 pour le détail de l'audit.

```python
# academie_core/domain/base.py  (v2 — post-Sprint 3)

class Domain(Protocol):
    id: str                                   # "lang:en", "code:python"
    proficiency_scale: ProficiencyScale

    # === Taxonomy layer (inchangé v1) ===
    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]: ...
    def score_tier(self, error: Error, context: UserContext) -> Tier: ...

    # === Pedagogy layer — nouveautés v2 ===
    def build_dynamic_sections(self, context: PromptContext) -> dict[str, str]:
        """Produit les blocs dynamiques (rubric / fewshots / dosage / level_reminder /
        drift / l1_watch / spaced / output_schema) à injecter dans le chatflow Dify."""

    def build_system_prompt(self, context: PromptContext) -> str:
        """Compose le system prompt complet à partir des dynamic sections. Webapp
        le transmet à Dify qui stream la réponse LLM."""

    def parse_response(self, raw_text: str) -> StructuredResponse:
        """Extrait `<output>JSON</output>` + fallback gracieux sur malformé."""

    def pedagogical_feedback(
        self,
        errors: list[Error],
        context: UserContext,
    ) -> FeedbackPlan:
        """Décide pour l'ensemble du turn : quel tier → quel feedback_type, quel dosage,
        quelle diversity_rule. Un plan agrégé, pas par erreur individuelle."""

    # === Progression / session layer (inchangé v1) ===
    def compute_progression(self, error_log: list[Error], context: UserContext) -> Progression: ...
    def snapshot(self, session: Session, context: UserContext) -> Snapshot: ...
```

**Orchestration contract (acté Sprint 4 ré-analyse 2026-04-16)** :
- **Domain** pure logic — compose le prompt, parse la réponse, décide la pédagogie. Jamais de httpx ou FastAPI Response.
- **Webapp** (chat_router) tient le httpx + SSE streaming Dify → user, persist error_log + spaced_retrieval_queue. Appelle `Domain.build_system_prompt` avant Dify, `Domain.parse_response` après stream.
- **Services orthogonaux** (hors Domain) : `SpacedRetrievalService` partagé toutes Domains (`.fetch_due`, `.enqueue`, `.complete`) — pattern déjà appliqué Phase 7.

**Changements v1 → v2** :
- ➕ `build_dynamic_sections`, `build_system_prompt`, `parse_response`
- `pedagogical_feedback` signature ajustée — prend `list[Error]` → `FeedbackPlan` (plan turn-level, pas per-error)

## Interface Domain (v1 — archivée)

```python
# academie_core/domain/base.py
from typing import Protocol
from dataclasses import dataclass

@dataclass
class Error:
    code: str
    family: str
    span: tuple[int, int]
    reasoning: str
    detected_by: str                  # "rules" | "llm" | "hybrid"
    gravity_axes: "GravityAxes"

@dataclass
class GravityAxes:
    linguistic: float                 # 0-1
    communicative: float              # 0-1
    social_pragmatic: float           # 0-1

@dataclass
class UserContext:
    user_id: int
    level: str                        # "A1", "B2", etc. (langues) ou custom
    prerequisite_profile: dict        # {"L1": "fr"} pour langues
    scores_confiance: dict            # concept → progress
    recent_correct_uses: dict         # concept → nb de prod correctes récentes

@dataclass
class Tier:
    id: str                           # "T0" ... "T4"
    weight: float                     # 0-1 (calibré empiriquement)
    display: bool                     # affiché à l'user ou non

@dataclass
class FeedbackHint:
    tier: Tier
    feedback_type: str                # "recast" | "elicitation" | "metalinguistic" | ...
    template_key: str                 # référence dans templates.py
    delay: str                        # "inline" | "end_of_session" | "spaced_J+1"
    force_user_response: bool

class Domain(Protocol):
    id: str
    proficiency_scale: "ProficiencyScale"

    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]:
        """Rules layer + LLM → liste d'erreurs structurées."""
        ...

    def score_tier(self, error: Error, context: UserContext) -> Tier:
        """Applique la fonction tier(error, context) empirique."""
        ...

    def compute_progression(self, error_log: list[Error], context: UserContext) -> "Progression":
        """Scores confiance, mastery_probability, niveau estimé, etc."""
        ...

    def snapshot(self, session: "Session", context: UserContext) -> "Snapshot":
        """Génère snapshot JSONB persistable."""
        ...

    def pedagogical_feedback(self, tier: Tier, error: Error, context: UserContext) -> FeedbackHint:
        """Décide quoi renvoyer à l'user (type + template + timing)."""
        ...
```

## Implementation `LanguageDomain`

```python
# academie_core/domain/language.py

class LanguageDomain:
    def __init__(self, lang_target: str):
        self.id = f"lang:{lang_target}"
        self.lang_target = lang_target
        self.proficiency_scale = CEFR_SCALE
        self._load_tolerance_matrix()
        self._load_criterial_features()
        self._load_transfer_multipliers()

    def detect_errors(self, user_input, context):
        # 1. Rules layer Python (taxonomy/rules.py)
        # 2. LLM analysis via LiteLLM (ft:gpt-4o-mini-v3)
        # 3. Merge & deduplicate
        ...

    def score_tier(self, error, context):
        # 1. Load tier depuis tolerance_matrix[lang][level][family]
        # 2. Ajuster selon gravity_axes + criterial_level
        # 3. Ajuster selon L1 transfer multiplier
        # 4. Ajuster selon mistake vs error (recent_correct_uses)
        # 5. Ajuster U-shape protection
        ...
```

## Stratégie de publication

**Option retenue** : monorepo sous `packages/academie-core/`. Installé via `pip install -e ./packages/academie-core` en dev.

Pour prod : tag git + version bump dans `pyproject.toml`. Le webapp `pyproject.toml` épingle `academie-core==1.x.y`.

Alternative considérée : dépôt git séparé `Sinsemilila/academie-core`. Rejetée pour l'instant — overhead pas justifié tant qu'on est solo.

## Tests

- **Unit** : coverage > 80% sur taxonomy/, psychometrics/, pedagogy/
- **Fixtures** : snippets d'erreurs fabriqués, inputs CEFR-tagged, expected tiers
- **Property-based** (hypothesis) : pour les invariants (T0 si pre_acquisition, commutativity gravity)
- **Integration** : test réel contre rules layer + LLM stub (mocked LiteLLM)

## Migration depuis webapp actuel

Le code actuel `webapp/backend/app/error_taxonomy/{rules,scoring,llm,differ,categories}.py` (~2000 lignes) sera **progressivement porté** vers `academie-core/taxonomy/` sur Sprint 2-3 (refonte schéma).

Étape par étape :
1. Scaffolder `academie-core` vide, pyproject.toml, CI pytest
2. Port de `rules.py` → `academie_core.taxonomy.rules`. webapp importe depuis le package au lieu du router.
3. Port de `scoring.py` → `academie_core.taxonomy.scoring`
4. Port de `categories.py` → `academie_core.taxonomy.gravity` + `academie_core.taxonomy.transfer`
5. Port de `llm.py` → `academie_core.taxonomy.llm` (stays dans taxonomy car LLM = outil de détection)
6. Introduce `Domain` wrapper : `LanguageDomain.detect_errors` qui appelle ces composants
7. webapp/chat_router utilise `LanguageDomain(lang="en")` au lieu de call direct

## Re-évaluation

À l'ajout du 2ᵉ domaine (Maestro) : l'interface `Domain` actuelle tient-elle pour du ES sans modif majeure ?

## Références

- [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md)
- [agent-topology.md](agent-topology.md) — comment s'intègre avec Dify chatflows
- [../01-pedagogy/taxonomy-framework.md](../01-pedagogy/taxonomy-framework.md) — concepts implémentés
- Code existant : `webapp/backend/app/error_taxonomy/*.py`
