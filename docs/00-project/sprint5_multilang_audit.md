---
title: Sprint 5 — Audit Multi-Langue
date: 2026-04-18
status: active
last_reviewed: 2026-04-18
author: Claude (Opus 4.7) — Session 26
---

# Audit Multi-Langue AcademIA — Post-Sprint 5 Infra

**Contexte** : Sprint 5 infra (commit `33a862a`) a externalisé les YAML data EN et introduit `_DOMAIN_REGISTRY` dans `chat_router.py`. Cet audit couvre les **5 surfaces restantes** à nettoyer avant de lancer Maestro ES, avec analyse du fine-tune v3 et stratégie CEFR.

---

## TL;DR

- **Critical path restant** : ~15-20h pour un env propre multi-domaine (hors content pack ES).
- **1 bloquant DB critique** : `error_log.domaine` manquante (impossible de scoper erreurs par langue).
- **11 SQL hardcodés** dans backend, **14 defaults hardcodés** frontend, **3 workflows n8n** avec prompt/App ID EN.
- **Dify chatflow** : 4 LLM nodes persona EN + 20 concept hints EN → candidat au `language-tutor` generic shell (2-3j).
- **Fine-tune v3** : toujours en prod (89/137 error rows), **pas obsolète**. Pour ES : base `gpt-4o-mini` + prompt ES (Option B) au lancement, re-fine-tune plus tard.
- **CEFR** : sourcer les descripteurs natifs (PCIC pour ES, CILS pour IT, Profile Deutsch pour DE, JF Standard pour JP) — **pas** traduire depuis EN.

---

## PART 1 — État post-Sprint 5 infra

### Acquis (commit `33a862a`)

- `_DOMAIN_REGISTRY: dict[str, tuple[str, LanguageDomain]]` dans `chat_router.py` — registry keyed by agent (`"teacher"` → `("anglais", LanguageDomain("en"))`)
- `domaine` DB string paramétré partout dans `chat_router.py` (4 call sites)
- `RUBRICS` / `FEWSHOT_BANK` / `L1_TRANSFER_SEED` externalisés depuis `teacher_prompt.py` vers YAML :
  - `packages/academie-core/academie_core/data/rubrics/en.yaml`
  - `packages/academie-core/academie_core/data/fewshots/en.yaml`
  - `packages/academie-core/academie_core/data/l1_transfer/fr_to_en.yaml`
  - `packages/academie-core/academie_core/data/l1_transfer/l1_names.yaml`
- `data/loader.py` : chargement YAML dynamique par `lang_target`
- `build_l1_watch()` lit `{l1}_to_{lang}.yaml` dynamiquement
- Lang guards défensifs dans `rules.py` / `llm.py` (return empty si lang≠"en")
- 102 tests pass

**Ajout d'une nouvelle langue = 3 fichiers YAML + 1 ligne registry + 1 env var `DIFY_KEY_<AGENT>`.**

### Dette résiduelle dans `academie-core` (~5%)

- `taxonomy/rules.py` : détection EN-hardcoded (`FRENCH_COGNATES`, `PREP_CALQUES`, `CONTRACTION_MAP`, `IRREGULAR_PAST_ERRORS`). Pour ES → `rules_es.py` (3-4j linguistique).
- `taxonomy/llm.py` : fine-tune v3 EN-only (voir PART 3).
- `LanguageDomain.snapshot()` : raises `NotImplementedError` (v3+ deferred).
- Legacy `PromptContext` vs `domain/base.py` `PromptContext` pas unifiés.
- `teacher_prompt.py` reste monolithique (696L) — split en `dosage.py`/`rubrics.py`/`fewshots.py` différé.

---

## PART 2 — Audit par surface

### 2.1 Backend webapp — 11 SQL hardcodés

**État** : 🟡 70% ready (post-Sprint 5).

Tous les call sites `chat_router.py` sont OK. Résidus dans les autres routers :

