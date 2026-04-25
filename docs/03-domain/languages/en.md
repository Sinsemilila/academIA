---
title: Teacher EN — LanguageDomain(lang="en")
status: authoritative
last_reviewed: 2026-04-15
---

# Teacher EN — LanguageDomain(lang="en")

> Spécificités du Teacher anglais actuel (état production avril 2026) et cible avec la refonte taxonomie v2.

## État actuel (avril 2026)

### Chatflow Dify

- **Type** : Chatflow (advanced-chat) — **seul chatflow actif dans Dify**
- **App ID** : `39565197-c9d1-4d5b-b66f-18925de236d9`
- **Workflow IDs** :
  - Published : `c52a451f-e381-46f1-a23a-077197b0fccb`
  - Draft : `ed0d1c91-8c9a-48ad-9c3a-063981f8da87`
- **Architecture** : **41 nodes, 45 edges** (scan 2026-04-15)
- **Volumétrie** : 125 conversations, **1693 messages** (97.8% du trafic Dify total)
- **Source de vérité** : `/opt/academie/scripts/update_teacher_chatflow.py` (2097 lignes) + `update_teacher_onboarding.py`
- **Autres agents Dify** : Maestro/Sensei/Lehrer/Professore/PyMentor/CyberMentor existent en mode `chat` simple (pas chatflow), plus une app test `cccccccc` à cleanup

### Distribution des nodes (41 total)

| Type | Count | Nommages clés |
|---|---|---|
| `code` | 9 | code_profil_check, code_turn_check, code_check, code_eval_check, code_exam_detect, code_exam_track, code_exam_persist, code_exam_bilan, parse_snapshot |
| `assigner` | 8 | (variables de conversation) |
| `http-request` | 7 | http_diagnostic, http_snapshot, http_profil_update, http_exam_scoring, http_exam_persist, http_scoring_recovery_clear, Requête HTTP (profil-get) |
| `if-else` | 7 | if_exam_active, if_resume_exam, if_snap, if_profil, if_first_turn, if_eval_ready, (+1) |
| `answer` | 5 | answer_onboarding, answer_session, answer_plan, answer_exam, answer_exam_bilan |
| `llm` | 4 | llm_onboarding, llm_session, llm_plan_choice, llm_exam |
| `start` | 1 | Start node (3 inputs : minutes_since_last, mock_exam, mode_override) |

### HTTP nodes externes (7 URLs appelées)

| Title | URL |
|---|---|
| Requête HTTP (profil-get) | `http://n8n-academie:5678/webhook/dify-profil-get?username={{sys.user_id}}&domaine=anglais` |
| Snapshot session | `http://n8n-academie:5678/webhook/dify-snapshot` |
| Maj profil élève | `http://n8n-academie:5678/webhook/dify-profil-update` |
| Diagnostic CECRL | `http://n8n-academie:5678/webhook/dify-diagnostic` |
| Score Exam (n8n) | `http://n8n-academie:5678/webhook/dify-exam-scoring` |
| Persist Exam (n8n) | `http://n8n-academie:5678/webhook/dify-exam-persist` |
| Clear Scoring Stuck (n8n) | `http://n8n-academie:5678/webhook/dify-exam-persist` |

### Conversation variables (15 total)

| Nom | Type | Default | Rôle |
|---|---|---|---|
| `exam_mode` | string | `off` | off / intro / active / scoring |
| `review_mode` | string | `""` | active si révision |
| `exam_modules` | string (JSON) | `[]` | Modules d'examen |
| `exam_niveau_to` | string | `""` | Niveau cible (gelé au EXAM_START) |
| `exam_niveau_from` | string | `""` | Niveau départ (évite hallucination post-promotion) |
| `exam_responses` | string (JSON) | `[]` | Réponses examen |
| `exam_module_name` | string | `""` | Module en cours |
| `exam_module_index` | integer | `0` | Index module (0-based) |
| `exam_module_total` | integer | `0` | Nombre modules |
| `exam_module_concepts` | string | `""` | Concepts+poids module |
| `exam_question_num` | integer | `0` | Numéro question |
| `exam_total_questions` | integer | `0` | Total questions du module |
| `nb_interactions` | integer | `0` | Interactions session courante |
| `session_snapshot` | string | `""` | Résumé glissant |
| (+ autres) | | | |

