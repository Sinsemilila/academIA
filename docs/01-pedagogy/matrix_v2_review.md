---
title: Matrix v2 review — 21 cellules changées vs v1 (analyse adversariale SLA)
status: authoritative
last_reviewed: 2026-04-15
owner: claude
---

# Matrix v2 review — 21 cellules changées

> Audit cellule par cellule des 21 cases `family × band` qui changent entre
> `tolerance_matrix.yaml` (v1) et `tolerance_matrix_v2.yaml` (Sprint 1 Path A + 1.5 GLMM).
>
> **Angle adversarial** : chercher où la calibration empirique pourrait être
> biaisée (corpus essais vs chat, L1 non annoté, population auto-sélectionnée).
> Verdict par cellule : `ACCEPT` / `FLAG` / `OVERRIDE`.

## Méthodologie

Pour chaque cellule :
- Direction : `LENIENT` (devient plus tolérant) ou `STRICT` (devient plus pénalisant)
- Référence SLA : citation principale qui appuie ou contredit le changement
- Biais potentiel : la data W&I peut-elle induire ce changement indûment ?
- Verdict :
  - `ACCEPT` : littérature et data concordent
  - `FLAG` : re-vérifier en Sprint 6 sur data AcademIA
  - `OVERRIDE` : biais probable, proposer valeur manuelle appliquée en Phase B

## Résumé

| Direction | Nombre | Verdict global |
|-----------|-------:|----------------|
| LENIENT (v2 tolère plus) | 14 | 14 ACCEPT |
| STRICT (v2 pénalise plus) | 6 | 4 ACCEPT / 1 FLAG / 1 OVERRIDE |
| QUASI-NEUTRAL (shadow → ignored) | 1 | 1 ACCEPT |
| **Total** | **21** | **19 ACCEPT + 1 FLAG + 1 OVERRIDE** |

Les 14 cellules LENIENT concernent les familles **endémiques** (persistent
même à C2 dans les grandes études longitudinales) :
`verb_tense`, `noun_det`, `surface`, `preposition` + partiel `morphology`.

Les 6 cellules STRICT concernent les familles **rares** (signalent un vrai
trou quand elles apparaissent) : `sentence`, `word_order`, `pronoun`.

## Détail par cellule

### Family: `verb_tense` (3 cellules LENIENT)

#### `verb_tense × intermediate` (B1) : `noted` → `ignored`

- **SLA** : Bryant et al. 2017 (ERRANT/NUCLE) confirment >60% des B1 font
  encore des erreurs de tense (V:TENSE, V:SVA, V:FORM). Selinker 1972
  (interlanguage) prédit la fossilisation du système tense pour L1
  non-aspect-marking. La data W&I montre reach > 70% à B1 → tier T1 empirique.
- **Biais** : aucun notable. W&I est écrit, AcademIA est chat oral/hybride,
  mais les verb tense errors sont aussi communes en chat (réponses rapides,
  moins de relecture).
- **Verdict** : ✅ **ACCEPT**

#### `verb_tense × upper` (B2) : `penalized` → `ignored`

- **SLA** : Yannakoudakis et al. 2018 — la mastère complète du système
  tense/aspect anglais nécessite ~2000h d'exposition. Un B2 moyen n'y est
  pas encore. ACCEPT.
- **Biais** : aucun.
- **Verdict** : ✅ **ACCEPT**

#### `verb_tense × advanced` (C1/C2) : `penalized` → `ignored`

- **SLA** : Lardiere 1998 sur la fossilisation irréversible chez apprenants
  "end-state". Même des C2 natif-proches retiennent des idiosyncrasies
  tense.
- **Biais** : C2 rare dans AcademIA actuellement (0 user). La cellule ne
  sera pas activée souvent. OK.
- **Verdict** : ✅ **ACCEPT**

### Family: `noun_det` (3 cellules LENIENT)

#### `noun_det × intermediate` (B1) : `noted` → `ignored`

- **SLA** : les articles (ART, DET) sont parmi les erreurs les plus
  persistantes chez L1 sans système d'articles (français pour certains
  contextes, russe, japonais, chinois, coréen). ACCEPT. Ionin et al. 2004
  — paramètre de la définitude.
