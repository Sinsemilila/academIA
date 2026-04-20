# Vague 2 — Design détaillé QCM pre-chat onboarding

**Date** : 2026-04-20
**Auteur** : Claude (design doc pour Sinse)
**Statut** : SPEC — prêt pour implémentation
**Scope** : remplacer l'onboarding conversationnel LLM (bugué) par un QCM modal bloquant pre-chat, 1re visite par langue.
**Decisions figées** : D1-D7 (cf. note Sinse 2026-04-20)

---

## 1. Executive summary

### 1.1 Problème

L'onboarding actuel d'AcademIA repose sur une phase conversationnelle LLM (Teacher EN / Maestro ES) censée extraire le niveau, les objectifs et la motivation de l'apprenant via dialogue libre. Observations terrain :

- **Extraction non-déterministe** : le LLM oublie de demander certaines variables, en invente d'autres, produit des `profils_eleves` partiels ou incohérents.
- **Onboarding qui traîne** : 8-15 tours de conversation avant la 1re activité réelle → drop-off mesuré ~40 % avant la 1re leçon.
- **Impossible à QA** : chaque run produit un profil différent → pas de baseline pour évaluer la personnalisation downstream.
- **Bugs Dify récurrents** : variables qui ne se câblent pas (`{{#start.X#}}` vs `{{#code_turn_check.X#}}`), Maestro qui régresse après chaque patch Teacher.

### 1.2 Décision (retenue Option C)

On remplace l'onboarding conversationnel par un **QCM modal bloquant** de 8-10 items, structuré en 3 blocs réutilisables (universal core / domain level / domain motivation), rendu côté front avant le 1er chat. Le profil extrait est persisté en DB (`learner_profiles`) et injecté au LLM via double canal (JSON structuré + résumé NL) dans le prompt système au 1er tour.

### 1.3 Gains attendus

| Métrique | Avant (conversationnel) | Après (QCM) | Source |
|---|---|---|---|
| Temps onboarding médian | 8-12 min | 90 s - 3 min | Estimation items Likert/can-do |
| Variables ID extraites | 2-3 sur 8 | 8 sur 8 (100 %) | Déterministe par construction |
| Taux d'abandon onboarding | ~40 % | <15 % (cible) | Benchmark Duolingo placement |
| Reproductibilité profil | ~0 % | 100 % | QCM = contrat |
| Coût LLM onboarding | ~8k tokens/user | 0 tokens | Plus d'appel LLM en phase ID |

### 1.4 Architecture 3 blocs (rappel D4 Option C hybride)

```
Bloc A — UNIVERSAL CORE (5 items, tous domaines futurs : langues, pymentor, math, …)
  A1 · Self-efficacy          (Bandura 1997)
  A2 · Mindset                (Dweck 2006, Lou & Noels 2019)
  A3 · Goal specificity       (Locke & Latham 2002)
  A4 · Autonomy orientation   (Dörnyei 2005 ; Deci & Ryan 2000)
  A5 · Engagement frequency   (auto-reported practice rhythm)

Bloc B — DOMAIN LEVEL (2 items pour langues, + mini-probe conditionnel)
  B1 · CEFR can-do comprehension     (CECRL self-assessment grid)
  B2 · CEFR can-do production        (idem, bi-skill split)
  B*  · Mini-probe discriminant       (si self ≥ B1 → anti-Dunning-Kruger)

Bloc C — DOMAIN MOTIVATION (2 items pour langues)
  C1 · Ideal L2 Self                 (Dörnyei 2005, Taguchi et al. 2009)
  C2 · FLA (Foreign Language Anxiety) — 3 sub-items Likert compressés (Teimouri 2019, forme courte MacIntyre-Gardner 1994)
```

Total rendu : **8 écrans + 1 conditionnel + intro + résumé = 10-11 screens**, 90 s-3 min.

### 1.5 Livrables couverts

1. ✅ Formulations FR exactes des 8 questions (+ mini-probe)
2. ✅ YAMLs `core.yaml`, `domains/language.yaml`, `overlays/en.yaml`, `overlays/es.yaml`
3. ✅ Format d'injection LLM double canal (JSON + NL 200 mots)
4. ✅ Schéma DB `learner_profiles` + DDL + migration
5. ✅ Endpoints REST FastAPI (GET / POST / PATCH) + Pydantic
6. ✅ Branching mini-probe CEFR conditionnel
7. ✅ UX flow step-by-step + gestion back/refresh
8. ✅ Tradeoffs A/B/C

---

## 2. Architecture 3 blocs

### 2.1 Principe

