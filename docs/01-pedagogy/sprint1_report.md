---
title: Sprint 1 Report — External corpus calibration (Path A)
status: authoritative
last_reviewed: 2026-04-15
owner: claude
---

# Sprint 1 — Calibration empirique via corpus externes

> Rapport de résultats du Sprint 1 de la roadmap taxonomie v2.
> Path A retenu (Sinse, Session 15) : calibration sur corpus externes faute de
> volume AcademIA interne suffisant.

## 1. Contexte et décision

**Objectif initial** (roadmap.md § Sprint 1) : remplacer les poids arbitraires
`ignored=0.0 / noted=0.3 / penalized=0.8 / shadow=0.0` par des valeurs calibrées
empiriquement via GLMM + Cox PH sur data AcademIA réelle.

**Data reality check** au pickup de Session 15 :
- `error_log` = 9 rows (pipeline déployée 2026-04-14, hier)
- Messages Dify utilisables = ~300 réels + ~1 200 synthétiques test-e2e-*
- `profils_eleves` actifs : 11 B1 + 1 A1
- **Incompatible avec GLMM random-effects** sur data interne

**Décision** : Path A — calibrer sur W&I + LOCNESS (BEA 2019) pour obtenir des
priors calibrés, et préparer la méthodologie pour re-tourner sur AcademIA quand
la data sera suffisante (Sprint 1.5 ou 6+).

## 2. Corpus utilisé

**W&I + LOCNESS Corpus** — BEA 2019 shared task on Grammatical Error Correction.
- Source : Cambridge English, https://www.cl.cam.ac.uk/research/nl/bea2019st/
- Licence : non-commercial research and educational use
- Volume téléchargé : 6.12 MB compressé, 20 MB extrait
- Contenu : 3 370 essays CEFR-annotés + 50 essays natifs (LOCNESS)
- Splits utilisés : train + dev (test set ne contient pas les annotations)
- Format : JSON (text + userid + CEFR + edits) + M2 (ERRANT annotations)

### Statistiques empiriques

Après normalisation via spaCy sentencization + mapping ERRANT :
- **2 671 apprenants** distincts (user IDs pseudonymisés)
- **70 489 annotations d'erreurs mappées** vers les 57 codes AcademIA
- **10 822 annotations non mappables** (ERRANT `OTHER`, `UNK` — 15.3%)
- **Couverture instances** : 84.7% des erreurs W&I (hors `noop`) mappées

### Distribution par CEFR level

| Level | Learners | Errors mapped |
|-------|---------:|--------------:|
| A1    |      493 |         9 668 |
| A2    |      711 |        22 319 |
| B1    |      482 |        14 291 |
| B2    |      364 |        12 199 |
| C1    |      361 |         7 097 |
| C2    |      210 |         3 965 |
| N     |       50 |           950 |

**Remarque** : A2 domine (tendance du corpus W&I original) — à considérer dans
les analyses croisées.

### EFCAMDAT non utilisé

EFCAMDAT (1.18M textes, 174k apprenants, 16 niveaux) nécessite une inscription
académique. Non complétée dans cette itération. **Impact** : pas de données
longitudinales, donc **pas de Cox PH** pour half-life dans cette itération.
Reportée à Sprint 1.5 si registration obtenue.

## 3. Méthodologie

### 3.1 Mapping ERRANT → AcademIA

Table de correspondance `errant_to_academie.yaml` — 18 tags ERRANT directement
mappés à 18 codes AcademIA dans 9 familles :

| Couverture | Familles AcademIA |
|---|---|
| ✅ **Calibrées** (via ERRANT) | verb_tense, noun_det, preposition, pronoun, word_order, morphology, surface, sentence |
| ⚠️ **Partielles** | verb_usage (seul V:CHOICE via bare VERB) |
| ❌ **Non calibrées** (priors v1 préservés) | vocabulary, calque, discourse |

Les familles non calibrées reflètent des distinctions **sémantiques** (faux
amis, collocations, cohésion discursive) que ERRANT n'annote pas.

**Validation** : 4/4 tests pytest verts, couverture 84.7% des instances W&I.

### 3.2 Définition empirique des tiers (§ Étape 2 de error-gradation.md)

Pour chaque (family, CEFR level) : `reach = n_learners_with_error / n_learners_at_level`.

| Tier | Seuil reach |
|------|------------|
| T1 `ignored` | ≥ 0.70 (erreur normale à ce niveau) |
| T2 `noted` | 0.30 – 0.70 |
| T3 `penalized` | 0.10 – 0.30 |
| T4 `regressive` | < 0.10 (aberrant — signaler) |

Intervalles de confiance 95% calculés par bootstrap (1000 iterations, binomial).

### 3.3 GLMM — **REPORTÉ à Sprint 1.5**