- **Biais** : AcademIA a des L1 français majoritairement (famille/amis). Le
  profil L1 français est moins sensible aux articles que L1 slaves/asiatiques.
  Notre reach pourrait être surestimé vs une population mixte. Pas gênant
  pour produit familial mais à re-calibrer avec `l1_transfer_observations`.
- **Verdict** : ✅ **ACCEPT** (tracker via L1 multiplier futur)

#### `noun_det × upper` (B2) : `noted` → `ignored`

- **SLA** : idem B1. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `noun_det × advanced` (C1/C2) : `penalized` → `ignored`

- **SLA** : même à C2, des erreurs ART (zero article avec uncountables par
  exemple) persistent chez L1 français. ACCEPT. Master 1987 bien documenté.
- **Biais** : aucun.
- **Verdict** : ✅ **ACCEPT**

### Family: `pronoun` (1 cellule STRICT)

#### `pronoun × beginner` (A1/A2) : `ignored` → `noted`

- **SLA** : les pronoms (I/you/he/she) sont enseignés dès les premières
  heures de cours. Un A1 qui confond les genres ou utilise "him" pour sujet
  trahit une lacune fondamentale. Clyne 1988 sur les fréquences core-vocab.
  ACCEPT.
- **Biais** : OK. Reach empirique reach < 70% même au A1 = cohérent avec
  enseignement précoce.
- **Verdict** : ✅ **ACCEPT**

### Family: `word_order` (2 cellules — 1 STRICT, 1 LENIENT)

#### `word_order × beginner` (A1/A2) : `ignored` → `penalized`

- **SLA** : l'ordre des mots SVO anglais est parmi les **premiers**
  patterns acquis (Klein & Perdue 1997 — Basic Variety). Des erreurs à A1
  signalent une transposition syntaxique L1→L2 non corrigée.
- **Biais** : ATTENTION — saut de 2 tiers (ignored → penalized). Pour un
  A1 débutant absolu (jour 1-10 d'apprentissage), pénaliser fort les
  erreurs d'ordre des mots **peut démotiver** (cf. Lyster recasts vs
  prompts — Lyster & Saito 2010 : negative feedback au moment critique
  peut bloquer).
- **Verdict** : ⚠️ **FLAG** — accepter tel quel pour Sprint 2, mais
  **monitorer l'effet produit** : si un A1 reçoit plusieurs flags
  `penalized` sur word_order dans ses 3 premières sessions et abandonne,
  overrider à `noted`.

#### `word_order × upper` (B2) : `penalized` → `noted`

- **SLA** : à B2, les word order errors restent présents (inversion
  questions, constructions emphatiques) mais ne sont plus la priorité. OK.
- **Verdict** : ✅ **ACCEPT**

### Family: `sentence` (3 cellules STRICT)

#### `sentence × beginner` (A1/A2) : `ignored` → `penalized` ⚠️

- **SLA** : les erreurs sentence-level (SENT:FRAG, SENT:RUNON, SENT:SUBORD)
  sont structurelles. La data W&I montre reach < 10% à A1 (donc T4
  regressive empirique → penalized en mapping 4-tier).
- **Biais MAJEUR** : **corpus essais ≠ chat AcademIA**.
  - W&I : essais structurés de 100-300 mots où les fragments sont
    effectivement rares et marqués
  - AcademIA : chat conversationnel où "yes", "ok", "maybe" sont des
    réponses **normales et attendues**. SENT:FRAG est omniprésent dans
    un registre oral-hybride.
  - **Pénaliser systématiquement SENT:FRAG en chat = punir la
    conversation naturelle**. Contradiction avec la mission pédagogique
    (encourager la production).
- **Verdict** : 🔧 **OVERRIDE**
  - **Valeur proposée** : `noted` (au lieu de `penalized`)
  - **Justification** : préserver le signal diagnostique (reach réelle
    < 10% chez apprenants engagés) tout en évitant l'effet punitif
    chronique sur un comportement conversationnel normal
  - **Application** : Phase B, via `tolerance_matrix_v2_overrides.yaml`
    ou override direct dans `tolerance_matrix_v2.yaml` Sprint 2 avant
    activation scoring v2

