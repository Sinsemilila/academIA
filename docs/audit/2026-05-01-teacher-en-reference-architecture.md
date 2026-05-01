---
title: Teacher EN reference architecture — single source of truth for IT/DE/RU/JP build
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 55
tags: [audit, multilang, architecture, reference]
ai_summary: "Architecture exhaustive Teacher EN end-to-end (FastAPI pipeline + Dify 41 nodes + n8n 7 webhooks + data layer YAMLs + Oracle infra). Template pour build IT/DE/RU/JP with per-lang adaptation notes."
---

# Teacher EN — reference architecture

**Context** : Pivot S55 acté — Build avant Measure. Teacher EN = ~40 sessions maturation = source of truth pour future langues. Ce doc cartographie EXHAUSTIVELY comment Teacher EN fonctionne de fond en comble + tout ce qui lui est injecté + comment chaque sous-système se déclenche.

**Usage** : 
1. Référence canonique "comment Teacher EN fonctionne" pour future Claude sessions
2. Template pour build Maestro ES Phase 1+ (correctifs structurels) — cf `2026-05-01-maestro-es-vs-teacher-en-build-gap.md`
3. Template pour Wave 2 (IT/DE A1-B2) + Wave 3 (JP) + Wave 4 (RU) — chaque wave = même architecture, adaptations per-lang documentées en fin de doc

---

# 🎯 ARCHITECTURE OVERVIEW

## System diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  Frontend SvelteKit  /chat/[agent]  → POST /api/chat/send           │
└───────────────────────────────────┬─────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Backend FastAPI  chat_router.chat_send()                           │
│  ├─ auth middleware (cookie session)                                │
│  ├─ rate_limit per-user                                             │
│  ├─ resolve agent (agents_config.py: AgentDef → dify_app_id)        │
│  ├─ LanguageDomain(lang_target)                                     │
│  │    └─ taxonomy.rules.detect_errors() (spaCy + regex hybrid EN)   │
│  ├─ Build dify_inputs dict (23 keys) :                              │
│  │    ├─ Pedagogy modules :                                         │
│  │    │   ├─ scaffolding_policy.build_scaffolding_block()           │
│  │    │   ├─ priority_loop.compute_priority_concepts()              │
│  │    │   ├─ three_strikes.detect_three_strikes_family()            │
│  │    │   ├─ cf_classifier.classify_cf() (BIPED S1, flag-gated)     │
│  │    │   └─ teacher_prompt.build_dynamic_sections() :              │
│  │    │        ├─ load_rubrics(lang)                                │
│  │    │        ├─ load_fewshots(lang)                               │
│  │    │        ├─ load_l1_transfers(l1, target)                     │
│  │    │        ├─ load_micro_lessons(lang)                          │
│  │    │        ├─ load_concept_hints_for_level(lang, niveau) [S55]  │
│  │    │        └─ load_cefr_diagnostics(lang)                       │
│  │    └─ tolerance_matrix._get_error_tier() — T1/T2/T3/T4 routing   │
│  ├─ PII scrubber (security/pii_scrubber.py — 5 regex patterns)      │
│  ├─ Token budget 3-tier waterfall (gpt-4o-mini → groq-std → groq-snap)│
│  └─ httpx POST Dify /v1/chat-messages (response_mode=streaming)     │
└───────────────────────────────────┬─────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Dify workflow Teacher EN (39565197...)  41 nodes                   │
│  ┌──────┐  ┌──────────────┐  ┌──────────────────────────────┐      │
│  │ start│→ │http_profil_get│→│code_profil_check (qcm bypass)│      │
│  └──────┘  └──────────────┘  └──────┬───────────────────────┘      │
│                                     ↓                              │
│                              ┌──────────────────┐                  │
│                              │ if_profil ?      │                  │
│                              └──┬─────────┬─────┘                  │
│                              YES│         │NO                       │
│                                 ↓         ↓                         │
│                        code_turn_check  llm_onboarding              │
│                         (orchestration)  (QCM diagnostic 5-7q)      │
│                                 ↓                                   │
│                        ┌────────┴────────┐                          │
│                        ↓                 ↓                          │
│                   if_first_turn?    if_exam_active?                 │
│                       │                 │                           │
│                       ↓                 ↓                           │
│                   llm_plan_choice    llm_exam (T=0.2)               │
│                                                                     │
│                       ↓                                             │
│                  llm_session (T=0.7, cache_v1, MAIN LLM)            │
│                       ↓                                             │
│                   var_assigner counter, code_check, http_snapshot   │
│                       ↓                                             │
│                   answer node → SSE stream client                   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  n8n webhooks (7 actifs)                                            │
│  ├─ dify-profil-get GET → profils_eleves SELECT (2024 runs, 100%)   │
│  ├─ dify-profil-update POST → profils_eleves UPDATE (87 runs, 95%)  │
│  ├─ dify-snapshot POST → Dify msgs + LiteLLM groq → store (144,83%) │
│  ├─ dify-diagnostic POST → CEFR scoring LiteLLM gpt-4o-mini (32,72%)│
│  ├─ dify-exam-scoring POST → exam grading LiteLLM ft:gpt-4o-mini    │
│  ├─ dify-exam-persist POST → save state (842 runs, 100%)            │
│  └─ dify-snapshot fallback → academie-api error analysis            │
└───────────────────────────────────┬─────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  PostgreSQL (academie_db) — single source of truth                  │
│  ├─ profils_eleves (learner state, CEFR, exam, scores)              │
│  ├─ error_log (detected errors per turn)                            │
│  ├─ user_sessions (session timing, conversation_id, dify_user_id)   │
│  ├─ token_usage_daily (3-tier budget tracking)                      │
│  ├─ streaks (daily login streak)                                    │
│  ├─ spaced_retrieval_queue (J+1 items)                              │
│  ├─ learner_profiles (QCM output)                                   │
│  └─ workflows (Dify graph stored, EN draft + published)             │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Post-turn hooks (in stream_with_xp generator after SSE complete)   │
│  ├─ _track_gpt4o_tokens(input, output) — 3-tier waterfall update    │
│  ├─ _update_streak — daily login increment                          │
│  ├─ _update_session — XP trigger at message 10 (50 XP event)        │
│  ├─ lang.parse_response() — extract Teacher JSON output             │
│  ├─ _persist_spaced_retrieval — enqueue J+1 items (flag-gated)      │
│  └─ _consolidation_post_turn — update CEFR observed_level           │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 1. BACKEND FastAPI pipeline

