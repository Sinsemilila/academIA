---
created: 2026-05-04
updated: 2026-05-05
type: plan
tags: [plan, architecture]
ai_summary: "Concept Coach Sportif (3e domaine, projet séparé d'AcademIA). Architecture 3-couches, profil_coaché, séquence V1.0→V1.5. Frontend + backend dédiés, LiteLLM mutualisé."
status: claude_draft
confidence: medium
sessions_validated: [60-prep-2026-05-04, 60-prep-2026-05-05]
last_reviewed_human: null
---

# Coach Sportif — concept exploratoire (3e domaine AcademIA)

> **Statut** : draft session 60-prep, **PAS** acté pour build. Reprise session future après décision sprint S60 (Wave 2 IT vs autre).
> **Users cibles** : Sinse (escalade + sports combat + muscu) + 1 ami (muscu + sports combat, pas d'escalade).
> **Sources de cette synthèse** : 3 agents dispatched (web research apps coach IA + frameworks training, web research bibliothèque canonique par discipline, vault-reader pattern Teacher/Maître Comptable réutilisable).

---

## 1. Positionnement archétypal

**3e archétype distinct**, pas Teacher bis ni Maître Comptable bis :

- **Teacher EN/ES** : oracle pédago Lyster + CEFR mesurable, baseline 18-19/26 ±1
- **Maître Comptable** : omniscient + tools déterministes (`verify_partie_double`, `lookup_pcg`) sur knowledge fermée canonique (PCG, règles compta françaises)
- **Coach Sportif** : *coach longitudinal adaptatif* — ce qui change cross-session = **le corps de l'apprenant dans le temps**, pas le contenu

**Conséquence design** : la valeur n'est PAS dans la générativité du conseil ponctuel (un random GPT te sort un programme PPL passable). Elle est dans :

1. Mémoire structurée cross-séances (event-stream, pas snapshots)
2. Modèle de fatigue cumulative cross-disciplines (concurrent training interference)
3. Anti-hallu sur détails techniques précis (où GPTCoach paper arxiv 2405.06061 confirme que LLMs explosent : OK generic, fail spécifique)

## 2. Profil Coaché (analogue profil_eleve)

Réutilisable de Teacher : table `profils_coache (athlete_id, domain)` + JSONB onboarding + `snapshots_session` checkpoints cross-session. Mais contenu diverge :

| profil_eleve (Teacher) | profil_coaché (Coach) |
|---|---|
| Niveau CEFR | Niveau par discipline (escalade : grade redpoint/onsight ; muscu : 1RM big lifts ; combat : années pratique + niveau compétition) |
| Erreurs récurrentes (codes Lyster) | Asymétries / faiblesses identifiées (ex : valgus genou squat, épaule droite limitante crochet, antagoniste poignet sous-développé escalade) |
| Objectifs apprentissage | Objectifs SMART datés ("voie 6c onsight août 2026", "deadlift 180kg fin 2026", "premier combat amateur boxe printemps 2027") |
| Préférences pédago | Contraintes pratiques (jours dispos, horaires, matos home/gym/salle escalade, durée max séance) |
| — | **Historique blessures + red flags** (CRITIQUE — hardcodé, pas négociable) |
| — | **Readiness J-1** (sleep, soreness, mood — questionnaire 30s, validé Saw 2016) |

**Différence d'échelle** : Teacher checkpoint conversationnel, Coach time-series performance. Journal de séance = event-stream (chaque set/rep/RPE/sensation), pas snapshot 10-turn.

## 3. Architecture knowledge — 3 couches superposées (recommandation)

Vault-reader disait "single mode adaptive sans tools" — **désaccord** : sport a énormément de calculs durs canonisés (RPE→%1RM, volume landmarks, ACWR, Wilks/DOTS) qui sont *exactement* le bon endroit pour sortir du LLM.

### Couche 1 — Authority Anchor RAG (citations obligatoires)

Bibliothèque canonique par discipline (cf. §7). Tout conseil technique cite source. Pas de source → flag *"opinion non-référencée"*. ADR-016 cross-lang authority anchor transposé.

### Couche 2 — Tools déterministes

- `compute_volume_landmark(muscle, training_history) → {MEV, MAV, MRV}` (Israetel Renaissance Periodization)
- `lookup_exercise(name) → {muscles_targeted, equipment, common_form_errors, contraindications}` (catalogue exo curé)
- `validate_program_safety(plan, profile) → flags` (ex : hangboard <2 ans pratique → BLOCK ; sparring lourd + heavy squat même semaine → WARN)
- `estimate_acwr(load_history) → ratio` (Gabbett 2016, >1.5 = injury risk spike documenté rugby/foot)
- `compute_finger_recovery(load_history) → hours_remaining` (escalade-spécifique)
- `validate_hangboard_eligibility(years_practice) → bool` (Anderson contre-indication <2 ans)

### Couche 3 — Mémoire longitudinale (event store + spaced retrieval)

Séances loggées en `journal_seance`. LLM y accède comme à un journal — pas de RAG sémantique floue, requêtes structurées (`SELECT exercises FROM sessions WHERE athlete='sinse' AND week>NOW-4`). Pattern detection cross-séances : *"3 séances tu mentionnes coude droit douloureux"*, *"plateau bench 4 sem → trigger deload programmé"*.

## 4. Pédagogie : Lyster transposé en cueing technique

Framework T1-T4 marche en coaching :

| Lyster langues | Équivalent coaching |
|---|---|
| Recast (T2) — modèle correct inline | Cue micro inline ("genoux dehors") |
| Elicitation (T3) — l'apprenant produit la correction | "Comment tu sens ton dos en bas du squat ?" |
| Clarification request (T1) | "Tu peux refaire en filmant côté ?" |
| Métalinguistique (T4) | "Ton genou rentre = valgus dynamique, l'abducteur lâche en fatigue, on va programmer du clamshell" |

Dosage analogue 4-item WM Cowan : **1-2 cues max par set**, pas 5. Anti-drift Pak 2025 transposé : **re-anchor forme tous les 5 reps** (vs 5 turns en convo).

## 5. Pistes design clés (issues recherche web)

### A. Concurrent training interference — LE problème central pour Sinse

Wilson 2012 méta-analyse : escalade + combat + muscu = 3 stimuli concurrents avec interférences documentées (force×endurance r=−0.29 à −0.75, hypertrophie×fréquence endurance r=−0.26 à −0.35).

Le coach IA doit **modéliser stimulus×fatigue par système** (finger flexors, CNS, aérobie, GPP) et **refuser** combinaisons toxiques :
- Hangboard mardi matin + boxe mardi soir + squat mercredi → CNS smash + fingers pas récupérés
- Recovery règle : finger flexors 48-72h, sparring lourd ≈ PR squat côté CNS
- 2 stimuli haute intensité max/jour, jamais 2 jours consécutifs même système

**C'est plus dur que coaching mono-discipline. Aucune app commerciale ne fait ça** (Fitbod, Boostcamp, KAYA sont mono-domaine).

### B. Readiness check matin (J-1) → composition séance dynamique

4 questions 30s (sleep / soreness / mood / charge subjective J-1) → score readiness → swap auto. Low score : heavy squat → mobilité ou technique escalade. Saw et al. 2016 : self-report > marqueurs objectifs pour load monitoring quotidien.

### C. Rétroplanification objectif sous contrainte canonique

*"Voie 6c en 3 mois"* → décomposition Anderson 12 sem (Base Fitness → Strength → Power → Power Endurance → Performance → Rest), milestones hebdo. LLM décompose mais sous contrainte programme canonique — ne pas inventer phases.

### D. Deload obligatoire non-négociable

Israetel : deload toutes 4-6 sem même si tu te sens bien. Hardcodé côté coach. User peut choisir *quel type* (volume cut vs intensity cut), pas opt-out.

### E. Scope refusal médical hardcodé

Douleur >3/10 persistante, dérobement, gonflement, paresthésie, douleur poitrine effort → STOP + redirige kiné/médecin. Pre-tool-use rule, pas négociable même si user insiste. Risque légal et éthique.

### F. Contre-indications par discipline

- Hangboard : <2 ans pratique escalade → BLOCK (tendinopathies poulies A2/A4 documentées)
- Heavy deadlift + lombalgie active → BLOCK
- Sparring contact lourd même semaine que combat amateur → WARN
- Muscu lourde MI <72h post-jiujitsu compétition → WARN

### G. Voice (STT/TTS) — DROPPÉ V1+

Sinse "vraiment pas fan". Pas de Whisper, pas de TTS. Output reste textuel. Input via UI tap-based (Hevy-style). Économie complexity + zéro débat prix.

## 6. Apps existantes pertinentes (état de l'art 2026)

Pattern dominant 2026 : **hybride structured plan + chat justification + readiness daily**. Pure-chat coaching (ChatGPT custom GPT fitness) considéré inférieur — programmes dérivent, pas de mémoire de charge.

| App | Pattern | Réutilisable ? |
|---|---|---|
| **Fitbod** | Algo regen workout 400M+ data, rotation muscle groups, gestion fatigue par muscle. Structured plan adaptatif J+1, pas de chat. Pas de générative. | Pattern adaptation J+1 oui |
| **Future** | Coach humain dédié + Apple Watch feedback. ~150€/mois. Pas IA générative. | Non (humain scale) |
| **Caliber** | Hybride AI programming + coach humain check-in. AI = day-to-day tracking, humain = strategic guidance. | Pattern hybride pertinent (Sinse = humain ici, IA = day-to-day) |
| **Freeletics** | AI motion analysis (MediaPipe BlazePose) pour form check. Bodyweight-centric. | Pas pour V1 (vision = scope creep) |
| **KAYA (escalade)** | Algo auto-sélectionne problèmes, traduit attempts/sends en 3 zones intensité. Logger augmenté + selection bias removal. | Pattern logger augmenté oui |
| **Hevy / Strong** | Loggers purs, zéro coaching. Référence UX input rapide post-séance (2-3 taps/set). | UX référence input |
| **Boostcamp** | Bibliothèque programmes coachs établis (Sheiko, nSuns, 5/3/1). "Curated programs". | Anti-hallu fallback : si AI hésite → canonical program |

## 7. Bibliothèque RAG — pré-tri par tier (V1 visé ~16-21 PDFs)

| Discipline | Tier 1 (must) | Tier 2 (nice) |
|---|---|---|
| **Escalade** | Anderson Rock Climber's Training Manual ; Hörst Training for Climbing 3rd ; MacLeod 9 out of 10 Climbers ; Eva López hangboard papers (PhD UPM Madrid) | Lattice research (blog/PDFs Tom Randall/Ollie Torr) ; Vigouroux FR (FFME) ; Steve House Training for the New Alpinism |
| **Muscu** | Schoenfeld Science and Development of Muscle Hypertrophy ; Helms Muscle and Strength Pyramid (Training+Nutrition) ; Israetel Scientific Principles Hypertrophy + Strength ; Rippetoe Starting Strength | Greg Nuckols MASS sélection ; Cometti FR (INSEP) |
| **Boxe** | Dempsey Championship Fighting (1950) ; Haislet Boxing (1940) ; USA Boxing Coaching Manual | Atlas bio (méthodo D'Amato) ; Sheridan Fighter's Mind |
| **BJJ** | Saulo Ribeiro Jiu-Jitsu University ; Renzo+Danaher Mastering Jiu-Jitsu ; Galvao Drill to Win | Gregoriades Black Belt Blueprint ; Derval FR |
| **MMA conditioning** | Joel Jamieson Ultimate MMA Conditioning | — (Jackson/Zahabi pas de livre canonique, doctrine orale) |
| **Récup / prévention** | McGill Back Mechanics + Ultimate Back Fitness ; Galpin Unplugged ; Starrett Becoming Supple Leopard | Renaissance Diet 2.0 ; Pavel Simple & Sinister ; Gabbett ACWR papers (BJSM) |

**Total visé V1 ≈ 16-21 PDFs**, ordre de grandeur Maître Comptable (22 PDFs). Faisable côté Qdrant (~10-15K chunks estimé) et OpenAI embeddings (qq € one-shot).

**Acquisition** : moitié dispo en grey area (library genesis), moitié achat physique/PDF officiel. Estimation budget achat propre : ~200-350€ pour les Tier 1. Compatible précédent "P0 books acquisition list" Session 51 (Profile Deutsch + Lyster + Lightbown ~250-300€).

**TODO next session** : Sinse cherche d'autres livres en plus si pertinents. Liste actuelle = base V1, pas figée.

## 8. Séquence V1.0 → V1.5 (acté session 60-prep)

**Décision (a)** : architecturer pour scope complet dès J1, ship en couches incrémentales (pattern Maître Comptable dual-mode A/B mais shipped Mode B en premier).

**Réordonnancement vs proposition initiale** (4 critiques actées) :

1. **Muscu first** au lieu d'escalade — 2 users dès V1.0 (toi + ami), terrain le plus structuré, tools déterministes Israetel utilisables immédiatement
2. **Q&A omniscient en V1.0** avant journal — pattern Maître Comptable validé, value rapide, lowest stakes
3. **Backbone (journal + readiness) en V1.1** au lieu V1.4 — tout le reste en dépend
4. **Cross-domain interference en V1.5** logique (besoin ≥2 disciplines pour modéliser)

| Version | Scope | Users | Durée | Value testable |
|---|---|---|---|---|
| **V1.0** Q&A omniscient muscu | Coach chat-only + RAG muscu Tier 1 (Schoenfeld, Helms, Israetel, Rippetoe) + authority anchor citations + 2 profils minimaux | toi + ami | 4-6 sem | "20 Q test cross-user, both actives, citations live" |
| **V1.1** Journal + tools muscu | PG `journal_seance` event-stream + UI tap-input + tools `compute_volume_landmark` / `estimate_acwr` / `lookup_exercise` + readiness check J-1 + pattern detection (plateau, deload trigger) | toi + ami | 4-6 sem | "10 séances loggées, deload triggered automatiquement" |
| **V1.2** Programmation proactive muscu | Coach génère plan hebdo (profil + objectif + readiness) + Authority Anchor sur structure programme + deload forcé hardcodé | toi + ami | 4-6 sem | "Plan tenable 4 sem, adjustments weekly" |
| **V1.3** Escalade ajoutée | RAG escalade Tier 1 (Anderson, Hörst, MacLeod, López) + tools spécifiques (`validate_hangboard_eligibility`, `compute_finger_recovery`) + extension schema journal (grades, voies, redpoint/onsight) | toi seul | 4-6 sem | "Hangboard refusé si <2 ans pratique, recovery fingers respectée" |
| **V1.4** Combat ajouté | RAG combat Tier 1 (Dempsey, Haislet, Ribeiro, Danaher, Jamieson) + extension schema (rounds, sparring intensity, technique/conditioning split) | toi + ami | 4-6 sem | "Programmation sparring + S&C insertion concurrent" |
| **V1.5** Cross-domain interference | Modèle stimulus×fatigue par système (CNS, finger flexors, aérobie, GPP) + refus combinaisons toxiques + Wilson 2012 concurrent penalty + périodisation cross-domaine | toi (3 disciplines) + ami (2) | 4-6 sem | "Refuse hangboard mardi + boxe mardi soir + squat mercredi" |

**Total ≈ 24-36 semaines = 6-9 mois**, sprints 4-6 sem (cohérent rythme actuel Wave 2/3/4 langues).

**Risques actés** :
- Tu fais l'escalade aussi, V1.3 = tu attends 12-18 sem avant que ton sport principal soit couvert. Acceptable selon Sinse session 60-prep.
- V1.0 Q&A pur = pas encore d'utilité quotidienne, juste référence — risque désengagement avant V1.1 si usage perçu faible
- Schema PG dès V1.1 doit anticiper extensions V1.3/V1.4 (escalade grades, combat rounds) → design upfront pour éviter migration painful

## 9. Décisions actées session 60-prep

1. **3e domaine** : Coach Sportif acté comme concept (projet séparé, plus 3e module AcademIA — cf D7). PAS encore programmé sprint (priorité S60 decision pending d'abord).
2. **Architecture (a)** : scope complet J1 + ship couches incrémentales.
3. ~~**Frontend** : SvelteKit AcademIA actuel suffit (mobile via web). PWA installable possible V2 si besoin offline-first.~~ **SUPERSEDED 2026-05-05 par D7.**
4. **Voice DROPPED V1+** : pas STT, pas TTS. Sinse "vraiment pas fan".
5. **Bibliothèque RAG** : ~16-21 PDFs cible V1, pré-tri Tier 1 acté. Sinse cherche compléments next session.
6. **Séquence V1.0→V1.5** : muscu first, Q&A avant journal, second user dès V1.0, escalade V1.3, combat V1.4, interference V1.5.
7. **Projet séparé d'AcademIA (acté 2026-05-05)** : frontend ET backend dédiés.
   - **Frontend dédié** : nouveau repo `/opt/coach` (nom à figer), mobile-first, paradigmes UX disjoints d'AcademIA (tap-input post-séance Hevy-style, readiness 4 questions matin, calendrier programme hebdo, graphs progression 1RM/grades, timer repos). PWA installable. Stack à choisir (SvelteKit reuse OK, ou expé Svelte 5 fresh).
   - **Backend dédié** : nouveau service `coach-api` (FastAPI). Modèles de données disjoints (`profils_coache`, `journal_seance`, tools coaching `compute_volume_landmark`/`estimate_acwr`/`validate_hangboard_eligibility`/...). Pas de couplage avec `academie-api`.
   - **LiteLLM mutualisé** : seul point partagé infra. Rationale Sinse — clés API (OpenAI, Gemini, Anthropic) pas infinies, mutualiser proxy évite duplication crédits + leverage LiteLLM virtual keys / budgets / rate limits par projet. Cosmos LiteLLM existant suffit.
   - **Auth** : à trancher next session — Cosmos Zero Trust email policy partagée OU comptes séparés. Reuse Cosmos = simple + cohérent (tu = mariejuanes / compte coach même bucket SSO). Probable reuse.
   - **DB** : Postgres dédié (`postgres-coach`) ou schema séparé dans `postgres-academie` ? Schema séparé = simpler ops, isolation logique suffit early. À trancher V1.1 quand journal arrive.
   - **Qdrant** : collection dédiée (`coach_books_v1`) sur le Qdrant cosmos existant. Pas besoin instance séparée.
   - **Conséquence sur §10 Q4** : question "frontend route `/coach` chat-like" → obsolète, projet séparé.

## 10. Questions ouvertes pour next session

1. **Quand démarrer V1.0** ? Après sprint S60 + Wave 2 IT (=~2-3 mois delay) ou en parallèle (split focus risqué) ?
2. **Sprint 4-6 sem** OK rythme ou ajuster vu transition PTP déc 2026 ?
3. **Acquisition livres Tier 1** : Sinse veut compléter liste (chercher d'autres références) avant de figer la base V1.
4. ~~**Frontend route** : `/coach` chat-like analogue `/maitre-comptable` ? Ou refondre nav AcademIA pour exposer 3 domaines (Teacher / Maître Comptable / Coach) en first-class navigation ?~~ **RÉSOLU D7 2026-05-05** : projet séparé `/opt/coach`, frontend + backend dédiés, LiteLLM mutualisé.

7. **Auth Cosmos** : reuse SSO Cosmos Zero Trust (un seul email policy étendu) ou comptes séparés ? Reco reuse pour simplicité, mais si distribution future hors cercle ami → impact.
8. **Postgres** : schema séparé dans `postgres-academie` (ops simpler) ou container `postgres-coach` dédié (isolation forte) ? Trancher V1.1 quand journal arrive.
9. **Stack frontend coach** : reuse SvelteKit (familier, lib composants AcademIA partiellement réutilisable) ou expé Svelte 5 / Solid / autre ? À évaluer balance vélocité vs apprentissage stack neuve.
10. **Repo nom** : `/opt/coach` ou `/opt/coach-sportif` ou autre (placeholder branding) ?
5. **Modèle LLM par couche** : gpt-4o-mini suffisant Q&A coach (cf. Maître Comptable agent_compta) ou besoin Sonnet pour nuance pédago Lyster transposée ?
6. **Multi-user data model** : reuse pattern Marie/Sinse compte AcademIA actuel (CF Zero Trust email policy) ou besoin schema dédié athletes ?

---

**Reprise** : prochaine session après S60 decision actée. Charger ce doc + ouvrir question §10 #1 (timing V1.0 start).
