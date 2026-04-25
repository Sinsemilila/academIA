---
title: Glossaire AcademIA
status: authoritative
last_reviewed: 2026-04-19
---

# Glossaire AcademIA

## Pédagogie

**CECRL / CEFR** — Cadre Européen Commun de Référence pour les Langues. 6 niveaux : A1 (débutant absolu) → A2 → B1 → B2 → C1 → C2 (maîtrise native). Source : Conseil de l'Europe, [Companion Volume 2020](https://www.coe.int/en/web/common-european-framework-reference-languages). Utilisé par AcademIA pour EN/ES/IT/DE (domaines européens).

**JLPT** (Japanese Language Proficiency Test) — système de niveau officiel japonais, standard de facto mondial pour l'apprentissage du JP. 5 niveaux : N5 (débutant) → N4 → N3 → N2 → N1 (avancé). Géré par Japan Foundation + Japan Educational Exchanges and Services (JEES). Mapping CEFR officiel : N5≈A1, N4≈A2, N3≈B1, N2≈B2, N1≈C1. Utilisé par AcademIA pour domaine Sensei (pivot Session 29).

**TORFL / ТРКИ** (Test of Russian as a Foreign Language / Тест по русскому языку как иностранному) — système de niveau officiel russe, Ministère de l'éducation de la Fédération de Russie (Gosstandart ТРКИ). 6 niveaux : TEU (Элементарный) ≈ A1, TBU (Базовый) ≈ A2, TORFL-I ≈ B1, TORFL-II ≈ B2, TORFL-III ≈ C1, TORFL-IV ≈ C2. Utilisé par AcademIA pour domaine Maestro-RU (pivot Session 29).

**Mapping natif↔CEFR** — AcademIA conserve un storage interne unifié en CEFR a1-c2 (analytics cross-lang comparables) avec un module `academie_core/levels.py` qui mappe JLPT et TORFL↔CEFR aux bornes UI/prompts. Chaque domaine déclare son système via `LEVEL_SYSTEM_BY_DOMAIN`. JP voit N5-N1, RU voit TEU-IV, autres voient A1-C2.

**Profile Deutsch** (Glaboniat et al., éd. Langenscheidt/Hueber) — référentiel officiel CECRL pour l'allemand A1-C1, ~13K exposants lexicaux + inventaire grammaire + actes de parole + notions. Équivalent allemand de l'English Grammar Profile (Cambridge). Publication commerciale ~40€, acquis par Sinse pour domaine Lehrer.

**Gosstandart ТРКИ** — organisme officiel russe qui publie les standards TORFL (descriptors par niveau, Lexical Minimum, Grammatical Minimum). Ressources open utilisées par AcademIA pour rubrics Maestro-RU.

**Japan Foundation JF Standard** — référentiel officiel japonais aligné JLPT, ressource open utilisée par AcademIA pour rubrics Sensei. Voir jfstandard.jp.

**Proficiency scale** — échelle de maîtrise d'un domaine. CECRL pour langues européennes ; JLPT pour JP ; TORFL pour RU ; Bloom / NICE / custom pour autres domaines. Abstraite dans `academie-core`.

**Tier** — niveau de gravité d'une erreur pour un apprenant à un niveau donné. 5 tiers : T0 `pre_acquisition` / T1 `ignored` / T2 `noted` / T3 `penalized` / T4 `regressive` (cf. ADR-003).

**Error family** — regroupement de codes d'erreur par type grammatical/pédagogique. Aujourd'hui 12 familles pour les langues : verb_tense, verb_usage, noun_det, pronoun, word_order, sentence, morphology, surface, preposition, vocabulary, calque, discourse.

**Error code** — identifiant atomique d'un type d'erreur. Ex : `V:TENSE`, `LEX:CALQUE`, `N:COUNT`. 57 codes actuels.

**Criterial feature** — structure grammaticale qui émerge à un niveau CECRL précis (concept clé du Cambridge English Profile — Hawkins & Filipović 2012).

**Gravity axes (James 1998)** — 3 dimensions de sévérité d'une erreur :
- `linguistic` — violation de règle brute
- `communicative` — impact sur compréhension (Burt-Kiparsky global vs local)
- `social_pragmatic` — irritation native, registre, appropriation

**Mistake vs Error (Corder 1967)** — mistake = slip de performance (structure acquise, raté ponctuel) ; error = lacune de compétence (structure pas encore acquise).

**Teachability Hypothesis (Pienemann)** — une structure ne peut être enseignée que si le stade développemental antérieur est acquis. Impossible de forcer une structure hors séquence.

**U-shaped learning** — pattern régressif apparent lors de l'acquisition d'une règle (ex : *went* correct rote → *goed* surgénéralisation → *went* correct règle).

**Affective filter (Krashen)** — niveau d'anxiété/motivation qui bloque l'intake. Sur-correction augmente le filtre, bloque l'apprentissage.

**ZPD (Vygotsky)** — Zone of Proximal Development. Structure au niveau n+ε, apprenable avec aide/scaffolding.