## Entry point : `POST /api/chat/send`

**File** : `/opt/academie/webapp/backend/app/routers/chat_router.py:590-1162`

**Imports critiques** :
```python
from academie_core.taxonomy.rules import ERROR_CODE_TO_FAMILY
from academie_core.openai_reconcile import reconcile_openai_usage
from academie_core.pedagogy.teacher_prompt import PromptContext
from academie_core.domain.language import LanguageDomain
```

## Pipeline 15 étapes

| # | Lines | Operation | Vars produites | Dify inputs populés |
|---|---|---|---|---|
| 1 | 596-600 | Auth + rate limit + agent dispatch | `dify_key`, `domain`, `lang`, `dify_user` | — |
| 2 | 602-657 | Session timing + ownership check | `minutes_since_last`, `turn_response_secs` | `minutes_since_last`, `turn_response_secs` |
| 3 | 660-668 | Init dify_inputs + mock_exam/mode_override | `dify_inputs={}` | `mock_exam`, `mode_override` (opt) |
| 4 | 669-695 | Error detection + learner profile fetch | `detections`, `niveau`, `profile_l1`, `l1_watch_on` | — |
| 5 | 697-742 | QCM learner profile load | `has_qcm_profile`, `fla_*`, `self_efficacy`, `autonomy_pref` | `learner_profile_json`, `learner_profile_summary` |
| 6 | 749-778 | Priority concepts (Ebbinghaus forgetting) | `priority_concepts` | (injecté scaffolding_block) |
| 7 | 780-795 | Three-strikes detection (3× same family in 10 errors, 3-day dedup) | `three_strikes_family` | (injecté scaffolding_block) |
| 8 | 797-828 | Build error_feedback + repeated_errors (tolerance matrix) | `lines`, `repeated_errors` | `error_feedback`, `repeated_errors` |
| 9 | 830-1053 | Build dynamic sections (scaffolding S35 + priority S37 + micro-lessons S38 + BIPED CF S52) | `v2_errors`, `cf_recommendation` | rubric, fewshots, dosage, level_reminder, drift_validation, l1_watch, spaced_retrieval, scaffolding, priority_concepts, micro_lesson, output_schema, concept_hints, cefr_diagnostics, lang_target_name, lang_target_prof |
| 10 | 1055-1062 | 3-tier waterfall token budget check | `target_tier`, `reason` | (model switch only) |
| 11 | 1064-1070 | Assemble Dify payload | `payload` (dict) | — |
| 12 | 1072-1078 | PII scrubber on query + inputs | `pii_hits` | — (in-place scrub) |
| 13 | 1080-1125 | SSE stream generator + collect chunks | `collected_answer` | — |
| 14 | 1107-1111 | Streak/session/XP hooks | `xp_earned` | — |
| 15 | 1119-1161 | Post-turn hooks (parse, spaced retrieval, consolidation) | `parsed: TeacherResponse` | — |

## Dify inputs dict — full mapping (23 keys)

| Key | Source module | Data file | Populated when |
|---|---|---|---|
| `minutes_since_last` | chat_router session timing | `user_sessions` | Always |
| `turn_response_secs` | chat_router session timing | `user_sessions` | Always |
| `mock_exam` | ChatRequest payload | (in-request) | If req.mock_exam |
| `mode_override` | ChatRequest payload | (in-request) | If req.mode_override |
| `learner_profile_json` | loader + DB | `learner_profiles` | If eleve_id + QCM done |
| `learner_profile_summary` | loader + DB | `learner_profiles` | If eleve_id + QCM done |
| `error_feedback` | rules + tolerance_matrix | `tolerance_matrix.yaml` | Always (empty if no errors) |
| `repeated_errors` | error_log query | `error_log` | If errors in last 7d |
| `rubric_for_level` | teacher_prompt.build_dynamic_sections | `rubrics/<lang>.yaml` | Always |
| `fewshots_block` | teacher_prompt.build_dynamic_sections | `fewshots/<lang>.yaml` | Always |
| `dosage_block` | teacher_prompt.arbitrate_dosage | (computed) | Always |
| `level_reminder_inject` | teacher_prompt.build_level_reminder | (hardcoded) | If turn_count % 5 == 0 |
| `drift_validation_request` | teacher_prompt.build_drift_check_request | (hardcoded) | If turn_count % 10 == 0 |
| `l1_watch` | teacher_prompt.build_l1_watch | `l1_transfer/fr_to_<target>.yaml` | If l1 + l1_watch_on |
| `spaced_retrieval_today` | teacher_prompt.build_spaced_retrieval_block | `spaced_retrieval_queue` | If SPACED_RETRIEVAL_ENABLED |
| `scaffolding_block` | scaffolding_policy.build_scaffolding_block | (computed via PolicyRow matrix) | Always (S35+) |
| `priority_concepts_block` | teacher_prompt.build_priority_concepts_block | `curriculum_<lang>.yaml` | If PRIORITY_CONCEPTS_ENABLED |
| `micro_lesson_block` | three_strikes.build_micro_lessons_block | `micro_lessons/<lang>.yaml` | If MICRO_LESSON_ENABLED + three_strikes_family |
| `output_schema_block` | teacher_prompt.build_output_schema_block | (hardcoded JSON schema) | Always |
| `concept_hints_json` | loader.load_concept_hints_for_level | `concept_hints/<lang>.yaml` | Always (S55 fix : filtered ≤level) |
| `cefr_diagnostics_block` | loader.build_cefr_diagnostics_block | `cefr_diagnostics/<lang>.yaml` | Always |
| `lang_target_name` | loader.get_persona_label | `cefr_diagnostics/<lang>.yaml` | Always |
| `lang_target_prof` | loader.get_persona_label | `cefr_diagnostics/<lang>.yaml` | Always |

## Pedagogy modules `packages/academie-core/academie_core/pedagogy/`

### 1. `scaffolding_policy.py`
- API : `build_scaffolding_block(cefr_placement, distance, fla, target_lang_name, l1_name, turn_count, **kwargs)` → str
- Inputs : CEFR (A1-C2), distance (close/medium/distant), FLA (low/mid/high), per-item FLA + self_efficacy + autonomy_pref + post_qcm_welcome
- Lang-aware : ✅ via `target_lang_name` + `l1_name` params (no hardcoded content)
- PolicyRow matrix lines 45-58 : Hawkins-aligned A1/A2/B1+ × close/medium/distant → l2_ratio_pct, l1_uses, sandwich, reassurance, intensity
- Called : line 961-973 chat_router

