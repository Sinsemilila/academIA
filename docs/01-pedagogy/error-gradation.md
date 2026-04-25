---
title: Calibration empirique des tiers de gravité d'erreur
status: authoritative
last_reviewed: 2026-04-15
---

> **Sprint 1 + 1.5 exécutés** (Session 15, 2026-04-15) : Path A retenu, calibration sur W&I + LOCNESS via NumPyro GLMM hierarchical logistic. Poids empiriques (relative-to-T1) : `ignored=0.00, noted=0.196, penalized=0.394, regressive=0.538`. Résultats détaillés dans [`sprint1_report.md`](sprint1_report.md).

# Calibration empirique des tiers de gravité d'erreur

> Comment on passe de poids arbitraires (ex: `noted=0.3, penalized=0.8` actuels) à des valeurs calibrées sur des données réelles.

## Contexte

La matrice de tolérance actuelle utilise des poids inventés. **Rifkin & Roberts (1995)** a démoli les hiérarchies d'error gravity publiées pour cause de non-généralisabilité. La science recommande de construire **sa propre** calibration sur **sa population**.

## Pipeline de calibration — 5 étapes

### Étape 1 — Corpus seed

Bootstrap avec data existante AcademIA + corpus open externes :
- `error_log` + `profils_eleves` + `snapshots_session` (AcademIA)
- **W&I Corpus 2024** (5050 essays EN, CEFR + erreurs) — CC open
- **EFCAMDAT** (1.18M textes EN, 174k apprenants, 16 niveaux) — application académique
- **MERLIN** (2286 textes DE/IT A1-C1, CC BY-SA 4.0) — pour les futurs Lehrer/Professore
- **CEDEL2** (ES L2, 6560 participants) — pour Maestro futur

Pour chaque combinaison `(famille, concept, niveau_CECRL)`, calculer :
- **Taux d'incidence** : erreurs / 1000 tokens
- **Distribution inter-apprenants** : quelle proportion des apprenants à ce niveau fait cette erreur

### Étape 2 — Définition statistique des tiers

Seuils percentile sur la distribution :

| Tier | Seuil |
|---|---|
| T0 `pre_acquisition` | concept pas encore testé à ce niveau (curriculum-based) |
| T1 `ignored` | erreur présente chez ≥ 70% des apprenants du niveau |
| T2 `noted` | erreur chez 30-70% des apprenants |
| T3 `penalized` | erreur chez 10-30% des apprenants |
| T4 `regressive` | erreur chez < 10% (aberrante pour ce niveau) |

**Rationale** : si 80% des A1 font cette erreur, elle est **normale** au A1. Pénaliser = pénaliser la normalité → démotivation. À l'inverse, si seulement 5% des B2 la font, celle-ci **doit** être signalée.

**Ces seuils 70/30/10 sont des priors**, à valider et affiner via étape 3-4.

### Étape 3 — GLMM (Generalized Linear Mixed Model)

Modèle :

```
logit(P_next_error_ij) = β₀ + β_tier · tier_ij + u_i + v_j
  où u_i ~ N(0, σ²_u)    # effet aléatoire par élève
     v_j ~ N(0, σ²_v)    # effet aléatoire par concept
```

Intuition : si la matrice capture bien la gravité, les β_tier doivent former un gradient (T1 → T4 = β croissant).

**Lib Python** : `pymer4` (wrapper lme4 R via rpy2) ou NumPyro en random-effects bayésien.

**Effort** : ~2-3 jours de dev + analyse.

**Output** : coefficients empiriques par tier, à comparer avec les priors 0.0/0.3/0.8. Ajustement direct dans `tolerance_matrix.yaml`.

### Étape 4 — Cox Proportional Hazards (half-life d'erreur)

Modèle de survie :

```
h(t | x) = h_0(t) · exp(β^T x)
  où x = [tier_at_last_occurrence, concept, niveau, mode_session]
        t = nombre de sessions avant que l'erreur se reproduise
```

Intuition : une erreur `penalized` corrigée **doit** réapparaître moins vite qu'une `noted` (sinon notre tier n'est pas le bon).