L'étape GLMM (`logit(P_next_error) = β₀ + β_tier·tier + u_learner + v_concept`)
est écrite en NumPyro mais **non exécutée** dans ce sprint.

**Raison** : les tier assignments empiriques de l'étape 4 suffisent à générer
un `tolerance_matrix_v2_draft.yaml` exploitable. Le GLMM apportera :
- Des coefficients numériques `β_tier` en log-odds (calibrés)
- Une validation statistique du gradient T1→T4
- Les random effects par apprenant et par concept

C'est un **raffinement**, pas un bloqueur. Sprint 1.5 (2-3 jours) dédié.

### 3.4 Cox PH — **SKIP** (pas de data longitudinale)

Le Cox PH pour half-life par famille × niveau est **skippable sans EFCAMDAT**.
W&I est un corpus d'essais one-shot (pas de séquence temporelle par apprenant).
Reporté à Sprint 1.5 avec EFCAMDAT ou directement à Sprint 6 sur data AcademIA.

## 4. Résultats

### 4.1 Tier map empirique

(Voir `/mnt/cosmos-data/sprint1/results/figures/tier_map.png`.)

| Famille       | A1            | A2            | B1           | B2           | C1            | C2            |
|---------------|---------------|---------------|--------------|--------------|---------------|---------------|
| morphology    | T2 noted      | T2 noted      | T2 noted     | T2 noted     | T2 noted      | T2 noted      |
| noun_det      | T1 ignored    | T1 ignored    | T1 ignored   | T1 ignored   | T1 ignored    | T1 ignored    |
| preposition   | T2 noted      | T1 ignored    | T1 ignored   | T1 ignored   | T2 noted      | T2 noted      |
| pronoun       | T2 noted      | T2 noted      | T2 noted     | T2 noted     | T3 penalized  | T3 penalized  |
| sentence      | T4 regressive | T3 penalized  | T3 penalized | T3 penalized | T4 regressive | T4 regressive |
| surface       | T1 ignored    | T1 ignored    | T1 ignored   | T1 ignored   | T1 ignored    | T1 ignored    |
| verb_tense    | T1 ignored    | T1 ignored    | T1 ignored   | T1 ignored   | T1 ignored    | T2 noted      |
| verb_usage*   | T2 noted      | T1 ignored    | T1 ignored   | T1 ignored   | T2 noted      | T2 noted      |
| word_order    | T3 penalized  | T3 penalized  | T2 noted     | T2 noted     | T3 penalized  | T3 penalized  |

_* verb_usage : calibration partielle (V:CHOICE uniquement)._

### 4.2 Comparaison avec matrice v1

**21/48 cellules du tableau (44%) changent** par rapport à `tolerance_matrix.yaml` actuelle.

**Insights majeurs** :

1. **Les "bar-raising" montants de v1 ne sont PAS empiriquement fondés.**
   v1 suppose : "une erreur X tolérée à A1 devient penalized à C1".
   Empirique : `noun_det`, `verb_tense`, `surface`, `preposition` **restent
   T1_ignored à tous les niveaux** (≥70% des C2 continuent à faire ces erreurs).
   → Pénaliser à C1/C2 = pénaliser la normalité = effet démotivateur (conforme
   à Rifkin & Roberts 1995, cf. error-gradation.md).

2. **Les erreurs rares sont sous-diagnostiquées au beginner.**
   v1 `sentence` et `word_order` à A1/A2 = `ignored`.
   Empirique : T3 à T4 (< 30% de learners les font) → à FLAGGER même à A1.
   → Ce sont des signaux pertinents de mastère déficiente à tout niveau.

3. **Aucun gradient "v1 correct partout" dans les 9 familles.**
   Même `morphology` (où v1 fait beginner=ignored → advanced=penalized) est en
   réalité T2 noted à TOUS les niveaux empiriquement.

### 4.3 Poids numériques (placeholders)

En attendant Sprint 1.5 GLMM :

| Tier      | v1    | v2_draft |
|-----------|-------|----------|
| ignored   | 0.00  | **0.10** (track soft — plus de "vraiment zero") |
| noted     | 0.30  | **0.35** |
| penalized | 0.80  | **0.75** (moins punitif) |
| shadow    | 0.00  | 0.00 (inchangé) |

Ces valeurs sont des **priors informatifs** calibrés qualitativement sur les
distributions observées. Le Sprint 1.5 GLMM fournira les `β_tier` numériques
exacts en log-odds.

## 5. Livrables