Séparer ce qui est **universel** (traits apprenant valables pour tout domaine d'apprentissage) de ce qui est **spécifique au domaine** (niveau initial, motivation propre au champ). Permet de réutiliser Bloc A tel quel quand on ouvre PyMentor, Maths, Droit, etc. Seuls Blocs B et C changent par domaine.

### 2.2 Diagramme de flux

```
         ┌──────────────────────┐
         │ User clique langue X │
         └──────────┬───────────┘
                    ▼
       ┌─────────────────────────────┐
       │ GET /api/learner-profile/X  │
       └──────────┬──────────────────┘
                  │
        ┌─────────┴──────────┐
     404│                    │200
        ▼                    ▼
  ┌─────────────┐      ┌──────────────┐
  │ QCM modal   │      │ Chat normal  │
  │ bloquant    │      │ (profil déjà │
  └──────┬──────┘      │  injecté)    │
         ▼             └──────────────┘
  ┌────────────────────────────────────┐
  │ Bloc A (5 Q) · Bloc B (2 Q + probe)│
  │ Bloc C (2 Q dont FLA)              │
  └──────┬─────────────────────────────┘
         ▼
  ┌────────────────────────────────┐
  │ POST /api/learner-profile/X    │
  │   → valide schema Pydantic     │
  │   → persiste learner_profiles  │
  │   → renvoie profile_id         │
  └──────┬─────────────────────────┘
         ▼
  ┌────────────────────────────────┐
  │ Résumé "voici ton profil"      │
  │ + CTA "Commencer"              │
  └──────┬─────────────────────────┘
         ▼
  ┌────────────────────────────────┐
  │ Chat Dify (1er tour)           │
  │   system_prompt injecte :      │
  │     - JSON profile             │
  │     - NL summary 200 mots      │
  └────────────────────────────────┘
```

### 2.3 Réutilisabilité cross-domain

| Bloc | Langues v1 | PyMentor v2 | Maths v3 | Statut v1 |
|---|---|---|---|---|
| A — core (5 Q) | Identique | Identique | Identique | Implémenté |
| B — level | CEFR can-do bi-skill | Python self-rating + probe algo | Pré-test diagnostic | Langues seul |
| C — motivation | Ideal L2 Self + FLA | Ideal programmer self + anxiété code | Math anxiety (Hembree) | Langues seul |

Structure YAML prête (`domains/pymentor.yaml`, `domains/maths.yaml` placeholders vides).

---

## 3. Les 8 questions détaillées

Chaque question inclut : **ID stable**, **énoncé FR**, **format**, **options/échelle**, **source scientifique**, **variable DB**, **règle de scoring**.

---

### 3.1 Bloc A — Universal Core

---

#### A1. `core_self_efficacy_1`

- **Énoncé FR** : « Quand je me fixe un objectif d'apprentissage, je suis généralement capable de l'atteindre, même si ça demande des efforts. »
- **Format** : Likert 5 points (ancrage verbal)
- **Options** :
  1. Pas du tout d'accord
  2. Plutôt pas d'accord
  3. Ni d'accord ni pas d'accord
  4. Plutôt d'accord
  5. Tout à fait d'accord
- **Source** : Bandura (1997), *Self-Efficacy: The Exercise of Control*. Adaptation item générique de la General Self-Efficacy Scale (Schwarzer & Jerusalem 1995), version courte.
- **Rationale** : la self-efficacy prédit la persistance face à l'effort et le choix d'objectifs ambitieux. Score faible → tuteur doit scaffolder plus, proposer micro-wins fréquents.
- **Variable DB** : `self_efficacy` (INT 1-5)
- **Scoring** : valeur brute 1-5. Catégories dérivées :
  - 1-2 → `low` (scaffold +, micro-steps, validation fréquente)
  - 3 → `medium` (neutre)
  - 4-5 → `high` (challenge +, autonomie +)

---

#### A2. `core_mindset_1`

- **Énoncé FR** : « Selon toi, la capacité à apprendre une nouvelle compétence, c'est plutôt… »
- **Format** : choix unique 2 options (forced-choice, réduit désirabilité sociale)
- **Options** :
  - A. Un talent qu'on a ou qu'on n'a pas, et qui change peu avec la pratique.
  - B. Une aptitude qui se développe avec l'effort et les bonnes méthodes.
- **Source** : Dweck (2006) *Mindset* ; Lou & Noels (2019) *Language Mindsets*. Adaptation forced-choice inspirée du Implicit Theories of Intelligence Scale, version bi-polaire courte.
- **Rationale** : mindset fixe → l'apprenant abandonne plus vite sur échec, interprète la difficulté comme « je ne suis pas doué ». Growth mindset → recadrage erreur = info. Détermine la framing du feedback LLM.
- **Variable DB** : `mindset` (ENUM `fixed` | `growth`)
- **Scoring** : A → `fixed`, B → `growth`.

---

#### A3. `core_goal_specificity_1`

- **Énoncé FR** : « Pourquoi veux-tu progresser dans cette langue ? Décris en une phrase concrète (ex : *comprendre les séries en VO sans sous-titres* ou *parler avec ma belle-famille espagnole*). »
- **Format** : textarea libre, max 200 caractères, min 10 caractères
- **Options** : N/A (texte libre)
- **Source** : Locke & Latham (2002) *Goal-Setting Theory* — "specific, difficult goals lead to higher performance than vague or easy goals". Adaptation : capturer la spécificité auto-rapportée avant calibration.
- **Rationale** : un goal spécifique (« VO sans ST ») calibre le niveau CEFR cible, le lexique prioritaire et le registre (familier vs pro). Goal vague (« progresser ») → tuteur doit proposer 3 scénarios génériques.
- **Variable DB** : `goal_text` (TEXT) + `goal_specificity_score` (INT 0-3, dérivé par règle NLP simple côté backend au POST)
- **Scoring (dérivation `goal_specificity_score`)** :
  - 0 : <10 chars ou mots vagues uniquement (« progresser », « améliorer », « apprendre »)
  - 1 : générique mais avec contexte d'usage (« parler avec des amis », « voyager »)
  - 2 : concret avec contexte + entité (« comprendre les séries Netflix en VO », « échanger avec collègues espagnols »)
  - 3 : concret + contexte + échéance ou jalon (« passer le C1 en juin », « présenter un projet au boulot en mars »)
- **Règle de dérivation (v1, heuristique)** :
  ```
  if len(text) < 10 or matches(vague_verbs_only): 0
  elif matches(has_context_verb_nominal): 1
  elif matches(has_named_entity_or_domain): 2
  elif matches(has_temporal_marker): 3
  ```
  Liste `vague_verbs_only` = `{progresser, améliorer, apprendre, maîtriser, parler mieux}` sans complément.
  Liste `temporal_marker` = `{avant, en <mois>, d'ici, pour <date>, en <N> mois}`.

---

#### A4. `core_autonomy_1`

- **Énoncé FR** : « Quand tu apprends quelque chose de nouveau, tu préfères… »
- **Format** : choix unique 3 options (catégoriel, pas d'ordinal)
- **Options** :
  - A. Qu'on me donne un plan précis étape par étape.
  - B. Qu'on me propose un cadre, mais que je choisisse le rythme et les sujets.
  - C. Que je définisse moi-même mes objectifs et que le tuteur s'adapte.
- **Source** : Dörnyei (2005) *The Psychology of the Language Learner* + Deci & Ryan (2000) *Self-Determination Theory* — continuum contrôlé → autonome. Adaptation 3-niveaux discrète (plutôt que Likert) pour décision franche.
- **Rationale** : détermine le **style d'intervention du tuteur** — A : prescriptif (prochaine leçon imposée), B : proposer 2-3 options, C : demander à l'user ce qu'il veut travailler aujourd'hui. Sans cette info, le tuteur oscille et frustre tout le monde.
- **Variable DB** : `autonomy_pref` (ENUM `guided` | `semi_autonomous` | `autonomous`)
- **Scoring** : A → `guided`, B → `semi_autonomous`, C → `autonomous`.

---

#### A5. `core_engagement_1`

- **Énoncé FR** : « Tu comptes t'entraîner à quelle fréquence ? »
- **Format** : choix unique 4 options
- **Options** :
  - A. Quelques minutes par jour (5-15 min)
  - B. Une session plus longue 2-3 fois par semaine (30-45 min)
  - C. Plutôt 1-2 fois par semaine, quand j'ai le temps
  - D. Très intensif, tous les jours 30+ min
- **Source** : pas un construct psychométrique formel ; dérivé de la littérature spaced-repetition (Ebbinghaus, Cepeda et al. 2006) + auto-rapport d'intention qui prédit modérément le comportement (Ajzen, TPB). Sert de **signal de calibrage de la taille des sessions**, pas de prédicteur fort.
- **Rationale** : oriente la longueur proposée par le tuteur (micro-leçon 5 min vs session 30 min), la fréquence des relances de révision, et le framing des objectifs (daily streak vs weekly goal).
- **Variable DB** : `engagement_pattern` (ENUM `daily_short` | `weekly_long` | `opportunistic` | `daily_intense`)
- **Scoring** : A → `daily_short`, B → `weekly_long`, C → `opportunistic`, D → `daily_intense`.

---

### 3.2 Bloc B — Domain Level (langues)

---

#### B1. `lang_cando_comprehension_1`

- **Énoncé FR** : « En [LANGUE_CIBLE], à l'écrit comme à l'oral, je peux… (choisis la description qui te correspond le mieux actuellement) »
- **Format** : radio image+texte, 6 options exclusives (1 carte par niveau CEFR)
- **Options** (reformulées FR depuis la grille CECRL self-assessment) :
  - **A1** : « Je comprends des mots familiers et des expressions très simples quand on me parle lentement et clairement. »
  - **A2** : « Je comprends des phrases et un vocabulaire très fréquent (infos personnelles, achats, travail). Je saisis l'essentiel d'annonces simples. »
  - **B1** : « Je comprends les points essentiels quand un langage clair et standard est utilisé, sur des sujets familiers (travail, école, loisirs). »
  - **B2** : « Je comprends des émissions TV et films en langue standard, et l'essentiel de textes complexes sur des sujets concrets ou abstraits. »
  - **C1** : « Je comprends un discours long même non clairement structuré, et des textes longs et exigeants. Je saisis les sous-entendus. »
  - **C2** : « Je comprends sans effort pratiquement tout ce que je lis ou entends, y compris dans un débat rapide entre natifs. »
- **Source** : Conseil de l'Europe (2001, 2020) — *Cadre Européen Commun de Référence pour les Langues*, grille d'auto-évaluation. Formulations adaptées-raccourcies depuis la version officielle FR.
- **Rationale** : calibre la borne basse du niveau (compréhension généralement plus haute que production). Utilisé avec B2 pour détecter les profils bi-skill asymétriques (compréhension C1, production B1 = profil typique "réceptif").
- **Variable DB** : `cefr_comprehension` (ENUM `A1`|`A2`|`B1`|`B2`|`C1`|`C2`)
- **Scoring** : valeur directe.

---

#### B2. `lang_cando_production_1`

- **Énoncé FR** : « Et quand il s'agit de **t'exprimer** en [LANGUE_CIBLE], à l'oral ou à l'écrit… »
- **Format** : radio image+texte, 6 options (1 par CEFR)
- **Options** :
  - **A1** : « Je peux utiliser des expressions simples pour me décrire et poser des questions très basiques, si on m'aide. »
  - **A2** : « Je peux décrire en termes simples ma famille, mon travail, mes habitudes, et échanger sur des sujets familiers. »
  - **B1** : « Je peux raconter une expérience, donner mon opinion brièvement, et me débrouiller dans la plupart des situations courantes en voyage. »
  - **B2** : « Je peux argumenter de façon claire et détaillée sur des sujets variés, et communiquer avec aisance avec des locuteurs natifs. »
  - **C1** : « Je m'exprime spontanément et couramment, je formule mes idées avec précision et j'utilise la langue de façon flexible dans la vie sociale et pro. »
  - **C2** : « Je m'exprime avec précision et nuance, même sur des sujets complexes, dans un registre adapté à chaque contexte. »
- **Source** : CECRL idem B1, échelle "Prendre part à une conversation" + "S'exprimer oralement en continu" fusionnées pour économie cognitive.
- **Rationale** : borne haute auto-perçue. Combinée à B1 → détermine le niveau de départ (on prend `min(comprehension, production)` comme baseline conservateur, sauf contre-preuve mini-probe).
- **Variable DB** : `cefr_production` (ENUM `A1`|`A2`|`B1`|`B2`|`C1`|`C2`)
- **Scoring** : valeur directe. **Dérivée** `cefr_baseline = min(cefr_comprehension, cefr_production)`.

---

#### B*. `lang_probe_discriminant_1` (conditionnel — mini-probe)

- **Condition de déclenchement** : si `max(cefr_comprehension, cefr_production) >= B1` ET Sinse a activé `probe_enabled=true` (flag YAML), affiche cet écran après B2. Sinon skip.
- **Rationale** : au-dessus de A2, les auto-évaluations sont bruitées (effets Dunning-Kruger en A1-A2 faux-B1, imposteurs en C1-réel-B2). Un mini-item discriminant calibre. Sous A2, pas besoin : la marge d'erreur ne change pas les premiers exercices.
- **Énoncé FR** : « Une dernière question rapide pour bien calibrer : traduis cette phrase en [LANGUE_CIBLE]. Ne cherche pas la perfection, fais de ton mieux. »
- **Phrase à traduire (v1, FR → cible)** :
  - **EN** : « Si j'avais su que tu venais, j'aurais préparé un repas. »
    → cible idéale : *If I had known you were coming, I would have prepared a meal.*
    → discriminant : 3rd conditional (past perfect + would have + past participle) = B2+
  - **ES** : « Si hubiera sabido que venías, habría preparado una comida. »
    → discriminant : pluscuamperfecto de subjuntivo + condicional compuesto = B2+
- **Format** : textarea, max 200 chars, placeholder « Écris ta traduction ici… », bouton « Je ne sais pas » (skip accepté).
- **Options** : N/A
- **Source** : item inspiré du *C-Test* (Klein-Braley 1985) et des grammar gap tests utilisés dans Duolingo English Test / Oxford Online Placement Test. Le 3rd conditional / pluscuamperfecto de subjuntivo est un marqueur morphosyntaxique robuste B1/B2 vs B2+ dans les études placement (Purpura 2004).
- **Variable DB** : `probe_answer` (TEXT nullable), `probe_score` (INT 0-3 nullable), `probe_flag` (BOOL — true si self-assessment ≥ B2 mais probe_score ≤ 1, indique overconfidence)
- **Scoring (`probe_score` calculé backend)** :
  - 0 : vide, « je ne sais pas », hors-sujet
  - 1 : tentative avec structure simple (présent ou passé simple) — sub-B1
  - 2 : past simple + would ("if I knew, I would have prepared") — B1-B2, proche
  - 3 : 3rd conditional correct ("if I had known, I would have prepared") ou variante idiomatique équivalente — B2+
- **Implémentation scoring v1** : regex permissive (`if .* had .+ (known|sabido)`, `would have .+ (prepared|preparado)`, `hubiera .+ sabido`, `habría .+ preparado`) + fallback LLM-as-judge `gpt-4.1-mini` 1-shot en async post-POST si ambigu. Coût ~<0.001 $/user. Cf. section 6.3.
- **Règle de fusion avec self-assessment** :
  ```
  cefr_final = cefr_baseline  # défaut
  if probe_score >= 2 and cefr_baseline < 'B1':
      cefr_final = 'B1'       # probe révèle sous-estimation
  if probe_score <= 1 and cefr_baseline >= 'B2':
      cefr_final = 'B1'       # probe révèle surestimation (Dunning-Kruger)
      probe_flag = true       # signal au tuteur de tester doucement
  ```

---

### 3.3 Bloc C — Domain Motivation (langues)

---

#### C1. `lang_ideal_l2_self_1`

- **Énoncé FR** : « Imagine-toi dans 2 ans, parlant couramment [LANGUE_CIBLE]. Qu'est-ce qui te tient le plus à cœur dans cette image ? »
- **Format** : choix multiple (max 2 cochés sur 5), cases à cocher
- **Options** :
  - A. Être compris·e sans effort dans des conversations quotidiennes
  - B. Pouvoir lire / regarder / écouter du contenu natif (livres, films, podcasts)
  - C. Travailler ou étudier dans un pays où cette langue est parlée
  - D. Construire des relations personnelles (amis, famille, partenaire)
  - E. Me sentir à l'aise et confiant·e quand je m'exprime, sans peur de l'erreur
- **Source** : Dörnyei (2005) *Motivational Self System* — construct *Ideal L2 Self* = image vivante de soi comme utilisateur compétent de la langue cible. Taguchi, Magid & Papi (2009) validation cross-cultural. Reformulation des prompts Ideal-L2 ciblant identification vs ought-to vs instrumental.
- **Rationale** : l'Ideal L2 Self est **le meilleur prédicteur de persistance** dans les études Dörnyei/Taguchi (r ≈ 0.5). Le choix A/B/C/D/E permet au tuteur de **teinter les scénarios** (A → dialogues daily, B → extraits authentiques, C → registre pro, D → conversations chaleureuses, E → travail métacognitif sur l'anxiété).
- **Variable DB** : `ideal_l2_self_tags` (TEXT[] ou JSONB array — ex `["daily_communication", "authentic_content"]`)
- **Scoring / mapping tags** :
  - A → `daily_communication`
  - B → `authentic_content`
  - C → `professional_academic`
  - D → `relationships`
  - E → `confidence_expression`

---

#### C2. `lang_fla_short_1` (FLA 3-items compressés)

- **Énoncé FR** : « Quand tu imagines parler [LANGUE_CIBLE] à voix haute avec quelqu'un, voici trois situations. Dis-nous à quel point tu es d'accord avec chacune : »
  - **C2.a** : « Je me sens stressé·e à l'idée de parler sans préparation. »
  - **C2.b** : « J'ai peur qu'on se moque de mes erreurs ou de mon accent. »
  - **C2.c** : « Même quand je connais les mots, j'ai peur de bloquer au moment de parler. »
- **Format** : 3 Likert 5 points empilés sur 1 écran (anti-fatigue, groupés par construct), ancrage :
  1. Pas du tout d'accord
  2. Plutôt pas d'accord
  3. Ni d'accord ni pas d'accord
  4. Plutôt d'accord
  5. Tout à fait d'accord
- **Source** : Teimouri, Goetze & Plonsky (2019) meta-analysis FLA ; items courts dérivés de Horwitz, Horwitz & Cope (1986) *FLCAS* (Foreign Language Classroom Anxiety Scale, 33 items) — on garde les 3 items à charge factorielle la plus élevée sur le facteur *Communication Apprehension* (le sous-construct le plus prédictif de l'évitement de l'oral). MacIntyre & Gardner (1994) pour la forme courte compressée.
- **Rationale** : l'anxiété langagière est un **modérateur majeur** de la motivation → performance. User à FLA élevé : le tuteur doit **démarrer écrit**, autoriser audio-only optionnel, recadrer systématiquement les erreurs comme signal (pas comme faute), éviter le mode "production forcée" des 3 premières sessions. FLA bas : on peut proposer speaking rapidement.
- **Variable DB** : `fla_score` (FLOAT 1.0-5.0 — moyenne des 3 items), `fla_category` (ENUM `low` | `moderate` | `high`)
- **Scoring** :
  - `fla_score = mean(C2.a, C2.b, C2.c)`
  - `fla_category`:
    - 1.0-2.33 → `low`
    - 2.34-3.66 → `moderate`
    - 3.67-5.0 → `high`
  - Les 3 items bruts sont aussi persistés (`fla_items_raw JSONB`) pour future ré-analyse.

---

### 3.4 Récapitulatif scoring → variables DB

| ID item | Variable DB | Type | Source psychométrique |
|---|---|---|---|
| A1 core_self_efficacy_1 | `self_efficacy` | INT 1-5 | GSE / Bandura |
| A2 core_mindset_1 | `mindset` | ENUM fixed/growth | Dweck, Lou & Noels |
| A3 core_goal_specificity_1 | `goal_text` + `goal_specificity_score` | TEXT + INT 0-3 | Locke-Latham |
| A4 core_autonomy_1 | `autonomy_pref` | ENUM g/s/a | Deci-Ryan, Dörnyei |
| A5 core_engagement_1 | `engagement_pattern` | ENUM 4 | intention self-report |
| B1 lang_cando_comprehension_1 | `cefr_comprehension` | ENUM A1-C2 | CECRL |
| B2 lang_cando_production_1 | `cefr_production` | ENUM A1-C2 | CECRL |
| B* lang_probe_discriminant_1 | `probe_answer`, `probe_score`, `probe_flag` | TEXT, INT, BOOL | C-Test / Purpura |
| C1 lang_ideal_l2_self_1 | `ideal_l2_self_tags` | JSONB array | Dörnyei, Taguchi et al. |
| C2 lang_fla_short_1 | `fla_score`, `fla_category`, `fla_items_raw` | FLOAT, ENUM, JSONB | Teimouri / Horwitz / MacIntyre-Gardner |

Dérivées calculées backend au POST :
- `cefr_baseline = min(cefr_comprehension, cefr_production)`
- `cefr_final` (avec correction mini-probe si déclenchée)
- `goal_specificity_score` (heuristique NLP)
- `fla_score`, `fla_category`

---

## 4. Structure YAML — contenu complet

Arborescence :

```
data/onboarding/
├── core.yaml                       # Bloc A, 5 items universels
├── domains/
│   ├── language.yaml               # Bloc B + C tronc commun langues
│   ├── pymentor.yaml               # placeholder v2
│   └── maths.yaml                  # placeholder v3
├── overlays/
│   ├── en.yaml                     # Teacher-specific (anglais)
│   ├── es.yaml                     # Maestro-specific (espagnol)
│   ├── it.yaml                     # placeholder (Wave 2)
│   ├── de.yaml                     # placeholder
│   ├── jp.yaml                     # placeholder
│   ├── ru.yaml                     # placeholder
│   └── _i18n/                      # FR-only v1, structure i18n-ready
│       └── README.md               # « v1 = FR-only, keys prêtes pour EN/ES/IT/DE UI »
└── schema.json                     # JSON Schema validant les YAMLs
```

### 4.1 `core.yaml`

```yaml
# data/onboarding/core.yaml
# Bloc A — Universal Core (5 items)
# Réutilisable pour tous domaines (langues, pymentor, maths, …)
# Sources : Bandura 1997, Dweck 2006, Lou & Noels 2019, Locke-Latham 2002,
#           Deci-Ryan 2000, Dörnyei 2005

version: "1.0.0"
block: core
locale_default: fr
items:

  - id: core_self_efficacy_1
    order: 1
    construct: self_efficacy
    source: "Bandura 1997 — GSE short form"
    format: likert_5
    required: true
    prompt:
      fr: >-
        Quand je me fixe un objectif d'apprentissage, je suis généralement
        capable de l'atteindre, même si ça demande des efforts.
    scale:
      labels_fr:
        - "Pas du tout d'accord"
        - "Plutôt pas d'accord"
        - "Ni d'accord ni pas d'accord"
        - "Plutôt d'accord"
        - "Tout à fait d'accord"
      values: [1, 2, 3, 4, 5]
    db_variable: self_efficacy
    db_type: INT
    scoring:
      type: raw
      derived_category:
        low: [1, 2]
        medium: [3]
        high: [4, 5]

  - id: core_mindset_1
    order: 2
    construct: mindset
    source: "Dweck 2006 ; Lou & Noels 2019 — forced-choice adapted"
    format: choice_single
    required: true
    prompt:
      fr: >-
        Selon toi, la capacité à apprendre une nouvelle compétence, c'est plutôt…
    options:
      - id: fixed
        label_fr: >-
          Un talent qu'on a ou qu'on n'a pas, et qui change peu avec la pratique.
      - id: growth
        label_fr: >-
          Une aptitude qui se développe avec l'effort et les bonnes méthodes.
    db_variable: mindset
    db_type: "ENUM('fixed','growth')"
    scoring:
      type: map
      map: { fixed: fixed, growth: growth }

  - id: core_goal_specificity_1
    order: 3
    construct: goal_specificity
    source: "Locke & Latham 2002 — specific goals"
    format: text_short
    required: true
    min_chars: 10
    max_chars: 200
    prompt:
      fr: >-
        Pourquoi veux-tu progresser dans cette langue ? Décris en une phrase
        concrète (ex : *comprendre les séries en VO sans sous-titres* ou
        *parler avec ma belle-famille espagnole*).
    placeholder_fr: "Ex : comprendre les podcasts en VO, parler au boulot…"
    db_variable: goal_text
    db_type: TEXT
    scoring:
      type: text_passthrough
      derived:
        goal_specificity_score:
          type: heuristic
          algorithm: goal_nlp_v1
          range: [0, 3]

  - id: core_autonomy_1
    order: 4
    construct: autonomy_pref
    source: "Deci & Ryan 2000 ; Dörnyei 2005"
    format: choice_single
    required: true
    prompt:
      fr: >-
        Quand tu apprends quelque chose de nouveau, tu préfères…
    options:
      - id: guided
        label_fr: "Qu'on me donne un plan précis étape par étape."
      - id: semi_autonomous
        label_fr: >-
          Qu'on me propose un cadre, mais que je choisisse le rythme et les sujets.
      - id: autonomous
        label_fr: >-
          Que je définisse moi-même mes objectifs et que le tuteur s'adapte.
    db_variable: autonomy_pref
    db_type: "ENUM('guided','semi_autonomous','autonomous')"
    scoring:
      type: map
      map:
        guided: guided
        semi_autonomous: semi_autonomous
        autonomous: autonomous

  - id: core_engagement_1
    order: 5
    construct: engagement_pattern
    source: "Ajzen TPB intention ; spaced repetition (Cepeda 2006)"
    format: choice_single
    required: true
    prompt:
      fr: "Tu comptes t'entraîner à quelle fréquence ?"
    options:
      - id: daily_short
        label_fr: "Quelques minutes par jour (5-15 min)"
      - id: weekly_long
        label_fr: "Une session plus longue 2-3 fois par semaine (30-45 min)"
      - id: opportunistic
        label_fr: "Plutôt 1-2 fois par semaine, quand j'ai le temps"
      - id: daily_intense
        label_fr: "Très intensif, tous les jours 30+ min"
    db_variable: engagement_pattern
    db_type: "ENUM('daily_short','weekly_long','opportunistic','daily_intense')"
    scoring:
      type: map
      map:
        daily_short: daily_short
        weekly_long: weekly_long
        opportunistic: opportunistic
        daily_intense: daily_intense
```

### 4.2 `domains/language.yaml`

```yaml
# data/onboarding/domains/language.yaml
# Bloc B (level) + Bloc C (motivation) — tronc commun pour toutes langues
# Overlays dans overlays/{en,es,it,de,jp,ru}.yaml injectent LANGUE_CIBLE

version: "1.0.0"
domain: language
requires_variable: target_language    # injecté par l'overlay : en, es, …
locale_default: fr

# ---------- Bloc B — Domain Level ----------
items:

  - id: lang_cando_comprehension_1
    block: level
    order: 6
    construct: cefr_comprehension
    source: "CECRL 2001/2020 — self-assessment grid"
    format: choice_single_rich
    required: true
    prompt:
      fr: >-
        En {{language_display_fr}}, à l'écrit comme à l'oral, je peux…
        (choisis la description qui te correspond le mieux actuellement)
    options:
      - id: A1
        label_fr: >-
          Je comprends des mots familiers et des expressions très simples quand
          on me parle lentement et clairement.
      - id: A2
        label_fr: >-
          Je comprends des phrases et un vocabulaire très fréquent (infos
          personnelles, achats, travail). Je saisis l'essentiel d'annonces simples.
      - id: B1
        label_fr: >-
          Je comprends les points essentiels quand un langage clair et standard
          est utilisé, sur des sujets familiers (travail, école, loisirs).
      - id: B2
        label_fr: >-
          Je comprends des émissions TV et films en langue standard, et
          l'essentiel de textes complexes sur des sujets concrets ou abstraits.
      - id: C1
        label_fr: >-
          Je comprends un discours long même non clairement structuré, et des
          textes longs et exigeants. Je saisis les sous-entendus.
      - id: C2
        label_fr: >-
          Je comprends sans effort pratiquement tout ce que je lis ou entends,
          y compris dans un débat rapide entre natifs.
    db_variable: cefr_comprehension
    db_type: "ENUM('A1','A2','B1','B2','C1','C2')"
    scoring:
      type: direct

  - id: lang_cando_production_1
    block: level
    order: 7
    construct: cefr_production
    source: "CECRL 2001/2020 — spoken/written production grids"
    format: choice_single_rich
    required: true
    prompt:
      fr: >-
        Et quand il s'agit de **t'exprimer** en {{language_display_fr}}, à
        l'oral ou à l'écrit…
    options:
      - id: A1
        label_fr: >-
          Je peux utiliser des expressions simples pour me décrire et poser
          des questions très basiques, si on m'aide.
      - id: A2
        label_fr: >-
          Je peux décrire en termes simples ma famille, mon travail, mes
          habitudes, et échanger sur des sujets familiers.
      - id: B1
        label_fr: >-
          Je peux raconter une expérience, donner mon opinion brièvement, et
          me débrouiller dans la plupart des situations courantes en voyage.
      - id: B2
        label_fr: >-
          Je peux argumenter de façon claire et détaillée sur des sujets
          variés, et communiquer avec aisance avec des locuteurs natifs.
      - id: C1
        label_fr: >-
          Je m'exprime spontanément et couramment, je formule mes idées avec
          précision et j'utilise la langue de façon flexible dans la vie
          sociale et pro.
      - id: C2
        label_fr: >-
          Je m'exprime avec précision et nuance, même sur des sujets
          complexes, dans un registre adapté à chaque contexte.
    db_variable: cefr_production
    db_type: "ENUM('A1','A2','B1','B2','C1','C2')"
    scoring:
      type: direct

  # ---------- Mini-probe conditionnel ----------
  - id: lang_probe_discriminant_1
    block: level
    order: 7.5
    construct: probe_discriminant
    source: "C-Test (Klein-Braley 1985) ; Purpura 2004 grammar placement"
    format: text_short
    required: false       # skip autorisé
    conditional:
      rule: "max(cefr_comprehension, cefr_production) >= B1"
      feature_flag: onboarding_probe_enabled   # ON/OFF global
    min_chars: 0
    max_chars: 200
    prompt:
      fr: >-
        Une dernière question rapide pour bien calibrer : traduis cette phrase
        en {{language_display_fr}}. Ne cherche pas la perfection, fais de ton
        mieux.
    sentence_to_translate:
      fr: "Si j'avais su que tu venais, j'aurais préparé un repas."
      # les phrases cibles sont dans les overlays en.yaml / es.yaml
    skip_label_fr: "Je ne sais pas"
    placeholder_fr: "Écris ta traduction ici…"
    db_variable: probe_answer
    db_type: TEXT
    scoring:
      type: hybrid
      algorithm: probe_scorer_v1
      range: [0, 3]
      derived:
        probe_flag:
          rule: "self_assessment_max >= B2 AND probe_score <= 1"

# ---------- Bloc C — Domain Motivation ----------
  - id: lang_ideal_l2_self_1
    block: motivation
    order: 8
    construct: ideal_l2_self
    source: "Dörnyei 2005 ; Taguchi, Magid & Papi 2009"
    format: choice_multi
    required: true
    min_selected: 1
    max_selected: 2
    prompt:
      fr: >-
        Imagine-toi dans 2 ans, parlant couramment {{language_display_fr}}.
        Qu'est-ce qui te tient le plus à cœur dans cette image ?
    options:
      - id: daily_communication
        label_fr: "Être compris·e sans effort dans des conversations quotidiennes"
      - id: authentic_content
        label_fr: >-
          Pouvoir lire / regarder / écouter du contenu natif (livres, films,
          podcasts)
      - id: professional_academic
        label_fr: "Travailler ou étudier dans un pays où cette langue est parlée"
      - id: relationships
        label_fr: "Construire des relations personnelles (amis, famille, partenaire)"
      - id: confidence_expression
        label_fr: >-
          Me sentir à l'aise et confiant·e quand je m'exprime, sans peur de l'erreur
    db_variable: ideal_l2_self_tags
    db_type: "JSONB"
    scoring:
      type: tags_array

  - id: lang_fla_short_1
    block: motivation
    order: 9
    construct: foreign_language_anxiety
    source: "Teimouri et al. 2019 ; Horwitz et al. 1986 FLCAS ; MacIntyre-Gardner 1994"
    format: likert_group_3
    required: true
    prompt_group:
      fr: >-
        Quand tu imagines parler {{language_display_fr}} à voix haute avec
        quelqu'un, voici trois situations. Dis-nous à quel point tu es
        d'accord avec chacune :
    sub_items:
      - id: fla_a
        prompt_fr: "Je me sens stressé·e à l'idée de parler sans préparation."
      - id: fla_b
        prompt_fr: "J'ai peur qu'on se moque de mes erreurs ou de mon accent."
      - id: fla_c
        prompt_fr: "Même quand je connais les mots, j'ai peur de bloquer au moment de parler."
    scale:
      labels_fr:
        - "Pas du tout d'accord"
        - "Plutôt pas d'accord"
        - "Ni d'accord ni pas d'accord"
        - "Plutôt d'accord"
        - "Tout à fait d'accord"
      values: [1, 2, 3, 4, 5]
    db_variable: fla_items_raw
    db_type: JSONB
    scoring:
      type: likert_mean
      derived:
        fla_score:
          formula: "mean(fla_a, fla_b, fla_c)"
          range: [1.0, 5.0]
        fla_category:
          bins:
            low:      [1.0, 2.33]
            moderate: [2.34, 3.66]
            high:     [3.67, 5.0]
```

### 4.3 `overlays/en.yaml`

```yaml
# data/onboarding/overlays/en.yaml
# Overlay spécifique pour apprenants d'anglais (Teacher)

version: "1.0.0"
extends: domains/language.yaml
language_code: en
language_display_fr: "anglais"
language_display_en: "English"

# Phrase pour mini-probe (cible anglaise)
probe:
  item_id: lang_probe_discriminant_1
  source_sentence_fr: "Si j'avais su que tu venais, j'aurais préparé un repas."
  target_gold:
    - "If I had known you were coming, I would have prepared a meal."
    - "Had I known you were coming, I would have prepared a meal."
  target_structure: "3rd conditional (past perfect + would have + past participle)"
  discriminant_cefr: "B2+"
  accepted_variants_regex:
    strong: '(?i)(if i had known|had i known).*(you were coming|you (were|''d) come).*(would(n''t)? have (prepared|made|cooked))'
    medium: '(?i)(if i (knew|had known)).*(coming|come).*(would (have )?(prepared|made|cooked))'
    weak: '(?i)(if i know|knew).*(come|coming).*(prepare|make|cook)'
  fallback_judge:
    enabled: true
    model: "gpt-4.1-mini"
    prompt_template: probe_judge_en_v1

# Tuteur (Teacher) override — rien pour v1, hook pour futur
tutor_overrides: {}
```

### 4.4 `overlays/es.yaml`

```yaml
# data/onboarding/overlays/es.yaml
# Overlay spécifique pour apprenants d'espagnol (Maestro)

version: "1.0.0"
extends: domains/language.yaml
language_code: es
language_display_fr: "espagnol"
language_display_es: "español"

probe:
  item_id: lang_probe_discriminant_1
  source_sentence_fr: "Si j'avais su que tu venais, j'aurais préparé un repas."
  target_gold:
    - "Si hubiera sabido que venías, habría preparado una comida."
    - "Si hubiese sabido que venías, habría preparado una comida."
    - "De haber sabido que venías, habría preparado una comida."
  target_structure: "Pluscuamperfecto de subjuntivo + condicional compuesto"
  discriminant_cefr: "B2+"
  accepted_variants_regex:
    strong: '(?i)(si (hubiera|hubiese) sabido|de haber sabido).*(venías|ibas a venir|vendrías).*(habría|hubiera) (preparado|hecho|cocinado)'
    medium: '(?i)(si (supiera|supiese|sabía)).*(venías|vienes).*(preparar(ía|ía)|har(ía|ía))'
    weak: '(?i)(si (sé|sabía)).*(vienes|venías).*(preparo|hago|cocino)'
  fallback_judge:
    enabled: true
    model: "gpt-4.1-mini"
    prompt_template: probe_judge_es_v1

tutor_overrides: {}
```

### 4.5 `overlays/_i18n/README.md`

```markdown
# i18n placeholder — FR-only v1

Decision D5 (Sinse, 2026-04-20) : v1 livre QCM en FR uniquement.
Les YAMLs sont déjà structurés i18n-ready (champs `prompt.fr`, `label_fr`,
`scale.labels_fr`, etc.). Pour ajouter une langue d'UI :

1. Pour chaque item, ajouter un sibling `prompt.en`, `label_en`, `scale.labels_en`.
2. Ajouter `locale_default: en` à l'overlay concerné, ou laisser le
   LocaleResolver côté front basculer via `navigator.language`.
3. Mettre à jour les overlays probe_judge_*_v1 prompts si le matching
   pattern diffère par langue d'UI (rare — le contenu de traduction reste
   dans la langue cible).

**Aucune clé à traduire pour v1.**
```

### 4.6 `schema.json` (résumé)

```jsonc
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AcademIA onboarding item",
  "type": "object",
  "required": ["id", "order", "construct", "source", "format",
               "required", "prompt", "db_variable", "scoring"],
  "properties": {
    "id": { "type": "string", "pattern": "^[a-z]+(_[a-z0-9]+)*_\\d+$" },
    "order": { "type": "number" },
    "construct": { "type": "string" },
    "source": { "type": "string" },
    "format": {
      "enum": ["likert_5", "choice_single", "choice_single_rich",
               "choice_multi", "text_short", "likert_group_3"]
    },
    "required": { "type": "boolean" },
    "conditional": {
      "type": "object",
      "properties": {
        "rule": { "type": "string" },
        "feature_flag": { "type": "string" }
      }
    },
    "prompt": {
      "type": "object",
      "required": ["fr"],
      "properties": { "fr": {"type":"string"}, "en": {"type":"string"} }
    },
    "options": { "type": "array" },
    "db_variable": { "type": "string" },
    "scoring": { "type": "object" }
  }
}
```

---

## 5. Format d'injection LLM (double canal)

### 5.1 Principe

Deux canaux complémentaires injectés dans le **system prompt Dify** au 1er tour après QCM :

1. **Canal JSON structuré** (bloc délimité `<learner_profile_json>…</learner_profile_json>`) — consommé par les **code nodes Dify** pour brancher logique déterministe (choix scénario, niveau exercice, registre).
2. **Canal NL résumé** (≤200 mots, bloc `<learner_profile_summary>…</learner_profile_summary>`) — pour que le LLM **comprenne** l'apprenant en prose, sans avoir à parser du JSON (coûte moins de "raisonnement tokens" et évite les hallucinations de champs).

Le LLM reçoit les deux. Le code node Dify reçoit le JSON uniquement. Source de vérité = JSON.

### 5.2 Schéma JSON canal 1

```json
{
  "schema_version": "1.0.0",
  "learner_id": "eleve_uuid_xxx",
  "domain": "language",
  "target_language": "es",
  "created_at": "2026-04-20T10:23:00Z",
  "core": {
    "self_efficacy": 4,
    "self_efficacy_category": "high",
    "mindset": "growth",
    "goal_text": "Parler avec la belle-famille espagnole l'été prochain",
    "goal_specificity_score": 3,
    "autonomy_pref": "semi_autonomous",
    "engagement_pattern": "daily_short"
  },
  "level": {
    "cefr_comprehension": "B1",
    "cefr_production": "A2",
    "cefr_baseline": "A2",
    "cefr_final": "A2",
    "probe_administered": false,
    "probe_score": null,
    "probe_flag": false
  },
  "motivation": {
    "ideal_l2_self_tags": ["relationships", "daily_communication"],
    "fla_score": 3.67,
    "fla_category": "high",
    "fla_items_raw": { "fla_a": 4, "fla_b": 3, "fla_c": 4 }
  },
  "derived_tutor_hints": {
    "scaffold_level": "medium",
    "feedback_framing": "growth_recadrage_erreur",
    "session_size": "micro_5_15min",
    "initial_modality": "writing_first",
    "challenge_level": "stretch_but_safe",
    "scenario_tags_priority": ["relationships", "daily_communication"],
    "fla_hint": "high_anxiety_avoid_forced_speaking_first_3_sessions"
  }
}
```

**`derived_tutor_hints`** — champ calculé backend au POST à partir de règles déterministes (cf. `learner_profile_service.compute_hints()`), **pas** inféré par le LLM. Les règles v1 :

```
scaffold_level       = {self_efficacy_category→low: "high", medium: "medium", high: "low"}
feedback_framing     = mindset==fixed ? "reframe_fixed_to_growth" : "growth_recadrage_erreur"
session_size         = engagement_pattern→{daily_short:"micro_5_15min", weekly_long:"medium_30_45min",
                                           opportunistic:"flex", daily_intense:"long_30_60min"}
initial_modality     = fla_category==high ? "writing_first" : "mixed"
challenge_level      = self_efficacy>=4 AND mindset==growth ? "stretch" : "safe_first"
scenario_tags_priority = ideal_l2_self_tags   # ordre de préférence
fla_hint             = fla_category==high ? "high_anxiety_avoid_forced_speaking_first_3_sessions"
                      : fla_category==moderate ? "moderate_anxiety_gentle_oral_invite"
                      : "low_anxiety_ok_speaking_early"
```

### 5.3 Format résumé NL (canal 2)

Le résumé est **généré par backend** au POST (template Jinja2, pas de LLM), ≤200 mots, 6-8 phrases, registre neutre pour le LLM.

**Template (Jinja2, extrait)** :

```jinja
Apprenant de {{ target_language_name }} (FR natif). Niveau CEFR estimé :
{{ cefr_final }} (compréhension {{ cefr_comprehension }}, production
{{ cefr_production }}{% if probe_flag %}, probe indique une possible
surestimation — démarrer doucement{% endif %}). Objectif déclaré : « {{ goal_text }} »
({{ goal_specificity_level_label }}).

Profil psycho-pédagogique : self-efficacy {{ self_efficacy_category }}
({{ self_efficacy }}/5), mindset {{ mindset }}, préfère un cadre
{{ autonomy_pref_label }}, rythme visé {{ engagement_pattern_label }}.

Motivation : priorités {{ ideal_l2_self_tags|join(", ") }}. Anxiété
langagière (FLA) {{ fla_category }} ({{ fla_score }}/5)
{%- if fla_category == "high" %}, évite la production orale forcée les
premières sessions, privilégie l'écrit{% endif %}.

Consignes tuteur synthétiques : scaffold {{ scaffold_level }},
feedback {{ feedback_framing }}, sessions {{ session_size }},
challenge {{ challenge_level }}.
```

### 5.4 Exemple concret — user fictif « Sophie »

**Entrée (réponses QCM)** :
- A1 self-efficacy : 4
- A2 mindset : `growth`
- A3 goal_text : « Parler avec la belle-famille espagnole l'été prochain »
- A4 autonomy : `semi_autonomous`
- A5 engagement : `daily_short`
- B1 cefr_comprehension : B1
- B2 cefr_production : A2
- B* probe : non administré (max=B1 mais flag `probe_enabled=false` en v1 conservative — OU administré si on active : « Si sabía que venías, preparaba una comida » → score 1, probe_flag=true car self B1 et probe=1 → on bascule à A2)
- C1 ideal_l2_self : [`relationships`, `daily_communication`]
- C2 FLA : [4, 3, 4] → fla_score 3.67 → `high`

**JSON injecté** : identique à l'exemple section 5.2.

**NL résumé rendu** :

> Apprenante d'espagnol (FR natif). Niveau CEFR estimé : A2 (compréhension
> B1, production A2). Objectif déclaré : « Parler avec la belle-famille
> espagnole l'été prochain » (objectif concret avec contexte et échéance).
>
> Profil psycho-pédagogique : self-efficacy élevée (4/5), mindset growth,
> préfère un cadre semi-autonome (on propose 2-3 options, elle choisit),
> rythme visé 5-15 min quotidien.
>
> Motivation : priorités « relations personnelles » puis « communication
> quotidienne ». Anxiété langagière (FLA) élevée (3.67/5) : éviter la
> production orale forcée les premières sessions, privilégier l'écrit.
>
> Consignes tuteur synthétiques : scaffold léger, feedback
> growth-recadrage-erreur, sessions micro 5-15 min, challenge stretch-safe.

