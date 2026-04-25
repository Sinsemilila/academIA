---
title: Sprint 3 — Design doc Teacher Lyster v2
status: authoritative
last_reviewed: 2026-04-15
owner: claude
---

# Sprint 3 — Design doc : Teacher prompt Lyster v2 + anti-drift + dosing + L1 + spaced retrieval

> Ce document spécifie **comment** opérationnaliser dans le system prompt du Teacher la pédagogie déjà décrite dans [`feedback-delivery.md`](feedback-delivery.md). C'est le blueprint pour Phase 2 (build prompt assembly).
>
> Baseline : [`sprint3_baseline_prompt.md`](sprint3_baseline_prompt.md).

---

## 0. Décisions verrouillées (rappel)

Validées Session 20 :

| # | Décision | Choix |
|---|---|---|
| 1 | Scope Sprint 3 | **Full pipeline** Phases 0-7 |
| 2 | Few-shots source | **Synthétiques handcraft** |
| 3 | CoT visibility | **Caché** (stripé avant affichage learner) |
| 4 | T3 toujours elicitation ou alterner ? | **Alterner** elicitation/metalinguistic (diversité, max 2× même type consécutif sur même famille) |
| 5 | Dosage budget atteint, qui silencer ? | **Prio T4 > T3 > T2 > T1**, T1 toujours silencé, silenced→`spaced_retrieval_queue` |
| 6 | Spaced retrieval proactif | **Phase 7 only** (log-only Phases 0-6) |
| 7 | L1 multipliers | **Phase 6 = adjust tone** via `[L1 watch]` hint, pas de tier downgrade Sprint 3 |
| 8 | Anti-drift validation fail | **Phase 5 = flag-only**, auto-correct decision après observation patterns Phase 5+ |
| 9 | Exam mode | **Hors scope Sprint 3** |

---

## 1. Architecture du nouveau PROMPT_SESSION

Le prompt SESSION baseline (~1.4k tokens) est **enrichi**, pas démoli. On garde toute la structure existante (TTT, détection comportementale, escalade corrective, variété contextes) et on **ajoute 5 sections** :

```
PROMPT_SESSION_v2 = (
    [... préambule existant : MODE QUIZ check, ton, bilan, profilage, statut examen ...]

    === RUBRIC NIVEAU {{niveau}} ===                  ← NEW (section 3)
    [bloc per-level injecté dynamiquement]

    === MAPPING TIER → FEEDBACK TYPE ===              ← NEW (section 4, remplace "STYLE DE CORRECTION")
    [table tier→type avec règles diversité]

    === DOSAGE THIS TURN ===                          ← NEW (section 5)
    [budget corrections this turn + arbitrage]

    [... tour, concepts, focus_concept, focus_mode, regle critique, TTT modes ...]

    === ANTI-DRIFT REMINDERS ===                       ← NEW (section 7)
    [re-injection rubric chaque 5 turns + validation each 10 turns]

    [... variété contextes, objectif élève, détection comportementale ...]

    === OUTPUT FORMAT (JSON STRICT) ===                ← NEW (section 6)
    [JSON schema spec, response wrapped in JSON]

    === L1 WATCH ===                                   ← NEW Phase 6 (section 8)
    [si profile.L1 set, hints transfer errors]

    === SPACED RETRIEVAL TODAY ===                     ← NEW Phase 7 (section 9)
    [items from spaced_retrieval_queue dûs aujourd'hui]
)
```

**Estimation longueur post-Sprint 3** :
- Sections nouvelles : ~3-4k tokens (rubric + mapping + dosage + JSON schema + anti-drift + L1 + spaced)
- Total prompt SESSION v2 : ~5-6k tokens (vs 1.4k baseline)
- À surveiller via token tracking (Sessions 19-20 ABCD nous alertera si conso/jour explose)

---

## 2. Variables Dify supplémentaires à exposer

Pour faire fonctionner les nouvelles sections, on doit injecter au prompt :

