---
title: ADR-002 — Schéma de taxonomie conçu multi-langue et multi-domaine dès le départ
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-002 — Schéma de taxonomie conçu multi-langue et multi-domaine dès le départ

## Contexte

La taxonomie d'erreur actuelle (`webapp/backend/app/config/tolerance_matrix.yaml` + `error_taxonomy/*.py`) est entièrement centrée sur l'anglais. La roadmap prévoit :

1. Extension à 4 langues supplémentaires (ES/JP/DE/IT)
2. Extension à des domaines **non-linguistiques** (Python, cybersec, compta) où le CECRL ne s'applique pas

Question : refondre le schéma multi-langue + multi-domaine dès maintenant ou attendre d'avoir besoin ?

## Options envisagées

### Option A — EN-first, port à chaque ajout

- Pour : ship plus vite, apprentissage par expérience, pas de YAGNI
- Contre : refactor douloureux à chaque ajout, risque de re-architecturer N fois

### Option B — Schema-from-day-1 complet

- Pour : aucun refactor futur, rigueur de design
- Contre : ~30% effort initial, risque d'over-engineer dans le vide

### Option C — Voie médiane (structure multi, data EN-only)

- Pour : compromis entre coût initial et solidité future
- Contre : le data EN peut quand même devoir évoluer quand on ajoute une langue

## Décision

**Option B (Schema-from-day-1 complet)**, dans sa déclinaison la plus complète : **abstraction Domain + instances par langue/domaine**.

**Justification** : 
- Le message produit "socle pour toutes les langues futures" (Sinse) implique que la refondation doit être structurelle, pas cosmétique
- L'ajout de domaines non-linguistiques (Python, cybersec, compta) impose de toutes façons une abstraction au-dessus de CECRL
- Faire l'abstraction maintenant, alors qu'on ne la peuple que pour EN, est moins cher que de la créer plus tard en rebâtissant l'existant
- Le surcoût ~30% concerne principalement l'architecture du schéma, pas les données (qui restent EN-only pour l'instant)

## Conséquences

- Positives : aucun refactor au moment d'ajouter Maestro/Sensei/PyMentor ; forces la conception propre de l'abstraction `Domain`
- Acceptées : effort initial plus important sur Sprint 2 ; risque que certains choix d'abstraction se révèlent mal adaptés quand les vrais besoins ES/JP/DE/IT/Python apparaissent (à mitiger par une itération future non-bloquante)
- Neutres à surveiller : la complexité cognitive d'une abstraction Domain peut ralentir temporairement les contributeurs qui ne l'ont pas intériorisée

## Actions de mise en œuvre

- [ ] Sprint 2 taxonomie : refactor `tolerance_matrix.yaml` → structure par langue, table `l1_transfer_multipliers.yaml` séparée
- [ ] Interface `Domain` dans `academie-core` (cf. ADR-005)
- [ ] Documentation de l'abstraction dans [`02-architecture/shared-core.md`](../02-architecture/shared-core.md)
- [ ] Tests unitaires sur l'abstraction avant instanciation autres langues

## Re-évaluation

À re-examiner à l'ajout du 2ᵉ domaine effectif (Maestro ou PyMentor) — vérifier que l'abstraction tient la route ou doit évoluer.

## Références

- [ADR-003-5-tiers-taxonomy.md](ADR-003-5-tiers-taxonomy.md) — taxonomie elle-même
- [ADR-004-hybrid-orchestrated-agent-topology.md](ADR-004-hybrid-orchestrated-agent-topology.md) — architecture d'orchestration
- [ADR-005-academie-core-shared-library.md](ADR-005-academie-core-shared-library.md) — package Python partagé
