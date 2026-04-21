# Politique de consolidation CEFR — QCM provisoire → niveau validé

**Statut** : livré Session 36 (2026-04-21) — MVP code + UI
**Scope** : tous les tuteurs langues (Teacher EN, Maestro ES ; extensibles IT/DE/JP/RU)

---

## 1. Rationale

Le QCM post-onboarding fournit un `cefr_placement` **auto-déclaré ± probe discriminant** : rapide, mais sujet à Dunning-Kruger. La littérature (Ross 1998 — *Language Testing* ; Blanche & Merino 1989) rapporte une corrélation auto-évaluation ↔ test objectif de **0.3–0.5** (faible-moyenne). Overclaim dominant aux transitions B1↔B2 (learners motivés surestiment leur production). Underclaim aux A2 (bases solides mais FLA empêche reconnaissance).

Sans mécanisme de consolidation, l'apprenant·e peut rester des semaines avec un rubric erroné (tolerance matrix, fewshots, dosage calibrés sur le mauvais niveau). **Objectif** : après **N=8 turns OR 20 error_log entries** (first hit), engager un process transparent et bienveillant qui :
1. valide le niveau si OBS == QCM,
2. déclenche un mini-exam 8 items si OBS ≠ QCM,
3. présente le résultat avec wording de prof chaleureux et **laisse le choix final à l'apprenant·e** (agency OLM Bull & Kay 2016).

## 2. Les 8 décisions approuvées (Session 35)

| # | Paramètre | Valeur |
|---|---|---|
| 1 | N turns trigger | 8 turns OR 20 error_log entries (whichever first) |
| 2 | Sources OBS | LLM `observed_level` hint (majority vote) + distribution `error_log.criterial_level_emergence` |
| 3 | Mini-exam | 8 items fixes ciblés niveau suspecté, YAML bank par lang×level |
| 4 | Refus changement | Soft re-prompt après +20 turns + badge "stabilisation volontaire" |
| 5 | Granularité | 1 badge global MVP ; split compréhension/production Phase 2 |
| 6 | Écart >1 CEFR | Max +1/-1 par épisode (anti-whiplash) |
| 7 | Re-calibrer après dormance | 30j inactivité + régression sur 5 turns → mini-exam |
| 8 | Schema | `niveau_status` + `niveau_validated_at` + `consolidation_decision_pending` sur `profils_eleves` |

## 3. Matrice d'états `niveau_status`

| État | Signification | Transitions |
|---|---|---|
| `provisoire` | Défaut post-QCM, avant N turns | → `calibration_en_cours` si OBS≠QCM ; → `validé` si OBS==QCM |
| `calibration_en_cours` | Mini-exam déclenché ou decision pending | → `validé` (accept_new ou auto_validate) ; → `stabilisation_volontaire` (stay_current) |
| `validé` | Niveau confirmé par obs ou user | → `a_recalibrer` si 30j+régression |
| `stabilisation_volontaire` | User a refusé le changement proposé | → re-éval après +20 turns |
| `a_recalibrer` | Régression détectée après dormance | → `calibration_en_cours` (mini-exam relancé) |

## 4. Textes bienveillants (prof Alliance Française)

Rendus via `academie_core.pedagogy.consolidation.pick_message()`.

### Validation (OBS == QCM)
> Après ces {N} échanges, j'ai pu confirmer ton niveau {X}. Tes auto-évaluations étaient justes — bravo pour cette lucidité, c'est un vrai atout d'apprenant·e. Ton badge passe de *provisoire* à *validé*. On continue sur cette lancée.

### Upgrade (OBS > QCM + mini-exam passed)
> J'ai observé tes productions sur les {N} derniers échanges et, après ce petit test de consolidation, je constate que tu manies déjà les structures du niveau {X+1}. Félicitations, tu as progressé plus vite que tu ne le pensais ! Deux options s'offrent à toi : on passe officiellement en {X+1} et on attaque les objectifs de ce niveau, ou on reste un peu en {X} pour consolider certaines bases avant de monter. Qu'est-ce qui te semble le plus juste ?