### 2. `priority_loop.py`
- API : `compute_priority_concepts(scores_confiance, concept_keys, concept_weights, today_date)` → list[PriorityConcept]
- Formula : `priority(c) = weight_norm(c) × time_factor(c) × deficit(c)` (Ebbinghaus forgetting curve)
- Lang-aware : ❌ language-agnostic (formula universal)
- Called : line 752-775 chat_router

### 3. `three_strikes.py`
- API : `detect_three_strikes_family(conn, eleve_id, domain, window_errors=10, threshold=3, dedup_days=3)` → str | None
- Logic : Query last 10 errors, count by family (ERROR_CODE_TO_FAMILY mapping), trigger if 3× same in 3-day dedup window
- Lang-aware : ⚠️ via ERROR_CODE_TO_FAMILY (per-lang taxonomy mapping)
- Called : line 787-792 chat_router

### 4. `cf_classifier.py`
- API : `classify_cf(learner_text, errors_detected, level, turn_count, lang)` → dict | None
- Returns : `{cf_move, target_concept, confidence, reasoning, source}`
- Uses : LiteLLM proxy gemini-flash-lite + `extracted/lyster-2007/cf-taxonomy.yaml` (Lyster 10-move + AcademIA silent policy)
- Lang-aware : ✅ multi-lang LLM-based (not hardcoded patterns)
- Called : line 886-901 chat_router (BIPED Step 1, flag-gated `BIPED_CF_CLASSIFIER_ENABLED`)

### 5. `consolidation.py`
- API : post-turn hook updates CEFR observed_level + dormancy watch + niveau reconciliation
- Lang-aware : ❌ domain-agnostic (logic uniforme)
- Called : line 1150-1157 chat_router (post-stream, flag-gated)

### 6. `typological_distance.py`
- API : `get_distance(l1, target_lang)` → Distance (close/medium/distant)
- Hardcoded `_DISTANCE_TABLE` 62 pairs (lines 22-62)
- FR-EN = "close" (Romance/Germanic Latin contact)
- FR-ES = "close" (Romance siblings)
- FR-IT = "close"
- FR-DE = "medium"
- FR-RU = "distant"
- FR-JP = "distant"
- Called : line 958 (input scaffolding_policy)

### 7. `teacher_prompt.py`
- API : `build_dynamic_sections(ctx: PromptContext, lang_data: LanguageData | None)` → dict
- Assembles 8 sections : rubric, dosage, fewshots, level_reminder, drift_check, l1_watch, spaced_retrieval, output_schema
- `parse_teacher_response(raw_text)` → TeacherResponse (post-stream JSON parse)
- Lang-aware : ✅ `LanguageData.for_lang(target_lang)` loads per-lang YAMLs
- Called : line 933 chat_router

## Data loaders `data/loader.py` (lru_cache)

| Function | Cache size | Data source | Called by |
|---|---|---|---|
| `load_rubrics(lang)` | 16 | `rubrics/<lang>.yaml` | teacher_prompt |
| `load_fewshots(lang)` | 16 | `fewshots/<lang>.yaml` | teacher_prompt |
| `load_anti_patterns(lang)` | 16 | `fewshots/<lang>.yaml` (anti_patterns key) | teacher_prompt (futur) |
| `load_l1_names()` | 1 | `l1_transfer/l1_names.yaml` | teacher_prompt |
| `load_l1_transfers(l1, target)` | uncached | `l1_transfer/<l1>_to_<target>.yaml` | teacher_prompt.build_l1_watch |
| `load_extracted(book_slug, name)` | 64 | `extracted/<slug>/<name>.yaml` | cf_classifier (cf-taxonomy) |
| `load_concept_hints(lang)` | 16 | `concept_hints/<lang>.yaml` | teacher_prompt, chat_router |
| `load_concept_hints_for_level(lang, level)` | 16 | + `curriculum_<lang>.yaml` | chat_router (S55 fix filter) |
| `load_micro_lessons(lang)` | 16 | `micro_lessons/<lang>.yaml` | three_strikes |
| `load_functions(lang)` | 16 | `functions/<lang>.yaml` | (Phase D1) |
| `load_cefr_diagnostics(lang)` | 16 | `cefr_diagnostics/<lang>.yaml` | chat_router |
| `load_onboarding_content(domain)` | 16 (per-tier) | `onboarding/core.yaml` + `domains/<kind>.yaml` + `overlays/<lang>.yaml` | /api/onboarding |

## Token budget 3-tier waterfall

**File** : `chat_router.py:352-448`

```python
_TIER_CHAIN = [
    ("gpt-4o-mini", 2_500_000),    # Tier 1 OpenAI complimentary 2.5M TPD
    ("groq-standard", 100_000),    # Tier 2 Groq llama-3.3-70b-versatile 100K TPD
    ("groq-snapshot", 500_000),    # Tier 3 Groq llama-3.1-8b-instant 500K TPD
]
_TIER_SWITCH_THRESHOLD = 0.95  # switch when 95% TPD reached
```

**Logic** : `_select_active_tier()` walks chain, picks first tier <95% used. `_switch_dify_model()` UPDATEs `workflows.graph` text replacement.

## Flag-gated features (env var overrides)

- `SCAFFOLDING_BLOCK_ENABLED` (default true)
- `PRIORITY_CONCEPTS_ENABLED` (default false)
- `MICRO_LESSON_ENABLED` (default false)
- `SPACED_RETRIEVAL_ENABLED` (default false)
- `CONSOLIDATION_ENABLED` (default true)
- `BIPED_CF_CLASSIFIER_ENABLED` (default false)
- `USE_V2_TOLERANCE` (default false)
- `THREE_STRIKES_DEDUP_BYPASS` (default false)

---

# 2. DIFY workflow (41 nodes, app `39565197-c9d1-4d5b-b66f-18925de236d9`)

## Workflow overview

41 nodes / 45 edges / type advanced-chat / provider langgenius/openai_api_compatible.

## Node inventory (clés)

