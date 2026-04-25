---
title: Framework de taxonomie d'erreur abstrait (domain-agnostic)
status: authoritative
last_reviewed: 2026-04-15
---

# Framework de taxonomie d'erreur abstrait

> Le socle abstrait qui s'applique à **tous les domaines** (langues, code, cybersec, compta, …). Les domaines concrets [l'instancient](cefr-language-instance.md) avec leurs spécificités.

## Motivation

AcademIA va couvrir plusieurs domaines : langues (CECRL), code (Bloom-like), cybersécurité (NICE), comptabilité (à définir). Plutôt que de réinventer un système d'évaluation par domaine, on définit un **framework abstrait** et chaque domaine fournit ses données.

Décisions fondatrices :
- [ADR-002](../05-decisions/ADR-002-schema-from-day-1.md) — schéma multi-domaine dès le départ
- [ADR-003](../05-decisions/ADR-003-5-tiers-taxonomy.md) — 5 tiers de gravité
- [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md) — package `academie-core`

## Concepts du framework

### 1. `Domain`

Instance pédagogique : `LanguageDomain("en")`, `LanguageDomain("es")`, `CodeDomain("python")`, `CyberSecDomain("nice")`, ...

Chaque Domain fournit :
- **Proficiency scale** — échelle de maîtrise (CECRL pour langues, Bloom pour code, NICE pour cybersec, …)
- **Competency map** — concepts/skills couverts × niveau d'émergence/maîtrise
- **Error taxonomy** — familles d'erreur + codes
- **Tolerance matrix** — quel tier pour quelle erreur à quel niveau
- **Transfer multipliers** — ajustements selon prérequis (L1 pour langues, L0 pour code)
- **Feedback mapping** — tier → type de feedback pédagogique

### 2. `Tier` (5 niveaux, cf. ADR-003)

| Tier | Nom | Condition | Action |
|---|---|---|---|
| **T0** | `pre_acquisition` | concept/skill hors curriculum du niveau | jamais affiché |
| **T1** | `ignored` | erreur normale au niveau | journalisée, pas affichée |
| **T2** | `noted` | erreur fréquente mais formative | feedback implicite léger |
| **T3** | `penalized` | erreur attendue corrigible | feedback explicite / prompt |
| **T4** | `regressive` | concept censé acquis depuis N-2 niveaux | feedback + remédiation |

T0 et T4 distinguent ce que l'ancien système à 4 tiers ne capturait pas :
- T0 ≠ T1 : "pas encore vu" ≠ "vu mais toléré"
- T4 ≠ T3 : "erreur sur structure acquise" ≠ "erreur sur structure en cours"

### 3. `GravityAxes` (James 1998)

Chaque erreur a 3 dimensions de gravité (score 0-1) :

- **linguistic** : violation de règle brute, indépendante du contexte
- **communicative** : impact sur la compréhension (global vs local, cf. Burt & Kiparsky 1972)
- **social_pragmatic** : irritation native, registre, appropriation contextuelle

Le tier final est une fonction composite :

```
tier(err, learner) = f(
    err.gravity_axes,
    learner.level - err.criterial_mastery_level,
    learner.recent_correct_uses(err.concept),   # mistake vs error
    learner.prerequisite_profile(err),            # L1 pour langues
    err.global_or_local
)
```

`f` est **calibrée empiriquement** (cf. [error-gradation.md](error-gradation.md)), pas hardcodée.

### 4. `Competency Map`

Chaque concept/skill a :
- `emergence_level` : niveau où il apparaît typiquement (≥ 30% des apprenants)
- `mastery_level` : niveau où il est censé être maîtrisé (≥ 80% des apprenants, peu d'erreurs)

Ces valeurs sont **empiriques**, dérivées de corpus annotés (EGP pour EN, MERLIN pour DE/IT, CEDEL2 pour ES, etc.), pas prescrites.

**Conséquence** : T0 `pre_acquisition` = `learner.level < emergence_level` ; T4 `regressive` = `learner.level > mastery_level + 2`.

### 5. `Prerequisite Profile`

Modulation selon le profil de départ de l'apprenant :
- **Langues** : L1 (langue maternelle) → multiplicateurs de transfert via URIEL/lang2vec
- **Code** : langues de programmation déjà connues → transferts syntaxiques
- **Cybersec** : background sys/admin/dev → compétences existantes
- **Compta** : exposition préalable aux normes IFRS/GAAP/locales

Matérialisé dans une table `prerequisite_transfer.yaml` indexée `(prereq_code, target_code, concept)`.

### 6. `FeedbackHint`

Tier → type de feedback. Basé sur Lyster & Ranta (1997) pour les langues ; à adapter pour autres domaines.

| Tier | Feedback langues | Feedback code |
|---|---|---|
| T0 | — (invisible) | — |
| T1 | — (invisible) | — |
| T2 | recast implicite | reformulation code |
| T3 | elicitation / metalinguistic | "try running it with X — what do you get?" |
| T4 | prompt + remédiation | debugger + explication règle |

## Interface `Domain` (Python Protocol)

Documenté dans [`02-architecture/shared-core.md`](../02-architecture/shared-core.md). Extrait :

```python
class Domain(Protocol):
    id: str
    proficiency_scale: ProficiencyScale
    
    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]: ...
    def score_tier(self, error: Error, context: UserContext) -> Tier: ...
    def compute_progression(self, error_log: list[Error]) -> Progression: ...
    def snapshot(self, session: Session) -> Snapshot: ...
    def pedagogical_feedback(self, tier: Tier, context: UserContext) -> FeedbackHint: ...
```

## Instanciations prévues

- [`LanguageDomain` (EN/ES/JP/DE/IT)](cefr-language-instance.md) — CECRL
- `CodeDomain` (Python d'abord) — Bloom + exec traces *(à écrire au moment du PyMentor)*
- `CyberSecDomain` — NICE framework *(à écrire au moment du CyberMentor)*
- `AccountingDomain` — à concevoir *(futur)*

## Invariants universels (cross-domaine)

4 règles qui s'appliquent **quel que soit** le domaine (confirmées par la recherche SLA mais généralisables) :

1. **Structure pré-acquisition → T0 obligatoire** (Pienemann teachability)
2. **Global errors > local errors** partout (Burt-Kiparsky)
3. **Protéger la motivation** : sur-correction = anti-pédagogique (Krashen affective filter, Mueller-Dweck mindset)
4. **Mistake vs error** (Corder) : erreur sur structure démontrée correctement auparavant ≠ erreur sur structure neuve

## Ce que le framework ne fait PAS

- **Ne décide pas de la pédagogie de délivrance** — c'est le boulot du Domain concret (cf. [feedback-delivery.md](feedback-delivery.md))
- **Ne hardcode pas de poids** — tout est calibré empiriquement (cf. [error-gradation.md](error-gradation.md))
- **Ne dépend pas d'un LLM spécifique** — le LLM est un composant interchangeable via LiteLLM

## Références

- Framework pédagogique : [cefr-language-instance.md](cefr-language-instance.md), [feedback-delivery.md](feedback-delivery.md)
- Calibration : [error-gradation.md](error-gradation.md)
- Code associé : `academie-core/taxonomy/*.py` (à créer, cf. [shared-core.md](../02-architecture/shared-core.md))
- Bibliographie : [bibliography.md](bibliography.md)