**Injection Dify — system prompt Maestro au 1er tour** :

```
[...prompt système Maestro existant...]

<learner_profile_summary>
{le résumé NL ci-dessus}
</learner_profile_summary>

<learner_profile_json>
{le JSON section 5.2}
</learner_profile_json>

INSTRUCTION : ne jamais afficher ces blocs à l'utilisateur. Utilise-les
pour personnaliser ton premier message et ta première activité proposée.
Salue l'utilisatrice par prénom si disponible, propose 2-3 scénarios
ancrés dans ses priorités (relations perso + communication quotidienne),
en démarrant par de l'écrit (FLA élevée).
```

### 5.5 Câblage Dify (rappel n8n workflow_history split)

Le profil est chargé par un **code node early** (avant LLM node) :
- input : `learner_id`, `domain`
- HTTP call backend : `GET /api/learner-profile/{domain}?learner_id=...`
- output variables : `profile_json`, `profile_summary`, `derived_hints`

Variables référencées par le LLM node via `{{#load_profile.profile_summary#}}` et `{{#load_profile.profile_json#}}` (**pas** `{{#start.X#}}` — cf. memory entry `project_dify_variable_wiring.md`).

**IMPORTANT** : patch obligatoire des deux tables n8n pour les workflows Dify cross-compilés :
- `workflow_entity.nodes`
- `workflow_history.nodes`
(cf. `project_n8n_workflow_history.md`).