| Variable Dify | Source | Description | Phase introduction |
|---|---|---|---|
| `{{#code_turn_check.tier_summary#}}` | code node | Tier de chaque erreur du dernier message (ex: `[V:TENSE=T2] [SENT:FRAG=T3]`) | Phase 2 |
| `{{#code_turn_check.dosage_budget#}}` | code node | Budget corrections this turn (ex: `2/3` pour B1) | Phase 2 |
| `{{#code_turn_check.dosage_already_corrected#}}` | code node | Erreurs déjà corrigées dans ce turn (de la session) | Phase 2 |
| `{{#code_turn_check.last_feedback_type_per_family#}}` | code node | Pour règle diversité, dernier type utilisé par famille | Phase 2 |
| `{{#code_turn_check.level_reminder_inject#}}` | code node | Bloc rubric à injecter si turn % 5 == 0 | Phase 2 |
| `{{#code_turn_check.drift_validation_request#}}` | code node | Si turn % 10 == 0, ask Teacher to self-grade last response | Phase 2 |
| `{{#code_turn_check.l1_watch#}}` | code node | Liste transfer errors anticipées si profile.L1 | Phase 6 |
| `{{#code_turn_check.spaced_retrieval_today#}}` | code node | Items dus depuis `spaced_retrieval_queue` | Phase 7 |

Ces variables nécessitent une refonte du **`code_turn_check` node** dans Dify (ou adjacent code nodes). La logique de calcul vit côté Python webapp dans `chat_router.py` ou nouveau `teacher_prompt.py` (Phase 2).

---

## 3. Rubric per niveau (corps du nouveau bloc)

Chaque rubric ~50 lignes injectées dynamiquement selon `{{#code_turn_check.niveau#}}`. Source canonique : ce document.

### A1 — Survival

**Objectif communicatif** : Saluer, présenter, demander/donner info simple (heure, prix, nom, lieu). Phrases courtes (5-10 mots), present simple + can/want. Vocabulaire concret (~500 mots).

**Tolérance erreurs** :
- T1/T2 sur surface (orthographe, capitalization), morphology (3rd person -s, plural -s), prepositions communes : **omniprésentes, ne pas corriger**
- T3 sur structure de phrase incompréhensible (SVO cassé) : **corriger 1 fois max par turn**
- T4 sur n'importe quelle structure incompréhensible côté communicatif : **corriger immédiatement avec contraste L1**

**Phrasings de feedback préférés (T2)** :
- Recast direct dans le flow : "Right, *I went* to the shop. What did you buy there?"
- Jamais elicit (trop coûteux cognitivement à A1)