**Profile router** (`webapp/backend/app/routers/profile_router.py`) :
- L67 : `GET /api/profile/l1` — `WHERE eleve_id=$1 AND domaine='anglais'` hardcodé
- L88 : `PUT /api/profile/l1` — idem
- L252 : `GET /api/profile/summary` — idem
- L271/501/528/669 : defaults `domain: str = "anglais"` dans signatures endpoints (acceptable si param query override, mais dette)

**Settings router** (`webapp/backend/app/routers/settings_router.py`) :
- L48 : `PATCH /api/me/profile` — `WHERE domaine='anglais'` hardcodé (jsonb_set personnalite)
- L66 : `PATCH /api/me/mode` — idem
- L105 : `GET /api/me/settings` — idem (SELECT personnalite)
- L179, 187, 200, 210 : 4× `"action": "/chat/teacher"` hardcodés dans JSON responses

**Admin router** (`webapp/backend/app/routers/admin_router.py`) :
- L80 : `LEFT JOIN profils_eleves p ON e.id = p.eleve_id AND p.domaine = 'anglais'` — dashboard EN-only

**Error analysis router** (`webapp/backend/app/routers/error_analysis_router.py`) :
- L27 : `class AnalyzeRequest: domaine: str = "anglais"` — Pydantic default
- L189 : `"action": "/chat/teacher"` hardcodé

**Effort** : 4-6h (regex + param refactor, pas de risque structurel).

---

### 2.2 DB schema — `error_log.domaine` manquante (CRITIQUE)

**État** : 🟡 70% ready.

**Tables avec `domaine` OK** :
- `profils_eleves` (VARCHAR(100) NOT NULL, UNIQUE `(eleve_id, domaine)` ✅)
- `spaced_retrieval_queue` (VARCHAR(50) NOT NULL ✅)
- `snapshots_session` (VARCHAR(100) NOT NULL ✅)
- `historique_sessions` (VARCHAR(100) NOT NULL ✅)
- `curriculums` (VARCHAR(50), UNIQUE `(domaine, niveau)` ✅)

**🔴 Bloquant — `error_log` N'A PAS de colonne `domaine`** :
- 137 rows actuellement, toutes originaires de profils `domaine='anglais'`
- Sans cette colonne, une erreur ES sera indistinguable d'une erreur EN pour le scoring/analytics
- Migration :
  ```sql
  ALTER TABLE error_log ADD COLUMN domaine VARCHAR(50);
  UPDATE error_log SET domaine='anglais' WHERE domaine IS NULL;
  ALTER TABLE error_log ALTER COLUMN domaine SET NOT NULL;
  CREATE INDEX idx_error_log_eleve_domaine ON error_log(eleve_id, domaine, created_at DESC);
  ```

**Dette mineure** :
- `user_sessions` : mapping indirect via `agent_name` (pas `domaine` explicite). Fonctionne mais sous-optimal.
- Pas de `CHECK (domaine IN (...))` constraints → accepte n'importe quelle string.
- Indexes non-optimisés pour queries multi-domaine (recommandations dans plan).

**Effort** : 2h migration + backfill.

---

### 2.3 Frontend SvelteKit — defaults + links hardcodés

**État** : 🟡 80% ready.

**Acquis** :
- `/lib/config.ts` : tous agents (teacher/maestro/sensei/lehrer/professore) déclarés, `available: false` sauf teacher ✅
- Route `/chat/[agent]` paramétrée ✅
- Route `/stats/concepts?domain=` paramétrée ✅

**Dette** :

**API defaults** (`/lib/api.ts`) :
- L124/131/159/165/171/196/266/278 : 8× `domain: string = 'anglais'` defaults
- L203/209 : 2× `agent: string = 'teacher'` defaults
- Problème : callers oublient le param → bug actif sur `stats/+page.svelte:43-47` (affiche anglais même si user sur Maestro)

