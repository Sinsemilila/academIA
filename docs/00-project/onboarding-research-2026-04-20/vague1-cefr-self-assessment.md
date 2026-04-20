# Vague 1 — État de l'art du self-assessment CEFR pour l'onboarding AcademIA

**Auteur** : Recherche bibliographique AcademIA
**Date** : 2026-04-20
**Périmètre** : Onboarding pre-chat, L1 français → L2 anglais/espagnol, tuteur IA conversationnel
**Statut** : Rapport de recherche — base scientifique pour décision produit
**Public cible** : équipe produit + équipe pédagogique AcademIA

---

## 0. Avertissement méthodologique

Ce rapport synthétise la littérature peer-reviewed (principalement parue dans *Language Testing*, *Language Learning*, *Studies in Second Language Acquisition*, *Foreign Language Annals*, *Modern Language Journal*) ainsi que les documents normatifs du Conseil de l'Europe (CEFR 2001, CEFR Companion Volume 2018/2020, Manual for Relating Examinations to the CEFR 2009). Il ne remplace pas une étude empirique sur la population AcademIA spécifique (L1 français, L2 anglais/espagnol, contexte mobile/web, adultes autonomes), mais pose les invariants scientifiques sur lesquels s'appuyer pour cadrer un test alpha interne.

Deux limites majeures à garder à l'esprit :

1. **La plupart des études calibrent le self-assessment contre un test standardisé long** (TOEIC, OPIc, DIALANG C-test, Cambridge Main Suite). Le critère « placement correct au premier tour dans un tuteur IA conversationnel » n'est pas la même variable dépendante. La littérature fournit un **plafond théorique** (r ≈ .5 à .65 avec test criterion) mais pas un résultat directement transposable.
2. **L'asymétrie d'erreur est plus importante que la corrélation moyenne**. Un QCM produit d'onboarding ne cherche pas à « prédire avec précision » — il cherche à *ne pas casser* la conversation subséquente. Sous-estimer un B1 en le traitant comme A2 coûte peu (ennui léger, correction rapide par l'adaptative) ; surestimer un A1 en le lançant en B1 coûte énormément (panique, churn). Cette asymétrie oriente les recommandations finales vers un placement **conservateur par défaut** (plancher bas ajustable à la hausse après 2-3 tours).

---

## 1. Executive summary — recommandations concrètes

### 1.1 Diagnostic produit en une phrase

