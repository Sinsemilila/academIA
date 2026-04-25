---
title: Agent Topology — architecture hybride orchestrée
status: accepted
last_reviewed: 2026-04-16
---

# Agent Topology — architecture hybride orchestrée

> **Statut** : **accepted** dans [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) après ré-analyse Sprint 4 (2026-04-16). Voir [sprint4_preimpl_review.md](../00-project/sprint4_preimpl_review.md) pour le détail des 4 checkpoints fermés + chiffrage 8-11 jours-dev.

## Cible

```
SvelteKit Frontend
        │
        ▼
FastAPI orchestrator (webapp/backend)
        │
        ├──► LanguageDomain (Lyster, CECRL, gravity axes, L1 transfer)
        │      └──► 1 seul Dify chatflow "language-tutor"
        │           paramétré : {lang_target, level, L1, mode}
        │
        ├──► CodeDomain (Bloom-like, sandbox exec, error trace)
        │      └──► 1 Dify chatflow "code-mentor"
        │           paramétré : {programming_lang, level}
        │
        ├──► CyberSecDomain (NICE framework, scenarios)
        │      └──► 1 Dify chatflow "cybersec-mentor"
        │
        └──► (futur) AccountingDomain, etc.

Tous implémentent l'interface Domain de academie-core (cf. ADR-005)
```

## Pourquoi pas une alternative ?

| Option | Pourquoi rejetée |
|---|---|
| **Un chatflow par agent** (status quo extended) | Duplication massive. 5 langues = 5 chatflows à maintenir. Update pédago × 5. Anti-pattern. |
| **Un chatflow universel pour tout** | Impossible. Teacher (dialogue socratique Lyster) et PyMentor (debug, exec sandbox) = pédagogies incompatibles. Compromis médiocre partout. |

## Factorisation par famille pédagogique

- **LanguageDomain** : 5 langues (EN/ES/JP/DE/IT) partagent pédagogie Lyster, CECRL, gravity axes. 1 chatflow paramétré suffit. Extension = ajouter data, pas de nouveau chatflow.
- **CodeDomain** : 1 chatflow paramétré par `programming_lang`. Logique commune (execution + stack trace + Bloom-like).
- **CyberSecDomain** : scenarios interactifs, NICE framework, workflows Capture-the-Flag light.
- **AccountingDomain** (futur) : peut-être un chatflow spécifique selon besoins.

## Interface `Domain` — point de contact unique webapp ↔ domaine

Le webapp ne connaît que l'interface abstraite. Quel que soit le domaine, le flow est identique :

```
POST /api/chat/send
  ↓
FastAPI route to Domain(domain_id)
  ↓
domain.handle_turn(user_input, context)
  ↓ (implementation-specific)
  - LanguageDomain : appelle Dify "language-tutor" avec config
  - CodeDomain : appelle Dify "code-mentor" avec config  
  ↓
returns StreamingResponse to frontend
```

Voir [shared-core.md](shared-core.md) pour le détail de l'interface.

## Chatflows Dify paramétrés

**Principe** : le chatflow est une **coquille minimaliste**. Tout ce qui est logique pédagogique vit dans `academie-core` (Python) et compose un prompt complet envoyé au chatflow.

Le chatflow Dify :
- Reçoit un prompt système déjà formé par `academie-core`
- Call LiteLLM avec le bon modèle (selon config domaine)
- Retourne la réponse streamée
- Minimal de nodes Python de pré/post-processing (marker stripping, sandbox)

**Avantage** : la logique est testable en Python pur (`academie-core.tests`) sans dépendre de Dify. Dify = pur orchestrateur de LLM.

## Migration depuis Teacher EN actuel

Aujourd'hui : 1 chatflow Dify `Teacher` avec ~28 nodes, prompt hardcoded EN.

**Plan de migration** (Sprint 4-5 si GO après analyse de risques) :

1. **Préserver l'actuel** : Teacher EN chatflow reste en place comme fallback
2. **Nouveau chatflow `language-tutor`** créé en parallèle, minimaliste
3. **LanguageDomain Python** instantie `academie-core/domain/language.py`
4. **FastAPI route `/api/chat/send?agent=teacher`** bascule progressivement vers `LanguageDomain(lang="en")` qui appelle `language-tutor`
5. **Tests E2E** sur users familiaux, comparaison comportement vs Teacher EN actuel
6. **Bascule complète** après validation. Teacher EN archivé.

Rollback possible à tout moment en rebasculant `/api/chat/send` vers l'ancien chatflow.

## Multi-langues : coût marginal d'ajout

Pour ajouter Maestro (ES) **après** bascule Teacher EN (Sprint 4 impl complet) :

1. Seed `rules/es.yaml` + `rubrics/es.yaml` + `fewshots/es.yaml` + `l1_transfer/fr_to_es.yaml`
2. Cloner Teacher V2 chatflow Dify pour `language-tutor-es` (les 6 chatbots legacy Maestro/Sensei/etc. sont **obsolètes** — à supprimer en Sprint 4 side-task, pas à activer)
3. Wire `DIFY_KEY_MAESTRO` en env var academie-api
4. Instancier `LanguageDomain(lang="es")` côté webapp — routing via `agent="maestro"`
5. Tests E2E avec family users

**Estimation post-Sprint-4** : **4.5-6.5 jours-dev** par nouvelle langue (Sprint 4 ré-analyse 2026-04-16), vs ~15 jours-dev avec l'approche "un chatflow per language + duplication code". Gain net = factorisation `academie-core` paie après 2ᵉ langue, et se cumule sur les 4 suivantes (ES/JP/DE/IT).

## Risques documentés

Cf. [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — 4 risques identifiés :

1. **Chatflow paramétré devient monstre à variables** → mitigation : logique dans Python, Dify minimaliste
2. **Abstraction Domain prématurée** → mitigation : conception minimale, extension incrémentale
3. **Coûts migration sous-estimés** → mitigation : estimation détaillée avant Sprint 4, rollback possible
4. **Scaling inter-domaines (cross-transfer)** → décision différée v3+

## Observability

Chaque appel Domain doit être loggué avec :
- `domain_id` (lang:en, code:python, …)
- `user_id`
- `tier` retourné (pour stats)
- `latency`
- `tokens_used`

Table cible `domain_call_log` (à créer avec la migration), avec partition par mois.

## Docs liées

- [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — décision détaillée + risques
- [shared-core.md](shared-core.md) — interface `Domain`
- [overview.md](overview.md) — contexte stack
- [../01-pedagogy/taxonomy-framework.md](../01-pedagogy/taxonomy-framework.md) — concepts pédagogiques sous-jacents
