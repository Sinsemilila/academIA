---
title: v1 vs v2 — simulation 6 personas A1→C2 (Approach A)
status: authoritative
last_reviewed: 2026-04-15
owner: claude
---

# v1 vs v2 — simulation 6 personas (Approach A)

> Simulation déterministe : 6 personas (A1→C2) avec error sets typiques
> de chaque niveau (sources : Bryant 2017, Yannakoudakis 2018, Rifkin &
> Roberts 1995, AcademIA criterial priors). Pour chaque persona, scoring
> identique appliqué avec matrix v1 vs matrix v2 (avec override).
>
> But : valider quantitativement que v2 produit des scores plus
> empiriquement pertinents (lenient sur endemic, strict sur rare).

## Synthèse globale

| Niveau | Erreurs total | Score v1 | Score v2 | Delta | Direction |
|---|---:|---:|---:|---:|---|
| **A1** | 48 | 1.20 | 1.96 | +0.76 (+64%) | 🔴 plus strict |
| **A2** | 50 | 0.90 | 2.35 | +1.45 (+162%) | 🔴 plus strict |
| **B1** | 35 | 7.80 | 2.75 | -5.05 (-65%) | 🟢 plus lenient |
| **B2** | 31 | 13.80 | 5.10 | -8.70 (-63%) | 🟢 plus lenient |
| **C1** | 20 | 16.00 | 6.50 | -9.50 (-59%) | 🟢 plus lenient |
| **C2** | 11 | 8.80 | 3.54 | -5.26 (-60%) | 🟢 plus lenient |

**Lecture** :
- A1/A2 : v2 plus strict — détecte les rare errors (sentence, word_order) que v1 ignorait
- B1+ : v2 plus lenient — relaxe les endemic errors (verb_tense, noun_det, surface) que v1 sur-pénalisait
- Pattern attendu (cf. sprint1_report.md § 4.2 et matrix_v2_review.md)

## Persona A1

**Erreurs simulées** : 48 occurrences sur 14 codes distincts

```
  SPELL              × 6
  ORTH:CASE          × 4
  PUNCT              × 3
  V:TENSE            × 5
  V:SVA              × 4
  V:FORM             × 3
  N:COUNT            × 4
  ART                × 5
  PRON:FORM          × 3
  PREP               × 5
  SENT:FRAG          × 1
  WO                 × 1
  LEX:CALQUE         × 2
  PREP:CALQUE        × 2
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| calque | 4 | noted | 0.30 | 1.20 | noted | 0.20 | 0.78 | -0.42 🟢 |
| noun_det | 9 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| preposition | 5 | shadow | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| pronoun | 3 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.59 | +0.59 🔴 |
| sentence | 1 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.20 | +0.20 🔴 |
| surface | 13 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| verb_tense | 12 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| word_order | 1 | ignored | 0.00 | 0.00 | penalized | 0.39 | 0.39 | +0.39 🔴 |
| **TOTAL** | **48** | | | **1.20** | | | **1.96** | **+0.76** |

## Persona A2

**Erreurs simulées** : 50 occurrences sur 18 codes distincts

```
  SPELL              × 4
  ORTH:CASE          × 2
  PUNCT              × 3
  V:TENSE            × 5
  V:SVA              × 3
  V:FORM             × 4
  V:INFL             × 3
  V:MODAL            × 2
  N:COUNT            × 3
  ART                × 4
  DET                × 2
  PRON:FORM          × 2
  PRON:CHOICE        × 2
  PREP               × 4
  PREP:CALQUE        × 3
  ADJ:CHOICE         × 2
  SENT:FRAG          × 1
  WO:QUEST           × 1
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| calque | 3 | noted | 0.30 | 0.90 | noted | 0.20 | 0.59 | -0.31 🟢 |
| morphology | 2 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.39 | +0.39 🔴 |
| noun_det | 9 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| preposition | 4 | shadow | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| pronoun | 4 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.78 | +0.78 🔴 |
| sentence | 1 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.20 | +0.20 🔴 |
| surface | 9 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| verb_tense | 15 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| verb_usage | 2 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| word_order | 1 | ignored | 0.00 | 0.00 | penalized | 0.39 | 0.39 | +0.39 🔴 |
| **TOTAL** | **50** | | | **0.90** | | | **2.35** | **+1.45** |

## Persona B1

**Erreurs simulées** : 35 occurrences sur 18 codes distincts

