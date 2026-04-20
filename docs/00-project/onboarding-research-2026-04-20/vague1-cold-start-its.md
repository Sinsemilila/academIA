# Vague 1 — Cold-start et Intelligent Tutoring Systems : état de l'art pour l'onboarding AcademIA

> **Date** : 2026-04-20
> **Auteur** : équipe recherche AcademIA
> **Statut** : brief de recherche — vague 1 de 3 (Cold-start ITS / Recommender)
> **Destinataires** : produit, pédagogie, ML, ingénierie tuteur
> **Périmètre** : onboarding nouveau learner (turn 0 → turn 1), signal minimal viable, trade-offs exploration-exploitation
> **Langue** : français, niveau chercheur EdTech / AIED

---

## 0. Executive Summary

AcademIA fait face à un problème **cold-start classique** en apprentissage adaptatif : à l'inscription, le tuteur dispose de zéro historique comportemental (`error_log`, rétention, difficulté préférée) mais doit néanmoins produire un premier turn qui (a) calibre un niveau estimé, (b) choisit un concept à travailler, (c) vise une difficulté dans la zone proximale de développement de Vygotsky. Un turn mal calibré frustre (too hard) ou ennuie (too easy) et la littérature est unanime : les 3–5 premiers turns conditionnent la rétention à J7 bien plus que la qualité pédagogique moyenne des 50 suivants.

La recommandation synthétisée par ce rapport — issue de la confrontation d'environ quarante références évaluées par les pairs (Corbett & Anderson 1995 ; Piech et al. 2015 ; Ghosh, Heffernan & Lan 2020 ; Desmarais & Baker 2012 ; Falmagne et al. 2013 ; Heffernan & Heffernan 2014 ; Bull & Kay 2016 ; Settles & Meeder 2016 ; VanLehn 2011 ; Pardos & Heffernan 2010 ; Yudelson, Koedinger & Gordon 2013 ; Vie & Kashima 2019) et du benchmark de quatre systèmes industriels (Duolingo, Khan Academy, ALEKS, ASSISTments) — peut se résumer en un bullet :

> **Signal minimal viable cold-start = 4 à 8 items auto-rapportés bien choisis + observation comportementale du 1er turn LLM, agrégés dans un Open Learner Model inspectable et négociable dès le 2e turn.**

Plus précisément :