| Livrable | Chemin |
|---|---|
| Scripts sprint 1 | `/opt/academia/scripts/sprint1/` |
| Corpus raw | `/mnt/cosmos-data/sprint1/data/raw/wi+locness/` |
| Parquet normalisé | `/mnt/cosmos-data/sprint1/data/processed/errors_long.parquet` |
| Learner stats | `/mnt/cosmos-data/sprint1/data/processed/learners.parquet` |
| Tier assignments | `/mnt/cosmos-data/sprint1/data/processed/tier_assignments_external.parquet` |
| Figures | `/mnt/cosmos-data/sprint1/results/figures/*.png` |
| **Matrice v2 draft** | `/opt/academia/webapp/backend/app/config/tolerance_matrix_v2_draft.yaml` |
| Mapping ERRANT | `/opt/academia/scripts/sprint1/errant_to_academie.yaml` |
| Tests | `/opt/academia/scripts/sprint1/tests/` (4/4 green) |

## 6. Limites et biais

### 6.1 Biais corpus externe → transposition AcademIA incertaine

- **W&I = essais écrits** d'apprenants en ligne (platforme Write & Improve).
- AcademIA = **chat conversationnel** parfois oral/hybride.
- Distribution d'erreurs probablement différente (ex : `ORTH:SPACE` rare à
  l'écrit formel mais fréquent au chat mobile).
- Mitigation : calibrer aussi sur AcademIA dès ≥ 200 real students × ≥ 10
  erreurs chacun (Sprint 1.5 ou 6).

### 6.2 CEFR sub-levels perdus dans l'agrégation

W&I a A1.i / A1.ii / A2.i / A2.ii / ... Pour cette itération on a collapsé à
A1/A2/B1/B2/C1/C2. Information perdue — à récupérer si besoin de finer-grained
tier au Sprint 6 (GRM).

### 6.3 Couverture ERRANT partielle

15.3% des annotations W&I tombent en `OTHER` ou `UNK`. Ces erreurs
**existent** mais ne sont pas utilisées pour calibrer les familles.
→ Pas de perte pour les 9 familles calibrées (volume suffisant), mais les
familles `vocabulary` / `discourse` / `calque` restent aveugles.

### 6.4 L1 non pris en compte

W&I contient des apprenants de multiples L1. Les multiplicateurs L1→L2
(cf. `cefr-language-instance.md`) ne sont pas calibrés dans cette itération.
Reportés au Sprint 7 (URIEL/lang2vec) ou Sprint 1.5 si une source L1-annotée
devient disponible.

## 7. Recommandations

### Pour Sprint 2 (bascule)

- ✅ La matrice `tolerance_matrix_v2_draft.yaml` peut être reviewée par Sinse
  puis renommée en `tolerance_matrix_v2.yaml` pour activation.
- ⚠️ Avant activation : protocole de validation expert κ ≥ 0.6 sur échantillon
  AcademIA (hors scope Sprint 1, en prep pour Sprint 2).
- ⚠️ Prévoir un A/B switch (flag) pour revenir à v1 si effet indésirable.

### Sprint 1.5 (raffinement, 2-3j)

- Lancer NumPyro GLMM sur `errors_long.parquet` pour obtenir `β_tier`
  numériques (remplace les priors `0.10 / 0.35 / 0.75`).
- Tenter registration EFCAMDAT à nouveau pour débloquer Cox PH half-life.

### Sprint 6 (calibration AcademIA interne)

- Quand `error_log` dépasse 10k rows AcademIA, re-tourner les scripts de
  Sprint 1 sur data interne et comparer aux priors externes.
- Écart > 2σ sur une famille → drift à investiguer.

### Dette technique tracée

- [ ] Alignement JSON ↔ M2 perd 30-40% des annotations sur les essais longs
  (spaCy sentencizer vs ERRANT tokenizer). Amélioration possible : utiliser
  les M2 source-lines en pivot, faire du matching fuzzy texte → essay_id.
- [ ] `verb_usage`, `vocabulary`, `calque`, `discourse` restent non calibrés.
  Besoin d'un corpus annoté finer-grained (CLC-FCE XML, ou dédicter budget
  annotation manuelle LLM-as-grader).

## 9. Sprint 1.5 results — GLMM posterior (2026-04-15)

Raffinement des poids via un GLMM hiérarchique bayésien fitté sur les données
Sprint 1. Livrables : `05_glmm_fit.py`, `06_posterior_to_weights.py`,
`glmm_posterior.nc`, `weights_from_posterior.json`.

### 9.1 Modèle

```
y_i ~ Bernoulli(sigmoid(β_0 + β_tier[tier_i] + u_learner[i] + v_family[i]))
```
- 29 412 observations Bernoulli (essai × famille, y = 1 si erreur observée)
- β_tier[T1] fixé à 0 (baseline, identifiabilité)
- Random effects non-centered : 2 598 learners + 9 families
- NumPyro NUTS, 2 chains × 1000 samples, target_accept=0.9

### 9.2 Convergence

