---
title: ADR-005 — Package Python `academie-core` pour la logique pédagogique partagée
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-005 — Package Python `academie-core` pour la logique pédagogique partagée

## Contexte

Actuellement toute la logique pédagogique (taxonomie, scoring, rules, error analysis) vit dans `webapp/backend/app/error_taxonomy/*.py`. Avec :
- 7+ agents à venir (Teacher, Maestro, Sensei, Lehrer, Professore, PyMentor, CyberMentor, …)
- Multi-domaines (langues, code, cybersec, compta…)

Elle doit être réutilisable **sans dépendre de webapp**.

## Options envisagées

### Option A — Laisser dans webapp/backend, chaque composant qui a besoin importe depuis là

- Pour : simple, pas de nouveau dépôt
- Contre : couplage webapp ↔ agents, fragilité si on extrait un service

### Option B — Package Python interne `academie-core`

- Pour : découplage, réutilisable par tout composant Python (FastAPI, scripts, n8n handlers, futurs services), versionnable
- Contre : léger overhead setup (pyproject.toml, publication interne)

### Option C — Microservice scoring indépendant (REST API)

- Pour : isolation maximale
- Contre : overkill actuel (cf. ADR-001), latence réseau inutile

## Décision

**Option B — Package Python `academie-core`**.

**Organisation** :

```
academie-core/
├── pyproject.toml
├── academie_core/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── base.py                 # Interface Domain abstraite
│   │   ├── language.py             # LanguageDomain (CECRL, Lyster, L1 transfer)
│   │   ├── code.py                 # CodeDomain (futur)
│   │   └── cybersec.py             # CyberSecDomain (futur)
│   ├── taxonomy/
│   │   ├── tiers.py                # T0-T4 definitions
│   │   ├── matrix.py               # tolerance_matrix loading + query
│   │   ├── rules.py                # rules layer (ex-webapp)
│   │   └── scoring.py              # scoring engine (ex-webapp)
│   ├── psychometrics/
│   │   ├── irt.py                  # GRM, IRT helpers
│   │   ├── kt.py                   # BKT, PFA helpers
│   │   └── calibration.py          # GLMM, Cox PH helpers
│   ├── pedagogy/
│   │   ├── feedback.py             # Lyster prompts mapping
│   │   └── dosage.py               # corrections/minute selon niveau
│   └── data/
│       ├── tolerance_matrix.yaml   # déplacé depuis webapp
│       ├── l1_transfer.yaml
│       └── cefr_criterial_features/
│           └── en.yaml             # EGP-derived, extensible par langue
└── tests/
    └── ...
```

**Interface Domain minimale (v1)** :

```python
class Domain(Protocol):
    id: str                                      # "lang:en", "code:python", ...
    proficiency_scale: ProficiencyScale          # CECRL | Bloom | NICE | custom
    
    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]: ...
    def score_tier(self, error: Error, context: UserContext) -> Tier: ...
    def compute_progression(self, error_log: list[Error]) -> Progression: ...
    def snapshot(self, session: Session) -> Snapshot: ...
    def pedagogical_feedback(self, tier: Tier, context: UserContext) -> FeedbackHint: ...
```

**Publication** : dépôt git privé (GitHub `Sinsemilila/academie-core` ou dans le monorepo actuel sous `packages/academie-core/`). Installation via `pip install -e ./packages/academie-core` en dev, ou tag + version pour prod.

## Conséquences

- Positives : réutilisable par tout composant, testable indépendamment, versionnable (`academie-core==1.2.0`)
- Acceptées : effort scaffolding initial (~2-3 jours) ; discipline de maintien de l'API
- Neutres : nouveau point de maintenance (dépendances, versions)

## Actions de mise en œuvre

- [ ] Choisir l'emplacement (monorepo sous `packages/` ou dépôt séparé) — **à trancher**
- [ ] Scaffolding : `pyproject.toml`, structure minimale, CI basique (pytest + mypy optionnel)
- [ ] Migration progressive depuis `webapp/backend/app/error_taxonomy/*`
- [ ] Premier consommateur : le webapp lui-même (import academie-core depuis FastAPI)

## Re-évaluation

À l'ajout du 2ᵉ agent (Maestro) : valider que l'interface `Domain` tient pour du ES sans modification majeure.

## Références

- [ADR-001-monolith-vs-microservices.md](ADR-001-monolith-vs-microservices.md)
- [ADR-004-hybrid-orchestrated-agent-topology.md](ADR-004-hybrid-orchestrated-agent-topology.md)
- [02-architecture/shared-core.md](../02-architecture/shared-core.md) — doc détaillée (à écrire)
