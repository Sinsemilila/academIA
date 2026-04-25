---
title: ADR-001 — Architecture monolithe FastAPI maintenue, microservices envisagés
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-001 — Architecture monolithe FastAPI maintenue, microservices envisagés

## Contexte

Le backend `webapp/backend/app` est un monolithe FastAPI unique qui gère auth, chat proxy Dify, profil, error_analysis, admin, settings, token usage. La roadmap prévoit 7+ agents (Teacher EN, Maestro ES, Sensei JP, Lehrer DE, Professore IT, PyMentor Python, CyberMentor) et l'extension à des domaines non-linguistiques (Python, cybersec, système/réseau, comptabilité).

Question : découper en microservices maintenant ou rester monolithe ?

## Options envisagées

### Option A — Monolithe unique (actuel)

- Pour : simple déploiement, 1 pool DB, pas de complexité réseau inter-services, debugging direct
- Contre : un endpoint gourmand peut saturer les autres, code qui grossit devient moins lisible à terme

### Option B — Microservices par agent/domaine

- Pour : isolation pannes, scale indépendant, équipes distinctes possibles
- Contre : overkill solo-dev, complexité réseau, latence cumulée, debugging distribué

### Option C — Hybride (extraction ciblée quand pertinent)

- Pour : garder la simplicité monolithe, extraire un service quand un besoin réel apparaît (ex : scoring/IRT lourd)
- Contre : décisions au cas-par-cas, manque de standard

## Décision

**Option A (monolithe) maintenue pour l'instant.**

**Intention documentée** de migrer vers Option C (extraction ciblée) si :
- La charge sur un module spécifique sature le reste (ex : scoring/IRT batch)
- Le nombre d'agents rend le code monolithique difficile à maintenir
- Un domaine spécifique a un stack technologique très différent (ex : PyMentor qui a besoin d'un sandbox code exec temps réel)

**Justification** : le développement est solo, l'échelle utilisateurs est familiale (~20 max à court terme), la complexité d'un découpage microservices n'est pas justifiée aujourd'hui. Extraction ciblée au moment où un besoin concret apparaît.

## Conséquences

- Positives : vélocité de dev préservée, déploiements simples, 1 seul dépôt à maintenir
- Acceptées : si un agent lourd arrive (PyMentor avec exec code en sandbox temps réel), il faudra ré-évaluer
- Neutres à surveiller : taille du monorepo, temps de CI, mémoire du process FastAPI

## Actions de mise en œuvre

- [x] Conserver l'organisation actuelle `webapp/backend/app/routers/*.py`
- [ ] Pour la factorisation de logique commune (taxonomie, scoring, IRT), utiliser le package `academie-core` (cf. ADR-005) — **sans** en faire un microservice séparé
- [ ] Monitoring des ressources du process monolithe pour détecter saturation (cf. dimension observability à définir)

## Re-évaluation

À re-examiner si :
- Users actifs > 500 simultanés
- Temps de réponse API > 2s sur endpoints critiques (chat, profile)
- Incidents de saturation mémoire
- Roadmap explicite vers SaaS public activée

## Références

- Conversation Session 13 (2026-04-15) avec sinse
- [ADR-005-academie-core-shared-library.md](ADR-005-academie-core-shared-library.md) — complémentaire
