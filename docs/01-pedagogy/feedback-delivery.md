---
title: Pédagogie de la délivrance du feedback
status: authoritative
last_reviewed: 2026-04-15
---

# Pédagogie de la délivrance du feedback

> Le scoring dit **quel tier** pour quelle erreur. Ce document dit **comment** le feedback est effectivement délivré à l'apprenant pour maximiser l'apprentissage.

## Mapping tier → type de feedback (Lyster & Ranta 1997)

| Tier | Type Lyster | Exemple phrasing (EN Teacher) |
|---|---|---|
| **T0** `pre_acquisition` | — | invisible (non-erreur à ce niveau) |
| **T1** `ignored` | — | invisible (journalisé pour stats) |
| **T2** `noted` | **recast implicite** | Élève: "I go yesterday to Paris" → Teacher: "Right, *I went* to Paris — and what did you do there?" |
| **T3** `penalized` | **elicitation OR metalinguistic** | Élève: "I go yesterday" → Teacher: "Almost — what's the past form of *go*?" |
| **T4** `regressive` | **prompt + metalinguistic + remédiation** | Élève (C1): "I go yesterday" → Teacher: "Watch the tense — past simple because the action is finished. Try again, then we'll revise this pattern tomorrow." |

**Rationale** :
- Recast (T2) : léger, ne demande pas de reformulation, préserve la fluency du dialogue
- Elicitation / Metalinguistic (T3) : force le **noticing the gap** (Swain output hypothesis), produit plus d'uptake que les recasts (Lyster & Saito 2010, d = 1.16 vs 0.71)
- Prompt + remédiation (T4) : erreur sur structure censée acquise → flag pour revisiting ultérieur + correction explicite

## Principes Hattie & Timperley — 4 niveaux de feedback

1. **Task** : "This verb form doesn't match past tense" ← **à privilégier**
2. **Process** : "Watch the auxiliary in past questions" ← **à privilégier**
3. **Self-regulation** : "You tend to drop articles — focus on them this week" ← bon en C1+
4. **Self** : "You're so smart!" ← **BANNI**

> d moyen feedback efficient = 0.79 (Hattie 2007).
> Praise d'intelligence → évitement de la difficulté (Mueller & Dweck 1998). Banni.

## Dosage par niveau (Sweller + Cowan)

**Working memory ≈ 4 items** (Cowan 2001). Ne jamais dépasser ~3-4 corrections visibles simultanément.

| Niveau | Corrections/tour max | Total/session 15 min | Type dominant |
|---|---|---|---|
| A1 | 1-2 | 5-8 | ≥ 80% recasts (T2) |
| A2 | 2-3 | 10-15 | 50/50 recast/prompt, 1 structure cible |
| B1 | 3-4 | 15-20 | prompts dominants, 1-2 structures cibles |
| B2 | 3-5 | 20-25 | prompts + metalinguistic bienvenu |
| C1-C2 | 5+ | 25-35 | metalinguistic + pushed output + nuances stylistiques |

**Ces quotas sont une extrapolation** de Cowan + Sweller + Lyster, **pas** une étude L2 dédiée. À valider empiriquement (A/B tests internes).

## Timing du feedback

| Tier | Timing | Placement UI |
|---|---|---|
| T1 ignored | — | journal |
| T2 noted | inline discret | tooltip ou fond léger, bottom-of-screen |
| T3 penalized | immédiat | inline prominent + prompt |
| T4 regressive | immédiat + récap fin de session | inline + "on reviendra dessus demain" |
| Patterns multi-tours | end-of-session récap | "Aujourd'hui tu as bien géré le passé simple. Deux points à surveiller : articles et since/for." |
| Erreurs récurrentes | **spaced retrieval J+1 / J+3 / J+7** | micro-quiz début session suivante |

Intervalles spaced retrieval basés sur **Cepeda (2006)** (distributed practice, spacing ≈ 10-20% du retention interval). **Pas** de source L2 dédiée — extrapolation.

## Focused > unfocused (Sheen & Ellis 2011)

**Règle** : 1-2 structures cibles par session seulement. Les autres erreurs :
- T2 restent inline (non-invasif)
- T3/T4 entrent dans la pile `spaced_retrieval` (revisite ultérieure, pas corrigées cette session)

Rationale : Truscott (1996) — sur-correction écrite ne produit pas de gain, **peut nuire**. Focused > unfocused confirmé par Sheen & Ellis.

## Anti-drift (Pak et al. 2025)

Les LLMs prompted avec contrainte CECRL **dérivent après 5-9 tours de dialogue**. Le Teacher commence à parler B2 à un A1.