| Sequence | Node ID | Type | Role |
|---|---|---|---|
| 0 | `1775343637677` | start | Input hub 23 vars |
| 1 | `1775343918798` | http-request | n8n `dify-profil-get` (GET) |
| 2 | `code_profil_check` | code | Parse profil n8n + QCM bypass detection |
| 3 | `if_profil` | if-else | Route has_profile vs onboarding |
| 4 | `llm_onboarding` | llm | First-time QCM diagnostic (gpt-4o-mini, 400tok, T=0.7) |
| 5 | `code_eval_check` | code | Detect [EVAL_READY] marker |
| 6 | `if_eval_ready` | if-else | Trigger n8n diagnostic |
| 7 | `http_diagnostic` | http-request | n8n `dify-diagnostic` POST |
| 8 | `code_turn_check` | code | **Core orchestrator** ~600L (concept selection, TTT mode, exam detection, spaced retrieval) |
| 9 | `if_first_turn` | if-else | Route premier tour |
| 10 | `llm_plan_choice` | llm | Plan concepts session (gpt-4o-mini, 400tok, T=0.7) |
| 11 | `llm_session` | llm | **Main conversation LLM** (gpt-4o-mini, 600tok, T=0.7, **CACHE_REORDER_v1**) |
| 12 | `llm_exam` | llm | Examinateur CECRL (gpt-4o-mini, 400tok, **T=0.2**) |
| 13 | `code_exam_detect` | code | Parse [EXAM_START]/[REVIEW_LACUNES] markers |
| 14 | `var_assigner_exam_start` | assigner | Init exam state |
| 15 | `if_exam_active` | if-else | Route exam path vs normal |
| 16 | `code_exam_track` | code | Track question num + responses ; detect [EXAM_COMPLETE]/[EXAM_ABORT] |
| 17 | `if_exam_complete` | if-else | Trigger scoring |
| 18 | `http_exam_scoring` | http-request | n8n `dify-exam-scoring` POST |
| 19 | `code_exam_bilan` | code | Format scoring report |
| 25 | `http_exam_persist` | http-request | n8n `dify-exam-persist` POST (high freq) |
| 27-31 | snapshot family | code+http | Every 10 turns : code_check → http_snapshot → parse → store |
| 32 | `http_profil_update` | http-request | n8n `dify-profil-update` async |
| 33 | `var_assigner` | assigner | Increment counter |
| 34-37 | `answer_*` | answer | Return to user (plan/session/onboarding/exam) |

## Start node — 23 input variables

| Variable | Type | Required | Max | Default | Format |
|---|---|---|---|---|---|
| `minutes_since_last` | text-input | False | 10 | '0' | int as str |
| `mock_exam` | text-input | False | 200 | '' | "Q3/10:concept:MODE" or "bilan" |
| `mode_override` | text-input | False | 20 | '' | 'libre' or 'structure' |
| `error_feedback` | text-input | False | 1000 | '' | rules + tolerance enriched |
| `turn_response_secs` | text-input | False | 10 | '0' | int as str |
| `repeated_errors` | text-input | False | 500 | '' | last 7d recurring codes |
| `rubric_for_level` | paragraph | False | 4000 | '' | Sprint 3 V2 rubric YAML rendered |
| `fewshots_block` | paragraph | False | 4000 | '' | rendered fewshots context |
| `dosage_block` | paragraph | False | 2000 | '' | T1-T4 mapping |
| `level_reminder_inject` | paragraph | False | 2000 | '' | implicit scaffolding |
| `drift_validation_request` | paragraph | False | 2000 | '' | drift check prompt |
| `l1_watch` | paragraph | False | 2000 | '' | L1 transfer alert |
| `spaced_retrieval_today` | paragraph | False | 2000 | '' | J+1 items list |
| `output_schema_block` | paragraph | False | 2000 | '' | JSON output schema |
| `lang_target_name` | text-input | False | 40 | 'Anglais' | "Anglais", "Espagnol" etc |
| `lang_target_prof` | text-input | False | 40 | "d'anglais" | "d'anglais", "d'espagnol" etc |
| `concept_hints_json` | paragraph | False | **50000** | '{}' | dict[concept_key→hint] (S55 bumped 10K→50K) |
| `cefr_diagnostics_block` | paragraph | False | 5000 | '' | palier examples + guidance |
| `learner_profile_json` | paragraph | False | 10000 | '{}' | QCM JSON |
| `learner_profile_summary` | paragraph | False | 10000 | '' | QCM summary text |

## LLM nodes — system prompts (résumé)

### `llm_session` (main, 144L, T=0.7, cache_v1)
- Persona "Tu es Teacher, prof {lang_target_prof}. Tu tutoies."
- Sections (in order) : `rubric_for_level` → TON ET STYLE → BILAN POST-DIAGNOSTIC → PROFILAGE PROGRESSIF → DETECTION EXAMEN → DETECTION REVISION → REGLES ABSOLUES → ERREURS DETECTEES → MAPPING TIER → CONCEPT ACTIF → APPROCHE TTT → level_reminder + drift + l1_watch + spaced_retrieval → VARIETE CONTEXTES → DETECTION COMPORTEMENTALE → fewshots + output_schema → OBSERVED_LEVEL_v2

### `llm_onboarding` (168L, T=0.7)
- Phase 1 ACCUEIL (3 tours FR : prénom + niveau auto-éval 5 choix + intérêts/style)
- Phase 2 DIAGNOSTIC (5-7 échanges EN) avec micro-tâche obligatoire échange 4-5
- Trigger [EVAL_READY] post 5+ EN questions
- QCM_OVERRIDE_v1 : si learner_profile non-vide → bypass Phase 1 + démarrer EN au palier QCM
- NO_LEGACY_BILAN_v1 : si QCM done → JAMAIS produire bilan textuel

### `llm_plan_choice` (60L, T=0.7)
- Présente plan session avec icônes 🆕⏰⚡✅
- Demande "Tu veux commencer par lequel ?"
- INTERDICTIONS : never [EXAM_START] / never enseigner ici

### `llm_exam` (94L, T=0.2)
- Examinateur CECRL ton neutre, vouvoie
- 4 priorités : message parasite [REPEAT_QUESTION] / reprise / première question / réponse normale
- Format strict : "Question N/total — concept\n[TYPE]\n[question]"
- 6 types : FILL/CORRECT/TRANSFORM/CHOICE/FORM/PRODUCE
- PRODUCE % per CEFR : A1-A2 20% / B1 40% / B2 50% / C1-C2 60%

