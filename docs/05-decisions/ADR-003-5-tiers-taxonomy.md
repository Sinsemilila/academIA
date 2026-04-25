---
title: ADR-003 — 5 tiers de gravité d'erreur (T0-T4) pour la taxonomie
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-003 — 5 tiers de gravité d'erreur (T0-T4) pour la taxonomie

## Contexte

La matrice actuelle (`tolerance_matrix.yaml`) utilise **4 tiers** : `ignored`, `shadow`, `noted`, `penalized`. La refonte visera à :

- Distinguer pré-acquisition (structure pas encore vue au curriculum) de tolérance (structure vue mais acceptée à ce niveau)
- Capturer les erreurs "régressives" (C2 qui rate quelque chose normalement acquis depuis B1) distinctes des erreurs "attendues" (B1 qui fait une erreur B2)
- Permettre un feedback gradué Lyster (cf. ADR-sur-feedback-delivery à venir)

Le research agent SLA (cf. `01-pedagogy/bibliography.md`) a identifié l'importance de ces distinctions (Pienemann teachability, Corder mistake vs error, DeKeyser skill acquisition stages).

## Options envisagées

### Option A — Garder 4 tiers actuels

- Pour : simplicité, continuité
- Contre : ne distingue pas pre_acquisition de ignored, ne capture pas les cas régressifs

### Option B — 5 tiers avec T0 pre_acquisition et T4 regressive

- Pour : alignement avec la science (Pienemann + Corder + DeKeyser), feedback plus fin
- Contre : +1 catégorie = complexité UX, nécessite plus de data pour calibrer

### Option C — Scoring continu (pas de tiers, juste θ ∈ ℝ)

- Pour : flexibilité maximale
- Contre : trop abstrait pour UX admin, besoins en data massive (IRT continu)

## Décision

**Option B — 5 tiers** :

| Tier | Nom | Sens | Action pédagogique |
|---|---|---|---|
| **T0** | `pre_acquisition` | structure pas encore au curriculum du niveau | **jamais flag** (Pienemann teachability) |
| **T1** | `ignored` | erreur normale au niveau attendu | jamais affichée, journalisée pour stats |
| **T2** | `noted` | erreur fréquente mais formative | recast léger inline (style Lyster implicite) |
| **T3** | `penalized` | erreur attendue corrigible au niveau | prompt elicitation/metalinguistic |
| **T4** | `regressive` | structure censée acquise depuis N-2 niveaux | prompt + remédiation + flag remediation |

**Justification** :
- T0 distingue vraiment "structure pas vue" de "structure vue mais tolérée" — important pédagogiquement (ne jamais pénaliser une structure pré-acquisition)
- T4 identifie un pattern pédagogique distinct (fossilisation ou slip déclaratif) qui mérite une action différente
- Scoring continu (option C) est prématuré tant qu'on n'a pas la data pour calibrer un IRT ; peut être ajouté **au-dessus** des tiers plus tard sans casser la rétrocompatibilité

## Conséquences

- Positives : meilleure granularité pédagogique, mapping direct vers les types de feedback Lyster & Ranta (1997)
- Acceptées : complexité UX légèrement supérieure côté admin (afficher 5 tiers au lieu de 4)
- Acceptées : migration des snapshots existants (cf. ADR-007 cut-off propre)

## Actions de mise en œuvre

- [ ] Refactor `tolerance_matrix.yaml` structure (cf. ADR-002)
- [ ] Mettre à jour `error_taxonomy/scoring.py::_get_error_tier()` pour retourner T0-T4
- [ ] Mettre à jour les consommateurs frontaux (dashboard, Teacher prompt)
- [ ] Calibrer les seuils entre tiers empiriquement (GLMM sur données existantes, cf. Sprint 1)

## Re-évaluation

Si après 3-6 mois de calibration empirique les données montrent que certains tiers sont inutiles (peu peuplés) ou qu'il en manque un, réviser.

## Références

- [01-pedagogy/bibliography.md](../01-pedagogy/bibliography.md) — Pienemann (1998), Corder (1981), DeKeyser (2007), Lyster & Saito (2010)
- [ADR-002-schema-from-day-1.md](ADR-002-schema-from-day-1.md)
- [ADR-007-snapshot-versioning-cutoff.md](ADR-007-snapshot-versioning-cutoff.md)