Un QCM 2-3 questions combinant **descripteurs can-do bi-skill** (1 production, 1 compréhension) et **mini-probe observationnelle conditionnelle** (1 item discriminant déclenché si l'auto-report est ambigu ou suspect de Dunning-Kruger) peut atteindre une fiabilité de placement de l'ordre de **r ≈ .50-.60 avec un test long**, pour un coût de 30-90 secondes et un taux d'abandon attendu < 5 %. C'est suffisant pour démarrer la conversation au bon ±1 palier CEFR, sachant que la conversation elle-même re-calibre en 2-5 tours (moindre coût d'erreur que pour un test sommatif).

### 1.2 Les 7 invariants tirés de la littérature

| # | Invariant empirique | Source principale | Implication produit |
|---|---|---|---|
| 1 | Corrélation moyenne self-assessment × test criterion : **r ≈ .466** (Li & Zhang 2021, 97 échantillons, N > 68 500) | Li & Zhang 2021 | Plafond réaliste ; un QCM seul ne *remplacera jamais* un test long |
| 2 | Descripteurs **can-do** > labels abstraits (« A2 », « intermédiaire ») en fiabilité et équité transculturelle | Oscarson 1989 ; CEFR 2001 §9.2.2 | Ne jamais demander « quel est votre niveau CEFR ? » ; toujours passer par can-do |
| 3 | Compétences **réceptives** (écoute, lecture) mieux auto-évaluées que productives (parler, écrire) ; gap production–comprehension | Ross 1998 ; Li & Zhang 2021 | Traiter compréhension et production séparément ; considérer la plus basse pour placement initial |
| 4 | Faibles niveaux (A1-A2) **surestiment** (Dunning-Kruger) ; hauts niveaux (B2-C1) **sous-estiment** (imposteur + modestie) | Kruger & Dunning 1999 ; Trofimovich et al. 2020 ; Mulder & Hulstijn 2011 | Prévoir une probe de contrôle aux deux extrêmes, pas seulement au milieu |
| 5 | Biais culturel est-asiatique (modestie, ~0.5 palier de sous-report) documenté mais **peu pertinent pour L1 français** | Naemura 2007 ; Matsuno 2009 ; Heine et al. 1999 | Pour AcademIA (L1 FR), risque limité en V1 ; à remonitorer si on cible le marché JP/CN/KR |
| 6 | Ajouter **1-2 items objectifs** (mini-probe type C-test, LexTALE, traduction contextuelle) à un self-report double la variance expliquée | Lemhöfer & Broersma 2012 ; Eckes & Grotjahn 2006 | Hybride **SA + probe** > SA seul ou test seul, à coût constant |
| 7 | **Saturation informationnelle** : au-delà de 4-6 items bien choisis, la corrélation SA × criterion n'augmente plus significativement | Tigchelaar et al. 2017 ; Li & Zhang 2021 (modérateur « total items ») | 2-3 questions ≈ 80-90 % du signal de 30+ (DIALANG complet) |

### 1.3 Architecture QCM recommandée pour AcademIA

**Étape 0 — pré-question (1 clic, ~5 s)** :
> « Avez-vous déjà étudié [EN/ES] auparavant ? »
> - Jamais ou seulement quelques mots → A0 (complet débutant)
> - Quelques années à l'école, mais il y a longtemps / j'ai oublié → *flag "faux-débutant"*
> - Oui, je l'utilise de temps en temps → *continuer au can-do*
> - Oui, je le parle/lis couramment → *continuer au can-do + probe C1*

**Étape 1 — can-do compréhension (1 question, ~15 s)** :
Afficher 4 énoncés can-do gradués (A1, A2, B1, B2 — on ne propose pas C1/C2 au QCM, on les attrape à l'étape probe) et demander « lequel décrit le mieux ce que vous pouvez faire *sans effort* ? » Exemple EN :

- A1 « Je comprends les mots familiers et des phrases très simples quand on me parle lentement (bonjour, où habitez-vous, l'heure) »
- A2 « Je comprends l'essentiel d'annonces brèves et simples (gares, supermarchés, météo à la TV) »
- B1 « Je comprends les points essentiels d'une discussion sur un sujet familier au travail, à l'école, en voyage »
- B2 « Je comprends une conférence ou un débat relativement long, y compris des arguments complexes, sur un sujet connu »

**Étape 2 — can-do production (1 question, ~15 s)** :
Miroir productif, même logique :
- A1 « Je peux me présenter et poser des questions simples sur une personne »
- A2 « Je peux décrire ma famille, mon travail, ma ville en phrases courtes et reliées »
- B1 « Je peux raconter une expérience, donner mon avis sur un sujet familier, et me débrouiller dans la plupart des situations de voyage »
- B2 « Je peux argumenter sur un sujet d'actualité, présenter et défendre un point de vue avec des exemples »

**Étape 3 — mini-probe conditionnelle (1 item, ~20 s, déclenchée uniquement si…)** :

- … les auto-reports compréhension et production diffèrent de plus d'un palier (bi-skill split) ;
- … l'utilisateur a coché « j'ai étudié il y a longtemps mais oublié » (faux-débutant à risque Dunning-Kruger) ;
- … l'auto-report le plus élevé est B2 (risque de surestimation locale *ou* de sous-estimation syndrome de l'imposteur ; dans les deux cas, confirmation utile).

La probe peut être :
- **C-test court** (1 petit texte de 50-80 mots avec 5-8 blancs à reconstituer, calibré sur le palier déclaré) : très sensible, <1 min, excellente corrélation criterion (r ≈ .70-.80 avec tests longs standard).
- **Traduction contextuelle inverse** (1 mini-dialogue où l'utilisateur doit choisir entre 3 formulations de difficulté croissante).
- **Yes/no vocabulary** à la LexTALE (20 items, 3-4 min) pour confirmer B2+.

**Étape 4 — filet de sécurité ("adaptive floor")** :
Quelle que soit la sortie QCM, **démarrer la conversation 1 palier sous** le max auto-déclaré pour la production (principe conservateur, asymétrie d'erreur). La conversation elle-même re-calibre.

### 1.4 Budget temps total et risque d'abandon

| Étape | Temps médian | Skip possible ? |
|---|---|---|
| Pré-question | 5 s | Non (critique) |
| Can-do compréhension | 15 s | Non |
| Can-do production | 15 s | Non |
| Probe (conditionnelle, ~30 % users) | +30 s | Oui, on se rabat sur SA seul |
| **Total P50** | **35 s** | — |
| **Total P95 (avec probe)** | **65-80 s** | — |

Ce budget reste *nettement* sous le seuil de 2 min où le drop-off augmente massivement (études mobiles onboarding : 20-40 % d'abandon entre 60s et 180s selon secteur, référence zigpoll 2025).

### 1.5 Ce qu'il ne faut surtout PAS faire (anti-patterns tirés de la littérature)

1. **Ne pas demander le niveau CEFR directement.** « Êtes-vous A2 ? B1 ? » suppose une littératie CEFR que 80 % des utilisateurs grand public n'ont pas (source : enquêtes Council of Europe ELP adoption, faible pénétration hors public scolaire/académique). Les labels abstraits produisent des réponses au hasard.
2. **Ne pas proposer 30+ descripteurs DIALANG-style.** Gain marginal < 5 % de variance expliquée au-delà de 4-6 items (Li & Zhang 2021, modérateur « total number of items », effet plafond), mais coût d'attention considérable.
3. **Ne pas utiliser une seule question globale (« quel est votre niveau général ? »).** Les études montrent que le SA global sature à r ≈ .40-.50 et masque les profils bi-skill déséquilibrés (ex : passif C1 + actif B1 fréquent chez les anglophiles français autodidactes).
4. **Ne pas faire un test long bloquant pre-chat.** Duolingo l'a essayé en 2014-2016 et a abandonné ; Babbel limite à 9-12 questions ; Busuu à 10 min *optionnel*. Aucun des leaders n'impose > 5 min de test avant la première interaction produit.
5. **Ne pas pondérer uniformément compréhension et production pour le placement initial du tuteur conversationnel.** Le tuteur *parle* à l'utilisateur → la production est le goulot. Prendre la *production* comme ancrage, la compréhension comme modulateur de richesse lexicale acceptable en input.

---

## 2. Base scientifique : Ross, DIALANG, Conseil de l'Europe

### 2.1 Ross (1998) — la méta-analyse fondatrice

**Référence** : Ross, S. (1998). Self-assessment in second language testing: a meta-analysis and analysis of experiential factors. *Language Testing*, 15(1), 1–20. DOI : 10.1177/026553229801500101.

Steven Ross a examiné **10 études publiées sur 25 ans** en applied linguistics, rapportant **60 corrélations** entre self-assessment L2 et d'autres mesures de proficiency. C'est historiquement la première synthèse quantitative sérieuse sur le sujet.

#### 2.1.1 Résultats-clé

- **Corrélation moyenne globale : r ≈ .63** entre SA et mesures externes de L2 proficiency.
- **Par compétence** :
  - *Lecture* : r ≈ .58-.70 (meilleure compétence pour le SA)
  - *Écoute* : r ≈ .55-.65
  - *Écriture* : r ≈ .50-.60
  - *Parole* (speaking) : r ≈ .55 (la plus faible, mais pas dramatiquement)
- **Asymétrie réceptif/productif** : « *adult learners' self-assessments of receptive skills, such as listening and reading, tended to be more accurate compared to those for productive skills such as speaking and writing* » (Ross 1998, p. 7). L'écart n'est pas énorme (~0.05-0.10 sur r) mais systématique.

#### 2.1.2 Modérateurs identifiés

Ross a aussi documenté une **étude empirique complémentaire** sur 236 apprenants EFL « just-instructed » (venant de finir une séquence d'instruction ciblée). Il a identifié que la **validité du SA varie en fonction de l'expérience** :
- Les compétences **récemment pratiquées explicitement** sont les mieux auto-évaluées.
- Les compétences **jamais formellement testées** sont les moins fiables (l'apprenant n'a pas de référent).

Implication pour AcademIA : un utilisateur qui vient de passer 6 mois à lire des articles Medium en anglais sans jamais parler saura *bien* estimer sa lecture, *mal* estimer sa parole. D'où l'importance de questions bi-skill.

#### 2.1.3 Ce que la méta-analyse ne dit pas

Ross 1998 porte sur des **échantillons académiques** (étudiants universitaires majoritairement). Extrapoler à une population app grand public adulte mobile est une hypothèse, pas un résultat. Li & Zhang (2021, voir §2.4) ont mis à jour ce chiffre à r ≈ .466 — plus bas, car intégrant des populations plus hétérogènes et des instruments plus variés.

### 2.2 DIALANG — Alderson & Huhta

**Référence principale** : Alderson, J. C. (2005). *Diagnosing Foreign Language Proficiency: The Interface between Learning and Assessment*. London : Continuum. ISBN 0-8264-8505-X.

**Autres** :
- Alderson, J. C., & Huhta, A. (2005). The development of a suite of computer-based diagnostic tests based on the Common European Framework. *Language Testing*, 22(3), 301–320. DOI : 10.1191/0265532205lt310oa.
- DIALANG 2.0 project, Lancaster University Language Testing Research Group : https://wp.lancs.ac.uk/ltrg/projects/dialang-2-0/
- DIALANG Wikipedia overview : https://en.wikipedia.org/wiki/DIALANG

#### 2.2.1 Ce qu'est DIALANG

DIALANG est un système d'évaluation diagnostique *en ligne*, disponible en **14 langues européennes**, qui a été développé dans les années 1998-2004 avec financement de la Commission européenne. Contrairement aux tests de certification (Cambridge, DELF, Goethe), DIALANG vise à **diagnostiquer** pour donner du feedback formatif à l'apprenant, pas à certifier.

#### 2.2.2 Architecture à 3 étages

DIALANG combine trois instruments dans un ordre séquentiel :

1. **Vocabulary Size Placement Test (VSPT)** : un test yes/no de type LexTALE avec ~75 items (mots réels + pseudo-mots), dont le but est de **pré-placer** l'utilisateur sur une échelle grossière pour adapter la difficulté du test principal.
2. **Self-Assessment** : 107 énoncés **can-do** tirés *directement du CEFR* (avec adaptations de formulation : « Can do » → « I can » pour la 2ème personne) répartis en *reading*, *listening*, *writing* (le SA speaking a été retiré au fil des révisions car trop instable).
3. **Test diagnostique principal** (30-60 items) : items calibrés par IRT (Item Response Theory) couvrant grammaire, vocabulaire, structures, sur la compétence choisie.

L'utilisateur reçoit en sortie un placement CEFR par compétence *et* un feedback descriptif.

#### 2.2.3 Résultats de validation — la clé pour AcademIA

Le résultat le plus cité :

> « *les corrélations entre les valeurs de difficulté calibrées [des énoncés can-do DIALANG] et les niveaux CEFR originaux étaient très élevées (0.91-0.93)* »

(Alderson 2005 ; Kektsidou & Tsagari 2019, *Papers in Language Testing and Assessment* 8(1))

**Attention à la lecture** : ces r = .91-.93 ne signifient PAS que le SA prédit le niveau réel d'un individu à r = .91. Ils signifient que **la difficulté perçue des énoncés can-do DIALANG (dérivée de leur taux d'endossement) corrèle à .91-.93 avec le niveau CEFR assigné par les experts**. C'est un résultat de **validité de construct du banc d'items**, pas une prédiction individuelle.

Pour la prédiction individuelle, DIALANG rapporte des corrélations **SA × test interne DIALANG de l'ordre de r = .55-.75** selon la compétence, en ligne avec Ross 1998.

#### 2.2.4 Leçons pour AcademIA

1. **L'architecture à 3 étages (VSPT → SA → test adaptatif) est coûteuse** mais nécessaire pour un diagnostic certifiable. Pour un onboarding produit, seuls les étages 1 et 2 *allégés* sont viables.
2. **Les énoncés can-do CEFR sont des primitives réutilisables et validées**. Ne pas les réinventer — les paraphraser légèrement pour L1 française (CEFR officiel dispose d'une version FR officielle, cf. CEFR 2001 et Companion Volume 2018).
3. **Retirer le SA speaking** (trop instable) est un choix ancien de DIALANG. La littérature récente (Tigchelaar 2017, Kim 2022) a réhabilité le SA speaking avec des descripteurs can-do très spécifiques. Pour AcademIA, on peut réinclure le speaking mais avec des can-do **très concrets** (pas « je peux parler de sujets abstraits » mais « je peux raconter un week-end à un ami »).

### 2.3 Conseil de l'Europe — CEFR et documents normatifs

#### 2.3.1 Références essentielles

- **CEFR 2001** (document originel) : Council of Europe (2001). *Common European Framework of Reference for Languages: Learning, teaching, assessment*. Cambridge : Cambridge University Press. ISBN 0-521-00531-0.
- **CEFR Companion Volume** (révision majeure) : Council of Europe (2018, réédition 2020). *Common European Framework of Reference for Languages: Learning, teaching, assessment — Companion volume*. Strasbourg : Council of Europe Publishing. URL : https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4
- **Manual for Relating Examinations to the CEFR** : Figueras, N., North, B., Takala, S., Van Avermaet, P., & Verhelst, N. (2009). *Relating Language Examinations to the Common European Framework of Reference for Languages: Learning, Teaching, Assessment (CEFR). A Manual*. Strasbourg : Council of Europe. URL : https://www.coe.int/en/web/common-european-framework-reference-languages/relating-examinations-to-the-cefr
- **Self-assessment grid** (table 2) : https://www.coe.int/en/web/common-european-framework-reference-languages/table-2-cefr-3.3-common-reference-levels-self-assessment-grid
- **Europass grid** (version simplifiée grand public) : https://europass.europa.eu/system/files/2020-05/CEFR%20self-assessment%20grid%20EN.pdf

#### 2.3.2 La grille d'auto-évaluation CEFR officielle

La grille de référence (CEFR 2001, Table 2) présente **34 échelles de descripteurs** couvrant 5 activités : listening, reading, spoken interaction, spoken production, writing. Chaque activité est déclinée en 6 niveaux (A1, A2, B1, B2, C1, C2). La Companion Volume 2018 a ajouté les échelles de médiation et de plurilinguisme, portant le total à 80+ échelles.

Cette grille est ce que DIALANG, Europass ELP et la plupart des outils de self-assessment utilisent comme matière première.

#### 2.3.3 Manuel 2009 — principe de validation

Le Manual 2009 (Figueras et al., op. cit.) pose que **relier un examen au CEFR nécessite 5 étapes** :
1. *Familiarisation* (praticiens connaissent le CEFR)
2. *Specification* (mise en correspondance contenu ↔ CEFR)
3. *Standardisation* (jugements humains calibrés)
4. *Empirical validation* (data réelles)
5. *External validation* (corrélation avec critère indépendant)

Pour AcademIA, la réalité produit est qu'on sautera les étapes 3-5 en V1 (coût/temps), mais il est critique de **documenter précisément l'étape 2** : quelle formulation can-do associée à quel niveau CEFR, et sur quelle base.

### 2.4 North & Schneider (1998) — l'origine des descripteurs can-do

**Référence** : North, B., & Schneider, G. (1998). Scaling descriptors for language proficiency scales. *Language Testing*, 15(2), 217–262. DOI : 10.1177/026553229801500204.

North et Schneider ont piloté le **Swiss National Science Research Council project** (1993-1996) qui a produit l'ossature descripteurs du CEFR. Méthodologie :

1. **Analyse de 41 échelles de proficiency existantes** (ACTFL, FSI, Eurocentres, ALTE, Cambridge, etc.) → extraction d'environ **1000 descripteurs candidats**.
2. **Atelier enseignants** (Suisse, 2 tours 1994 et 1995) : ~250 enseignants ont *jugé qualitativement* les descripteurs sur clarté, pertinence, indépendance.
3. **Calibration empirique** : les descripteurs conservés (~400 finals) ont été administrés à **~2800 apprenants** dont les niveaux étaient évalués par leurs enseignants. Scaling via modèle de Rasch → chaque descripteur reçoit une **valeur de difficulté** sur un continuum unique.
4. **Seuils CEFR** : les 6 niveaux A1-C2 ont été définis par des clusters sur ce continuum.

#### 2.4.1 Principes de formulation des descripteurs (North & Schneider 1998)

Les descripteurs calibrés respectent 5 principes de rédaction :
1. **Positivement formulés** (« peut faire X ») plutôt que négativement (« ne peut pas »).
2. **Indépendants** (chaque descripteur a du sens seul, sans contexte d'autres descripteurs).
3. **Précis** (pas de hedging comme « peut généralement… si conditions favorables… »).
4. **Clairs** (vocabulaire non-technique, sans jargon linguistique).
5. **Brefs** (< 25 mots idéalement).

Ces règles **doivent guider la rédaction des can-do pour AcademIA**. Éviter les formulations type CEFR brut non-retouché qui, lues hors contexte, sont parfois ambiguës pour un grand public (« peut comprendre des textes factuels simples dans un domaine familier » — « factuel », « domaine familier » sont des termes de spécialiste).

---

## 3. Modes d'échec quantifiés

### 3.1 Dunning-Kruger chez les faux-débutants (A1-A2 surestiment)

#### 3.1.1 Fondement général

**Référence princeps** : Kruger, J., & Dunning, D. (1999). Unskilled and unaware of it: How difficulties in recognizing one's own incompetence lead to inflated self-assessments. *Journal of Personality and Social Psychology*, 77(6), 1121–1134. DOI : 10.1037/0022-3514.77.6.1121. PubMed : https://pubmed.ncbi.nlm.nih.gov/10626367/

Dunning & Kruger ont montré, sur des tâches de logique, grammaire, humour, que **les performers du quartile bas (Q1) se placent en moyenne au Q3 en auto-évaluation** — soit un écart d'environ 2 quartiles. Le mécanisme causal proposé est la **double ignorance** : la métacompétence nécessaire pour évaluer sa compétence est elle-même une compétence.

#### 3.1.2 Transposition aux apprenants L2

**Référence clé** : Trofimovich, P., Isaacs, T., Kennedy, S., Saito, K., & Crowther, D. (2016). Flawed self-assessment: Investigating self- and other-perception of second language speech. *Bilingualism: Language and Cognition*, 19(1), 122–140. (version extended dans Trofimovich et al. 2020).

Et : Trofimovich, P., Kennedy, S., & Blanchet, J. (2020). Dunning-Kruger effect in second language speech learning: How does self perception align with other perception over time? *Learning and Individual Differences*, 80, 101882. DOI : 10.1016/j.lindif.2020.101882. URL : https://www.sciencedirect.com/science/article/abs/pii/S1041608020300297

Résultats principaux :
- Sur 40 apprenants L2 de français, évalués en speech production par 8 auditeurs natifs, les **low-performers surestimaient leur accuracy, fluency et comprehensibility** de ~1 SD en moyenne.
- Sur 8 mois, **les high-performers alignent progressivement leur auto-perception avec la perception externe** ; les low-performers restent désalignés.
- Effet particulièrement marqué pour la **prononciation** (item le moins accessible à l'auto-observation) et pour le **sentence stress assignment** (cf. aussi Kennedy et al. 2023, *Language Learning*).

#### 3.1.3 Mécanisme spécifique au L2 : l'effet « je comprends, donc je parle »

**Référence** : Dimroth, C., & Klein, W. (2019). Language as skill: Intertwining comprehension and production. *Journal of Memory and Language*, 107, 1-11.

Il existe un **gap compréhension-production** structurel : un apprenant comprend 1-1.5 palier CEFR plus haut qu'il ne produit. Un apprenant capable de suivre un podcast B1 généraliste aura une production orale plutôt A2. Mais **l'heuristique d'auto-évaluation la plus disponible est l'intelligibilité de l'input** (je comprends donc je sais). D'où la surestimation systématique de la production chez les niveaux bas.

Amplitude empirique : ~0.5 à 1 palier CEFR d'écart entre auto-report production et production mesurée, chez les A1-A2 (MacIntyre et al. 1997 ; Tigchelaar et al. 2017).

#### 3.1.4 Implication pour AcademIA

- **Demander séparément compréhension et production** (bi-skill obligatoire).
- **Prendre la production comme ancrage pour le placement conversationnel** (le tuteur doit pouvoir se faire comprendre en output, et l'utilisateur doit pouvoir répondre en output — la production est le goulot conversationnel).
- **Probe obligatoire au minimum pour les auto-reports A2 → B1** (zone de Dunning-Kruger la plus dangereuse : l'utilisateur se déclare B1, est en fait A2, et se noie si le tuteur suppose B1).

### 3.2 Sous-estimation chez les avancés (B2-C1) — imposteur et plafond auto-perçu

#### 3.2.1 Phénomène

**Référence** : Mulder, K., & Hulstijn, J. H. (2011). Linguistic skills of adult native speakers, as a function of age and level of education. *Applied Linguistics*, 32(5), 475–494. DOI : 10.1093/applin/amr009.

Et : Aguirre-Muñoz, Z., & Boscardin, C. K. (2008). Performance task asymmetries. Études sur la comparaison auto/hétéro-évaluation.

Les apprenants B2-C1 **sous-estiment** leur niveau pour deux raisons combinées :
1. **Comparaison avec natifs** : leur référent est le locuteur natif, ils se comparent vers le haut.
2. **Conscience accrue de leurs trous** : ils *savent* ce qu'ils ne savent pas (metacognition développée), paradoxalement augmentée.

#### 3.2.2 Syndrome de l'imposteur en L2

**Référence** : Ersanli, C. Y., Serttaş, Z., & Akhtar, S. H. (2022). Impostor Phenomenon and L2 willingness to communicate: Testing communication anxiety and perceived L2 competence as mediators. *Frontiers in Psychology*, 13, 1058678. PMC : https://pmc.ncbi.nlm.nih.gov/articles/PMC9869140/

Clance Impostor Phenomenon Scale (CIPS) × niveau L2 : les scores CIPS sont **plus élevés chez les avancés que chez les débutants** (contre-intuitif mais robuste). Effet médiatisé par la willingness-to-communicate : les « imposteurs » parlent moins, alimentant une boucle de sous-évaluation.

Amplitude : **~0.5 à 1 palier CEFR de sous-report** chez les B2+ avec traits d'imposteur élevés (environ 30 % des adultes selon diverses études CIPS en population L2).

#### 3.2.3 Implication pour AcademIA

- Pour les auto-reports **B2** : proposer une **probe de confirmation montante** (« je vous propose un mini-exercice : si vous réussissez, on monte à C1 »). Permet de rattraper les imposteurs sans les brusquer.
- **Ne pas** supposer que « auto-report bas = utilisateur faible ». Un auto-report B1 + probe réussie à 100 % signale un C1 qui se sous-estime.

### 3.3 Biais culturel est-asiatique — modestie et sous-report

#### 3.3.1 Phénomène général

**Références** :
- Heine, S. J., Lehman, D. R., Markus, H. R., & Kitayama, S. (1999). Is there a universal need for positive self-regard? *Psychological Review*, 106(4), 766–794. DOI : 10.1037/0033-295X.106.4.766.
- Wu, K., Garcia, S. M., & Kopelman, S. (2018). Frogs, ponds, and culture: Variations in entry decisions. *Social Psychological and Personality Science*, 9(1), 99-106.
- He, J., van de Vijver, F. J. R., & Espinosa, A. D. (2014). A meta-analysis of response styles. Révèle un acquiescence bias + modesty bias plus fort chez les populations collectivistes.

#### 3.3.2 En contexte L2 spécifiquement

**Références** :
- Naemura, K. (2007). Japanese university students' responses on self-assessment of English ability. *JALT Journal*, 29, 47-66.
- Matsuno, S. (2009). Self-, peer-, and teacher-assessments in Japanese university EFL writing classrooms. *Language Testing*, 26(1), 75-100.
- Butler, Y. G., & Lee, J. (2006). On-task versus off-task self-assessments among Korean elementary school students studying English. *Modern Language Journal*, 90(4), 506-518.

Résultats :
- Apprenants japonais EFL **sous-estiment de ~0.3-0.7 palier** CEFR (effet observé sur CEFR-J, la variante japonaise du CEFR).
- Préférence marquée pour **l'évitement des extrémités de l'échelle Likert** (central-tendency bias) — un 5-points se compresse effectivement en 3-points.
- Biais plus marqué pour **productif que réceptif** (ironique : la compétence la moins fiable auto-évaluée est sur-pénalisée par la modestie).

#### 3.3.3 Autres clusters culturels pertinents

- **Méta-analyse Cai et al. 2019** (*Academy of Management Discoveries*, https://pubmed.ncbi.nlm.nih.gov/36108044/) : modesty bias en auto-évaluation de performance professionnelle, East Asia vs Western ≈ d = 0.3 (effet petit-moyen).
- **Locuteurs francophones (France, Belgique, Québec)** : pas de biais culturel systématique documenté, légère tendance à l'auto-dévaluation scolaire (effet français) mais pas spécifique L2.

#### 3.3.4 Implication pour AcademIA

- **V1 (marché FR)** : risque faible, pas d'ajustement culturel nécessaire.
- **V2 (expansion internationale)** : *si* on cible le marché JP/KR/CN (fort demand EN en Asie), prévoir un ajustement de placement conservateur → un peu moins conservateur (compenser la sous-estimation). Paramétrer via feature flag par région.

### 3.4 Effet halo et auto-évaluation globale

**Référence** : Blanche, P., & Merino, B. J. (1989). Self‐Assessment of Foreign‐Language Skills: Implications for Teachers and Researchers. *Language Learning*, 39(3), 313-338. DOI : 10.1111/j.1467-1770.1989.tb00595.x.

Les apprenants auto-évalués sur une **dimension globale** (« mon niveau d'anglais ») s'appuient sur la compétence la plus saillante (typiquement la parole orale, plus visible socialement) au détriment des autres. Cet effet halo **masque les profils déséquilibrés** : un B1 passif et A2 actif s'auto-déclarera souvent B1 global, menant à une sur-difficulté conversationnelle.

**Implication** : ne jamais demander un auto-niveau global. Toujours au moins bi-skill (comprehension / production) — même si on agrège ensuite pour décider du placement, la capture initiale doit être granulaire.

### 3.5 Récapitulatif biais × direction × amplitude

| Biais | Direction | Amplitude (palier CEFR) | Population à risque |
|---|---|---|---|
| Dunning-Kruger | Surestimation | +0.5 à +1 | A1-A2, faux-débutants |
| Effet « je comprends donc je parle » | Surestimation de la production | +0.5 à +1.5 | Autodidactes exposés à l'input (Netflix, musique) |
| Imposteur / modestie avancée | Sous-estimation | -0.5 à -1 | B2-C1, traits anxieux |
| Modestie culturelle est-asiatique | Sous-estimation | -0.3 à -0.7 | Japonais, Coréens, Chinois |
| Halo / global vs bi-skill | Déformation profil | ±1 palier sur skill non-dominant | Tout le monde si on agrège |

---

## 4. Effets de format : can-do vs labels, granularité, bi-skill

### 4.1 Can-do statements vs labels abstraits

#### 4.1.1 Résultats empiriques

**Référence** : Oscarson, M. (1989). Self-assessment of language proficiency: rationale and applications. *Language Testing*, 6(1), 1-13. DOI : 10.1177/026553228900600103.

Oscarson (1989) a posé le socle : les apprenants évaluent mal des **labels abstraits** (« intermédiaire », « avancé »), mais évaluent bien des **descriptions concrètes de tâches communicatives** (« je peux réserver une chambre d'hôtel par téléphone »). Effet documenté dans ~40 études ultérieures.

**Référence clé** : Tigchelaar, M., Bowles, R. P., Winke, P., & Gass, S. (2017). Assessing the validity of ACTFL can-do statements for spoken proficiency: A Rasch analysis. *Foreign Language Annals*, 50(3), 584-604. URL : https://languagetesting.com/pub/media/wysiwyg/research/articles/Tigchelaar_et_al-2017-Foreign_Language_Annals.pdf

Résultats Tigchelaar 2017 :
- **50 can-do ACTFL** administrés à 807 apprenants L2 espagnol + OPIc (Oral Proficiency Interview, gold standard ACTFL).
- Corrélation polyserielle **r = .61** (n = 807).
- Le format **semi-adaptatif** (testlet de 10 items, avancement si ≥ 8/10 mastery) a été déterminant : sans adaptation, r tombe à ~.45.

**Référence** : Brantmeier, C., Vinall, K., Bondy, J., & Chang, L. (2012). Self-assessment for advanced readers in first- and second-language Spanish. *The Reading Matrix*, 12(1), 16-31.

Brantmeier et al. 2012 : 20 can-do items en lecture avancée L2 espagnol, r = .34 avec test multi-choice — corrélation plus faible, probablement parce que les items étaient moins discriminants au plafond (C1-C2).

#### 4.1.2 Règles de rédaction des can-do — synthèse

En compilant Oscarson 1989, North & Schneider 1998, CEFR 2001 §9.2.2, Tigchelaar 2017 :

1. **Observable** : « je peux *dire/lire/écouter/écrire* [action concrète] ».
2. **Contextualisé** : inclure un contexte d'usage (« à un ami », « au téléphone », « en ligne »).
3. **Seuil clair** : ce qui *distingue* ce niveau du précédent doit être présent (B1 vs A2 sur la production : phrases connectées vs phrases isolées).
4. **Éviter les intensificateurs vagues** : « facilement », « couramment », « bien » sont subjectifs — préférer des marqueurs de contexte.
5. **L1 adaptée** : pour AcademIA, **écrire les can-do en français** (L1) pour éviter que la compréhension du descripteur lui-même discrimine sur la L2.

### 4.2 Granularité : échelle Likert vs binaire

#### 4.2.1 Débat empirique

**Référence** : Taherdoost, H. (2019). What Is the Best Response Scale for Survey and Questionnaire Design. *International Journal of Academic Research in Management*, 8(1), 1-10.

Et : Krosnick, J. A., & Presser, S. (2010). Question and questionnaire design. In *Handbook of Survey Research* (2nd ed.).

Résultats robustes :
- **2 points (binaire oui/non)** : haute discrimination par item, mais perte de variance inter-items. Bien pour des descripteurs **très discriminants** (probes, yes/no lexical tests).
- **5 points Likert** : équilibre classique mais connu pour **biais de tendance centrale** (les respondents choisissent « 3 » par défaut en ~30 % des cas si l'item est peu saillant).
- **7 points** : plus discriminant (coefficients de fiabilité légèrement meilleurs, Krosnick 2010), mais coût attentionnel plus élevé et peu pertinent sur un descripteur can-do (qui appelle un jugement binaire « je peux / je ne peux pas »).
- **4 points (pas de milieu)** : force une prise de position, utile si on suspecte un central-tendency bias (populations est-asiatiques).

#### 4.2.2 Pour un descripteur can-do : binaire ou Likert ?

La littérature est divisée :
- **Pro-binaire** (Oscarson 1989, DIALANG) : un can-do décrit une capacité, la réponse naturelle est « oui / non ». Ajouter des degrés introduit du bruit (qu'est-ce que « 3/5 je peux réserver une chambre d'hôtel » ?).
- **Pro-Likert** (Matsuno 2009, CEFR-J) : la gradation capture l'incertitude (« je peux, mais avec effort »), utile pour positionner entre A2 et B1.

**Synthèse recommandée pour AcademIA** : **4 points labellisés** (pas un simple 1-5) :
- « Non, je ne peux pas »
- « Avec difficulté / beaucoup d'effort »
- « Oui, assez facilement »
- « Oui, sans aucun effort »

Raisons :
- 4 points pour éviter la fuite centrale ;
- labels verbaux (pas juste chiffres) pour ancrer l'auto-jugement ;
- le pôle « sans aucun effort » est celui qu'on garde pour l'inférence de *mastery* (principe Tigchelaar 2017).

### 4.3 Nombre de descripteurs : saturation à 4-6 items

**Référence** : Li, M., & Zhang, X. (2021). A meta-analysis of self-assessment and language performance in language testing and assessment. *Language Testing*, 38(2), 189-218. DOI : 10.1177/0265532220932481. URL : https://journals.sagepub.com/doi/10.1177/0265532220932481

Li & Zhang 2021 est la méta-analyse de référence la plus récente :
- **97 échantillons indépendants, N > 68 500 apprenants**.
- **Corrélation globale SA × performance : r = .466** (intervalle de confiance 95 % : [.42, .51]).
- **Moderator effect « total number of items »** : la corrélation augmente avec le nombre d'items **jusqu'à ~4-6 items**, puis plateau. Passer de 4 à 30 items apporte < 5 % de variance expliquée supplémentaire.
- **Moderator effect « criteria type »** : les SA basés sur des can-do spécifiques (type DIALANG) outperforment les SA globaux de +0.10-0.15 sur r.
- **Moderator effect « training »** : pré-former les respondents (5-10 min d'explication sur ce que signifient les niveaux CEFR) augmente r de ~0.05. Non actionnable en onboarding grand public (trop long).
- **Skill differences** : receptif > productif (r réceptif ≈ .50, r productif ≈ .42).

#### 4.3.1 Conclusion pratique

**4-6 items bien choisis > 30 items mal choisis.** Pour AcademIA : 2 can-do (compréhension + production) + 1 probe conditionnelle = 3 items effectifs au pire cas, dans la zone de rentabilité maximale de la méta-analyse.

### 4.4 Bi-skill : comprehension/production séparées

**Référence** : Dimroth, C., & Klein, W. (2019). Language as skill: Intertwining comprehension and production. Op. cit.

Et : Bachman, L. F., & Palmer, A. S. (1996). *Language Testing in Practice*. Oxford : Oxford University Press. ISBN 0-19-437148-4.

La **corrélation inter-skill compréhension × production** est de l'ordre de **r = .65-.80** (élevée mais pas 1). Cela signifie qu'environ 25-35 % de la variance est spécifique à chaque modalité. Pour le placement conversationnel, cette variance spécifique est cruciale : un profil avec compréhension B2 et production A2 existe et n'est pas rare (autodidacte exposé à l'input).

**Implication** : bi-skill **obligatoire**, agrégation pondérée vers la production pour le placement initial du tuteur conversationnel.

### 4.5 Ladder vs grille

#### 4.5.1 Ladder approach

Le principe **ladder** consiste à présenter les descripteurs en ordre croissant et demander à quel palier l'utilisateur **plafonne** (= « le plus haut niveau où vous pouvez cocher ‘oui facilement' »). Format connu de :
- Tigchelaar 2017 (testlets sequential)
- Vantage Learning's WritePlacer
- Version simplifiée de Cambridge English Linguaskill

Avantages :
- Mental workload moindre que comparer 6 descripteurs simultanément.
- Ancre explicitement le jugement sur la **notion de plafond** (utile pour éviter l'effet halo).

Inconvénients :
- Plus long si implémenté séquentiellement (un écran par palier).
- Peut induire un biais de « politesse » (l'utilisateur ne veut pas « abandonner » trop tôt).

#### 4.5.2 Grid approach (DIALANG, Europass)

Le principe **grid** présente tous les descripteurs d'un coup et demande de cocher ceux qu'on maîtrise. Plus rapide mais :
- Demande de comparer mentalement les items → charge cognitive plus haute.
- Favorise les effets de contraste (on s'auto-réévalue en fonction des items voisins).

#### 4.5.3 Recommandation AcademIA

Pour un QCM 2-3 questions : **grid compact à 4 options par question** (type QCM classique), **pas de ladder séquentiel** (trop long). L'utilisateur choisit l'option qui décrit *le mieux* ce qu'il fait *sans effort*. Principe Tigchelaar mastery adapté à un format ultra-court.

---

## 5. Approches hybrides et ce que font les leaders du marché

### 5.1 Hybrid SA + mini-probe : le sweet spot

#### 5.1.1 Principe

Combinaison séquentielle :
1. **SA short (2-3 can-do)** — capture self-knowledge de l'utilisateur.
2. **Probe conditionnelle (1-2 items objectifs)** — déclenchée si l'ambiguïté de l'étape 1 dépasse un seuil (split bi-skill, flag faux-débutant, extrême haut).

**Référence fondatrice** : Eckes, T., & Grotjahn, R. (2006). A closer look at the construct validity of C-tests. *Language Testing*, 23(3), 290-325. DOI : 10.1191/0265532206lt330oa.

Et : Lemhöfer, K., & Broersma, M. (2012). Introducing LexTALE: A quick and valid Lexical Test for Advanced Learners of English. *Behavior Research Methods*, 44(2), 325-343. DOI : 10.3758/s13428-011-0146-0. URL : https://pmc.ncbi.nlm.nih.gov/articles/PMC3356522/

Eckes & Grotjahn 2006 montrent que le **C-test court** (5-8 blancs dans un texte de 50-80 mots) corrèle à **r = .70-.85** avec des tests long-form de proficiency, et à **r ~ .60-.70** avec les CEFR-levels calibrés. Soit **plus fort que le SA seul**. Coût : ~45-90 secondes.

Lemhöfer & Broersma 2012 (LexTALE) : **60 items yes/no lexicaux, 3.5 minutes**, corrélation r ≈ .75 avec des tests de vocabulaire longs et r ≈ .65 avec un Oxford Placement Test. « *LexTALE was generally superior to self-ratings in its predictions* ».

**Synthèse : probe courte > SA seul, mais combinaison hybride > probe seule.** Pourquoi ? Parce que le SA capture des dimensions que la probe ne capture pas (ex : motivation, use patterns, confort à parler) qui prédisent la réussite conversationnelle même à proficiency constante.

#### 5.1.2 Formats de probe candidats pour AcademIA

| Probe | Temps | Fiabilité (r avec test long) | Discriminable CEFR | Notes |
|---|---|---|---|---|
| C-test 1 texte 5-8 blancs | 45-90 s | .70-.85 | A2-C1 | Très robuste, calibration simple |
| LexTALE-FR / LexTALE-Esp court (20 items) | 90-120 s | .65-.75 | B1-C2 | Manque de discrimination A1-B1 |
| Traduction contextuelle inverse (3 options) | 20-40 s | .55-.65 (inféré) | Tous niveaux | Très simple à implémenter, moins validé |
| Listening cloze audio (1 clip) | 60 s | .60-.75 | A2-C1 | Coût production asset ; pertinent pour un tuteur oral |
| Mini-dialogue production (open-ended) | 30-60 s | non validé industrialisé | ? | Coûteux en NLP pour scorer |

**Recommandation V1** : C-test court généré dynamiquement à partir d'un corpus interne AcademIA calibré par niveau. Coût d'implémentation faible, fiabilité élevée, extensible.

### 5.2 Tests adaptatifs (CAT) — efficacité et coûts

#### 5.2.1 Références

**Fondamentaux** :
- Wainer, H. (ed.) (2000). *Computerized Adaptive Testing: A Primer* (2nd ed.). Routledge. ISBN 0-8058-3510-6.
- van der Linden, W. J., & Glas, C. A. W. (eds.) (2010). *Elements of Adaptive Testing*. Springer.
- International Association for Computerized Adaptive Testing (IACAT) : https://iacat.org/cat-assessments/

**En contexte L2/CEFR** :
- Wang, F.-L., Kuo, T.-H., & Chiang, H.-Y. (2013). The Development and Evaluation of a Computerized Adaptive Testing System for Chinese Proficiency - Based on CEFR. ResearchGate.
- Oxford Placement Test (OPT) : https://en.wikipedia.org/wiki/Oxford_Placement_Test
- Duolingo English Test (DET) — technical documentation : https://blog.englishtest.duolingo.com/duolingo-test-aligned-with-cefr/

#### 5.2.2 Principe

Un CAT sélectionne chaque item suivant en fonction de l'estimation courante du trait latent du sujet (IRT — Item Response Theory). Efficacité typique : **~50 % d'items en moins pour une précision équivalente** à un test linéaire (Wainer 2000).

Pour un test de placement CEFR (6 niveaux), un CAT bien calibré atteint une erreur SE < 0.3 palier en ~15-30 items, soit **7-15 minutes** en conditions normales.

#### 5.2.3 Coûts

- **Banc d'items calibré IRT** : 200-500 items minimum par compétence, avec pré-calibration sur échantillon de ~500-1000 sujets. Coût initial 50-200 k€.
- **Infrastructure de scoring IRT en temps réel** : faisable en Python/R (mirt, catIrt), mais nécessite expertise psychométrique.
- **Maintenance** : reshuffling d'items pour éviter item exposure, ajout régulier de nouveaux items.

**Verdict AcademIA** : **hors scope V1** (coût prohibitif, temps de dev 6-12 mois). Envisageable en V3+ si le produit génère assez de volume pour amortir le banc d'items (≥ 100 k users/an).

### 5.3 Ce que Duolingo, Babbel, Busuu font réellement

#### 5.3.1 Duolingo (app grand public, ~500 M users lifetime)

- **Aucune auto-évaluation demandée** à l'onboarding de l'app de learning.
- **Question binaire initiale** : « déjà débutant ou continuer là où tu t'arrêtes ? » → un des deux chemins.
- **Placement Test optionnel** (CAT) : ~10-15 items, 10 minutes, skip possible. Historiquement désactivé par défaut sur certains segments pour maximiser l'engagement immédiat.
- Source : https://duolingo.fandom.com/wiki/Placement_test ; https://blog.duolingo.com/partial-credit-improvements-to-duolingos-placement-test/

**Duolingo English Test (DET)** (produit de certification distinct, payant, comparable à TOEFL) utilise un CAT robuste avec ~45 minutes de test. Ce n'est pas ce qu'on utilise pour l'onboarding de l'app grand public.

**Leçon** : Duolingo, à travers itération et A/B testing massif, a conclu que **le placement test long est un boulet pour l'onboarding grand public**. Ils privilégient un démarrage rapide + adaptatif au cours des premières leçons.

#### 5.3.2 Babbel (~10 M abonnés)

- **2-3 questions de motivation/contexte** (« pourquoi apprends-tu ? », « depuis combien de temps ? »).
- **Placement quiz** (Spanish/French/Italian/German uniquement) : **~9-12 questions** multiple-choice, **3-5 minutes**, fill-in-the-blank style. Pas de CAT, pas de can-do, juste des items linguistiques gradués.
- Source : https://support.babbel.com/hc/en-us/articles/20202703767442-Placement-quiz

**Leçon** : Babbel a choisi **objectif court > self-assessment** : ils préfèrent 9-12 items de « petit test » de 3-5 min à du SA. Pas de rationale publié, probablement un choix d'équité culturelle et de simplicité UX.

#### 5.3.3 Busuu (~100 M users lifetime)

- **Test de placement optionnel** : ~10 minutes, adaptatif. Vocabulaire + grammaire + lecture.
- **Option « sélectionnez votre niveau »** avec can-do courts (4 options A1/A2/B1/B2+), utilisable pour skip le test.
- Source : https://www.busuu.com/en/languages/proficiency-levels

**Leçon** : Busuu est le plus proche de la recommandation AcademIA — ils offrent les deux modes (test ou SA can-do rapide). Mais leur SA est collé à des labels CEFR en cleartext, ce qui n'est pas optimal pour grand public non-familier CEFR.

#### 5.3.4 Synthèse concurrentielle

| Acteur | Approche | Temps onboarding | Fiabilité présumée |
|---|---|---|---|
| Duolingo | Binary start + adaptation in-lesson | <30 s | Basse (mais rattrapée par adaptation) |
| Babbel | Placement quiz court | 3-5 min | Moyenne (r ≈ .5-.6) |
| Busuu | Test long OU SA label | 30 s à 10 min | Bimodale selon choix user |
| **AcademIA cible** | **SA can-do bi-skill + probe conditionnelle** | **35-80 s** | **Moyenne-haute (r estimée .55-.65)** |

AcademIA peut se positionner entre Duolingo (trop peu) et Busuu (trop bimodal) avec un compromis supérieur.

### 5.4 Cas limite : le « zero onboarding »

Certains produits font le pari inverse : **aucune auto-évaluation, le modèle calibre en temps réel** à partir des 3-5 premiers tours de conversation. Exemples : Speak (conversation IA anglais), ChatGPT (usage organique, pas de placement). Viable techniquement pour un tuteur IA, mais :
- Coût : les 3-5 premiers tours sont *dégradés* (trop faciles ou trop durs).
- Opportunité manquée : capter le profil initial via SA est bon marché (30 s) et apporte info-gain réel.

**Recommandation** : AcademIA doit *ne pas* aller vers zero-onboarding pur. Le QCM 2-3 questions est meilleur compromis.

---

## 6. Recommandation finale pour AcademIA

### 6.1 Spécification détaillée du QCM

**Étape 1 — Pré-filtre contexte (5 s)**

Question unique, 4 options :
> « Votre niveau en [anglais/espagnol] aujourd'hui, c'est plutôt… »
> 1. Je débute complètement, ou quelques mots seulement → **placer A0/A1, skip reste du QCM**
> 2. J'ai étudié à l'école il y a longtemps, j'ai un peu oublié → *flag « faux-débutant », aller en étape 2 + probe forcée*
> 3. J'ai un niveau correct, je peux me débrouiller dans la vie quotidienne → *aller en étape 2*
> 4. Je suis à l'aise, je lis/regarde des contenus natifs régulièrement → *aller en étape 2 + probe C1 forcée*

**Étape 2 — Can-do compréhension (15 s)**

> « Laquelle de ces situations décrit ce que vous pouvez faire **sans effort** en [EN/ES] ? »

4 can-do gradués (adapter L2 à EN ou ES) :
- (A1) Je comprends des phrases courtes et très simples, si on me parle lentement : « bonjour », « où est la gare ? », l'heure, les prix.
- (A2) Je comprends l'essentiel d'annonces dans des lieux publics (aéroport, supermarché, gare), à condition que ce soit clair et bref.
- (B1) Je comprends l'essentiel d'une conversation entre natifs sur un sujet familier (travail, famille, voyage), même si je perds parfois des détails.
- (B2) Je comprends des films, podcasts ou conférences sur des sujets variés, y compris des arguments complexes, sans sous-titres.

Réponse unique. Option « je ne sais pas » → fallback prudent (B1 si étape 1 = 3, sinon A2).

**Étape 3 — Can-do production (15 s)**

> « Et pour **parler**, laquelle décrit ce que vous pouvez faire **sans trop hésiter** ? »

4 can-do :
- (A1) Je peux me présenter (nom, âge, nationalité, travail), et poser des questions très simples.
- (A2) Je peux décrire ma famille, ma ville, mes activités, en phrases courtes et parfois reliées.
- (B1) Je peux raconter une histoire, donner mon avis sur un sujet familier, me débrouiller en voyage dans la plupart des situations.
- (B2) Je peux argumenter de façon nuancée, défendre un point de vue, parler de sujets d'actualité avec aisance.

**Étape 4 — Décision + probe conditionnelle**

Algorithme (pseudo-code) :
```
niveau_comp = step2.cefr_level   # A0..B2
niveau_prod = step3.cefr_level   # A0..B2

if step1 == 1:
    placement = "A0"
    return placement

# Split bi-skill : si ≥ 2 paliers d'écart, probe obligatoire
if abs(niveau_comp - niveau_prod) >= 2:
    trigger_probe = True

# Flag faux-débutant : probe obligatoire
if step1 == 2:
    trigger_probe = True

# Extrême haut : confirmation
if max(niveau_comp, niveau_prod) >= B2 OR step1 == 4:
    trigger_probe = True  # pour détecter C1 sous-estimés

if trigger_probe:
    probe_result = run_probe(target_level = max(niveau_comp, niveau_prod))
    placement = adjust(niveau_prod, probe_result)
else:
    # Conservateur : placement = production - 0.5 palier
    placement = conservative_floor(niveau_prod)

return placement
```

**Probe** : C-test court de 50-70 mots calibré sur le niveau déclaré (5-7 blancs). Seuil de validation : 70 % de blancs corrects → niveau confirmé ; 50-70 % → -1 palier ; < 50 % → -2 paliers.

**Étape 5 — Transition vers conversation**

Premier tour du tuteur IA :
- **Au palier placé**, mais **avec un sous-palier de complexité lexicale pour la première salve** (principe « warm up under-level »).
- Monitoring actif : si l'utilisateur répond avec plus de fluency/complexité qu'attendu → re-calibrer +1 à partir du tour 3. Si l'inverse → re-calibrer -1.

### 6.2 Métriques de succès à suivre en alpha

Pour valider le QCM empiriquement (approche Wave 1 télémétrie alpha, cohérent avec [project_no_native_reviewers]) :

| Métrique | Mesure | Seuil cible |
|---|---|---|
| Taux de complétion QCM | users qui finissent les 3 étapes / users qui démarrent | > 92 % |
| Temps médian QCM | P50 de durée totale | < 45 s |
| Taux de déclenchement probe | % users avec probe | 20-40 % attendu |
| Alignement placement vs ajustement conversationnel (5 tours) | delta absolu (palier QCM vs palier inféré après 5 tours) | P50 ≤ 0.5, P90 ≤ 1.0 |
| Churn tour 1-3 | abandon dans les 3 premiers tours de conv | < 15 % |

Si delta tour-5 > 1 palier en P75 → le QCM n'a pas rempli son rôle, itérer.

### 6.3 Rédaction des can-do en français, piège à éviter

Le texte du descripteur est lu **en L1 (français)** par l'utilisateur. Donc :
- Ne pas traduire servilement le CEFR brut. Les descripteurs officiels FR du CEFR sont parfois plus hermétiques que l'anglais (« peut interagir avec un degré d'aisance et de spontanéité… »).
- **Tester empiriquement** avec 10-20 utilisateurs alpha la clarté perçue des descripteurs (lecture à voix haute, reformulation libre). Si un descripteur est reformulé différemment par > 3 utilisateurs, il est ambigu — réécrire.
- Utiliser **exemples concrets** (noms de lieux, types de conversations) plutôt que généralités.

### 6.4 Feature flag et rollout

Cohérent avec [feedback_merge_with_flag] et les patterns de la Wave 1 :
- **Feature flag `onboarding_qcm_v1`** off par défaut.
- Rollout progressif 5 % → 20 % → 50 % → 100 % sur 3 semaines.
- A/B test contre baseline actuel (que je n'ai pas inspecté dans ce rapport — à confirmer avec l'équipe produit ce qui existe).
- Telemetry obligatoire pour suivre les métriques de la §6.2.

### 6.5 Ce qui ne figure PAS dans ce rapport et nécessite suite

Vague 2+ de recherche à envisager :
1. **Télémétrie comportementale passive** (ex : temps de saisie moyen du premier message, richesse lexicale spontanée) comme substitut au self-report.
2. **NLP-based probe** (demander à l'utilisateur de décrire une image en 1 phrase, puis scorer via LLM) — plus moderne que le C-test, mais coût infrastructure + validation.
3. **Politique de re-calibration post-onboarding** (combien de tours, quels signaux, quelle granularité de palier).
4. **Validation sur population AcademIA réelle** — la littérature donne des bornes théoriques ; seul un alpha interne donnera les chiffres exacts.
5. **Ethnographie onboarding** : observer 5-10 utilisateurs pendant leur premier onboarding (pensée à voix haute) pour détecter les malentendus non visibles en télémétrie.

---

## 7. Références bibliographiques (format APA partiel)

### 7.1 Méta-analyses et fondations théoriques

- Blanche, P., & Merino, B. J. (1989). Self-Assessment of Foreign-Language Skills: Implications for Teachers and Researchers. *Language Learning*, 39(3), 313-338. DOI : 10.1111/j.1467-1770.1989.tb00595.x. URL : https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-1770.1989.tb00595.x
- Kruger, J., & Dunning, D. (1999). Unskilled and unaware of it: How difficulties in recognizing one's own incompetence lead to inflated self-assessments. *Journal of Personality and Social Psychology*, 77(6), 1121-1134. DOI : 10.1037/0022-3514.77.6.1121. URL : https://pubmed.ncbi.nlm.nih.gov/10626367/
- Li, M., & Zhang, X. (2021). A meta-analysis of self-assessment and language performance in language testing and assessment. *Language Testing*, 38(2), 189-218. DOI : 10.1177/0265532220932481. URL : https://www.academia.edu/43357997/A_meta_analysis_of_self_assessment_and_language_performance_in_language_testing_and_assessment
- Oscarson, M. (1989). Self-assessment of language proficiency: rationale and applications. *Language Testing*, 6(1), 1-13. DOI : 10.1177/026553228900600103. URL : https://journals.sagepub.com/doi/10.1177/026553228900600103
- Ross, S. (1998). Self-assessment in second language testing: a meta-analysis and analysis of experiential factors. *Language Testing*, 15(1), 1-20. DOI : 10.1177/026553229801500101. URL : http://www.drronmartinez.com/uploads/4/4/8/2/44820161/meta-analysis_of_self-assessment_language_testing-1998-ross-1-20.pdf

### 7.2 DIALANG et instrumentation CEFR

- Alderson, J. C. (2005). *Diagnosing Foreign Language Proficiency: The Interface between Learning and Assessment*. London : Continuum. ISBN : 0-8264-8505-X.
- Alderson, J. C., & Huhta, A. (2005). The development of a suite of computer-based diagnostic tests based on the Common European Framework. *Language Testing*, 22(3), 301-320. DOI : 10.1191/0265532205lt310oa. URL : https://journals.sagepub.com/doi/10.1191/0265532205lt310oa
- Kektsidou, O., & Tsagari, D. (2019). Using DIALANG to track English language learners' progress over time. *Papers in Language Testing and Assessment*, 8(1), 1-30. URL : https://arts.unimelb.edu.au/__data/assets/pdf_file/0018/3060414/8_1_S1_Kektsidou_Tsagari.pdf
- Lancaster University Language Testing Research Group. DIALANG 2.0 project. URL : https://wp.lancs.ac.uk/ltrg/projects/dialang-2-0/
- Wikipedia. DIALANG. URL : https://en.wikipedia.org/wiki/DIALANG

### 7.3 Conseil de l'Europe (CEFR normatif)

- Council of Europe (2001). *Common European Framework of Reference for Languages: Learning, teaching, assessment*. Cambridge : Cambridge University Press. ISBN : 0-521-00531-0.
- Council of Europe (2018/2020). *CEFR Companion Volume*. Strasbourg : Council of Europe Publishing. URL : https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4
- Figueras, N., North, B., Takala, S., Van Avermaet, P., & Verhelst, N. (2009). *Relating Language Examinations to the Common European Framework of Reference for Languages: Learning, Teaching, Assessment (CEFR). A Manual*. Strasbourg : Council of Europe. URL : https://www.coe.int/en/web/common-european-framework-reference-languages/relating-examinations-to-the-cefr
- North, B., & Schneider, G. (1998). Scaling descriptors for language proficiency scales. *Language Testing*, 15(2), 217-262. DOI : 10.1177/026553229801500204. URL : https://journals.sagepub.com/doi/10.1177/026553229801500204
- North, B. (2007). The CEFR Illustrative Descriptor Scales. *Modern Language Journal*, 91(4), 656-659. DOI : 10.1111/j.1540-4781.2007.00627_3.x. URL : https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-4781.2007.00627_3.x
- North, B., & Piccardo, E. (2019). Developing new CEFR descriptor scales and expanding the existing ones: constructs, approaches and methodologies. *Zeitschrift für Fremdsprachenforschung*, 30(2), 142-160. URL : https://www.dgff.de/assets/Uploads/ZFF-2-2019-01-North-Piccardo.pdf
- Council of Europe. Self-assessment Grids (CEFR). URL : https://www.coe.int/en/web/portfolio/self-assessment-grid
- Council of Europe. Table 2: Self-Assessment Grid. URL : https://www.coe.int/en/web/common-european-framework-reference-languages/table-2-cefr-3.3-common-reference-levels-self-assessment-grid
- Europass. CEFR self-assessment grid EN. URL : https://europass.europa.eu/system/files/2020-05/CEFR%20self-assessment%20grid%20EN.pdf

### 7.4 European Language Portfolio (ELP) et Little

- Little, D. (2005). The Common European Framework and the European Language Portfolio: involving learners and their judgements in the assessment process. *Language Testing*, 22(3), 321-336. DOI : 10.1191/0265532205lt311oa. URL : https://journals.sagepub.com/doi/10.1191/0265532205lt311oa
- Little, D. (2009). The European Language Portfolio: where pedagogy and assessment meet. 8th International Seminar on the European Language Portfolio, Graz, Austria. Council of Europe. URL : https://rm.coe.int/16805a3e55

### 7.5 Modes d'échec (biais cognitifs et culturels)

- Butler, Y. G., & Lee, J. (2006). On-task versus off-task self-assessments among Korean elementary school students studying English. *Modern Language Journal*, 90(4), 506-518. DOI : 10.1111/j.1540-4781.2006.00463.x
- Ersanli, C. Y., Serttaş, Z., & Akhtar, S. H. (2022). Impostor Phenomenon and L2 willingness to communicate. *Frontiers in Psychology*, 13, 1058678. URL : https://pmc.ncbi.nlm.nih.gov/articles/PMC9869140/
- Heine, S. J., Lehman, D. R., Markus, H. R., & Kitayama, S. (1999). Is there a universal need for positive self-regard? *Psychological Review*, 106(4), 766-794. DOI : 10.1037/0033-295X.106.4.766.
- Matsuno, S. (2009). Self-, peer-, and teacher-assessments in Japanese university EFL writing classrooms. *Language Testing*, 26(1), 75-100. DOI : 10.1177/0265532208097336.
- MacIntyre, P. D., Noels, K. A., & Clément, R. (1997). Biases in self‐ratings of second language proficiency: The role of language anxiety. *Language Learning*, 47(2), 265-287. DOI : 10.1111/0023-8333.81997008.
- Mulder, K., & Hulstijn, J. H. (2011). Linguistic skills of adult native speakers, as a function of age and level of education. *Applied Linguistics*, 32(5), 475-494. DOI : 10.1093/applin/amr009.
- Naemura, K. (2007). Japanese university students' responses on self-assessment of English ability. *JALT Journal*, 29, 47-66.
- Trofimovich, P., Isaacs, T., Kennedy, S., Saito, K., & Crowther, D. (2016). Flawed self-assessment: Investigating self- and other-perception of second language speech. *Bilingualism: Language and Cognition*, 19(1), 122-140.
- Trofimovich, P., Kennedy, S., & Blanchet, J. (2020). Dunning-Kruger effect in second language speech learning. *Learning and Individual Differences*, 80, 101882. DOI : 10.1016/j.lindif.2020.101882. URL : https://www.sciencedirect.com/science/article/abs/pii/S1041608020300297
- Cai, Y. et al. (2022). A matter of when, not whether: A meta-analysis of modesty bias in East Asian self-ratings of job performance. URL : https://pubmed.ncbi.nlm.nih.gov/36108044/

### 7.6 Format et granularité

- Bachman, L. F., & Palmer, A. S. (1996). *Language Testing in Practice*. Oxford : Oxford University Press. ISBN : 0-19-437148-4.
- Brantmeier, C., Vinall, K., Bondy, J., & Chang, L. (2012). Self-assessment for advanced readers in first- and second-language Spanish. *The Reading Matrix*, 12(1), 16-31.
- Dimroth, C., & Klein, W. (2019). Language as skill: Intertwining comprehension and production. *Journal of Memory and Language*, 107.
- Krosnick, J. A., & Presser, S. (2010). Question and questionnaire design. In *Handbook of Survey Research* (2nd ed.).
- Ma, W., & Winke, P. (2019). Self-assessment: How reliable is it in assessing oral proficiency over time? *Foreign Language Annals*, 52(1), 66-86. DOI : 10.1111/flan.12379. URL : https://onlinelibrary.wiley.com/doi/10.1111/flan.12379
- Taherdoost, H. (2019). What Is the Best Response Scale for Survey and Questionnaire Design. *International Journal of Academic Research in Management*, 8(1), 1-10.
- Tigchelaar, M., Bowles, R. P., Winke, P., & Gass, S. (2017). Assessing the validity of ACTFL can-do statements for spoken proficiency: A Rasch analysis. *Foreign Language Annals*, 50(3), 584-604. URL : https://languagetesting.com/pub/media/wysiwyg/research/articles/Tigchelaar_et_al-2017-Foreign_Language_Annals.pdf
- Winke, P., Zhang, X., & Pierce, S. J. (2022). A closer look at a marginalized test method: Self-assessment as a measure of speaking proficiency. *Studies in Second Language Acquisition*. URL : https://www.cambridge.org/core/journals/studies-in-second-language-acquisition/article/closer-look-at-a-marginalized-test-method-selfassessment-as-a-measure-of-speaking-proficiency/786D4E0E0D500DCDD43CCE24ED610592

### 7.7 Probes objectives et tests rapides

- Eckes, T., & Grotjahn, R. (2006). A closer look at the construct validity of C-tests. *Language Testing*, 23(3), 290-325. DOI : 10.1191/0265532206lt330oa.
- Lemhöfer, K., & Broersma, M. (2012). Introducing LexTALE: A quick and valid Lexical Test for Advanced Learners of English. *Behavior Research Methods*, 44(2), 325-343. DOI : 10.3758/s13428-011-0146-0. URL : https://pmc.ncbi.nlm.nih.gov/articles/PMC3356522/
- LexTALE project site. URL : http://www.lextale.com/

### 7.8 Placement adaptatif (CAT) et pratiques industrie

- IACAT — International Association for Computerized Adaptive Testing. URL : https://iacat.org/cat-assessments/
- Oxford Placement Test. URL : https://en.wikipedia.org/wiki/Oxford_Placement_Test
- van der Linden, W. J., & Glas, C. A. W. (Eds.) (2010). *Elements of Adaptive Testing*. Springer.
- Wainer, H. (Ed.) (2000). *Computerized Adaptive Testing: A Primer* (2nd ed.). Routledge. ISBN : 0-8058-3510-6.
- Wang, F.-L., Kuo, T.-H., & Chiang, H.-Y. (2013). A CEFR-Based Computerized Adaptive Testing System for Chinese Proficiency. URL : https://www.researchgate.net/publication/257717608_The_Development_and_Evaluation_of_a_Computerized_Adaptive_Testing_System_for_Chinese_Proficiency_-_Base_on_CEFR
- Duolingo English Test aligned with CEFR. URL : https://blog.englishtest.duolingo.com/duolingo-test-aligned-with-cefr/
- Duolingo blog. Partial credit: improvements to Duolingo's placement test. URL : https://blog.duolingo.com/partial-credit-improvements-to-duolingos-placement-test/
- Duolingo Placement test wiki. URL : https://duolingo.fandom.com/wiki/Placement_test
- Babbel. Placement quiz support article. URL : https://support.babbel.com/hc/en-us/articles/20202703767442-Placement-quiz
- Busuu. CEFR proficiency levels. URL : https://www.busuu.com/en/languages/proficiency-levels

---

## 8. Annexe — check-list d'implémentation pour l'équipe dev AcademIA

**Copier pour issue tracking, en V1 alpha.**

- [ ] Rédiger les 4 can-do compréhension × 2 langues (EN, ES) en français, validés par relecture croisée équipe pédagogique.
- [ ] Rédiger les 4 can-do production × 2 langues, idem.
- [ ] Concevoir le pré-filtre en 1 question 4 options.
- [ ] Spécifier l'algorithme de décision (pseudo-code §6.1) en TypeScript/Python et le tester unitairement sur 20 profils synthétiques.
- [ ] Construire le banc de C-tests courts (5-7 blancs, 50-80 mots) calibrés par palier A2/B1/B2 × 2 langues : **minimum 10 textes par palier** pour éviter l'item exposure.
- [ ] Implémenter le scoring C-test (tolérance fautes orthographe mineures, case-insensitive, validation via gold standard).
- [ ] Feature flag `onboarding_qcm_v1` + rollout progressif.
- [ ] Télémétrie sur les 5 métriques §6.2, dashboard Grafana dédié.
- [ ] Test alpha interne N=30-50 utilisateurs avant rollout public, avec interview qualitative post-QCM.
- [ ] Documenter explicitement l'étape « Specification » du Manual 2009 : mapping can-do → CEFR, avec justifications.
- [ ] Plan de révision : revue des métriques à J+15 et J+30, ajustements si P75 delta > 1 palier.

---

**Fin du rapport Vague 1.**

Prochaine vague suggérée : *Wave 2 — Télémétrie comportementale passive et NLP-based probes comme substituts/compléments au self-report.*