## Code nodes (JS extracted)

### `code_profil_check`
- Inputs : `body` (n8n response) + `learner_profile_json` + `learner_profile_summary`
- Logic : parse n8n profile + **QCM_AS_PROFIL_v1** bypass + exam_resume detection
- Outputs : 20 fields (profil_present, profil_text, concept_keys_json, scores_json, mode_apprentissage, exam_resume_*, etc)

### `code_turn_check` (~600L core orchestrator)
- Inputs : 37 variables
- Logic :
  1. Spaced repetition score per concept (weakness 100-score + days overdue × 2)
  2. Concept selection top-2 par priorité
  3. TTT mode inference : score=0 DECOUVERTE / 1-49 RENFORCEMENT / 50-79 PRATIQUE / 80+ MAINTIEN
  4. Exam recommendation logic (all_tested + ≥80% mastery → "recommended", 3-day cooldown)
  5. Promotion detection
  6. Module failure recovery
  7. Absence-aware welcome (>1h, days, weeks)
  8. Review mode if conversation.review_mode==active
  9. Mock exam (quiz) instructions
- Outputs : 24 fields (`is_first_turn`, `tour`, `niveau`, `selected_concepts`, `focus_concept`, `focus_mode`, `transition_instruction`, `duration_hint`, `promotion_msg`, `plan_prefix`, `exam_modules_json`, +Sprint 3 V2 blocks)

### `code_eval_check` / `code_exam_detect` / `code_exam_track` / `code_exam_persist` / `code_exam_bilan` / `code_check`
Markers parsing + state mutations (cf table inventaire ci-dessus).

## Conversation variables (state)

| Variable | Type | Initial | Updated by | Usage |
|---|---|---|---|---|
| `nb_interactions` | int | 0 | var_assigner | Turn counter |
| `exam_mode` | str | 'off' | var_assigner_exam_start, code_exam_track | off/intro/active/scoring |
| `exam_question_num` | int | 0 | code_exam_track | Current Q # |
| `exam_responses` | JSON[] | '[]' | code_exam_track | [{q, answer}] |
| `exam_module_index` | int | 0 | var_assigner_exam_reset | Module 0-indexed |
| `exam_module_total` | int | 1 | var_assigner_exam_start | Total modules |
| `exam_module_name` | str | '' | var_assigner | Label |
| `exam_module_concepts` | str | '' | var_assigner | Concept list |
| `exam_total_questions` | int | 20 | var_assigner | Q count module |
| `exam_modules` | JSON[] | '[]' | var_assigner_exam_start | Full config |
| `review_mode` | str | '' | code_exam_detect | 'active' |
| `session_snapshot` | str | '' | store_snapshot | Last summary |

---

# 3. n8n workflows (7 actifs)

## Inventory

| Workflow | Webhook | Method | Runs | Success | Trigger source |
|---|---|---|---|---|---|
| `dify-profil-get` | `/dify-profil-get` | GET | 2024 | 100% ✅ | Dify start (always) |
| `dify-profil-update` | `/dify-profil-update` | POST | 87 | 95% | Snapshot post-write |
| `dify-snapshot` | `/dify-snapshot` | POST | 144 | 83% ⚠️ | Every 10 turns |
| `dify-diagnostic` | `/dify-diagnostic` | POST | 32 | 72% ⚠️ | [EVAL_READY] post-onboarding |
| `dify-exam-scoring` | `/dify-exam-scoring` | POST | 60 | 97% | [EXAM_COMPLETE] |
| `dify-exam-persist` | `/dify-exam-persist` | POST | 842 | 100% ✅ | Every exam state change |

⚠️ Note : duplicate `dify-diagnostic` workflow exists (cleanup pending).

## Webhook contracts (concrete examples)

### `dify-profil-get` GET response (verbatim sample)
```json
{
  "profil_formate": "[PROFIL ELEVE]\nPrénom: Alice\nNiveau : B1\n...",
  "concept_keys": ["present_simple", "past_simple", "phrasal_verbs"],
  "scores_confiance": {"present_simple": 90, "past_simple": 75, "phrasal_verbs": 30},
  "mode_apprentissage": "structure",
  "next_concept_keys": [],
  "next_niveau": "B2",
  "examen_en_cours": null,
  "dernier_examen": {"passed": true, "date": "...", "score": 71, "niveau": "B1"},
  "concept_weights": {"present_simple": 2, "past_simple": 3},
  "concept_groups": {"Module 1": [...], "Module 2": [...]},
  "error_exam_eligible": false,
  "learner_profile_json": "{}",
  "learner_profile_summary": ""
}
```

### `dify-exam-scoring` POST request (verbatim sample)
```json
{
  "username": "user_123",
  "domain": "en",
  "niveau": "B1",
  "concept_keys": ["past_perfect", "conditionals", "phrasal_verbs"],
  "module_index": 0,
  "module_total": 2,
  "exam_responses": [{"q": 1, "answer": "..."}, ...]
}
```

Response : `{passed, total_score, concept_scores, commentaire, to_review[]}`.

## DB schema critique : `profils_eleves`

```sql
CREATE TABLE profils_eleves (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255),
  domain VARCHAR(10),  -- 'en', 'es', 'it', etc
  profil_formate TEXT,
  concept_keys JSONB,
  scores_confiance JSONB,
  mode_apprentissage VARCHAR(50),
  next_concept_keys JSONB,
  next_niveau VARCHAR(5),
  examen_en_cours JSONB,
  dernier_examen JSONB,
  nb_examens_niveau INT,
  sessions_depuis_examen INT,
  concept_weights JSONB,
  concept_groups JSONB,
  session_snapshot TEXT,
  error_exam_eligible BOOLEAN,
  learner_profile_json JSONB,
  learner_profile_summary TEXT,
  UNIQUE(username, domain)
);
```

---

# 4. DATA layer YAMLs (per-language)

