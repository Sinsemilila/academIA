---
title: LanguageDomain — instanciation CEFR du framework taxonomie
status: authoritative
last_reviewed: 2026-04-15
---

# LanguageDomain — instanciation CEFR

> Instanciation concrète du [framework abstrait](taxonomy-framework.md) pour les langues (EN, ES, JP, DE, IT).

## Proficiency scale

**CEFR** (A1/A2/B1/B2/C1/C2). 6 niveaux pures (pas 4 bandes). Peut être étendu plus tard vers une **ability latente θ continue** (cf. [error-gradation.md](error-gradation.md) — IRT).

## Familles d'erreur (12)

Héritées et étendues de la taxonomie actuelle :

| Famille | Description | Exemples de codes |
|---|---|---|
| `verb_tense` | Temps & conjugaison | V:TENSE, V:SVA, V:FORM, V:COND, V:ASPECT, V:AUX, V:INFL |
| `verb_usage` | Usage des verbes | V:MODAL, V:PASS, V:EXIST, V:CHOICE, V:PHRASAL |
| `noun_det` | Noms & déterminants | N:COUNT, N:INFL, N:POSS, N:CHOICE, ART, ART:GENERIC, DET |
| `pronoun` | Pronoms | PRON:FORM, PRON:CHOICE, PRON:REF |
| `word_order` | Ordre des mots | WO, WO:QUEST |
| `sentence` | Structure de phrase | SENT:RUNON, SENT:FRAG, SENT:NEG, SENT:MOD, SENT:PARALLEL, SENT:SUBORD |
| `morphology` | Morphologie | MORPH:DERIV, MORPH:WORDCLASS, ADJ:CHOICE, ADJ:FORM, ADJ:ORDER, ADV:CHOICE |
| `surface` | Orthographe/ponctuation | SPELL, SPELL:COGNATE, ORTH:CASE, ORTH:SPACE, PUNCT, PUNCT:COMMA, PUNCT:APOST, CONTR, REDUND |
| `preposition` | Prépositions | PREP |
| `vocabulary` | Vocabulaire | LEX:CHOICE, LEX:COLLOC, LEX:FALSE, LEX:IDIOM, LEX:ARGSTRUCT |
| `calque` | Calques L1 | LEX:CALQUE, PREP:CALQUE |
| `discourse` | Discours & registre | DISC:TRANS, DISC:COHER, REG:LEVEL, REG:PRAGMA |

Total : 57 codes. À **étendre/remapper par langue** : toutes les familles existent pour EN/ES/DE/IT/FR. Pour le japonais, ajouter des familles spécifiques : `particles` (は/が/を/に/で), `keigo` (politesse), `kanji_reading`, `classifiers`.

## Criterial levels

Chaque famille (et plus finement chaque concept) a deux niveaux :
- **emergence_level** : niveau où la structure est typiquement produite par ≥ 30% des apprenants
- **mastery_level** : niveau où elle est produite correctement par ≥ 80%