---

## 6. Schéma DB + endpoints REST

### 6.1 Table `learner_profiles` — DDL PostgreSQL

```sql
-- migrations/2026_04_20_01__create_learner_profiles.sql
-- Idempotent — safe à rerun

BEGIN;

-- ENUMs (si absents — IF NOT EXISTS pattern pour PG ≥9.6 via DO block)
DO $$ BEGIN
    CREATE TYPE mindset_enum AS ENUM ('fixed', 'growth');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE autonomy_pref_enum AS ENUM (
        'guided', 'semi_autonomous', 'autonomous'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE engagement_pattern_enum AS ENUM (
        'daily_short', 'weekly_long', 'opportunistic', 'daily_intense'
    );
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE cefr_enum AS ENUM ('A1','A2','B1','B2','C1','C2');
EXCEPTION WHEN duplicate_object THEN null; END $$;

DO $$ BEGIN
    CREATE TYPE fla_category_enum AS ENUM ('low','moderate','high');
EXCEPTION WHEN duplicate_object THEN null; END $$;

-- Table
CREATE TABLE IF NOT EXISTS learner_profiles (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eleve_id                  UUID NOT NULL
                                REFERENCES eleves(id) ON DELETE CASCADE,
    domain                    VARCHAR(32) NOT NULL,             -- 'language', 'pymentor', …
    target_language           VARCHAR(8),                       -- 'en','es',… NULL si non-langue
    schema_version            VARCHAR(16) NOT NULL DEFAULT '1.0.0',

    -- Bloc A (core)
    self_efficacy             SMALLINT NOT NULL
                                CHECK (self_efficacy BETWEEN 1 AND 5),
    mindset                   mindset_enum NOT NULL,
    goal_text                 TEXT NOT NULL
                                CHECK (char_length(goal_text) BETWEEN 10 AND 200),
    goal_specificity_score    SMALLINT NOT NULL
                                CHECK (goal_specificity_score BETWEEN 0 AND 3),
    autonomy_pref             autonomy_pref_enum NOT NULL,
    engagement_pattern        engagement_pattern_enum NOT NULL,

    -- Bloc B (level) — nullables si domaine != language
    cefr_comprehension        cefr_enum,
    cefr_production           cefr_enum,
    cefr_baseline             cefr_enum,
    cefr_final                cefr_enum,
    probe_administered        BOOLEAN NOT NULL DEFAULT FALSE,
    probe_answer              TEXT,
    probe_score               SMALLINT CHECK (probe_score BETWEEN 0 AND 3),
    probe_flag                BOOLEAN NOT NULL DEFAULT FALSE,

    -- Bloc C (motivation)
    ideal_l2_self_tags        JSONB,                            -- ["daily_communication", ...]
    fla_items_raw             JSONB,                            -- {"fla_a":4,"fla_b":3,"fla_c":4}
    fla_score                 NUMERIC(3,2)
                                CHECK (fla_score BETWEEN 1.0 AND 5.0),
    fla_category              fla_category_enum,

    -- Dérivés tuteur (cache, recalculables)
    derived_tutor_hints       JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Metadata
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- 1 profil par (eleve, domain, target_language)
    CONSTRAINT uniq_learner_profile
        UNIQUE (eleve_id, domain, target_language)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_learner_profiles_eleve
    ON learner_profiles (eleve_id);
CREATE INDEX IF NOT EXISTS idx_learner_profiles_domain_lang
    ON learner_profiles (domain, target_language);
CREATE INDEX IF NOT EXISTS idx_learner_profiles_updated
    ON learner_profiles (updated_at DESC);

-- Trigger updated_at
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_learner_profiles_updated_at ON learner_profiles;
CREATE TRIGGER trg_learner_profiles_updated_at
    BEFORE UPDATE ON learner_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMIT;
```