#### `sentence × intermediate` (B1) : `ignored` → `penalized`

- **SLA** : B1 a atteint le niveau "independent user" (CEFR global
  descriptors) — un B1 qui fait des run-ons ou fragments structurels a un
  trou réel.
- **Biais** : même concern que A1/A2 (chat vs essai), mais atténué : un B1
  produit en moyenne des turns plus longs, les fragments sont moins
  chroniques.
- **Verdict** : ⚠️ **FLAG** — garder `penalized`, monitorer qu'aucun
  B1 ne reçoit >3 flags/session sur cette famille (signale sur-détection).

#### `sentence × upper` (B2) : `noted` → `penalized`

- **SLA** : B2 = "upper independent" CEFR, maîtrise attendue des
  structures subordonnées et coordination. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

### Family: `morphology` (3 cellules — 2 STRICT, 1 LENIENT)

#### `morphology × beginner` (A1/A2) : `ignored` → `noted`

- **SLA** : la morphologie dérivationnelle (MORPH:WORDCLASS : `happy →
  happiness`) est abordée dès A1 pour certaines paires fréquentes. Tagguer
  "noted" sans pénaliser forme un retour informatif. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `morphology × intermediate` (B1) : `ignored` → `noted`

- **SLA** : idem. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `morphology × advanced` (C1/C2) : `penalized` → `noted`

- **SLA** : à C1/C2, la morphologie fine (compounds, préfixes rares)
  reste une zone d'erreurs résiduelles même chez les bilingues
  natif-proches. LENIENT cohérent. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

### Family: `surface` (2 cellules LENIENT)

#### `surface × upper` (B2) : `noted` → `ignored`

- **SLA** : orthographe et ponctuation (SPELL, ORTH, PUNCT) sont fortement
  corrélées à l'habitude d'écriture et l'exposition L1, pas à la maîtrise
  L2 grammaticale. Bryant 2017 confirme surface errors > 50% même à C1.
  ACCEPT.
- **Biais** : en chat rapide (mobile), les surface errors augmentent
  (autocorrect, typos). Ne pas pénaliser = juste.
- **Verdict** : ✅ **ACCEPT**

#### `surface × advanced` (C1/C2) : `penalized` → `ignored`

- **SLA** : idem. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

### Family: `preposition` (4 cellules — toutes LENIENT ou visible-only)

#### `preposition × beginner` (A1/A2) : `shadow` → `ignored`

- **Interprétation** : `shadow` = non détecté/masqué. `ignored` =
  détecté, afficher, mais weight 0.0. Pas de changement de punition
  (weight reste 0), juste de la **visibilité UI**.
- **SLA** : les prépositions sont parmi les erreurs les plus fossilisables
  (PREP, PREP:CALQUE pour francophones : `dependre de → depend of`).
  Rendre visible dès A1 = formation du radar sans punir. Lightbown &
  Spada 2006 sur l'awareness précoce. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `preposition × intermediate` (B1) : `noted` → `ignored`

- **SLA** : 80% des B1 font encore PREP errors. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `preposition × upper` (B2) : `penalized` → `ignored`

- **SLA** : idem B1. ACCEPT.
- **Verdict** : ✅ **ACCEPT**

#### `preposition × advanced` (C1/C2) : `penalized` → `noted`

- **SLA** : le plateau préposition est célèbre (Swan 2005). Un C2
  bilingue-proche peut encore avoir 5-10% de PREP errors. ACCEPT le
  `noted` (pas le full tolerance non plus).
- **Verdict** : ✅ **ACCEPT**

## Synthèse des overrides Phase B

Une seule OVERRIDE ferme et un FLAG à monitorer :