### Downgrade (OBS < QCM + mini-exam failed at QCM level)
> J'ai observé tes productions sur les {N} derniers échanges et j'ai remarqué que certaines structures du niveau {X} ne sont pas encore totalement acquises — c'est tout à fait normal, la progression n'est jamais linéaire. Je te propose deux options : soit on repart sur {X-1} pour renforcer ces fondations avant de remonter (mon conseil, mais c'est toi qui décides), soit on continue en {X} et on travaille les points faibles au fil de l'eau. Qu'est-ce que tu préfères ?

## 5. Architecture

```
chat_router.chat_send()  (per turn)
├─ parse TeacherResponse → extract observed_level (new field)
├─ append to user_sessions.observations_json (jsonb array)
├─ _update_session() → message_count++
└─ _consolidation_post_turn()     [flag-gated CONSOLIDATION_ENABLED]
   ├─ evaluate_trigger(message_count, error_log_count, niveau_status, ...)
   ├─ IF trigger :
   │   ├─ decide_consolidation(qcm_level, hints, error_dist, ...)
   │   │   ├─ reconcile(obs_llm, obs_errors) → conservative consensus
   │   │   ├─ clamp_single_step(qcm, observed)  # anti-whiplash
   │   │   └─ outcome : auto_validate | propose_mini_exam | noop
   │   ├─ IF auto_validate :
   │   │   UPDATE profils_eleves SET niveau_status='validé', niveau_validated_at=NOW()
   │   │   INSERT consolidation_events (auto_validate)
   │   └─ IF propose_mini_exam :
   │       UPDATE profils_eleves SET niveau_status='calibration_en_cours',
   │                             consolidation_decision_pending=<snapshot>
   │       INSERT consolidation_events (pending)

Frontend (chat page mount + dashboard poll)
├─ fetch /api/consolidation/state/{domain}
├─ IF niveau_status='calibration_en_cours' AND pending.awaiting_user=false :
│   open MiniExamModal → POST /mini-exam/start → render items → submit
├─ IF mini-exam returns outcome='awaiting_user_decision' :
│   open ConsolidationDecisionModal (upgrade or downgrade)
├─ user clicks [accept_new] | [stay_current] :
│   POST /consolidation/decide → status = validé | stabilisation_volontaire
```

## 6. Mini-exam

### Structure (8 items)
- 3 fill-in-the-blank
- 2 transform (grammatical)
- 2 choice (multiple choice)
- 1 produce_short (free production, LLM-judged)

Durée cible 5-7 min. Pass threshold **≥6/8 (0.75)**.

### YAML banks livrés (MVP)
- `data/mini_exam/es_{A1,A2,B1}.yaml`
- `data/mini_exam/en_{A1,A2,B1}.yaml`

Phase 2 : compléter B2/C1 + IT/DE/JP/RU.

### Scoring
1. Exact regex match (`expected_regex`) → 1 point.
2. Fallback LLM judge (`llm_judge_hint` + gpt-4.1-mini, PASS/FAIL binary) pour paraphrases et `produce_short`.
3. Total /8, pass si ≥6.

### Décision post-scoring
| Scoring | Action |
|---|---|
| ≥6/8 (passed) + observed > QCM | Modal MSG_UPGRADE avec 2 boutons |
| ≥6/8 (passed) + observed < QCM | Modal MSG_DOWNGRADE avec 2 boutons |
| <6/8 (failed) | Auto-validate QCM (l'obs ne s'est pas confirmée), MSG_VALIDATION |

## 7. Kill switch et rollback

- Env var `CONSOLIDATION_ENABLED=true` (défaut).
- `false` → `_consolidation_post_turn` no-op, endpoints 503, modals ne s'ouvrent pas (dashboard reste au flag `provisional` legacy).
- Migration idempotente (`ADD COLUMN IF NOT EXISTS`) → rollback = set env false, pas de DROP nécessaire.
- Table `consolidation_events` permet audit ex-post (quoi décidé, quand, pourquoi).

## 8. Signaux d'observation

### LLM `observed_level` (TeacherResponse)
Nouveau champ JSON, optionnel. L'LLM évalue le niveau CEFR apparent de l'apprenant·e à partir de turn 4+ (évite noise initial). Vide `""` si incertain. Collecté dans `user_sessions.observations_json[]`.

### error_log distribution
On agrège `criterial_level_emergence` (tagué par `enrich_error_fields()`) sur tous les `error_log` du learner+domain. Niveau dominant = niveau où ≥50% des erreurs émergent (heuristique "où le learner galère encore").

### Réconciliation
- Si les 2 sources agreent → consensus.
- Si disagree → **conservative** : garde le plus bas (évite de déclarer le learner plus haut qu'il ne l'est démontrablement).
- Si une source vide → prend l'autre.
- Si les 2 vides → noop (pas de signal, attendre plus de turns).

## 9. Données persistées

### `profils_eleves` (colonnes nouvelles)
- `niveau_status` : enum 5-valued (voir §3)
- `niveau_validated_at` : timestamp de bascule vers validé
- `last_consolidation_turn` : throttling (cooldown 10 turns)
- `consolidation_decision_pending` : JSONB snapshot de la decision en attente user
- `regression_watch_active` + `regression_watch_started_turn` : post-dormance

### `user_sessions.observations_json` (JSONB)
Array de `{turn, observed_level, ts}` — capped à N*3 entrées récentes.

### `consolidation_events` (table nouvelle)
Audit trail : trigger_reason, qcm_level, observed_level, mini_exam_triggered, mini_exam_score_pct, user_decision, final_level, notes.

## 10. Open questions / Phase 2

- **Granularité compréhension vs production** : QCM capture déjà split (`cefr_comprehension`, `cefr_production`). Consolider asymétriquement possible mais UI x2.
- **Adaptive IRT-light mini-exam** : actuellement fixe ; pourrait démarrer au QCM level et ajuster selon réponses (Samejima GRM).
- **Banks manquants** : B2/C1 en ES/EN, puis toutes les langues.
- **Dormance regression watch** : colonnes ajoutées, logique trigger présente, mais **évaluation obs vs niveau validé** à coder dans la boucle post-turn (MVP fait seulement le flag-setting).
- **Monitoring dashboard admin** : inspecter `consolidation_events` (taux upgrade vs downgrade vs stabilisation) — Phase 2.
- **A/B test wording** : 3 variants des messages pour mesurer acceptance rate — Phase 3.

## 11. Sources clés

- Bull S. & Kay J. (2016). *Student Models that Invite the Learner In*. Springer (OLM negotiability).
- Ross S. (1998). Self-assessment in second language testing. *Language Testing* 15(1).
- Blanche P. & Merino B. (1989). Self-assessment of foreign-language skills. *Language Learning* 39(3).
- Dunning D. & Kruger J. (1999). Unskilled and unaware. *JPSP* 77(6).
- Samejima F. (1969). Graded Response Model. *Psychometrika*.
- Piech et al. (2015). Deep Knowledge Tracing. *NeurIPS*.

## 12. Changelog

- **2026-04-21 (Session 36)** — MVP livré : migration `01_consolidation_schema.sql`, module `pedagogy/consolidation.py` (29 tests), `TeacherResponse.observed_level`, chat_router hook, router `/api/consolidation/*`, 3 Svelte components, YAML banks ES/EN A1-B1. Kill switch `CONSOLIDATION_ENABLED=true`.
