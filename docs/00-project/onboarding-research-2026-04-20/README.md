# Onboarding Refonte — Dossier de recherche (2026-04-20)

Archive des 7 rapports de recherche multi-agents qui ont cadré la refonte de l'onboarding AcademIA — passage d'un onboarding conversationnel LLM vers un **QCM pre-chat** (modal bloquant 1re visite par langue) qui collecte les préférences déclaratives en bloc et injecte un contexte structuré au LLM avant son premier turn. Le LLM se concentre alors uniquement sur le diagnostic CEFR observationnel.

## Décisions figées avec Sinse (2026-04-20)

| ID | Décision | Reco | Choix final |
|---|---|---|---|
| D1 | Scope Bloc A | 5 variables ID complètes | ✅ 5 complètes |
| D2 | FLA / anxiety | Dans le QCM (3 items Likert) | ✅ Dans le QCM |
| D3 | Stockage DB | Nouvelle table `learner_profiles` | ✅ Nouvelle table |
| D4 | Cross-domain | Option C hybride (structure prête, items 100% langue) | ✅ Option C |
| D5 | Langue UI | FR-only v1 + structure i18n-ready | ✅ FR-only + YAML `_i18n` prêt |
| D6 | Migration users ES existants | Redéclenche QCM fresh | ✅ Fresh |
| D7 | Archivage | Figer les rapports en docs | ✅ Ce dossier |

## Architecture retenue — 3 blocs

```
Bloc A — UNIVERSAL CORE (5 Q, tous domaines)
  Self-efficacy · Mindset · Goal specificity · Autonomy · Engagement
Bloc B — DOMAIN LEVEL (2-3 Q, propre au domaine)
  Langues : CEFR can-do bi-skill + mini-probe conditionnel
Bloc C — DOMAIN MOTIVATION (2 Q, propre au domaine)
  Langues : Ideal L2 Self + FLA 3-items
```
Total : 8-10 questions, 90 s-3 min.

## Inventaire des rapports

### Vague 1 — Recherche théorique (4 agents en parallèle)

- [`vague1-competitive-benchmark.md`](vague1-competitive-benchmark.md) — Benchmark des onboardings Duolingo, Babbel, Busuu, Loora, Speak, Noom, Headspace. Patterns à voler (image picker motivation, self-report + placement test conditionnel, daily commitment slider) et anti-patterns (Noom 96-screens, placement obligatoire pré-signup, open text forcé).
- [`vague1-cefr-self-assessment.md`](vague1-cefr-self-assessment.md) — Science du self-assessment CEFR. Ross 1998 (r=.63), DIALANG r=.91-.93, effets format (can-do > labels A1/A2), modes d'échec (Dunning-Kruger, impostor B2-C1, biais culturel est-asiatique), approche hybride self-report + mini-probe.
- [`vague1-motivation-id-variables.md`](vague1-motivation-id-variables.md) — Variables de différences individuelles prouvées prédictives en L2 : Ideal L2 Self (Dörnyei r=.61), FLA (Teimouri r=-.36), self-efficacy, autonomy orientation (SDT), language mindset (Lou & Noels), goal specificity (Locke-Latham), WTC. Variables écartées : learning styles VAK (pseudoscience Pashler 2008), integrativeness Gardner, SILL complet, MLAT.
- [`vague1-cold-start-its.md`](vague1-cold-start-its.md) — Littérature Intelligent Tutoring Systems et Open Learner Model (Bull & Kay), cold-start recommender systems, Knowledge Tracing (BKT/DKT/AKT), systèmes réels (ASSISTments, ALEKS, Khan, Duolingo). Minimum viable signal = 4 items + placement adaptatif optionnel.

### Vague 2 — Application au projet (3 agents en parallèle)

- [`vague2-codebase-audit.md`](vague2-codebase-audit.md) — Cartographie exhaustive du flow onboarding actuel (frontend route, chat_router, Dify chatflow, n8n diagnostic, DB schema). Points d'injection pour le QCM pre-chat. Impact structurel sur les 3 bugs Session 32 (language-mixing, `[EVAL_READY]` loop, bilan sans niveau CEFR). Fichiers à modifier/créer + ordre de déploiement.
- [`vague2-qcm-design.md`](vague2-qcm-design.md) — Design détaillé du QCM multi-langues. 8 questions, structure tronc commun + overlays YAML par langue, format d'injection LLM (double canal JSON + résumé NL), schéma DB `learner_profiles`, endpoints REST, branching mini-probe, UX flow step-by-step, tradeoffs A/B/C (C recommandée).
- [`vague2-cross-domain-vision.md`](vague2-cross-domain-vision.md) — Extension du framework à PyMentor, CyberMentor et autres domaines hors-langue. Décomposition en 3 couches (universal / domain-wrapped / domain-specific). Faux-amis identifiés (goal specificity, anxiety phénoménologies distinctes, Ideal Future Self expérientiel vs identitaire). Règle de 3 pour factoriser (ne pas spéculer avant 3 instanciations réelles).

## Prochaines étapes

1. Design doc consolidé (formulations FR exactes des 8 questions + UX modal + contract d'API)
2. Implémentation Sprint 1 : tronc commun YAML + UI modal + persistance DB + injection Dify
3. Activation Teacher EN + Maestro ES (alpha famille)
4. Sprint 2+ : overlays par langue pour Wave 2+ (IT, DE, JP, RU)

## Contexte Wave 1 ES

La refonte onboarding est prioritaire sur la Phase D battery validation ES (bugs live Session 32 structurellement résolus par le refactor). Wave 1 ES reprendra post-onboarding sur le nouveau flow.