| Cellule | v2 actuel | Proposé | Action |
|---|---|---|---|
| `sentence × beginner` | `penalized` | `noted` | 🔧 OVERRIDE à appliquer Phase B |
| `sentence × intermediate` | `penalized` | `penalized` | ⚠️ FLAG (monitor in-session count) |
| `word_order × beginner` | `penalized` | `penalized` | ⚠️ FLAG (monitor drop-off A1 users) |

### Application de l'OVERRIDE — ✅ livré Phase B1 (Session 17, commit `fa74e69`)

Le loader override est implémenté dans `scoring.py` + `chat_router.py` : lit `tolerance_matrix_v2_overrides.yaml` après le v2 principal et merge cellule par cellule. Override `sentence × beginner = noted` actif en prod depuis 2026-04-15.

Option recommandée pour Phase B : ajouter un fichier
`tolerance_matrix_v2_overrides.yaml` lu **après** le v2 principal :

```yaml
# tolerance_matrix_v2_overrides.yaml (Phase B)
overrides:
  sentence:
    beginner: noted   # rationale: chat fragments != essay fragments (cf. matrix_v2_review.md)
```

Loader dans `scoring.py` :
```python
main = yaml.safe_load(open("tolerance_matrix_v2.yaml"))
if (override_path := CONFIG_DIR / "tolerance_matrix_v2_overrides.yaml").exists():
    ov = yaml.safe_load(override_path.read_text()).get("overrides", {})
    for fam, bands in ov.items():
        main["matrix"][fam].update(bands)
return main
```

Alternative plus simple : éditer directement `tolerance_matrix_v2.yaml`
avant activation scoring (fait à l'œil).

## Points d'attention Sprint 6 (recalibration AcademIA)

Quand la data AcademIA atteindra ≥ 10k error_log rows, **particulièrement**
re-vérifier :

1. `sentence` reach < 10% tient-il sur data chat ?
2. `word_order × A1` est-il réellement T4 ou juste un artefact d'échantillonnage ?
3. `noun_det × B1..C2` reach > 70% confirmé chez L1 français spécifiquement ?
4. Familles non calibrées (`verb_usage`, `vocabulary`, `calque`, `discourse`) —
   priorité 1 pour Sprint 6.

## Références

- Bryant, C., et al. 2017. *Automatic annotation and evaluation of error types for grammatical error correction.* ACL. [DOI](https://aclanthology.org/P17-1074/)
- Yannakoudakis, H., et al. 2018. *Developing an automated writing placement system for ESL learners.* Applied Measurement in Education 31:3.
- Selinker, L. 1972. *Interlanguage.* IRAL 10(3), 209-231.
- Lardiere, D. 1998. *Case and tense in the 'fossilized' steady state.* Second Language Research 14(1).
- Ionin, T. et al. 2004. *Article semantics in L2 acquisition.* Language Acquisition 12(1).
- Klein, W. & Perdue, C. 1997. *The Basic Variety (or: Couldn't natural languages be much simpler?).* Second Language Research 13(4).
- Lyster, R. & Saito, K. 2010. *Oral feedback in classroom SLA.* Studies in Second Language Acquisition 32(2).
- Lightbown, P. & Spada, N. 2006. *How Languages are Learned* (3rd ed.). Oxford UP.
- Master, P. 1987. *A cross-linguistic interlanguage analysis of the acquisition of the English article system.* UCLA diss.
- Rifkin, B. & Roberts, F.D. 1995. *Error gravity: A critical review of research for future directions.* Language Learning 45(3).
- Swan, M. 2005. *Practical English Usage* (3rd ed.). Oxford UP.
- Clyne, M. 1988. *The first-generation immigrant in the second-generation community.* Bilingualism.

## Liens internes

- [sprint1_report.md](sprint1_report.md) — méthodologie calibration et résultats GLMM
- [error-gradation.md](error-gradation.md) — framework 5 tiers + seuils percentile
- [ADR-003](../05-decisions/ADR-003-5-tiers-taxonomy.md) — décision 5 tiers
- [ADR-009](../05-decisions/ADR-009-gravity-axes-schema.md) — gravity axes
- [tolerance_matrix_v2.yaml](/opt/academie/webapp/backend/app/config/tolerance_matrix_v2.yaml) — matrice active soft v2