Sources par langue :
- **EN** : [English Grammar Profile (EGP)](https://englishprofile.org/english-grammar/) — 1222 criterial features
- **ES** : [Plan Curricular del Instituto Cervantes](https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/indice.htm)
- **DE** : Profile Deutsch (Glaboniat et al. 2005)
- **IT** : Sillabo CILS (Università per Stranieri di Siena)
- **JP** : JF Standard (Japan Foundation)

Format de stockage : YAML par langue dans `academie-core/data/cefr_criterial_features/<lang>.yaml`.

## Tolerance matrix — 6 bandes pures

Remplace la matrice actuelle à 4 bandes par **6 bandes pures** (A1/A2/B1/B2/C1/C2) :

Exemple famille `verb_tense` (valeurs à calibrer empiriquement, cf. [error-gradation.md](error-gradation.md)) :

| Famille | A1 | A2 | B1 | B2 | C1 | C2 |
|---|---|---|---|---|---|---|
| verb_tense | T1 | T2 | T2 | T3 | T3 | T4 si slip |
| verb_usage | T1 | T1 | T2 | T3 | T3 | T3 |
| noun_det | T1 | T2 | T2 | T3 | T3 | T3 |
| surface | T0 | T1 | T1 | T2 | T3 | T3 |
| discourse | T0 | T0 | T1 | T2 | T3 | T3 |
| calque | T2 | T2 | T3 | T3 | T3 | T3 |
| ... | ... | ... | ... | ... | ... | ... |

**Règle** : T0 obligatoire quand la structure est avant le niveau d'émergence ; T4 déclenchée quand l'erreur est sur une structure dont le mastery_level est ≥ 2 niveaux avant le niveau courant de l'apprenant.

## Gravity axes par famille

Chaque famille a 3 scores (0-1), **valeurs prior** à calibrer :

```yaml
verb_tense:
  linguistic: 0.85       # violation claire
  communicative: 0.50    # peut impacter le sens (passé vs présent)
  social_pragmatic: 0.10

noun_det:                 # articles a/the, pluriels
  linguistic: 0.60
  communicative: 0.20    # rarement global
  social_pragmatic: 0.30 # audible par natif

surface:                  # spelling, punct
  linguistic: 0.80
  communicative: 0.05    # jamais global
  social_pragmatic: 0.15 # perçu comme négligent à haut niveau

discourse:                # registre, cohérence
  linguistic: 0.20       # pas vraiment une "règle"
  communicative: 0.60
  social_pragmatic: 0.90 # cible directe de jugement social
```

**Le tier final** est calculé par une fonction qui combine ces axes avec le CEFR level, puis saturée via calibration empirique (cf. ADR-002 fonction `f`).

## L1 transfer multipliers

Table séparée `l1_transfer_multipliers.yaml` :

```yaml
# Francophone vers anglais
fr_to_en:
  calque:              1.8  # beaucoup plus d'erreurs
  preposition:         1.4  # "depend of" → "on"
  noun_det:            1.3  # "the France" / "the music" en généralité
  word_order:          0.9  # similarité de structure → moins d'erreurs

# Japonais vers anglais
ja_to_en:
  noun_det:            2.0  # absence d'articles en JP → énormes difficultés
  verb_tense:          1.5  # moins de temps en JP
  word_order:          1.6  # SOV vs SVO
  discourse:           1.3  # registre très différent

# Anglais vers espagnol (reverse)
en_to_es:
  verb_tense:          1.5  # subjonctif espagnol absent en EN
  morphology:          1.4  # gender agreement
  preposition:         1.2
```

**Source** : URIEL / lang2vec typological distances + calibration empirique sur corpus (EFCAMDAT a la L1 par apprenant).

Sans data réelle, on démarre avec des **priors dérivés de typologie** (WALS via lang2vec), raffinés au fur et à mesure.

## Règles universelles appliquées

Les invariants du [framework](taxonomy-framework.md) se matérialisent ainsi pour les langues :

1. **Pré-acquisition → T0** : toute famille × niveau où `emergence_level > learner.level` = T0, zéro flag (Pienemann)
2. **Global > local** : `communicative > 0.5` → tier minimum T2 même en A1 (Burt-Kiparsky)
3. **Protection motivation** : plafonner le nombre de corrections affichées par tour (cf. [feedback-delivery.md](feedback-delivery.md))
4. **Mistake vs error** : tracker `n_recent_correct_uses` par concept × apprenant, ajuster tier en conséquence

## U-shape protection

Détection automatique des **régressions sur structures productives** (passé irrégulier, pluriels, accords gender) :

```
if learner.had_correct(concept, N-1_level) and learner.now_wrong(concept, current_level):
    tier = downgrade_by_one(tier)       # T3 → T2, etc.
    mark_observation_window(concept, 2_to_4_weeks)
```

Justification : la régression est un **signe de progrès pédagogique** (surgénéralisation de règle), pas un symptôme à pénaliser.

## Extension aux autres langues

Pour ajouter Maestro (ES) :

1. Remplir `cefr_criterial_features/es.yaml` depuis PCIC
2. Adapter `tolerance_matrix[es].yaml` si particularités espagnoles (ex. subjonctif plus central que EN)
3. Ajouter paires L1→ES dans `l1_transfer_multipliers.yaml` : `fr_to_es`, `en_to_es`, etc.
4. Instancier `LanguageDomain(lang="es")` dans webapp
5. Data de calibration : importer CEDEL2 (open) pour peupler les seuils

Coût marginal par langue supplémentaire : **data + config**, pas de code.

## Références

- [taxonomy-framework.md](taxonomy-framework.md) — framework abstrait
- [error-gradation.md](error-gradation.md) — calibration empirique
- [feedback-delivery.md](feedback-delivery.md) — types de feedback
- [bibliography.md](bibliography.md) — sources scientifiques
- Code actuel : `webapp/backend/app/config/tolerance_matrix.yaml` (à refondre)
- Code futur : `academie-core/domain/language.py`, `academie-core/data/cefr_criterial_features/*.yaml`