**Lib Python** : `lifelines` (mature, excellent).

**Output interprétable** : "half-life de la famille verb_tense au niveau B1 = 8 sessions" → dashboard admin direct.

### Étape 5 — Validation expert (kappa inter-raters)

Protocole :
- 3 à 5 enseignants CECRL-certifiés
- Échantillon stratifié ~300-500 productions d'apprenants
- Chaque expert annote le tier perçu : T0 / T1 / T2 / T3 / T4
- Calcul du **kappa de Cohen pondéré quadratique** entre expert et modèle

**Cible** : κ ≥ 0.6 (accord "substantiel" selon Landis & Koch 1977).

Si κ < 0.6 sur un sous-ensemble famille × niveau, **re-calibrer** les seuils sur ce sous-ensemble.

### Étape 6 — Validation prédictive (leave-one-level-out)

Cross-validation : mask un niveau (ex. A2), prédire depuis A1+B1+B2, comparer aux vrais tags A2.

Si le modèle généralise mal sans un niveau → la matrice n'est pas réellement graduée, elle est surajustée aux niveaux vus.

## Graded Response Model (au-delà du GLMM)

Pour les sprints moyens/longs (quand on a > 25k interactions) :

**GRM de Samejima (1969)** — IRT polytomique :

```
P*(X_ij ≥ k | θ_i) = 1 / (1 + exp(-a_j · (θ_i - b_jk)))
P(X_ij = k) = P*(≥k) - P*(≥k+1)
```

Chaque concept = item polytomique, catégories {T1=0, T2=1, T3=2, T4=3} (T0 traité séparément car curriculum-based).

Les **seuils bⱼ,₁, bⱼ,₂, bⱼ,₃** remplacent les 0.3/0.8 arbitraires.

**Lib** : `girth` (légère, supporte GRM) ou NumPyro bayésien.

**Output** : par concept, courbes de probabilité par tier en fonction de θ (ability latente en logits).

## Protocole de re-calibration continue

Mensuel automatique :
1. Query `error_log` + `snapshots_session` → dump Parquet
2. Re-fit GLMM + Cox PH sur data cumulée
3. Comparer coefficients au mois précédent — alerte si drift > 1 σ
4. Re-fit GRM trimestriel (plus coûteux)
5. Dashboard admin montre : "matrice calibrée sur N interactions, dernière mise à jour YYYY-MM-DD"

## Priors initiaux (avant data suffisante)

Tant qu'on a < 10k interactions AcademIA :
- Gravity axes par famille : valeurs de [`cefr-language-instance.md`](cefr-language-instance.md) (prior intuitif, annotation cible)
- Seuils tiers : percentiles 70/30/10 empiriques bootstrappés sur W&I + EFCAMDAT (corpus externes)
- L1 multipliers : typologie URIEL/lang2vec (default 1.0, ajustement typologique limité)

Dès que les 3 premières itérations de calibration empirique convergent (σ stable), on bascule sur les valeurs auto-calibrées.

## Risques méthodologiques

### Biais de sélection
Notre population est auto-sélectionnée (familial, amis de Sinse). Ne pas assumer la généralisabilité au grand public avant qu'AcademIA soit ouvert.

### Overfitting au corpus externe
W&I + EFCAMDAT sont des essais **écrits** et souvent **examen**. Ne pas transposer trivialement au chat conversationnel oral/hybride d'AcademIA.

### Effet plafond
Les erreurs les plus rares (< 1%) n'ont pas assez de data pour calibrer fiablement → garder les priors jusqu'à accumulation.

### Confounding élève × concept
Un élève donné peut avoir un profil d'erreur très différent de la moyenne. Les random effects du GLMM le capturent partiellement, pas totalement.

## Références

- [bibliography.md](bibliography.md) — GLMM, Cox PH, GRM, calibration méthodologie
- [ADR-003-5-tiers-taxonomy.md](../05-decisions/ADR-003-5-tiers-taxonomy.md)
- Code futur : `academie-core/psychometrics/calibration.py`, `academie-core/psychometrics/irt.py`