**Notes** :
- Relation 1-to-many avec `eleves` (D3 respecté — **pas** de réutilisation de `profils_eleves` legacy).
- `UNIQUE (eleve_id, domain, target_language)` → 1 user peut avoir 1 profil langue EN et 1 profil langue ES (il repasse le QCM pour chaque langue, D6).
- `ON DELETE CASCADE` : si eleve supprimé, profils nettoyés.
- `NUMERIC(3,2)` pour fla_score (précision 0.01, range 1.00-5.00).
- `JSONB` pour tags/items bruts : permet requête `WHERE ideal_l2_self_tags @> '["relationships"]'`.

### 6.2 Schémas Pydantic

```python
# app/schemas/learner_profile.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, constr, conint, confloat, model_validator


# ---------- ENUMs ----------
class MindsetEnum(str, Enum):
    fixed = "fixed"
    growth = "growth"


class AutonomyPrefEnum(str, Enum):
    guided = "guided"
    semi_autonomous = "semi_autonomous"
    autonomous = "autonomous"


class EngagementPatternEnum(str, Enum):
    daily_short = "daily_short"
    weekly_long = "weekly_long"
    opportunistic = "opportunistic"
    daily_intense = "daily_intense"


class CEFREnum(str, Enum):
    A1 = "A1"; A2 = "A2"; B1 = "B1"
    B2 = "B2"; C1 = "C1"; C2 = "C2"


class FLACategoryEnum(str, Enum):
    low = "low"; moderate = "moderate"; high = "high"


IdealL2SelfTag = Literal[
    "daily_communication",
    "authentic_content",
    "professional_academic",
    "relationships",
    "confidence_expression",
]


# ---------- Sub-schemas ----------
class FLAItemsRaw(BaseModel):
    fla_a: conint(ge=1, le=5)
    fla_b: conint(ge=1, le=5)
    fla_c: conint(ge=1, le=5)


# ---------- Input (QCM submit) ----------
class LearnerProfileSubmit(BaseModel):
    """Payload envoyé par le front à la fin du QCM (POST)."""
    domain: Literal["language", "pymentor", "maths"] = "language"
    target_language: Optional[Literal["en","es","it","de","jp","ru"]] = None

    # Bloc A
    self_efficacy: conint(ge=1, le=5)
    mindset: MindsetEnum
    goal_text: constr(min_length=10, max_length=200)
    autonomy_pref: AutonomyPrefEnum
    engagement_pattern: EngagementPatternEnum

    # Bloc B (langues)
    cefr_comprehension: Optional[CEFREnum] = None
    cefr_production: Optional[CEFREnum] = None
    probe_answer: Optional[constr(max_length=200)] = None

    # Bloc C
    ideal_l2_self_tags: List[IdealL2SelfTag] = Field(
        default_factory=list, min_length=1, max_length=2
    )
    fla_items_raw: Optional[FLAItemsRaw] = None

    @model_validator(mode="after")
    def validate_language_fields(self):
        if self.domain == "language":
            assert self.target_language is not None, \
                "target_language required for language domain"
            assert self.cefr_comprehension and self.cefr_production, \
                "cefr fields required for language domain"
            assert self.fla_items_raw is not None, \
                "fla_items_raw required for language domain"
        return self


# ---------- Output (read) ----------
class LearnerProfileRead(BaseModel):
    id: UUID
    eleve_id: UUID
    domain: str
    target_language: Optional[str]
    schema_version: str

    # Core
    self_efficacy: int
    self_efficacy_category: Literal["low", "medium", "high"]
    mindset: MindsetEnum
    goal_text: str
    goal_specificity_score: int
    autonomy_pref: AutonomyPrefEnum
    engagement_pattern: EngagementPatternEnum

    # Level
    cefr_comprehension: Optional[CEFREnum]
    cefr_production: Optional[CEFREnum]
    cefr_baseline: Optional[CEFREnum]
    cefr_final: Optional[CEFREnum]
    probe_administered: bool
    probe_score: Optional[int]
    probe_flag: bool

    # Motivation
    ideal_l2_self_tags: List[IdealL2SelfTag]
    fla_items_raw: Optional[FLAItemsRaw]
    fla_score: Optional[float]
    fla_category: Optional[FLACategoryEnum]

    # Dérivé
    derived_tutor_hints: dict

    # Meta
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Partial update (PATCH) ----------
class LearnerProfilePatch(BaseModel):
    """Tous champs optionnels — l'user peut ré-éditer 1 ou plusieurs réponses."""
    self_efficacy: Optional[conint(ge=1, le=5)] = None
    mindset: Optional[MindsetEnum] = None
    goal_text: Optional[constr(min_length=10, max_length=200)] = None
    autonomy_pref: Optional[AutonomyPrefEnum] = None
    engagement_pattern: Optional[EngagementPatternEnum] = None
    cefr_comprehension: Optional[CEFREnum] = None
    cefr_production: Optional[CEFREnum] = None
    probe_answer: Optional[constr(max_length=200)] = None
    ideal_l2_self_tags: Optional[List[IdealL2SelfTag]] = Field(
        default=None, min_length=1, max_length=2
    )
    fla_items_raw: Optional[FLAItemsRaw] = None
```