```
  SPELL              × 2
  PUNCT              × 2
  V:TENSE            × 4
  V:SVA              × 2
  V:ASPECT           × 2
  V:MODAL            × 3
  V:COND             × 2
  V:PASS             × 1
  N:COUNT            × 2
  ART                × 3
  ART:GENERIC        × 1
  PREP               × 3
  LEX:CHOICE         × 2
  LEX:COLLOC         × 1
  SENT:RUNON         × 1
  SENT:SUBORD        × 2
  MORPH:WORDCLASS    × 1
  DISC:TRANS         × 1
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| discourse | 1 | shadow | 0.00 | 0.00 | shadow | 0.00 | 0.00 | +0.00 ≈ |
| morphology | 1 | ignored | 0.00 | 0.00 | noted | 0.20 | 0.20 | +0.20 🔴 |
| noun_det | 6 | noted | 0.30 | 1.80 | ignored | 0.00 | 0.00 | -1.80 🟢 |
| preposition | 3 | noted | 0.30 | 0.90 | ignored | 0.00 | 0.00 | -0.90 🟢 |
| sentence | 3 | ignored | 0.00 | 0.00 | penalized | 0.39 | 1.18 | +1.18 🔴 |
| surface | 4 | ignored | 0.00 | 0.00 | ignored | 0.00 | 0.00 | +0.00 ≈ |
| verb_tense | 10 | noted | 0.30 | 3.00 | ignored | 0.00 | 0.00 | -3.00 🟢 |
| verb_usage | 4 | noted | 0.30 | 1.20 | noted | 0.20 | 0.78 | -0.42 🟢 |
| vocabulary | 3 | noted | 0.30 | 0.90 | noted | 0.20 | 0.59 | -0.31 🟢 |
| **TOTAL** | **35** | | | **7.80** | | | **2.75** | **-5.05** |

## Persona B2

**Erreurs simulées** : 31 occurrences sur 17 codes distincts

```
  V:ASPECT           × 2
  V:COND             × 2
  V:MODAL            × 3
  V:PASS             × 2
  V:CHOICE           × 2
  ART:GENERIC        × 2
  PREP               × 3
  PREP:CALQUE        × 1
  LEX:CHOICE         × 3
  LEX:COLLOC         × 2
  LEX:FALSE          × 1
  SENT:SUBORD        × 2
  SENT:PARALLEL      × 1
  DISC:TRANS         × 2
  DISC:COHER         × 1
  REG:LEVEL          × 1
  WO                 × 1
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| calque | 1 | penalized | 0.80 | 0.80 | penalized | 0.39 | 0.39 | -0.41 🟢 |
| discourse | 4 | noted | 0.30 | 1.20 | noted | 0.20 | 0.78 | -0.42 🟢 |
| noun_det | 2 | noted | 0.30 | 0.60 | ignored | 0.00 | 0.00 | -0.60 🟢 |
| preposition | 3 | penalized | 0.80 | 2.40 | ignored | 0.00 | 0.00 | -2.40 🟢 |
| sentence | 3 | noted | 0.30 | 0.90 | penalized | 0.39 | 1.18 | +0.28 🔴 |
| verb_tense | 4 | penalized | 0.80 | 3.20 | ignored | 0.00 | 0.00 | -3.20 🟢 |
| verb_usage | 7 | noted | 0.30 | 2.10 | noted | 0.20 | 1.37 | -0.73 🟢 |
| vocabulary | 6 | noted | 0.30 | 1.80 | noted | 0.20 | 1.18 | -0.62 🟢 |
| word_order | 1 | penalized | 0.80 | 0.80 | noted | 0.20 | 0.20 | -0.60 🟢 |
| **TOTAL** | **31** | | | **13.80** | | | **5.10** | **-8.70** |

## Persona C1

**Erreurs simulées** : 20 occurrences sur 14 codes distincts

```
  V:COND             × 1
  V:ASPECT           × 1
  ART:GENERIC        × 1
  LEX:COLLOC         × 3
  LEX:FALSE          × 2
  LEX:IDIOM          × 2
  LEX:ARGSTRUCT      × 1
  SENT:PARALLEL      × 1
  SENT:MOD           × 1
  DISC:COHER         × 2
  DISC:TRANS         × 1
  REG:LEVEL          × 2
  REG:PRAGMA         × 1
  MORPH:DERIV        × 1
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| discourse | 6 | penalized | 0.80 | 4.80 | penalized | 0.39 | 2.36 | -2.44 🟢 |
| morphology | 1 | penalized | 0.80 | 0.80 | noted | 0.20 | 0.20 | -0.60 🟢 |
| noun_det | 1 | penalized | 0.80 | 0.80 | ignored | 0.00 | 0.00 | -0.80 🟢 |
| sentence | 2 | penalized | 0.80 | 1.60 | penalized | 0.39 | 0.79 | -0.81 🟢 |
| verb_tense | 2 | penalized | 0.80 | 1.60 | ignored | 0.00 | 0.00 | -1.60 🟢 |
| vocabulary | 8 | penalized | 0.80 | 6.40 | penalized | 0.39 | 3.15 | -3.25 🟢 |
| **TOTAL** | **20** | | | **16.00** | | | **6.50** | **-9.50** |

## Persona C2

**Erreurs simulées** : 11 occurrences sur 8 codes distincts

```
  LEX:COLLOC         × 2
  LEX:IDIOM          × 2
  DISC:COHER         × 1
  REG:LEVEL          × 1
  REG:PRAGMA         × 2
  MORPH:DERIV        × 1
  PREP               × 1
  ART:GENERIC        × 1