**Links hardcodés `/chat/teacher`** :
- `Sidebar.svelte:19`
- `CommandPalette.svelte:35` (duplicate avec entries auto-générées)
- `+page.svelte:140, 272, 282`
- `stats/+page.svelte:109`

**Messages EN-centric** :
- `chat/[agent]/+page.svelte:191` : `'Teacher ne répond pas'` hardcodé (devrait être `${agent?.name}`)
- `+page.svelte:127` : `Teacher · Anglais` hardcodé en header

**Manquant** :
- Pas de store `currentAgent` / `currentDomain` → pas de persistence entre pages (user switch chat→stats perd le contexte)

**Effort** : 2-3h minimum (fix defaults + links), +2h pour store navigation persistent.

---

### 2.4 n8n workflows — 3/6 prêts, 3/6 à fixer

**État** : 🟡 50% ready.

**Workflows audités** (container `n8n-postgres`, table `workflow_entity`) :

| Workflow | Nodes | `domaine` param | Issues | Status |
|---|---|---|---|---|
| `dify-profil-get` | 4 | ✅ query param | aucun | ✅ READY |
| `dify-profil-update` | 3 | ✅ webhook body | aucun | ✅ READY |
| `dify-snapshot` | 13 | ✅ webhook body | Dify App ID hardcoded | 🟡 |
| `dify-diagnostic` | 8 | ✅ webhook body | LLM prompt EN + App ID | 🟡 |
| `dify-exam-persist` | 4 | ✅ webhook body | Fallback `|| 'anglais'` | 🟡 |
| `dify-exam-scoring` | 10 | ✅ webhook body | Fallback `|| 'anglais'` + App ID | 🟡 |

**Hardcodes identifiés** :

1. **Dify App ID** `39565197-c9d1-4d5b-b66f-18925de236d9` hardcodé dans 3 workflows (dify-diagnostic, dify-exam-scoring, dify-snapshot — HTTP nodes "Fetch Dify Messages"). **Blocker architectural** : pour ES, il faudra un `app_id` Maestro différent. Solution : table de mapping `agent → app_id` ou env vars n8n.

2. **`dify-diagnostic` node "Build Analysis Prompt"** (jsCode lines 68-111) : 4 strings hardcodés EN :
   - `"professeur d'anglais"`
   - `"apprend l'anglais"`
   - `"questions en anglais"`
   - `"CECRL"` (acceptable — framework européen)

3. **Silent fallbacks** :
   - `dify-exam-persist` node "Build SQL" : `const domaine = (body.domaine || 'anglais')`
   - `dify-exam-scoring` node "Parse Body" : idem

**Bonne nouvelle** : toutes les **SQL queries** sont déjà paramétrées `{{ $json.domaine }}` ✅.

**Effort** : 5-8h (1h fallbacks + 1-2h prompt paramétrage + 2-4h Dify app mapping + 2h tests).

---

### 2.5 Dify chatflow — 41 nodes, EN-heavy

**État** : 🔴 20% ready (structure agnostique, contenu EN-only).

**Chatflow identifié** : Teacher - Professeur d'Anglais (app_id `39565197-c9d1-4d5b-b66f-18925de236d9`), table `workflows` dans DB Dify.

**41 nodes** : 4 LLM + 9 Code + 6 IF-ELSE + 5 HTTP + 5 Variable Assigner + 4 Answer + 1 Start + autres.

**Hardcodes majeurs** :

**4 LLM nodes avec persona EN** :
- `llm_plan_choice` : "Tu es Teacher, prof d'anglais" (L1)
- `llm_session` : "Tu es Teacher, prof d'anglais. Tu tutoies" (L1)
- `llm_onboarding` : "Tu es Teacher, prof d'anglais" + "Tu passes à l'anglais UNIQUEMENT pour la Phase 2" + 40 lignes d'exemples CEFR diagnostics EN
- `llm_exam` : "Tu es un examinateur CECRL" + 6 question types avec exemples EN