| File | Schema | Top keys | Entries EN |
|---|---|---|---|
| `curriculum_<lang>.yaml` | CurriculumPack | domain + A1/A2/B1/B2/C1/C2 | 131 (105 pre-S53 + 26 Hawkins audit) |
| `concept_hints/<lang>.yaml` | ConceptHintsPack (Lax) | dict concept_key → hint | 131 (100% coverage curriculum) |
| `rubrics/<lang>.yaml` | RubricPack | dict CEFR → prose | 6 rubrics |
| `fewshots/<lang>.yaml` | FewshotPack | fewshots[] + anti_patterns[] | 14-16 fewshots + N anti-patterns |
| `cefr_diagnostics/<lang>.yaml` | CEFRDiagnosticsPack (Lax) | paliers_first_question + paliers_reference | 2 dicts |
| `functions/<lang>.yaml` | FunctionsPack | domain + A1-C2 | 10 (A1-A2 stub, S53 Phase D1) |
| `micro_lessons/<lang>.yaml` | MicroLessonPack | family → {A1, A2, B1} | TBD |
| `mini_exam/<lang>_*.yaml` | MiniExamBank | level + lang + items[] | 4 files A1-B2, ~15 items each |
| `l1_transfer/fr_to_<lang>.yaml` | L1TransferPack | l1 + target + transfers[] | 12 |
| `tolerance_matrix/*.yaml` | Dict | per-error rules | shared lang-agnostic |
| `onboarding/overlays/<lang>.yaml` | Dict | shared core + lang overlay | shared |

## Curriculum structure (verbatim top)

```yaml
domain: en
A1:
  description: "Survival — greet, introduce, request basic info..."
  concept_keys: [present_simple_basic, articles_a_an_the, ...]
  concept_weights: {present_simple_basic: 5, ...}
  concept_groups: {grammar: [...], nouns_articles: [...], ...}
A2: {...}
B1: {...}
[etc]
```

---

# 5. EXTRACTED authority anchors EN

| Source | Path | YAMLs produced | Consumption |
|---|---|---|---|
| **Hawkins & Filipović 2012** *Criterial Features L2 English* | `extracted/hawkins-filipovic-2012-criterial-features-l2-english/` | `criterial-features-by-level.yaml` | Audit `curriculum_en` Phase B4 S53 → +26 concepts |
| **CEFR Companion 2020** | `extracted/coe-2020-cefr-companion-volume/` | `salient-features-by-level.yaml` + `changes-2001-to-2020.yaml` | Authority reference inclusivity wording (C2 "highly successful learner") |
| **Lyster 2007** *Counterbalanced* | `extracted/lyster-2007-counterbalanced-content/` | `cf-taxonomy.yaml` + `counterbalanced-principle.yaml` | Judge `llm_pairwise.py` CF move 10-class enum + cf_classifier.py grounding |
| **Lightbown & Spada 2021** | `extracted/lightbown-spada-2021-how-languages-learned/` | `ch5-additional-observations.yaml` + `ch5-cf-observation-schemes.yaml` + `ch6-six-proposals.yaml` | CF strategy theoretical grounding |

---

# 6. ORACLE infrastructure

## Harness pipeline

**File** : `/opt/academie/scripts/oracle/harness.py`

```
python3 scripts/oracle/harness.py --agent teacher_en --mode [lint|smoke|full]
  --panel [off|cross-provider]
  --cache [on|off]
```

**Flow** : `discover_scenarios()` → `score_scenario()` → `run_lint()` + `fetch_current_response()` (Dify API) + `deterministic.score_all()` + `llm_pairwise.score_all()` (3 dims × n_votes=5) → `_persist_run_to_db()`

## Judges architecture

| Judge | File | Role | Dims |
|---|---|---|---|
| `deterministic.py` | scripts/oracle/judges/ | Structural validation no LLM | cf_move_set_valid, scaffolding_flags_honored, recast_saliency_and_dosage |
| `llm_pairwise.py` | scripts/oracle/judges/ | LLM dim scoring | cf_move_set_valid (LLM), register_cefr_alignment, semantic_fidelity_pairwise |
| `dify_client.py` | scripts/oracle/judges/ | Dify public API dispatch | (fetch bot response) |

**Judge prompts dans `llm_pairwise.py`** :
- `CF_MOVE_PROMPT` v2 (S54 P3.5) : decision tree + 7 EN fewshots + 5 ES fewshots cross-lang (S55 G3)
- `PAIRWISE_PROMPT` (S55 G4) : multi-error tolerance + doctrinal anti-pattern detection
- `CEFR_REGISTER_PROMPT` : language-agnostic CEFR pitch classifier

## Cache + AC2 + κ

| Tool | File | Formula | Purpose |
|---|---|---|---|
| **SQLite cache** | `cache.py` | sha256(messages JSON + model) | content-addressed, TTL 30d, 4× speedup |
| **Gwet AC2** | `kappa/ac2.py` | AC2 = (Po-Pe)/(1-Pe), Pe via marginal homogeneity | multi-rater n_votes=5 + bootstrap CI |
| **Cohen κ** | `kappa/compute_kappa.py` | κ = (Po-Pe)/(1-Pe), classical | reference (paradox-prone on skew) |

## Scenarios EN (26 total)

Coverage CEFR × tier × error_category :
| CEFR | T1 | T2 | T3 | T4 | Risk | EL | Total |
|---|---|---|---|---|---|---|---|
| A1 | — | 1 | — | — | 1 | 4 | 6 |
| A2 | — | 2 | 1 | — | — | — | 3 |
| B1 | — | 1 | 3 | — | — | — | 4 |
| B2 | — | 1 | 2 | — | — | — | 3 |
| C1 | — | — | 3 | — | — | — | 3 |
| Multi | — | — | — | — | — | — | 4 |

## ScenarioSchema (Pydantic strict)

```yaml
id: a2_t2_past_simple_001
source: handcrafted
scenario_key:
  agent: teacher_en
  cefr: A2
  target_tier: T2
  error_category: verb_tense
  fla: low
  style_profile: direct
multi_turn: false
turns:
  - role: learner
    text: "Last weekend I goed to the cinema..."
    turn_number: 5
    expected_errors: [V:INFL]
expected_dimensions:
  cf_move_set_valid:
    mode: set_membership
    acceptable: [full_recast, partial_recast, ...]
    forbidden: [explicit_correction]
  scaffolding_flags_honored:
    mode: all_required
    l2_ratio_band: [0.85, 1.0]
```

---

# 7. TESTS pytest

