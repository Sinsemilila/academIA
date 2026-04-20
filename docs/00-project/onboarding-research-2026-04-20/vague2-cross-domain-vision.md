# Vague 2 — Vision cross-domain du framework d'onboarding AcademIA

**Date** : 2026-04-20
**Auteur** : Recherche onboarding, wave 2
**Statut** : document de cadrage (architecture + psychométrie)
**Audience** : ingénieurs seniors, architectes, responsable produit
**Décision de référence** : D4 — Option C hybride (structure cross-domain prête, items v1 100% langue)

---

## 0. Note de lecture

Ce document cadre la vision long terme du framework d'onboarding AcademIA pour qu'il supporte, sans refactor douloureux, l'extension au-delà du domaine "langues" (agents Teacher EN, Maestro ES, et vague 2/3/4 : Professore IT, Lehrer DE, Sensei JP, Maestro-RU) vers des domaines hors-langue (PyMentor, CyberMentor, et potentiellement math/science/soft skills).

**Le document ne spécifie pas une implémentation cross-domain à livrer en v1.** Il cadre :

- Ce qu'on construit en v1 comme infrastructure cross-domain (3 couches, DB, API, modal générique)
- Ce qu'on reporte (items hors-langue, factorisation Bloc B/C)
- Les faux-amis à ne pas commettre (réutiliser FLA pour code anxiety, forcer un CEFR partout)
- Quand on active les overlays hors-langue (règle de 3 : PyMentor + CyberMentor en domaines 2 et 3)

Lecture obligatoire avant tout code hors-langue.

---

## 1. Executive summary

### 1.1 Trois principes non négociables

1. **Règle de 3** — Tant qu'on a 1 ou 2 instanciations d'un pattern, on duplique. À partir de 3, on factorise. Actuellement nous avons **1 domaine réel** (langues, avec EN + ES, et 4 langues à venir mais isomorphes). PyMentor et CyberMentor sont requis pour atteindre le seuil de 3 domaines et déclencher la factorisation Bloc B / Bloc C cross-domain.

2. **Trois couches** — Universal (Bloc A, 5 items vraiment trans-domaines), Domain-wrapped (Bloc B + Bloc C structure, constructs partagés mais items distincts), Domain-specific (items 100% propres — CEFR pour langues, capability matrix pour Python, maturity model pour cyber). Cette stratification **est posée dès v1** dans le YAML loader, la DB et les endpoints. C'est le seul engagement architectural cross-domain en v1.

3. **Pas de spéculation prématurée** — Les fichiers `domains/pymentor.yaml` et `domains/cybermentor.yaml` existent en v1 comme **stubs vides** (structure validée par le schéma, zéro item). On ne les remplit que lorsque le domaine est réellement prioritaire, avec ses propres items validés psychométriquement. Forcer des items par symétrie avec les langues produit du code mort et un faux signal de maturité.

### 1.2 Ce qui DOIT être cross-domain dès v1

- Structure 3 blocs (A / B / C) dans le YAML loader, avec schéma JSON Schema documenté
- Table DB `learner_profiles` unique, avec colonne `domain` (varchar) et `payload` (JSON) — pas une table par agent
- Endpoints REST paramétrés : `/api/learner-profile/{domain}/*` — pas `/api/teacher-profile`, pas `/api/maestro-profile`
- Composant Svelte `OnboardingModal.svelte` générique qui consomme un YAML domain et un schéma de validation — pas un modal par agent
- Logging télémétrie typé `{domain, item_id, bloc, construct, response}` — pas un schéma ad hoc par agent

### 1.3 Ce qu'on reporte