1. **4–8 self-reports** (et non pas 20–30) : au-delà, le taux d'abandon dans l'onboarding monte significativement (Spotify, Netflix et la littérature RecSys convergent), et le gain informationnel marginal décroît rapidement (Desmarais & Baker 2012 — « a handful of well-chosen indicators is typically sufficient to personalize the prior »).
2. **Mix de signaux** : déclaratif (niveau CEFR auto-estimé, objectif, L1, domaine pro) + contextuel (temps disponible, pays) + comportemental léger (1 question de placement calibrée, type DIALANG).
3. **Prior $P(L_0)$ personnalisé** : utiliser ces 4–8 signaux pour passer d'un prior population ($P(L_0)_{\text{pop}} \approx$ moyenne classe) à un prior conditionnel $P(L_0 \mid \text{onboarding})$, à la manière du modèle Prior-Per-Student (PPS) de Pardos & Heffernan (2010) et de ses successeurs individualisés (Yudelson et al. 2013).
4. **Observation post-hoc = calibration continue** : le Teacher AcademIA ré-estime à chaque turn la position du learner via `error_log` + taxonomie CEFR (cf. memory `project_error_taxonomy`). Le 1er turn LLM sert donc d'abord d'**observation** (pas d'évaluation sommative) qui raffine les priors dès T+1.
5. **Open Learner Model** (Bull & Kay 2016) : le résultat du QCM doit être **montré** au learner et **négociable** (« je pense que vous êtes B1 intermédiaire en compréhension orale — êtes-vous d'accord ? »). Cette transparence améliore motivation, auto-régulation et précision du modèle (correction utilisateur sur outliers).

Le reste du rapport justifie ces choix par les évidences empiriques disponibles dans la littérature AIED/EDM et par le benchmark des systèmes qui ont résolu ce problème à l'échelle de millions d'utilisateurs.

### Décisions concrètes proposées pour AcademIA (teaser, détaillées en §6)

| Bloc | Items | Rationale |
|------|-------|-----------|
| A — Contexte | L1, langue cible, objectif (pro / voyage / académique / loisir) | Prior de difficulté + biais d'erreurs L1→L2 (transfert) |
| B — Auto-éval CEFR | Can-do statements DIALANG × 2 (compréhension + expression) | Prior $P(L_0)$ continu [0,1] calibré sur corpus CEFR |
| C — Préférences | Temps/jour disponible, format préféré (lecture / audio / conversation) | Contrôle du bandit sur type de turn initial |
| D — Comportemental | 1 question de placement auto-adaptative (niveau estimé auto-rapporté ± 1 CEFR) | Observation comportementale qui réduit l'over-claim self-report |

Soit **7 items** — dans la fenêtre 4–8 recommandée — complétables en moins de 90 secondes. Le Teacher LLM reçoit ces 7 signaux en system prompt structuré et produit le 1er turn avec une incertitude assumée ("best-guess niveau = B1, IC = ±1 CEFR, confirmation attendue via 1er `error_log`").

---

## 1. Le problème cold-start en ITS : cadrage théorique

### 1.1 Définition et taxinomie

Le cold-start en recommender system et en ITS désigne la situation où le système ne peut pas inférer avec fiabilité à propos d'un **utilisateur**, d'un **item** ou d'un **système** pour lesquels il n'a pas encore collecté d'information suffisante (Wikipedia, « Cold start (recommender systems) » ; Schein et al. 2002 ; Lika et al. 2014). Trois sous-cas :

- **User cold-start** : un nouveau learner arrive, aucun historique. **C'est le cas d'AcademIA.**
- **Item cold-start** : un nouveau concept / exercice est ajouté au catalogue, aucun learner ne l'a jamais vu.
- **System cold-start** : démarrage total, ni users ni items avec historique (cas d'un pivot produit ou d'un nouveau marché / nouvelle langue).

Dans un ITS, le cold-start user pose un défi spécifique : contrairement à un recommender musical où une mauvaise recommandation coûte « un skip Spotify », une mauvaise calibration pédagogique au 1er turn coûte :

1. **Affectif** : perte de confiance, frustration si trop dur, ennui si trop facile (Csikszentmihalyi — concept de flow).
2. **Épistémique** : le learner reçoit un modèle interne erroné de lui-même si le système communique un niveau faux.
3. **Métriques produit** : chute de D1/D7 (retention), corrélée dans les études Duolingo et Khan à la qualité du premier feedback.

### 1.2 Pourquoi le cold-start est structurellement plus dur en éducation

Plusieurs propriétés spécifiques aux ITS exacerbent le problème vs. un RecSys de contenu :

1. **Espace de connaissance latent non observable** : on veut inférer $\theta \in \mathbb{R}^K$ (maîtrise par skill) à partir d'observations bruitées binaires (réponse correcte / incorrecte). IRT et BKT supposent tous deux un prior ; sans prior personnalisé, l'EAP (Expected A Posteriori) est tiré par la moyenne population et biaisé pour les outliers (débutants vrais et quasi-natifs).
2. **Séquentialité contraignante** : on ne peut pas « tester » 10 items aléatoires ; la séquence elle-même est pédagogique. Un placement trop exploratoire est punitif (cf. VanLehn 2011 sur l'importance de l'immediacy du feedback adapté).
3. **Coût asymétrique** : surestimer le niveau d'un débutant (lui donner du B2 alors qu'il est A1) est bien plus coûteux que sous-estimer (lui donner du A1 alors qu'il est A2). Conséquence : les priors doivent être **prudemment bas** en cas d'incertitude.
4. **Dépendance au self-report** : contrairement à Netflix qui observe directement les visionnages, l'ITS dépend de déclarations parfois inexactes (sur-estimation fréquente chez les learners adultes, cf. littérature DIALANG et Ross 1998).

### 1.3 Stratégies classiques de mitigation

La littérature recommender systems et AIED converge sur 6 familles :

1. **Demographic / contextuel** : utiliser des variables démographiques (âge, langue maternelle, pays) comme proxies. Limite : stéréotypage, faible pouvoir discriminant individuel.
2. **Onboarding questionnaire** : demander explicitement des préférences / compétences. C'est le modèle Spotify « choisissez 3 artistes », Netflix « choisissez 3 films aimés », Duolingo « aviez-vous appris cette langue avant ? ». Équilibre à trouver : trop de questions → drop-off.
3. **Content-based** : utiliser les features des items pour recommander du contenu similaire aux quelques interactions initiales. Appliqué à l'ITS : exposer d'abord un panel de concepts (mots thématiques, audio, visuel, texte) et observer l'engagement.
4. **Hybrid (content + collaborative)** : combiner quand on a quelques interactions. Adapté au 2e–10e turn.
5. **Transfer learning cross-domain** : si le user a un historique dans un domaine connecté (ex : compte Google lié à YouTube Learning), réutiliser. Non exploitable pour AcademIA à court terme.
6. **Bandits contextuels / active learning** : exploration structurée des 10 premiers turns via UCB, Thompson sampling ou ε-greedy, avec priors initialisés par onboarding. **C'est la direction la plus prometteuse pour un ITS LLM moderne.**

Ces six familles ne sont pas exclusives : le 2025–2026 state of the art les **hybride** (Duolingo = demographic légère + onboarding court + bandit + deep KT ; ALEKS = onboarding lourd + knowledge space theory ; Khan = quasi-nul onboarding + signal comportemental rapide).

---

## 2. Open Learner Model (OLM) : principe et implications UX

### 2.1 Définition

Un Open Learner Model est un modèle interne de l'apprenant **rendu visible à l'apprenant lui-même** (et éventuellement au tuteur, aux pairs, aux parents), avec possibilité d'inspection, de contestation et parfois de négociation (Bull & Kay 2007, 2010, 2016 ; Bull 2020). Historiquement, les student models des ITS étaient des « black boxes » : le système savait (approximativement) que le learner maîtrisait mal `passé_composé_auxiliaire_être`, mais ce savoir restait interne. L'OLM rend la représentation **inspectable** au minimum, **éditable** idéalement, et **négociable** dans la forme la plus avancée.

### 2.2 Le framework SMILI

Bull et Kay ont introduit en 2007 puis révisé en 2016 le framework SMILI ☺ (Student Models that Invite the Learner In), qui formalise les questions de conception d'un OLM selon trois axes :

- **WHAT** : quelle partie du modèle est ouverte ? (complet / partiel / résumé) Quelle granularité ? (skill atomique / skill composite / score global)
- **HOW** : sous quelle forme ? (barre de progression, carte de chaleur, diagramme radar, treemap, narration textuelle, comparaisons à cohortes)
- **WHO** : ouvert à qui ? (learner seul / + teacher / + peers / + parents)

Le framework SMILI 2016 ajoute des catégories pour les tendances contemporaines : **négociabilité** (le learner peut contester et modifier), **persuasion** (le système essaie de convaincre le learner quand il conteste à tort, avec évidence à l'appui), **comparaison sociale** (cohortes anonymisées).

### 2.3 Effets empiriques

La synthèse de littérature de Bodily et al. (2018) puis la revue systématique de Jivet et al. (2020) sur OLM et dashboards d'analytics trouvent des effets positifs sur :

1. **Motivation intrinsèque et auto-efficacité** : voir son propre progrès améliore la motivation (Zimmerman, self-regulated learning).
2. **Auto-régulation (SRL)** : le learner peut planifier, monitorer, adapter (phases de Zimmerman 2000, 2008).
3. **Précision du modèle** : le learner peut corriger des inférences erronées (ex : « j'ai raté cet exercice parce que j'étais distrait, pas parce que je ne sais pas »). Utile surtout pour les outliers que les priors population ne capturent pas.
4. **Transparence éthique** : le learner comprend pourquoi le système lui propose tel exercice, ce qui réduit l'effet boîte noire (« black-box AI ») préjudiciable à la confiance.

Ces effets ne sont pas universels : un OLM mal conçu (trop complexe, anxiogène, comparatif punitif) peut être contre-productif. La littérature recommande un OLM **clair, positif, actionnable**.

### 2.4 Implications pour AcademIA

La littérature OLM a trois conséquences directes pour l'onboarding AcademIA :

1. **Le QCM d'onboarding n'est pas qu'une collecte : c'est le début de l'OLM.** Ce que le learner déclare (niveau auto-estimé, objectif) doit être **re-montré** dès le premier turn sous forme d'un « voilà ce que j'ai compris de vous, dites-moi si c'est juste ».
2. **La négociabilité est une feature, pas un nice-to-have.** Le learner doit pouvoir dire « non, je suis plutôt B2 que B1 » et le système doit soit ajuster, soit répondre avec évidence (« vous avez commis 3 erreurs sur l'accord du participe passé, ce qui suggère un B1 solide mais pas encore B2 — voulez-vous qu'on vérifie ? »).
3. **Dès le 1er turn, l'OLM doit être visible** : pas une surface distincte à chercher dans les paramètres, mais une petite vignette (« niveau estimé : A2+, concept en cours : passé composé, confiance système : moyenne ») affichée proche du chat.

Ceci s'articule avec la taxonomie d'erreurs CEFR (cf. memory `project_error_taxonomy`) : chaque entrée `error_log` alimente directement un skill de l'OLM qui devient observable.

---

## 3. Knowledge Tracing models et cold-start

Le Knowledge Tracing (KT) est le problème canonique de l'AIED : étant donné une séquence d'observations $(q_1, r_1), (q_2, r_2), \ldots, (q_t, r_t)$ où $q_i$ est une question et $r_i \in \{0, 1\}$ la réponse, estimer la probabilité de réponse correcte à $q_{t+1}$, ce qui revient à inférer la maîtrise latente. Trois grandes familles : BKT (probabiliste structuré), DKT (récurrent profond), AKT (attentif profond).

### 3.1 Bayesian Knowledge Tracing (BKT — Corbett & Anderson 1995)

BKT modélise chaque skill comme un HMM à deux états latents (maîtrisé / non maîtrisé), avec 4 paramètres :

- $P(L_0)$ : **prior**, probabilité initiale de maîtrise.
- $P(T)$ : **learn rate**, probabilité de transition non-maîtrisé → maîtrisé à une opportunité d'apprentissage.
- $P(G)$ : **guess**, probabilité de répondre correctement sans maîtriser.
- $P(S)$ : **slip**, probabilité de se tromper en maîtrisant.

Mise à jour bayésienne classique après observation $r_t$ (Corbett & Anderson 1995 ; Van de Sande 2013) :

$$
P(L_n \mid r_n = 1) = \frac{P(L_{n-1}) \cdot (1 - P(S))}{P(L_{n-1}) \cdot (1 - P(S)) + (1 - P(L_{n-1})) \cdot P(G)}
$$

$$
P(L_n \mid r_n = 0) = \frac{P(L_{n-1}) \cdot P(S)}{P(L_{n-1}) \cdot P(S) + (1 - P(L_{n-1})) \cdot (1 - P(G))}
$$

Puis application de la transition :

$$
P(L_{n+1}) = P(L_n \mid r_n) + (1 - P(L_n \mid r_n)) \cdot P(T)
$$

#### Le problème du prior

En pratique, les quatre paramètres sont ajustés par EM ou brute-force grid search sur les données historiques (PSLC DataShop, ASSISTments). Le prior $P(L_0)$ est classiquement estimé **par skill au niveau population**, soit typiquement $\approx 0.2$–$0.4$ selon le domaine. C'est précisément là que réside le cold-start :

- Un learner novice vrai a $P(L_0)_{\text{réel}} \approx 0$.
- Un learner expert retournant à la plateforme a $P(L_0)_{\text{réel}} \approx 0.9$.
- Utiliser $0.3$ pour les deux coûte cher : pour le novice, on surestime et on propose trop dur ; pour l'expert, on sous-estime et on ennuie. La variance est énorme autour de la moyenne population.

#### Prior Per Student (Pardos & Heffernan 2010)

Pardos et Heffernan (UMAP 2010) ont introduit le modèle Prior-Per-Student (PPS) qui individualise $P(L_0)$ au niveau de chaque apprenant. Ils ont comparé trois stratégies pour estimer le prior individuel :

1. Prior basé sur la moyenne de la population (baseline).
2. Prior basé sur la première réponse du learner sur le skill (« priorize on first response »).
3. Prior basé sur l'historique multi-skills du learner (« multi-skill prior »).

Résultat : la stratégie 3 domine, avec amélioration de la prédiction sur 33 des 42 problem sets évalués. L'implication cold-start est claire : **dès qu'on dispose d'une seule observation comportementale pertinente, individualiser $P(L_0)$ est strictement préférable au prior population**. Et si l'on peut faire mieux : utiliser le self-report pré-first-response pour poser $P(L_0)$ conditionnel au QCM d'onboarding.

#### Extension : Yudelson, Koedinger, Gordon (2013)

Individualized BKT avec per-student ET per-skill learn rates. Gain marginal supplémentaire, au prix de davantage de paramètres à ajuster et d'un risque d'overfit pour les learners à faible historique. Pour un cold-start pur (turn 0 à 5), le PPS simple est l'option recommandée.

### 3.2 Deep Knowledge Tracing (DKT — Piech et al. 2015)

Piech et al. (NeurIPS 2015) ont proposé de remplacer le HMM BKT par un LSTM qui prend en entrée la séquence $(q_i, r_i)$ one-hot encodée et prédit à chaque pas la distribution sur les skills futurs. Gains annoncés : AUC de 0.86 sur ASSISTments vs. 0.69 pour BKT (≈ +25%). Pas de paramétrage humain explicite ; le modèle apprend des représentations denses des skills.

#### Forces

- Capture des dépendances inter-skills (prerequisite, transfer) sans les encoder à la main.
- Fonctionne mieux quand on a beaucoup de données.
- Robuste aux erreurs de tagging expert des skills (la relation skill↔item peut être floue).

#### Faiblesses pour le cold-start

1. **Besoin de données massives** : DKT n'est pas performant sans corpus d'entraînement large. Pour un nouveau produit ou une nouvelle langue, data scarcity rend DKT peu fiable — BKT/IRT sont plus économes en données.
2. **Absence de prior explicite inspectable** : l'état caché d'un LSTM n'est pas directement interprétable comme « P(maîtrise) ». Pour un OLM, il faut projeter sur un espace latent lisible, ce qui complique la transparence.
3. **Cold-start learner → représentation dégénérée** : au turn 0, l'état caché est un vecteur zéro ; toute prédiction relève de la moyenne population. DKT n'a pas de mécanisme intégré de personnalisation initiale. Des travaux ultérieurs (DKT+ Yeung & Yeung 2018, DKVMN Zhang et al. 2017, SAKT Pandey & Karypis 2019) partagent cette limite.

### 3.3 Attentive Knowledge Tracing (AKT — Ghosh, Heffernan & Lan 2020)

Ghosh et al. (KDD 2020) ont proposé AKT qui combine :

1. Une attention monotone qui pondère les interactions passées selon une **décroissance exponentielle contextuelle** (distance temporelle × similarité).
2. Une régularisation par le modèle de Rasch (IRT 1PL) sur les embeddings de questions et de concepts, ce qui capture les différences inter-questions au sein d'un même skill sans exploser le nombre de paramètres.
3. Une interprétabilité supérieure : les poids d'attention peuvent être visualisés, ouvrant la porte à un OLM partiellement compatible.

Gain : jusqu'à +6% AUC sur BKT/DKT/SAKT selon le dataset. Comme DKT, AKT souffre du cold-start au niveau learner mais moins au niveau item grâce au prior Rasch.

### 3.4 Synthèse : quel KT pour AcademIA phase onboarding ?

Le tableau suivant résume les trade-offs :

| Modèle | Prior cold-start | Interprétabilité OLM | Data requise | Complexité |
|--------|------------------|----------------------|--------------|------------|
| BKT classique | Population, pauvre | Haute (4 params/skill) | Faible | Très faible |
| BKT-PPS (Pardos & Heffernan) | Individualisé si on a un signal | Haute | Faible | Faible |
| BKT individualisé (Yudelson) | Très individualisé | Haute | Moyenne | Moyenne |
| IRT / Rasch | Estimation conjointe $\theta$ × $b$ | Haute | Moyenne | Faible |
| DKT | Population (vecteur zéro) | Faible | Élevée | Élevée |
| AKT | Population + Rasch | Moyenne | Élevée | Élevée |
| KTM (Vie & Kashima 2019) | Via factorisation et side info | Moyenne | Moyenne | Moyenne |

**Recommandation AcademIA (phase 1)** : BKT-PPS ou IRT 1PL, avec $P(L_0)$ calibré sur les 4–8 items d'onboarding via une fonction déterministe (cf. §6). Migration vers DKT/AKT envisagée quand on aura ≥ 100 K trajectoires (ordre de grandeur).

### 3.5 Rôle opérationnel du prior : un exemple chiffré

Supposons deux learners pour le skill `conditionnel_passé_ES` :

- **Ana** : novice vraie, $P(L_0)_{\text{réel}} = 0.05$.
- **Luis** : bilingue portugais, $P(L_0)_{\text{réel}} = 0.70$ (transfert romance fort).

Avec un prior population $P(L_0) = 0.30$ :
- Ana répond faux au 1er item. Posterior $P(L_1 \mid r=0) \approx 0.13$. Encore loin du vrai 0.05.
- Luis répond juste. Posterior $P(L_1 \mid r=1) \approx 0.53$. Encore loin du vrai 0.70.

Il faut 4–6 observations avant que le posterior converge vers la vérité. En attendant, la recommandation de difficulté est biaisée : Ana reçoit des items calibrés pour $0.13$ (trop dur), Luis reçoit des items calibrés pour $0.53$ (trop facile). Résultat : frustration et ennui.

Avec des priors personnalisés issus du QCM d'onboarding — Ana déclare « débutante », Luis déclare « bilingue portugais + niveau conversationnel espagnol » — on part de $P(L_0)_{\text{Ana}} = 0.08$ et $P(L_0)_{\text{Luis}} = 0.65$. La convergence est quasi immédiate et les premiers turns tombent dans la zone de flow.

**C'est exactement ce que la littérature PPS démontre empiriquement (Pardos & Heffernan 2010).**

---

## 4. Cold-start recommender systems : exploration-exploitation

### 4.1 Les deux régimes

Le cold-start, en théorie des bandits contextuels, n'est pas un problème distinct : c'est le régime **exploration dominante** d'un problème exploration-exploitation (E-E) où l'agent doit maximiser la récompense cumulée $\mathbb{E}[\sum_t r_t]$ sans connaître au départ les paramètres de la distribution des récompenses.

- **Exploration** : choisir une action dont la valeur est incertaine pour acquérir de l'information.
- **Exploitation** : choisir l'action actuellement la mieux estimée.

Dans un ITS LLM, chaque action = un type de turn (exercice, explication, conversation libre, quiz, récap). La récompense est multidimensionnelle : learning gain, engagement (temps passé, retour J+1), satisfaction (feedback explicite).

### 4.2 Algorithmes canoniques

- **ε-greedy** : exploite avec probabilité $1-\varepsilon$, explore uniformément avec probabilité $\varepsilon$. Simple, souvent baseline.
- **UCB (Upper Confidence Bound)** : choisit $a_t = \arg\max_a [\hat{\mu}_a + c \sqrt{\ln t / n_a}]$. Optimiste face à l'incertitude. Propriétés théoriques de regret $O(\sqrt{T \log T})$.
- **Thompson sampling** : maintient une distribution posterior sur les paramètres de chaque bras, échantillonne et choisit l'argmax. Performant empiriquement, élégant en bayésien.
- **Contextual bandits** (LinUCB, neural bandits) : intègrent un contexte $x_t$ (ici : embedding du learner issu de l'OLM). Permettent le transfert entre learners similaires.

### 4.3 Trade-offs pour un ITS

Explorer trop = frustrer le learner (items hors de la ZPD). Exploiter trop = stuck in local optimum (on ne découvre jamais les capacités latentes). La littérature ITS converge sur deux heuristiques :

1. **Shrinking exploration** : démarrer avec un $\varepsilon$ élevé (0.3–0.5) et le décroître rapidement sur les 20 premiers turns. S'aligne sur l'intuition que l'incertitude décroît vite avec les premières observations.
2. **Exploration contrainte pédagogiquement** : au lieu d'explorer uniformément, contraindre l'exploration à la zone $[\hat{\theta} - 1\sigma, \hat{\theta} + 1\sigma]$ où $\hat{\theta}$ est l'estimée courante du niveau. Garantit que même un turn exploratoire reste dans une ZPD plausible.

### 4.4 Applications ITS récentes

- **Hierarchical Multi-Armed Bandits for Concurrent Intelligent Tutoring** (Aiyappa et al. arXiv 2408.07208, 2024) : bandit hiérarchique pour sélectionner concept puis difficulté, montre amélioration vs. heuristique statique.
- **Settles & Meeder 2016** (Duolingo, ACL 2016) : half-life regression pour spaced repetition. Pas un bandit au sens strict, mais logique proche — trade-off rétention (exploiter) vs. nouveauté (explorer).
- **Lopes et al.** : bandits en tutorial dialogue systems, gains modestes mais positifs sur engagement.

### 4.5 Implication pour AcademIA

Pour AcademIA, le bandit sert à sélectionner le **type** et la **difficulté** du 1er turn. Avec les priors issus du QCM :

- **Concept** : déterministique (carte de concepts × niveau estimé → concept prioritaire selon pedagogical sequence).
- **Difficulté** : Thompson sampling avec prior $\beta(\alpha_0, \beta_0)$ où $\alpha_0, \beta_0$ sont initialisés par le QCM (plus le self-report est cohérent et confiant, plus $\alpha_0 + \beta_0$ est grand — prior fort — et moins on explore).
- **Format** : bandit sur {lecture, audio, dialogue, quiz} contraint par la préférence déclarée Bloc C.

---

## 5. Benchmark des systèmes ITS réels

### 5.1 ASSISTments (Heffernan & Heffernan, IJAIED 2014)

ASSISTments, hébergé par Worcester Polytechnic Institute, est un des ITS les plus étudiés académiquement. Le mot combine « ASSISTance » et « assessMENT » — le système assiste les élèves tout en évaluant les enseignants. Déployé massivement en classes de math US, il sert aussi de **plateforme de recherche** (les données ont alimenté des centaines de publications EDM/AIED).

#### Cold-start approach

- **Onboarding minimal** : pas de questionnaire initial complexe. L'élève est enrôlé par son enseignant dans un problem set.
- **Placement implicite** : le problem set lui-même est calibré par l'enseignant pour la classe, pas individualisé au départ.
- **Knowledge Tracing actif** : un BKT (puis des variantes) tourne dès le 1er item pour estimer la maîtrise par skill.
- **Prior population** : $P(L_0)$ estimé sur la cohorte classe (amélioration : PPS de Pardos & Heffernan 2010 développé sur ASSISTments).
- **Self-assessment light** : certains sous-modules demandent au learner « à quel point es-tu confiant ? » après réponse — signal utilisé pour recalibrer slip/guess (Baker et al. 2008 sur contextual estimation).

#### Leçons pour AcademIA

1. **Calibrage par cohorte** fonctionne si on a une cohorte définie (classe). Pour AcademIA (B2C, learners isolés), moins applicable.
2. **Self-assessment léger intra-turn** est une pratique éprouvée et peu intrusive, qui pourrait enrichir l'OLM.
3. **BKT + PPS** est un standard établi pour ce type de matière structurée.

### 5.2 ALEKS (Assessment and LEarning in Knowledge Spaces)

ALEKS, basé sur la Knowledge Space Theory (KST) de Falmagne et Doignon (1985, formalisé dans le livre *Learning Spaces* 2011 et repris dans Falmagne et al. 2013, Matayoshi 2021), adopte une philosophie inverse d'ASSISTments : un **placement assessment long mais fait une fois**.

#### Principes

- Un **knowledge space** $\mathcal{K} \subseteq 2^Q$ est un ensemble d'états de connaissance compatibles avec la structure de prérequis du domaine. Chaque état = sous-ensemble des skills maîtrisés.
- Le placement assessment navigue adaptivement dans ce graphe via un processus markovien qui élimine les états incompatibles avec les réponses.
- En 20–25 questions, ALEKS identifie l'état exact (parmi souvent plusieurs milliers possibles) — efficacité démontrée par Falmagne et équipe sur des millions d'étudiants.

#### Cold-start approach

- **Onboarding = placement assessment 20–25 items, 30–45 min**. Long mais unique.
- Pas de self-report ; tout est comportemental.
- Après placement : recommandations déterministes (« What you are ready to learn next » = les skills dont tous les prérequis sont maîtrisés mais pas ce skill lui-même).

#### Leçons pour AcademIA

1. **Un placement long fonctionne pour un commitment fort** (classe universitaire obligatoire). Pas applicable à un B2C consumer où le taux d'abandon grimpe exponentiellement après 2–3 minutes d'onboarding.
2. **La structure de prérequis est puissante** : pour une langue, on peut bâtir un knowledge space CEFR-based (A1.1 → A1.2 → A2.1 …). C'est une direction moyen terme pour AcademIA.
3. **Placement one-shot vs. continuous** : AcademIA doit plutôt viser continuous (observer chaque turn) car les learners adultes sont hétérogènes et auto-dirigés.

### 5.3 Khan Academy

Khan Academy pratique le **mastery learning** : chaque skill a un niveau (Attempted / Familiar / Proficient / Mastered) et le learner progresse via Mastery Challenges personnalisés.

#### Cold-start approach

- **Onboarding quasi inexistant** : pas de test de niveau obligatoire. Le learner choisit une matière (ou est placé par un teacher) et commence.
- **Signal comportemental très rapide** : les premiers exercices sont fixes (à l'ouverture d'un skill donné), les niveaux de mastery s'ajustent ensuite dynamiquement.
- **Mastery Challenges** : 6 questions sur 3 skills, personnalisées selon l'espacement et le niveau courant.
- **Philosophie Sal Khan** : self-paced, « don't move on until you master ». La calibration est implicite — si c'est trop dur, le learner échoue et le niveau redescend.

#### Leçons pour AcademIA

1. **Minimiser l'onboarding** est une option viable si le 1er turn est **auto-calibrant** robustement. Pour Khan, c'est le cas parce que les items math sont discrets et qu'une série de 3–6 items donne rapidement un signal.
2. **Mais pour un ITS LLM conversationnel, le 1er turn est moins standardisé** qu'un quiz Khan, donc plus difficile à auto-calibrer sans prior. Conséquence : un minimum d'onboarding (4–8 items) est plus adapté à AcademIA.
3. **Mastery levels visibles** (Khan affiche clairement `Proficient` etc.) est un bon exemple d'OLM simple.

### 5.4 Duolingo

Duolingo est probablement le benchmark le plus pertinent pour AcademIA (L2 learning, consumer, mobile-first, ML-heavy).

#### Cold-start approach

- **Deux parcours** : « Je débute » (commence au A1) ou « Je connais déjà cette langue » (déclenche un placement test court, 5–10 min adaptatif).
- **Placement test adaptatif** : version interne de Duolingo Placement, distincte du Duolingo English Test (DET). Burr Settles (research director) a publié plusieurs fois sur les modèles sous-jacents.
- **Calibration par erreurs comportementales** : même sans placement test, Duolingo ajuste rapidement la difficulté via les erreurs des premiers exercices.
- **Onboarding questions légères** : « Pourquoi apprends-tu ? », « Combien de minutes par jour ? », objectif quotidien (5/10/15/20 min). Ces réponses alimentent plus l'engagement / motivation que le prior de difficulté.
- **Pas de self-report CEFR explicite** : Duolingo préfère mesurer comportementalement. Les traces collectées sont massives (plusieurs dizaines de millions de learners actifs), ce qui rend le comportemental viable.
- **Spaced repetition (HLR) Settles & Meeder 2016** : une fois que le learner est entré, la rétention est pilotée par half-life regression trainable, qui prédit la probabilité de rappel d'un item en fonction de la dernière révision et des erreurs passées. Résultats publiés : +12% activité globale, +9.5% rétention pratiques.

#### Leçons pour AcademIA

1. **Deux parcours (novice / avec acquis) au début** est UX-winning et pertinent.
2. **Onboarding léger orienté motivation** (raison, temps) + placement optionnel calibrage niveau : c'est la structure la plus imitable.
3. **Half-life regression** s'intègre bien avec un BKT/IRT pour gérer le rappel post-onboarding. À considérer pour AcademIA phase 2.
4. **Le comportemental fonctionne à l'échelle Duolingo** parce qu'ils ont 50 M+ utilisateurs actifs. Pour AcademIA en phase de lancement, **s'appuyer davantage sur le self-report** est rationnel tant que le corpus comportemental n'est pas dense.

### 5.5 Comparaison synthétique

| Système | Onboarding items | Temps onboarding | Prior type | KT model | OLM visible |
|---------|------------------|------------------|------------|----------|-------------|
| ASSISTments | ~0 (classe-level) | 0 | Cohorte | BKT / PPS | Partiel (teacher dashboard) |
| ALEKS | 20–25 | 30–45 min | Individuel (KST) | Knowledge Space | Oui (pie chart) |
| Khan Academy | ~0 | 0 | Population | Proprio (mastery thresholds) | Oui (mastery levels) |
| Duolingo | 3–5 questions + placement optionnel | 1–10 min | Mix (self-report + comportemental) | Proprio (HLR + deep KT) | Partiel |
| **AcademIA proposé** | **7 items + 1 placement** | **90 s** | **Personnalisé QCM + PPS** | **BKT-PPS / IRT, migration AKT** | **Oui, négociable** |

Le positionnement AcademIA vise le sweet spot : plus riche que Khan / Duolingo (parce que learners adultes hétérogènes et corpus comportemental initial pauvre), plus léger qu'ALEKS (parce que B2C consumer, drop-off rapide), avec OLM explicite plus avancé que la concurrence.

---

## 6. Recommandations AcademIA : un QCM de 8 items + Teacher continue à calibrer

### 6.1 Principes directeurs

1. **4–8 items self-report**, pas plus (cf. §4 RecSys et Desmarais & Baker 2012).
2. **Mix déclaratif / contextuel / comportemental léger** (1 item comportemental suffit à réduire l'over-claim).
3. **OLM inspectable dès le 2e turn** : renvoyer au learner ce qui a été inféré.
4. **Priors personnalisés** $P(L_0)$ calibrés comme fonction déterministe des réponses QCM.
5. **Taxonomie d'erreurs CEFR** (cf. `project_error_taxonomy`) pour calibration continue post-onboarding.
6. **Fallback safety** : si le learner répond des choses incohérentes ou abandonne le QCM, utiliser un prior conservateur ($P(L_0) = 0.15$, un « débutant présumé prudent »).

### 6.2 Proposition concrète : 7 items QCM (avec justification)

#### Bloc A — Contexte (3 items, ~25 s)

**A1. Quelle est votre langue maternelle ?**
- Rationale : transferts L1→L2 fortement prédictifs des patterns d'erreurs (ex : hispanophone vers italien apprend plus vite grammaire qu'un anglophone mais hérite de faux-amis). Alimentera la taxonomie d'erreurs contextualisée.

**A2. Votre objectif principal avec [langue cible] ?**
- Options : Voyage / Conversation sociale / Professionnel / Académique / Loisir / Autre (libre).
- Rationale : pilote la sélection de thématiques du 1er turn (bandit sur {touristique, business, académique, culture}).

**A3. Combien de minutes par jour voulez-vous consacrer ?**
- Options : 5 / 10 / 20 / 30+ min.
- Rationale : (a) contrôle le pacing des sessions, (b) sert à calibrer les intervalles de spaced repetition si on adopte un HLR-like ensuite.

#### Bloc B — Auto-évaluation CEFR (2 items, ~30 s)

**B1. Can-do compréhension (écrite + orale combinée, inspiré DIALANG)** — le learner sélectionne l'énoncé qui lui ressemble le plus parmi :
- « Je ne comprends rien ou presque. » (→ A0/A1)
- « Je comprends des mots et phrases très simples si on parle lentement. » (→ A1)
- « Je comprends le sens général si le sujet est familier et simple. » (→ A2)
- « Je comprends l'essentiel d'une conversation ou d'un texte standard sur des sujets familiers. » (→ B1)
- « Je comprends des textes complexes et des discussions à débit normal. » (→ B2)
- « Je comprends presque tout, y compris des nuances et registres variés. » (→ C1/C2)

**B2. Can-do expression (orale + écrite combinée)** — symétrique, 6 options de A0 à C2.

Rationale : les can-do CEFR (DIALANG, CEFR self-assessment grid) ont été validés empiriquement (Alderson 2005, Luoma 2004, revues Eurocentres) comme corrélés avec les scores externes (r ≈ 0.4–0.6 selon études, suffisant pour un prior). Deux items suffisent pour capturer la dimension réceptive vs. productive, qui peuvent diverger (particulièrement fréquent chez les learners adultes).

#### Bloc C — Préférences (1 item, ~5 s)

**C1. Quel format préférez-vous ?**
- Options : Lire des textes / Écouter de l'audio / Discuter à l'oral avec l'IA / Faire des quiz rapides / Mix.
- Rationale : pilote le bandit de format pour le 1er turn. Gain d'engagement important sans coût de calibration (préférence déclarée = préférence initiale, ajustée ensuite par comportement).

#### Bloc D — Observation comportementale (1 item, ~20 s)

**D1. Question de placement calibrée sur le niveau déclaré ± 1 CEFR.**
- Si B1 + B2 moyennent à B1 → proposer un item B1.
- Si moyenne à A2 → proposer un item A2.
- L'item est choisi dans une banque calibrée IRT 1PL sur le niveau cible.
- Rationale : réduit l'over-claim (tendance documentée dans la littérature self-assessment, Ross 1998 ; cf. Blanche & Merino 1989). Si le learner échoue un item présumé dans sa ZPD, on abaisse le prior ; s'il réussit trop facilement (temps < seuil), on relève.

#### Total : 7 items + 1 item comportemental = 8, durée ≈ 80–100 s.

### 6.3 Calcul du prior $P(L_0)$ à partir du QCM

Définissons $\theta_{\text{prior}} \in [0, 1]$ comme probabilité initiale de maîtrise du niveau cible (où « niveau cible » est le CEFR du prochain turn proposé).

Soient :
- $\mu_B = \text{mean}(\text{CEFR}_{B1}, \text{CEFR}_{B2})$ après mapping A0=0, A1=1, …, C2=5.
- $\delta_{D1} = +1$ si D1 réussi vite, $0$ si réussi lentement, $-1$ si échoué.
- $\mu_{\text{adj}} = \mu_B + 0.5 \cdot \delta_{D1}$ (ajustement comportemental léger).
- Bonus L1-cible : $+0.3$ si L1 est linguistiquement proche (ex : portugais → espagnol). Table de distances pré-calculée hors-ligne.

Niveau-cible proposé = $\mu_{\text{adj}}$ arrondi au CEFR le plus proche.

$P(L_0) = 0.5 + 0.1 \cdot (\mu_{\text{adj}} - \text{niveau-cible})$ (centré sur 0.5 si pile au niveau, augmenté si au-dessus, diminué si en-dessous).

Tronqué à $[0.05, 0.95]$ pour éviter les dégénérescences bayésiennes.

**Cette fonction est une proposition initiale à calibrer empiriquement sur les premières cohortes alpha.**

### 6.4 OLM négociable à partir du turn 2

À la fin du 1er turn, afficher au learner :

```
🧭 Ce que j'ai compris de vous :
- Niveau estimé : B1 (intermédiaire)
- Objectif : professionnel
- Format préféré : conversation
- Confiance système : moyenne (on ajuste dans les prochains tours)

[ ✓ C'est juste ] [ ✏️ Je veux corriger ]
```

Si le learner corrige → réajuster les priors et logger l'événement `onboarding_override` pour audit futur.

### 6.5 Calibration continue post-onboarding

Chaque tour, le Teacher :

1. Génère un turn (contenu, difficulté, format) conditionné sur l'OLM courant.
2. Observe la réponse du learner.
3. Applique la taxonomie CEFR d'erreurs (cf. `project_error_taxonomy`) pour classifier chaque erreur selon sa gravité par niveau.
4. Met à jour les skills BKT/IRT correspondants.
5. Met à jour le niveau estimé si convergence sur N tours consécutifs.
6. Expose l'update à l'OLM si la variation dépasse un seuil (pour éviter les oscillations anxiogènes).

### 6.6 Sanity checks et edge cases

- **Learner abandonne au milieu du QCM** → prior conservateur $P(L_0) = 0.15$, niveau cible A1, observation longue requise.
- **Learner over-claims** (déclare C2, échoue item A2) → prior aligné sur comportement, message OLM « on a révisé votre niveau vers B1 basé sur le premier exercice, est-ce que c'est cohérent avec ce que vous ressentez ? ».
- **Learner under-claims** (déclare A1, réussit items B1 sans effort) → prior aligné sur comportement, message OLM encourageant.
- **L1 non listée / multilingue** → fallback sur langue dominante déclarée ou neutre ; ne bloque pas l'onboarding.

### 6.7 Métriques produit recommandées

Dès l'alpha :

- **Completion rate** du QCM (objectif > 85%).
- **Temps onboarding médian** (objectif < 120 s).
- **Override rate** à l'OLM turn 2 (surveillance : si > 30%, le QCM est mal calibré).
- **D1 / D7 retention** du cohort onboardée vs. baseline historique.
- **Flow proxy** : distribution des `error_log` par niveau de difficulté — on veut une médiane autour de 20–40% d'erreurs (ZPD).
- **Coverage du prior** : distribution empirique de $P(L_0)$ issue du QCM ; on doit voir une dispersion large (signe que le QCM discrimine).

---

## 7. Discussion et limites

### 7.1 Limites de l'approche proposée

1. **Self-report reste bruité.** Même avec can-do statements validés, r ≈ 0.5 avec score externe laisse 50% de variance inexpliquée. C'est pour cela que l'item comportemental D1 et la calibration continue sont essentiels.
2. **Absence de reviewers natifs** (cf. memory `project_no_native_reviewers`) : nous ne pourrons valider la taxinomie d'erreurs CEFR ES/IT/DE/JP/RU qu'indirectement, via corpus oracle + consensus LLM + télémétrie alpha. L'onboarding lui-même est relativement peu exposé à ce risque (les can-do sont standard CEFR, traduits officiellement par le Conseil de l'Europe), mais les skills de détail dépendront de la taxinomie.
3. **Bandit sur format = peu de données initiales** : le choix du format optimal par learner restera bruité sur les 20 premiers turns. À surveiller.
4. **Non-stationnarité du learner** : le niveau réel bouge (surtout en L2, plateaux et sprints). Un BKT standard suppose un état qui ne retourne pas de « maîtrisé » à « non maîtrisé ». La réalité inclut l'oubli. HLR ou BKT-forget (Khajah et al. 2016) à considérer en phase 2.

### 7.2 Travaux connexes non détaillés ici

- **Performance Factors Analysis (PFA)** — Pavlik et al. 2009 — alternative à BKT, compte les succès/échecs passés.
- **Learning Factor Analysis (LFA)** — Cen et al. 2006 — modèle logistique mixte similaire.
- **SAKT** (Pandey & Karypis 2019), **SAINT** (Choi et al. 2020), **LPKT** (Shen et al. 2021) : variantes de KT à attention.
- **Item Response Theory multi-facettes** (MFRM) — utile si on veut intégrer difficulté + discrimination + biais sévérité annotateur.
- **Cognitive Diagnostic Models** (DINA, G-DINA) — plus fins sur la maîtrise de skills multiples par item ; complexes à calibrer.

### 7.3 Prochaines vagues de recherche recommandées

- **Vague 2** : onboarding de systèmes LLM-tutor spécifiques (Khanmigo, Duolingo Max, Replika-for-learning) — UX et système prompt patterns.
- **Vague 3** : learner modeling longitudinal — comment passer d'un prior cold-start à un user embedding dense après 50+ turns, et quelles représentations privilégier pour la mémoire long-terme du tuteur.

---

## 8. Bibliographie

### Knowledge Tracing / Student Models

- **Corbett, A.T., & Anderson, J.R. (1995).** Knowledge tracing: Modeling the acquisition of procedural knowledge. *User Modeling and User-Adapted Interaction*, 4(4), 253–278. DOI: 10.1007/BF01099821. URL: https://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/893CorbettAnderson1995.pdf
- **Piech, C., Bassen, J., Huang, J., Ganguli, S., Sahami, M., Guibas, L., & Sohl-Dickstein, J. (2015).** Deep Knowledge Tracing. *Advances in Neural Information Processing Systems 28 (NeurIPS 2015)*, 505–513. URL: https://proceedings.neurips.cc/paper/2015/hash/bac9162b47c56fc8a4d2a519803d51b3-Abstract.html
- **Ghosh, A., Heffernan, N., & Lan, A.S. (2020).** Context-Aware Attentive Knowledge Tracing. *Proceedings of the 26th ACM SIGKDD Conference (KDD 2020)*. DOI: 10.1145/3394486.3403282. arXiv: 2007.12324. URL: https://arxiv.org/abs/2007.12324
- **Pardos, Z.A., & Heffernan, N.T. (2010).** Modeling Individualization in a Bayesian Networks Implementation of Knowledge Tracing. *UMAP 2010 (User Modeling, Adaptation and Personalization)*. DOI: 10.1007/978-3-642-13470-8_24. URL: https://people.csail.mit.edu/zp/papers/UMAP_final.pdf
- **Yudelson, M.V., Koedinger, K.R., & Gordon, G.J. (2013).** Individualized Bayesian Knowledge Tracing Models. *AIED 2013*. URL: https://www.cs.cmu.edu/~ggordon/yudelson-koedinger-gordon-individualized-bayesian-knowledge-tracing.pdf
- **Baker, R.S.J.d., Corbett, A.T., & Aleven, V. (2008).** More Accurate Student Modeling through Contextual Estimation of Slip and Guess Probabilities in Bayesian Knowledge Tracing. *ITS 2008*. DOI: 10.1007/978-3-540-69132-7_44.
- **Van de Sande, B. (2013).** Properties of the Bayesian Knowledge Tracing Model. *Journal of Educational Data Mining*, 5(2). URL: https://jedm.educationaldatamining.org/index.php/JEDM/article/download/35/pdf_27
- **Desmarais, M.C., & Baker, R.S.J.d. (2012).** A review of recent advances in learner and skill modeling in intelligent learning environments. *User Modeling and User-Adapted Interaction*, 22(1–2), 9–38. DOI: 10.1007/s11257-011-9106-8. URL: https://link.springer.com/article/10.1007/s11257-011-9106-8
- **Vie, J.-J., & Kashima, H. (2019).** Knowledge Tracing Machines: Factorization Machines for Knowledge Tracing. *AAAI 2019*, 33, 750–757. URL: https://github.com/jilljenn/ktm
- **Pavlik, P.I., Cen, H., & Koedinger, K.R. (2009).** Performance Factors Analysis: A New Alternative to Knowledge Tracing. *AIED 2009*.
- **Khajah, M., Lindsey, R.V., & Mozer, M.C. (2016).** How Deep is Knowledge Tracing? *EDM 2016*. URL: https://www.educationaldatamining.org/EDM2016/proceedings/paper_144.pdf
- **Zhang, J., Shi, X., King, I., & Yeung, D.-Y. (2017).** Dynamic Key-Value Memory Networks for Knowledge Tracing. *WWW 2017*.
- **Pandey, S., & Karypis, G. (2019).** A Self-Attentive model for Knowledge Tracing. *EDM 2019*.
- **Choi, Y. et al. (2020).** Towards an Appropriate Query, Key, and Value Computation for Knowledge Tracing. *L@S 2020* (SAINT).

### Open Learner Models / Self-Regulated Learning

- **Bull, S., & Kay, J. (2007).** Student Models that Invite the Learner In: The SMILI☺ Open Learner Modelling Framework. *International Journal of Artificial Intelligence in Education*, 17(2), 89–120. URL: https://journals.sagepub.com/doi/10.3233/IRG-2007-17%282%2902
- **Bull, S., & Kay, J. (2010).** Open Learner Models. In *Advances in Intelligent Tutoring Systems*. Springer. DOI: 10.1007/978-3-642-14363-2_15.
- **Bull, S., & Kay, J. (2016).** SMILI☺: a Framework for Interfaces to Learning Data in Open Learner Models, Learning Analytics and Related Fields. *International Journal of Artificial Intelligence in Education*, 26, 293–331. DOI: 10.1007/s40593-015-0090-8. URL: https://link.springer.com/article/10.1007/s40593-015-0090-8
- **Bodily, R., Kay, J., Aleven, V., Jivet, I., Davis, D., Xhakaj, F., & Verbert, K. (2018).** Open Learner Models and Learning Analytics Dashboards: A Systematic Review. *LAK 2018*. DOI: 10.1145/3170358.3170409.
- **Jivet, I., Scheffel, M., Schmitz, M., Robbers, S., Specht, M., & Drachsler, H. (2020).** From students with love: An empirical study on learner goals, self-regulated learning and sense-making of learning analytics in higher education. *The Internet and Higher Education*.
- **Zimmerman, B.J. (2000).** Attaining self-regulation: A social cognitive perspective. In *Handbook of Self-Regulation*, Academic Press, 13–39.
- **Zimmerman, B.J. (2008).** Investigating self-regulation and motivation: Historical background, methodological developments, and future prospects. *American Educational Research Journal*, 45(1), 166–183.

### ITS benchmarks

- **Heffernan, N.T., & Heffernan, C.L. (2014).** The ASSISTments Ecosystem: Building a Platform that Brings Scientists and Teachers Together for Minimally Invasive Research on Human Learning and Teaching. *International Journal of Artificial Intelligence in Education*, 24(4), 470–497. DOI: 10.1007/s40593-014-0024-x. URL: https://link.springer.com/article/10.1007/s40593-014-0024-x
- **VanLehn, K. (2011).** The Relative Effectiveness of Human Tutoring, Intelligent Tutoring Systems, and Other Tutoring Systems. *Educational Psychologist*, 46(4), 197–221. DOI: 10.1080/00461520.2011.611369. URL: https://www.tandfonline.com/doi/abs/10.1080/00461520.2011.611369
- **Ma, W., Adesope, O.O., Nesbit, J.C., & Liu, Q. (2014).** Intelligent Tutoring Systems and Learning Outcomes: A Meta-Analysis. *Journal of Educational Psychology*, 106(4), 901–918. URL: https://www.apa.org/pubs/journals/features/edu-a0037123.pdf
- **Falmagne, J.-C., Albert, D., Doble, C., Eppstein, D., & Hu, X. (Eds.) (2013).** *Knowledge Spaces: Applications in Education*. Springer.
- **Doignon, J.-P., & Falmagne, J.-C. (1985).** Spaces for the assessment of knowledge. *International Journal of Man-Machine Studies*, 23(2), 175–196.
- **Falmagne, J.-C., & Doignon, J.-P. (2011).** *Learning Spaces*. Springer.
- **Matayoshi, J. (2021).** A practical perspective on knowledge space theory: ALEKS and its data. *Journal of Mathematical Psychology*, 101. URL: https://jmatayoshi.github.io/publications/JMP2021_KST_ALEKS_preprint.pdf
- **Settles, B., & Meeder, B. (2016).** A Trainable Spaced Repetition Model for Language Learning. *Proceedings of ACL 2016*, 1848–1858. URL: https://research.duolingo.com/papers/settles.acl16.pdf
- **Settles, B., LaFlair, G.T., & Hagiwara, M. (2020).** Machine Learning–Driven Language Assessment. *Transactions of the Association for Computational Linguistics*, 8, 247–263. URL: https://research.duolingo.com/papers/settles.tacl20.pdf
- **Khan Academy (2023).** Using Khan Academy for personalized practice and mastery. Khan for Educators. URL: https://www.khanacademy.org/khan-for-educators/

### Cold-start et bandits

- **Schein, A.I., Popescul, A., Ungar, L.H., & Pennock, D.M. (2002).** Methods and Metrics for Cold-Start Recommendations. *SIGIR 2002*.
- **Lika, B., Kolomvatsos, K., & Hadjiefthymiades, S. (2014).** Facing the cold start problem in recommender systems. *Expert Systems with Applications*, 41(4), 2065–2073.
- **Li, L., Chu, W., Langford, J., & Schapire, R.E. (2010).** A Contextual-Bandit Approach to Personalized News Article Recommendation. *WWW 2010*.
- **Lattimore, T., & Szepesvári, C. (2020).** *Bandit Algorithms*. Cambridge University Press.
- **Aiyappa, R. et al. (2024).** Hierarchical Multi-Armed Bandits for the Concurrent Intelligent Tutoring of Concepts and Problems of Varying Difficulty Levels. arXiv: 2408.07208. URL: https://arxiv.org/html/2408.07208
- **Wikipedia.** Cold start (recommender systems). URL: https://en.wikipedia.org/wiki/Cold_start_(recommender_systems)
- **Wikipedia.** Multi-armed bandit. URL: https://en.wikipedia.org/wiki/Multi-armed_bandit

### Self-assessment, CEFR, psychométrie

- **Alderson, J.C. (2005).** *Diagnosing Foreign Language Proficiency: The Interface between Learning and Assessment*. Continuum.
- **Blanche, P., & Merino, B.J. (1989).** Self-assessment of foreign-language skills: Implications for teachers and researchers. *Language Learning*, 39(3), 313–340.
- **Ross, S. (1998).** Self-assessment in second language testing: a meta-analysis and analysis of experiential factors. *Language Testing*, 15(1), 1–20.
- **Luoma, S. (2004).** *Assessing Speaking*. Cambridge Language Assessment Series.
- **Council of Europe (2020).** *Common European Framework of Reference for Languages: Learning, Teaching, Assessment — Companion volume*. URL: https://rm.coe.int/common-european-framework-of-reference-for-languages-learning-teaching/16809ea0d4
- **DIALANG project.** URL: https://en.wikipedia.org/wiki/DIALANG
- **Council of Europe.** Self-assessment grid (CEFR Table 2). URL: https://www.coe.int/en/web/common-european-framework-reference-languages/table-2-cefr-3.3-common-reference-levels-self-assessment-grid
- **Embretson, S.E., & Reise, S.P. (2000).** *Item Response Theory for Psychologists*. Lawrence Erlbaum.
- **van der Linden, W.J., & Glas, C.A.W. (Eds.) (2010).** *Elements of Adaptive Testing*. Springer.

---

*Fin du rapport Vague 1. Vagues 2 (LLM tutors benchmark) et 3 (learner modeling longitudinal) à planifier.*