268 test functions across 18 files. Key Teacher EN tests :
- `test_teacher_prompt.py::test_a1_never_emits_metalinguistic` : A1 hard constraint
- `test_teacher_prompt.py::test_a2_t3_default_elicitation` : A2 T3 default move
- `test_scaffolding_policy.py` : 33 tests Hawkins A1/A2/B1 progression
- `test_yaml_parity.py::test_all_levels_covered` : 6 CEFR per lang
- `test_cf_classifier.py` : Lyster 10-move taxonomy validation

---

# 8. SPRINT MVP COMPLETE (S54) — DoD criteria

| DoD | Status | Evidence |
|---|---|---|
| Score 22-24/26 stable cross 3+ runs | ✅ | S54 baseline 22/26 |
| Cross-judge AC2 ≥ 0.7 | ✅ | Panel cerebras+mistral+gemini cross-provider 0.66+ |
| Run-to-run AC2 ≥ 0.7 | ✅ | Cache + temperature=0 reproducible |
| κ vs manual ≥ 0.7 | ✅ | gemini baseline 0.84 |
| 0 stable structural fails | ❌ partial | 2 known fails (b2_passive, b1_prep) |
| Capacity 5-10 runs/day | ✅ | Cerebras 14400 RPD × cache → 12+ runs feasible |

---

# 🌐 PER-LANGUAGE ADAPTATION GUIDE (Wave 2-4 build)

Pour chaque nouvelle langue (IT, DE, RU, JP), suivre ce gabarit :

## A. KEEP (shared, lang-agnostic — pas de modif requise)

- Backend Python pipeline `chat_router.py` (polymorphic via AgentDef)
- Pedagogy modules (`scaffolding_policy.py`, `priority_loop.py`, `consolidation.py`, `three_strikes.py`, `teacher_prompt.py`) — params lang-aware déjà
- Tolerance matrix (lang-agnostic codes)
- PII scrubber, token budget waterfall, streak/session/XP hooks
- Oracle harness (lang-agnostic via `--agent <slug>_<lang>`)
- Judge prompts CF_MOVE / PAIRWISE / CEFR_REGISTER (Lyster taxonomy universelle)
- Pydantic schemas (loader.py validators)

## B. ADD (per-lang creation required)

### Data layer YAMLs (mandatory)
- [ ] `curriculum_<lang>.yaml` — A1-C2 concepts (target 100-150 per ADR-013 scope)
- [ ] `concept_hints/<lang>.yaml` — 100% coverage curriculum
- [ ] `rubrics/<lang>.yaml` — 6 rubrics A1-C2
- [ ] `fewshots/<lang>.yaml` — 12-22 fewshots stratifiés CEFR × CF type
- [ ] `cefr_diagnostics/<lang>.yaml` — paliers 1ère question + reference
- [ ] `mini_exam/<lang>_*.yaml` — A1-B2 (4 files Wave 2 IT/DE per ADR-013)
- [ ] `micro_lessons/<lang>.yaml` — family × {A1, A2, B1}
- [ ] `l1_transfer/fr_to_<lang>.yaml` — calques + transfer multipliers
- [ ] `onboarding/overlays/<lang>.yaml` — copy localisation

### Detector code (mandatory)
- [ ] `taxonomy/rules_<lang>.py` — error code detection (V:TENSE, V:FORM, V:SVA, V:ASPECT, etc + lang-specific codes ex JP : KEIGO_FORM, PARTICLE_WO_GA)
  - **Wave 2 IT/DE** : regex + spaCy (parity Teacher EN)
  - **Wave 3 JP** : SudachiPy/GiNZA tokenizer (no spaCy native JP) + custom JP morphology
  - **Wave 4 RU** : pymorphy3 + spaCy + russian morphology

### Authority anchor extraction (mandatory)
- **EN**: Hawkins + CoE Companion 2020 → already done
- **ES**: PCIC Cervantes A1-A2 + B1-B2 → done S53, **C1-C2 pending**
- **IT**: CILS Sillabo + Profile Italiano (Wave 2)
- **DE**: Profile Deutsch (Glaboniat 2005) + CEFR Companion 2020 (Wave 2)
- **JP**: JFS Standard (Japan Foundation 2024) + Marugoto (Wave 3, ADR-015)
- **RU**: TORFL Lexical/Grammatical Minimums (Pushkin Institute) + Antonova Doroga (Wave 4)

### Dify workflow (mandatory)
- [ ] Create app + workflow JSON (clone Teacher EN structure 41 nodes)
- [ ] Translate 4 LLM system prompts (plan_choice, onboarding, session, exam) — lang-target persona
- [ ] Update `lang_target_name` + `lang_target_prof` defaults in start node
- [ ] Verify variable wiring (23 input vars same)
- [ ] Test webhook contracts → n8n (same payload format, just `domain` field changes)

### agents_config.py (mandatory)
- [ ] Add `AgentDef("<slug>", "<lang>", "DIFY_KEY_<UPPER>", "<Display Name>", "<dify_app_id>")`
  - IT : professore + DIFY_KEY_PROFESSORE
  - DE : lehrer + DIFY_KEY_LEHRER
  - JP : sensei + DIFY_KEY_SENSEI
  - RU : prepodavatel + DIFY_KEY_PREPODAVATEL

### Oracle scenarios (mandatory)
- [ ] `scripts/oracle/scenarios/<agent>_<lang>/` : 24-30 scenarios stratifiés CEFR × tier
- [ ] `scripts/oracle/scenarios/<agent>_<lang>/golden/` : record via `record_golden.py --agent <agent>_<lang> --apply`

## C. ADAPT (per-lang specific overrides)

### typological_distance.py
- [ ] Add FR-{IT,DE,JP,RU} pairs (already done in `_DISTANCE_TABLE`)
- IT : close (Romance siblings)
- DE : medium (Germanic)
- JP : distant (isolate, agglutinative)
- RU : distant (Cyrillic, fusional)

### scaffolding_policy.py — PolicyRow matrix
Verify defaults applicables. Distance-aware automatically. Si nouveau pattern (ex JP keigo register switch) : add row.

### Judge fewshots (recommended)
Lyster taxonomy universelle MAIS patterns linguistiques diffèrent. Ajouter dans `CF_MOVE_PROMPT` (file `llm_pairwise.py`) une section per-target-lang fewshots :
- ES : 5 fewshots done S55 G3 (`9a589cb`)
- IT : add 5 fewshots Wave 2 (`congiuntivo`, `passato remoto`, `aggettivi`, etc)
- DE : add 5 fewshots Wave 2 (Konjunktiv II, V2, Präteritum, etc)
- JP : add 5 fewshots Wave 3 (keigo, particles wo/ga, te-form, etc)
- RU : add 5 fewshots Wave 4 (cases, aspect, motion verbs, etc)