### 6.3 Endpoints FastAPI

```python
# app/api/learner_profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.learner_profile import (
    LearnerProfileSubmit, LearnerProfileRead, LearnerProfilePatch,
)
from app.services import learner_profile_service as svc
from app.deps import get_db, get_current_eleve


router = APIRouter(prefix="/api/learner-profile", tags=["learner-profile"])


@router.get(
    "/{domain}",
    response_model=LearnerProfileRead,
    responses={404: {"description": "No profile yet — show QCM"}},
)
async def get_profile(
    domain: str,
    target_language: str | None = None,
    eleve=Depends(get_current_eleve),
    db: AsyncSession = Depends(get_db),
):
    """Renvoie 404 si pas de profil (front déclenche le QCM modal)."""
    profile = await svc.get_profile(
        db, eleve_id=eleve.id,
        domain=domain, target_language=target_language,
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="learner_profile_not_found",
        )
    return profile


@router.post(
    "/{domain}",
    response_model=LearnerProfileRead,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Profile already exists (use PATCH)"}},
)
async def submit_profile(
    domain: str,
    payload: LearnerProfileSubmit,
    eleve=Depends(get_current_eleve),
    db: AsyncSession = Depends(get_db),
):
    """Submit QCM — valide schema, calcule dérivés, persiste."""
    if payload.domain != domain:
        raise HTTPException(422, "domain mismatch path vs body")

    existing = await svc.get_profile(
        db, eleve_id=eleve.id,
        domain=domain, target_language=payload.target_language,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="learner_profile_already_exists",
        )

    profile = await svc.create_profile(db, eleve_id=eleve.id, payload=payload)
    return profile


@router.patch(
    "/{domain}",
    response_model=LearnerProfileRead,
)
async def patch_profile(
    domain: str,
    payload: LearnerProfilePatch,
    target_language: str | None = None,
    eleve=Depends(get_current_eleve),
    db: AsyncSession = Depends(get_db),
):
    """Update partiel — recalcule dérivés sur champs modifiés."""
    profile = await svc.get_profile(
        db, eleve_id=eleve.id,
        domain=domain, target_language=target_language,
    )
    if not profile:
        raise HTTPException(404, "learner_profile_not_found")

    updated = await svc.patch_profile(db, profile=profile, payload=payload)
    return updated
```