**Lyster feedback types** — 6 types de feedback correctif : recast, explicit correction, clarification request, metalinguistic, elicitation, repetition. Prompts (4 derniers) plus efficaces que recasts pour erreurs traitables.

**L1 / L2** — L1 = langue maternelle, L2 = langue cible.

**L1 transfer** — influence de la L1 sur L2, produit des erreurs prédictibles (ex : francophone → articles, prépositions, faux amis).

## Système AcademIA

**Agent** — instance d'interaction pédagogique. Teacher (EN), Maestro (ES), Sensei (JP), Lehrer (DE), Professore (IT), PyMentor, CyberMentor…

**Domain** — famille pédagogique : `LanguageDomain`, `CodeDomain`, `CyberSecDomain`. Chaque Domain implémente l'interface abstraite dans `academie-core`.

**Chatflow** — workflow Dify (28 nodes, 45 edges pour Teacher) qui orchestre l'interaction LLM.

**Snapshot** — JSONB sérialisé de l'état pédagogique d'un user à un instant t. Généré toutes les 10 interactions. Contient scores_confiance, points_forts, lacunes, derniere_session, personnalite, tolerance_matrix, etc.

**Diagnostic** — test CECRL initial de niveau (5-7 questions), produit par n8n workflow, persiste dans `profils_eleves`.

**Tolerance matrix** — table YAML/DB indexée `(famille_erreur, bande_CECRL)` → tier. Cœur de la gradation d'erreur.

**L1 transfer multipliers** — table `(L1, L2, family)` → float, ajuste la tolérance selon la paire linguistique.

**Rules layer** — détection d'erreurs par règles Python déterministes (98% coverage A1-C1). Complément/garde-fou du LLM.

**Error log** — table `error_log` en PostgreSQL, journal de toutes les erreurs détectées.

**scores_confiance** — JSONB dans `profils_eleves`, {concept_key: score 0-100} de maîtrise perçue par concept.

## Infra & techniques

**LiteLLM** — proxy OpenAI-compatible qui route les appels LLM, gère le load-balancing, fallback, spend logs. Seul gateway LLM du système (cf. ADR-006).

**Dify** — plateforme visuelle de chatflows LLM. Héberge les workflows Teacher, futurs agents.

**n8n** — orchestrateur de workflows. Gère les 3 webhooks (profil-get, snapshot, profil-update + diagnostic + exam-scoring).

**cosmos** — VM Proxmox Debian qui héberge toute l'infra (Docker Compose, PostgreSQL, Redis, LiteLLM, Dify, n8n, webapp SvelteKit/FastAPI).

**BYOK** — Bring Your Own Key. Stratégie de pool familial de clés API (OpenAI / Groq / Mistral) gérée par LiteLLM (cf. ADR-006).

**ADR** — Architecture Decision Record. Un fichier par décision architecturale structurante, immutable (supersedes en cas de remplacement). Dans `docs/05-decisions/`.

## Math/ML (pour calibration future)

**IRT** — Item Response Theory. Psychométrie qui estime une ability θ latente par élève et une difficulté b par item. 1PL/2PL/3PL/GRM selon granularité.

**GRM (Graded Response Model, Samejima 1969)** — IRT pour réponses ordinales (nos 5 tiers).

**BKT (Bayesian Knowledge Tracing)** — HMM binaire qui estime p(maîtrise) par concept × élève.

**PFA (Performance Factors Analysis)** — régression logistique alternative à BKT avec features riches.

**DKT / AKT / SAINT** — Deep Knowledge Tracing (LSTM/Transformer). SOTA mais requiert >500k interactions.

**FSRS** — Free Spaced Repetition Scheduler. Meilleur algo open source de spaced repetition (2024).

**HLR (Half-Life Regression)** — algo Duolingo de spaced repetition (Settles & Meeder 2016).

**CAT** — Computerized Adaptive Testing. Choix adaptatif de l'item suivant via maximisation Fisher information.

**GLMM** — Generalized Linear Mixed Model. Utilisé pour calibrer empiriquement les seuils de tiers à partir de données réelles.

**Cox PH** — Cox proportional hazards. Survival analysis, utilisé pour half-life d'erreur par famille × niveau.

**ERRANT** — ERRor ANnotation Toolkit (Bryant 2019), standard NLP pour annotation d'erreurs GEC.

**EGP / EVP** — English Grammar Profile / English Vocabulary Profile (Cambridge). 1222+ criterial features / 7000 words × CECRL level.

## Acronymes récurrents

- **SLA** — Second Language Acquisition
- **GEC** — Grammatical Error Correction
- **CAT** — Computerized Adaptive Testing
- **AES** — Automated Essay Scoring
- **CLT** — Cognitive Load Theory (Sweller)
- **CLC** — Cambridge Learner Corpus
- **PCIC** — Plan Curricular del Instituto Cervantes
- **NICE** — National Initiative for Cybersecurity Education (framework compétences cybersec)