```

### Comparaison family × tier × weight

| Famille | Erreurs | Tier v1 | Weight v1 | Subtotal v1 | Tier v2 | Weight v2 | Subtotal v2 | Δ |
|---|---:|---|---:|---:|---|---:|---:|---:|
| discourse | 4 | penalized | 0.80 | 3.20 | penalized | 0.39 | 1.58 | -1.62 🟢 |
| morphology | 1 | penalized | 0.80 | 0.80 | noted | 0.20 | 0.20 | -0.60 🟢 |
| noun_det | 1 | penalized | 0.80 | 0.80 | ignored | 0.00 | 0.00 | -0.80 🟢 |
| preposition | 1 | penalized | 0.80 | 0.80 | noted | 0.20 | 0.20 | -0.60 🟢 |
| vocabulary | 4 | penalized | 0.80 | 3.20 | penalized | 0.39 | 1.58 | -1.62 🟢 |
| **TOTAL** | **11** | | | **8.80** | | | **3.54** | **-5.26** |

## Effet de l'override `sentence × beginner = noted`

- **A1** : sentence sans override = `penalized` (subtotal 0.39) → avec override = `noted` (subtotal 0.20). Différence : -0.20 sur le total.
- **A2** : sentence sans override = `penalized` (subtotal 0.39) → avec override = `noted` (subtotal 0.20). Différence : -0.20 sur le total.

**Conclusion override** : réduit la pénalité sentence chez A1/A2 (cohérent avec rationale chat fragments != essay fragments).

## Effet de l'enrichissement gravity_axes + criterial_levels

Les nouvelles colonnes `gravity_*` et `criterial_level_*` sont **populées** dans `error_log` mais
**pas encore utilisées** par `compute_error_profile` (`USE_V2_SCORING=false`). Pour montrer leur potentiel :

| Famille | gravity_linguistic | gravity_communicative | gravity_social | criterial_emergence | criterial_mastery |
|---|---:|---:|---:|---|---|
| calque | 0.4 | 0.5 | 0.5 | A1 | B2 |
| discourse | 0.3 | 0.8 | 0.5 | B1 | C1 |
| morphology | 0.5 | 0.3 | 0.1 | A1 | C1 |
| noun_det | 0.4 | 0.3 | 0.0 | A1 | B1 |
| preposition | 0.5 | 0.4 | 0.1 | A1 | B2 |
| pronoun | 0.6 | 0.6 | 0.2 | A1 | A2 |
| sentence | 0.7 | 0.7 | 0.1 | A2 | C1 |
| surface | 0.3 | 0.2 | 0.3 | A1 | A2 |
| verb_tense | 0.6 | 0.4 | 0.1 | A1 | B2 |
| verb_usage | 0.7 | 0.5 | 0.2 | A2 | C1 |
| vocabulary | 0.4 | 0.7 | 0.3 | A1 | C2 |
| word_order | 0.8 | 0.7 | 0.1 | A1 | B1 |

**Cas d'usage futurs (Phase B3 / Sprint 6+)** :
- UI : afficher gravity_communicative comme "impact sur la compréhension" (score colorisé)
- Scoring : pondérer le tier par gravity_communicative pour les erreurs blocantes (priorité haute si > 0.7)
- Recommendation : prioriser les erreurs au-dessus du criterial_mastery du niveau ("tu devrais déjà maîtriser ça")

## Limites de la simulation

- **Personas synthétiques** : codes choisis par intuition SLA, pas issus d'utilisateurs réels AcademIA
- **Counts arbitraires** : 5×SPELL pour A1 = approximation, vraies distributions varieront
- **Pas d'effet random_effect (learner)** : tous les personas considérés "moyens"
- **Familles non calibrées** (verb_usage, vocabulary, calque, discourse) gardent les priors v1 — leur impact dans le tableau peut être surestimé
- **`compute_error_profile` complet** non simulé — recommendation/eligibility nécessitent session_id et turn structure que les personas n'ont pas

Pour valider en réel : Approach C (synthetic transcripts + LLM analysis) ou attendre des users réels A1-C2 sur AcademIA.

## Recommandations

1. **Valider auprès d'un éleve** : montrer le tableau des familles à un user réel à différents niveaux pour qualité ressentie
2. **Phase B3** (USE_V2_SCORING=true) : activer la lecture de `tier` depuis error_log → consistance historique
3. **Sprint 6** : recalibration sur AcademIA quand error_log ≥ 10k rows + activation gravity-based pondération
4. **Approach C** dans une session ultérieure : générer 6 transcripts via LLM Teacher pour test E2E réaliste