### 6.4 Service — calculs dérivés (extrait)

```python
# app/services/learner_profile_service.py
# Fonctions clés (signatures ; implémentations détaillées hors scope doc)

async def create_profile(
    db, *, eleve_id: UUID, payload: LearnerProfileSubmit
) -> LearnerProfile:
    goal_spec = score_goal_specificity(payload.goal_text)         # 0-3
    cefr_baseline = min_cefr(payload.cefr_comprehension,
                             payload.cefr_production)
    probe_score, probe_flag, cefr_final = score_probe(
        payload.probe_answer,
        target_language=payload.target_language,
        cefr_baseline=cefr_baseline,
        self_max=max_cefr(payload.cefr_comprehension, payload.cefr_production),
    )
    fla_score, fla_cat = score_fla(payload.fla_items_raw)
    hints = compute_tutor_hints(
        self_efficacy=payload.self_efficacy,
        mindset=payload.mindset,
        autonomy_pref=payload.autonomy_pref,
        engagement_pattern=payload.engagement_pattern,
        fla_category=fla_cat,
        ideal_l2_self_tags=payload.ideal_l2_self_tags,
        probe_flag=probe_flag,
    )
    # persist + return
    ...


def score_goal_specificity(text: str) -> int:
    """Heuristique NLP v1 — cf. section 3 A3."""
    ...


def score_probe(answer: str | None, *, target_language: str,
                cefr_baseline: str, self_max: str
                ) -> tuple[int, bool, str]:
    """
    1. Load overlay regex for target_language.
    2. Match strong → 3, medium → 2, weak → 1, else 0 or fallback LLM judge.
    3. Compute probe_flag + cefr_final per règle section 3.2 B*.
    """
    ...


def score_fla(items: FLAItemsRaw | None) -> tuple[float, FLACategoryEnum]:
    if items is None:
        return None, None
    mean = (items.fla_a + items.fla_b + items.fla_c) / 3
    cat = ("low" if mean <= 2.33 else
           "moderate" if mean <= 3.66 else "high")
    return round(mean, 2), cat


def compute_tutor_hints(**kwargs) -> dict:
    """Règles déterministes section 5.2 — renvoie derived_tutor_hints JSONB."""
    ...
```

---

## 7. UX flow step-by-step

### 7.1 Vue d'ensemble

```
Screen 0 — Intro (bloquant, pas de skip)
Screen 1 — A1 self-efficacy           (Likert 1-5)                [1/8]
Screen 2 — A2 mindset                 (forced-choice 2)           [2/8]
Screen 3 — A3 goal_text               (textarea)                  [3/8]
Screen 4 — A4 autonomy                (choice 3)                  [4/8]
Screen 5 — A5 engagement              (choice 4)                  [5/8]
Screen 6 — B1 cefr_comprehension      (cards 6 CEFR)              [6/8]
Screen 7 — B2 cefr_production         (cards 6 CEFR)              [7/8]
Screen 7.5 — B* probe (conditionnel)  (textarea + skip)           [7.5/8]
Screen 8 — C1 ideal_l2_self           (checkboxes max 2)          [8/9] ¹
Screen 9 — C2 fla (3 Likert groupés)  (Likert x3 sur 1 écran)     [9/9]
Screen 10 — Résumé "Voici ton profil" (recap + CTA "Commencer")
```

¹ La progress bar ajuste son dénominateur à 9 si mini-probe déclenchée, sinon 8.

### 7.2 Détail par écran

#### Screen 0 — Intro

