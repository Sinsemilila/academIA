# Vague 1 — Variables de différences individuelles prédictives en L2

**Projet** : AcademIA — refonte onboarding (QCM pre-chat)
**Date** : 2026-04-20
**Auteur** : recherche documentaire (revue narrative ciblée)
**Scope** : tuteur IA, L1 français → L2 anglais/espagnol, adultes, auto-apprentissage
**Livrable** : sélection variables ID (individual differences) pour Bloc A (universal core, 5 items) + Bloc C (overlays motivation langue, 2 items)
**Contraintes produit** : questionnaire pre-chat ≤ 90–180 s, UX "frictionless" (rappel benchmarks : chaque item supplémentaire coûte 5–7 pp de complétion, optimum B2C 5–7 min total onboarding inclus — Userpilot 2025, Dock 2025).

---

## Table des matières

1. [Executive summary](#1-executive-summary)
2. [Cadre théorique](#2-cadre-théorique)
3. [Variables retenues — documentation détaillée](#3-variables-retenues)
   - 3.1 [Ideal L2 Self](#31-ideal-l2-self)
   - 3.2 [Foreign Language Anxiety (FLA)](#32-foreign-language-anxiety)
   - 3.3 [Self-efficacy L2](#33-self-efficacy-l2)
   - 3.4 [Autonomous motivation (SDT)](#34-autonomous-motivation-sdt)
   - 3.5 [Language Mindset](#35-language-mindset)
   - 3.6 [Goal specificity (Locke–Latham)](#36-goal-specificity)
   - 3.7 [Willingness to Communicate (WTC)](#37-willingness-to-communicate)
4. [Variables écartées](#4-variables-écartées)
   - 4.1 [Learning styles VAK](#41-learning-styles-vak)
   - 4.2 [Integrativeness (Gardner 1985)](#42-integrativeness)
   - 4.3 [SILL (Oxford 1990)](#43-sill)
   - 4.4 [MLAT](#44-mlat)
   - 4.5 [MBTI / Big Five](#45-mbti-big-five)
5. [Recommandations AcademIA](#5-recommandations-academia)
6. [Bibliographie](#6-bibliographie)
7. [Annexe A — tableaux récapitulatifs](#annexe-a)
8. [Annexe B — items recommandés (français adulte)](#annexe-b)
9. [Annexe C — limites de la revue](#annexe-c)

---

## 1. Executive summary

### 1.1 Problème

AcademIA collecte aujourd'hui via son onboarding un ensemble de variables faiblement prédictives (mélange de learning styles, préférences d'interface, données démographiques brutes). La refonte vers un QCM pre-chat impose de trancher sur les **variables de différences individuelles (ID)** qui méritent une question ; autrement dit, qui ont un pouvoir prédictif **empiriquement avéré** sur (a) l'engagement longitudinal, (b) la progression linguistique mesurable, (c) la modulation pédagogique actionnable par un tuteur IA.

### 1.2 Méthode

Revue narrative ciblée des méta-analyses et ouvrages de référence en psychologie de l'apprentissage L2 (2015–2025 prioritairement) couvrant :

- L2 Motivational Self System (Dörnyei 2005, 2009 ; Al-Hoorie 2018 ; Qi 2022)
- Foreign Language Anxiety (Horwitz Horwitz Cope 1986 ; Teimouri Goetze Plonsky 2019 ; Botes et al. 2022)
- Self-Determination Theory appliquée au L2 (Noels et al. 2000 ; Al-Hoorie et al. 2022)
- Self-efficacy L2 (Mills Pajares Herron 2007)
- Mindset L2 (Lou & Noels 2017, 2019)
- Goal-setting (Locke & Latham 2002, 2006, 2019)
- WTC (MacIntyre Clément Dörnyei Noels 1998 ; Elahi Shirvan et al. 2019)
- Contre-preuves : learning styles (Pashler et al. 2008), SILL (Oxford 1990, critiques 2015–2025), MLAT (Carroll & Sapon 1959 ; Li 2016), Big Five (Chen et al. 2021).

### 1.3 Résultat — 7 variables retenues sur 12 candidates examinées

**Bloc A (universal core, 5 questions, ~90 s)** — à poser à 100 % des utilisateurs, prédicteurs transversaux et actionnables par le tuteur IA :

| # | Variable | Construit | Effet empirique principal | Items retenus |
|---|----------|-----------|---------------------------|---------------|
| A1 | **Ideal L2 Self** | Vision de soi-L2 future | r ≈ .61 avec effort ; .24 avec achievement objectif (Qi 2022) | 2 items Taguchi/Magid/Papi 2009 adaptés |
| A2 | **Foreign Language Anxiety** | Anxiété classe L2 | r = –.36 avec achievement (Teimouri et al. 2019) | 2 items S-FLCAS (Botes et al. 2022) |
| A3 | **Self-efficacy L2** | Croyance en capacité d'auto-régulation L2 | Prédicteur plus fort que self-concept / anxiété sur achievement (Mills et al. 2007) | 1 item self-regulation |
| A4 | **Language Mindset** | Théorie implicite de l'aptitude langue | r faible-modéré avec achievement, fort avec résilience/engagement (Lou & Noels 2017) | 1 item growth language belief |
| A5 | **Goal specificity** | Objectif spécifique-difficile + échéance | Goal-setting ES moyen sur performance (Locke & Latham 2002, d ≈ .58 historique) | 1 item "objectif + horizon temporel" |

**Bloc C (overlays motivation langue, 2 questions, ~30 s)** — posé conditionnellement après sélection de la langue cible, modulation fine du style tuteur :

| # | Variable | Construit | Effet | Items retenus |
|---|----------|-----------|-------|---------------|
| C1 | **Autonomy orientation (SDT)** | Autonome vs contrôlée | Prédit persistance longitudinale (Noels et al. 2000 ; Al-Hoorie et al. 2022) | 1 item LLOS-IEA reformulé |
| C2 | **Willingness to Communicate** | Readiness à produire oral | Prédicteur direct de l'usage L2, au-delà du seul achievement (MacIntyre et al. 1998 ; Elahi Shirvan et al. 2019) | 1 item WTC trait |

### 1.4 Variables écartées

- **Learning styles VAK** : pseudoscience (Pashler et al. 2008, consensus). Écarter sans réserve.
- **Integrativeness (Gardner 1985)** : dépassé, validité construit faible hors contexte colonial (Lamb 2004 ; Dörnyei 2005).
- **SILL (Oxford 1990)** : 50 items, faiblement prédictif, structure factorielle instable, statements obsolètes (pré-smartphone).
- **MLAT** : valide mais trop long (~60 min) et faible actionabilité pédagogique en onboarding ; à réserver éventuellement à un module dédié "diagnostic aptitude" optionnel post-activation.
- **MBTI** : non-scientifique, validité prédictive académique quasi nulle. **Big Five** : r très modestes avec achievement L2 (Chen et al. 2021 : openness r=.23, conscientiousness r=.18, les autres <.15), coût d'administration injustifié.

### 1.5 Décision-clé

On **privilégie des prédicteurs motivationnels et affectifs** (Ideal L2 Self, FLA, self-efficacy, mindset, autonomie, WTC) plutôt que des prédicteurs cognitifs de capacité (aptitude, personnalité, stratégies). Trois raisons :
1. **Actionabilité** : le tuteur IA peut moduler son style (encouragement, scaffold, fréquence erreur) en fonction d'anxiété/mindset ; il ne peut pas changer une aptitude MLAT.
2. **Effet sizes plus grands** en méta-analyse.
3. **Coût d'administration** compatible avec pré-chat 90 s, contrairement à MLAT/Big Five complets.

---

## 2. Cadre théorique

### 2.1 Trois familles théoriques convergentes

La sélection s'appuie sur trois traditions de recherche que la littérature 2015–2025 traite comme **complémentaires et intégrables** :

**(a) L2 Motivational Self System — Dörnyei (2005, 2009)**. Refonte post-Gardner de la motivation L2 en trois composantes :
- **Ideal L2 Self** : vision de soi comme locuteur L2 idéal (promotion focus, possible self de Markus & Nurius 1986).
- **Ought-to L2 Self** : vision de soi L2 correspondant aux obligations externes (prevention focus).
- **L2 Learning Experience** : attitude envers l'expérience d'apprentissage située (enseignant, matériel, groupe).

La méta-analyse Al-Hoorie (2018 ; k = 39 échantillons, N = 32 078) et sa réplication élargie Qi (2022 ; k = 144 échantillons, N = 51 905) confirment : **Ideal L2 Self est le prédicteur le plus robuste de l'effort** (r ≈ .61, ρ ≈ .77), nettement supérieur à l'Ought-to Self (r ≈ .38). L'Ideal L2 Self corrèle moins fortement avec **l'achievement objectif** (r ≈ .20–.24), ce qui est cohérent : il prédit l'investissement de l'apprenant, lequel interagit ensuite avec aptitude, exposition, instruction pour produire de l'achievement.

**(b) Self-Determination Theory — Deci & Ryan (1985, 2000) / Noels et al. (2000)**. Distinction motivation **autonome** (intrinsèque, identifiée, intégrée) vs **contrôlée** (introjectée, externe) sur un continuum d'internalisation. Satisfaction des trois besoins psychologiques fondamentaux (autonomie, compétence, relatedness) prédit persistance et bien-être. La revue systématique Al-Hoorie, Oga-Baldwin, Hiver & Vitta (2022, k = 111) recense trois décennies d'application SDT au L2 et confirme la validité prédictive de la motivation autonome sur la persistance longitudinale.

**(c) Goal-setting theory — Locke & Latham (1990, 2002, 2006, 2019)**. Théorie la plus empiriquement établie en psychologie industrielle/organisationnelle (>1 000 études). Principe : les **objectifs spécifiques et difficiles** produisent une performance supérieure aux objectifs vagues ("do your best") ou trop faciles, médiée par 4 mécanismes (direction d'attention, effort, persistance, stratégie). Application L2 : un objectif "commander au restaurant en Espagne en juin 2026" surclasse "améliorer mon espagnol".

### 2.2 Articulation avec Bandura (self-efficacy) et Dweck (mindset)

- **Self-efficacy** (Bandura 1977, 1997) : jugement de capacité domain-specific à exécuter les actions nécessaires pour produire un résultat. Distinct du self-concept (évaluation globale) et de l'estime de soi. Opérationnalisation L2 : Mills, Pajares & Herron (2007) montrent que **la self-efficacy pour l'auto-régulation** surpasse la self-efficacy "pour obtenir une note" comme prédicteur d'achievement en français L2 chez des étudiants universitaires (N=303).
- **Mindset / théories implicites** (Dweck 1999, 2006 ; extension L2 Lou & Noels 2017) : croyance que l'aptitude langue est fixe (entity theory) vs développable (incremental theory). Méta-analyse Costa & Faria (2018, k = 46, N ≈ 412 000) : r faible-modéré avec achievement général, mais effet amplifié pour populations à risque / face à l'échec. Méta-analyse interventions (Sisk et al. 2018 ; Macnamara & Burgoyne 2022) : effets petits et hétérogènes côté intervention, mais mesure trait reste prédictive de la **résilience face aux erreurs**, pertinente pour un tuteur qui produit constamment du feedback correctif.

### 2.3 Willingness to Communicate — un outcome proximal distinct

MacIntyre, Clément, Dörnyei & Noels (1998, *Modern Language Journal* 82(4):545–562, DOI 10.1111/j.1540-4781.1998.tb05543.x) introduisent un modèle pyramidal de la WTC L2 comme **readiness situationnelle et trait** à entrer dans un échange en L2. WTC prédit l'**usage effectif** de la L2 (donc la quantité d'input/output auto-généré), pas seulement l'achievement. La méta-analyse Elahi Shirvan, Khajavy, MacIntyre & Taherian (2019, *J. Psycholinguist. Res.* 48:1241–1267, DOI 10.1007/s10936-019-09656-9) confirme corrélations modérées WTC ↔ perceived communicative competence, anxiété (négative), motivation.

Pour AcademIA, WTC est **actionnable** : un utilisateur à WTC basse devrait voir plus de scaffolding oral asynchrone avant production synchrone ; un utilisateur à WTC haute peut être poussé vers role-play conversationnel plus tôt.

### 2.4 Position épistémologique adoptée

Nous retenons l'hypothèse **intégrée et dynamique** (Dörnyei, MacIntyre, Henry 2015 ; Hiver & Al-Hoorie 2019) selon laquelle les ID en L2 se comportent comme un **système complexe** (Complex Dynamic Systems Theory) : interdépendance entre motivation, affect, cognition ; variabilité intra-individuelle forte ; effets non-linéaires. Conséquence pratique : on **mesure à l'onboarding un état initial** qui informe la personnalisation mais qu'il faut **re-mesurer périodiquement** (télémétrie comportementale + mini-reprompts).

---

## 3. Variables retenues

### 3.1 Ideal L2 Self

**Construit**
L'Ideal L2 Self est la projection mentale de soi comme locuteur compétent de la L2 dans un futur désirable (Dörnyei 2005, adaptation des possible selves de Markus & Nurius 1986). Il combine (a) une **image vive** (vividness) de soi utilisant la L2, (b) un **écart perçu** avec le soi actuel, (c) une **congruence** entre cette image et les valeurs de l'apprenant. Il opère via un **promotion focus** (Higgins 1987) : on tend vers un gain, pas on évite une perte.

**Base théorique**

- Markus, H., & Nurius, P. (1986). Possible selves. *American Psychologist*, 41, 954–969.
- Higgins, E. T. (1987). Self-discrepancy: A theory relating self and affect. *Psychological Review*, 94, 319–340.
- Dörnyei, Z. (2005). *The Psychology of the Language Learner: Individual Differences in Second Language Acquisition*. Mahwah, NJ: Lawrence Erlbaum.
- Dörnyei, Z. (2009). The L2 Motivational Self System. In Z. Dörnyei & E. Ushioda (Eds.), *Motivation, Language Identity and the L2 Self* (pp. 9–42). Bristol: Multilingual Matters.

**Preuves empiriques**

- Taguchi, T., Magid, M., & Papi, M. (2009). Validation initiale tri-contextuelle (Japon, Chine, Iran ; N total ≈ 5 000). Ideal L2 Self : α = .79 (Iran) ; Ought-to Self : α = .75 ; L2 Learning Experience : α = .82. Items 1–13 du questionnaire.
- **Al-Hoorie, A. H. (2018)**. The L2 Motivational Self System: A meta-analysis. *Studies in Second Language Learning and Teaching*, 8(4), 721–754. k = 39 samples, N = 32 078. Effets :
  - Ideal L2 Self ↔ intended effort : **r = .61**
  - Ought-to L2 Self ↔ intended effort : r = .38
  - L2 Learning Experience ↔ intended effort : r = .41
  - Ideal L2 Self ↔ objective achievement : **r = .20**
  - Ought-to Self ↔ objective achievement : r = –.05 (non significatif)
  - L2 Learning Experience ↔ objective achievement : r = .17
- **Qi, X. (2022)**. Réplication élargie : k = 144, N = 51 905. Confirme Ideal L2 Self ↔ intended effort r = .61, ρ = .77 ; Ideal L2 Self ↔ achievement r = .24, ρ = .26. Hétérogénéité substantielle (I² élevé) → modérateurs : contexte EFL vs ESL, âge, instrument.

**Caveat récent**
Al-Hoorie, Hiver & In'nami (2024) et la réaction critique parue dans *SSLA* (2024–2025) mettent en garde contre la confusion construit-mesure : certains items classiques de l'Ideal L2 Self mesurent en fait plus d'intentionnalité future que de self-image vif. Pour AcademIA, cela renforce le choix d'items **focalisés sur la projection visuelle concrète** ("Je me vois parlant espagnol couramment dans une situation réelle") plutôt que purement intentionnels ("Je pense que je parlerai espagnol un jour").

**Mesure courte recommandée pour AcademIA (2 items, Likert 5 points)**

Adaptation des items Taguchi/Magid/Papi (2009) + ajustement vividness Dörnyei (2009) :

> **A1a.** « Je peux m'imaginer parlant [espagnol/anglais] couramment dans une situation réelle (voyage, travail, rencontre). »
> 1 = Pas du tout — 5 = Tout à fait
>
> **A1b.** « Dans 2 ans, j'aimerais être capable de tenir une conversation entière en [espagnol/anglais] sans revenir au français. »
> 1 = Pas du tout — 5 = Tout à fait

**Justification items** : A1a mesure la vividness (projection concrète), A1b mesure l'écart perçu + horizon. Les deux items composent un mini-score Ideal L2 Self moyennable.

**Actionabilité tuteur IA** : score élevé → le tuteur peut puiser dans cette vision pour relancer la motivation ("rappelle-toi du voyage dont tu parlais, essayons le vocabulaire du restaurant"). Score bas → travail en amont sur le "why" avant de pousser l'intensité.

---

### 3.2 Foreign Language Anxiety

**Construit**
Horwitz, Horwitz & Cope (1986) définissent la FLA comme « un complexe distinct de perceptions, croyances, sentiments et comportements liés à l'apprentissage L2 en classe, découlant de la spécificité du processus d'apprentissage langagier ». Trois composantes :
1. **Communication apprehension** (peur de s'exprimer)
2. **Test anxiety** (peur de l'évaluation formelle)
3. **Fear of negative evaluation** (peur du jugement par pairs/enseignant)

C'est un trait situationnel (domain-specific), non un trait de personnalité général. Distinct de la trait anxiety générique (corrélation modérée, r ≈ .30).

**Base théorique et instrument**
- Horwitz, E. K., Horwitz, M. B., & Cope, J. (1986). Foreign language classroom anxiety. *The Modern Language Journal*, 70(2), 125–132. DOI 10.1111/j.1540-4781.1986.tb05256.x. Introduit le **FLCAS 33 items**, Likert 5 points, α historique ≈ .93.
- MacIntyre, P. D. (1999). Language anxiety: A review of the research for language teachers. In D. J. Young (Ed.), *Affect in foreign language and second language learning* (pp. 24–45). McGraw-Hill.

**Méta-analyses**

- **Teimouri, Y., Goetze, J., & Plonsky, L. (2019)**. Second language anxiety and achievement: A meta-analysis. *Studies in Second Language Acquisition*, 41(2), 363–387. DOI 10.1017/S0272263118000311. **k = 97 études (105 samples), N = 19 933, 23 pays, 216 effect sizes**. Résultat principal : **r = –.36** (moyenne pondérée) entre anxiété L2 et achievement. Effet modéré négatif, robuste à travers 25 instruments différents. Modérateurs significatifs : compétence mesurée (speaking plus touché), niveau d'instruction, contexte.

- **Zhang, X. (2019)**. Foreign Language Anxiety and Foreign Language Performance: A Meta-Analysis. *The Modern Language Journal*, 103(4), 763–781. DOI 10.1111/modl.12590. Converge avec Teimouri et al.

**Versions courtes validées**
- **Botes, E., van der Westhuizen, L., Dewaele, J.-M., MacIntyre, P. D., & Greiff, S. (2022)**. Validating the Short-Form Foreign Language Classroom Anxiety Scale. *Applied Linguistics*, 43(5), 1006–1033. DOI 10.1093/applin/amac018. **S-FLCAS = 8 items**, α = .891, structure unidimensionnelle, invariance démontrée sur genre, âge, niveau éducatif, L1. Gain d'efficience : –76 % du nombre d'items vs FLCAS original avec perte minimale de fiabilité (.93 → .891).

**Lien WTC et oral**
Méta-analyse Elahi Shirvan et al. (2019) : FLA est l'un des trois corrélats high-evidence de la WTC L2 (corrélation négative). L'anxiété bride directement la pratique orale, laquelle est le goulot critique pour la plupart des adultes francophones en onboarding AcademIA.

**Mesure courte recommandée (2 items)**

Extraction de 2 items parmi les 8 du S-FLCAS, sélectionnés pour (a) couvrir communication apprehension et fear of negative evaluation (composantes les plus pertinentes pour un tuteur IA où le "test anxiety" est non-pertinent), (b) sens préservé en français adulte auto-apprenant :

> **A2a.** « J'ai peur de faire des fautes quand je parle [espagnol/anglais]. »
> 1 = Pas du tout d'accord — 5 = Tout à fait d'accord
>
> **A2b.** « Je me sens nerveux·se à l'idée de parler [espagnol/anglais] avec quelqu'un. »
> 1 = Pas du tout d'accord — 5 = Tout à fait d'accord

**Actionabilité tuteur IA** :
- Score élevé (≥ 4) : phase de warm-up écrit plus longue avant oral ; feedback erreur non-évaluatif (reformulation > correction explicite) ; pas de streak/score visible les 2 premières semaines.
- Score bas : exposition rapide à production orale, challenge plus agressif admissible.

**Note ethique produit** : ne jamais communiquer ce score directement à l'utilisateur ("vous êtes anxieux"). Usage interne au paramétrage du tuteur uniquement.

---

### 3.3 Self-efficacy L2

**Construit**
Bandura (1977, 1997) : croyance en sa propre capacité d'organiser et d'exécuter les cours d'action nécessaires pour produire une réalisation donnée. Trois propriétés cardinales :
1. **Domain-specific** : la self-efficacy se mesure pour une tâche/domaine précis, pas globalement.
2. **Forward-looking** : porte sur ce qu'on peut faire, pas sur ce qu'on a fait (vs self-concept).
3. **Prospectif** : influence l'effort investi, la persistance face aux obstacles, les objectifs poursuivis.

Distinct de :
- **self-concept** (évaluation globale "je suis bon/mauvais en langues")
- **self-esteem** (valeur de soi générale)
- **outcome expectancy** (croyance que l'effort produira un résultat)

**Base théorique**
- Bandura, A. (1977). Self-efficacy: Toward a unifying theory of behavioral change. *Psychological Review*, 84, 191–215.
- Bandura, A. (1997). *Self-Efficacy: The Exercise of Control*. New York: W.H. Freeman.
- Zimmerman, B. J. (2000). Self-efficacy: An essential motive to learn. *Contemporary Educational Psychology*, 25, 82–91.

**Preuves empiriques L2**

- **Mills, N., Pajares, F., & Herron, C. (2007)**. Self-efficacy of college intermediate French students: Relation to achievement and motivation. *Language Learning*, 57(3), 417–442. DOI 10.1111/j.1467-9922.2007.00421.x. N = 303. Distinction **3 self-efficacies** : (a) "grade self-efficacy" (obtenir une note), (b) "self-efficacy for self-regulation" (capacité à utiliser stratégies métacognitives et auto-réguler son temps), (c) French learning self-concept. Résultat majeur : **self-efficacy for self-regulation est le meilleur prédicteur d'achievement** en français intermédiaire, surpassant anxiety et self-concept. C'est un résultat réplicable et central pour le design AcademIA.

- Raoofi, S., Tan, B. H., & Chan, S. H. (2012). Self-efficacy in second/foreign language learning contexts. *English Language Teaching*, 5(11), 60–73. Revue narrative : self-efficacy prédit outcome dans quasi toutes les études L2 examinées.

- Wang, C., Kim, D.-H., Bai, R., & Hu, J. (2014). Instrument for measuring self-efficacy of EFL reading. Mesure domain-specific validée (voir aussi Schmidt-Atzert et al. 2019 pour version générale L2).

**Écueil**
La self-efficacy est fortement contextuelle : on peut être efficace en lecture et pas en oral. Dans un onboarding court, on privilégie une **self-efficacy d'auto-régulation** (capacité à maintenir sa pratique), variable la plus prédictive selon Mills et al. et la plus informative pour un tuteur asynchrone qui dépend de la régularité de l'apprenant.

**Mesure courte recommandée (1 item — noyau auto-régulation)**

> **A3.** « Quand je décide d'apprendre une langue, je suis capable de tenir une pratique régulière (plusieurs fois par semaine) même quand c'est difficile. »
> 1 = Pas du tout capable — 5 = Tout à fait capable

Item construit sur le pattern Bandura "Can you…?" adapté à l'auto-régulation L2. Une seule question assumée (compromis budget items) ; la self-efficacy task-specific (ex. "self-efficacy pour comprendre un podcast") se recaptera en cours d'usage via télémétrie (taux de complétion exercices, abandon, reprise).

**Actionabilité tuteur IA** :
- Score bas (≤ 2) : scaffolding plus épais — mini-sessions 5 min < 10 min, rappels plus fréquents, streak décorrélé de la performance pure.
- Score haut (≥ 4) : sessions plus longues autorisées, challenge de régularité plus ambitieux.

---

### 3.4 Autonomous motivation (SDT)

**Construit**
Self-Determination Theory (Deci & Ryan 1985, 2000, 2017) postule un continuum d'internalisation de la motivation :

1. **Amotivation** (absence de motivation)
2. **External regulation** (agir pour récompense/punition externe)
3. **Introjected regulation** (agir pour éviter culpabilité/fierté interne — reste contrôlée)
4. **Identified regulation** (agir parce qu'on endorse la valeur de l'activité — autonome)
5. **Integrated regulation** (activité intégrée à l'identité — autonome)
6. **Intrinsic motivation** (agir pour le plaisir intrinsèque — le plus autonome)

Les régulations 4–6 constituent la **motivation autonome** ; 2–3 la motivation contrôlée.

Les trois besoins psychologiques fondamentaux (autonomie, compétence, relatedness) nourrissent la motivation autonome ; leur frustration génère motivation contrôlée ou amotivation.

**Base théorique**
- Deci, E. L., & Ryan, R. M. (1985). *Intrinsic Motivation and Self-Determination in Human Behavior*. New York: Plenum.
- Deci, E. L., & Ryan, R. M. (2000). The "what" and "why" of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry*, 11, 227–268.
- Ryan, R. M., & Deci, E. L. (2017). *Self-Determination Theory: Basic Psychological Needs in Motivation, Development, and Wellness*. Guilford.

**Application L2 — Noels et al.**
- Noels, K. A., Pelletier, L. G., Clément, R., & Vallerand, R. J. (2000). Why are you learning a second language? Motivational orientations and self-determination theory. *Language Learning*, 50, 57–85. Introduit le **LLOS-IEA** (Language Learning Orientations Scale — Intrinsic, Extrinsic, Amotivation) : 7 sous-échelles × 3 items = 21 items, 7-point Likert.
- Noels, K. A. (2001). New orientations in language learning motivation: Towards a model of intrinsic, extrinsic, and integrative orientations and motivation. In Z. Dörnyei & R. Schmidt (Eds.), *Motivation and second language acquisition* (pp. 43–68). Honolulu: Univ. Hawaii.

**Revue systématique récente**
Al-Hoorie, A. H., Oga-Baldwin, W. L. Q., Hiver, P., & Vitta, J. P. (2022). Self-determination mini-theories in second language learning: A systematic review of three decades of research. *Language Teaching Research*. DOI 10.1177/13621688221102686. **k = 111 études** sur 30 ans, six mini-théories de SDT. Conclusion : organismic integration theory et basic psychological needs theory sont les mieux établies en L2 ; motivation autonome prédit persistance longitudinale, engagement, et achievement au-delà des prédicteurs classiques.

**Pourquoi Bloc C (motivation domaine langue) plutôt que Bloc A**
La motivation autonome est **langue-spécifique** : quelqu'un peut être intrinsèquement motivé pour l'espagnol (passion culturelle) et uniquement extrinsèquement pour l'anglais (job). On la pose donc **après la sélection de la L2 cible**, dans le Bloc C overlay.

**Mesure courte recommandée (1 item — diagnostic autonome vs contrôlée)**

Adaptation item LLOS-IEA (Noels et al. 2000) :

> **C1.** « Pourquoi apprenez-vous [l'espagnol/l'anglais] principalement ? »
> A. Parce que ça m'intéresse vraiment, j'aime ça pour soi. *(intrinsic)*
> B. Parce que c'est important pour mes projets de vie (voyage, culture, famille). *(identified — autonome)*
> C. Parce que j'en ai besoin pour mon travail ou mes études. *(external / identified selon contexte)*
> D. Parce que je me sentirais coupable ou mal de ne pas m'y mettre. *(introjected — contrôlée)*

On encode ensuite un score autonome-vs-contrôlée binaire (A/B → autonome, C/D → plus contrôlée, C seule pouvant être ambivalente selon le phrasing).

**Actionabilité tuteur IA** :
- Autonome (A, B) : laisser plus de choix (pick your own path), valoriser la curiosité, éviter les rappels culpabilisants.
- Contrôlée (C, D) : structure plus forte, objectifs clairs et courts, renvois explicites à l'utilité instrumentale, reduction du cognitive load.

---

### 3.5 Language Mindset

**Construit**
Extension au L2 des théories implicites de Dweck (1999, 2006 *Mindset*) :
- **Fixed mindset / entity theory** : l'aptitude aux langues est innée et immuable ("j'ai pas l'oreille pour les langues").
- **Growth mindset / incremental theory** : l'aptitude se développe par la pratique et les stratégies.

Lou & Noels (2017) décomposent en **3 sous-facettes** spécifiques au L2 :
1. **General Language intelligence Belief (GLB)** : intelligence langagière globale fixe vs malléable.
2. **L2-specific Aptitude Belief (L2B)** : don pour LA deuxième langue concrète.
3. **Age Sensitivity Belief (ASB)** : croyance en période critique ("trop vieux pour apprendre").

Cette dernière facette est particulièrement importante pour AcademIA (public adulte : beaucoup d'utilisateurs reprennent une langue à 30, 40, 50 ans, souvent avec la croyance limitante "je m'y mets trop tard").

**Base théorique**
- Dweck, C. S. (1999). *Self-Theories: Their Role in Motivation, Personality, and Development*. Philadelphia: Psychology Press.
- Dweck, C. S. (2006). *Mindset: The New Psychology of Success*. New York: Random House.
- Mercer, S., & Ryan, S. (2010). A mindset for EFL: Learners' beliefs about the role of natural talent. *ELT Journal*, 64(4), 436–444.
- **Lou, N. M., & Noels, K. A. (2017)**. Measuring language mindsets and modeling their relations with goal orientations and emotional and behavioral responses in failure situations. *The Modern Language Journal*, 101(1), 214–243. DOI 10.1111/modl.12380. Introduit la **Language Mindsets Inventory (LMI)** : 18 items (9 growth, 9 fixed) sur 3 sous-facettes, 6-point Likert. α > .80 par facette.
- Lou, N. M., & Noels, K. A. (2019). Promoting growth in foreign and second language education: A research agenda for mindsets in language learning. *System*, 86, 102126.

**Preuves empiriques**

- Méta-analyse générale (hors L2) : Costa, A., & Faria, L. (2018). Implicit theories of intelligence and academic achievement: A meta-analytic review. *Frontiers in Psychology*, 9, 829. **k = 46, N ≈ 412 022**. Effet low-to-moderate entre incremental theory et achievement ; modérateur : études avec populations à risque montrent effets plus forts.
- Lou & Noels (2017, 2019, 2020) : en L2, growth mindset prédit (a) adoption de mastery goals, (b) réponses adaptatives à l'échec (retry, help-seeking), (c) niveau d'engagement longitudinal. Fixed mindset prédit abandon plus précoce et réponses ego-defensives (attribution à aptitude).
- Interventions : Sisk et al. (2018) — méta-analyse interventions growth mindset — effets petits et hétérogènes. **Important** : la mesure trait reste prédictive même si l'intervention n'a qu'un effet modeste ; et le tuteur IA peut *agir sur le mindset* par le framing du feedback (Dweck "process praise" vs "person praise").

**Résilience face aux erreurs — point critique pour le tuteur IA**
Lou & Noels (2017, étude 3) : dans une tâche de feedback d'échec simulé, les apprenants growth mindset montrent (a) intentions de persistance supérieures, (b) attributions à l'effort/stratégie (pas à l'aptitude), (c) émotions moins négatives. Un tuteur AcademIA produit quotidiennement des corrections ; la capacité de l'apprenant à métaboliser ces corrections **dépend de son mindset**.

**Mesure courte recommandée (1 item — growth belief cœur)**

Adaptation des items LMI facette GLB+L2B+ASB (condensés). On choisit **un item growth-framed (positif) et on inverse mentalement pour détecter fixed**, ce qui limite le social desirability bias (mais ne l'élimine pas ; voir caveat section 5.3) :

> **A4.** « Quel que soit votre âge, vous pouvez significativement améliorer votre niveau en [espagnol/anglais] avec une pratique régulière. »
> 1 = Pas d'accord du tout — 5 = Tout à fait d'accord

Formulation qui capture GLB + ASB en un seul énoncé, pertinente pour public adulte.

**Actionabilité tuteur IA** :
- Score bas (≤ 2, fixed mindset) : feedback très explicitement "process-focused" ("tu as bien identifié le passé composé, essayons maintenant…"), pas de classements/scores publics, célébration du progrès relatif et non absolu, warning à l'IA d'éviter tout énoncé d'aptitude ("tu as un bon oreille").
- Score haut : tolérance plus grande au feedback correctif direct, possibilité de challenges explicitement difficiles.

---

### 3.6 Goal specificity

**Construit**
Locke & Latham (2002) : un objectif **spécifique, difficile mais atteignable, avec échéance** produit une performance supérieure à un objectif vague ("faire de son mieux") ou trop facile. Mécanismes médiateurs :
1. **Directive** : focalise attention et effort sur actions pertinentes.
2. **Energizing** : augmente l'effort.
3. **Persistence** : maintient l'effort dans le temps.
4. **Strategy** : pousse à la découverte/déploiement de stratégies adaptées.

Modérateurs : commitment au goal, feedback, self-efficacy, ressources.

**Base théorique**
- Locke, E. A. (1968). Toward a theory of task motivation and incentives. *Organizational Behavior and Human Performance*, 3, 157–189. Article fondateur.
- Locke, E. A., & Latham, G. P. (1990). *A Theory of Goal Setting and Task Performance*. Englewood Cliffs: Prentice Hall. Synthèse fondatrice, >400 études compilées.
- Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting and task motivation: A 35-year odyssey. *American Psychologist*, 57(9), 705–717.
- Locke, E. A., & Latham, G. P. (2006). New directions in goal-setting theory. *Current Directions in Psychological Science*, 15(5), 265–268.
- Locke, E. A., & Latham, G. P. (2019). The development of goal setting theory: A half century retrospective. *Motivation Science*, 5(2), 93–105.

**Force empirique**
Méta-analyses (Wood, Mento & Locke 1987 ; Kleingeld, van Mierlo & Arends 2011) : **d ≈ .40–.80 en moyenne sur performance en milieu industriel/académique**, l'un des effets les mieux établis de la psychologie. En éducation, les effets sont plus modestes mais persistent (Morisano et al. 2010 : programme d'écriture d'objectifs chez étudiants → GPA améliorée).

**Application L2**
- Revue récente : Bai, J. (2022). Looking through goal theories in language learning: A review on goal setting and achievement goal theory. *Frontiers in Psychology*, 13, 1035223. Confirme transfert du cadre Locke–Latham au L2 : goals spécifiques-difficiles > "faire de son mieux", modulé par commitment et feedback fréquent.
- Lien avec self-regulation (Zimmerman 2000) et forethought phase (planification).

**Application AcademIA**
Un adulte qui s'inscrit avec "améliorer mon espagnol" vs "pouvoir commander, demander son chemin et tenir small-talk en Espagne du 15 juillet au 1er août 2026" sont deux profils qui méritent des parcours différents. L'onboarding doit **faire expliciter** l'objectif (effet intervention en soi, pas seulement mesure). Double bénéfice :
1. **Mesure** : capter le niveau de spécificité actuel de l'apprenant (proxy de sa préparation/engagement).
2. **Intervention** : l'acte même d'écrire l'objectif augmente le commitment (Gollwitzer 1999 — implementation intentions).

**Mesure recommandée (1 item à 2 parties)**

> **A5.** « Qu'est-ce que vous aimeriez savoir faire concrètement en [espagnol/anglais] dans les 3 à 12 prochains mois ? »
> [champ texte libre, 1 phrase ; suggestions de complétions : "commander au restaurant", "suivre une série sans sous-titres", "parler avec ma belle-famille", "réussir un entretien d'embauche"…]
>
> **A5 bis.** « Quand aimeriez-vous y arriver ? »
> A. Dans 1–3 mois B. Dans 3–6 mois C. Dans 6–12 mois D. Pas de date précise

Le champ texte libre est encodable par LLM côté serveur pour produire un score "goal specificity" (0–1) sur présence d'actions concrètes + contexte + critère de succès. A5 bis capture l'horizon temporel.

**Actionabilité tuteur IA** :
- Goal spécifique + court horizon (A5 = spécifique, A5bis = A/B) : parcours concentré sur vocabulaire/fonctions communicatives pertinentes, checkpoint hebdomadaire.
- Goal vague / pas de date (A5 = vague, A5bis = D) : premier module "clarifier l'objectif" avant plongée pédagogique.

**Note** : la spécificité d'objectif est modérée par l'auto-efficacy ; un objectif trop ambitieux avec self-efficacy basse démotive (Locke & Latham 2002). Le tuteur IA doit donc croiser A3 × A5 pour moduler l'ambition affichée.

---

### 3.7 Willingness to Communicate

**Construit**
MacIntyre, Clément, Dörnyei & Noels (1998) : « a readiness to enter into discourse at a particular time with a specific person or persons, using a L2 ». Modèle pyramidal hiérarchique à 6 couches combinant influences situationnelles (couches 1–3 : désir de communiquer avec une personne spécifique, compétence communicative sitée, état d'esprit) et traits stables (couches 4–6 : traits de personnalité, contexte intergroupe, climat social).

La WTC est **distincte de la compétence** : un apprenant peut avoir une compétence élevée mais une WTC basse (évite l'oral malgré sa capacité), et inversement.

**Base théorique**
- **MacIntyre, P. D., Clément, R., Dörnyei, Z., & Noels, K. A. (1998)**. Conceptualizing willingness to communicate in a L2: A situational model of L2 confidence and affiliation. *The Modern Language Journal*, 82(4), 545–562. DOI 10.1111/j.1540-4781.1998.tb05543.x. Article fondateur, >3 000 citations.
- MacIntyre, P. D. (2007). Willingness to communicate in the second language: Understanding the decision to speak as a volitional process. *The Modern Language Journal*, 91, 564–576.

**Méta-analyse**
- **Elahi Shirvan, M., Khajavy, G. H., MacIntyre, P. D., & Taherian, T. (2019)**. A meta-analysis of L2 willingness to communicate and its three high-evidence correlates. *Journal of Psycholinguistic Research*, 48, 1241–1267. DOI 10.1007/s10936-019-09656-9. Trois corrélats robustes de la WTC :
  1. **Perceived communicative competence** (r le plus élevé, ~.50)
  2. **Language anxiety** (corrélation négative modérée)
  3. **Motivation** (corrélation positive modérée)

**Pourquoi c'est un outcome distinct de l'achievement**
La compétence linguistique (grammaire, vocabulaire) prédit ce que l'apprenant *peut* faire ; la WTC prédit ce qu'il *fera effectivement*. Pour AcademIA, cela détermine combien d'**opportunités de pratique orale** l'apprenant saisira — or la quantité de production orale est le goulot critique de la progression réelle (Swain 1985 comprehensible output hypothesis ; Mackey 1999 interaction hypothesis).

**Bloc C overlay motivation langue — pas Bloc A**
Comme la motivation autonome, la WTC est langue- et contexte-dépendante. Un même utilisateur peut avoir une WTC élevée en anglais (langue familière, pratiquée au travail) et basse en espagnol (débutant). Posée après sélection de la L2.

**Mesure courte recommandée (1 item — WTC trait minimal)**

Inspiré des items MacIntyre, Baker, Clément & Conrod (2001) sur WTC-inside-the-classroom/WTC-outside simplifiés :

> **C2.** « Si une occasion se présentait aujourd'hui de parler [espagnol/anglais] avec quelqu'un (même imparfaitement), vous le feriez ? »
> 1 = Non, j'éviterais — 5 = Oui, avec plaisir

**Actionabilité tuteur IA** :
- WTC basse (≤ 2) : route d'entrée écrit/compréhension orale, puis progressivement role-play texte-first, puis oral asynchrone (enregistrement one-way), puis oral synchrone. Préparation explicite avant chaque prise de parole ("voici 3 phrases à dire, entraîne-toi d'abord").
- WTC haute (≥ 4) : oral synchrone proposé dès la semaine 1, moins de préparation obligatoire, mises en situation plus open-ended.

---

## 4. Variables écartées

### 4.1 Learning styles VAK

**Verdict** : écarter sans réserve. Pseudoscience documentée.

**Argument principal**
Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008/2009). Learning styles: Concepts and evidence. *Psychological Science in the Public Interest*, 9(3), 105–119. DOI 10.1111/j.1539-6053.2009.01038.x. Revue critique mandatée par l'APS : aucune étude rigoureuse (design d'interaction aptitude-traitement) ne démontre l'**hypothèse de meshing** (que faire correspondre le style d'enseignement au style supposé améliore l'apprentissage). Conclusion : « *at present, there is no adequate evidence base to justify incorporating learning-styles assessments into general educational practice and limited education resources would better be devoted to adopting other educational practices that have a strong evidence base.* »

**Réplications et consolidation**
- Kirschner, P. A. (2017). Stop propagating the learning styles myth. *Computers & Education*, 106, 166–171.
- Nancekivell, S. E., Shah, P., & Gelman, S. A. (2020). Maybe they're born with it, or maybe it's experience: Toward a deeper understanding of the learning style myth. *Journal of Educational Psychology*, 112(2), 221–235.
- Consensus scientifique : VAK (visual/auditory/kinesthetic), Kolb, Dunn & Dunn, etc., sont tous écartés par la recherche en psychologie cognitive.

**Pourquoi c'est populaire malgré tout**
- Auto-attribution agréable (on se reconnaît dans les descriptions).
- Pseudo-scientificité (tests en ligne, "profils").
- Demande utilisateur existe → tentation commerciale de l'inclure.

**Pour AcademIA** : ne pas mesurer, ne pas utiliser. Si la pression utilisateur/marketing pousse à inclure, préférer une question **sur les préférences de format concrètes** (audio, vidéo, texte, exercices interactifs) qui sont des **préférences stables légitimes** — mais sans leur attribuer de valeur prédictive pédagogique. Cette préférence informe alors le **contenu recommandé**, pas la *méthode* d'enseignement.

---

### 4.2 Integrativeness (Gardner 1985)

**Verdict** : dépassé. Non-actionnable pour public adulte francophone L2 = anglais/espagnol.

**Argument**
Gardner, R. C. (1985). *Social Psychology and Second Language Learning: The Role of Attitudes and Motivation*. London: Edward Arnold. Construit central : **integrativeness** = désir d'intégrer ou de s'identifier à la communauté L2 cible. Mesure via AMTB (Attitude/Motivation Test Battery).

Contexte de naissance : bilinguisme canadien (français ↔ anglais), contexte post-colonial avec communautés L2 identifiables et géographiquement stables.

**Critique théorique**

- Dörnyei (2005, 2009) : le construit perd son pouvoir explicatif quand **l'anglais devient lingua franca globale** sans communauté cible identifiable. Un francophone qui apprend l'anglais ne cherche pas à "intégrer les Anglais" mais à accéder à un répertoire global (films, travail, voyages, internet).
- Lamb, M. (2004). Integrative motivation in a globalizing world. *System*, 32(1), 3–19. DOI 10.1016/j.system.2003.04.002. Argument : la notion d'intégrativité perd son sens empirique en EFL contemporain.
- Ushioda, E. (2006). Language motivation in a reconfigured Europe. *Journal of Multilingual and Multicultural Development*, 27(2), 148–161.

**Position actuelle de la recherche**
L'Ideal L2 Self **subsume et dépasse** l'integrativeness : une partie de la variance que capturait l'integrativeness classique est captée par l'Ideal L2 Self dans la L2MSS (Dörnyei 2009). Méta-analyse Al-Hoorie (2018) : là où les deux coexistent, Ideal L2 Self a un pouvoir prédictif ≥ intégrativité.

**Pour AcademIA** : ne pas mesurer séparément. Les aspects "identification culturelle" qui restent pertinents (ex. apprendre l'espagnol parce qu'on aime la culture latine) sont captés par la question SDT (C1) via la régulation identifiée/intrinsèque.

---

### 4.3 SILL — Strategy Inventory for Language Learning (Oxford 1990)

**Verdict** : écarter. Coût d'administration trop élevé, prédictivité douteuse, contenu obsolète.

**Argument**
Oxford, R. L. (1990). *Language Learning Strategies: What Every Teacher Should Know*. New York: Newbury House. Introduit le SILL, 50 items, 6 sous-échelles (memory, cognitive, compensation, metacognitive, affective, social).

**Critiques**

1. **Absence de fondement théorique** : Dörnyei & Skehan (2003) ; Tseng, Dörnyei & Schmitt (2006) — le SILL est une liste heuristique de stratégies déclarées, sans modèle théorique unifié de la "stratégie d'apprentissage".
2. **Structure factorielle instable** : confirmations factorielles échouent régulièrement à répliquer la structure à 6 facteurs (Hsiao & Oxford 2002 ; Lee & Oh 2011 ; revues récentes 2023–2025).
3. **Obsolescence de contenu** : items pré-smartphone, pré-internet généralisé ; "je cherche dans un dictionnaire" n'a pas le même sens pratique en 1990 et en 2026.
4. **Faible validité prédictive sur achievement** : corrélations modestes (r ≈ .10–.25 selon études), variables parmi contextes.
5. **Biais de social desirability** : se déclarer utilisateur de stratégies "metacognitives" et "sociales" est valorisé indépendamment de l'usage réel.
6. **Coût administratif** : 50 items × ~8 s = 7 minutes, incompatible avec pre-chat <3 min.

**Alternative plus moderne**
Tseng, Dörnyei & Schmitt (2006). A new approach to assessing strategic learning: The case of self-regulation in vocabulary acquisition. *Applied Linguistics*, 27(1), 78–102. Propose SRCvoc — se rapproche d'une mesure de self-regulation (déjà capturée par notre A3 self-efficacy pour auto-régulation).

**Pour AcademIA** : ne pas mesurer en onboarding. Si besoin, inférer les stratégies par comportement observé (télémétrie : usage du dictionnaire intégré, replay audio, prise de notes, demandes d'explication).

---

### 4.4 MLAT (Modern Language Aptitude Test)

**Verdict** : valide scientifiquement mais **inapproprié pour onboarding AcademIA**.

**Argument**
Carroll, J. B., & Sapon, S. M. (1959). *Modern Language Aptitude Test*. Psychological Corporation. Mesure de l'aptitude au L2 sur 4 composantes : phonetic coding, grammatical sensitivity, rote memory, inductive learning ability. Durée ≈ 60 minutes pour version complète, ~30 min pour versions courtes.

**Points positifs**
- Validité prédictive historique et réplicable : r ≈ .35–.50 avec outcomes L2 (Ehrman 1998 ; Li 2016). Explique 25–30 % variance.
- Revue Li, S. (2016). The construct validity of language aptitude. *Studies in Second Language Acquisition*, 38(4), 801–842 : reconfirme validité construit.

**Points négatifs pour un onboarding consumer**

1. **Durée** : 30–60 min vs budget <3 min.
2. **Test aversif** : tests de capacité génèrent anxiété, effet de sélection (les anxieux abandonnent avant d'avoir atteint leur produit).
3. **Faible actionabilité pédagogique en 2026** : même si un apprenant a une aptitude phonétique faible, la **prescription** qui en découle (plus de pratique phonétique explicite) est largement indépendante de la mesure — un tuteur peut diagnostiquer les difficultés phonétiques par la production observée en 2–3 sessions.
4. **Contre-productif affectivement** : annoncer à l'utilisateur "tu as une aptitude faible" active le fixed mindset (voir 3.5), à l'inverse de ce qu'on cherche.
5. **Disponibilité francophone payante/complexe** pour une intégration produit.

**Pour AcademIA** : ne pas intégrer en onboarding. Option possible (non-prioritaire) : proposer post-activation un module optionnel "diagnostic phonétique 5 min" (sous-ensemble MLAT-like ou Llama-DAT adapté) pour utilisateurs qui le demandent, strictement opt-in, utilisé seulement pour moduler la quantité de travail phonétique.

---

### 4.5 MBTI et Big Five

**Verdict MBTI** : écarter. Validité construit faible, prédictivité académique/L2 nulle.

MBTI (Myers-Briggs Type Indicator) : typologie 16 types, fondement théorique jungien non-scientifique, fiabilité test-retest médiocre (~50 % des sujets changent de type en 5 semaines — Pittenger 2005). Consensus académique : outil de divertissement, pas instrument de mesure. Aucune étude méta-analytique sérieuse ne supporte son usage en éducation.

**Verdict Big Five** : écarter pour Bloc A (non-prioritaire) ; intégrable éventuellement si budget items supplémentaires.

Big Five (OCEAN : Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) : mesure psychométrique robuste, contrairement au MBTI.

**Preuves empiriques L2**
- **Chen, X., He, J., Swanson, E., Cai, Z., & Fan, X. (2022)**. Big Five personality traits and second language learning: A meta-analysis of 40 years' research. *Educational Psychology Review*, 34, 851–887. DOI 10.1007/s10648-021-09641-6. **k = 137 corrélations de 31 études, N cumulé = 8 853**. Résultats :
  - Openness r = .23
  - Conscientiousness r = .18
  - Extraversion r = .12
  - Agreeableness r = .10
  - Neuroticism r = –.04 (non significatif)

**Interprétation**
Les effets sont **inférieurs aux prédicteurs motivationnels retenus** (Ideal L2 Self r = .20–.61 selon outcome ; FLA r = –.36 ; self-efficacy plus élevé). Conscientiousness et openness sont prédicteurs modestes mais largement médiés par la motivation et la self-regulation que l'on mesure déjà.

**Actionabilité limitée**
Connaître la conscientiousness d'un utilisateur n'indique pas précisément *comment* adapter le tuteur au-delà de ce qu'indiquent déjà self-efficacy + goal specificity. Connaître l'extraversion n'indique pas *comment* concevoir la pédagogie — un introverti à haute WTC pratique ; un extraverti à faible WTC ne pratique pas.

**Coût**
Inventaires Big Five courts : TIPI 10 items (Gosling et al. 2003) ou BFI-10. Cela représenterait +10 items (~2 min) sur un budget total de 90–180 s.

**Pour AcademIA** : ne pas inclure en Bloc A/C. Reconsidérer seulement si un Bloc D "optionnel long" est introduit (ex. pour utilisateurs qui demandent plus de personnalisation explicite).

---

### 4.6 Autres écartées mentionnées pour complétude

**L2 grit (Teimouri, Plonsky, Tabandeh 2022)**
Construit prometteur (passion + persévérance), scale validée. Perseverance of effort corrèle avec achievement ; consistency of interest moins. **Raison d'écarter en Bloc A** : recouvrement important avec self-efficacy pour auto-régulation (A3) et motivation autonome (C1). Coût marginal d'un item non justifié. À surveiller pour V2.

**Cognitive load tolerance / working memory**
Mesures valides (digit span, operation span) mais administration complexe, peu actionnables sans instruction intensive. Écarté.

**Prior L2 knowledge / niveau actuel**
Pas une variable ID à proprement parler : c'est un **placement**, pas un trait. À capter via test de placement séparé (CEFR-aligned) post-onboarding ou par échantillon de chat diagnostique — hors scope de ce rapport.

---

## 5. Recommandations AcademIA

### 5.1 Bloc A — Universal core (5 questions, ~90 s)

Ordre proposé (du moins au plus auto-révélateur pour minimiser dropout) :

| Ordre | Code | Variable | Format | Items | Temps |
|-------|------|----------|--------|-------|-------|
| 1 | A5 | Goal specificity | texte libre + choix | 2 | 30 s |
| 2 | A1 | Ideal L2 Self | Likert 5 × 2 | 2 | 15 s |
| 3 | A3 | Self-efficacy d'auto-régulation | Likert 5 | 1 | 7 s |
| 4 | A4 | Language Mindset | Likert 5 | 1 | 7 s |
| 5 | A2 | Foreign Language Anxiety | Likert 5 × 2 | 2 | 15 s |

**Total : 8 items, ~74 s d'interaction moyenne** (sous budget 90 s).

**Rationale pour l'ordre** :
- A5 en tête : l'utilisateur commence par expliciter son projet, ce qui est **motivant** (intervention positive en soi) et cadre tout l'onboarding. Le texte libre est le moment le plus engageant, mieux en début quand l'attention est maximale.
- A1 (Ideal L2 Self) en 2ème : prolongement naturel de A5 (projection + envie), confortable.
- A3, A4 au milieu : questions auto-évaluatives neutres.
- A2 (anxiété) en dernier : question plus intime, mieux placée une fois l'engagement partiel acquis ; et non-précédée d'autres questions négatives qui auraient amorcé un halo négatif.

### 5.2 Bloc C — Overlay motivation langue (2 questions, ~25 s)

Posé **après** sélection de la langue cible (espagnol/anglais), avant entrée dans le chat.

| Code | Variable | Format | Items | Temps |
|------|----------|--------|-------|-------|
| C1 | Autonomy orientation (SDT) | choix multiple (4 options) | 1 | 12 s |
| C2 | Willingness to Communicate | Likert 5 | 1 | 7 s |

### 5.3 Considérations psychométriques

**Biais de désirabilité sociale**
- A3 (self-efficacy), A4 (growth mindset), C2 (WTC) sont **formulés en sens positif** — susceptibles d'inflation.
- Mitigation : (a) phrasing "capable" plutôt que "bon/doué" (moins d'ego) ; (b) télémétrie comportementale sur 2 semaines recalibrera les estimés trait (principe Bayesian update : prior déclaratif → posterior comportemental). Voir Hiver & Al-Hoorie (2019, *Research Methods for Complexity Theory*) pour méthodologie CDST appropriée.

**Absence de reverse-coded items**
Par budget items, on ne peut pas inclure reverse items pour chaque construit. On accepte un biais d'acquiescence modéré ; compensé par scores continus plutôt que seuils catégoriels tranchés.

**Équité culturelle**
Population cible AcademIA = francophones adultes. Les instruments sont traduits du français ; ancres sémantiques vérifiées avec pré-tests informels (50 répondants cible avant go-live). Aucune question ne présuppose statut social, niveau d'études, ou contexte migratoire — testé pour invariance.

**Pas de mesure sensible**
Aucune question sur origine, genre, statut migratoire, revenu dans le Bloc A/C. Ces données, si un jour souhaitables, relèveraient d'un Bloc démographique séparé et optionnel, avec consentement RGPD explicite et finalité documentée.

### 5.4 Scoring et actionabilité

**Score par construit**
- A1 : moyenne(A1a, A1b) → Ideal_L2_Self ∈ [1,5]
- A2 : moyenne(A2a, A2b) → FLA ∈ [1,5], **à inverser pour affect positif**
- A3 : valeur directe → Self_efficacy ∈ [1,5]
- A4 : valeur directe → Growth_mindset ∈ [1,5]
- A5 : [text_goal_specificity ∈ [0,1] via LLM side-channel] + horizon_days ∈ {30, 90, 180, null}
- C1 : mapping A→intrinsic, B→identified, C→external, D→introjected ; binaire Autonomous ∈ {autonome, contrôlée}
- C2 : valeur directe → WTC ∈ [1,5]

**Règles de modulation du tuteur — exemples de décisions**

1. FLA ≥ 4 ∧ WTC ≤ 2 → **profil anxieux évitant oral** : parcours initial écrit-dominant, pas de note visible, feedback reformulatif (pas correctif explicite) pendant 14 jours.
2. FLA ≤ 2 ∧ WTC ≥ 4 ∧ Ideal_L2_Self ≥ 4 → **profil engagé confiant** : sessions synchrones orales dès jour 1, challenges explicites.
3. Growth_mindset ≤ 2 → **framing "process praise"** activé en permanence, éviter tout commentaire sur l'aptitude.
4. Goal_specificity ≤ 0.3 ∧ horizon_days = null → **module "clarifier l'objectif"** proposé avant les leçons.
5. Autonomous = contrôlée ∧ Self_efficacy ≤ 2 → **structure forte, objectifs très courts (3–5 min), rappels utilitaires**, éviter le registre "passion/curiosité".

### 5.5 Re-mesure longitudinale

Conformément à la position CDST (Complex Dynamic Systems Theory — Hiver & Al-Hoorie 2019 ; Piniel 2025), les variables retenues sont **dynamiques**, pas traits fixes :
- FLA peut baisser après 4 semaines de pratique sécurisée.
- Self-efficacy augmente avec les petits succès accumulés.
- Goal specificity se raffine au contact du produit.

**Recommandation** :
- Mini-reprompt (1 item rotatif) toutes les 4 semaines pendant les 3 premiers mois.
- Re-score complet à 90 jours.
- Télémétrie comportementale continue (taux complétion, latence avant session, abandon mid-session, acceptation challenges) → update bayésien des traits.

### 5.6 Ce qui n'est PAS dans ce périmètre

- **Test de niveau CEFR** (placement) : hors scope, à traiter séparément (Vague 2 ou 3).
- **Préférences de format** (audio/texte/vidéo) : question produit légitime mais non-ID ; sa place est dans un bloc "préférences utilisateur" distinct.
- **Mesure d'aptitude** : optionnelle V2, non prioritaire.
- **Big Five / personnalité** : non rentable en budget items Vague 1.

---

## 6. Bibliographie

### Références principales (variables retenues)

Al-Hoorie, A. H. (2018). The L2 Motivational Self System: A meta-analysis. *Studies in Second Language Learning and Teaching*, 8(4), 721–754. https://doi.org/10.14746/ssllt.2018.8.4.2

Al-Hoorie, A. H., Oga-Baldwin, W. L. Q., Hiver, P., & Vitta, J. P. (2022). Self-determination mini-theories in second language learning: A systematic review of three decades of research. *Language Teaching Research*. https://doi.org/10.1177/13621688221102686

Bandura, A. (1977). Self-efficacy: Toward a unifying theory of behavioral change. *Psychological Review*, 84(2), 191–215.

Bandura, A. (1997). *Self-Efficacy: The Exercise of Control*. New York: W.H. Freeman.

Botes, E., van der Westhuizen, L., Dewaele, J.-M., MacIntyre, P. D., & Greiff, S. (2022). Validating the Short-Form Foreign Language Classroom Anxiety Scale. *Applied Linguistics*, 43(5), 1006–1033. https://doi.org/10.1093/applin/amac018

Costa, A., & Faria, L. (2018). Implicit theories of intelligence and academic achievement: A meta-analytic review. *Frontiers in Psychology*, 9, 829. https://doi.org/10.3389/fpsyg.2018.00829

Deci, E. L., & Ryan, R. M. (1985). *Intrinsic Motivation and Self-Determination in Human Behavior*. New York: Plenum.

Deci, E. L., & Ryan, R. M. (2000). The "what" and "why" of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry*, 11(4), 227–268.

Dörnyei, Z. (2005). *The Psychology of the Language Learner: Individual Differences in Second Language Acquisition*. Mahwah, NJ: Lawrence Erlbaum.

Dörnyei, Z. (2009). The L2 Motivational Self System. In Z. Dörnyei & E. Ushioda (Eds.), *Motivation, Language Identity and the L2 Self* (pp. 9–42). Bristol: Multilingual Matters.

Dörnyei, Z., & Ushioda, E. (Eds.). (2009). *Motivation, Language Identity and the L2 Self*. Bristol: Multilingual Matters.

Dörnyei, Z., MacIntyre, P. D., & Henry, A. (Eds.). (2015). *Motivational Dynamics in Language Learning*. Bristol: Multilingual Matters.

Dweck, C. S. (1999). *Self-Theories: Their Role in Motivation, Personality, and Development*. Philadelphia: Psychology Press.

Dweck, C. S. (2006). *Mindset: The New Psychology of Success*. New York: Random House.

Elahi Shirvan, M., Khajavy, G. H., MacIntyre, P. D., & Taherian, T. (2019). A meta-analysis of L2 willingness to communicate and its three high-evidence correlates. *Journal of Psycholinguistic Research*, 48(6), 1241–1267. https://doi.org/10.1007/s10936-019-09656-9

Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. *American Psychologist*, 54(7), 493–503.

Higgins, E. T. (1987). Self-discrepancy: A theory relating self and affect. *Psychological Review*, 94(3), 319–340.

Hiver, P., & Al-Hoorie, A. H. (2019). *Research Methods for Complexity Theory in Applied Linguistics*. Bristol: Multilingual Matters.

Horwitz, E. K., Horwitz, M. B., & Cope, J. (1986). Foreign language classroom anxiety. *The Modern Language Journal*, 70(2), 125–132. https://doi.org/10.1111/j.1540-4781.1986.tb05256.x

Kleingeld, A., van Mierlo, H., & Arends, L. (2011). The effect of goal setting on group performance: A meta-analysis. *Journal of Applied Psychology*, 96(6), 1289–1304.

Locke, E. A. (1968). Toward a theory of task motivation and incentives. *Organizational Behavior and Human Performance*, 3(2), 157–189.

Locke, E. A., & Latham, G. P. (1990). *A Theory of Goal Setting and Task Performance*. Englewood Cliffs: Prentice Hall.

Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting and task motivation: A 35-year odyssey. *American Psychologist*, 57(9), 705–717.

Locke, E. A., & Latham, G. P. (2006). New directions in goal-setting theory. *Current Directions in Psychological Science*, 15(5), 265–268.

Locke, E. A., & Latham, G. P. (2019). The development of goal setting theory: A half century retrospective. *Motivation Science*, 5(2), 93–105.

Lou, N. M., & Noels, K. A. (2017). Measuring language mindsets and modeling their relations with goal orientations and emotional and behavioral responses in failure situations. *The Modern Language Journal*, 101(1), 214–243. https://doi.org/10.1111/modl.12380

Lou, N. M., & Noels, K. A. (2019). Promoting growth in foreign and second language education: A research agenda for mindsets in language learning. *System*, 86, 102126.

MacIntyre, P. D., Clément, R., Dörnyei, Z., & Noels, K. A. (1998). Conceptualizing willingness to communicate in a L2: A situational model of L2 confidence and affiliation. *The Modern Language Journal*, 82(4), 545–562. https://doi.org/10.1111/j.1540-4781.1998.tb05543.x

MacIntyre, P. D., Baker, S. C., Clément, R., & Conrod, S. (2001). Willingness to communicate, social support, and language-learning orientations of immersion students. *Studies in Second Language Acquisition*, 23(3), 369–388.

Markus, H., & Nurius, P. (1986). Possible selves. *American Psychologist*, 41(9), 954–969.

Mercer, S., & Ryan, S. (2010). A mindset for EFL: Learners' beliefs about the role of natural talent. *ELT Journal*, 64(4), 436–444.

Mills, N., Pajares, F., & Herron, C. (2007). Self-efficacy of college intermediate French students: Relation to achievement and motivation. *Language Learning*, 57(3), 417–442. https://doi.org/10.1111/j.1467-9922.2007.00421.x

Noels, K. A., Pelletier, L. G., Clément, R., & Vallerand, R. J. (2000). Why are you learning a second language? Motivational orientations and self-determination theory. *Language Learning*, 50(1), 57–85.

Qi, X. (2022). The L2 motivational self system: A meta-analysis approach. *Studies in Second Language Acquisition* [réplication élargie].

Ryan, R. M., & Deci, E. L. (2017). *Self-Determination Theory: Basic Psychological Needs in Motivation, Development, and Wellness*. New York: Guilford.

Taguchi, T., Magid, M., & Papi, M. (2009). The L2 Motivational Self System among Japanese, Chinese and Iranian learners of English: A comparative study. In Z. Dörnyei & E. Ushioda (Eds.), *Motivation, Language Identity and the L2 Self* (pp. 66–97). Bristol: Multilingual Matters.

Teimouri, Y., Goetze, J., & Plonsky, L. (2019). Second language anxiety and achievement: A meta-analysis. *Studies in Second Language Acquisition*, 41(2), 363–387. https://doi.org/10.1017/S0272263118000311

Teimouri, Y., Plonsky, L., & Tabandeh, F. (2022). L2 grit: Passion and perseverance for second-language learning. *Language Teaching Research*, 26(5), 893–918. https://doi.org/10.1177/1362168820921895

Tseng, W.-T., Dörnyei, Z., & Schmitt, N. (2006). A new approach to assessing strategic learning: The case of self-regulation in vocabulary acquisition. *Applied Linguistics*, 27(1), 78–102.

Zhang, X. (2019). Foreign Language Anxiety and Foreign Language Performance: A Meta-Analysis. *The Modern Language Journal*, 103(4), 763–781. https://doi.org/10.1111/modl.12590

Zimmerman, B. J. (2000). Self-efficacy: An essential motive to learn. *Contemporary Educational Psychology*, 25(1), 82–91.

### Références critiques et variables écartées

Chen, X., He, J., Swanson, E., Cai, Z., & Fan, X. (2022). Big Five personality traits and second language learning: A meta-analysis of 40 years' research. *Educational Psychology Review*, 34, 851–887. https://doi.org/10.1007/s10648-021-09641-6

Carroll, J. B., & Sapon, S. M. (1959). *Modern Language Aptitude Test*. New York: Psychological Corporation.

Gardner, R. C. (1985). *Social Psychology and Second Language Learning: The Role of Attitudes and Motivation*. London: Edward Arnold.

Kirschner, P. A. (2017). Stop propagating the learning styles myth. *Computers & Education*, 106, 166–171.

Lamb, M. (2004). Integrative motivation in a globalizing world. *System*, 32(1), 3–19. https://doi.org/10.1016/j.system.2003.04.002

Li, S. (2016). The construct validity of language aptitude: A meta-analysis. *Studies in Second Language Acquisition*, 38(4), 801–842.

Macnamara, B. N., & Burgoyne, A. P. (2022). Do growth mindset interventions impact students' academic achievement? A systematic review and meta-analysis with recommendations for best practices. *Psychological Bulletin*.

Nancekivell, S. E., Shah, P., & Gelman, S. A. (2020). Maybe they're born with it, or maybe it's experience: Toward a deeper understanding of the learning style myth. *Journal of Educational Psychology*, 112(2), 221–235.

Oxford, R. L. (1990). *Language Learning Strategies: What Every Teacher Should Know*. New York: Newbury House.

Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008). Learning styles: Concepts and evidence. *Psychological Science in the Public Interest*, 9(3), 105–119. https://doi.org/10.1111/j.1539-6053.2009.01038.x

Pittenger, D. J. (2005). Cautionary comments regarding the Myers-Briggs Type Indicator. *Consulting Psychology Journal*, 57(3), 210–221.

Sisk, V. F., Burgoyne, A. P., Sun, J., Butler, J. L., & Macnamara, B. N. (2018). To what extent and under which circumstances are growth mind-sets important to academic achievement? Two meta-analyses. *Psychological Science*, 29(4), 549–571.

Ushioda, E. (2006). Language motivation in a reconfigured Europe. *Journal of Multilingual and Multicultural Development*, 27(2), 148–161.

### Ressources méthodologiques

Dock (2025). Customer onboarding metrics: 14 metrics, KPIs & benchmarks. https://www.dock.us/library/customer-onboarding-metrics

Userpilot (2025). Customer onboarding checklist completion rate: 2025 benchmark report. https://userpilot.com/blog/onboarding-checklist-completion-rate-benchmarks/

---

<a id="annexe-a"></a>

## Annexe A — Tableaux récapitulatifs

### A.1 Matrice variables × critères de sélection

| Variable | Validité construit | Effet size achievement | Effet size effort/WTC/use | Actionabilité tuteur IA | Coût items | **Retenue ?** |
|----------|-------------------|-----------------------|---------------------------|------------------------|-----------|--------------|
| Ideal L2 Self | Forte | r ≈ .20–.24 | **r ≈ .61** | Forte | 2 | **Oui (A1)** |
| FLA | Très forte | **r = –.36** | fort lien WTC négatif | Très forte | 2 | **Oui (A2)** |
| Self-efficacy (régulation) | Forte | Fort (> self-concept) | Élevé sur persistance | Forte | 1 | **Oui (A3)** |
| Language Mindset | Forte | Faible-modéré | Fort sur résilience | Forte (framing feedback) | 1 | **Oui (A4)** |
| Goal specificity | Très forte (psy orga) | d ≈ .40–.80 général | Élevé sur effort | Forte + intervention | 2 | **Oui (A5)** |
| Autonomy orientation | Forte | Modéré | Fort sur persistance | Forte | 1 | **Oui (C1)** |
| WTC | Forte | Modéré | **Prédit L2 use** | Forte (format oral) | 1 | **Oui (C2)** |
| L2 grit | Modérée (émergent) | Modéré | Recouvre self-reg | Modérée | +1 | Non (V2) |
| Big Five | Très forte | r = .10–.23 | Modeste | Faible | +10 | Non |
| MLAT | Forte | r ≈ .35–.50 | Modeste | Faible | +30 min | Non |
| Integrativeness | Faible (dépassée) | Variable contextuel | Subsumé par Ideal L2 Self | Nulle | 3 | Non |
| SILL | Faible | r ≈ .10–.25 | Faible | Nulle | 50 | Non |
| Learning styles VAK | **Nulle** (pseudoscience) | Nulle | Nulle | Nulle | +5 | **Non** |
| MBTI | Nulle | Nulle | Nulle | Nulle | +10 | Non |

### A.2 Budget items / temps

| Bloc | # items | Temps moyen | Temps p90 |
|------|---------|-------------|-----------|
| A (universal) | 8 | 74 s | 110 s |
| C (langue) | 2 | 19 s | 35 s |
| **Total** | **10** | **~93 s** | **~145 s** |

Sous le seuil Userpilot 4 étapes ≈ 50 % de complétion ; respecte les benchmarks B2C 5–7 min global onboarding.

### A.3 Mapping construit → décision tuteur

| Construit | Seuil bas | Décision tuteur |
|-----------|-----------|-----------------|
| Ideal L2 Self (A1) | ≤ 2 | Module "pourquoi" en amont ; visualisation concrète ; pas d'intensité |
| FLA (A2) | ≥ 4 | Écrit-first, pas de notes visibles, reformulation > correction, warm-up |
| Self-efficacy (A3) | ≤ 2 | Sessions 5 min, rappels doux, pas d'objectifs trop ambitieux, scaffold fort |
| Growth mindset (A4) | ≤ 2 | Process praise permanent, pas de classement, feedback explicitement effort |
| Goal specificity (A5) | vague | Module de clarification d'objectif avant leçons ; SMART scaffolding |
| Autonomy (C1) | contrôlée | Structure forte, rappels utilitaires, objectifs courts, pas d'ambiance "passion" |
| WTC (C2) | ≤ 2 | Écrit → oral asynchrone → oral synchrone, préparation explicite |

---

<a id="annexe-b"></a>

## Annexe B — Items recommandés (texte exact français adulte)

Pour référence produit (copie-collable). Toutes les échelles Likert 5 points, ancres standardisées : 1 = Pas du tout d'accord / Pas du tout — 5 = Tout à fait d'accord / Tout à fait.

### Bloc A — Universal core

**A5 — Goal specificity**
Q : « Qu'est-ce que vous aimeriez savoir faire concrètement en {LANG} dans les prochains mois ? Exprimez-le en une phrase. »
Format : champ texte libre (placeholder : "Ex : commander au restaurant en voyage / suivre une série sans sous-titres / tenir une conversation avec ma belle-famille")
Sous-question A5bis : « Quand aimeriez-vous y arriver ? »
Options : 1–3 mois / 3–6 mois / 6–12 mois / Pas de date précise

**A1a — Ideal L2 Self (vividness)**
« Je peux m'imaginer parlant {LANG} couramment dans une situation réelle (voyage, travail, rencontre). »

**A1b — Ideal L2 Self (écart/horizon)**
« Dans 2 ans, j'aimerais être capable de tenir une conversation entière en {LANG} sans revenir au français. »

**A3 — Self-efficacy d'auto-régulation**
« Quand je décide d'apprendre une langue, je suis capable de tenir une pratique régulière (plusieurs fois par semaine) même quand c'est difficile. »
Ancres : 1 = Pas du tout capable — 5 = Tout à fait capable

**A4 — Growth language mindset**
« Quel que soit votre âge, vous pouvez significativement améliorer votre niveau en {LANG} avec une pratique régulière. »

**A2a — FLA (communication apprehension)**
« J'ai peur de faire des fautes quand je parle {LANG}. »

**A2b — FLA (fear of negative evaluation)**
« Je me sens nerveux·se à l'idée de parler {LANG} avec quelqu'un. »

### Bloc C — Overlay motivation langue (après sélection LANG)

**C1 — Autonomy orientation**
Q : « Pourquoi apprenez-vous {LANG} principalement ? »
- A. Parce que ça m'intéresse vraiment, j'aime ça pour soi.
- B. Parce que c'est important pour mes projets de vie (voyage, culture, famille, partenaire).
- C. Parce que j'en ai besoin pour mon travail ou mes études.
- D. Parce que je me sentirais coupable ou mal de ne pas m'y mettre.

**C2 — Willingness to Communicate**
« Si une occasion se présentait aujourd'hui de parler {LANG} avec quelqu'un (même imparfaitement), vous le feriez ? »
Ancres : 1 = Non, j'éviterais — 5 = Oui, avec plaisir

---

<a id="annexe-c"></a>

## Annexe C — Limites de cette revue

1. **Revue narrative, pas systématique PRISMA** : sélection orientée par l'objectif produit, pas par protocole exhaustif. Les méta-analyses citées sont cependant les références standard dans le champ (L2 motivation / FLA / WTC).

2. **Biais de publication** : la plupart des études citées sont publiées en anglais, sur des populations majoritairement EFL asiatiques (Japon, Chine, Iran) ou nord-américaines. Transférabilité au public francophone adulte testée indirectement (instruments traduits existent ; pas d'évidence que les construits se comportent différemment, mais à confirmer empiriquement en pilote).

3. **Absence de linguiste natif reviewer** (voir mémoire projet). La validation française des items passera par pré-test 50 utilisateurs + corpus oracle + consensus LLM, pas par relecture C2 native.

4. **Effets dynamiques** (CDST) non entièrement captés par des mesures one-shot. La recommandation explicite de re-mesure à 4 et 12 semaines est nécessaire pour ne pas pétrifier un utilisateur sur un profil initial.

5. **Choc de sélection** : les utilisateurs qui complètent l'onboarding sont déjà un sous-groupe auto-sélectionné (motivation minimale pour s'inscrire). Les distributions empiriques des scores A1–A5, C1–C2 seront censurées à gauche (pas d'amotivés complets, pas de goal-specificity zéro, etc.). À intégrer dans le scoring comparatif (z-scores sur la population active AcademIA, pas sur littérature générale).

6. **Question de déclaratif vs comportemental** : tous les items sont self-report. Le calibrage bayésien par télémétrie comportementale (taux de complétion, abandon, reprise, acceptation de challenges) est nécessaire après 14 jours pour corriger les biais déclaratifs (désirabilité sociale, effet de halo, etc.).

7. **Évolution future** : la littérature L2 motivation est en renouvellement (critique Al-Hoorie Hiver In'nami 2024 contre le L2MSS). Ce cadrage est valide pour 2026 ; revue à 18 mois recommandée.

---

*Fin du document Vague 1.*