### Modèles LLM

- **Session courante** : `gpt-4o-mini` (free tier OpenAI) via LiteLLM
- **Onboarding** : `gpt-4o-mini` avec fallback groq-standard via LiteLLM
- **Exam mode** : `gpt-4o-mini` (meilleure qualité, même quand token budget dépassé)
- **Error analysis** : `ft:gpt-4o-mini-2024-07-18:personal:academie-errors-v3:DU6GUv6v` (paid)

### Nodes clés

- **Start node** : 3 inputs (`minutes_since_last`, `mock_exam`, `mode_override`)
- **HTTP Request au start** → `/webhook/dify-profil-get` (n8n) → profil injecté via Jinja2 dans system prompt
- **code_turn_check** : logique déterministe Python — focus_concept, concept_modes, mock_exam parsing, is_first_turn
- **code_profil_check** : validation profil présent
- **code_check** : branchement mode (onboarding vs session vs exam)
- **llm_onboarding** / **llm_session** / **llm_exam** : 3 paths LLM selon le mode
- **code_eval_check** : strip marker `[EVAL_READY]`, fallback FR si marker seul (cf. [`_legacy/` ou commit history pour contexte](../../_legacy/))
- **if_eval_ready** : conditionnel pour déclencher diagnostic
- **http_diagnostic** : appel n8n `/webhook/dify-diagnostic` après onboarding

### Mode exam

- Déclenché via bouton Quiz côté webapp
- 10 questions, feedback immédiat, score final
- 6 types de questions issus de Cambridge CECRL research : FILL/CORRECT/TRANSFORM/CHOICE/FORM/PRODUCE
- Examens modulaires avec poids par concept
- Progression multi-module (A1 = 43q → C2 = 56q)

### Onboarding

- **Phase 1 FR** (tours 1-3) : collecte nom + motivation + préférence correction + auto-évaluation + centres d'intérêt + style
- **Phase 2 EN** (tours 4-10+) : diagnostic CECRL, questions de difficulté croissante
- **Marqueur `[EVAL_READY]`** : signale la fin du diagnostic, déclenche n8n scoring CECRL
- **Fallback** si LLM envoie `[EVAL_READY]` seul : message FR générique "Merci pour tes réponses ! Envoie-moi **ok** pour découvrir ton bilan de niveau." (cf. fix Session 11, 2026-04-15)

### Taxonomie actuelle utilisée

Matrice `tolerance_matrix.yaml` v1 : 12 familles, 57 codes, 4 bandes CECRL (beginner/intermediate/upper/advanced), 4 tiers (ignored/shadow/noted/penalized).

Rules layer : `webapp/backend/app/error_taxonomy/rules.py` (754 lignes, 98% coverage A1-C1, 43 tests).

## Cible v2 (post-refonte)

Teacher EN devient **`LanguageDomain(lang="en")`** (cf. [`02-architecture/shared-core.md`](../../02-architecture/shared-core.md)).

### Changements

| Aspect | Avant (v1) | Après (v2) |
|---|---|---|
| Chatflow Dify | `Teacher` dédié 28 nodes | `language-tutor` paramétré (minimaliste) |
| Prompt système | Hardcoded EN dans chatflow | Généré par `academie-core` + injecté |
| Bandes CECRL | 4 (beginner/intermediate/upper/advanced) | 6 pures (A1/A2/B1/B2/C1/C2) |
| Tiers | 4 (ignored/shadow/noted/penalized) | 5 (T0/T1/T2/T3/T4) |
| Poids | 0.0 / 0.3 / 0.8 (arbitraires) | Calibrés empiriquement (GLMM + GRM) |
| Gravity | Non modélisée | 3 axes (linguistic/communicative/social) |
| L1 transfer | Non modélisée | Multiplicateurs `l1_transfer_multipliers.yaml` |
| Feedback type | Majoritairement recast | Mapping tier → Lyster (recast/elicitation/metalinguistic/prompt) |
| Dosage | Libre, variable selon prompt | Max corrections/tour selon niveau (cf. [`01-pedagogy/feedback-delivery.md`](../../01-pedagogy/feedback-delivery.md)) |
| Anti-drift | Aucun | Re-injection rubric toutes les 5 interactions |

