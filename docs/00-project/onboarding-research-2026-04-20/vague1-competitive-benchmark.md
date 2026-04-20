# Vague 1 — Benchmark compétitif des onboardings

**Projet** : AcademIA — tuteur de langues IA (Teacher EN + Maestro ES, L1 français, alpha en cours)
**Date** : 2026-04-20
**Auteur** : recherche assistée par agent
**Objet** : identifier les patterns et anti-patterns réutilisables pour la refonte de l'onboarding d'AcademIA (conversationnel LLM → QCM pre-chat modal bloquant).

---

## Table des matières

1. [Contexte et cadrage](#1-contexte-et-cadrage)
2. [Executive summary — 5 patterns à voler, 5 anti-patterns à éviter](#2-executive-summary)
3. [Méthodologie](#3-méthodologie)
4. [Profils détaillés par application](#4-profils-détaillés-par-application)
   - 4.1 [Duolingo](#41-duolingo)
   - 4.2 [Babbel](#42-babbel)
   - 4.3 [Busuu](#43-busuu)
   - 4.4 [Loora AI](#44-loora-ai)
   - 4.5 [Speak](#45-speak)
   - 4.6 [Noom](#46-noom)
   - 4.7 [Headspace](#47-headspace)
5. [Synthèse transversale — patterns qui marchent, anti-patterns](#5-synthèse-transversale)
6. [Recommandations pour AcademIA](#6-recommandations-pour-academia)
7. [Annexe A — tableau comparatif](#7-annexe-a--tableau-comparatif)
8. [Annexe B — données quantitatives de rétention (benchmarks publics)](#8-annexe-b--données-quantitatives-de-rétention)
9. [Annexe C — frameworks psychologiques mobilisés](#9-annexe-c--frameworks-psychologiques-mobilisés)
10. [Annexe D — copy patterns (wording comparé)](#10-annexe-d--copy-patterns)
11. [Annexe E — checklist de décision pour le QCM AcademIA](#11-annexe-e--checklist-de-décision)
12. [Annexe F — questions non résolues et pistes Vague 2](#12-annexe-f--questions-non-résolues)
13. [Annexe G — positionnement AcademIA vs concurrents](#13-annexe-g--positionnement-academia-vs-concurrents)
14. [Annexe H — ancrage dans la recherche académique CEFR + LLM](#14-annexe-h--ancrage-dans-la-recherche-académique-cefr--llm)
15. [Annexe I — glossaire](#15-annexe-i--glossaire)
16. [Annexe J — index des patterns identifiés](#16-annexe-j--index-des-patterns-identifiés)
17. [Annexe K — journey maps comparées](#17-annexe-k--journey-maps-comparées-descriptions-en-prose)
18. [Annexe L — recommandations de lecture complémentaires](#18-annexe-l--recommandations-de-lecture-complémentaires)
19. [Annexe M — changelog de ce rapport](#19-annexe-m--changelog-de-ce-rapport)
20. [Sources](#20-sources)

---

## 1. Contexte et cadrage

### 1.1 Le problème AcademIA aujourd'hui

AcademIA est un tuteur de langues conversationnel basé sur des LLM, actuellement en alpha avec deux produits :

- **Teacher** : tuteur d'anglais, L1 français
- **Maestro** : tuteur d'espagnol, L1 français (clone Dify en cours, Wave 1 Phase C tout juste livrée)

L'onboarding actuel est **entièrement conversationnel** : dès le premier écran, le LLM engage un dialogue libre avec l'apprenant pour comprendre son niveau, ses objectifs et ses motivations. Trois pathologies observées en alpha :

1. **Language-mixing** — le tuteur mélange L1 (français) et L2 (anglais/espagnol) pendant la phase de découverte, ce qui crée une dissonance pédagogique (on est censé apprendre la langue, mais on commence en français puis on alterne).
2. **Boucle "ok"** — lorsque l'apprenant donne des réponses minimales ("oui", "ok", "d'accord"), le LLM relance sans progresser, ce qui crée une friction cognitive inutile ("pourquoi il me redemande la même chose ?").
3. **Bilan sans niveau CEFR** — à la fin du tour 1, le LLM produit un résumé textuel du profil mais ne positionne pas l'apprenant sur l'échelle A1-C2, ce qui rend impossible la calibration downstream (choix des activités, des corrections, du vocabulaire).

### 1.2 La cible de la refonte

La direction produit veut **remplacer cet onboarding conversationnel par un QCM pre-chat**, avec les caractéristiques suivantes :

- **Modal bloquant** : première visite par langue → impossible d'accéder au chat tant que le QCM n'est pas rempli.
- **Collecte en bloc** : 8-10 questions à choix multiples/sliders, pas d'open text obligatoire.
- **Préférences déclaratives** : motivation, objectif d'usage, temps disponible, niveau auto-évalué (avec can-do statements plutôt que labels A1/A2 nus), style d'apprentissage perçu.
- **Injection contexte structuré** : le résultat du QCM est sérialisé dans un JSON que le LLM reçoit en system prompt avant son **premier tour**, au lieu de devoir arracher l'info à la conversation.

### 1.3 Pourquoi ce benchmark

Avant de figer le QCM, on veut répondre à quatre questions :

- **Combien de questions** est tolérable avant que les utilisateurs ne décrochent ? (Duolingo ~7, Babbel ~17, Noom ~113 — quelles sont les vraies bornes ?)
- **Quelles variables** sont prédictives de rétention et utilisables par un LLM, vs quelles variables sont du théâtre de personnalisation ?
- **Quels formats d'input** (image picker, sliders, MCQ, placement test) convertissent le mieux sans sacrifier la qualité des données ?
- **À quel moment** intercaler le gate (avant signup ? après ? avant le 1er chat ?) ?

Le périmètre du benchmark couvre 7 apps :

- **Langues** : Duolingo, Babbel, Busuu (apps "classiques" à grande échelle), Loora, Speak (AI tutors conversationnels, cohortes AcademIA les plus proches).
- **Hors-langue, rétention-centrées** : Noom (onboarding long controversé) et Headspace (onboarding court pédagogique), pour calibrer les deux extrêmes du curseur "questionnaire long = investissement perçu" vs "questionnaire court = time-to-value".

---

## 2. Executive summary

### 2.1 Les 5 patterns à voler pour AcademIA

1. **Motivation-first, niveau ensuite** (Duolingo, Headspace, Loora).
   Toutes les apps à fort rétention ouvrent par "pourquoi êtes-vous là ?" avant de demander le niveau. Cela ancre l'utilisateur émotionnellement ("voyage", "famille", "travail"), personnalise visiblement la suite, et permet au LLM d'adapter le registre (vocabulaire touristique vs business, formel vs familier). Pour AcademIA : question 1 du QCM doit être la motivation, pas le niveau.

2. **Auto-évaluation + placement test optionnel conditionnel** (Duolingo, Babbel, Busuu).
   Les débutants déclarés sautent le placement test → 0 friction. Les "intermédiaires / avancés" déclarés se voient proposer un test de placement court (3-5 minutes). Ça évite le chemin de croix pour les gens qui savent qu'ils partent de zéro, et ça calibre précisément ceux qui ne savent pas. Pour AcademIA : placement test **jamais bloquant avant le premier chat**, mais proposable en option pour les auto-déclarés "B1+".

3. **Temps perçu compressé par la personnalisation visible** (Noom, Headspace, Loora).
   Chaque réponse déclenche un écran de feedback ("On va adapter tes leçons à X…", "Tu n'es pas seul, 73 % des apprenants ont commencé comme toi…"). Ça transforme un questionnaire en dialogue perçu. Principe Noom : *"Length isn't the enemy; emptiness is."* Pour AcademIA : chaque question du QCM doit être suivie d'un mini écran d'acquittement ou d'un indicateur de progression qui confirme que la réponse est intégrée.

4. **Commitment device léger : slider de temps quotidien** (Duolingo, Headspace, Busuu, Babbel).
   Demander "combien de minutes par jour ?" (5/10/15/20) sert trois fonctions cumulées : (a) calibration réaliste du contenu, (b) engagement par effet de consistance (Cialdini), (c) setup des rappels. Duolingo nomme les niveaux (Casual/Regular/Serious/Intense), ce qui active aussi l'effet d'identité. Pour AcademIA : slider de temps = obligatoire, mais nommer les niveaux par des verbes d'action plutôt que des adjectifs de charge ("découvrir" / "pratiquer" / "progresser" / "intensif").

5. **Image picker pour les variables abstraites** (Duolingo, Noom, Headspace).
   Pour les motivations, les objectifs émotionnels, les styles perçus, des tuiles visuelles avec illustration + label convertissent mieux que des listes textuelles. L'image réduit la charge cognitive, ancre en mémoire, et évite le piège du jargon (A1/A2 = jargon ; "je sais commander un café" = concret). Pour AcademIA : motivation et niveau perçu doivent passer par un image picker avec illustrations et can-do statements.

### 2.2 Les 5 anti-patterns à éviter absolument

1. **Le "hostage flow" à la Noom** (~113 écrans, 15-30 minutes).
   Ce qui marche pour une app de perte de poids où l'investissement temporel renforce la monétisation par sunk cost **ne transfère pas** à une app d'apprentissage de langues où la valeur est délivrée par la pratique. Un QCM de 113 écrans sur AcademIA tuerait l'engagement — on n'a pas le même contrat implicite que Noom ("je te donne 30 minutes de ma vie contre un plan personnalisé que je vais suivre 6 mois"). Plafond recommandé : 10 questions, 2 minutes de remplissage.

2. **Placement test forcé pré-signup** (cf. critique Drops case study).
   Si on bloque l'accès au chat par un test de placement obligatoire, on perd les prospects "curieux" (ceux qui veulent tester avant de s'engager). Le placement test doit être **opt-in** et positionné après une première expérience de valeur, ou réservé aux auto-déclarés intermédiaires/avancés.

3. **Open text obligatoire au lieu de MCQ**.
   C'est précisément l'erreur actuelle d'AcademIA : le LLM pose des questions ouvertes et tente d'extraire l'info. Résultats constatés : boucles "ok", language-mixing, bilans flous. Le QCM en bloc est une régression ergonomique apparente mais un gain qualitatif massif : (a) données structurées, (b) temps de remplissage contrôlé, (c) pas de dépendance à la qualité des extractions LLM.

4. **Variables non prédictives qui simulent la personnalisation** (e.g. "comment avez-vous entendu parler de nous ?" chez Babbel, demandé en plein milieu de l'onboarding).
   Deux sources le pointent comme friction : Braingineers (neuromarketing Duolingo) et Babbel lui-même (testing interne). Toute variable collectée doit alimenter soit (a) le system prompt du LLM, soit (b) un nudge personnalisé visible dans les 3 premières sessions. Sinon c'est du théâtre qui augmente le churn pré-chat.

5. **Labels CEFR nus (A1/A2/B1…) comme options de niveau**.
   Les L2 débutants ne savent pas ce que veulent dire ces acronymes. Busuu et Babbel les utilisent mais compensent par un libellé ("A1 — débutant absolu"). Les can-do statements (pattern Duolingo : *"Je comprends des phrases simples comme 'Je voudrais un café'"*) convertissent mieux et calibrent plus précisément. Pour AcademIA : jamais de A1/A2 en premier niveau de lecture, toujours un can-do d'abord.

---

## 3. Méthodologie

### 3.1 Sources consultées

Trois types de sources, hiérarchisées :

1. **Primaires** : blog produit des apps elles-mêmes (Babbel Design Medium, Duolingo Engineering), annonces presse sourcées (TechCrunch, OpenAI blog pour Speak), captures Mobbin / PageFlows / ScreensDesign (dépôts de référence UX qui archivent les flows réels).
2. **Secondaires analytiques** : études de cas UX (Appcues GoodUX, UserGuiding, Justinmind, The Behavioral Scientist, Growth Waves Substack), reviews d'utilisateurs experts (FluentU, LanguaTalk, Mid.oo).
3. **Tertiaires** : articles-listes best practices (évités sauf pour triangulation).

Wikipédia et articles SEO génériques **explicitement exclus**. Quand une info est sourcée d'un seul canal secondaire, c'est signalé.

### 3.2 Limites de la recherche

- **Les captures live ne sont pas transcrites** : plusieurs sources (AppFuel, Mobbin, PageFlows) archivent des screenshots mais sans OCR. On a donc dû croiser les comptes rendus textuels pour reconstruire le détail des écrans.
- **Les flows évoluent vite** : les apps font du A/B testing permanent. Une description "2024" peut être obsolète en 2026. Quand possible, on signale la date de la source.
- **Speak reste opaque** : aucune source publique ne documente finement son onboarding écran par écran (hors Mobbin / site officiel). La description ci-dessous est donc partielle.
- **Pas de natifs pour vérifier** : cf. memory `project_no_native_reviewers.md` — on ne peut pas valider la pertinence des can-do statements cibles auprès d'un C2 ES/IT/DE/JP/RU.

### 3.3 Grille d'analyse appliquée à chaque app

Pour chaque app, on documente :

- **Structure** : nombre d'étapes, durée estimée, types d'inputs (MCQ, slider, image picker, open text, placement test, freemium gate).
- **Variables collectées** : motivation, objectifs, niveau auto-évalué, temps dispo, style perçu, démographie, santé/historique (pour Noom).
- **Tactiques de rétention** : investment moment (où la valeur est promise), personnalisation visible (feedback immédiat), commitment device (engagement d'avenir), social proof.
- **Bloquant vs optionnel** : qu'est-ce qui est obligatoire avant d'accéder au produit core ? Qu'est-ce qui est reportable ?

---

## 4. Profils détaillés par application

### 4.1 Duolingo

**Catégorie** : langues, gamifié, freemium, ~500M users, L1 universel.
**Sources principales** : Appcues GoodUX, UserGuiding, Braingineers, AppFuel, Duolingo Help Center, Mobbin.

#### 4.1.1 Structure

Durée : **~90 secondes à 2 minutes**. Nombre d'écrans : variable selon A/B test, **23 écrans documentés sur mobile iOS** (ScreensDesign), dont ~7-8 vraies questions. Le reste = écrans d'acquittement, animations de Duo, valeur propositionnelle.

Séquence reconstruite (mobile, 2024-2025) :

1. **Splash mascotte** — Duo l'hibou apparaît, salut animé, zéro texte engagé. Fonction : baby-schema effect, ton ludique posé d'emblée (source : Braingineers).
2. **Sélection de la langue cible** — liste scrollable de ~40 langues avec drapeaux. Historiquement critiquée (absence de search), UI depuis optimisée avec regroupements par région.
3. **Question "Où as-tu entendu parler de Duolingo ?"** — Facebook / Google / TV / bouche-à-oreille / autre. *Anti-pattern documenté par Braingineers : "évoque des émotions négatives, perçu comme inattendu et non pertinent". Garde-t-il sa place uniquement pour les besoins marketing attribution ; à ne pas dupliquer pour AcademIA.*
4. **Motivation** — *"Pourquoi apprends-tu cette langue ?"* — tuiles avec icônes : voyage, famille, école, travail, culture, amusement du cerveau, autre. Image picker typique ; ~6 options ; max 1 choix.
5. **Niveau auto-déclaré** — *"Quel est ton niveau en [langue] ?"* — deux chemins :
   - Tuile "Je suis complètement débutant·e" → skip placement, direction lesson 1 Unit 1.
   - Tuile "J'en connais déjà un peu" → placement test adaptatif de 5 minutes.
6. **Daily goal / commitment device** — 4 options nommées :
   - **Casual** : 5 min/jour
   - **Regular** : 10 min/jour
   - **Serious** : 15 min/jour
   - **Intense** : 20 min/jour
   Chaque option est illustrée par un nombre de flammes (streaks), image picker implicite. L'utilisateur peut changer après (cf. Duolingo Help Center).
7. **(Placement test conditionnel)** — exercices courts en ramp-up difficulté, permet de skipper des unités. Durée ~3-5 min.
8. **"Juste encore 7 questions avant ta 1re leçon"** — compteur de progression explicite, marker d'investissement.
9. **Écran de valeur ("Voici ton parcours personnalisé")** — affiche une roadmap avec unités débloquées/verrouillées.
10. **Première leçon — avant signup** — gradual engagement : l'utilisateur fait une vraie leçon, gagne XP, voit progression. *Le signup apparaît seulement APRÈS cette micro-victoire.* A/B tests internes Duolingo ont montré que delayed signup performe mieux que signup front-loaded (source : Appcues).

#### 4.1.2 Variables collectées

- Langue cible (obligatoire)
- Source d'acquisition (attribution marketing, pas utilisée pour persona)
- Motivation parmi ~6 catégories (utilisée pour adaptation contextuelle du vocabulaire dans certains lessons)
- Niveau de départ (binary : débutant ou non)
- Résultats du placement test (si pris) → saut dans le skill tree
- Daily goal en minutes/XP

Remarquablement, Duolingo **ne demande pas** : âge, métier, style d'apprentissage perçu, attentes sur la méthode. Le profil est minimal.

#### 4.1.3 Tactiques de rétention

- **Baby schema + animations** : Duo l'hibou désamorce le stress cognitif, le temps passe sans être perçu comme "questionnaire" (Braingineers).
- **Gradual engagement** : signup repoussé APRÈS la première XP gagnée → biais de consistance, sunk cost positif.
- **Commitment device** : le daily goal est un engagement public (visible sur le profil), renforcé par les streaks.
- **Compteur "encore X questions"** : progressive disclosure qui réduit l'anxiété d'incertitude.
- **Réciprocité** : Duolingo donne une leçon gratuite avant de demander un compte.

#### 4.1.4 Ce qui est bloquant vs optionnel

| Élément | Bloquant avant 1er cours ? |
|---|---|
| Sélection langue cible | Oui |
| Motivation | Oui (pas de "skip") |
| Niveau auto-déclaré | Oui |
| Placement test | Non — uniquement pour auto-déclarés "j'en connais déjà" |
| Daily goal | Oui (mais modifiable ensuite) |
| Création de compte | **Non** — peut être fait après la 1re leçon |
| Notifications | Non — demandé après 1-2 jours d'usage |

#### 4.1.5 Enseignements pour AcademIA

- Structure cible : 6-8 vraies questions + écrans de transition.
- Motivation = tuiles image picker, pas dropdown texte.
- Daily goal = slider nommé, pas chiffre nu.
- Placement test = conditionnel, jamais imposé aux débutants déclarés.
- Zone grise pour AcademIA : Duolingo fait du delayed signup alors qu'AcademIA a un gate modal — c'est une divergence délibérée liée au contrat LLM (coût API par session oblige à qualifier avant de chatter). À assumer, mais compenser par un time-to-value très court post-QCM (première leçon dans les 30 secondes).

#### 4.1.6 Chiffres de rétention Duolingo en contexte

Pour AcademIA, la comparaison n'est pas 1:1 (Duolingo = 500M users, gamification mature depuis 12 ans), mais les ordres de grandeur Duolingo servent de **plafond théorique** à ce qu'un onboarding peut délivrer en rétention :

- **Next-day retention 2012** : 12 % (avant refonte onboarding). Cible post-refonte AcademIA : ≥ 35 % (secteur moyen B2C pour apps langues selon Userpilot / UXCam).
- **DAU/MAU Duolingo 2025** : 37 %. Cible AcademIA alpha : 15-20 % (réaliste à ce stade).
- **Impact streak** : +14 % D14 retention avec streak wager. Pour AcademIA : la mécanique streak peut venir en v2, une fois la rétention de base assainie.
- **Part DAU avec streak ≥7j** : >50 % chez Duolingo. Signal de stickiness extrême — pas un objectif réaliste en alpha mais une direction long terme.

Citation directe de Jorge Mazal (Lenny's Newsletter) sur la priorité CURR :

> "Sensitivity analysis showed CURR had 5 times the impact of the second-best metric on daily active users. […] Over four years, we achieved a 21% increase in CURR, which represented a reduction in the daily churn of our best users by over 40%."

Traduction opérationnelle pour AcademIA : se concentrer sur les **utilisateurs actifs récents** plutôt que sur l'acquisition ou la résurrection. Un QCM qui qualifie mieux = meilleur premier chat = meilleur J+1 retention = meilleur CURR.

---

### 4.2 Babbel

**Catégorie** : langues, méthode structurée, payant d'emblée (freemium limité), ~16M users payants.
**Sources principales** : Babbel Design Medium, AppFuel, Mobbin, GoodUX, Babbel Help Center.

#### 4.2.1 Structure

Durée : **~3 à 4 minutes**. Nombre d'écrans : **17 étapes documentées** (source AppFuel). C'est le plus long des onboardings langues mainstream, deux fois Duolingo.

Séquence reconstruite :

1. **Splash** — logo, tagline méthode.
2. **Sélection langue cible** — liste réduite (~14 langues chez Babbel, vs ~40 Duolingo).
3. **Motivation** — *"Pourquoi apprenez-vous [langue] ?"* — options principales : famille / carrière / voyage / culture / amis / école. MCQ à choix unique.
4. **Objectifs spécifiques** — écran séparé : *"Qu'est-ce qui vous intéresse le plus ?"* — tuiles : avoir des conversations / lire / comprendre la culture / préparer un examen. Pluri-sélection possible.
5. **Niveau auto-déclaré** — deux options principales : débutant / avancé (moins granulaire que Busuu).
6. **Placement test** — optionnel pour les "avancés", proposé avec promesse de durée ("juste quelques minutes"). C'est ici que l'équipe Design Babbel a le plus itéré : leur blog post documente 8 tests unmoderated qui ont abouti à (a) afficher la durée attendue, (b) clarifier les skills testés (grammaire + vocab + listening), (c) offrir une revue des réponses en liste.
7. **Questions démographiques** — âge + comment vous avez entendu parler de Babbel. *Même anti-pattern que Duolingo : placement sous-optimal.*
8. **Daily goal / rappel** — *"Quand souhaitez-vous apprendre ?"* — dropdown avec horaires suggérés, ancrage routine.
9. **Permissions** — microphone (pour les exercices de prononciation), notifications.
10. **Freemium gate / paywall** — très tôt chez Babbel : après la première leçon gratuite, paywall obligatoire pour continuer. *Différence majeure vs Duolingo.*

#### 4.2.2 Variables collectées

Plus riche que Duolingo :

- Langue cible
- Motivation (catégorielle)
- Objectifs d'apprentissage (multi-select)
- Niveau auto-déclaré (2 niveaux) + résultats placement test si pris (grammaire + vocab + listening, mappés sur CEFR A1-C1)
- Âge
- Source d'acquisition (anti-pattern)
- Horaire préféré de pratique
- Permissions (mic/notifs)

#### 4.2.3 Tactiques de rétention

- **Placement test valorisé** : Babbel le positionne comme "certificat low-stakes" pour rassurer sur le sérieux de la méthode (vs Duolingo qui le présente comme un raccourci).
- **Permission priming** : GoodUX documente que Babbel demande les permissions microphone avec un écran explicatif AVANT le vrai prompt iOS/Android — ça double le taux d'acceptation (*"We need microphone access to help you practice speaking…"*).
- **Objectifs multi-select** : crée l'impression d'un plan sur mesure alors que le contenu réel est largement partagé entre apprenants.

#### 4.2.4 Ce qui est bloquant

Tout le flow est bloquant jusqu'à la 1re leçon. Le paywall post-1re-leçon est lui aussi bloquant pour l'accès continu, ce qui fait de Babbel une app où le commitment gate est **payant** très tôt.

#### 4.2.5 Enseignements pour AcademIA

- Le fait que Babbel utilise 17 étapes sans s'effondrer en rétention montre qu'on peut aller au-delà de 10 questions **si le contenu perçu est pédagogique** (la conversation design de Babbel enrobe les questions avec de la justification méthode).
- En revanche, l'étape "source d'acquisition" est documentée comme friction par Braingineers chez Duolingo — **à ne pas reproduire** pour AcademIA.
- Le permission priming est un pattern à reprendre si AcademIA ajoute un jour du micro (fonctionnalité vocal).

#### 4.2.6 Détail du processus de recherche Babbel sur le placement test

L'article de Carina de Magalhães (Babbel Design Medium) vaut d'être détaillé parce qu'il documente **explicitement** le processus UX research qui a conduit au design actuel — rare dans le benchmark.

Contexte : équipe Babbel a identifié que les nouveaux utilisateurs déclaraient un niveau "au pif" (auto-éval biaisée), ce qui dégradait la pertinence des premières leçons. Hypothèse : un assessment tool de quelques minutes améliorerait le matching niveau/contenu.

Méthodologie :
- 8 tests unmoderated avec des non-utilisateurs Babbel (recrutés externes pour éviter le biais de familiarité).
- Prototype MVP : onboarding screen (durée + skills testés) + test (grammaire + vocab) + results screen + answer review.

Findings clés (quotes de l'article) :
- *"Users felt that the results screen was confusing and they didn't know how to distinguish Grammar and vocab skills."*
- *"They felt the information about the test was irrelevant."*
- Forte demande utilisateur pour tester aussi le listening (ajouté en v2).
- Forte demande pour revoir ses réponses (ajouté : answer review en liste plutôt que one-by-one).

Métriques post-launch :
- 80 % completion rate sur 2 semaines (~1900 completions).
- 90 % des utilisateurs consultent les réponses après le test.

**Leçon pour AcademIA** :
- Si on propose un placement test optionnel, dire clairement la durée à l'entrée (*"3 minutes, 10 questions"*).
- Séparer visuellement les skills testés dans le résultat (*"Compréhension : X, Grammaire : Y"*) plutôt que de ne donner qu'un niveau global.
- Offrir la revue des réponses en fin de test (pédagogique, réutilisable pour l'apprentissage).
- Cible réaliste de completion rate pour un placement opt-in : 60-80 % des auto-déclarés A2+.

---

### 4.3 Busuu

**Catégorie** : langues, community-driven (corrections par natifs), CEFR-first, ~120M users revendiqués.
**Sources principales** : FluentU, Busuu Help Center, Busuu Certification pages, AppFuel (archive de 15 screenshots d'onboarding).

#### 4.3.1 Structure

Durée : **~3 minutes**. Nombre d'écrans : ~**15 écrans documentés**.

Séquence reconstruite :

1. **Splash / signup social** — login Facebook / Google / email, très tôt.
2. **Choix langue cible** — 12 langues.
3. **Motivation** — *"Pourquoi apprenez-vous [langue] ?"* — catégories similaires aux autres (famille / voyage / travail / école).
4. **Placement test obligatoire** (source : FluentU 2024) — *"La première chose à faire en rejoignant Busuu est de compléter un test de placement"*. 4 niveaux possibles : A1 / A2 / B1 / B2. *C'est le seul de notre benchmark qui impose le placement test à tous.*
5. **Étude plan setup** — *"Quels jours voulez-vous pratiquer ?"* (multi-select jours de la semaine) + *"À quelle heure ?"* (time picker) + *"Combien de temps par jour ?"* (slider 5-30 min).
6. **Objectifs** — sélection d'objectifs (grammaire / vocab / conversation / culture).
7. **Date estimée de fin** — calculée à partir du niveau + goal + temps dispo. *Commitment device explicite : "Vous atteindrez B1 le 14 août 2026 si vous tenez votre plan."*
8. **Paywall** — Busuu Premium proposé, mais accès gratuit limité possible.

#### 4.3.2 Variables collectées

- Langue cible
- Motivation
- Niveau (via test placement obligatoire, pas auto-déclaré)
- Plan hebdomadaire : jours, heures, durée
- Objectifs d'apprentissage
- Date cible calculée
- Email / compte social

#### 4.3.3 Tactiques de rétention

- **Placement test obligatoire** : positionnement "sérieux", CEFR-first, cible les learners orientés résultats (préparation examen, exigence entreprise). *Risque : churn pré-chat plus élevé chez les curieux.*
- **Date de fin calculée** : loss aversion — si tu ne tiens pas ton plan, la date recule (commitment visible).
- **Community = social proof différé** : les corrections par natifs sont promises mais apparaissent plus tard, créant de l'anticipation.

#### 4.3.4 Ce qui est bloquant

Tout le flow, plus le placement test. C'est l'onboarding langues le plus "corporate" des trois mainstream : exhaustif, mais friction maximale à l'entrée.

#### 4.3.5 Enseignements pour AcademIA

- **Contre-exemple sur le placement test forcé** : à ne pas reproduire. Busuu peut se le permettre car son positionnement B2B et certification le justifie, AcademIA a un positionnement "tuteur personnel accessible" qui exige un time-to-value plus court.
- **Date de fin calculée** = pattern intéressant à tester en V2. Pour la V1 du QCM AcademIA, on peut se contenter d'un "plan de 4 semaines" générique affiché en écran de valeur post-QCM.
- **Plan hebdo détaillé** (jours + heures) = over-engineered pour AcademIA, on peut se contenter du slider minutes/jour comme Duolingo.

---

### 4.4 Loora AI

**Catégorie** : AI English tutor conversationnel, positionnement coaching soft skills / pro / self-confidence. Cohorte la plus proche d'AcademIA.
**Sources principales** : Icanlearn review, ScreensDesign showcase, Papora review, Mid.oo review.

#### 4.4.1 Structure

Durée : **~2-3 minutes**. Nombre d'écrans : ~**22 étapes** (source : ScreensDesign). Plus long que Duolingo/Headspace, volontairement : Loora vend un coaching premium, l'investissement questionnaire prépare le paywall.

Séquence reconstruite :

1. **Splash valeur** — *"Your Personal AI English Tutor"* — sliders de value props.
2. **Questions "challenges" / anxiétés** — *"What's your biggest challenge with English?"* — pronunciation / confidence / grammar / speaking in meetings / other. Pattern notable documenté par ScreensDesign : *"The app directly addresses user anxiety after asking about their biggest challenges, building trust early on."*
3. **Goals / profession** — Loora tend à segmenter pro (business, healthcare, IT) vs generalist.
4. **Niveau auto-déclaré** — catégoriel (débutant / intermédiaire / avancé) sans jargon CEFR.
5. **Daily practice goal** — slider minutes/jour, visualisation d'une timeline de progrès projetée (*"In 30 days, you'll be able to…"*). Pattern notable : *"When a user sets a daily practice goal, the app visualizes their projected progress on a timeline, making the long-term benefit clear."*
6. **Reminder setup** — time picker pour rappels quotidiens.
7. **Soft paywall** — écran avec 2 plans (Yearly / Monthly), badge "Save 33%" sur yearly, social proof (note moyenne + nombre de reviews).
8. **Dismiss paywall → free lesson** — si l'utilisateur ferme le paywall, Loora offre *"a free lesson as a gift"* avant de lock. Pattern smart retention : ça laisse goûter la valeur sans capituler la monétisation.

#### 4.4.2 Variables collectées

- Challenges / anxiétés (multi-select)
- Profession / contexte d'usage (pro vs general)
- Niveau auto-déclaré (3 niveaux)
- Daily goal minutes
- Horaire rappel
- Email / compte

#### 4.4.3 Tactiques de rétention

- **Anxiety-first** : unique dans notre benchmark. Poser la question "qu'est-ce qui te frustre le plus ?" active l'empathie LLM et calibre le ton du tuteur (encourageant vs rigoureux).
- **Timeline projection** : commitment device visuel puissant, crée une narrative.
- **Free lesson après dismiss paywall** : inverse le pattern Noom (Noom = pay-wall hostage, Loora = value-first after hesitation).

#### 4.4.4 Ce qui est bloquant

Le placement test n'est pas explicite chez Loora (source : reviews n'en mentionnent pas). Le QCM est bloquant avant la 1re conversation, mais **le paywall est soft** (dismissable une fois).

#### 4.4.5 Enseignements pour AcademIA

- **Anxiety question à reprendre** : "Qu'est-ce qui te bloque le plus en [langue] ?" (prononciation / grammaire / vocabulaire / confiance) — ça alimente directement le system prompt du LLM avec un signal de registre pédagogique utile ("être extra-patient sur la prononciation").
- **Timeline projection** = bon écran de valeur post-QCM pour AcademIA.
- **Pas de placement test obligatoire** = confirmation du pattern "débutants skip, avancés optionnel".

#### 4.4.6 Pourquoi Loora est la cohorte la plus directement comparable à AcademIA

Quatre raisons structurelles :

1. **Produit LLM conversationnel**, pas skill tree : comme AcademIA, pas de leçons pré-scriptées à la Duolingo ; chaque session est un dialogue IA.
2. **Premium, sans freemium massif** : ciblage utilisateur adulte motivé (pas l'audience ado gamifiée Duolingo).
3. **Focus sur l'anglais (Teacher)** puis ouverture multi-langues : trajectoire produit proche.
4. **Positionnement "coaching personnel"** : la motivation affichée côté marketing est *"improve your confidence speaking English"*, pas *"learn 500 words"*. C'est un contrat émotionnel plutôt que mécanique — aligné avec la promesse AcademIA.

Différences importantes quand même :
- Loora est mono-langue (EN only), AcademIA sera multilingue.
- Loora a un business model B2C pur, AcademIA explore B2B2C (éducation).
- Loora utilise des modèles OpenAI/Anthropic sans infrastructure propre, AcademIA construit des pipelines Dify spécifiques.

#### 4.4.7 Pattern spécifique : anxiety-first question

C'est LA trouvaille Loora qui mérite d'être répliquée. La question "Quel est ton plus gros blocage ?" fait 3 choses simultanées :

1. **Valide l'émotion** (l'utilisateur se sent compris : "oui, la prononciation c'est MON problème").
2. **Calibre le tuteur** : le LLM peut adapter son comportement.
3. **Sert de commitment device inversé** : si l'utilisateur abandonne, il abandonne en sachant que son blocage n'a pas été adressé — création d'une tension cognitive qui favorise le retour.

Copy potentiel AcademIA : *"Avant de démarrer, dis-moi : qu'est-ce qui te bloque le plus en [anglais / espagnol] ?"* — tuiles : *Prononciation* / *Grammaire* / *Vocabulaire* / *Confiance à l'oral* / *Compréhension* / *Autre*. Unicité : on peut imaginer un multi-select (2 choix max) car beaucoup d'apprenants combinent "confiance + prononciation" par exemple.

---

### 4.5 Speak

**Catégorie** : AI conversational, backed OpenAI, valorisation $1B en déc. 2024, cohorte directe d'AcademIA.
**Sources principales** : Speak.com, OpenAI blog, TechCrunch, LanguaTalk review, Practice.me review, Medium Lucien analyse.

#### 4.5.1 Structure

**Source principale indirecte** : les reviews décrivent l'onboarding comme *"smooth, with personalization questions that tailor your starting level and learning goals"*, mais aucune source ne documente le séquençage écran par écran (opacité Speak). Les URLs de speak.com exposent les slugs : `/onboarding/native-language`, `/onboarding/learning-language`, `/onboarding/goal`, ce qui permet de reconstruire une séquence probable.

Séquence probable (reconstruction à partir des slugs URL + captures Mobbin référencées) :

1. Splash + value prop.
2. **Native language** — choix L1 (Speak supporte 40+ L1, dont le français).
3. **Learning language** — choix L2 (6 langues supportées : anglais, espagnol, français, allemand, japonais, coréen).
4. **Goal** — objectif d'apprentissage (business / travel / general fluency / academic).
5. **Level** — auto-déclaré.
6. **AI interview / placement** — Speak est documenté pour faire des *"AI interviews"* pour ajuster le curriculum, mais on ne sait pas si c'est pré-chat obligatoire ou intégré aux premières sessions.
7. **Paywall 7-day trial** — Speak pousse un trial gratuit 7 jours sur carte bancaire.

#### 4.5.2 Variables collectées

Identifiables avec certitude :
- L1 (native language)
- L2 (learning language)
- Goal
- Level auto-déclaré

Probables :
- Résultats AI interview (si pris)
- Email / CB (pour trial)

#### 4.5.3 Tactiques de rétention

- **OpenAI co-branding** : Speak affiche explicitement "Powered by OpenAI" comme social proof technologique.
- **7-day trial sur CB** : commitment fort côté monétisation, friction côté acquisition.
- **AI interview adaptatif** : si c'est implémenté comme décrit, c'est un pattern hybride QCM + LLM qui intéresse directement AcademIA. Besoin d'investigation user testing directe.

#### 4.5.4 Enseignements pour AcademIA

- **Speak est la comparaison la plus proche mais la moins documentée publiquement**. Recommandation : faire une **Vague 2** de recherche terrain (installer l'app, filmer l'onboarding, transcrire).
- Le slug `onboarding/native-language` confirme que Speak a bien un onboarding multi-étape QCM-like, pas un chat pur — c'est cohérent avec la direction AcademIA.
- Le 7-day trial CB est probablement à éviter pour AcademIA en alpha (friction signup excessive vs une app qui doit encore prouver sa valeur).

---

### 4.6 Noom

**Catégorie** : perte de poids / changement d'habitudes, CBT-based, benchmark mondial de l'onboarding long. **Hors langues**, inclus pour calibrer le curseur "long questionnaire = investissement" à son extrême.
**Sources principales** : The Behavioral Scientist (product critique), Growth Waves Substack (analyse 113 écrans), Untrapped Academy (critique dark patterns), Justinmind, Amanda Liu Medium, Noom support page.

#### 4.6.1 Structure

Durée : **15 à 30 minutes** (selon la rapidité de lecture). Nombre d'écrans : **~113 écrans** (source Growth Waves), dont ~80 avec une vraie question.

Trois phases identifiées (source Amanda Liu) :
- **Phase A — démographie** (~20 questions) : sexe, âge, taille, poids actuel, poids cible, zone géographique, état civil.
- **Phase B — habitudes & comportements** (~30 questions) : fréquence des repas, triggers émotionnels, sport actuel, sommeil, stress au travail.
- **Phase C — historique & mentalité** (~30 questions) : tentatives de perte de poids antérieures, régimes essayés, relation à la nourriture, traumas, confiance en soi.

Séquence remarquable reconstruite (Behavioral Scientist) :
1. *"How much weight do you want to lose?"* — première question = cible, ancre immédiatement résultat.
2. Sex / current weight / target weight.
3. Lifestyle description.
4. Health risk assessment (diabète, problèmes cardiaques).
5. Eating disorder history.
6. Living environment.
7. Priority selection (pourquoi vouloir maigrir : santé / apparence / énergie / événement).
8. Event-based motivation (mariage, vacances, retour au bureau).
9. Daily pace preference.
10. Behavioral profile quiz de 10 questions (style psychométrique).
11. **Écran "3,627,436 personnes comme toi"** — social proof chiffré, placé juste avant le pic de dropout documenté au step 11.
12. Dietary restrictions / alcohol / snacking triggers / wellness queries.
13. "On analyse tes réponses…" — écrans de chargement simulé (Harvard operational transparency research).
14. **Personnalisation visible** : *"Ton profil comportemental nous aide à mieux comprendre X"* — crée l'illusion que les 80 questions étaient toutes utilisées.
15. **Goal timeline prediction** — calendrier personnalisé : *"Tu atteindras ton objectif le 14 septembre 2026"*.
16. **Accountability buddy prompt** — demande d'ajouter un ami avant même d'avoir accès au produit.
17. Paywall : $50/mois + upsell mental wellness course $50, "50 cent trial" (dark pattern).

#### 4.6.2 Variables collectées

Exhaustivité quasi-pathologique :
- Démographie complète (âge, sexe, taille, poids, localisation, statut familial)
- Historique médical (maladies chroniques, antécédents TCA, GLP-1 en cours)
- Habitudes alimentaires détaillées
- Triggers émotionnels
- Historique régimes
- Cible + délai + événement déclencheur
- Profil comportemental (quiz 10 questions)

#### 4.6.3 Tactiques de rétention (et de monétisation prédatrice)

Les sources convergent sur un mélange de patterns légitimes et dark patterns :

**Légitimes / transférables** :
- **Reciprocal value exchange** (Growth Waves) : chaque écran donne soit un acquittement émotionnel, soit un bout d'info éducative (green/yellow/red food system enseigné via les questions sur l'alimentation). *Length isn't the enemy; emptiness is.*
- **Progress visualization** : barres de progression + goal date qui se rapproche à mesure qu'on répond.
- **Operational transparency** (Harvard) : écrans de chargement qui signalent "on travaille sur ton profil", quand bien même le traitement est instantané côté serveur.
- **Social proof placé aux points de dropout** (step 5 et step 11).

**Dark patterns / à ne pas reproduire** :
- **PAS marketing** (Problem / Agitate / Solve) — Untrapped Academy : *"le questionnaire cause Mental Fatigue, rendant les consommateurs moins capables d'évaluer critiquement l'info de paiement en fin de tunnel"*.
- **Sunk cost manipulation** : les 30 minutes investies rendent psychologiquement coûteux de partir sans s'abonner.
- **Roach motel** (documenté par Justinmind) : annulation d'abonnement = contacter le coach par chat, pas de bouton self-service.
- **Trick wording** : "RISK FREE 100% GUARANTEED" proche d'un auto-renouvellement caché.
- **Countdown timer** sur l'écran de paiement.
- **Class action** aux US mentionnée : auto-enrôlement en plans multi-mois après "free trial" à 50 cts.

#### 4.6.4 Ce qui est bloquant

Tout. Impossible d'accéder au produit sans passer les 113 écrans et le paywall. C'est le modèle "hostage flow" archetypal.

#### 4.6.5 Deux citations clés pour comprendre Noom

De Growth Waves Substack (analyse favorable au modèle) :

> *"Length isn't the enemy; emptiness is. Each screen either acknowledges shared information, teaches something new, or displays progress — eliminating perceived friction by converting questions into moments of connection and insight."*

De Untrapped Academy (critique psychologue) :

> *"The lengthy questionnaire uses the 'PAS' marketing tactic — Problem, Agitate, Solve. This process creates Mental Fatigue, causing consumers to be less likely to critically evaluate the information about payment which is presented right at the end of the funnel."*

Les deux sources ont raison simultanément : Noom **réussit** à garder les utilisateurs engagés pendant 15-30 minutes de questionnaire (donc technique UX valide), MAIS exploite ce succès pour une conversion paywall prédatrice (donc éthiquement contestable). **Pour AcademIA, retenir la technique, laisser l'intention.**

#### 4.6.6 Enseignements pour AcademIA

Noom est un **anti-pattern global** pour AcademIA, mais avec **3 patterns récupérables** :

1. **Reciprocal value exchange** : chaque question du QCM AcademIA doit donner un micro-feedback ("On va adapter ton vocab au voyage →"). Ça transforme 8 questions en dialogue.
2. **Progress visualization** : barre de progression explicite sur le QCM + projection *"Après 2 semaines, tu pourras…"* post-QCM.
3. **Social proof placé au bon endroit** : si AcademIA a des stats de rétention à afficher (ex: *"73 % des apprenants comme toi pratiquent 3x/semaine"*), les positionner au milieu du QCM et non à la fin.

**À ne pas reproduire** : la longueur (>20 écrans = zone de danger pour une app langues), les dark patterns paywall, et surtout le principe "extraire max d'info pour monétiser par sunk cost". AcademIA n'a pas le contrat Noom.

---

### 4.7 Headspace

**Catégorie** : méditation, wellness, subscription. Benchmark de l'onboarding minimaliste qui marche.
**Sources principales** : Appcues GoodUX, PageFlows, medium designpractice.io, InsiderGrowth.

#### 4.7.1 Structure

Durée : **~1 minute**. Nombre d'écrans : **3 vraies questions + écrans splash/recap**, ~7 écrans totaux.

Séquence :

1. **Welcome / value prop sliders** — 3 slides swipables : *"Meditation made simple"* → *"Focus on what matters to you" (Sleep / Anxiety / Focus)* → *"Learn in just 10 minutes a day"*.
2. **Signup / login** — email ou social (avant les questions, contrairement à Duolingo).
3. **Question 1 — expérience méditation** : *"Have you meditated before?"* — None / A little / A lot. MCQ 3 options.
4. **Question 2 — motivation** : *"What brings you to Headspace?"* — tuiles image picker : Sleep / Reduce Stress / Focus / Relieve Anxiety / Be More Mindful / Something else. Pattern notable : optimisé en 2024 pour passer de "1 goal" à "multiple goals" acceptés (source : Insider Growth) — reconnaissance que les utilisateurs arrivent avec des besoins pluriels.
5. **Question 3 — timing** : *"When would you like to meditate?"* — options ancrées sur routines (Morning / Lunch / After Work / Before Bed), pas des heures précises.
6. **Recap** — *"Voici ton plan : X minutes, Y fois par semaine, pour [motivation]"*.
7. **Notifications priming** + paywall + trial gratuit.

#### 4.7.2 Variables collectées

Minimalisme délibéré :
- Expérience méditation (3 niveaux)
- Motivation (multi-select depuis 2024)
- Créneau routine préféré

Headspace ne demande pas : âge, profession, style perçu, durée session cible (option choisie plus tard in-app).

#### 4.7.3 Tactiques de rétention

- **Routine anchoring** : pas une heure précise ("07h30") mais un ancrage cognitif ("après le déjeuner"). Plus robuste psychologiquement.
- **Multi-goal après 2024** : reconnaissance que les gens ont des besoins pluriels, pas un seul "problème à résoudre". Contraste fort avec Noom qui force un "pourquoi unique".
- **1 minute de setup** : time-to-first-meditation extrêmement court.

#### 4.7.4 Ce qui est bloquant

Signup bloquant (email + mot de passe avant questions), mais questions minimales, paywall en fin après écran d'onboarding.

#### 4.7.5 Enseignements pour AcademIA

- **3 questions suffisent** pour calibrer un produit LLM, si elles sont bien choisies. Le QCM 8-10 questions d'AcademIA peut probablement être compressé à 6-7 sans perte de signal.
- **Routine anchoring** > heure précise : à tester pour le rappel de pratique AcademIA.
- **Multi-goal** : permettre à l'apprenant de cocher plusieurs motivations (voyage ET travail) plutôt que de forcer un choix unique. Gain en réalisme de profil.

#### 4.7.6 La leçon Headspace 2024 sur la pluralité des motivations

En 2024, Headspace a modifié sa 2e question ("What brings you here?") pour permettre un multi-select au lieu d'un single-select. L'analyse Insider Growth documente le rationale :

> *"Users often arrived at Headspace with multifaceted needs rather than a single goal. By acknowledging and addressing these multiple needs, the app created a more personalized and effective user experience, enhancing engagement and conversion rates during onboarding."*

Deux enseignements indirects pour AcademIA :

1. **Les motivations sont rarement monolithiques** dans la vraie vie. Un apprenant peut vouloir voyager ET parler à sa famille expatriée ET progresser pour le travail. Forcer un choix unique → faux positif, mauvaise adaptation downstream.
2. **Le changement s'est accompagné d'un gain mesurable** (pas chiffré publiquement mais Insider Growth classe ça dans ses "case studies from Headspace on how to increase revenue"). Signal faible mais cohérent : investir dans la qualité de la représentation utilisateur paye.

#### 4.7.7 Pourquoi Headspace est pertinent malgré le hors-domaine

Headspace n'est pas une app de langue, mais trois raisons structurelles le rendent utile pour AcademIA :

1. **Session count court (10-15 min)** : ratio proche d'une session AcademIA cible.
2. **Cœur d'expérience audio-conversationnel** : guidé par la voix, proche d'une interaction LLM vocal (Loora/Speak).
3. **Ton bienveillant non-gamifié** : alternative au modèle Duolingo agressif sur les streaks, plus aligné avec le positionnement AcademIA "tuteur personnel".

Ce qui ne se transfère pas : la verticalité bien-être (méditation = outcome difficilement mesurable quantitativement) vs langue (outcome mesurable via CEFR). AcademIA peut s'inspirer du ton mais doit garder une dimension "progrès visible" plus forte.

---

## 5. Synthèse transversale

### 5.1 Patterns qui convertissent (documentés sur ≥2 apps)

| Pattern | Apps qui l'appliquent | Pourquoi ça marche | Applicabilité AcademIA |
|---|---|---|---|
| **Motivation-first** (avant niveau) | Duolingo, Headspace, Loora | Ancrage émotionnel, personnalisation visible immédiate | Essentielle |
| **Niveau auto-déclaré binaire + placement test optionnel** | Duolingo, Babbel, Loora | Zéro friction débutants, précision pour avancés | Essentielle |
| **Image picker pour variables abstraites** | Duolingo, Headspace, Noom | Charge cognitive réduite, ancrage mémoire | Essentielle |
| **Slider de commitment temps/jour** | Duolingo, Busuu, Babbel, Headspace, Loora | Consistance, calibration réaliste, setup rappels | Essentielle |
| **Can-do statements plutôt que labels CEFR** | Duolingo (partiel), Busuu (mixte) | Évite le jargon, positionne concrètement | Essentielle |
| **Écran d'acquittement / feedback après chaque question** | Noom, Headspace (partiel) | Transforme questionnaire en dialogue | Forte |
| **Projection temporelle post-QCM** | Busuu, Loora, Noom | Loss aversion + commitment device | Moyenne (v2) |
| **Gradual engagement / signup après 1re valeur** | Duolingo | Réciprocité, sunk cost positif | Faible (incompatible avec gate modal AcademIA) |
| **Permission priming** (écran explicatif avant prompt OS) | Babbel | Double le taux d'acceptation | Si mic ajouté |
| **Multi-select motivation** (≠ choix unique) | Headspace (2024), Babbel (objectifs) | Réalisme profils réels | Forte |
| **Social proof placé aux points de dropout** | Noom | Réduit l'abandon au moment critique | Moyenne |
| **Baby schema / mascotte** | Duolingo | Désamorce stress cognitif | Optionnelle (Maestro/Teacher identité visuelle) |

### 5.2 Anti-patterns documentés

| Anti-pattern | Apps concernées | Coût observé | Pertinence AcademIA |
|---|---|---|---|
| **Placement test obligatoire pour tous** | Busuu | Churn pré-chat élevé chez curieux/débutants | À éviter |
| **Open text obligatoire** | AcademIA actuel | Boucles, language-mixing, extractions flous | C'est exactement ce qu'on fuit |
| **Questionnaire >30 écrans** sans contrat perçu | Noom (hostage flow) | Mental fatigue, dark patterns requis pour convertir | À éviter |
| **Labels CEFR nus (A1/A2/B1)** sans can-do | Busuu, Babbel (en partie) | Apprenants L1 perdus, auto-déclaration biaisée | À éviter |
| **Questions démographiques non prédictives** (source d'acquisition, âge sauf contexte) | Duolingo, Babbel | Friction sans retour produit | À éviter |
| **Paywall pré-first-value** | Noom, Babbel (partiel) | Churn avant que la valeur soit démontrée | À éviter |
| **Choix unique de motivation** | Duolingo, Babbel, Busuu (jusqu'à récemment) | Faux profils, nudges mal calibrés | À éviter |
| **Dark patterns paywall** (trick wording, countdown, roach motel) | Noom | Risque légal + réputationnel | À éviter |
| **Surcharge variables collectées** (Noom 80+ questions) | Noom | Low signal/noise, faux théâtre de personnalisation | À éviter |
| **Heure précise de rappel** (au lieu d'ancrage routine) | Busuu, Babbel | Moins robuste que "après le déjeuner" | À éviter partiellement |

### 5.3 Analyse comparée : durée onboarding vs type de contrat utilisateur

L'une des découvertes majeures de ce benchmark est que **la durée optimale d'un onboarding n'est pas universelle** ; elle dépend du contrat implicite entre l'utilisateur et le produit.

| App | Durée onboarding | Contrat utilisateur | Pourquoi ça marche à cette durée |
|---|---|---|---|
| Headspace | 1 min | "Je veux du calme rapidement" | Immédiateté est la proposition de valeur |
| Duolingo | 2 min | "Je veux apprendre en m'amusant" | Gamification compense le questionnaire ; gradual engagement |
| Loora / Speak | 2-3 min | "Je veux un coach IA personnel premium" | Investissement léger justifie le prix premium à venir |
| Busuu | 3 min | "Je veux une méthode sérieuse CEFR" | Placement test force l'investissement mais certifie le sérieux |
| Babbel | 3-4 min | "Je veux une méthode structurée de qualité" | Multiples questions justifient la méthode pédagogique premium |
| Noom | 15-30 min | "Je veux un programme médicalisé de perte de poids" | Engagement émotionnel fort + programme long (6-12 mois) |

**AcademIA** :
- Contrat cible : "Je veux un tuteur personnel IA qui s'adapte à moi"
- Proche du contrat Loora/Speak
- Durée optimale projetée : **2 min**
- Justifie le QCM comme "configuration du tuteur" plutôt que "formulaire administratif"

Mauvais mapping possible à éviter : positionner AcademIA comme "méthode sérieuse CEFR" avec placement test obligatoire → casse le contrat "tuteur personnel accessible", pousse vers Busuu-like.

### 5.4 Zones grises (trade-offs à assumer)

**1. Gate modal avant valeur vs gradual engagement**
Duolingo fait le pari du gradual engagement (signup après 1re leçon). AcademIA fait le pari inverse (QCM + signup AVANT chat). La raison est structurelle : chaque tour LLM coûte $0.01-0.10 selon le modèle — impossible de laisser l'utilisateur chatter anonymement. Compensation : rendre le QCM le plus court possible et l'écran de valeur post-QCM le plus rapide possible.

**2. Mascotte pédagogique vs ton sérieux**
Duolingo gagne avec Duo. Babbel et Busuu restent sobres. Headspace a une identité douce sans mascotte explicite. AcademIA a déjà un ton établi côté Teacher/Maestro — pas de mascotte. Ce trade-off est déjà tranché, mais il faut en tirer les conséquences : on ne peut pas compter sur le baby schema pour désamorcer la friction du QCM, donc le rythme, la clarté du copy et les micro-feedbacks doivent compenser.

**3. Placement test optionnel : à quel seuil ?**
Option A : seuil auto-déclaré (débutants skip, intermédiaires+ offert). Option B : toujours optionnel avec CTA "Tester mon niveau en 3 min" visible. Recommandation : A pour la v1, B pour la v2 une fois qu'on a un placement test fiable et rapide.

---

## 6. Recommandations pour AcademIA

### 6.1 Structure cible du QCM pre-chat

**Plafond** : 8 questions, durée perçue ≤ 2 minutes, ≤ 12 écrans au total (incluant splash, transitions, écran de valeur final).

**Séquence recommandée** :

1. **Splash identité langue** — *"Bienvenue chez Teacher"* (ou Maestro). L2 déjà choisie par la landing page, donc pas d'écran de sélection.
2. **Question 1 — Motivation (image picker, multi-select)** : *"Pourquoi tu veux [apprendre/perfectionner ton] anglais ?"* — tuiles illustrées : voyage, travail, études, famille, culture (films/séries/livres), autre. Multi-select autorisé (max 2 pour éviter la dispersion). → Variable `motivation[]` injectée dans system prompt.
3. **Micro-acquittement** — *"On adapte tes leçons à [top motivation]."*
4. **Question 2 — Niveau auto-déclaré via can-do (MCQ single)** :
   - *"Je ne connais presque rien, je démarre de zéro."*
   - *"Je sais dire bonjour, me présenter, commander un café."* (~A1-A2)
   - *"Je peux avoir une conversation simple sur ma vie quotidienne."* (~A2-B1)
   - *"Je peux parler de sujets variés, mais je fais encore des erreurs."* (~B1-B2)
   - *"Je maîtrise, je veux juste pratiquer et affiner."* (~B2-C1)
   Pas de label A1-C2 visible. → Variable `self_level` injectée.
5. **Question 3 — Anxiété / challenge principal (MCQ single)** : *"Qu'est-ce qui te bloque le plus ?"* — prononciation / grammaire / vocabulaire / confiance à l'oral / comprendre les natifs / autre. → Variable `main_blocker` injectée, calibre le ton LLM.
6. **Question 4 — Temps quotidien (slider 4 paliers)** : 5 / 10 / 15 / 20+ minutes, nommés avec verbes d'action ("découvrir" / "pratiquer" / "progresser" / "intensif"). → Variable `daily_minutes`.
7. **Question 5 — Créneau préféré (routine anchoring, MCQ)** : matin / midi / après le travail / soirée / pas de préférence. → Variable `preferred_slot`.
8. **Question 6 — Style perçu (MCQ single, optionnel skip)** : *"Tu apprends mieux quand…"* — on te corrige direct / on t'encourage d'abord / on t'explique la règle / on pratique direct. → Variable `correction_style`, directement utilisée par le system prompt pour le comportement du tuteur.
9. **Question 7 (conditionnelle, si `self_level` >= A2-B1) — Placement test optionnel** : *"Tu veux faire un test rapide de 3 min pour qu'on calibre précisément ?"* — Oui / Plus tard. Skip possible.
10. **(Placement test si pris)** — sinon skip direct.
11. **Écran de valeur** — *"Voici ton plan : [résumé 3 lignes]. Dans 2 semaines, tu pourras [projection]."* → injection finale dans le system prompt + enregistrement profil.
12. **CTA "Commencer ma première conversation"** → chat LLM avec contexte structuré déjà chargé.

### 6.2 Contrat d'injection contexte LLM

Le JSON généré par le QCM doit être sérialisé dans le system prompt sous forme explicite, par exemple :

```
<learner_profile>
  language: en
  native_language: fr
  motivation: [travel, work]
  self_declared_level: A2_to_B1  # "Je peux avoir une conversation simple"
  placement_score: 42/60 (if done, else null)
  main_blocker: pronunciation
  daily_minutes: 15
  preferred_slot: evening
  correction_style: explain_rules_first
</learner_profile>
```

**Règles d'usage par le LLM** (à coder dans le system prompt) :
- Ouvrir en **L2 exclusivement** (plus de language-mixing) avec adaptation au niveau déclaré.
- Si `main_blocker = pronunciation`, ne jamais corriger la prononciation sans encouragement préalable.
- Si `correction_style = explain_rules_first`, donner la règle avant l'exercice.
- Si `self_level = débutant absolu`, limiter le vocab aux 500 mots les plus fréquents.

### 6.3 Ce qui est bloquant vs optionnel

| Élément | Statut |
|---|---|
| Question motivation | Bloquant |
| Question niveau auto-déclaré | Bloquant |
| Question challenge | Bloquant |
| Question temps/jour | Bloquant |
| Question créneau | Bloquant (défaut "pas de préférence" disponible) |
| Question style | **Optionnel skip** (donne un défaut "équilibré") |
| Placement test | **Conditionnel** (proposé si niveau >= A2, jamais imposé) |
| Signup / email | Bloquant APRÈS le QCM, avant 1er chat |

### 6.4 Ce qu'AcademIA NE doit PAS faire

- Pas de question "comment as-tu entendu parler de nous" dans le QCM (anti-pattern Duolingo/Babbel documenté).
- Pas de demande d'âge / profession sauf si c'est strictement utilisé pour la personnalisation LLM (ce qui n'est pas le cas aujourd'hui).
- Pas de placement test bloquant.
- Pas de paywall dans le QCM v1 (alpha = valeur d'abord, monétisation v2).
- Pas de dark patterns (trick wording, countdown, auto-renewal piégé).
- Pas de labels A1-C2 en premier niveau de lecture.
- Pas de open text obligatoire.
- Pas de plus de 10 questions.

### 6.5 Risques identifiés et mitigations

| Risque | Mitigation |
|---|---|
| QCM perçu trop "formulaire administratif" vs ton chaleureux actuel du LLM | Micro-acquittements après chaque réponse + ton conversationnel dans le copy ("On adapte ça pour toi") |
| Auto-déclaration biaisée (Dunning-Kruger) sur le niveau | Placement test optionnel cadré pour les auto-déclarés "je maîtrise" + recalibration continue par le LLM sur les 3 premières sessions |
| Variables collectées mais sous-utilisées → faux théâtre de perso | Audit post-lancement : chaque variable doit modifier le comportement LLM ou les prompts de manière vérifiable |
| Time-to-value allongé par le QCM (vs ancien onboarding conversationnel qui démarrait le chat immédiatement) | Viser un QCM ≤ 2 minutes + écran de valeur qui survends le gain de précision ("Ton tuteur sait déjà que tu veux voyager, que tu bloques sur la prononciation…") |
| Pas de reviewer C2 ES/IT/DE/JP/RU pour valider les can-do statements | Utiliser les can-do officiels du Conseil de l'Europe (CEFR companion volume 2020) en traduction officielle ; alpha télémétrie pour détecter les erreurs d'auto-classement |
| Confusion chez les tests/retours : "j'ai répondu X et rien n'a changé" | Exposer 1-2 éléments visibles du profil dans l'UI du chat ("Profil : voyage · niveau ~A2 · 15 min/jour") |

### 6.6 Mapping variable collectée → usage LLM

Principe : **chaque variable collectée doit avoir une règle d'usage LLM explicite**. Sinon c'est du théâtre de personnalisation. Ce tableau est une première version à ajuster avec l'équipe prompt engineering (Maestro Dify Phase C et suivantes).

| Variable | Type | Valeurs possibles | Règle d'usage LLM (brouillon) |
|---|---|---|---|
| `l1` | string (fixe) | fr | *"L'apprenant est francophone L1. Tu peux faire des références ponctuelles au français pour expliquer un point, mais tu DOIS rester en [l2] pour la conversation principale."* |
| `l2` | enum | en, es, (it, de, jp, ru futurs) | Détermine le prompt pack chargé (Teacher vs Maestro vs futurs). |
| `motivation[]` | multi-select | travel, work, study, family, culture, other | Biaise le choix de vocabulaire / scénarios. Si `travel` → introduire phrases de transport, restaurant, hôtel dans les 3 premières sessions. Si `work` → scénarios pro (meeting, email). |
| `self_level` | enum | beginner_zero, A1_A2, A2_B1, B1_B2, B2_plus | Borne le registre lexical et la complexité grammaticale. Pour beginner_zero → 500 mots les plus fréquents, phrases courtes, présent uniquement. |
| `placement_score` | int nullable | 0-60 (si test pris) | Affine `self_level` : un débutant auto-déclaré qui fait 50/60 est recalé en A2_B1 pour la suite. |
| `main_blocker` | enum | pronunciation, grammar, vocabulary, confidence, listening, other | Biaise le ton du tuteur. Si `pronunciation` → corrections prosodiques prioritaires, encouragements explicites. Si `confidence` → encouragements avant correction, jamais de correction directe sans préambule positif. |
| `daily_minutes` | int | 5, 10, 15, 20+ | Calibre la **durée visée** de chaque session. Le LLM produit une pause explicite autour de T-30s pour proposer un wrap-up. |
| `preferred_slot` | enum | morning, midday, evening, afternoon, none | Alimente le système de rappel (notification ou email). Ne modifie pas le comportement LLM lui-même. |
| `correction_style` | enum nullable | direct, encouraging_first, explain_rule, practice_first, null | Modifie la structure de réponse du tuteur. `explain_rule` → donne la règle avant l'exercice. `practice_first` → exercice d'abord, règle en debrief. `direct` → correction inline sans ambages. `encouraging_first` → validation positive avant toute correction. Default (null) → style équilibré. |

### 6.7 Exemple de system prompt final (brouillon)

Pour illustrer à quoi ressemble l'injection contexte post-QCM dans le system prompt du LLM :

```
Tu es Maestro, un tuteur d'espagnol bienveillant et précis.

PROFIL APPRENANT :
- Langue maternelle : français
- Langue cible : espagnol
- Motivations : voyage, culture (films/séries)
- Niveau auto-déclaré : A2→B1 ("peut avoir une conversation simple sur sa vie")
- Placement test non pris
- Point de blocage principal : confiance à l'oral
- Durée de pratique visée : 15 minutes par session
- Style de correction préféré : encouragement d'abord

CONSIGNES :
- Ouvre en espagnol uniquement. Pas de mélange français/espagnol.
- Registre : phrases de 8-15 mots max, vocabulaire A2 avec introductions B1 ciblées.
- Contextualise les exemples sur voyage ou culture hispano (pas business).
- Quand l'apprenant fait une erreur : valide d'abord l'effort ("¡Buen intento!"), puis propose la forme correcte, puis demande de reformuler. Ne JAMAIS commencer par "No, eso está mal."
- Prononciation : si détectable via la tournure écrite, signale uniquement une fois par session.
- À T-12 minutes (80 % de la durée visée), propose un mini récap ("Antes de terminar, repasemos…").
- Si l'apprenant répond "ok" / "si" / "claro" sans ajouter de contenu, ne relance PAS la même question. Passe à une nouvelle micro-situation.
```

Cette approche résout les trois pathologies de l'onboarding actuel :
- **Language-mixing** : traité par la consigne explicite "ouvre en espagnol uniquement".
- **Boucle "ok"** : traitée par la consigne "ne relance pas la même question".
- **Bilan sans CEFR** : le bilan n'est plus conversationnel, il est **déterminé par le QCM dès l'entrée** et le placement test optionnel vient le préciser.

### 6.8 Séquencement de livraison suggéré

- **Sprint 1** : QCM 6 questions (motivation, niveau, blocker, temps, créneau, style), sans placement test, sans image picker (juste MCQ texte). Time-to-build court, data immédiate. Injection contexte system prompt LLM. Feature flag `onboarding_qcm_v1`.
- **Sprint 2** : ajout image picker sur motivation et niveau (illustrations), micro-acquittements, écran de valeur post-QCM. Dashboard télémétrie dropout par étape.
- **Sprint 3** : placement test conditionnel (3 min, 10 questions adaptatives), timeline projection, multi-select motivation.
- **Sprint 4** : A/B test sur l'ordre des questions, wording des can-do statements, routine anchoring vs heure précise.

### 6.9 Critères de succès de la refonte (KPIs)

Rapportés aux trois pathologies initiales :

| Pathologie initiale | KPI mesurable | Cible v1 |
|---|---|---|
| Language-mixing | % sessions où le LLM insère du français (hors citations pédagogiques) | < 5 % |
| Boucle "ok" | Nb moyen de relances identiques par session | < 0.5 |
| Bilan sans CEFR | % utilisateurs avec niveau CEFR déterminé en fin d'onboarding | 100 % |

Et sur la rétention :

| KPI | Baseline actuelle | Cible v1 |
|---|---|---|
| Dropout pré-chat | ? (à mesurer) | -30 % |
| Temps médian pré-1er-chat | ~ temps onboarding conversationnel (variable) | < 2 min |
| Retention J+1 | ? | +20 % |
| Retention J+7 | ? | +15 % |
| Qualité perçue du 1er chat (survey 5 points) | ? | ≥ 4.0 / 5 |

---

## 7. Annexe A — tableau comparatif

| App | Étapes | Durée | Signup avant Qs ? | Placement test | Image picker | Paywall | Variables LLM-utiles |
|---|---|---|---|---|---|---|---|
| Duolingo | ~7 questions / 23 écrans | ~2 min | Non (delayed) | Optionnel (auto-déclaré avancé) | Oui (motivation) | Freemium soft | Motivation, niveau, goal |
| Babbel | ~17 étapes | ~3-4 min | Variable | Optionnel (avancés) | Partiel | Paywall post-1re leçon | Motivation, objectifs, level, goal horaire |
| Busuu | ~15 écrans | ~3 min | Oui, très tôt | **Obligatoire** | Non | Soft | Motivation, level précis, plan hebdo |
| Loora AI | ~22 étapes | ~2-3 min | Oui | Implicite | Oui | Soft (dismiss→free lesson) | Challenge, niveau, goal |
| Speak | ~8-10 écrans (estimé) | ~2 min | Oui | AI interview (peu doc) | Partiel | 7-day trial CB | L1, L2, goal, level |
| Noom | ~113 écrans | 15-30 min | Oui | N/A | Oui | Obligatoire (+dark patterns) | ~80 vars (dont beaucoup non utilisées produit) |
| Headspace | 3 vraies Qs / 7 écrans | ~1 min | Oui | N/A | Oui | Post-onboarding | Expérience, motivation (multi), créneau |
| **AcademIA cible** | **6-8 Qs / 12 écrans** | **≤ 2 min** | **Oui (après QCM)** | **Conditionnel opt-in** | **Oui** | **Pas en v1** | **Motivation, niveau, blocker, temps, créneau, style** |

---

## 8. Annexe B — données quantitatives de rétention

Cette annexe rassemble les métriques publiques disponibles pour calibrer les attentes d'AcademIA. Toutes les données viennent de sources citées ; quand une métrique est absente de la littérature publique pour une app, c'est signalé.

### 8.1 Duolingo — métriques de rétention documentées

Jorge Mazal, ancien CPO Growth de Duolingo, a publié sur Lenny's Newsletter et sur le blog engineering Duolingo une série de chiffres qui servent de baseline pour toute app d'apprentissage de langue :

- **Next-day retention en 2012** : 12 %. Les équipes l'ont identifié comme alerte rouge et c'est ce qui a déclenché la refonte de l'onboarding.
- **Gain CURR (Current User Retention Rate) sur 4 ans** : +21 %, correspondant à une **baisse de >40 % du churn quotidien des meilleurs utilisateurs**.
- **Impact streak sur day-14 retention** : +14 % pour les utilisateurs exposés à un "streak wager" (pari sur maintien de la streak).
- **Next-day return pour maintenir une streak** : **55 %** des utilisateurs reviennent J+1.
- **Seuil de streak** : à partir de 10 jours consécutifs, le risque de drop-off baisse "substantiellement".
- **DAU/MAU ratio** : ~37 % en Q2 2025 (plus d'un utilisateur mensuel sur trois revient quotidiennement — métrique exceptionnelle pour une app consumer).
- **Gain DAU sur 4 ans** : x4.5.
- **Part de DAU avec streak ≥ 7 jours** : passée à >50 % en 4 ans (près de x3).
- **Impact leaderboards** : +17 % de temps d'apprentissage sur la plateforme ; triplement des "highly engaged" (>1h/jour, ≥5j/semaine).
- **Gains A/B Android performance 2024** : open conversion sur appareils entry-level passé de 91 % à 94.7 %, avec "des centaines de milliers de DAU gagnés" directement attribués aux perfs.

### 8.2 Babbel — métriques d'efficacité documentées

L'étude Yale (Vesselinov & Grego) et l'étude MSU sur l'efficacité Babbel donnent des ordres de grandeur sur le temps d'apprentissage nécessaire pour atteindre un niveau CEFR :

- **Yale** : médiane de 46 heures de pratique pour atteindre ACTFL Novice High (équivalent CEFR A1).
- **MSU** : médiane de 12 heures pour le même seuil.
- **CUNY** : 15 heures sur 2 mois pour couvrir un semestre universitaire d'espagnol pour vrais novices.
- **Corrélation temps/gains** : les gains en oral / grammaire / vocabulaire sont linéairement corrélés au temps passé après 3 mois de pratique.
- **Souscriptions Babbel** : >25 millions cumulées (chiffre commercial, pas rétention active).
- **Assessment tool (blog Babbel Design)** : 80 % completion rate sur les 2 semaines post-launch, 90 % des utilisateurs consultent les réponses après le test.

Implication pour AcademIA : notre promesse temporelle doit être calibrée. Le QCM peut afficher "Avec 15 min/jour, tu peux atteindre A2 en ~8 semaines" sans surpromettre (30 min/semaine × 8 semaines = 14-16h, dans la fourchette MSU).

### 8.3 Benchmarks sector onboarding

Sources : Userpilot, UXCam, Amra & Elma (2026 stats).

- **Sign-up onboarding drop-off après 1er écran** : ~38 % moyen sector.
- **Free-to-paid conversion SaaS average** : 17 % sur free trial.
- **Freemium conversion average** : 1-10 %.
- **Good onboarding completion rate B2C** : 30-50 %.
- **Good onboarding completion rate B2B** : 40-60 %.
- **Funnel drop-off >60 %** entre lead et conversion dans un SaaS type.

### 8.4 Noom — data paywall conversion (estimations)

Noom ne publie pas ses métriques, mais les class actions et audits UX documentent :

- **Durée médiane onboarding** : 15-30 min.
- **Trial price** : $0.50 pour 7-14 jours (décroissant dans le funnel via dark patterns de prix).
- **Prix plein post-trial** : ~$50/mois (auto-renewal).
- **Dropout points critiques documentés** : step 5 et step 11 (d'où le placement de la social proof "3,6M personnes aidées").
- **Social proof chiffre daté** : "3,627,436 people" (non mis à jour, ce qui trahit une sclérose du design).

### 8.5 Zones aveugles (données non trouvées publiquement)

- **Loora, Speak** : aucune publication de métriques de rétention/conversion. Les seules data publiques sont les levées de fonds (Speak : $162M cumulés, $1B valuation déc. 2024 ; Loora : non communiqué).
- **Busuu** : 120M users revendiqués (marketing) mais pas de DAU/MAU ni retention curve publiés.
- **Headspace** : >100M downloads mais pas de CURR ou NURR public.

---

## 9. Annexe C — frameworks psychologiques mobilisés

Les onboardings analysés mobilisent une dizaine de mécanismes psychologiques documentés. Cette annexe les cartographie pour aider l'équipe AcademIA à choisir consciemment lesquels répliquer.

### 9.1 Biais et principes utilisés de façon légitime

**Réciprocité (Cialdini)**
Duolingo, Loora (free lesson après dismiss paywall) : donner une valeur tangible avant de demander quoi que ce soit. Le signup devient alors un "merci" plutôt qu'une extraction. Pour AcademIA : l'écran de valeur post-QCM ("Ton tuteur a maintenant X, Y, Z informations pour t'aider") est un mini-don avant le premier chat.

**Consistance / commitment (Cialdini)**
Duolingo daily goal, Busuu plan hebdo, Headspace routine slot : faire prendre une micro-décision engageante tôt ancre l'utilisateur dans une identité ("je suis quelqu'un qui pratique 15 min/jour"). Fonctionne d'autant mieux que l'engagement est concret (choisir un créneau plutôt que "oui je veux apprendre").

**Preuve sociale**
Noom (placée aux points de dropout), Loora (notes moyennes sur paywall), Headspace (témoignages in-app). Effet amplifié si la preuve est pertinente et chiffrée récemment.

**Opération transparence (Harvard)**
Noom, Loora : afficher visiblement qu'un "traitement" est en cours ("Analyse de ton profil…") augmente la valeur perçue même quand le calcul est instantané. Effet validé expérimentalement par Ryan Buell et Michael Norton (HBS). À ne pas abuser : au-delà de 2 secondes de chargement simulé, ça devient perçu comme manipulatoire.

**Baby schema effect (Lorenz, éthologie)**
Duolingo Duo, Headspace identité douce : proportions enfantines (grande tête, grands yeux) déclenchent une réponse affective positive instinctive. Désamorce la charge cognitive d'un questionnaire.

**Ancrage contextuel / routine anchoring**
Headspace ("après le déjeuner" plutôt que "13h"). Les habits stickent mieux quand ils sont ancrés à un cue déjà existant (Atomic Habits, James Clear). Cité par Noom qui utilise explicitement le framework Atomic Habits.

**Progressive disclosure**
Noom introduit les fonctionnalités sur plusieurs jours (coach à J+3, chat groupe à J+14). Évite l'overwhelm et crée des "rendez-vous" qui relancent l'engagement. Applicable à AcademIA pour les fonctions avancées (corrections détaillées, historique, exports) qui peuvent attendre la semaine 2.

**Operational transparency / visible work**
Cf. §5 Noom. Applicable sous réserve d'honnêteté : AcademIA peut afficher "On charge ton tuteur personnalisé…" pendant la réelle construction du system prompt (non simulé).

### 9.2 Biais exploités façon dark pattern (à ne pas reproduire)

**Sunk cost fallacy pathologique**
Noom : 15-30 min investies rendent psychologiquement coûteux de partir sans s'abonner. Base légale fragile (class actions US). À éviter absolument pour AcademIA — notre contrat n'est pas là.

**Mental fatigue → baisse d'esprit critique au paywall**
Documenté par Untrapped Academy sur Noom. Le questionnaire épuise avant l'écran payant. Si AcademIA a un paywall un jour, il doit être positionné APRÈS une démonstration de valeur, pas APRÈS un questionnaire long.

**Trick wording**
"100 % RISK FREE GUARANTEED" alors qu'il y a un auto-renewal. Illégal dans plusieurs juridictions (FTC, DGCCRF). À proscrire.

**Countdown timers artificiels**
Noom affiche un timer sur le paywall. Crée urgence factice. Interdit par le DSA européen (2024) dans certains contextes.

**Roach motel**
Facile d'entrer, impossible de sortir. Noom force le contact coach pour annuler. Juridiquement à risque en UE depuis la Loi Modernisation de la vie économique (France) qui impose "aussi facile de résilier que de souscrire".

**Hostage flow**
Questionnaire long sans sortie avant le paywall. Noom archétypal. AcademIA doit toujours offrir un "Skip" ou "Plus tard" visible sur les questions non essentielles (Q6 style perçu, Q7 placement test).

### 9.3 Grille de décision éthique pour AcademIA

Avant d'ajouter une tactique, passer chaque élément au crible :

| Critère | Acceptable si… |
|---|---|
| La tactique augmente la rétention | Elle sert aussi la valeur pédagogique réelle |
| La tactique crée un engagement | L'utilisateur peut le modifier ou le rompre sans friction cachée |
| La tactique utilise de la preuve sociale | Les chiffres sont vrais, actualisés, pertinents |
| La tactique ajoute des étapes | Chaque étape acquitte l'info ou apporte un micro-bénéfice (reciprocal value exchange) |
| La tactique demande des données perso | Chaque donnée alimente visiblement la personnalisation du tuteur |

---

## 10. Annexe D — copy patterns

Cette annexe rassemble des exemples de wording observés sur les apps benchmarkées, organisés par fonction. L'objectif est de servir de palette pour le copywriting AcademIA.

### 10.1 Phrases d'ouverture motivation

- **Duolingo** : *"Why are you learning [language]?"*
- **Babbel** : *"Why are you learning [language]?"* (identique, copy générique)
- **Busuu** : *"What language would you like to learn, and why?"* (fusion langue + motivation)
- **Headspace** : *"What brings you to Headspace?"*
- **Loora** : orienté challenge (*"What's your biggest challenge with English?"*) plutôt que motivation positive

Proposition AcademIA : *"Qu'est-ce qui t'amène à apprendre [l'anglais / l'espagnol] aujourd'hui ?"* — reprend la forme Duolingo mais en français chaleureux, ouverture qui invite à une intention personnelle plutôt qu'à une catégorisation froide.

### 10.2 Phrases d'auto-évaluation de niveau

Niveau A1 auto-déclaré :

- **Duolingo (ancienne version)** : *"I'm new to [language]"*
- **Babbel** : *"Beginner"*
- **Busuu** : *"A1 — Absolute beginner"* (avec label CEFR explicite)
- **Loora** : *"I know some basics"* (plus granulaire)

Proposition AcademIA (can-do) : *"Je ne connais presque rien, je démarre."* (sans label). Ajouter en hover/tooltip discret pour les curieux : "≈ A1".

### 10.3 Commitment device / daily goal

- **Duolingo** : nommé par adjectifs (Casual / Regular / Serious / Intense) + unité XP
- **Babbel** : *"When would you like to learn?"* + dropdown horaire
- **Busuu** : *"How much time do you want to spend each day?"* + slider minutes
- **Headspace** : *"When would you like to meditate?"* + options routine (Morning / Lunch / After Work / Before Bed)
- **Loora** : *"How much time can you commit daily?"* + timeline projection

Proposition AcademIA (verbes d'action plutôt qu'adjectifs de charge) : *"Combien de temps tu veux consacrer par jour ?"* avec 4 paliers : Découvrir (5 min) / Pratiquer (10 min) / Progresser (15 min) / Intensif (20+ min). L'étiquette verbe = identité positive, contrairement à "Casual" (un peu péjoratif) ou "Intense" (anxiogène si surdosé).

### 10.4 Acquittements micro-feedback

Noom est le référent :

- Après entrée du poids : *"Thank you for sharing. That's an important (and hard) first step."*
- Après health condition : *"Noted. We'll adapt our recommendations to your situation."*
- Pendant chargement : *"Analyzing your inputs to personalize your plan…"*

Applicable AcademIA (propositions brouillon) :

- Après motivation : *"Parfait, on va orienter tes contenus sur [voyage / travail]."*
- Après niveau : *"On démarre à ton niveau — pas de jargon, pas de surcharge."*
- Après challenge : *"Entendu. Ton tuteur sera extra attentif à [la prononciation]."*
- Après temps : *"15 min/jour — on va tout faire pour que ce soit productif et pas ennuyeux."*
- Chargement final : *"On prépare ton plan personnalisé…"* (chargement réel côté serveur, pas simulé).

### 10.5 Écrans de valeur post-QCM

- **Busuu** : *"At this pace, you'll reach B1 by [date]."*
- **Loora** : *"In 30 days, you'll be able to…"*
- **Noom** : goal date dynamique qui se rapproche à chaque réponse

Proposition AcademIA (Vague 1, sans calcul précis) :

> *"Ton tuteur est prêt. Il sait que tu veux [motivation], que tu pars de [niveau], et que tu bloques surtout sur [challenge]. Vous allez pratiquer [temps] par jour. En 2 semaines, tu devrais pouvoir [can-do projection adaptée au niveau]."*

Cette projection peut être paramétrée par niveau :

- A1 → *"te présenter avec plus d'assurance"*
- A2-B1 → *"tenir une conversation simple de 5 minutes sans bloquer"*
- B1-B2 → *"aborder des sujets variés avec moins d'erreurs"*
- B2+ → *"gagner en fluidité et affiner tes nuances"*

### 10.6 Ce que le copy doit éviter

- Jargon : CEFR, A1-C2, "NLP", "LLM", "system prompt" visibles.
- Promesses irréalistes : "Parle couramment en 30 jours".
- Ton professoral : "Félicitations, vous avez franchi l'étape 3/8."
- Sur-chaleur : "On t'adoooore déjà !" (malaise).
- Auto-célébration produit : "Notre algorithme exclusif analyse…".

---

## 11. Annexe E — checklist de décision pour le QCM AcademIA

Cette checklist peut servir de gate de revue avant de pousser le QCM en prod.

### 11.1 Structure

- [ ] Nombre de questions ≤ 8 (dont au plus 1 conditionnelle).
- [ ] Durée perçue ≤ 2 minutes (tests chrono sur 5 profils internes).
- [ ] Pas plus de 12 écrans au total (splash + Qs + acquittements + valeur).
- [ ] Indicateur de progression visible sur chaque écran ("2/7").
- [ ] Bouton "Retour" disponible sur chaque écran (pas de navigation one-way forcée).

### 11.2 Questions

- [ ] Question 1 = motivation (ancrage émotionnel en premier).
- [ ] Niveau auto-déclaré via can-do, jamais via labels CEFR nus.
- [ ] Au moins une question multi-select (motivation idéalement).
- [ ] Au moins une question à slider (daily time).
- [ ] Placement test jamais obligatoire, conditionnel sur niveau auto-déclaré ≥ A2-B1.
- [ ] Pas de question démographique non prédictive (âge, acquisition source).
- [ ] Pas d'open text obligatoire.
- [ ] Une question "style de correction préféré" (single, skippable).

### 11.3 UX / micro-interactions

- [ ] Image picker sur motivation (illustration + label).
- [ ] Image picker ou illustration sur niveau (can-do en texte suffit si illustration indisponible).
- [ ] Micro-acquittement après chaque question (1 ligne de feedback).
- [ ] Écran de valeur final qui expose le profil reconstruit en clair.
- [ ] Transition < 300ms entre écrans (pas de lag perçu).

### 11.4 Intégration LLM

- [ ] Toutes les réponses sérialisées en JSON structuré.
- [ ] JSON injecté dans le system prompt avant le premier tour du LLM.
- [ ] Chaque variable a une règle explicite sur le comportement LLM (pas de variable "décorative").
- [ ] L1 (français) explicite dans le contexte LLM pour éviter le language-mixing.
- [ ] Niveau et motivation visibles dans l'UI chat (bandeau profil) pour transparence.

### 11.5 Éthique / légal

- [ ] Aucun countdown timer artificiel sur les écrans.
- [ ] Aucun prix ou paywall dans le QCM v1.
- [ ] Bouton "Plus tard" visible sur les questions optionnelles.
- [ ] RGPD : info de collecte visible sur l'écran splash ou pied de QCM.
- [ ] Aucun auto-opt-in sur notifications / emails marketing.
- [ ] Les données collectées sont documentées dans le registre RGPD d'AcademIA.

### 11.6 Télémétrie

- [ ] Log de chaque soumission de question (temps passé, choix).
- [ ] Log des abandons (quelle question déclenche le quit).
- [ ] Log du temps total perçu vs réel.
- [ ] Dashboard pour dropout par étape (identifier les points de friction).
- [ ] A/B test framework prêt pour tester l'ordre des questions en v2.

### 11.7 Rollback

- [ ] Feature flag `onboarding_qcm_v1` présent, permet de revenir à l'onboarding conversationnel si régression mesurée.
- [ ] Critère d'acceptation alpha : baisse du dropout pré-chat de ≥30 % ET pas de dégradation de la qualité perçue du 1er chat (survey utilisateur 3 questions).

---

## 12. Annexe F — questions non résolues

Cette Vague 1 a identifié des trous de connaissance qui méritent une Vague 2 ou un test terrain direct.

### 12.1 Questions non résolues sur les concurrents

**Speak** : onboarding écran par écran non documenté publiquement. Action recommandée Vague 2 : installer l'app, filmer le flow, transcrire.

**Loora** : nombre exact d'étapes confirmé à 22 mais contenu détaillé flou. Action recommandée : test terrain.

**Duolingo 2026** : les A/B tests sont permanents, les captures Mobbin peuvent dater de 2023-2024. Action : revérifier sur une install fraîche.

**Noom hors-US** : les dark patterns documentés portent sur le marché US. Le flow européen est peut-être adapté au RGPD/DSA. Action : test depuis la France (VPN si nécessaire).

**Busuu placement test obligatoire** : confirmé 2024, mais peut-être assoupli depuis. Action : revérifier.

### 12.2 Questions produit AcademIA pendantes

**Style perçu — est-ce prédictif ?**
On recommande la question "tu apprends mieux quand on te corrige direct / encourage d'abord / explique la règle / pratique direct". Aucune source benchmark ne l'utilise. Hypothèse : utile pour calibrer le LLM, mais à valider en A/B (cohorte avec la question vs sans).

**Multi-select motivation — combien max ?**
On recommande max 2. Headspace autorise multi illimité (changé en 2024). À tester.

**Placement test — conditionnel ou opt-in universel ?**
Recommandation : conditionnel sur niveau ≥ A2-B1. Alternative : opt-in universel ("Fais un test de 3 min pour une précision max"). Duolingo fait conditionnel, Busuu fait obligatoire, personne ne fait opt-in universel bien exposé. Opportunité de différentiation ?

**Image picker vs texte — mesure réelle d'uplift ?**
Patterns unanimement recommandés mais pas de chiffres précis dans la littérature grand public. Candidat pour A/B test chez AcademIA.

**Rappel email vs notification push ?**
Duolingo pousse notification (avec garde-fous opt-in), Babbel pousse email plus souvent. Pour AcademIA : défaut recommandé = email pour la v1 (moins intrusif, pas de gestion d'app push à la discipline Duolingo-grade).

**Tonalité (tu / vous) ?**
Choix culturel français. Duolingo FR utilise le tutoiement, Babbel FR est plus formel. Pour AcademIA (public jeune-adulte apprenant) : recommandation tutoiement dans le QCM, cohérent avec la culture d'apprentissage digital.

### 12.3 Vague 2 — plan de recherche suggéré

1. **Tests terrain filmés** : installer Speak, Loora, Duolingo, Busuu, Babbel, Headspace, Noom ; enregistrer le flow complet ; transcrire.
2. **User interviews** : 5 apprenants FR de niveau mixte, leur montrer 3 prototypes de QCM AcademIA (court 5Q / moyen 8Q / long 12Q), mesurer la préférence déclarative et le signal révélé (temps passé, qualité des réponses).
3. **A/B test quant** : pousser le QCM sur 50 % de la cohorte alpha, garder l'onboarding conversationnel sur l'autre moitié pendant 2 semaines. Mesurer : dropout pré-chat, qualité du 1er chat (rated par humain sur 20 sessions), rétention J+7.
4. **Benchmark academic** : lire Ace-CEFR, Alignment Drift (cités en §5), voir si des travaux récents documentent l'impact du contexte injection structuré sur la qualité du tutoring.

---

## 13. Annexe G — positionnement AcademIA vs concurrents

Matrice 2D pour visualiser où se place AcademIA dans l'espace compétitif :

### 13.1 Axe durée onboarding vs richesse profil LLM

```
Onboarding long / Profil riche     Onboarding long / Profil pauvre
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │                         │    │  NOOM (hors-cible)      │
  │  AcademIA cible v2      │    │  (15-30 min, 80 vars    │
  │  (2-3 min, 10-12 vars   │    │   dont 80 % non-LLM)    │
  │   toutes LLM-utiles)    │    │                         │
  └─────────────────────────┘    └─────────────────────────┘
Onboarding court / Profil riche    Onboarding court / Profil pauvre
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │  AcademIA cible v1      │    │  HEADSPACE (3 Qs)       │
  │  LOORA (22 étapes mais  │    │  DUOLINGO (peu de vars  │
  │   densité élevée)       │    │   LLM-utiles, tout      │
  │                         │    │   passe par skill tree) │
  └─────────────────────────┘    └─────────────────────────┘
```

### 13.2 Axe bloquant modal vs gradual engagement

| App | Modal bloquant ? | Gate de valeur | Paywall timing |
|---|---|---|---|
| Duolingo | Non (signup delayed après 1re leçon) | Compte opt-in | Freemium soft, paywall doux plus tard |
| Babbel | Oui pour QCM, non pour signup | Paywall rapide | Paywall après 1 leçon gratuite |
| Busuu | Oui complet | Placement test + plan | Premium push immédiat |
| Loora | Oui complet | Soft paywall avec escape | Trial direct, payant rapide |
| Speak | Oui complet | 7-day trial sur CB | CB dès entrée |
| Noom | Oui hostage | Paywall après 113 écrans | Dark pattern auto-renewal |
| Headspace | Oui modéré | Paywall post-onboarding | Free trial 7-14j |
| **AcademIA v1** | **Oui modéré (QCM)** | **Pas de paywall** | **N/A en alpha** |

AcademIA en alpha est donc positionné comme **Headspace-like sur le gating** (modal QCM court sans paywall) mais **Loora-like sur la densité profil** (anxiety question, style prefs, plusieurs dimensions). C'est une position atypique mais cohérente avec le contrat produit.

### 13.3 Axe gamification vs sérieux

| App | Mascotte ? | Streaks ? | Leaderboards ? | Ton |
|---|---|---|---|---|
| Duolingo | Duo (central) | Oui (central) | Oui | Ludique, pressant |
| Babbel | Non | Non | Non | Pédagogique sérieux |
| Busuu | Non | Non | Non (community) | Corporate CEFR |
| Loora | Non | Non | Non | Coaching bienveillant |
| Speak | Non | Oui (modéré) | Non | Tech premium |
| Noom | Non (coach humain) | Non | Non | Thérapeutique |
| Headspace | Non (identité douce) | Oui (modéré) | Non | Bien-être calme |
| **AcademIA** | **Non** | **TBD v2** | **Non** | **Tuteur personnel, registre FR tutoiement** |

### 13.4 Cible de différentiation

AcademIA peut se différencier par **la combinaison unique** :

1. **Onboarding court mais profil LLM-riche** (≠ Duolingo qui a long + pauvre, ≠ Noom qui a long + riche-mais-useless)
2. **Tuteur IA conversationnel français L1** (≠ Duolingo/Babbel qui sont L1-universels mais skill tree, ≠ Speak qui est plus international)
3. **CEFR sans jargon** (can-do first, ≠ Busuu qui affiche A1-C2 nu)
4. **Style d'apprentissage paramétrable** (personne ne le propose explicitement dans le benchmark, c'est une trouvaille AcademIA si implémentée)

Positionnement en une phrase :

> *"AcademIA : un tuteur IA qui te connaît en 2 minutes, parle ta langue sans jargon, et s'adapte à ta façon d'apprendre — pas de leçons toutes faites, pas de gamification forcée, juste un prof personnel qui démarre où tu en es."*

---

## 14. Annexe H — ancrage dans la recherche académique CEFR + LLM

Trois papiers récents (2025) ont un impact direct sur la manière dont AcademIA doit concevoir le QCM et surtout l'injection contexte qui en résulte.

### 14.1 Alignment Drift in CEFR-prompted LLMs (arXiv 2505.08351, 2025)

**Thèse** : le "prompting seul" est trop fragile pour maintenir un niveau CEFR constant dans un dialogue long.

**Méthodologie** : simulation de dialogues tuteur-apprenant en espagnol avec modèles open-source 7B-12B, system prompts basés sur CEFR (A1, B1, C1), évaluation de la dérive au fil des tours.

**Finding principal** : *"prompting alone is too brittle for sustained, long-term interactional contexts"*. Les auteurs baptisent le phénomène **alignment drift** — le modèle dérive progressivement vers un registre plus complexe que le niveau cible.

**Impact pour AcademIA** :

- **Le QCM ne suffit pas** à maintenir l'alignement niveau. Même si on injecte parfaitement `self_level: A2` dans le system prompt, le LLM va dériver en conversation. Le QCM est une **condition nécessaire mais pas suffisante**.
- Il faut compléter par : (a) des reminders de niveau en mid-session (re-injecter le contexte CEFR toutes les N minutes / tours), (b) un monitoring côté serveur de la complexité des outputs LLM, (c) une boucle de correction.
- Ceci justifie l'investissement AcademIA dans un orchestrateur Dify-clone plutôt qu'un simple prompt statique — on peut architecturalement gérer le drift.

### 14.2 Controllable Generation for Beginner-Friendly LLMs (arXiv 2506.04072v2, 2025)

**Thèse** : au-delà du prompting, des techniques de decoding-time steering (FUDGE) permettent de contraindre la difficulté générée.

**Finding quantitatif** : FUDGE fait passer la compréhensibilité de **39.4 % (prompting baseline) à 83.3 %** sur une évaluation humaine avec 6 apprenants japonais niveau JLPT N5-N4.

**Métrique clé proposée** : **Token Miss Rate (TMR)** = proportion de tokens dans la réponse qui dépassent le niveau lexical visé de l'apprenant. Corrélé à ρ=0.78 avec les jugements humains.

**Impact pour AcademIA** :

- Le QCM établit le niveau cible. Le **TMR peut servir de KPI qualité** côté backend : mesurer automatiquement combien de tokens dans chaque réponse du LLM dépassent le niveau A2 si l'apprenant est déclaré A2. Cible : TMR < 10 %.
- FUDGE nécessite d'intervenir au niveau decoding — pas faisable avec APIs closed-source (OpenAI, Anthropic) sans fine-tuning. Alternative : **re-génération conditionnelle** (si TMR > seuil, demander au LLM de simplifier).
- Cohérent avec la décision AcademIA "skip fine-tune" (cf. memory Phase B) : on ne modifie pas le modèle, on utilise des boucles applicatives.

### 14.3 Ace-CEFR dataset (arXiv 2506.14046, 2025)

**Apport** : dataset de passages conversationnels annotés manuellement par niveau CEFR, utilisable pour (a) entraîner des classifieurs de difficulté, (b) évaluer des outputs LLM, (c) construire des corpus oracles.

**Impact pour AcademIA** :

- Ressource directement utilisable pour le pipeline de validation corpus-based déjà évoqué dans les memories (`project_no_native_reviewers.md`).
- Permet de valider que les réponses du tuteur Maestro restent sous un plafond de complexité CEFR, sans nécessiter un reviewer natif.

### 14.4 Synthèse pour l'architecture AcademIA

Le QCM pre-chat n'est **que le premier maillon** d'une chaîne qui doit maintenir l'alignement pédagogique. La recherche récente suggère un empilement :

1. **QCM pre-chat** (cette vague 1) : établit le profil cible, injecté en system prompt.
2. **Re-injection périodique** : tous les N tours, rappeler le profil dans le contexte.
3. **Monitoring TMR** côté serveur : mesurer la dérive lexicale.
4. **Correction boucle** : si dérive détectée, demander au LLM de simplifier la prochaine réponse, ou rerouter vers une version du prompt plus contrainte.
5. **Validation par corpus oracle** (Ace-CEFR ou équivalent français) : sampling pour détection de régressions.

Le QCM est l'input qualité de toute cette chaîne. Mal rempli → chaîne dégradée dès l'origine. Ce qui justifie d'investir dans sa qualité UX.

---

## 15. Annexe I — glossaire

- **CEFR / CECRL** : Common European Framework of Reference for Languages / Cadre Européen Commun de Référence pour les Langues. Échelle A1-C2.
- **Can-do statement** : description concrète d'une compétence à un niveau CEFR donné (ex : "Je peux commander un café"). Alternative au label A1/A2 nu.
- **CURR** : Current User Retention Rate. Métrique Duolingo = % d'utilisateurs actifs cette semaine qui sont encore actifs semaine prochaine.
- **NURR** : New User Retention Rate. % d'utilisateurs J+1 qui reviennent à J+2.
- **DAU/MAU** : Daily Active Users / Monthly Active Users. Ratio mesurant la stickiness (Duolingo ~37 %).
- **Dark pattern** : design volontairement trompeur pour manipuler l'utilisateur (trick wording, roach motel, countdown factice).
- **Freemium / paywall soft / paywall hard** : modèles de gating progressif vs immédiat.
- **Gradual engagement** : pattern Duolingo = retarder le signup pour donner de la valeur d'abord (Samuel Hulick).
- **L1 / L2** : langue maternelle (L1) / langue cible (L2).
- **LLM** : Large Language Model.
- **MCQ** : Multiple Choice Question.
- **Opérational transparency** : pattern Harvard = afficher le "travail en cours" pour augmenter la valeur perçue.
- **PAS** : Problem-Agitate-Solve, technique marketing (et Noom onboarding).
- **Placement test** : test initial pour déterminer le niveau.
- **Prompt injection (contexte)** : technique consistant à sérialiser le profil utilisateur dans le system prompt du LLM pour modifier son comportement.
- **Roach motel** : dark pattern = facile à entrer, dur à sortir.
- **Routine anchoring** : ancrage d'une nouvelle habitude sur une routine existante (Atomic Habits, James Clear).
- **Streak** : nombre de jours consécutifs actifs. Mécanique de rétention majeure chez Duolingo.
- **Sunk cost fallacy** : biais cognitif où l'on continue un engagement à cause de l'investissement déjà fait.
- **Time-to-value** : temps entre le premier écran et le premier moment de valeur ressentie.

---

## 16. Annexe J — index des patterns identifiés

Pour référence rapide dans les discussions produit, voici l'index alphabétique des patterns cités dans ce rapport :

- Anxiety-first question — §4.4.7, §6.1
- Baby schema effect — §4.1.3, §9.1
- Can-do statements — §2.2 (anti-pattern CEFR nu), §6.1, §10.2
- Commitment device (daily goal) — §2.1, §4.1.2, §10.3
- Dark patterns (à éviter) — §4.6.3, §9.2
- Gradual engagement — §4.1.5, §5.4
- Hostage flow — §2.2, §4.6.4
- Image picker — §2.1, §5.1, §6.1
- Mental fatigue exploitation — §4.6.3, §9.2
- Micro-acquittement / reciprocal value exchange — §4.6.3, §10.4
- Motivation-first — §2.1, §5.1
- Multi-select motivation — §4.7.6, §5.1
- Opération transparence — §4.6.3, §9.1
- PAS (Problem-Agitate-Solve) — §4.6.3, §9.2
- Permission priming — §4.2.5
- Placement test conditionnel — §2.1, §5.1, §6.1
- Progressive disclosure — §4.6.3, §9.1
- Roach motel — §4.6.3, §9.2
- Routine anchoring — §4.7.2, §10.3
- Social proof placé aux points de dropout — §4.6.3, §5.1
- Sunk cost manipulation — §4.6.3, §9.2
- Timeline projection — §4.4.3, §6.1
- Trick wording — §4.6.3, §9.2

---

## 17. Annexe K — journey maps comparées (descriptions en prose)

Cette annexe offre une description narrative "en prose" des 7 journeys, comme si l'on décrivait à un designer ce qu'un utilisateur voit. L'objectif est de permettre à quelqu'un qui n'a pas ouvert ces apps de se figurer concrètement les flows.

### 16.1 Duolingo — journey narrative

*"Tu ouvres l'app. Un écran bleu apparaît avec une mascotte hibou verte (Duo) qui te fait coucou en animation. Tu tapes 'commencer'. On te demande de choisir une langue parmi une liste à scroller — des drapeaux, des noms de langues. Tu choisis l'espagnol. Bref écran de transition.*

*Une question apparaît en gros : 'Où as-tu entendu parler de Duolingo ?' avec des boutons (Facebook, TV, ami, autre). C'est un peu incongru mais rapide.*

*Ensuite : 'Pourquoi apprends-tu l'espagnol ?' avec 6 tuiles carrées avec icônes — un avion pour voyage, une mallette pour travail, un cerveau pour brain training, etc. Tu choisis voyage.*

*Puis : 'Quel est ton niveau en espagnol ?' avec deux grandes options : 'Je suis complètement débutant·e' et 'J'en connais déjà un peu'. Tu cliques débutant.*

*Un écran te dit : 'Super, combien de temps veux-tu consacrer chaque jour ?' — 4 options : Casual (5 min), Regular (10 min), Serious (15 min), Intense (20 min). Chaque option a une petite illustration avec des flammes. Tu choisis Regular.*

*Un compteur te dit 'Encore 3 questions avant ta première leçon'. C'est un geste psychologique : tu sais où tu en es.*

*Quelques écrans plus tard : 'Voici ton parcours personnalisé' avec une roadmap de leçons verticales, premières débloquées, suivantes verrouillées. Tu tapes sur la première.*

*Tu fais 5 exercices — drag-and-drop, traduction, prononciation. Duo commente chaque bonne réponse ('¡Muy bien!'). Tu gagnes des XP, tu vois une barre de progression.*

*À la fin de la leçon, écran de victoire avec des confettis, +15 XP. Streaks introduits : 'Tu viens de commencer ta streak !'. Là seulement, un écran sobre : 'Pour sauvegarder ta progression, crée un compte.' Tu signes avec Google.*

*Tu es sur le dashboard. La prochaine leçon t'attend. Duo te promet que demain il t'attendra."*

Remarques : cette journey a une **courbe de tension maîtrisée** — Duo désamorce, compteur de progression rassure, signup reporté après la 1re victoire. L'utilisateur arrive sur le dashboard avec déjà une micro-compétence + identité ("je suis quelqu'un qui fait du Duolingo").

### 16.2 Babbel — journey narrative

*"Tu ouvres l'app. Logo Babbel, tagline méthode structurée. Sélection langue (14 options, moins que Duolingo). Tu choisis espagnol.*

*Écran suivant : 'Pourquoi apprenez-vous l'espagnol ?' — 6 options en texte (pas d'icônes) : famille, travail, voyage, culture, amis, école. Tu cliques travail.*

*Deuxième écran de motivation (plus fin) : 'Qu'est-ce qui vous intéresse le plus ?' — tu peux cocher plusieurs : avoir des conversations, lire, comprendre la culture, préparer un examen. Tu coches conversations + culture.*

*Niveau : 'Débutant / Avancé ?' — binaire, pas granulaire. Tu choisis Avancé (parce que tu as fait 2 ans de lycée il y a longtemps). Un écran propose : 'Voulez-vous faire un test de placement de 5 minutes ? Vous pourrez commencer au bon niveau. Vous pouvez aussi choisir votre niveau manuellement.' Tu fais le test.*

*Le test (15-20 questions) mixe grammaire, vocab, listening (audios courts). Tu vois une barre de progression. À la fin : 'Vous êtes niveau B1'. Un graphique te montre tes forces et faiblesses.*

*Ensuite : 'Quel âge avez-vous ?' (dropdown). Puis : 'Comment avez-vous entendu parler de Babbel ?' (liste). Pas la question la plus pertinente pour un apprenant de 45 ans pressé, mais OK.*

*Suit un écran 'Quand souhaitez-vous apprendre ?' — dropdown avec horaires suggérés. Puis une demande de permission microphone, précédée d'un écran explicatif : 'Nous avons besoin du micro pour t'aider à pratiquer la prononciation.'*

*Enfin : 'Commencez votre première leçon gratuitement'. Tu fais la leçon. À la fin, paywall : 'Pour continuer, souscrivez à Babbel Premium — 7,99 €/mois'. Option 'Plus tard' visible mais petite.*

*Tu décides de payer."*

Remarques : journey plus long, plus corporate, plus orienté conversion payante rapide. La question démographique en plein milieu (âge + attribution) est le seul vrai point de friction — documenté par Braingineers.

### 16.3 Busuu — journey narrative

*"Tu ouvres l'app. Écran de signup social dès la 2e seconde : Facebook / Google / Email. Tu signes.*

*Choix langue (12 options). Puis : 'Pourquoi apprenez-vous cette langue ?' (6 options).*

*Écran important : 'Faites un test de placement de 5 minutes pour trouver votre niveau.' — pas d'option skip visible. Tu fais le test, il est exigeant : mix grammaire / vocab / compréhension écrite. Tu finis B1.*

*Puis écran de plan hebdo : 'Quels jours voulez-vous pratiquer ?' (cases à cocher L-M-M-J-V-S-D). 'À quelle heure ?' (time picker). 'Combien de temps par jour ?' (slider 5-30 min).*

*Objectifs : 'Sur quoi voulez-vous vous concentrer ?' (grammaire, vocab, conversation, culture — multi-select).*

*Écran de projection : 'À ce rythme, vous atteindrez B2 le 18 octobre 2026.' Un calendrier visuel.*

*Paywall : 'Busuu Premium débloque tout le contenu + corrections par des natifs. 9,99 €/mois'. Option 'Continuer en gratuit' disponible mais limitée.*

*Tu choisis gratuit pour tester. Dashboard : liste linéaire de leçons, première déverrouillée."*

Remarques : ton "corporate CEFR", placement test obligatoire = friction mais aussi sérieux perçu. La projection de date est puissante. La community (corrections natifs) est un différenciateur qui apparaît plus tard.

### 16.4 Loora AI — journey narrative

*"Tu ouvres l'app. Sliders de valeur : 'Your Personal AI English Coach' — 'Speak with confidence in any situation'. Tu swipes, tu tapes 'Get started'.*

*Question puissante, inattendue : 'What's your biggest challenge with English?' — 6 tuiles avec icônes : Pronunciation / Grammar / Speaking in meetings / Confidence / Listening / Other. Tu cliques Confidence.*

*Écran d'acquittement empathique : 'You're not alone. Many learners feel the same. Loora will help you gain confidence step by step.'*

*Question suivante : 'What's your goal?' — Business / Travel / Academic / Test prep / General fluency. Tu cliques Business.*

*'How would you describe your current English level?' — 3 options simples (Beginner / Intermediate / Advanced). Tu cliques Intermediate.*

*'How much time can you commit daily?' — slider de 5 à 60 min. Tu mets 15. Une timeline apparaît : 'In 30 days practicing 15 min/day, you'll…' avec des milestones visuelles (confidence level monte sur une courbe).*

*Permission notifications, setup reminder.*

*Paywall : 'Unlock Loora Premium — $19.99/month Yearly plan (Save 33 %) / $29.99 Monthly'. Avec social proof : '⭐ 4.7 (12,543 reviews)'.*

*Tu fermes le paywall. Un écran apparaît : 'Wait — try your first lesson for free.' Tu acceptes.*

*Tu démarres ta première conversation IA. Le tuteur te salue et pose une question ouverte : 'Tell me about yourself — what do you do for work?'"*

Remarques : journey où la personnalisation émotionnelle est centrale. L'anxiety-first crée immédiatement de l'empathie. Le soft paywall avec free-lesson fallback est élégant. Cohorte la plus proche d'AcademIA.

### 16.5 Speak — journey narrative (reconstituée, partielle)

*"Tu ouvres l'app. Splash 'Speak — the fastest way to learn languages by actually speaking'. Tu tapes continue.*

*'What's your native language?' — liste de 40+ langues. Tu choisis français.*

*'What do you want to learn?' — 6 options : English, Spanish, French, German, Japanese, Korean. Tu choisis anglais.*

*'What's your goal?' — General fluency / Work / Travel / Academic. Tu choisis Work.*

*'What's your level?' — auto-déclaré parmi beginner / intermediate / advanced (avec peut-être des can-do courts).*

*(Probable) AI interview : une courte conversation audio de 2-3 tours où le tuteur IA évalue ton niveau par un échange naturel. Cette partie n'est pas clairement documentée publiquement.*

*Paywall : 'Try Speak Premium free for 7 days. Then $19.99/month.' Demande de CB. Ceci filtre les curieux — seuls les utilisateurs déterminés continuent.*

*Ceux qui passent arrivent sur le dashboard : sentence drills, role-plays, AI conversations. Curriculum construit sur les réponses onboarding."*

Remarques : journey vraisemblablement élégant et court, avec AI interview comme différenciateur, mais peu documenté publiquement. La demande de CB au trial est la plus forte friction du benchmark.

### 16.6 Noom — journey narrative (extrait)

On ne peut pas décrire les 113 écrans en prose. Voici plutôt les premiers 20 et les derniers 5 pour donner la texture.

*"Tu arrives sur la landing page Noom. Deux gros boutons : 'Lose weight for good' / 'Get fit for good'. Pas de navigation libre. Tu cliques lose weight.*

*Écran 1 : 'How much weight do you want to lose?' — slider en kg. Tu mets 10 kg.*

*Écran 2 : 'What's your biological sex?' — M/F/Prefer not to say.*

*Écran 3 : 'What's your current weight?' (input). Écran 4 : 'What's your target weight?' (input). Écran 5 : 'Your goal date is [calculated]' — date affichée comme projection.*

*Écran 6 : bandeau 'Thank you for sharing. You're not alone.' + témoignage.*

*Écran 7-10 : âge, taille, localisation, statut familial.*

*Écran 11 : social proof — '3,627,436 people have lost weight with Noom.' Placé stratégiquement avant le pic de dropout.*

*Écrans 12-25 : health conditions (diabète, hypertension, TCA, GLP-1 actuels).*

*Écrans 26-40 : habitudes alimentaires (triggers, fréquence des repas, alcool, snacking).*

*Écrans 41-60 : historique régimes (quels régimes tentés, pourquoi échoué, relation à la nourriture).*

*Écrans 61-80 : quiz comportemental 10 questions + acquittements, mini-leçons sur la science Noom.*

*Écrans 81-100 : loading screens 'Analyzing your profile… 67%… 89%… 100%'. Écrans de personnalisation visible.*

*Écran 110 : 'Meet your personalized plan' — résumé.*

*Écran 111 : 'Add an accountability buddy' — demande contact ami.*

*Écran 112 : Paywall. 'Your plan is ready — start your 14-day trial for $0.50' + countdown timer.*

*Écran 113 : CB input + consent auto-renewal en petit."*

Remarques : 15-30 min total. Mix de value légitime (mini-leçons, acquittements) et de dark patterns (countdown, trick wording, roach motel post-signup). AcademIA doit garder les techniques légitimes et rejeter les autres.

### 16.7 Headspace — journey narrative

*"Tu ouvres l'app. 3 sliders de value props : 'Meditation made simple.' / 'Focus on what matters : Sleep / Anxiety / Focus.' / 'Learn in just 10 minutes a day.' Tu swipes.*

*Signup : email ou social. Rapide.*

*Question 1 : 'Have you meditated before?' — None / A little / A lot. 3 tuiles avec petites illustrations.*

*Question 2 : 'What brings you to Headspace?' — 6 tuiles avec illustrations douces : Sleep / Reduce Stress / Focus / Relieve Anxiety / Be More Mindful / Something else. Multi-select (depuis 2024). Tu coches Sleep + Reduce Stress.*

*Écran d'acquittement : 'We'll build a plan around sleep and stress reduction.'*

*Question 3 : 'When would you like to meditate?' — 4 routines : Morning / Lunch / After Work / Before Bed. Tu cliques After Work.*

*Écran récap : 'Your plan : 10-minute sessions, Evening, for Sleep & Stress. Ready to start?'*

*Demande notifications (avec priming). Puis paywall free trial 14 jours. Tu peux aussi faire une méditation 'free intro' sans payer."*

Remarques : 1 minute, 3 questions, extrêmement efficace. Contraste maximal avec Noom. Montre qu'on peut délivrer une personnalisation crédible en 3 questions bien choisies.

### 16.8 AcademIA projetée — journey narrative (recommandation)

*"Tu arrives sur academie.com. Page d'accueil montre deux langues : Teacher (anglais) et Maestro (espagnol). Tu cliques Maestro.*

*Landing Maestro : une phrase de valeur, un CTA 'Démarre ton premier cours'. Tu cliques.*

*Modal bloquant apparaît (QCM). Écran 1 : 'Salut ! Avant qu'on commence, j'ai quelques questions pour personnaliser ton tuteur.' Petit bandeau de progression '1/7'.*

*Question 1 : 'Qu'est-ce qui t'amène à apprendre l'espagnol ?' — 6 tuiles image picker : Voyage, Travail, Études, Famille, Culture (films/séries), Autre. Tu peux en cocher 2 max. Tu coches Voyage + Culture.*

*Micro-acquittement : 'Parfait, on va parler voyage et culture hispano.'*

*Question 2 (2/7) : 'Ton niveau aujourd'hui ?' — 5 options en can-do : 'Je démarre de zéro' / 'Je sais dire bonjour et commander un café' / 'Je peux avoir une conversation simple' / 'Je parle de sujets variés avec encore des erreurs' / 'Je maîtrise, je veux affiner'. Tu cliques la 3e.*

*Micro-acquittement : 'On démarre à ton niveau. Pas de surcharge.'*

*Question 3 (3/7) : 'Qu'est-ce qui te bloque le plus ?' — 5 options : Prononciation / Grammaire / Vocabulaire / Confiance à l'oral / Comprendre les hispanophones. Tu cliques Confiance.*

*Micro-acquittement : 'Entendu. Ton tuteur sera extra bienveillant là-dessus.'*

*Question 4 (4/7) : 'Combien de temps par jour ?' — slider 4 paliers avec verbes : Découvrir (5 min) / Pratiquer (10 min) / Progresser (15 min) / Intensif (20+ min). Tu mets Progresser.*

*Question 5 (5/7) : 'Quand préfères-tu pratiquer ?' — matin / midi / après le travail / soirée / pas de préférence. Tu cliques après le travail.*

*Question 6 (6/7) : 'Tu apprends mieux quand…' — on te corrige direct / on t'encourage d'abord / on t'explique la règle / on pratique direct. Un petit 'Skip' en bas. Tu cliques 'on t'encourage d'abord'.*

*Question 7 (conditionnelle, tu as déclaré conversation simple — donc proposée) : 'Tu veux faire un test rapide de 3 minutes pour qu'on calibre précisément ton niveau ?' — Oui, tester / Plus tard. Tu cliques Plus tard.*

*Écran de valeur final : 'Ton tuteur est prêt. Il sait que tu veux voyager et comprendre la culture, que tu pars d'un niveau conversation simple, que tu veux surtout gagner en confiance, et qu'on va pratiquer 15 min par jour. En 2 semaines, tu devrais pouvoir tenir une conversation de 5 minutes sans bloquer. On y va ?'*

*CTA 'Commencer ma première conversation'. Tu cliques.*

*Signup rapide (Google / email). Puis le chat démarre : le tuteur Maestro te salue EN ESPAGNOL uniquement, avec un ton encourageant adapté à 'confiance-first', commence par une question simple sur le voyage."*

Temps total projeté : **2 minutes QCM + 15 secondes signup = 2min15** jusqu'au premier chat. Time-to-value : ~3 minutes (signup + 1ère réponse du tuteur). Compétitif avec Duolingo malgré le gate modal.

---

## 18. Annexe L — recommandations de lecture complémentaires

Pour l'équipe produit et designers AcademIA qui voudraient aller plus loin sur un sujet spécifique :

- **Sur la rétention gamifiée** : "How Duolingo reignited user growth" de Jorge Mazal (Lenny's Newsletter) + "Duolingo Streak System Detailed Breakdown" (Premjit Singha, Medium). Deux lectures pour comprendre pourquoi CURR > CAC.
- **Sur l'onboarding long qui ne ressent pas long** : "The 113-screen onboarding that doesn't feel long" (Growth Waves Substack). 10 min à lire.
- **Sur les dark patterns à ne pas reproduire** : "A Psychologist Reviews The Dark Psychology of Noom" (Untrapped Academy). Cadrage éthique clair.
- **Sur la recherche UX chez une app de langue** : "Testing, testing — how we created an assessment tool for Babbel users" (Babbel Design Medium). Cas rare de transparence R&D d'une app commerciale.
- **Sur l'alignment CEFR + LLM** : Alignment Drift arXiv 2505.08351 + FUDGE arXiv 2506.04072v2. Lecture technique pour l'équipe backend / prompt engineering.
- **Sur la théorie de l'habit formation** : *Atomic Habits* (James Clear). Livre cité par Noom, bases de l'ancrage routine utilisé par Headspace.
- **Sur les biais psychologiques de design** : Learning Loop (learningloop.io/plays/psychology). Catalogue de plays par biais.

---

## 19. Annexe M — changelog de ce rapport

- **2026-04-20 v1** : publication initiale. 7 apps analysées (Duolingo, Babbel, Busuu, Loora, Speak, Noom, Headspace). 10 recommandations AcademIA. Mapping variable → usage LLM. Ancrage dans 3 papiers arXiv 2025. Checklist de décision + plan Vague 2.

Pas de v2 prévue avant que les tests terrain de la Vague 2 (propositions §12.3) soient menés.

---

## 20. Sources

### Sources primaires / mi-primaires

- [Lenny's Newsletter — How Duolingo reignited user growth (Jorge Mazal)](https://www.lennysnewsletter.com/p/how-duolingo-reignited-user-growth)
- [Duolingo Engineering Blog — Meaningful metrics: How data sharpened the focus of product teams](https://blog.duolingo.com/growth-model-duolingo/)
- [Duolingo Engineering Blog — Android app performance case study](https://blog.duolingo.com/android-app-performance/)
- [Babbel Design Medium — Testing, testing: how we created an assessment tool for Babbel users (Carina de Magalhães)](https://medium.com/babbeldesign/testing-testing-how-we-created-an-assessment-tool-for-babbel-users-9051407ca3be)
- [Babbel — Why Babbel works (research page UK)](https://uk.babbel.com/why-babbel-works/)
- [Babbel Efficacy Study PDF (Vesselinov & Grego, Yale)](https://assets.ctfassets.net/zuzqvf4m2o58/5eYRgCslJnJBF9yhZKgX01/78b93f75ca40fca6c7b927b6e2e82bf8/Babbel-Efficacy-Study.pdf)
- [Babbel Press Release 2019 — New Academic Study Shows How Learning with Babbel Develops Conversational Skills](https://www.babbel.com/press/en-us/releases/2019-07-25-How-learning-with-babbel-develops-conversational-skills-in-a-new-language.html)
- [Babbel Help Center — Placement quiz](https://support.babbel.com/hc/en-us/articles/20202703767442-Placement-quiz)
- [Babbel Help Center — Defining your learning goals](https://support.babbel.com/hc/en-us/articles/360037497132-Defining-your-learning-goals)
- [OpenAI blog — Speak is personalizing language learning with AI](https://openai.com/index/speak-connor-zwick/)
- [TechCrunch — OpenAI-backed Speak raises $78M at $1B valuation (2024-12-10)](https://techcrunch.com/2024/12/10/openai-backed-speak-raises-78m-at-1b-valuation-to-help-users-learn-languages-by-talking-out-loud/)
- [Speak.com — Onboarding native language page](https://app.speak.com/us-en/onboarding/native-language)
- [Speak.com — Onboarding learning language page](https://app.speak.com/us-en/onboarding/learning-language)
- [Duolingo Help Center — How do I set my daily goal?](https://support.duolingo.com/hc/en-us/articles/4404643575053-How-do-I-set-my-daily-goal-)
- [Duolingo Help Center — What is XP?](https://support.duolingo.com/hc/en-us/articles/204905880-What-is-XP-)
- [Busuu — CEFR proficiency levels page](https://www.busuu.com/en/languages/proficiency-levels)
- [Busuu — Certification pages](https://www.busuu.com/en/languages/certification)
- [Loora.com](https://www.loora.com/)
- [Noom support — Free features 2025](https://www.noom.com/support/private/2025/07/free-features-in-the-noom-app-h/)

### Études UX / case studies secondaires

- [Appcues GoodUX — Duolingo's delightful user onboarding experience](https://goodux.appcues.com/blog/duolingo-user-onboarding)
- [Appcues GoodUX — Babbel's brilliant mobile permission priming](https://goodux.appcues.com/blog/babbel-mobile-permission-priming)
- [Appcues GoodUX — Headspace's mindful onboarding sequence](https://goodux.appcues.com/blog/headspaces-mindful-onboarding-sequence)
- [UserGuiding — Duolingo: an in-depth UX and user onboarding breakdown](https://userguiding.com/blog/duolingo-onboarding-ux)
- [Braingineers — UX Design: A Neuromarketing Study of Duolingo's Onboarding Flow](https://www.braingineers.com/post/user-experience-design-a-neuromarketing-evaluation-of-duolingos-onboarding-flow)
- [Justinmind — UX case study of Noom app: gamification, progressive disclosure & nudges](https://www.justinmind.com/blog/ux-case-study-of-noom-app-gamification-progressive-disclosure-nudges/)
- [The Behavioral Scientist — Noom Product Critique: Onboarding](https://www.thebehavioralscientist.com/articles/noom-product-critique-onboarding)
- [Growth Waves Substack — The 113-screen onboarding that doesn't feel long (Noom)](https://growthwaves.substack.com/p/the-113-screen-onboarding-that-doesnt)
- [Untrapped Academy — A Psychologist Reviews The Dark Psychology of Noom (Part 1)](https://untrapped.com.au/a-psychologist-reviews-the-dark-psychology-of-noom-part-1/)
- [Medium Amanda Liu — Noom Case Study](https://thisisamandaliu.medium.com/noom-case-study-4c404a3e2dde)
- [Medium Michael Linares — Great UXpectations: Lessons from Noom](https://linares.medium.com/great-uxpectations-lessons-from-noom-e88c3687ade3)
- [Medium designpractice.io — Onboarding Journey of Headspace iOS App (Dhaval Gandhi)](https://medium.com/designpractice-io/onboarding-journey-of-headspace-ios-app-8867420accf)
- [Medium Lucien — In-depth Analysis of Speak AI](https://medium.com/@lucien1999s.pro/in-depth-analysis-of-speak-ai-how-ai-creates-an-immersive-and-personalized-language-learning-45f0b27848d0)
- [Medium Dmitrii Ziuzin Bootcamp — Case study: the onboarding of a language learning app (Drops)](https://medium.com/design-bootcamp/case-study-the-onboarding-of-a-language-learning-app-dc70d7e467f8)
- [Medium Arina Lopatina — Building Effective Onboarding Experiences: Lessons from Duolingo](https://medium.com/@kotarina832/building-effective-onboarding-experiences-lessons-from-duolingo-7aa2af536020)
- [Medium Ketaki Vaidya — Duolingo onboarding: Product feature case study](https://kittuvaidyakv.medium.com/duolingo-onboarding-product-feature-case-study-804e597a19f9)
- [Insider Growth HQ — 3 Case Studies from Headspace on how to increase revenue](https://www.insidergrowthhq.com/p/3-case-studies-from-headspace-on)
- [AppFuel — Duolingo onboarding example](https://theappfuel.com/examples/duolingo_onboarding)
- [AppFuel — Babbel onboarding example](https://www.theappfuel.com/examples/babbel_onboarding)
- [AppFuel — Busuu onboarding example](https://www.theappfuel.com/examples/busuu_onboarding)
- [AppFuel — Headspace onboarding example](https://theappfuel.com/examples/headspace_onboarding)
- [PageFlows — Headspace Onboarding Flow on iOS](https://pageflows.com/post/ios/onboarding/headspace/)
- [PageFlows — Onboarding on Duolingo Desktop Examples](https://pageflows.com/post/ios/onboarding/duolingo/)
- [PageFlows — Onboarding on Babbel Desktop Examples](https://pageflows.com/post/android/onboarding/babbel/)
- [Mobbin — Duolingo iOS Onboarding Flow](https://mobbin.com/explore/flows/0acc27c7-4e01-481c-83b2-99f8d741bef1)
- [Mobbin — Babbel iOS Onboarding Flow](https://mobbin.com/explore/flows/78aaba88-e477-4ba8-b178-a7c7ac7bf41e)
- [Mobbin — Noom Android Onboarding Flow](https://mobbin.com/explore/flows/c1404418-d156-4add-9abe-6b0b94d72628)
- [ScreensDesign — Speak English with Loora AI App Showcase](https://screensdesign.com/showcase/speak-english-with-loora-ai)
- [ScreensDesign — Noom Weight Loss, Food Tracker](https://screensdesign.com/showcase/noom-weight-loss-food-tracker)
- [ScreensDesign — Babbel Language Learning](https://screensdesign.com/showcase/babbel-language-learning)

### Reviews utilisateurs / tests

- [FluentU — The Complete Busuu Review of 2024](https://www.fluentu.com/blog/reviews/busuu/)
- [Icanlearn — Loora AI Review](https://www.icanlearn.com/loora-ai/)
- [Mid.oo — Loora Review: Can This AI English Coach Really Deliver Fluency?](https://www.midoo.ai/reviews/loora-review)
- [Papora — Loora App: Does Learning English with Artificial Intelligence Work?](https://www.papora.com/learn-english/loora-app/)
- [LanguaTalk — Speak App Review: Is It Worth It in 2026?](https://languatalk.com/blog/speak-app-review/)
- [Practice.me — Speak App Review: Is It Worth It for English? [2026]](https://practiceme.app/vs/speak)
- [Choosing Therapy — Noom Review 2024](https://www.choosingtherapy.com/noom-review/)

### Recherche académique (CEFR + LLM)

- [arXiv 2505.08351 — Alignment Drift in CEFR-prompted LLMs for Interactive Spanish Tutoring](https://arxiv.org/abs/2505.08351)
- [ACL Anthology — Alignment Drift in CEFR-prompted LLMs](https://aclanthology.org/2025.bea-1.6/)
- [arXiv 2506.14046 — Ace-CEFR: A Dataset for Automated Evaluation of Linguistic Difficulty](https://arxiv.org/html/2506.14046v1)
- [arXiv 2506.04072 — Toward Beginner-Friendly LLMs for Language Learning: Controlling Difficulty in Conversation](https://arxiv.org/html/2506.04072v2)
- [arXiv 2501.15247 — Prompting ChatGPT for Chinese Learning as L2: A CEFR and EBCL Level Study](https://arxiv.org/pdf/2501.15247)

### Benchmarks et stats sector

- [Userpilot — Drop-Off Rate: What Is It and How to Reduce It?](https://userpilot.com/blog/drop-off-rate/)
- [UXCam — Funnel Drop Off Rate: Benchmarks & Strategies](https://uxcam.com/blog/drop-off-rates/)
- [Amra & Elma — TOP 20 FUNNEL DROP-OFF RATE STATISTICS 2026](https://www.amraandelma.com/funnel-drop-off-rate-statistics/)
- [Userpilot — SaaS User Onboarding Funnel 101](https://userpilot.com/blog/saas-user-onboarding-funnel/)
- [TryPropel — Duolingo's Customer Retention Strategy (2026)](https://www.trypropel.ai/resources/duolingo-customer-retention-strategy)
- [StriveCloud — Duolingo gamification explained](https://www.strivecloud.io/blog/gamification-examples-boost-user-retention-duolingo)
- [NextLeap submissions — Boosting User Retention: Data-Driven Insights for Duolingo (PDF)](https://assets.nextleap.app/submissions/DATAANALYSISOFDUALINGO-cfa09e78-96db-4653-9cc7-59f9659c88f4.pdf)

### Listings tertiaires (consultés mais non cités en corpus)

- [Appagent — Mobile App Onboarding: 4 Examples of Successful New User Flows](https://appagent.com/blog/new-user-flow-types/)
- [Designerup — The 14 Types of Onboarding UX/UI Used by Top Apps](https://designerup.co/blog/the-14-types-of-onboarding-ux-ui-used-by-top-apps-and-how-to-copy-them/)
- [Designerup — I studied the UX/UI of over 200 onboarding flows](https://designerup.co/blog/i-studied-the-ux-ui-of-over-200-onboarding-flows-heres-everything-i-learned/)
- [UXCam — App Onboarding Guide: Top 10 Onboarding Flow Examples 2026](https://uxcam.com/blog/10-apps-with-great-user-onboarding/)
- [Retention.blog Jacob Rushfinn — 10+ tests for onboarding](https://www.retention.blog/p/10-tests-for-onboarding)
- [Reteno — Noom Weight Loss Food Tracker App Onboarding Flow gallery](https://gallery.reteno.com/flows/app-screens-noom)
- [Reteno — Babbel Language Learning App Onboarding Flow gallery](https://gallery.reteno.com/flows/app-screens-babbel)

---

*Fin du rapport — vague 1.*