### Tolerance matrix — error codes
v2 currently lang-agnostic. Ajouter lang-specific codes si nécessaire :
- JP : KEIGO_FORM (T2 if minor / T4 if breakdown), PARTICLE_WO_GA (T3 systematic)
- RU : CASE_GENITIVE_OF_NEGATION (T3), VERB_ASPECT_PERF_IMPERF (T2-T3)

### l1_transfer
FR→target multipliers based on typological distance + cognate/false-friend density :
- FR-IT : multipliers 1.4-1.8 (high cognate density)
- FR-DE : 1.2-1.6 (mixed Germanic/Latin)
- FR-JP : 1.0-1.3 (low transfer)
- FR-RU : 1.0-1.4 (low transfer except scientific lexicon)

## D. SPECIAL CASES

### JP — Wave 3 (ADR-015 productive eval JFS Standard)
- Tokenizer : **NOT spaCy native**. Use SudachiPy or GiNZA (Japanese morphological analyzer)
- Authority anchors : JFS Standard 2024 + Marugoto Elementary 1+2 + Marugoto Pre-Intermediate (B1) + Tobira (B2)
- ADR-013 cap A1-B2 : `curriculum_jp.yaml` covers JLPT N5-N3 equivalent
- Specific dims : keigo register accuracy, particle wo/ga discrimination, te-form chains

### RU — Wave 4
- Tokenizer : pymorphy3 + spaCy russian model
- Authority anchors : TORFL Lexical Min + TORFL Grammar Min (Pushkin Institute, free PDF) + Antonova Doroga A1-B1 + Wade Comprehensive Russian Grammar (lookup-only)
- ADR-013 cap A1-B2 : `curriculum_ru.yaml` covers TORFL TEU-TBU-TRKI-1 equivalent
- Specific dims : case agreement, verb aspect (perfective/imperfective), motion verbs

### IT — Wave 2
- spaCy native it_core_news_sm
- Authority anchors : CILS Sillabo (Università per Stranieri Siena) + Profilo della lingua italiana (Loescher free) + Maiden grammar lookup-only
- ADR-013 cap A1-B2 : `curriculum_it.yaml` ~80-100 concepts

### DE — Wave 2
- spaCy native de_core_news_sm
- Authority anchors : Profile Deutsch (Glaboniat 2005) + CEFR Companion 2020 + Helbig-Buscha Valenztheorie lookup-only + LanguageTool 3000 rules
- ADR-013 cap A1-B2 : `curriculum_de.yaml` ~80-100 concepts

---

# 📋 BUILD WORKFLOW per Wave (3-step recipe)

Pour chaque nouvelle langue, suivre cet ordre :

## Step 1 : Foundation (~5-7j)
1. Acquire authority anchors (Sinse manual download free PDFs)
2. Extract authority → `data/extracted/<book-slug>/*.yaml` (WebFetch ou manual)
3. Build `curriculum_<lang>.yaml` (audit vs authority, target 80-150 concepts)
4. Build `concept_hints/<lang>.yaml` (100% coverage curriculum)
5. Build `rubrics/<lang>.yaml` (6 rubrics A1-C2 per CEFR scaffolding policy)
6. Build `cefr_diagnostics/<lang>.yaml` (paliers 1ère Q + ref)

## Step 2 : Detector + scaffolding (~3-5j)
7. Build `taxonomy/rules_<lang>.py` (regex + tokenizer per-lang)
8. Build `fewshots/<lang>.yaml` (12-22 fewshots Lyster cells stratifiés)
9. Build `mini_exam/<lang>_*.yaml` (4 files A1-B2 stratifiés exam types)
10. Build `l1_transfer/fr_to_<lang>.yaml` (FR calques)
11. Build `micro_lessons/<lang>.yaml` (family × CEFR triplets)
12. Update `tolerance_matrix_v2_overrides.yaml` if lang-specific codes

## Step 3 : Dify + Oracle + tests (~4-6j)
13. Create Dify app + workflow JSON (clone Teacher EN, translate prompts)
14. Add `AgentDef` row in `agents_config.py`
15. Run smoke `harness.py --agent <slug>_<lang> --mode smoke`
16. Build 24+ oracle scenarios `scripts/oracle/scenarios/<agent>_<lang>/`
17. Record goldens `record_golden.py --agent <slug>_<lang> --apply`
18. Run battery `--mode full --panel cross-provider --cache on`
19. κ Opus calibration + AC2 metrics (DoD ≥0.7)
20. Add 5 lang fewshots to `CF_MOVE_PROMPT` cross-lang
21. Add `test_<lang>_content_pack.py` Pydantic validation tests

**Total per-langue effort** : ~12-18j (Wave 2 IT/DE) ; ~20-28j (Wave 3 JP, custom tokenizer + ADR-015 productive eval) ; ~16-22j (Wave 4 RU, pymorphy3 setup).

---

# Cross-references

- Sprint plan Maestro ES Phase 1+ : `docs/00-project/sprint-maestro-es-2026-05.md` (v2 pivot Build avant Measure)
- Build gap audit Maestro ES : `docs/audit/2026-05-01-maestro-es-vs-teacher-en-build-gap.md`
- Sprint Oracle EN MVP S54 : `docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`
- ADR-013 language scope by tier : `docs/05-decisions/ADR-013-language-scope-by-tier.md`
- ADR-014 structured knowledge extraction : `docs/05-decisions/ADR-014-structured-knowledge-extraction.md`
- ADR-015 JP productive eval JFS Standard : `docs/05-decisions/ADR-015-jp-productive-evaluation-strategy.md`
- ADR-016 authority anchor cross-lang : `docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`
- Vault books library : `vault/knowledge/books/USAGE-MAP.md`
- Vault multilang roadmap : `vault/knowledge/methodology/multilang-roadmap.md`

---

**Single source of truth pour build IT/DE/RU/JP**. Mise à jour incrémentale au fur et à mesure des Wave 2-4 livrées. Cross-validate vs sprint plans + ADRs avant chaque nouveau wave start.