### Criterial features sources

Pour calibrer `emergence_level` et `mastery_level` des concepts EN :

- **English Grammar Profile (EGP)** — 1222 features — [englishprofile.org](https://englishprofile.org/english-grammar/)
- **English Vocabulary Profile (EVP)** — ~7000 mots/sens — [englishprofile.org/?menu=evp-online](https://englishprofile.org/?menu=evp-online)
- **Cambridge Learner Corpus (CLC)** — privé, via Write & Improve Corpus 2024 public

Format de stockage : `academie-core/data/cefr_criterial_features/en.yaml`.

### Curriculum actuel

92 concepts dans `curriculums` table (A1 = 18, A2 = 18, B1 = 20, B2 = 14, C1 = 15, C2 = 7). Source : `/opt/academie-shared/curriculum_en.yaml` (skeleton original Gemini CLI 2026-04-05, enrichi par sessions ultérieures).

À auditer contre EGP pour vérifier alignement avec criterial features Cambridge.

### Personnalité d'agent

Teacher EN a une personnalité dédiée (ton amical, usage du tu, centré sur feedback constructif). Paramétrée dans le system prompt.

Adaptations par user via `profils_eleves.personnalite` :
- `centres_interet` : choisir exemples qui parlent à l'élève
- `style_correction` : modérer explicit/implicit ratio

## Endpoints API liés

- `POST /api/chat/send?agent=teacher` — envoyer un message au Teacher
- `GET /api/chat/conversations?agent=teacher` — liste conversations
- `GET /api/chat/messages?agent=teacher&conversation_id=X` — messages d'une conversation
- `POST /api/chat/exam-start?agent=teacher` — déclencher mode exam
- `GET /api/profile/anglais` — profil user pour Teacher

## Mapping Dify user_id ↔ AcademIA user_id

- **sys.user_id** dans chatflow = UUID compte Dify (pas username)
- Table `eleves.dify_user_id` fait le mapping
- Résolution dans les workflows n8n via query `SELECT username FROM eleves WHERE dify_user_id = $1`

## Intégrations n8n

- `dify-profil-get` : fetch profil au start de chaque conversation
- `dify-snapshot` : génération snapshot toutes les 10 interactions
- `dify-profil-update` : update profil en fin de session
- `dify-diagnostic` : scoring CECRL post-onboarding
- `dify-exam-scoring` : scoring mode exam

## Observabilité actuelle

- Token usage trackés dans `token_usage_daily` (local) + `LiteLLM_SpendLogs` (truth)
- Widget admin `/admin` affiche quota journalier gpt-4o-mini + cost ft:gpt-4o-mini-v3
- Error log dans `error_log` (via rules + LLM analysis)
- Snapshots dans `snapshots_session` (every 10 interactions)

## Known issues / gotchas

- **Alignment drift** potentiel en conversations longues (Pak 2025) — mitigation prévue Sprint 3
- **`var_assigner` Dify** : l'opération "set" ne supporte pas `input_type: "variable"` — utiliser "over-write" mode (bug connu Dify)
- **`code_eval_check` fallback** : si LLM envoie `[EVAL_READY]` seul, fallback FR implémenté (Session 11)

## Références

- [../../01-pedagogy/cefr-language-instance.md](../../01-pedagogy/cefr-language-instance.md) — instance LanguageDomain générique
- [../../02-architecture/agent-topology.md](../../02-architecture/agent-topology.md) — migration vers `language-tutor`
- [../../01-pedagogy/feedback-delivery.md](../../01-pedagogy/feedback-delivery.md) — pédagogie Lyster
- [../../_legacy/dify-teacher.md](../../_legacy/dify-teacher.md) — version legacy (historique)
- Scripts : `/opt/academie/scripts/update_teacher_chatflow.py`, `update_teacher_onboarding.py`