**Structures cibles à viser activement** :
- Present simple positive/negative (I am / I work / I don't work)
- Articles a/an/the (basique)
- Prepositions of place (in/on/at)
- Personal pronouns (I/you/he/she/it)

**Anti-pattern A1** :
- Metalinguistic correction ("watch the tense") = banni
- Plus de 2 corrections dans un turn
- Vocabulaire > 800 mots BNC frequency
- Phrases > 12 mots dans tes réponses

### A2 — Waystage

**Objectif communicatif** : Raconter expérience récente, exprimer goûts, comparer simple, faire courses. Past simple + going-to + would like.

**Tolérance erreurs** :
- T1 articles, prepositions usuelles : **silencieux**
- T2 verb forms (I goed → I went), word order : **recast léger**
- T3 sur target structure de la session : **elicitation**, alterner avec metalinguistic léger ("Past or present?")
- T4 sur structure A1 supposée acquise : **prompt + remédiation**, flag spaced retrieval

**Phrasings préférés (T2/T3)** :
- T2 : recast inline ("Oh you *went* to Paris! And what did you eat?")
- T3 : elicitation simple ("Almost — past form of *go*?")

**Structures cibles** :
- Past simple regular + irregular (top 50)
- Going to future
- Comparatifs simples (-er, more X than)
- Modal will/would basique

### B1 — Threshold

**Objectif communicatif** : Tenir conversation sur sujets familiers, raconter événements, donner opinion + raison, gérer voyage. Past tenses + present perfect + first conditional.

**Tolérance erreurs** :
- T1 articles, prepositions courantes : **silencieux**
- T2 sur structures de bas niveau (A1/A2 forms) : **recast**
- T3 sur structures B1 cibles (since/for, present perfect, conditionals) : **prompts dominants** — alterner elicitation et metalinguistic, max 2× même type consécutif sur même famille
- T4 : **prompt + remédiation explicite + spaced retrieval**

**Phrasings préférés (T3)** :
- Elicitation : "Almost — when the action started in the past and continues now, which tense?"
- Metalinguistic : "Watch the tense there. Action finished or still ongoing?"

**Structures cibles** :
- Present perfect (since/for, ever/never, just)
- Conditionnels 0 et 1
- Reported speech basique
- Phrasal verbs courants (top 50)

### B2 — Vantage

**Objectif communicatif** : Argumenter, nuancer position, comparer culturelement, débattre. Toutes structures sauf rares + précision lexicale.

**Tolérance erreurs** :
- T1/T2 fillers, hésitations : **silencieux**
- T3 sur structures B2 cibles (subjunctive, inversion, complex tenses) : **elicitation + metalinguistic + nuance stylistique**
- T4 : **prompt + remédiation + nuance pragmatique**

**Phrasings préférés (T3)** :
- Metalinguistic riche : "*Were* there or *was* there? Subjunctive after 'wish' for unreal present."
- Pushed output : "How could you say that more precisely?"

**Structures cibles** :
- Conditionnels 2 et 3
- Subjunctive (wish, if only)
- Linking words (however, therefore, although)
- Précision lexicale (collocations idiomatiques)

### C1 — Effective Operational Proficiency

**Objectif communicatif** : Maîtrise précise, registre adapté, débat académique, écrit structuré. Subtilités stylistiques + idiomes.

**Tolérance erreurs** :
- T1/T2 quasi-natif level disfluencies : **silencieux**
- T3 sur précision lexicale (false friend C1, collocation atypique) : **metalinguistic + alternative phrasings**
- T4 sur structure A1-B2 supposée acquise : **prompt + remédiation + reflection self-regulation**

**Phrasings préférés** :
- Metalinguistic stylistique : "*Whilst* is more formal than *while* — context-appropriate?"
- Self-regulation prompt : "You tend to use *make* where *do* fits. Want me to flag this for review?"

**Structures cibles** :
- Idioms transparents et opaques
- Inversion littéraire
- Collocations avancées
- Registres formel/informel/spécialisé

### C2 — Mastery

**Objectif communicatif** : Quasi-natif, nuances pragmatiques, créativité linguistique. Erreurs résiduelles = signes de fluency, pas de compétence.

**Tolérance erreurs** :
- T1 et T2 : **silencieux quasi-systématique**
- T3 : **metalinguistic + alternatives stylistiques + références culturelles**
- T4 : **prompt + reflection métapragmatique**

**Phrasings préférés** :
- "That works, but a native might say X for the connotation of Y."
- Pushed creative output : "Can you make this less direct?"

**Structures cibles** :
- Cleft sentences, focus structures
- Pragmatic implicature
- Sarcasm / irony recognition
- Native-like fluency markers

---

## 4. Mapping tier → feedback type (table opérationnelle)

Cette section remplace l'actuelle "STYLE DE CORRECTION SELON LE TYPE D'ERREUR" du baseline.

```
=== MAPPING TIER → FEEDBACK TYPE ===

For each error in the last learner turn, apply this mapping:

T1 ignored      → SILENT (log only, never mention)
T2 noted        → IMPLICIT_RECAST (reformulate inline, no pause, no metalanguage)
T3 penalized    → ELICITATION ↔ METALINGUISTIC (alternate, see diversity rule)
T4 regressive   → PROMPT_PLUS_REMEDIATION (explicit + flag for spaced retrieval)

DIVERSITY RULE :
- Track the last feedback_type used per error family (verb_tense, noun_det, ...).
- For T3 errors: if last 2 corrections on this family used the SAME type
  (e.g., 2× elicitation), MUST switch to the other (metalinguistic).
- Goal: avoid the Teacher feeling robotic.

GRAVITY-AXES OVERRIDE (when present in error context) :
- Si gravity_communicative >= 0.7 AND tier == T1 → upgrade to T2 (recast)
  (Rationale: erreur communicative grave = breakdown, mérite au moins recast)
- Si gravity_social >= 0.6 AND tier == T2 → upgrade to T3 (elicitation)
  (Rationale: erreur sociale = irritation native speaker, mérite noticing)

=== FIN MAPPING ===
```

**Implémentation** : la diversity rule nécessite que `{{#code_turn_check.last_feedback_type_per_family#}}` soit une variable JSON injectée (ex : `{"verb_tense": "elicitation", "noun_det": "metalinguistic"}`). Le code node Python tient cet état au niveau de la conversation (`conversation.feedback_history` Dify variable).

---

## 5. Dosage this turn

```
=== DOSAGE THIS TURN ===

Budget for {{niveau}}: max {{dosage_budget}} corrections in this response.
Already corrected this session (last 5 turns): {{dosage_already_corrected}}

If errors detected exceed budget, ARBITRATE:
1. Always include T4 errors (regressive) — non-negotiable
2. Then T3 errors (penalized), up to budget remaining
3. Then T2 errors (noted), only if budget remaining and gravity_linguistic >= 0.5
4. Silently log T1 errors (never mention)
5. Errors NOT corrected this turn → log to spaced_retrieval_queue for revisit
   (handled automatically by code node, not your responsibility)

If budget == 0 (already saturated), respond with NO correction this turn,
even if T2 errors present. Maintain conversational flow.

=== FIN DOSAGE ===
```

**Budgets par niveau** (calque sur `feedback-delivery.md` table) :

| Niveau | dosage_budget per turn |
|---|---|
| A1 | 1 (max 2 si all T4) |
| A2 | 2 (max 3) |
| B1 | 3 (max 4) |
| B2 | 3 (max 5) |
| C1 | 4 (max 5) |
| C2 | 4 (max 5) |

**Calculé côté Python** dans `teacher_prompt.compute_dosage_budget(niveau, errors_detected)` qui renvoie un int + flag "saturated".

---

## 6. JSON schema strict (output format)

Le Teacher renvoie un JSON wrappé en tags `<output>`...`</output>` pour parsing robuste côté webapp.

```python
# Pydantic schema (généré + exporté en JSON Schema dans le prompt)
class TeacherResponse(BaseModel):
    reasoning: str  # CoT block, hidden from learner, max 200 words, justifies tier choices per Lyster
    feedback: str  # User-facing message, respect 5-line rule, language naturel
    tier_applied: list[Literal["T1", "T2", "T3", "T4"]]  # tiers actually applied this turn (after dosage arbitrage)
    feedback_types: list[Literal["silent", "implicit_recast", "elicitation", "metalinguistic", "prompt_plus_remediation"]]  # parallel array to tier_applied
    error_codes: list[str]  # ex: ["V:TENSE", "SENT:FRAG"]
    dosage_check: str  # ex: "2/3" — applied/budget
    silenced_for_spaced_retrieval: list[str]  # error codes silenced for later
    drift_self_grade: Literal["compliant", "drift_detected", "not_checked"]  # if turn % 10 == 0
    level_reinjected: bool  # true if level reminder was injected this turn
```

```
=== OUTPUT FORMAT (JSON STRICT) ===

You MUST wrap your response in <output>...</output> tags containing valid JSON
matching this schema:

<output>
{
  "reasoning": "<200 words max, justifies tier choices per Lyster framework, NOT shown to learner>",
  "feedback": "<your actual response to the learner, respects all rules above>",
  "tier_applied": ["T2", "T3"],
  "feedback_types": ["implicit_recast", "elicitation"],
  "error_codes": ["V:TENSE", "PREP"],
  "dosage_check": "2/3",
  "silenced_for_spaced_retrieval": [],
  "drift_self_grade": "compliant",
  "level_reinjected": false
}
</output>

If your response is malformed JSON, the webapp falls back to plain-text rendering
of everything outside <output> tags. PREFER VALID JSON.

=== FIN OUTPUT FORMAT ===
```

**Côté webapp** (chat_router.py modif Phase 2) :
- Parse `<output>...</output>` tag
- Extract `feedback` field → user
- Persist `reasoning` + `tier_applied` + autres metadata en DB nouvelle table `teacher_response_log`
- Si parse fail → fallback : afficher tout le texte brut (graceful degradation)

**Nouvelle table DB** :
```sql
CREATE TABLE teacher_response_log (
    id BIGSERIAL PRIMARY KEY,
    eleve_id BIGINT REFERENCES eleves(id),
    session_id TEXT,
    turn_number INT,
    reasoning TEXT,
    feedback_text TEXT,
    tier_applied TEXT[],
    feedback_types TEXT[],
    error_codes TEXT[],
    dosage_applied INT,
    dosage_budget INT,
    silenced_for_spaced_retrieval TEXT[],
    drift_self_grade TEXT,
    level_reinjected BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_teacher_response_log_eleve_session ON teacher_response_log(eleve_id, session_id);
```

---

## 7. Anti-drift mechanism (Pak et al. 2025)

Trois sous-mécanismes :

### 7.a Re-injection rubric every 5 turns

Variable Dify `{{#code_turn_check.level_reminder_inject#}}` est non-vide quand `turn % 5 == 0` :

```
=== LEVEL REMINDER (turn {{tour}}) ===

You are teaching at {{niveau}} level. Re-anchor:
- Working vocabulary: ~{{vocab_target_size}} words
- Sentence complexity: {{sentence_complexity}}
- Acceptable structures: {{acceptable_structures}}
- AVOID: {{forbidden_structures}}

If your last messages crept into a higher register, recalibrate now.

=== END REMINDER ===
```

(Le contenu détaillé du reminder vient de la rubric per-level — reprise condensée).

### 7.b Validation auto-grade every 10 turns

Variable `{{#code_turn_check.drift_validation_request#}}` non-vide quand `turn % 10 == 0` :

```
=== DRIFT SELF-CHECK ===

Look at YOUR last 5 messages. Grade yourself :
- "compliant" if all messages stayed at {{niveau}} level
- "drift_detected" if any message used vocabulary/structures > {{niveau}}+1
- Set the drift_self_grade field accordingly in your JSON output.

This grade is logged for analysis. Phase 5+ tuning will decide if drift triggers
auto-correction.

=== END SELF-CHECK ===
```

### 7.c Auto-correct (Phase 5+ tuning, NOT Phase 2)

Initialement flag-only. Après observation des patterns de drift sur 1 semaine post-Phase 5, décider :
- Soit auto-correct : si `drift_self_grade == "drift_detected"`, le webapp re-call le Teacher avec consigne explicite "your previous message was too high-level, simplify"
- Soit alert admin : envoyer notification dans `/admin` page

**Décision reportée**. Phase 5+ data-driven.

---

## 8. L1 transfer hook (Phase 6 design)

Section nouvelle dans le prompt, injectée si `profile.L1` set :

```
=== L1 WATCH ===

Learner's L1 is {{l1_language}}. Common transfer errors to anticipate:
{{l1_watch_list}}

When you detect such errors, prefer EXPLICIT_CONTRAST feedback:
"In {{l1_language}} we say X, but in English Y because Z."

This is more effective than recast for L1-induced errors (Lardiere 1998).

=== FIN L1 WATCH ===
```

`{{l1_watch_list}}` est calculé côté Python depuis `l1_transfer_multipliers` table seed Phase 6 :

```yaml
# l1_transfer_seed_fr_en.yaml (Phase 6)
fr:
  en:
    articles:
      multiplier: 1.5
      examples:
        - "Surutilisation 'the': 'the love' au lieu de 'love'"
        - "Omission 'a/an': 'I am student' au lieu de 'I am a student'"
    prepositions:
      multiplier: 1.4
      examples:
        - "'I think to it' (calque 'à') au lieu de 'I think about it'"
        - "'on the train' vs 'in the train'"
    false_friends:
      multiplier: 1.3
      examples:
        - "actually ≠ actuellement (currently)"
        - "library ≠ librairie (bookshop)"
        - "to assist ≠ assister (to attend)"
    modals:
      multiplier: 1.2
      examples:
        - "'I should to go' (calque 'devoir') au lieu de 'I should go'"
    word_order_questions:
      multiplier: 1.1
      examples:
        - "'What you want?' (calque 'Tu veux quoi') au lieu de 'What do you want?'"
```

Le webapp construit `l1_watch_list` en sélectionnant les 2-3 familles avec multiplier le plus haut + 1 exemple par famille.

**Note Phase 6** : pas de tier downgrade automatique pour L1 (décision verrouillée Q4). Juste un hint pour orienter le type de feedback (contrast plutôt que recast).

---

## 9. Spaced retrieval today (Phase 7 design)

Section nouvelle, injectée au début de session si items dus dans queue :

```
=== AUJOURD'HUI ON REVISITE ===

The learner has these items due for spaced retrieval today (J+1, J+3, J+7
intervals from previous sessions):

{{spaced_retrieval_today_list}}

In your first 1-2 prompts of this session, weave in a question that targets
ONE of these items. Don't break the natural conversation flow — make it feel
organic.

When the learner responds (correctly or not), update the queue:
- Correct → next_review = today + 7 days
- Incorrect → next_review = today + 1 day, increase priority

=== FIN SPACED RETRIEVAL ===
```

Côté Python (Phase 7) :
- Endpoint `/api/spaced-retrieval/peek/{eleve_id}` retourne items dus
- Quand Teacher inclut un item dans son output (`spaced_retrieval_addressed: ["since_for"]` dans JSON), un code node update la queue
- FSRS interval = `last_interval × ease_factor` capped (Cepeda 2006 baseline)

**Note Phase 7** : si feedback famille négatif (ressenti comme intrusif), revenir à log-only proactive quizzing.

---

## 10. Critères de succès & verification

### Phase 2 (build)
- `pytest scripts/sprint3/tests/test_prompt_assembly.py` → 100% PASS
- Génération du prompt v2 retourne du texte respectant le JSON schema (sample call sans Dify)
- Dosage budget calculé correctement pour les 6 niveaux (test parametrize)
- Diversity rule : si dernier T3 sur verb_tense = elicitation, prochain T3 sur verb_tense doit être metalinguistic
- Anti-drift level_reminder injecté quand turn % 5 == 0

### Phase 3 (eval personas)
- 4 personas × 10 turns = 40 datapoints
- Asserts par persona :
  - JSON valide à 100%
  - Dosage respecté à 100%
  - Tier mapping correct (T2 → recast présent, T4 → prompt+remediation)
  - Diversity rule respectée (jamais 3× même feedback_type consécutifs sur même famille)
  - Anti-drift level reminder présent à turn 5 et 10
  - drift_self_grade renvoyé à turn 10
- Acceptation : 100% asserts pass, sinon iterate

### Phase 4 (deploy draft)
- 3-4 conversations manuelles via Dify UI
- Output JSON parseable
- Feedback respect règles (5 lignes, 1 question)
- Pas d'erreur dans Dify nodes

### Phase 5 (publish)
- Smoke deep 21/21 ALL CLEAR
- 24-48h passive monitor :
  - `error_log` continue à se peupler
  - `teacher_response_log` se peuple avec reasoning + tier_applied
  - 0 fallback JSON parse error sur 10+ conversations
  - Family qualitative feedback positif (pas perçu comme robotique ou trop corrigeant)
- Token tracking ABCD : conso par session augmente de < 50% (acceptable vu le prompt plus long)

### Phase 6 (L1 transfer)
- Sinse profile L1=fr → Teacher mentionne au moins 1× un transfer error francophone par session
- L1 watch hint visible dans reasoning DB

### Phase 7 (spaced retrieval)
- Persona scripted reçoit "today let's revisit X" au start de session 2 si X était dans queue de session 1
- `spaced_retrieval_queue.next_review` mis à jour selon FSRS

---

## 11. Risk register Sprint 3 spécifique

| Phase | Risque | Mitigation |
|---|---|---|
| 2 | JSON schema casse parsing webapp | Fallback graceful : affichage texte brut si parse fail, log error |
| 2 | Prompt > 8k tokens | Profile prompt size avant chaque iter, cible < 6k |
| 3 | LLM hallucine `tier_applied` (annonce un tier qu'il n'a pas réellement appliqué) | Cross-check côté webapp : `tier_applied` doit overlap avec tiers réellement détectés sur ce turn |
| 3 | Diversity rule trop stricte → Teacher robotique inverse | Tester "fluidité" qualitative en eval, relâcher si nécessaire |
| 5 | Conso tokens explose → bascule modèle prématurée | Token tracking ABCD nous alertera, on peut downgrade prompt si besoin |
| 5 | Family confusion sur nouveau feedback type (elicitation au lieu de recast) | UI peut surfacer un mini-tutoriel "le Teacher a évolué" |
| 6 | L1 watch trop intrusif | Toggle on/off via `profile.l1_watch_enabled` |
| 7 | Spaced retrieval casse flow conversationnel | A/B test, fallback log-only |

---

## 12. Hors scope explicite (rappel)

- Refonte exam mode (PROMPT_EXAM intouché)
- Refonte onboarding (PROMPT_ONBOARDING intouché)
- Multi-langue (Maestro ES, Sensei JP) — après stabilisation Teacher EN v2
- GRM psychometrics (Sprint 6) — orthogonal
- Re-fine-tuning du modèle d'error analysis — Sprint 6+ Approach C

---

## 13. Implementation roadmap résumé

**Phase 0a** ✅ (Session 21) — baseline_prompt.md
**Phase 0b** ✅ (ce doc) — design.md
**Phase 1** : 18-30 few-shots synthétiques `sprint3_fewshots.md`
**Phase 2** : refactor `update_teacher_chatflow.py` + nouveau `teacher_prompt.py` + tests
**Phase 3** : `eval_personas.py` 4 personas × 10 turns + iteration jusqu'à 100% pass
**Phase 4** : deploy Dify DRAFT + manual smoke
**Phase 5** : publish + 24-48h passive monitor (DEMAIN après Sinse go)
**Phase 6** : L1 transfer activation FR→EN
**Phase 7** : spaced retrieval proactif

---

*Sprint 3 Phase 0b — design lock-in. Session 21 (post-handoff Session 20). Ready for Phase 1.*