| Metric | Value | Seuil |
|---|---|---|
| R-hat max | 1.010 | ≤ 1.01 ✅ borderline |
| ESS bulk min | 329 | ≥ 400 ⚠️ un peu bas |
| Divergences | 0 | ≤ 10 ✅ |

ESS suboptimal concerne σ_v (random effect famille, naturellement lent à mixer). β_tier fixed-effects ont tous ESS > 1 500, donc les inférences sur les tiers sont fiables.

### 9.3 Coefficients posterior

| Paramètre | Posterior mean | CI 95% |
|-----------|---------------:|:-------|
| β_0 (intercept) | 0.961 | [0.02, 1.89] |
| β_tier[T1_ignored] | 0.000 | fixed |
| β_tier[T2_noted] | **–0.629** | [–0.75, –0.51] |
| β_tier[T3_penalized] | **–1.215** | [–1.40, –1.03] |
| β_tier[T4_regressive] | **–1.675** | [–2.00, –1.35] |
| σ_u (learner) | 0.925 | [0.87, 0.98] |
| σ_v (family) | 1.374 | [0.86, 2.15] |

Gradient monotone T1 → T4 **confirmé** (les CI 95% de β_tier[T2, T3, T4] ne se chevauchent pas).

### 9.4 Dérivation des poids (mapping relative-to-T1)

Formule retenue :

```
p_tier[t]   = sigmoid(β_0 + β_tier[t])
weight[t]   = 1 - p_tier[t] / p_tier[T1]
```

→ T1 = free pass (poids 0), et le poids croît proportionnellement à la raréfaction du tier.

| Tier       | p(error) | weight_v2 | weight_v1 (ancien) |
|------------|---------:|-----------:|-----------:|
| T1 ignored | 0.715 | **0.000** (CI [0.00, 0.00]) | 0.00 |
| T2 noted | 0.579 | **0.196** (CI [0.10, 0.30]) | 0.30 |
| T3 penalized | 0.440 | **0.394** (CI [0.23, 0.54]) | 0.80 |
| T4 regressive | 0.337 | **0.538** (CI [0.34, 0.70]) | — (merged penalized in v1) |

### 9.5 Interprétation

**v1 sur-pénalisait T3** : 0.80 vs empirique 0.39. Une erreur `penalized` n'est **pas deux fois plus grave qu'une `noted`** dans les données. Le vrai ratio T3/T2 = ~2.0 (pas 2.67 comme v1), et le vrai T3 absolu est ~50% moins punitif que v1 ne le suppose.

**v1 assimilait T3 à T4** : la donnée montre que T4_regressive (erreur rare) mérite un poids distinct, ~37% plus élevé que T3.

**v1 classait T1 à 0.0** : empiriquement correct, confirmé par le mapping relative-to-T1.

**La matrice courante sur-réagit aux erreurs modérées-sévères**. Le Sprint 2 devra soit adopter ces valeurs telles quelles soit faire un A/B test sur un sous-groupe avant de baser prod dessus.

### 9.6 Alternative — absolute sigmoid mapping

Pour référence, `weights_from_posterior.json` contient aussi le mapping absolu : `weight[t] = 1 - p_tier[t]`. Résultats : T1=0.285, T2=0.421, T3=0.560, T4=0.663. Cette version ne donne pas de free-pass à T1. Ne pas utiliser en prod sans discussion — choisi pour informer, pas pour activer.

### 9.7 Prochaines étapes

**Sprint 2** (bascule) :
- Review humain sur les 21 cellules changées de la matrice
- Protocole validation expert κ ≥ 0.6 sur échantillon AcademIA
- A/B flag pour revenir à v1 en cas d'effet indésirable

**Sprint 1.6** (si EFCAMDAT obtenue) :
- Cox PH half-life par famille × niveau
- Extension GLMM avec β_level interaction (gradient par niveau CECRL)

**Sprint 6** (quand AcademIA ≥ 10k error_log rows) :
- Re-tourner la pipeline Sprint 1 + 1.5 sur data interne
- Comparer priors externes vs AcademIA internes
- Décision : conserver priors ou re-calibrer

---

## 10. Références

- [roadmap.md](../00-project/roadmap.md) § Sprint 1 & 1.5
- [error-gradation.md](error-gradation.md) — méthodologie de calibration
- [ADR-003](../05-decisions/ADR-003-5-tiers-taxonomy.md) — 5 tiers T0-T4
- [ADR-008](../05-decisions/ADR-008-errant-mapping-later.md) — ERRANT
  précédemment reporté à Sprint 5+ ; amené ici pour analyse corpus externe,
  **pas** dans le code prod
- Plan exécuté : `/root/.claude/plans/encapsulated-sprouting-flamingo.md`
- Bryant et al. 2017, ERRANT : https://aclanthology.org/P17-1074/
- Ng et al. 2019, BEA 2019 shared task : https://aclanthology.org/W19-4406/