- Items Bloc B et Bloc C pour PyMentor et CyberMentor (attendre priorisation produit)
- Factorisation Bloc B / Bloc C cross-domain (attendre 3 domaines réels = règle de 3)
- Validation psychométrique des items hors-langue (code anxiety, math mindset, Ideal Programmer Self — ce sont des travaux de recherche, pas de sprint)
- Mapping cross-domain des échelles de niveau (CEFR ↔ capability matrix ↔ maturity model : inutile tant que la règle de 3 n'est pas atteinte)

### 1.4 Anti-patterns majeurs

- Sur-abstraire prématurément (Bloc B factorisé cross-domain sans second domaine réel → contrats flous)
- Supposer l'isomorphisme des constructs (FLA ≠ math anxiety ≠ code anxiety, même si structure factorielle proche)
- Forcer un "CEFR-équivalent" dans chaque domaine (CEFR = 20 ans de recherche européenne, pas transposable par analogie)
- Hardcoder `teacher_profile` ou `"language"` dans le code applicatif → refactor douloureux quand on ajoute PyMentor

---

## 2. Les trois couches du framework

### 2.1 Vue d'ensemble

```
┌───────────────────────────────────────────────────────────────┐
│  BLOC A — UNIVERSAL LAYER                                     │
│  5 items cross-domain, identiques quel que soit le domaine    │
│  Self-efficacy, mindset, goal specificity, autonomy, engage.  │
├───────────────────────────────────────────────────────────────┤
│  BLOC B — DOMAIN-WRAPPED LAYER (niveau + motivation)          │
│  Structure partagée (niveau, motivation), items spécifiques   │
│  Langues : CEFR bi-skill + Ideal L2 Self                      │
│  Python  : capability matrix + motivation carrière            │
│  Cyber   : maturity model + motivation clearance/bounty       │
├───────────────────────────────────────────────────────────────┤
│  BLOC C — DOMAIN-SPECIFIC LAYER (anxiety + item propres)      │
│  Anxiety du domaine + éventuels items 100% propres            │
│  Langues : FLA (Horwitz 1986) réduit 33→3 items               │
│  Python  : imposter dev / math anxiety (selon profil)         │
│  Cyber   : technical imposter / stakes anxiety                │
└───────────────────────────────────────────────────────────────┘
```

Cette stratification n'est pas une symétrie de confort : elle **reflète la réalité psychométrique** — certains constructs sont validés cross-domain (Bloc A), d'autres partagent leur structure mais pas leurs items (Bloc B), d'autres sont indissociables du domaine (Bloc C).

### 2.2 Bloc A — Universal layer

#### 2.2.1 Constructs retenus (5 items)

Les cinq constructs Bloc A sont choisis parce qu'ils sont :

1. Validés cross-domain empiriquement (méta-analyses sur langue + sport + académique + professionnel)
2. Stables dans leur phénoménologie (l'expérience subjective ne change pas drastiquement entre domaines)
3. Mesurables avec un item unique bien conçu sans perte grave de validité

| # | Construct | Source théorique | Échelle type | Transférabilité |
|---|-----------|------------------|--------------|-----------------|
| 1 | Self-efficacy générale | Bandura (1997), Schwarzer & Jerusalem (1995 GSE-10) | Likert 1–5, "Je suis capable d'apprendre ce que je décide d'apprendre" | Très élevée : Bandura théorise explicitement le transfert de self-efficacy entre domaines via sources vicaires |
| 2 | Mindset (implicit theory of intelligence) | Dweck (2006), Dweck & Leggett (1988) | Likert 1–6, "L'intelligence est une chose qu'on ne peut pas vraiment changer" (reverse) | Élevée mais avec nuance : la littérature distingue mindset général vs domain-specific (voir §4.4) |
| 3 | Goal specificity | Locke & Latham (1990, 2002) | Item ouvert + scoring structure S-M-A-R-T | Très élevée : la théorie Goal-Setting est indépendante du domaine |
| 4 | Autonomy (need satisfaction) | Deci & Ryan (2000) Self-Determination Theory, BPNS | Likert 1–5, "Je choisis comment j'apprends" | Très élevée : SDT explicitement trans-domaines |
| 5 | Engagement / effort intended | Fredricks et al. (2004) ; Schaufeli et al. (2002 UWES) | Quantitatif, "Combien de temps par semaine ?" + Likert sur régularité intentionnelle | Élevée : la mesure d'effort intentionnel est méthodologiquement neutre |

#### 2.2.2 Pourquoi 5 et pas plus

Un Bloc A à 10+ items serait tentant (ajouter grit, conscientiousness, curiosity, passion…) mais :

- Le temps d'onboarding total plafonne à ~3 minutes (fatigue décisionnelle, drop-off)
- Les 5 items Bloc A consomment ~45 secondes, laissant ~2 min pour Bloc B + Bloc C
- Plus d'items Bloc A = moins de profondeur domain-specific = perte de valeur opérationnelle pour l'agent

Grit (Duckworth), conscientiousness (Big Five), passion (Vallerand) sont des candidats sérieux mais reportés à une v2 si la télémétrie montre qu'ils améliorent la personnalisation (règle : ne pas ajouter un item tant qu'on ne sait pas lire celui qu'on a déjà).

#### 2.2.3 Stabilité temporelle

Les constructs Bloc A sont considérés comme **traits stables** à l'échelle d'un cycle d'apprentissage (3 à 6 mois). On les mesure une fois à l'onboarding et on ne les re-mesure pas à chaque session. Une re-mesure annuelle est raisonnable pour détecter les shifts (ex : self-efficacy qui s'effondre après un échec examen).

### 2.3 Bloc B — Domain-wrapped layer

Bloc B est le cœur de la tension cross-domain. La **structure** ("niveau actuel" + "motivation") se généralise, mais les **items** sont irréductiblement domain-specific.

#### 2.3.1 Construct "niveau actuel"

Chaque domaine a besoin d'une mesure de niveau, mais les instruments sont radicalement différents :

| Domaine | Instrument | Statut |
|---------|------------|--------|
| Langues | CEFR (Common European Framework of Reference) bi-skill (production + reception) | Standard international, 20+ ans de recherche, aligné sur 6 niveaux A1→C2 |
| Python | Capability matrix (syntax / data structures / control flow / functions / OOP / async / packaging / testing) | Pas de standard ; propositions industrielles (HackerRank skills, LinkedIn Skill Assessments) mais aucune convergence psychométrique |
| Cybersécurité | Maturity model (concepts → tooling → red/blue team → research) aligné partiellement sur NIST NICE framework | Standard NIST existe (NICE Framework) mais orienté rôles pro, pas parcours apprenant |
| Math / Science | Grade level (K-12) + gap analysis (topic mastery) | Standards nationaux variables (Common Core US, programmes nationaux EU) |
| Habits / Fitness | Baseline behavioral (fréquence actuelle) + capacité physique mesurable | Pas de standard unifié |

**Conséquence architecturale** : le champ `level` dans `learner_profiles.payload` est un JSON libre dont la structure est validée par le schéma du domain YAML. Pas de table `cefr_levels` partagée. Pas de conversion cross-domain.

#### 2.3.2 Construct "motivation"

Même logique : structure partagée (pourquoi tu apprends + à quel horizon), items domain-specific.

| Domaine | Items représentatifs |
|---------|----------------------|
| Langues | Ideal L2 Self (Dörnyei 2009), intégratif vs instrumental, besoins pro / voyage / famille |
| Python | Career pivot (data science, dev web), scratch-an-itch (automation personnelle), académique (cours / thèse) |
| Cybersécurité | Security clearance, bug bounty, defense job, curiosité technique |
| Math / Science | Exam prep (bac, SAT, gaokao), curiosité, remédiation lacune |

L'image picker Bloc B (si on garde cette UX) aurait donc des assets différents par domaine : photos de voyage pour langues, captures d'écran d'IDE pour Python, logos CTF / blue-team pour cyber. **Le composant UI est générique, le contenu vient du YAML du domaine.**

#### 2.3.3 Pourquoi Bloc B est "wrapped" et pas "universal"

Parce qu'on perdrait la validité des mesures si on imposait un wording cross-domain. Un item comme "À quel point es-tu motivé ?" en Likert 1–5 a une validité de façade mais **ne prédit rien**. Les items validés sont ceux qui activent la phénoménologie spécifique du domaine (ex : "Imagine-toi dans 5 ans parlant couramment espagnol — à quel point cette image est-elle vivante ?" pour Ideal L2 Self). Le wording domain-specific est le prix à payer pour la validité prédictive.

### 2.4 Bloc C — Domain-specific layer

Bloc C est le plus variable. Il contient :

- L'**anxiety** du domaine (construct central mais instrument radicalement différent selon domaine — voir §4.2)
- Les items 100% propres au domaine qui ne trouvent pas d'équivalent ailleurs (ex : tolerance to ambiguity pour langues, debugging patience pour Python, stakes awareness pour cyber)

#### 2.4.1 Exemples par domaine (projection v1+)

| Domaine | Anxiety instrument | Items propres éventuels |
|---------|--------------------|-------------------------|
| Langues | FLA (Horwitz, Horwitz & Cope 1986), réduit 33→3 items | Tolerance to ambiguity, willingness to communicate (MacIntyre 1998) |
| Python | Code anxiety ? (construct émergent, peu validé) ; math anxiety (Maloney & Beilock 2012) si profil débutant | Debugging resilience, abstraction comfort |
| Cybersécurité | Technical imposter syndrome + stakes anxiety (peur de causer un incident) | Ethical clarity / red-line awareness |
| Math | Math anxiety (Maloney & Beilock 2012) validé | Number sense self-assessment |
| Habits | Shame/guilt re : past failures | Self-compassion baseline (Neff 2003) |

#### 2.4.2 Statut "à valider psychométriquement"

Les items Bloc C hors-langue sont des **hypothèses de recherche**, pas des items prêts à la production. Les construire demande :

1. Revue de littérature (méta-analyse si disponible)
2. Adaptation d'items existants ou création d'items nouveaux
3. Pilot study (n ≥ 100 par domaine)
4. Analyse factorielle confirmatoire (CFA)
5. Validité concurrente (corrélation avec instrument full-length)

Ce cycle dure typiquement 3 à 6 mois par domaine. Aucun travail Bloc C hors-langue ne devrait être livré en production sans passer par ces étapes ou sans acter explicitement le compromis "items en alpha, fiabilité inconnue".

---

## 3. Projection par domaine

Cette section projette le mapping des 3 blocs pour chaque domaine envisagé. **Projection ≠ implémentation.** Seules les langues sont livrables en v1. Python et cyber sont des scénarios pour valider la robustesse de l'architecture.

### 3.1 Langues (domaine réel, v1)

#### 3.1.1 Bloc A (universal)

Les 5 items Bloc A décrits en §2.2 sont utilisés tels quels. Adaptation zéro : ce sont les mêmes pour Teacher EN, Maestro ES, Professore IT, Lehrer DE, Sensei JP, Maestro-RU.

#### 3.1.2 Bloc B (niveau + motivation)

- **Niveau** : self-assessment CEFR bi-skill (production orale/écrite + réception orale/écrite) via can-do statements réduits (3 items par skill, 12 items total, on ne peut pas descendre en dessous sans perdre le bi-skill). Option : scoring dynamique via conversation diagnostique de 2 minutes avec l'agent.
- **Motivation** : Ideal L2 Self (Dörnyei 2009 Motivational Self System) — 1 item vividness + 1 item frequency + 1 item alignment avec objectif concret. Intégratif vs instrumental traité en follow-up conversationnel par l'agent, pas via item dédié à l'onboarding.

Sources : Dörnyei Z. (2009) *The L2 Motivational Self System*; Dörnyei & Ushioda (2011) *Teaching and Researching Motivation*.

#### 3.1.3 Bloc C (anxiety + propres)

- **Anxiety** : FLA réduit à 3 items (sur la base de l'analyse factorielle de Horwitz et de l'étude Aida 1994 qui a reproduit la structure factorielle). Les 3 items retenus couvrent : communication apprehension, test anxiety, fear of negative evaluation.
- **Propres** : tolerance to ambiguity (1 item), willingness to communicate (MacIntyre et al. 1998, 1 item si on garde).

Source : Horwitz E. K., Horwitz M. B., Cope J. (1986) *Foreign Language Classroom Anxiety*, Modern Language Journal 70/2.

#### 3.1.4 Verdict v1

Livrable en production. Tous les items sont dérivés d'instruments validés et réduits de manière défensable. La télémétrie alpha (observer la distribution des réponses) permettra d'affiner.

### 3.2 PyMentor (domaine spéculatif, domaine #2 potentiel)

#### 3.2.1 Bloc A

Identique à §2.2. Zéro adaptation. C'est exactement le point de la couche universelle.

#### 3.2.2 Bloc B

- **Niveau** : capability matrix en 8 axes — syntax, data structures, control flow, functions, OOP, async, packaging, testing. Self-assessment "je peux faire X sans aide / avec docs / pas du tout" sur 3 items clés par axe (ou picker visuel : coche ce que tu as déjà fait). **Attention** : aucun de ces axes n'a de validation psychométrique équivalente au CEFR. On construirait une échelle "pragmatique" à améliorer avec la télémétrie.

- **Motivation** : 4 scénarios archetype (career pivot / scratch-an-itch / academic / exploratoire). Pas d'équivalent Ideal L2 Self validé pour la programmation (voir §4.3 — Ideal Programmer Self est un construct spéculatif). Se contenter d'une catégorisation + horizon temporel + objectif concret (Locke-Latham).

#### 3.2.3 Bloc C

- **Anxiety** : choix non trivial. Options :
  - Réutiliser FLA en l'adaptant → **mauvaise idée** (voir §4.2)
  - Adapter math anxiety (Maloney & Beilock 2012) → défensable si profil débutant mentionne matrices/calcul, pas pour Python débutant visant le web
  - Construire "code anxiety" ad hoc → nécessite pilot study
- **Propres** : debugging patience, abstraction comfort (items ad hoc, à valider)

#### 3.2.4 Verdict v1

Non livrable. Le YAML `domains/pymentor.yaml` reste un stub jusqu'à priorisation. Les items Bloc B et C demandent un cycle de validation de 3 à 6 mois.

### 3.3 CyberMentor (domaine spéculatif, domaine #3 potentiel)

#### 3.3.1 Bloc A

Identique à §2.2.

#### 3.3.2 Bloc B

- **Niveau** : maturity model 4 niveaux (Beginner / Intermediate / Advanced / Expert) sur plusieurs axes (concepts fondamentaux, tooling, red team, blue team, research). Possibilité de se baser sur le NIST NICE Framework pour aligner sur les rôles pro, mais le NICE est orienté emploi, pas apprentissage — adaptation nécessaire.

- **Motivation** : clearance (defense), bug bounty, blue team job, curiosité / CTF. Horizon temporel souvent lié à une certif (CompTIA Security+, CEH, OSCP).

#### 3.3.3 Bloc C

- **Anxiety** : technical imposter (Clance & Imes 1978, adapté au tech) + stakes anxiety (peur de causer un incident / d'endommager la prod). La stakes anxiety est spécifique au cyber — très peu d'autres domaines activent ce registre (médecine, aviation).

- **Propres** : ethical clarity (où tracer la red line), tolerance à l'incertitude (les attaquants ne jouent pas fair).

#### 3.3.4 Verdict v1

Non livrable. Stub YAML. Les items demanderaient un travail psychométrique spécifique, notamment pour l'axe "stakes anxiety" peu documenté en éducation.

### 3.4 Math / Science (domaine spéculatif au-delà)

#### 3.4.1 Bloc A

Identique.

#### 3.4.2 Bloc B

- **Niveau** : grade level (K-12, Common Core ou programme national) + gap analysis par topic (algebra, geometry, calculus pour math).

- **Motivation** : exam prep (bac, SAT, GRE), curiosité, remédiation. Hétérogène : un préparateur de bac n'a pas les mêmes leviers qu'un adulte curieux.

#### 3.4.3 Bloc C

- **Anxiety** : math anxiety (Maloney & Beilock 2012) — construct bien validé, instrument court disponible (MAS — Math Anxiety Scale, Hopko et al. 2003). Structure factorielle distincte de FLA (worry + somatic + cognitive interference) mais items propres.

- **Propres** : number sense self-assessment, visual-spatial confidence.

#### 3.4.4 Verdict v1

Non livrable, mais psychométrie math est mature si on souhaitait l'activer. Serait le 4e domaine, après langues / Python / cyber.

### 3.5 Habits / Life coaching (spéculatif, très éloigné)

#### 3.5.1 Bloc A

Identique, mais avec précaution : self-efficacy habit-related vs self-efficacy academic sont corrélés mais pas identiques (Bandura admet la contextualité). Un item Bloc A suffit pour un signal, pas pour une décision fine.

#### 3.5.2 Bloc B

- **Niveau** : baseline behavioral (fréquence actuelle, durée, contexte déclencheur) — très différent d'un "niveau de savoir".

- **Motivation** : Ideal Self **expérientiel** (me sentir énergique, être présent avec mes enfants) vs **identitaire** (être quelqu'un de sportif). Cette distinction est importante car elle change les items.

#### 3.5.3 Bloc C

- **Anxiety** : shame / guilt re : past failures (self-compassion, Neff 2003). Construct important dans l'onboarding habit car il oriente le tone de l'agent (pas de culpabilisation).

#### 3.5.4 Verdict v1

Très spéculatif. Le domaine "coaching" demande aussi de revoir le design agent (l'agent devient partiellement thérapeute-like, registre très différent d'un tuteur). Pas avant domaine #5.

### 3.6 Tableau récapitulatif

| Domaine | Statut v1 | Bloc A | Bloc B niveau | Bloc B motivation | Bloc C anxiety |
|---------|-----------|--------|---------------|-------------------|----------------|
| Langues | **Livrable** | 5 items universels | CEFR bi-skill | Ideal L2 Self | FLA réduit |
| Python | Stub | 5 items universels | Capability matrix 8 axes (à valider) | Scénarios carrière | Code anxiety (à construire) |
| Cyber | Stub | 5 items universels | Maturity model 4 niveaux | Clearance / bounty / CTF | Technical imposter + stakes |
| Math | Hypothèse | 5 items universels | Grade + gap analysis | Exam / curiosité | Math anxiety (validée) |
| Habits | Hypothèse lointaine | 5 items universels | Baseline behavioral | Ideal Self expérientiel | Shame/guilt + self-compassion |

---

## 4. Faux-amis : constructs qui semblent cross-domain mais ne le sont pas

Cette section est la plus importante du document. Quatre constructs paraissent cross-domain par intuition et ne le sont pas. Confondre structure et contenu sur ces constructs produirait des instruments invalides qui biaisent la personnalisation de l'agent.

### 4.1 Goal specificity — structure oui, exemples non

**Ce qui est cross-domain** : la théorie Locke-Latham (Locke & Latham 1990, 2002) établit que **les objectifs spécifiques et difficiles produisent de meilleures performances** que les objectifs vagues ("fais de ton mieux"). Cette prescription est robuste cross-domain : langues, sport, business, habitudes.

**Ce qui n'est pas cross-domain** : les exemples, les options, les heuristiques SMART adaptées. Un item Bloc A "à quel point ton objectif est-il spécifique ?" est recevable. Mais le **follow-up** doit offrir des exemples domain-specific :

- Langues : "commander au restaurant en Espagne en juin 2026"
- Python : "finir le module data science du cours Berkeley d'ici septembre"
- Cyber : "passer et réussir le CompTIA Security+ en novembre"
- Fitness : "deadlift 120 kg propre en 6 mois"

**Conséquence technique** : le scoring de goal specificity peut être un module cross-domain (détection de présence/absence de verbe d'action + deadline + mesurable), mais **les exemples et le picker sont dans le YAML du domaine**. Ne pas centraliser les exemples dans la couche universelle.

**Source** : Locke E. A. & Latham G. P. (2002) *Building a practically useful theory of goal setting and task motivation*, American Psychologist 57/9, 705-717.

### 4.2 Anxiety — même structure factorielle, constructs distincts

C'est le faux-ami le plus coûteux en cas d'erreur.

**Ce qui est similaire** : FLA (Horwitz 1986), math anxiety (Maloney & Beilock 2012), test anxiety (Sarason 1984), statistics anxiety (Cruise & Wilkins 1980), computer anxiety (Heinssen et al. 1987) partagent une **structure factorielle commune** en trois facteurs :

1. Worry (cognitive) — ruminations anticipées
2. Somatic — activation physiologique (tension, accélération cardiaque, transpiration)
3. Cognitive interference — intrusion de pensées non pertinentes pendant la tâche

Cette structure commune pourrait suggérer qu'il suffit d'adapter les items d'une échelle à l'autre.

**Ce qui est distinct** :

- Les corrélations inter-échelles sont modérées : FLA ↔ math anxiety r ≈ .25–.40 (Horwitz 2017, Maloney & Beilock 2012). Si c'était le même construct, on attendrait r > .70.
- Les **déclencheurs phénoménologiques** diffèrent : le pic d'anxiety FLA survient lors de la **production orale publique** ; le pic de math anxiety survient lors du **calcul mental sous contrainte temporelle** ; le pic de test anxiety survient lors de **l'évaluation formelle** indépendamment du contenu.
- Les **traitements validés** diffèrent : cognitive-behavioral pour test anxiety, exposure graduée pour math anxiety, approche communicative low-stakes pour FLA.

**Conséquence technique** : on **ne peut pas** réutiliser les items FLA pour mesurer code anxiety ou math anxiety, même si on les reformule. Un item comme "I feel anxious when I have to speak in class" devenu "I feel anxious when I have to debug in front of colleagues" **perd sa validité** parce qu'on n'a pas démontré que le nouvel item mesure effectivement le même facteur latent dans le nouveau domaine.

**Ce qu'il faut faire** : pour chaque nouveau domaine, construire ou adopter un instrument validé spécifique. Pour math, il existe (MAS). Pour Python/cyber, il faut soit construire (pilot study), soit se contenter d'une échelle générique de state anxiety (STAI — Spielberger 1983) avec une validité moindre mais connue.

**Sources** :
- Horwitz E. K., Horwitz M. B., Cope J. (1986) *Foreign Language Classroom Anxiety*, Modern Language Journal 70/2, 125-132.
- Maloney E. A. & Beilock S. L. (2012) *Math anxiety: who has it, why it develops, and how to guard against it*, Trends in Cognitive Sciences 16/8, 404-406.
- Aida Y. (1994) *Examination of Horwitz, Horwitz, and Cope's construct of foreign language anxiety*, Modern Language Journal 78, 155-168.

### 4.3 Ideal Future Self — identitaire vs expérientiel

**Ce qui est cross-domain** : la capacité à imaginer un soi futur ("possible self", Markus & Nurius 1986) est un mécanisme motivationnel général. Les recherches sur Ideal L2 Self (Dörnyei 2005, 2009) ont montré que la **vividness** et la **frequency of imagination** prédisent le comportement d'apprentissage (temps passé, persistance).

**Ce qui n'est pas cross-domain** : la **phénoménologie** de l'Ideal Self varie par domaine.

- Ideal L2 Self est **identitaire** : me voir "fluent" est se voir **comme** quelqu'un de fluent. C'est un basculement d'identité (bilingue/multilingue comme partie du self-concept). L'Ideal L2 Self est souvent ancré dans des relations (parler avec la famille du conjoint, être compris au travail).
- Ideal Programmer Self (si on le construisait) serait plutôt **expérientiel** : me voir programmer n'est pas forcément "devenir un programmeur" comme identité, c'est plus souvent "construire des produits, résoudre des problèmes". Les développeurs mid-career peuvent ne pas avoir d'identification forte au métier, mais conserver un Ideal Self centré sur l'output.
- Ideal Fit Self est souvent un mix expérientiel (me sentir énergique) et identitaire (être quelqu'un de sportif).
- Ideal Security Pro Self est fortement identitaire (badge, rôle, communauté).

**Conséquence technique** : les items ne peuvent pas être transposés mécaniquement. L'item Dörnyei "I can imagine myself speaking English with international friends" marche parce qu'il active une image sociale. Son équivalent Python "I can imagine myself coding with international friends" est absurde pour 80% des répondants. Il faut ré-écrire en partant de la phénoménologie du domaine.

**Travail préparatoire** : pour chaque nouveau domaine, faire une **qualitative study** (5-10 interviews semi-structurées) avec des apprenants pour documenter la phénoménologie de leur Ideal Self dans ce domaine. Sans ce travail, les items sont des suppositions.

**Sources** :
- Markus H. & Nurius P. (1986) *Possible Selves*, American Psychologist 41/9, 954-969.
- Dörnyei Z. (2009) *The L2 Motivational Self System*, in Dörnyei & Ushioda (eds) Motivation, Language Identity and the L2 Self, 9-42.

### 4.4 Mindset — général vs domain-specific

**Ce qui est cross-domain** : Dweck (2006) établit que **croire que l'intelligence est fixe vs malléable** prédit le comportement face à l'échec, la recherche de feedback, la persistance. Le mindset général est mesurable (Dweck Mindset Inventory).

**Ce qui n'est pas cross-domain** : la recherche ultérieure a montré que les **mindsets domain-specific** peuvent diverger du mindset général.

- Lou N. M. & Noels K. A. (2017) ont validé le **language mindset** comme construct distinct : un apprenant peut avoir un growth mindset général mais un fixed mindset spécifique aux langues ("je ne suis pas doué pour les langues"). La corrélation language mindset / general mindset est modérée (r ≈ .40–.55).
- Le math mindset est validé (Boaler 2013, Blackwell et al. 2007) — souvent plus fixed chez les filles après la puberté (menace du stéréotype).
- Le programming mindset est **émergent**, peu de données publiées. Intuitivement, l'idée du "natural programmer" (mindset fixed) existe dans le folklore tech mais la littérature académique manque.
- Cyber mindset : aucune donnée spécifique à ma connaissance.

**Conséquence technique** : mesurer un mindset général en Bloc A est un signal utile. Mais pour le Bloc C, si on veut un signal actionnable pour l'agent (ex : "propose un pédagogie growth-mindset"), il faut un item domain-specific. Pour les langues : Lou & Noels Language Mindset Inventory réduit. Pour math : Boaler / Blackwell. Pour Python/cyber : item ad hoc, validité faible, à piloter.

**Source** : Lou N. M. & Noels K. A. (2017) *Measuring language mindsets and modeling their relations with goal orientations and emotional and behavioral responses in failure situations*, Modern Language Journal 101/1, 214-243.

### 4.5 Autres candidats au statut de faux-ami (non traités en détail)

- **Self-efficacy** : Bandura argumente explicitement que la self-efficacy est contextuelle. On mesure une self-efficacy générale en Bloc A mais une self-efficacy domain-specific aurait plus de validité prédictive. Compromis v1 : Bloc A = général, Bloc B peut inclure un item domain-specific secondaire.
- **Engagement** : la mesure d'engagement (Schaufeli UWES-9) est transférable sur le papier, mais les déclencheurs d'engagement diffèrent (flow en programmation = résolution de puzzle ; flow en langue = conversation immersive).
- **Interest vs enjoyment** : interest (Hidi & Renninger 2006) a une phénoménologie "curiosité / exploration" relativement stable cross-domain. Enjoyment (Ryan & Deci 2000 intrinsic motivation) est plus dépendant du contenu.

---

## 5. La règle de 3 — quand factoriser

### 5.1 Principe

> "First time, do it. Second time, notice it. Third time, factor it."

Principe largement discuté (Sandi Metz 2014 *The Wrong Abstraction* ; Fowler *Refactoring* ; règle DRY prudente). Appliqué au framework d'onboarding AcademIA :

- **1 instance** d'un pattern (ex : un seul domaine `langue`) : coder en dur, ne pas abstraire.
- **2 instances** (ex : langue + Python) : dupliquer, **documenter la duplication**, noter les différences. Tentation de factoriser mais elle est prématurée : l'abstraction risque de cristalliser la ressemblance superficielle au détriment des différences profondes.
- **3 instances** (ex : langue + Python + cyber) : factoriser. Les 3 donnent assez de signal pour choisir la bonne abstraction.

### 5.2 Application au framework onboarding

#### 5.2.1 Où on en est aujourd'hui

**1 domaine réel** : langues.

Le domaine langues contient 2 agents actifs (Teacher EN, Maestro ES) et 4 en développement (Professore IT, Lehrer DE, Sensei JP, Maestro-RU). Ces 6 agents sont **isomorphes** sur l'onboarding — mêmes blocs A/B/C, mêmes items, juste la langue cible et les exemples changent. Ils ne comptent pas comme 6 instances au sens règle de 3 : ce sont 6 variantes du **même** pattern.

Donc règle de 3 : **1 instance**.

#### 5.2.2 Ce qu'on doit faire en v1

- Coder en dur les items du domaine langue dans `domains/language.yaml`
- Préserver la structure 3 blocs (A/B/C) dans le YAML loader
- Préserver la DB `learner_profiles` paramétrée par `domain`
- Ne **pas** abstraire prématurément Bloc B / Bloc C au niveau "framework"
- Créer `domains/pymentor.yaml` et `domains/cybermentor.yaml` comme stubs pour valider que le schéma supporte un YAML vide

#### 5.2.3 Quand on factorise

- **Ajout PyMentor (domaine 2)** : on duplique la structure B/C, on note dans le code les différences avec langue. Pas encore de factorisation.
- **Ajout CyberMentor (domaine 3)** : on factorise. À ce moment, on saura :
  - Si le schéma YAML actuel couvre les 3 domaines ou si on a besoin d'extensions
  - Si le Bloc B "niveau + motivation" est une bonne factorisation ou si Python/cyber demandent un découpage différent
  - Si des items Bloc A jugés "universels" se révèlent en fait domain-specific (candidat à la rétrogradation)

#### 5.2.4 Risque de ne pas suivre la règle de 3

**Scénario négatif A — sur-abstraction prématurée** : on introduit un système de plugin abstrait pour Bloc B dès v1, avec des interfaces génériques. Quand PyMentor arrive, on découvre que le niveau Python n'est pas un "level" au sens CEFR mais une **matrice de capability**, et que l'interface ne capture pas cette notion. On refactor l'abstraction, mais entretemps elle a contaminé le code langue qui a dû se plier à des contraintes inutiles. Coût double.

**Scénario négatif B — hardcode total** : on code `teacher_profile`, `maestro_profile`, etc., avec des DB et endpoints séparés. Quand PyMentor arrive, on refactor 6 agents pour passer à un modèle unifié. Coût énorme, plus dette technique dans le legacy (anciens endpoints à maintenir pendant la transition).

**Scénario optimal suivi ici** : structure 3 couches préservée en v1 (coût marginal faible), items hardcodés langue (simple, testé), PyMentor + cyber ajoutent leurs YAML quand prioritaires, factorisation Bloc B/C déclenchée à l'arrivée du 3e domaine.

### 5.3 Règle de 3 appliquée aux items intra-domaine

La règle s'applique aussi à l'intérieur d'un domaine. Exemple : si on a 2 items d'anxiety FLA qui partagent du code de scoring, dupliquer. Au 3e item, factoriser.

---

## 6. Anti-patterns + ce qui DOIT être cross-domain dès v1

### 6.1 Anti-patterns à éviter

#### 6.1.1 Sur-abstraire prématurément

**Symptôme** : un fichier `domains/base.yaml` ou `domains/abstract.yaml` qui définit des "slots" génériques pour Bloc B et Bloc C, avec un système d'héritage YAML. Les fichiers domain-specific étendent la base.

**Pourquoi mauvais** :
- Contrat flou (qu'est-ce qu'un "slot" générique ?)
- L'héritage YAML produit vite des comportements non-locaux difficiles à débugger
- Le coût cognitif pour comprendre le système dépasse la valeur tant qu'on a 1 domaine

**Règle** : pas d'héritage YAML tant qu'on n'a pas 3 domaines. Les YAML de domaines sont **plats, autonomes, lisibles en une session**.

#### 6.1.2 Supposer l'isomorphisme entre domaines

**Symptôme** : prendre les items FLA, les "traduire" en "code anxiety" en changeant les mots-clés, et livrer. Ou prendre l'Ideal L2 Self et le transposer en "Ideal Programmer Self" sans étude qualitative.

**Pourquoi mauvais** :
- Les items perdent leur validité psychométrique (le construct n'est plus celui qu'on pense mesurer)
- Le signal remonté à l'agent est biaisé (donc personnalisation biaisée)
- On contamine la base de données avec des mesures dont la fiabilité est inconnue, difficile de nettoyer rétroactivement

**Règle** : chaque nouveau construct Bloc B / Bloc C dans un nouveau domaine doit être validé (existant validé OU pilot study).

#### 6.1.3 Forcer un CEFR-équivalent dans chaque domaine

**Symptôme** : inventer une "échelle de niveau Python à 6 niveaux" parce que CEFR a 6 niveaux, et la faire passer pour un standard.

**Pourquoi mauvais** :
- CEFR bénéficie de 20 ans de recherche, d'alignement descripteurs / tâches, de corrélations avec tests standardisés
- Une échelle inventée n'a aucun de ces soutiens
- Elle crée un faux sens de rigueur qui biaise les décisions pédagogiques
- Elle cristallise une structure qui peut être le mauvais découpage pour le domaine

**Règle** : pour chaque domaine, choisir l'instrument de niveau le plus validé disponible, sans forcer la forme CEFR. Si aucun instrument validé, assumer l'incertitude (capability matrix "pragmatique") et télémétrer.

#### 6.1.4 Hardcoder "language" / "teacher_profile" dans le code

**Symptôme** : endpoints `/api/teacher-profile/create`, table `teacher_profiles`, variables `language` dans les signatures de fonction.

**Pourquoi mauvais** :
- Refactor douloureux à l'arrivée du 2e domaine
- Propagation : ces noms contaminent frontend, tests, logs, docs
- Chaque migration consomme du budget d'équipe

**Règle** : dès v1, tous les noms sont paramétrés par `domain`. L'agent Teacher EN parle au backend via `/api/learner-profile/language/*`, pas via `/api/teacher-profile/*`.

#### 6.1.5 Mélanger couche universelle et couche domain-specific

**Symptôme** : mettre un item de motivation Bloc B dans Bloc A parce qu'il semble "général".

**Pourquoi mauvais** :
- Le Bloc A doit rester stable quel que soit le domaine (c'est son contrat)
- Mettre un item Bloc B en Bloc A oblige à y avoir une variante par domaine, ce qui détruit l'homogénéité
- Crée de l'ambiguïté sur ce qu'est "universel" et affaiblit le modèle

**Règle** : si un item varie par domaine, il n'est pas Bloc A. Bloc A = identique mot pour mot dans tous les domaines.

#### 6.1.6 Charger l'onboarding pour "mesurer tout"

**Symptôme** : le Bloc A passe de 5 à 12 items parce qu'on veut aussi grit, Big Five, passion, curiosity.

**Pourquoi mauvais** :
- Drop-off avant fin de l'onboarding
- Fatigue répondant → qualité des réponses baisse sur les derniers items
- La valeur marginale d'un 8e item est faible si on ne sait pas lire les 7 premiers

**Règle** : 5 items Bloc A max en v1. N'ajouter un item que si la télémétrie montre que les items existants n'expliquent pas une variance opérationnelle critique.

### 6.2 Ce qui DOIT être cross-domain dès v1

#### 6.2.1 Structure 3 blocs dans le YAML loader

Schéma (JSON Schema exprimé en prose, formalisation séparée) :

```
domain_yaml:
  domain_id: string          # "language" | "pymentor" | "cybermentor" | ...
  domain_name: string
  version: semver
  blocs:
    bloc_a_universal:        # STRICTE : identique cross-domain, référencée, pas dupliquée
      ref: "blocs/universal.yaml"
    bloc_b_domain_wrapped:
      level:
        instrument: string   # "cefr_bi_skill" | "capability_matrix" | ...
        items: [...]
      motivation:
        instrument: string
        items: [...]
    bloc_c_domain_specific:
      anxiety:
        instrument: string
        items: [...]
      specific_items: [...]  # 0..N items propres au domaine
```

Le loader valide chaque YAML contre ce schéma. Un YAML `pymentor.yaml` stub contient les champs `domain_id` et `version` + blocs vides, et passe la validation.

#### 6.2.2 DB `learner_profiles` paramétrée

Schéma simplifié :

```
learner_profiles(
  id uuid pk,
  user_id uuid fk,
  domain varchar not null,       # "language" | "pymentor" | ...
  agent_id varchar,              # "teacher_en" | "maestro_es" | ... (optionnel, pour multi-agents d'un domaine)
  bloc_a_payload jsonb,          # structure stable cross-domain
  bloc_b_payload jsonb,          # structure validée par schéma domaine
  bloc_c_payload jsonb,          # idem
  created_at timestamptz,
  updated_at timestamptz,
  schema_version varchar         # pour migrations futures
)
```

Une seule table. Index sur `(user_id, domain)`. Les `*_payload` sont des JSON libres dont la structure est validée applicativement par le schéma du domaine.

#### 6.2.3 Endpoints REST paramétrés par domaine

```
POST   /api/learner-profile/{domain}/start       -- init onboarding
PUT    /api/learner-profile/{domain}/bloc-a      -- submit bloc A
PUT    /api/learner-profile/{domain}/bloc-b      -- submit bloc B
PUT    /api/learner-profile/{domain}/bloc-c      -- submit bloc C
GET    /api/learner-profile/{domain}             -- read current
PATCH  /api/learner-profile/{domain}             -- update partial (retour apprenant)
```

Tous les endpoints prennent `{domain}` en path. Validation middleware : le domaine existe (présence d'un YAML), l'utilisateur est autorisé pour ce domaine (RLS / ACL), le payload matche le schéma.

Pas d'endpoint `/api/teacher-profile` ou `/api/maestro-profile`. Les agents sont des consommateurs de `/api/learner-profile/language/*`.

#### 6.2.4 Composant Svelte `OnboardingModal.svelte` générique

Le composant prend en props :
- `domain: string`
- `yaml_config: DomainYaml` (parsé côté backend, transmis)
- `on_submit: (bloc, payload) => Promise<void>`

Il **ne contient pas** de logique domain-specific. Les items sont rendus via un set de sous-composants réutilisables :
- `LikertItem.svelte` (1–5, 1–6, 1–7 paramétrable)
- `OpenTextItem.svelte`
- `ImagePickerItem.svelte` (assets dans YAML)
- `ConversationalDiagnosticItem.svelte` (pour CEFR dynamique)

Le contenu (wording, exemples, assets) vient du YAML. Le composant est **stateless** sur le domaine.

#### 6.2.5 Logging télémétrie typé

Schéma d'événement :

```
{
  event: "onboarding.item.submitted",
  user_id: uuid,
  domain: string,
  bloc: "a" | "b" | "c",
  item_id: string,
  construct: string,       # "self_efficacy" | "cefr_production" | "fla" | ...
  response: json,
  response_time_ms: int,
  timestamp: iso
}
```

Ce schéma est paramétré par `domain` + `construct` mais **identique structurellement** cross-domain. Permet des dashboards uniformes, des analyses corrélationnelles par domaine, et une base pour d'éventuelles méta-analyses internes.

#### 6.2.6 Contract tests

Un ensemble de tests d'intégration qui vérifient que **toute nouvelle configuration de domaine** (nouveau YAML) respecte le contrat :
- Valide contre le schéma
- Les items Bloc A sont références (pas dupliqués)
- Les endpoints répondent en < 200 ms
- Le modal rend sans erreur
- La télémétrie est loguée

Ces tests sont exécutés en CI. Ajouter PyMentor en stub valide = ajouter un YAML stub + les tests passent.

---

## 7. Recommandations opérationnelles

### 7.1 Ce qu'on livre en v1

| Livrable | Statut |
|----------|--------|
| `data/onboarding/blocs/universal.yaml` (5 items Bloc A) | À livrer |
| `data/onboarding/domains/language.yaml` (Bloc B + Bloc C langues) | À livrer |
| `data/onboarding/domains/pymentor.yaml` (stub vide, schéma valide) | À livrer |
| `data/onboarding/domains/cybermentor.yaml` (stub vide, schéma valide) | À livrer |
| Schéma JSON Schema `data/onboarding/schema.json` | À livrer |
| Loader YAML + validation côté backend | À livrer |
| Table DB `learner_profiles` + migrations | À livrer |
| Endpoints REST paramétrés par `{domain}` | À livrer |
| Composant `OnboardingModal.svelte` générique | À livrer |
| Sous-composants items (Likert, OpenText, ImagePicker, ConvDiag) | À livrer |
| Télémétrie typée `onboarding.item.submitted` | À livrer |
| Contract tests | À livrer |
| Items Bloc B + Bloc C langues (CEFR, Ideal L2 Self, FLA réduit) | À livrer |

### 7.2 Ce qu'on reporte

| Livrable reporté | Condition de déblocage |
|------------------|------------------------|
| Items Bloc B + Bloc C PyMentor | Priorisation produit PyMentor + pilot study items (3-6 mois) |
| Items Bloc B + Bloc C CyberMentor | Idem pour cyber |
| Factorisation Bloc B/C cross-domain (framework) | Arrivée du 3e domaine réel (règle de 3) |
| Mapping cross-domain des échelles de niveau | Idem |
| Domaines math / habits | Priorisation produit + recherche dédiée |
| Items Bloc A additionnels (grit, conscientiousness, etc.) | Télémétrie v1 montre variance opérationnelle non expliquée |
| Re-mesure longitudinale des traits Bloc A | Décision produit re : cycle de vie apprenant |

### 7.3 Règles d'engagement pour ajouter un domaine

Checklist à appliquer à tout ajout de domaine (après v1) :

1. Le domaine est **prioritaire produit** (pas spéculatif)
2. Revue de littérature faite pour Bloc B niveau + motivation + Bloc C anxiety
3. Items Bloc B/C choisis parmi instruments validés quand disponibles
4. Items ad hoc passés en pilot study (n ≥ 100) avec CFA + validité concurrente
5. YAML domaine créé, passe les contract tests
6. Télémétrie alpha active pendant au moins 4 semaines avant passage en production
7. Revue inter-domaine si on atteint 3 domaines : déclencher la factorisation Bloc B/C

### 7.4 Règles pour modifier Bloc A (universel)

Bloc A est le contrat le plus sensible. Toute modification :

1. Requiert validation cross-domain : l'item nouveau/modifié doit avoir une littérature cross-domain (pas seulement langue)
2. Migration DB nécessaire (tous les profiles existants doivent gérer le nouvel item : valeur par défaut ou re-prompt)
3. Tous les domaines doivent accepter le changement — pas de Bloc A variable par domaine
4. Décision validée au niveau architecture (pas une feature request isolée)

### 7.5 Gouvernance psychométrique

Propositions de règles minimales :

- Toute échelle Bloc B / Bloc C est soit référencée (instrument public validé + source citée), soit construite en interne avec pilot study documenté
- Chaque item stocke dans le YAML : construct, source (DOI si possible), version
- Une revue de pertinence des items est faite tous les 6 mois (télémétrie : items à faible variance, items avec trop de non-réponses, items corrélés à d'autres items du même bloc → candidats à la suppression)
- Pas de modification d'item en prod sans bump de version du YAML et migration des profiles impactés

---

## 8. Questions ouvertes

Liste de points qui restent à trancher au-delà de ce document :

### 8.1 Multi-agents au sein d'un domaine

Teacher EN et Maestro ES sont deux agents du **même** domaine "langues". Leur onboarding est-il :

- Option A : un seul profil `learner_profiles` par utilisateur pour le domaine langues, partagé entre Teacher et Maestro (l'utilisateur ne refait pas l'onboarding en passant de EN à ES)
- Option B : un profil par (utilisateur, agent) : l'utilisateur refait l'onboarding pour chaque langue

Recommandation provisoire : **Option A pour le Bloc A** (identique cross-agents), **Option B pour le Bloc B + Bloc C** (le niveau CEFR et la motivation varient par langue cible). Implémentation : `agent_id` nullable, Bloc A stocké avec `agent_id = null`, Bloc B/C stockés avec `agent_id` défini.

### 8.2 Cas où un utilisateur traverse plusieurs domaines

Un utilisateur qui onboarde sur langues puis sur PyMentor : refait-il l'intégralité du Bloc A ? Recommandation : on **propose** au second onboarding de réutiliser le Bloc A existant (avec option "rafraîchir"), et on mesure en télémétrie si ça améliore la complétion.

### 8.3 Retour apprenant et re-mesure

Les traits Bloc A sont stables mais pas immuables (self-efficacy après échec, mindset après intervention pédagogique). Quand re-mesurer ?

- Recommandation v1 : pas de re-mesure automatique. Option manuelle "mettre à jour mon profil" dans les settings.
- Post-v1 : envisager re-prompt ciblé après événements critiques (fin de cycle, échec significatif).

### 8.4 Multi-linguisme de l'onboarding lui-même

L'onboarding est-il disponible dans la langue native de l'utilisateur ou dans la langue cible ?

- Pour langues : recommandation = **langue native** (l'utilisateur ne parle pas encore la langue cible, par définition du onboarding)
- Pour PyMentor, cyber : langue native, à déterminer produit.

Impact YAML : chaque item a des variantes par locale. Contrat à intégrer au schéma : `item.content.{locale}`.

### 8.5 Onboarding "adaptatif" vs "fixe"

Le framework supporte-t-il un onboarding adaptatif (les items Bloc B/C dépendent des réponses Bloc A) ou uniquement des items fixes ?

- v1 : **fixe**. L'adaptatif ajoute une complexité importante (moteur de règles, tests combinatoires).
- Post-v1 : à envisager si la recherche montre une valeur claire (ex : utilisateur avec fixed mindset → item supplémentaire sur past failure pour contextualiser).

---

## 9. Références

### 9.1 Psychologie et psychométrie

- Bandura A. (1997) *Self-Efficacy: The Exercise of Control*, Freeman.
- Blackwell L. S., Trzesniewski K. H., Dweck C. S. (2007) *Implicit theories of intelligence predict achievement across an adolescent transition*, Child Development 78/1, 246-263.
- Boaler J. (2013) *Ability and mathematics: the mindset revolution that is reshaping education*, Forum 55/1, 143-152.
- Clance P. R. & Imes S. A. (1978) *The imposter phenomenon in high achieving women*, Psychotherapy: Theory, Research & Practice 15/3, 241-247.
- Cruise R. J. & Wilkins E. M. (1980) *STARS: Statistical Anxiety Rating Scale*, Andrews University.
- Deci E. L. & Ryan R. M. (2000) *The "what" and "why" of goal pursuits*, Psychological Inquiry 11/4, 227-268.
- Dörnyei Z. (2005) *The Psychology of the Language Learner*, Lawrence Erlbaum.
- Dörnyei Z. (2009) *The L2 Motivational Self System*, in Dörnyei & Ushioda (eds) Motivation, Language Identity and the L2 Self, Multilingual Matters, 9-42.
- Dörnyei Z. & Ushioda E. (2011) *Teaching and Researching Motivation*, 2e éd., Pearson Longman.
- Dweck C. S. (2006) *Mindset: The New Psychology of Success*, Random House.
- Dweck C. S. & Leggett E. L. (1988) *A social-cognitive approach to motivation and personality*, Psychological Review 95/2, 256-273.
- Fredricks J. A., Blumenfeld P. C., Paris A. H. (2004) *School engagement: potential of the concept, state of the evidence*, Review of Educational Research 74/1, 59-109.
- Heinssen R. K., Glass C. R., Knight L. A. (1987) *Assessing computer anxiety*, Computers in Human Behavior 3, 49-59.
- Hidi S. & Renninger K. A. (2006) *The four-phase model of interest development*, Educational Psychologist 41/2, 111-127.
- Hopko D. R., Mahadevan R., Bare R. L., Hunt M. K. (2003) *The Abbreviated Math Anxiety Scale (AMAS)*, Assessment 10/2, 178-182.
- Horwitz E. K., Horwitz M. B., Cope J. (1986) *Foreign Language Classroom Anxiety*, Modern Language Journal 70/2, 125-132.
- Horwitz E. K. (2017) *On the misreading of Horwitz, Horwitz and Cope (1986) and the need to balance anxiety research and the experiences of anxious language learners*, in Gkonou, Daubney & Dewaele (eds) New Insights into Language Anxiety, Multilingual Matters.
- Locke E. A. & Latham G. P. (1990) *A Theory of Goal Setting and Task Performance*, Prentice Hall.
- Locke E. A. & Latham G. P. (2002) *Building a practically useful theory of goal setting and task motivation*, American Psychologist 57/9, 705-717.
- Lou N. M. & Noels K. A. (2017) *Measuring language mindsets and modeling their relations with goal orientations and emotional and behavioral responses in failure situations*, Modern Language Journal 101/1, 214-243.
- MacIntyre P. D., Clément R., Dörnyei Z., Noels K. A. (1998) *Conceptualizing willingness to communicate in a L2*, Modern Language Journal 82/4, 545-562.
- Maloney E. A. & Beilock S. L. (2012) *Math anxiety: who has it, why it develops, and how to guard against it*, Trends in Cognitive Sciences 16/8, 404-406.
- Markus H. & Nurius P. (1986) *Possible Selves*, American Psychologist 41/9, 954-969.
- Neff K. D. (2003) *Self-compassion: an alternative conceptualization of a healthy attitude toward oneself*, Self and Identity 2/2, 85-101.
- Ryan R. M. & Deci E. L. (2000) *Intrinsic and extrinsic motivations: classic definitions and new directions*, Contemporary Educational Psychology 25/1, 54-67.
- Sarason I. G. (1984) *Stress, anxiety, and cognitive interference*, Journal of Personality and Social Psychology 46/4, 929-938.
- Schaufeli W. B., Salanova M., González-Romá V., Bakker A. B. (2002) *The measurement of engagement and burnout*, Journal of Happiness Studies 3/1, 71-92.
- Schwarzer R. & Jerusalem M. (1995) *Generalized Self-Efficacy Scale*, in Weinman, Wright & Johnston (eds) Measures in Health Psychology, NFER-NELSON, 35-37.
- Spielberger C. D. (1983) *State-Trait Anxiety Inventory for Adults*, Consulting Psychologists Press.

### 9.2 Ingénierie logicielle

- Fowler M. (2018) *Refactoring: Improving the Design of Existing Code*, 2e éd., Addison-Wesley.
- Metz S. (2014) *The Wrong Abstraction*, Sandi Metz blog, January 2016. Règle couramment citée pour la règle de 3.

### 9.3 Cadres et standards

- Conseil de l'Europe (2001, 2020) *Common European Framework of Reference for Languages (CEFR)* + Companion Volume.
- NIST (2020) *National Initiative for Cybersecurity Education (NICE) Framework*, SP 800-181 Rev. 1.

---

## 10. Annexes

### 10.1 Check-list d'auto-évaluation pour ajouter un domaine

```
[ ] Domaine prioritaire produit (pas spéculatif)
[ ] Revue de littérature Bloc B niveau : instrument identifié et cité
[ ] Revue de littérature Bloc B motivation : instrument ou phénoménologie documentée
[ ] Revue de littérature Bloc C anxiety : instrument validé OU pilot study planifié
[ ] Items ad hoc : protocole pilot study (n, design, CFA, validité concurrente)
[ ] Qualitative study Ideal Future Self faite pour le domaine (5-10 interviews)
[ ] YAML domaine créé, respecte le schéma
[ ] YAML domaine passe contract tests
[ ] Télémétrie alpha activée avant production
[ ] Si 3e domaine : déclencher review cross-domain pour factoriser Bloc B/C
```

### 10.2 Exemples de YAML (esquisse, non normatif)

#### 10.2.1 `domains/language.yaml` (extrait)

```yaml
domain_id: language
domain_name: Langues étrangères
version: 1.0.0
blocs:
  bloc_a_universal:
    ref: blocs/universal.yaml
  bloc_b_domain_wrapped:
    level:
      instrument: cefr_bi_skill
      items:
        - id: cefr_production_oral
          type: conversational_diagnostic
          duration_s: 120
        - id: cefr_reception_oral
          type: likert_can_do
          scale: [1, 5]
          statements: [...]
        # etc.
    motivation:
      instrument: ideal_l2_self_short
      items:
        - id: vividness
          type: likert
          scale: [1, 6]
          prompt: "Imagine-toi dans 5 ans parlant couramment {target_language}. À quel point cette image est-elle vivante ?"
        # etc.
  bloc_c_domain_specific:
    anxiety:
      instrument: fla_reduced
      items:
        - id: fla_communication_apprehension
          type: likert
          scale: [1, 5]
          prompt: "..."
        # etc.
    specific_items:
      - id: willingness_to_communicate
        type: likert
        scale: [1, 5]
        prompt: "..."
```

#### 10.2.2 `domains/pymentor.yaml` (stub v1)

```yaml
domain_id: pymentor
domain_name: Python (PyMentor)
version: 0.0.1-stub
blocs:
  bloc_a_universal:
    ref: blocs/universal.yaml
  bloc_b_domain_wrapped:
    level:
      instrument: todo
      items: []
    motivation:
      instrument: todo
      items: []
  bloc_c_domain_specific:
    anxiety:
      instrument: todo
      items: []
    specific_items: []
```

Le stub passe les contract tests parce que la structure est respectée. Aucune donnée n'est collectée tant que les items sont vides ; le modal n'est pas déclenché pour ce domaine en production.

### 10.3 Tableau synthétique des constructs et leur transférabilité

| Construct | Bloc | Transférabilité | Raison |
|-----------|------|-----------------|--------|
| Self-efficacy générale | A | Élevée | Bandura, trans-domaines |
| Mindset général | A | Modérée-Élevée | Dweck, mais domain-specific existe |
| Goal specificity (structure) | A | Élevée | Locke-Latham, structure universelle |
| Autonomy (SDT) | A | Élevée | SDT trans-domaines |
| Engagement intentional | A | Élevée | Mesure méthodologiquement neutre |
| Goal specificity (exemples) | B | Faible | Exemples domain-specific |
| Niveau actuel | B | Nulle | Instrument radicalement différent |
| Motivation archetype | B | Structure oui, items non | Phénoménologie différente |
| Ideal Future Self | B/C | Structure oui, items non | Identitaire vs expérientiel |
| Anxiety du domaine | C | Structure oui, items non | FLA ≠ math ≠ code (r ≈ .25-.40) |
| Tolerance to ambiguity | C | Faible | Surtout étudié en langue |
| Willingness to communicate | C | Spécifique langue | N'a pas d'équivalent pertinent ailleurs |
| Debugging patience | C | Spécifique Python | N'a pas d'équivalent |
| Stakes awareness | C | Spécifique cyber/médical | Rare |
| Math anxiety | C | Spécifique math | Instrument validé (MAS) |
| Shame/guilt past failures | C | Spécifique habits | Self-compassion (Neff) |

---

## 11. Fin du document

Ce document est la référence d'architecture cross-domain pour l'onboarding AcademIA. Il est versionné avec le code. Toute décision qui le contredit doit être soit une mise à jour explicite du document (avec justification), soit une exception documentée dans l'ADR correspondant.

**Prochaines étapes recommandées** :

1. Formaliser le JSON Schema correspondant à la structure 3 blocs décrite en §2 et §6.2.1
2. Implémenter le loader YAML + validation applicative
3. Migrations DB : table unique `learner_profiles` paramétrée par `domain`
4. Livrer `domains/language.yaml` complet avec items CEFR / Ideal L2 Self / FLA réduit
5. Livrer stubs `pymentor.yaml` et `cybermentor.yaml`
6. Contract tests CI
7. Composant `OnboardingModal.svelte` générique + sous-composants items
8. Télémétrie typée en place avant activation production
9. Revoir ce document à chaque ajout de domaine (dérive documentaire)