**Concept taxonomy EN-only** dans `code_turn_check` (20 concepts hardcodés) :
```
'present_perfect_simple': 'have/has + past participle (I have visited)',
'conditional_2': 'if + past → would (If I had money, I would travel)',
'phrasal_verbs': 'verbes à particule (look up, give in, turn off)',
# ... 17 autres
```

**Inputs manquants au Start node** (14 inputs actuels, manquent) :
- `lang_target` (ex: "en"/"es"/"it")
- `lang_target_name` (ex: "Anglais"/"Espagnol")
- `lang_l1` (actuellement hardcodé FR dans les prompts)

**Autres hardcodes** :
- `code_exam_persist` : `"domaine": "anglais"` ligne 21
- HTTP `dify-profil-get?domaine=anglais` (URL param hardcodé)

**Refactor recommandé** : construire `language-tutor` generic shell (2-3j) qui :
1. Lit `lang_target` depuis Start node
2. Injecte la persona depuis un dict `{lang_target → "prof de X"}` ou variable
3. Query DB/YAML pour concept hints par langue (au lieu de hardcoded dict)
4. Passe `{{lang_target}}` aux HTTP webhooks

**Effort** :
- Shell paramétré (structure Dify) : 2-3j (indépendant du contenu)
- Content pack ES (voir PART 4 + content pack ES séparé) : 6-7j par langue

---

## PART 3 — Fine-tune v3 gpt-4o-mini (analyse complète)

### Identité

- **Modèle** : `ft:gpt-4o-mini-2024-07-18:personal:academie-errors-v3:DU6GUv6v`
- **Disponibilité LiteLLM** : `/opt/litellm/config.yaml.sops` lines 50-52 (v3 + v2 encore présent en fallback)
- **Base model** : `gpt-4o-mini-2024-07-18`
- **Training data** : 5000 examples synthétiques générés via `scripts/generate_v3_training_data.py` (catégories : V:TENSE, PREP:CALQUE, LEX:FALSE, etc. — taxonomie EN)
- **Pipeline fine-tune** : `scripts/launch_finetune_v3.py`
- **F1 baseline** : 85% (mesuré sur `phase1b_battery_1212.py`)

### À quoi il sert

**Layer 2 du error taxonomy pipeline** (complément de `rules.py`) :

```
user message (turn)
  │
  ├─ Layer 1 — rules.py (deterministic, surface errors)
  │    → spelling, apostrophes, simple word order, cognate patterns
  │    → ~35% des rows error_log en prod
  │
  └─ Layer 2 — llm.py monolithic (fine-tune v3)
       → tense, modals, conditionals, agreement, aspect, calques, false friends
       → ~65% des rows error_log en prod
       → monolithic : détecte ET classifie en 1 call
```

**Alimente** :
- `error_log.tier/gravity_*/criterial_level_*` (Sprint 2 scoring v2)
- `compute_error_profile()` → `scores_confiance` par concept (dashboard)
- `l1_transfer_observations` (Sprint 3 Phase 6)
- `spaced_retrieval_queue` (Sprint 3 Phase 7)

### Quand il est déclenché

- **Trigger** : n8n workflow `dify-snapshot` → POST `/internal/analyze-errors` (protected by `INTERNAL_API_TOKEN`)
- **Fréquence** : à chaque session snapshot = toutes les ~10 turns (code node `code_check` dans Dify)
- **Payload** : transcript complet de la session → extraction monolithique de toutes les erreurs user en 1 pass
- **Latence** : 2-4s typique, timeout 30s

### Usage prod actuel (2026-04-18)

```
Error log total : 137 rows (depuis activation)
├─ ft:gpt-4o-mini-v3 : 89 rows (65%)
└─ rules             : 48 rows (35%)

Activité 7 derniers jours :
  2026-04-18 : 3 LLM + 2 rules
  2026-04-16 : 77 LLM + 30 rules   ← gros run battery
  2026-04-15 : 4 LLM + 12 rules
  2026-04-14 : 5 LLM + 4 rules
```