- **Visuel** : illustration simple (pas d'emoji v1), titre H1.
- **Titre FR** : « 2-3 minutes pour calibrer ton tuteur »
- **Corps FR** :
  > Pour que ton tuteur {{LANGUAGE_DISPLAY_FR}} soit vraiment adapté à toi, on te pose 8 questions rapides. Aucune n'a de bonne ou mauvaise réponse — sois honnête, c'est pour toi.
- **CTA** : bouton primaire « Commencer » (obligatoire)
- **Pas de bouton skip/fermer** — la route `/chat/{lang}` est gatée côté front sur `hasProfile(domain, lang) === true`.
- **Comportement back** : désactivé (bouton back du navigateur capturé → modal « Tu veux vraiment quitter l'onboarding ? Tu devras le recommencer plus tard » avec OK/Annuler).

#### Screen 1 — A1 self-efficacy

- **Progress** : « 1/8 » + barre pleine à 12.5 %
- **Layout** : question centrée, 5 boutons radio horizontaux sur desktop / verticaux sur mobile. Chaque bouton contient son libellé Likert (« Pas du tout d'accord », …) et une micro-étoile pleine 1-5 pour anchor visuel.
- **CTA** : bouton « Suivant » désactivé tant qu'aucune option.
- **Back** : flèche gauche en haut → retour à l'intro OK, sans perte (réponse stockée en state local `qcmDraft`).

#### Screens 2-5 — Bloc A suite

- Mêmes patterns. 1 question par écran. Pas de long-scroll.
- Screen 3 (textarea goal_text) : compteur chars « 0/200 », validation front : `length >= 10` pour activer Suivant, message d'aide « Essaie d'inclure un contexte concret (avec qui, pour quoi, pour quand) — ça aide le tuteur ».

#### Screen 6-7 — Bloc B can-do bi-skill

- **Layout** : 6 cartes empilées (desktop : grid 2 colonnes × 3 lignes ; mobile : stack vertical).
- Chaque carte : badge CEFR en haut-gauche (« A1 », « B2 »…), texte au centre, hover met en évidence.
- Pas de labels « A1/A2/… » dominants côté user ; ils servent surtout l'interne. Le user choisit la description qui lui ressemble.

#### Screen 7.5 — Mini-probe (conditionnel)

- **Déclenchement** : `max(cefr_comprehension, cefr_production) >= B1` AND `feature_flag.onboarding_probe_enabled == true`.
- **Visuel** : même layout que goal_text mais avec :
  - Phrase source FR affichée en gris : *Si j'avais su que tu venais, j'aurais préparé un repas.*
  - Textarea pour traduction
  - Bouton secondaire « Je ne sais pas » (skip → probe_score = 0, probe_flag = true si self ≥ B2)
- **Timing** : pas de timer bloquant, mais tracking `time_spent_ms` pour télémétrie.

#### Screen 8 — Ideal L2 Self

- **Layout** : 5 checkboxes avec compteur « 2/2 max » en bas. Désactive les checkboxes au-delà de 2 cochés.
- **CTA Suivant** activé si ≥1 coché.

#### Screen 9 — FLA 3 items

- **Layout** : 1 écran, 3 questions Likert empilées verticalement, mêmes 5 labels réutilisés (répétés ou placés en entête commune « De 1 = pas du tout d'accord à 5 = tout à fait d'accord »).
- Pattern matrix Likert pour économiser scroll : 1 colonne par valeur 1-5, 1 ligne par sub-item.
- CTA Suivant activé si 3 lignes remplies.

#### Screen 10 — Résumé

- **Titre** : « Voici ton profil — {{PRÉNOM}} »
- **Corps** : carte recap avec 4-5 bullets dérivés **en langage naturel user-facing** (différent du résumé LLM) :
  - « Niveau estimé en {{LANGUAGE}} : {{cefr_final}} »
  - « Ton objectif : *{{goal_text}}* »
  - « Rythme visé : {{engagement_pattern_label_user}} »
  - « Tu préfères : {{autonomy_pref_label_user}} »
  - Si fla_category high : « On va démarrer tranquille, à l'écrit d'abord. »
- **CTA primaire** : « Commencer mon 1er échange » → redirige `/chat/{lang}` avec profil chargé.
- **CTA secondaire** (lien discret) : « Modifier mes réponses » → rouvre le flow en mode édition (PATCH-ready).

### 7.3 Persistance et gestion refresh/back

- **State local draft** (`qcmDraft`) persistée en `localStorage` sous clé `academie.qcm.draft.{eleveId}.{domain}.{lang}` à chaque `onChange`.
- Au mount du modal : si `qcmDraft` existe → modale « Reprendre où tu t'es arrêté·e ? » [Reprendre / Recommencer].
- Au POST réussi : `localStorage.remove(key)` et setState `hasProfile=true`.
- Refresh en cours de QCM : on reprend à l'écran où state draft s'arrête (tracking `lastScreenSeen`).
- Refresh après POST réussi : GET 200, modal ne s'affiche plus.

### 7.4 Télémétrie

Events à émettre (analytics pipeline) :
- `qcm_started` (eleve_id, domain, lang, version)
- `qcm_screen_viewed` (screen_id, time_since_start_ms)
- `qcm_item_answered` (item_id, answer_raw, time_spent_ms)
- `qcm_submitted` (total_time_ms, skipped_items[])
- `qcm_abandoned` (last_screen, time_on_screen_ms) — sur beforeunload si non-submit

Cible alpha : taux de complétion > 85 %, temps médian < 180 s.

### 7.5 Accessibilité

- `role="dialog"` `aria-modal="true"` sur le conteneur.
- Focus trap dans la modale.
- Navigation clavier : Tab / Shift+Tab, Enter = Suivant si bouton focus.
- Labels ARIA explicites sur chaque radio/checkbox.
- Contraste AA minimum, taille texte > 16 px.
- Pas de dépendance à la couleur seule (ex : carte CEFR sélectionnée a bordure + coche, pas juste teinte).

---

## 8. Tradeoffs A/B/C

### 8.1 Option A — Tout LLM conversationnel (status quo, rejetée)

**Description** : le Teacher/Maestro pose les questions en dialogue libre pendant 8-15 tours, extrait variables en JSON au fil de l'eau.

**Pros** :
- Naturel, user-friendly en apparence.
- Extensible sans refonte front (tout le prompt change).
- Couvre les edge-cases verbalement (« j'ai commencé l'espagnol à l'école mais j'ai tout oublié » → LLM reformule).

**Cons (observés en prod)** :
- **Non-déterministe** : oublie 30-50 % des variables, en invente d'autres.
- **Long** : 8-12 min médian.
- **Coûteux** : ~8k tokens/user × 2 tuteurs.
- **QA impossible** : pas de baseline reproductible.
- **Bugs Dify** : régressions à chaque patch, instabilité du câblage variables (`{{#start.X#}}` vs `{{#code_turn_check.X#}}`).
- **Drop-off 40 %** avant 1re activité.

**Verdict** : rejeté.

### 8.2 Option B — QCM 20+ questions exhaustif

**Description** : QCM complet couvrant FLCAS 33-items, MSLQ 81-items allégé, Ideal-L2 8-items, plus placement test 10 items.

**Pros** :
- Précision psychométrique maximale.
- Base de recherche future solide.
- Segments utilisateurs très fins.

**Cons** :
- **Fatigue onboarding** : 15-20 min estimés → drop-off probable > 50 % (Duolingo placement = 10 min fait ~35 % drop).
- **Over-engineering v1** : on n'a pas encore la volumétrie pour exploiter 20 variables.
- **Maintenance multilingue** lourde (traduire 20 Q × 6 langues UI à terme).
- Effort de calibration initial disproportionné par rapport aux usages downstream (tuteur ne va pas lire 20 variables dans le prompt).

**Verdict** : rejeté — diminishing returns.

### 8.3 Option C — QCM 8-10 Q + structure 3 blocs évolutive (**retenue**)

**Description** : la présente spec. Bloc A universel (5 Q) + Bloc B domain level (2-3 Q) + Bloc C domain motivation (2 Q) = 8-10 Q, 90 s-3 min.

**Pros** :
- **Court** : ~2 min médian attendu → drop-off < 15 % (cible).
- **Déterministe** : schéma DB contractualisé, valide au POST, reproductible 100 %.
- **Tuteur reçoit signal fort dès T0** : plus d'onboarding coûteux.
- **Structure 3 blocs** = réutilisation immédiate quand on ajoute PyMentor/Maths (on ne reconstruit que B et C).
- **Items scientifiquement sourcés** : Bandura, Dweck, Locke-Latham, Dörnyei, Taguchi, Teimouri, CECRL — on peut citer et défendre.
- **i18n-ready** : structure YAML prête pour EN/ES/IT/DE UI quand la base utilisateurs le justifie.
- **Coût LLM onboarding : 0** (sauf probe fallback judge, négligeable).
- **Testable** : chaque item a un contrat de valeur, donc test unitaire possible.

**Cons** :
- Perd la "chaleur conversationnelle" du tuteur pendant le QCM → compensé par le Screen 10 recap chaleureux + 1er message tuteur personnalisé via profil injecté.
- Un peu plus de code front (modal, state management) vs pur back.
- Le mini-probe CEFR est rustique (regex + LLM judge fallback) ; on pourrait raffiner v2.
- Risque de biais de désirabilité sur items Likert — mitigé par forced-choice sur mindset, texte libre sur goal.

**Verdict** : **retenu** — meilleur compromis déterminisme × UX × effort v1.

### 8.4 Roadmap post-v1

- **v1.1** : activer mini-probe CEFR par défaut, collecter 500 users, calibrer le regex contre le LLM judge.
- **v1.2** : télémétrie alpha → ajuster libellés items qui bruitent (ex : si engagement_pattern mal compris).
- **v2** : ouvrir PyMentor → implémenter `domains/pymentor.yaml` (2 items level + 2 items motivation ad hoc), Bloc A intact.
- **v2.1** : i18n UI EN/ES (pour users EN natifs apprenant FR, par ex).
- **v3** : A/B tester short-form FLCAS vs form ultra-courte, voir si on peut descendre à 2 sub-items C2.
- **v4** : enrichir `derived_tutor_hints` depuis les traces (si user ignore systématiquement speaking proposé, tuner `initial_modality` auto).

---

## 9. Annexes

### 9.1 Glossaire constructs

- **Self-efficacy** (Bandura) : croyance en sa propre capacité à réussir une tâche spécifique.
- **Mindset** (Dweck) : théorie implicite de l'intelligence — fixe ("talent inné") vs growth ("se développe").
- **Goal specificity** (Locke-Latham) : précision d'un objectif ; prédit la performance.
- **Autonomy orientation** (Deci-Ryan, SDT) : continuum contrôlé → autonome dans la régulation de l'apprentissage.
- **Ideal L2 Self** (Dörnyei) : représentation future de soi comme utilisateur compétent de la langue cible ; moteur motivationnel central.
- **FLA / Foreign Language Anxiety** (Horwitz, Teimouri) : anxiété spécifique situations L2, modérateur négatif performance.
- **CEFR / CECRL** : Cadre Européen Commun de Référence pour les Langues, 6 niveaux A1→C2.
- **Dunning-Kruger (in L2)** : surestimation de son niveau en A1-A2 par méconnaissance de ce qu'on ne sait pas encore.

### 9.2 Bibliographie courte

- Bandura, A. (1997). *Self-Efficacy: The Exercise of Control.* Freeman.
- Conseil de l'Europe. (2001, 2020). *Cadre Européen Commun de Référence pour les Langues.*
- Deci, E. L., & Ryan, R. M. (2000). The "what" and "why" of goal pursuits. *Psychological Inquiry*, 11(4), 227-268.
- Dweck, C. S. (2006). *Mindset: The New Psychology of Success.* Random House.
- Dörnyei, Z. (2005). *The Psychology of the Language Learner.* Erlbaum.
- Horwitz, E. K., Horwitz, M. B., & Cope, J. (1986). Foreign language classroom anxiety. *The Modern Language Journal*, 70(2), 125-132.
- Klein-Braley, C. (1985). A cloze-up on the C-Test. *Language Testing*, 2(1), 76-104.
- Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting and task motivation. *American Psychologist*, 57(9), 705-717.
- Lou, N. M., & Noels, K. A. (2019). Mindsets matter for linguistic minorities. *Language Learning*, 69, 155-183.
- MacIntyre, P. D., & Gardner, R. C. (1994). The subtle effects of language anxiety. *Language Learning*, 44(2), 283-305.
- Purpura, J. E. (2004). *Assessing Grammar.* Cambridge UP.
- Schwarzer, R., & Jerusalem, M. (1995). Generalized Self-Efficacy Scale. In *Measures in Health Psychology*.
- Taguchi, T., Magid, M., & Papi, M. (2009). The L2 Motivational Self System among Japanese, Chinese and Iranian learners. In *Motivation, Language Identity and the L2 Self*.
- Teimouri, Y., Goetze, J., & Plonsky, L. (2019). Second language anxiety and achievement: A meta-analysis. *Studies in Second Language Acquisition*, 41(2), 363-387.

### 9.3 Checklist implémentation

- [ ] Créer migration `2026_04_20_01__create_learner_profiles.sql` + rollback.
- [ ] Ajouter fichiers YAML `data/onboarding/core.yaml`, `domains/language.yaml`, `overlays/{en,es}.yaml`.
- [ ] Schéma JSON `schema.json` + validation au boot.
- [ ] `app/schemas/learner_profile.py` (Pydantic).
- [ ] `app/services/learner_profile_service.py` avec `score_goal_specificity`, `score_probe`, `score_fla`, `compute_tutor_hints`.
- [ ] `app/api/learner_profile.py` routes GET/POST/PATCH.
- [ ] Template Jinja2 résumé NL pour Dify.
- [ ] Feature flag `onboarding_qcm_enabled` + `onboarding_probe_enabled`.
- [ ] Front : modal blocking + 10 écrans + draft localStorage + télémétrie.
- [ ] Dify : code node `load_profile` → câbler sur LLM node Teacher + Maestro (attention double table `workflow_entity.nodes` + `workflow_history.nodes`).
- [ ] Migration users ES existants D6 : `eleves` avec `onboarded_es_legacy=true` → `learner_profiles` vide → QCM fresh au prochain login.
- [ ] Tests : unit (scoring), contract (Pydantic), e2e (QCM → profile → 1er message tuteur personnalisé).
- [ ] Télémétrie dashboard alpha 2 semaines.

---

**Fin du design doc Vague 2 QCM.**