**Mitigation** :
- Re-injection du level + rubric dans le system prompt toutes les **5 interactions**
- Validation automatique toutes les 10 interactions : le dernier message Teacher est-il conforme au niveau ? Si non → warning + correctif
- Snapshot toutes les 10 interactions (existe déjà) → inclut une **mesure de drift** (niveau estimé par LLM vs niveau attendu)

## Phrasings concrets — templates Teacher par tier

### T2 `noted` — recast léger

```
FR: "Ah oui, *j'ai mangé* une pomme. Et toi, tu as mangé quelque-chose ?"
EN: "Right, *I went* to Paris — and what did you do there?"
ES: "Claro, *fui* al cine — ¿y qué viste?"
```

Propriétés : (1) corrige implicitement, (2) continue la conversation sans pause correctrice, (3) aucune charge cognitive supplémentaire.

### T3 `penalized` — elicitation

```
FR: "Presque ! Quelle est la forme passée de *go* ?"
EN: "Almost — what's the past form of *go*?"
ES: "Casi — ¿cuál es el pasado de *ir*?"
```

Propriétés : (1) identifie l'erreur implicitement, (2) exige pushed output (Swain), (3) noticing du gap clair.

### T3 `penalized` — metalinguistic (B1+)

```
EN: "Watch the tense there. When the action is finished, past simple — not present simple. Try again?"
```

Propriétés : (1) explicite la règle, (2) demande reformulation, (3) vocabulaire metalinguistic active self-regulation.

### T4 `regressive` — prompt + remédiation

```
EN: "That tense surprised me at your level. Past simple because the action is finished. We'll revisit this pattern tomorrow — I'm adding it to your review list."
```

Propriétés : (1) signal que c'est anormal, (2) correction explicite, (3) déclencheur de spaced retrieval.

### End-of-session récap

```
"Bonne session ! Points forts aujourd'hui : past simple solide, articles propres.
 À surveiller demain : since / for (tu as hésité 3 fois), et la place de l'adverbe ('usually').
 On reprend ces deux points demain matin."
```

Propriétés : (1) positive first (Hattie), (2) process-level (pas self), (3) priorisation sur 2 points max, (4) inscription dans le temps.

## Anti-patterns à proscrire

1. **Sur-correction globale** (Truscott) — corriger tout en A1 détruit motivation et progression
2. **Praise d'intelligence** (Mueller & Dweck) — "You're so good!" diminue persistance face à la difficulté
3. **Feedback sandwich rigide** (Henley & DiGennaro Reed 2015) — pas d'évidence, perçu comme artificiel
4. **Pushed output sur apprenant saturé A1** — viole CLT, augmente anxiety
5. **Leaderboard compétitif visible** (Koivisto & Hamari 2019) — démotive low performers
6. **Correction immédiate pendant un flow communicatif** fluide — casse le contexte sans gain
7. **Penaliser un U-shape regression** — surgénéralisation après apprentissage = signe de progrès

## Personnalisation

### Par L1
- Francophone → anticiper prepositions, articles, faux amis (plus de patience sur ces familles)
- Sinophone → anticiper articles (absents en mandarin), plurals, tense morphology
- Japonophone → anticiper articles, tense, ordre SVO

Source : Odlin (1989), Jarvis & Pavlenko (2008). Pas de matrice standard → **calibrer empiriquement** par paire L1→L2.

### Par profil personnel
Utiliser `profils_eleves.personnalite` existant :
- `centres_interet` → choisir des exemples qui parlent à l'élève (musique, voyages, cinéma…)
- `style_correction` → modérer le ratio explicit/implicit selon préférence user

## Gaps de littérature à documenter honnêtement

- Pas de RCT solide sur **LLM feedback × CEFR levels** en dialogue multi-tours
- Intervalles spaced retrieval optimaux pour **erreurs grammaticales productives** L2 : pas établis (Cepeda concerne vocab/faits)
- Quotas de corrections/minute : pas de source L2 dédiée, extrapolation CLT
- Efficacité comparative LLM-recast vs LLM-prompt : pas mesurée sur données L2 réelles

**À mesurer chez nous** via A/B tests internes (cf. Dimension 8 Observability à définir).

## Références

- [bibliography.md](bibliography.md) — Lyster, Swain, Hattie, Sweller, Cowan, Mueller & Dweck, Pak, Cepeda, etc.
- [taxonomy-framework.md](taxonomy-framework.md) — interface `FeedbackHint`
- [cefr-language-instance.md](cefr-language-instance.md) — instanciation langues
- [ADR-003](../05-decisions/ADR-003-5-tiers-taxonomy.md) — 5 tiers
- Code futur : `academie-core/pedagogy/feedback.py`, `academie-core/pedagogy/dosage.py`