Volume bas (~5-10 calls/jour hors battery) — 6 users famille. Facturation : OpenAI free tier 1.5M tokens/jour, pool partagé avec Teacher chat (`is_openai_billable` dans `chat_router.py:56-60` inclut `ft:gpt-4o-mini-*`).

### Est-il obsolète ?

**NON.** Raisons :

1. **Rien ne l'a remplacé**. Sprint 2/3/4/5 ont changé comment on utilise ses sorties (tier scoring, spaced retrieval, LanguageDomain) — jamais le modèle.
2. Les 89 rows LLM récentes confirment qu'il tourne en prod.
3. Le code `llm.py:250-252` ajoute un **guard défensif Sprint 5** : `if lang != "en": return empty` — il sert TOUJOURS pour EN.
4. Pas de concurrent : sans lui, on retombe à 35% de couverture (rules-only).
5. Sprint 1.5/1.6 GLMM recalibré (commit `0bc40f8` aujourd'hui) produit des weights **appliqués aux sorties du fine-tune v3** — ils sont couplés.

### Stratégie multi-langue

Le fine-tune v3 est **EN-only par construction** (5000 training examples EN). Pour ES/IT/DE/JP :

| Option | Coût | Qualité attendue | Délai |
|---|---|---|---|
| **A — Re-fine-tune par langue** | ~$5 + génération 5000 examples | 85% F1 (match) | 2-3j / langue |
| **B — Base `gpt-4o-mini` + prompt lang-aware** | $0 extra | ~70-80% F1 estimé | 0.5j |
| **C — Rules-only pour ES (skip LLM layer)** | $0 | ~35% couverture | 0j |

**Recommandation** : **Option B au lancement Maestro ES**.
- Refactor `analyze_transcript(lang="es")` :
  ```python
  MODEL_BY_LANG = {
      "en": "ft:gpt-4o-mini-...academie-errors-v3:DU6GUv6v",
      "es": "gpt-4o-mini",  # base for now
  }
  PROMPT_BY_LANG = {"en": SYSTEM_PROMPT_EN, "es": SYSTEM_PROMPT_ES}
  ```
- Basculer vers Option A quand on a ~500 messages ES réels (training data meilleure que synthétique).

**Effort refactor** : 0.5-1j (dispatch lang dans `llm.py` + rédaction `SYSTEM_PROMPT_ES`).

---

## PART 4 — Stratégie CEFR pour multi-langue

### Le bon paradigme : sourcer, pas traduire

Le CEFR est un **meta-framework** (Council of Europe 2001) avec des descripteurs abstraits universels ("Can understand main ideas of complex text"). Ces descripteurs sont **génériques** — l'instantiation concrète (quels tense en A1 EN vs A1 ES ?) dépend de la langue.

**Sources natives existent pour chaque langue** :

| Langue | Source CEFR native | Format | Accès |
|---|---|---|---|
| EN | **English Grammar Profile** (EGP, Cambridge) | Online DB, ~1200 can-do | Open |
| ES | **PCIC** — Plan Curricular Instituto Cervantes | 3 volumes, ~2000 descripteurs | Open web |
| IT | **Sillabo CILS** / Profilo della lingua italiana | PDF officiel Siena | Open |
| DE | **Profile Deutsch** (Goethe Institut) | Livre (ISBN 978-3-468-49493-6) | Payant ~40€ |
| JP | **JF Standard** (Japan Foundation) | Online DB | Open, mapping JLPT↔CEFR approximatif |

### Pourquoi pas traduire EN → ES ?

1. **Disparité des systèmes linguistiques** : un A1 EN maîtrise `to be` / articles / plural-s. Un A1 ES maîtrise déjà genre masc/fém, concordancia básica, ser/estar basique. Traduire EGP EN vers ES produirait un A1 irréaliste.
2. **Calibration corpus-based** : PCIC / Profile Deutsch / CILS sont calibrés sur des corpus d'apprenants natifs (ex: PCIC = CEDEL2, ~1M mots). EGP calibré sur Cambridge Learner Corpus. Non-interchangeables.
3. **Ordre d'acquisition différent** : en allemand A1 inclut Nom/Akk cases (pas en EN). En japonais A1 inclut hiragana+katakana prérequis (pas applicable aux langues romanes).

### Implication opérationnelle

Pour chaque nouvelle langue, le "content pack" nécessite **sourcing humain** (1-2j par langue) :
- Lire l'inventaire officiel (PCIC, CILS, etc.)
- Extraire descripteurs par niveau A1-C2
- Formater en YAML `data/rubrics/{lang}.yaml` selon schema existant (objectif communicatif / règles tolérance par tier / anti-patterns / structures cibles)

Pas de LLM-translate. Pas de port automatique depuis EGP.

**Le `language-tutor` Dify shell et les rubrics YAML sont indépendants** :
- Shell = structure graph Dify paramétrée (2-3j, réutilisable)
- Content pack = sourcing linguistique par langue (1.5-2j rubrics + rules/fewshots/diagnostics/curriculum/l1_transfer)

---

## PART 5 — Plan d'attaque priorisé

### P0 — Bloquants Maestro ES (~8h)

**DB — error_log migration** :
```sql
ALTER TABLE error_log ADD COLUMN domaine VARCHAR(50);
UPDATE error_log SET domaine='anglais' WHERE domaine IS NULL;
ALTER TABLE error_log ALTER COLUMN domaine SET NOT NULL;
CREATE INDEX idx_error_log_eleve_domaine ON error_log(eleve_id, domaine, created_at DESC);
```

**Backend — 11 SQL hardcodés** :
- `profile_router.py:67, 88, 252` — accepter `domain` param + pass WHERE
- `settings_router.py:48, 66, 105` — idem
- `admin_router.py:80` — multi-domaine visibility
- `error_analysis_router.py:27` — Pydantic default required
- 5× `"/chat/teacher"` JSON responses → dynamic `f"/chat/{agent}"`

**Frontend — defaults + links** :
- `lib/api.ts:124, 131, 159, 165, 171, 196, 266, 278` — supprimer defaults ou lier au store
- Fix callers `stats/+page.svelte:43-47` (bug actif : oublient param)
- 6× hardcoded `/chat/teacher` → dynamic
- `chat/[agent]/+page.svelte:191` : `${agent?.name} ne répond pas`

### P1 — Infra multi-domaine propre (~7-10h)

**n8n** :
- Supprimer fallbacks `|| 'anglais'` (dify-exam-persist, dify-exam-scoring)
- Paramétrer prompt `dify-diagnostic` (4 strings EN)
- Implémenter mapping `agent → dify_app_id` (3 workflows affectés)

**Dify minimal** (avant language-tutor) :
- `code_exam_persist` : `"domaine": "anglais"` → `{{lang_target}}`
- HTTP `dify-profil-get?domaine=anglais` → `{{lang_target}}`
- Ajouter 3 inputs Start node : `lang_target`, `lang_target_name`, `lang_l1`
- Paramétrer persona dans 4 LLM nodes

**academie-core** :
- `taxonomy/llm.py` dispatch par lang : `MODEL_BY_LANG` + `PROMPT_BY_LANG` (rend `analyze_transcript` opérationnel pour ES base model)
- **Effort** : 0.5-1j

### P2 — Shell `language-tutor` Dify (~2-3j, infra)

Coquille Dify paramétrée par `lang_target`, consomme YAML en amont. Independant du content pack. Remplace Teacher EN 41-nœuds par un chatflow unique réutilisé pour toutes les langues.

### P3 — Content pack ES Maestro (~6-7j, contenu linguistique)

- `data/rubrics/es.yaml` sourcé PCIC (1.5j)
- `rules_es.py` (3-4j) — gender agreement, ser/estar, subjuntivo triggers, EN→ES calques
- `data/fewshots/es.yaml` (1j) — 14 exemples A1-C2
- `data/l1_transfer/fr_to_es.yaml` (0.5j) — por/para, genre fr vs es, faux amis
- `curriculum_es.yaml` + seed DB (1.5j) — ~80 concepts PCIC
- **Prompt ES pour `gpt-4o-mini` base** (0.5j) — Option B fine-tune
- `LanguageDomain("es")` activation (0.25j)

**Sprint ultérieur** (optionnel) : re-fine-tune `academie-errors-es-v1` quand ~500 msg ES réels disponibles (2-3j).

### P4 — Polish long-terme

- Frontend : store `currentAgent` / `currentDomain` pour persistence navigation (+2h)
- DB : `CHECK (domaine IN (...))` constraints + indexes multi-domaine optimisés (+2h)
- DB : `user_sessions.domaine` colonne explicite (actuellement déduit agent_name)
- `academie-core` dette : unifier `PromptContext` types, split `teacher_prompt.py` en dosage/rubrics/fewshots, implémenter `snapshot()`

---

## Annexes

### A. Commandes utiles

**Accès DB** :
```bash
docker exec postgres-academie psql -U sinse -d academie_db
```

**Vérifier statut Dify chatflow** :
```sql
-- Dans Dify DB
SELECT id, name, mode FROM public.apps WHERE mode = 'advanced-chat';
SELECT app_id, version, graph FROM public.workflows WHERE app_id = '<id>';
```

**Vérifier activité fine-tune v3** :
```sql
SELECT analysis_model, DATE(created_at) d, COUNT(*)
FROM error_log
WHERE created_at > NOW() - INTERVAL '14 days'
GROUP BY analysis_model, DATE(created_at)
ORDER BY d DESC;
```

**Smoke tests** :
```bash
python3 -m pytest packages/academie-core/tests/ scripts/sprint2/tests/ scripts/sprint3/tests/ -q
# → 140/140 pass attendus
```

### B. Fichiers clés à modifier

| Surface | Fichier | Action |
|---|---|---|
| DB | migration SQL | error_log.domaine ADD COLUMN + backfill |
| Backend | `profile_router.py`, `settings_router.py`, `admin_router.py`, `error_analysis_router.py` | 11 hardcodes → param domaine |
| academie-core | `taxonomy/llm.py` | dispatch `MODEL_BY_LANG` + `PROMPT_BY_LANG` |
| academie-core | `taxonomy/rules.py` | créer `rules_es.py` (sprint ES) |
| Frontend | `lib/api.ts` | supprimer defaults + lier au store navigation |
| Frontend | `lib/stores/navigation.ts` (NEW) | `currentAgent` / `currentDomain` |
| Frontend | `Sidebar.svelte`, `CommandPalette.svelte`, `+page.svelte` | dynamic links |
| n8n | workflows `dify-diagnostic`, `dify-exam-*` | prompt + fallback + app_id mapping |
| Dify | Start node, 4 LLM nodes, `code_exam_persist` | lang_target input + parametrage |

### C. Références

- Commit Sprint 5 infra : `33a862a` (2026-04-18)
- Commit GLMM recalibré : `0bc40f8` (2026-04-18, NUCLE 7920 learners)
- Roadmap multi-langue : `docs/00-project/roadmap_multilang.md`
- Session 26 handoff : `SESSION.md`
- ADR académie-core : `docs/05-decisions/ADR-005-academie-core-shared-library.md`

---

_Audit produit via 5 agents parallèles Session 26, synthèse par Opus 4.7 (1M context)._
