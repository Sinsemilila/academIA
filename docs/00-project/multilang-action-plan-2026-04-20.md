---
status: superseded
superseded_by: ADR-013-language-scope-by-tier (2026-04-29) + ADR-016-authority-anchor-cross-lang (2026-04-29)
last_reviewed: 2026-05-01
note: 'Doc research/planning multilang Phase 0 (S26-S33). Conservé pour cross-reference ADRs. Roadmap canonique actuelle = TODO.md macro section + ADR-013/016.'
---

# Multi-langue — plan d'action consolidé

**Date** : 2026-04-20 (Session 33, post-onboarding QCM refonte)
**Source** : audit triple (frontend / backend / Dify+n8n+data) par 3 agents Explore en parallèle
**Objectif** : identifier les blocages pour que le produit soit vraiment multi-langue (EN+ES aujourd'hui → IT/DE/JA/RU demain, + PyMentor/CyberMentor cross-domain)
**Méthode** : lister findings P0/P1/P2 → prioriser → établir checklist répliquable Wave 2+

---

## Executive summary — 7 blockers majeurs

| # | Surface | Finding | Sévérité | Effort |
|---|---|---|---|---|
| 1 | Backend admin | `admin_router.reset_profile()` L121+L152 : `DELETE FROM profils_eleves WHERE eleve_id=$1` sans scoping domain → **wipe de tous les profils** (EN + ES + IT…) d'un user au lieu d'un seul | **P0 data-loss** | 30min |
| 2 | Frontend SkillTree | `SkillTree.svelte:23` : `api.getConcepts()` appelé sans domain → retourne toujours EN même pour un user Maestro | **P0 UX cassée** | 10min |
| 3 | Frontend stats/concepts | `/stats/concepts` utilise `onMount` (pas `$effect`) → ne recharge pas au switch d'agent dans sidebar | **P0 UX cassée** | 10min |
| 4 | Frontend profile | Page `/profile:208,225` contient littéraux "Teacher" hardcodés → orphelin quand user est sur Maestro | **P0 confusing** | 10min |
| 5 | Data content | `curriculum_en.yaml` absent (seul `curriculum_es.yaml` existe) → template manquant, inconsistance schéma bloque Wave 2+ | **P0 structural** | 2h |
| 6 | Backend rules dispatch | `error_analysis_router.py:81` : `detect_errors(text)` sans `lang=` → rules EN toujours appliquées même sur chat ES/IT | **P1 data qualité** | 15min |
| 7 | n8n workflows | 4 workflows (`dify-diagnostic`, `dify-snapshot`, `dify-exam-scoring`, `dify-exam-persist`) sans param `domain` → contamination cross-domain possible + audit trail opaque | **P1 data integrity** | 4h |

**Non-bloquants mais coûteux sans action** : prolifération env vars (`ENABLE_*`, `DIFY_KEY_*` × 6 langues), absence tooling traduction prompts LLM pour clone Wave 2+, pas de validation YAML schémas, 100% UI FR sans infra i18n.

---

## Ce qui est déjà solide (ne pas toucher)

- **DB schema multi-domain** : `profils_eleves`, `learner_profiles`, `error_log`, `curriculums`, `spaced_retrieval_queue`, `snapshots_session`, `historique_sessions` tous scopés `(eleve_id, domain)` avec uniques et index. Session 5 D1 migration complète.
- **Store frontend `lib/stores/navigation.ts`** : `currentAgent` (writable, persisté localStorage) + `currentDomain` (derived ISO). Source de vérité propre.
- **`lib/config.ts`** : `agents[]` avec `slug/name/lang/langGenitive/domain/flagSrc/color/available`. Helpers `domainLabel()` + `domainGenitive()` (ajoutés 2026-04-20).
- **Teacher EN ↔ Maestro ES parité structurelle** : 41 nodes / 45 edges identiques, clone Session 32 + patches Session 33 appliqués symétriquement, conv_vars 3376 chars alignés.
- **`LanguageDomain` class** : instantiable pour n'importe quelle lang sans crash (fail-open gracieux sur YAMLs manquants).
- **`clone_app.py`** : INSERT transactionnel apps + workflows + sites + api_tokens, idempotent, `--dry-run` default. Session 32 l'a validé.
- **Onboarding QCM (Session 33)** : 3 blocs A/B/C, règle de 3 pour PyMentor/CyberMentor. `learner_profiles` table déjà multi-domain.
- **Env flags** : `ENABLE_MAESTRO`, `ENABLE_QCM_ONBOARDING` fonctionnent. Pattern répliquable (même si à factoriser).
- **n8n `dify-profil-get`** : déjà paramétré `domain=$1` en query string (Sprint 5 D1).
- **Tolerance matrix** : shared cross-lang intentionnellement (codes erreurs language-agnostic). OK.

---

## Plan d'action — 3 phases (P0 → P1 → P2)

### Phase A — P0 fixes (doit être fait avant tout merge Wave 2+, ~4h total)

**A1. Fix `admin_router.reset_profile` data-loss bug** (30min, risque data-loss)
- `webapp/backend/app/routers/admin_router.py:121` et `:152` : ajouter paramètre `domain` à l'endpoint + scoper toutes les DELETE à `WHERE eleve_id=$1 AND domain=$2`
- Ajouter un flag optionnel `all_domains: bool = False` pour compat admin ancien cas "reset total user"
- Test : reset profile domain=es ne touche pas la row domain=en
- Rollback : trivial (migration pure de signature)

**A2. Fix frontend SkillTree domain leak** (10min)
- `webapp/frontend/src/lib/components/SkillTree.svelte:23` : passer `$currentDomain` à `api.getConcepts(domain)`. Reactive via `$derived` + `$effect`.

**A3. Fix `/stats/concepts` onMount → $effect** (10min)
- `webapp/frontend/src/routes/stats/concepts/+page.svelte:67` : remplacer `onMount` par `$effect(() => loadForDomain($currentDomain))` (pattern identique au fix Session 33 dans `/stats/+page.svelte`)

**A4. Remove hardcoded "Teacher" de `/profile`** (10min)
- `webapp/frontend/src/routes/profile/+page.svelte:208,225` : remplacer par `{currentAgentObj.name}` (objet déjà dispo ligne 22)

**A5. Créer `curriculum_en.yaml`** (2h)
- Extraire depuis `rubrics/en.yaml` + concepts hardcodés ailleurs (audit `concept_hints/en.yaml` + `cefr_diagnostics/en.yaml` + loader Python) pour dresser la liste des concepts EN par niveau CEFR
- Structure = miroir de `curriculum_es.yaml` (même schéma : niveau → concept_keys + concept_groups + concept_weights)
- Valider via `curriculums` DB : rows EN doivent matcher les concept_keys du YAML

**A6. Provisionner stubs `fr_to_{it,de,ja,ru}.yaml`** (20min)
- Créer 4 fichiers avec structure minimale `transfers: []` + header explicatif
- Évite l'IndexError potentielle quand un user Wave 2+ aurait un profil mais pas de matrice L1→target
- Contenu réel viendra avec Wave 2+ (recherche contrastive FR→IT/DE/JA/RU)

**A7. Fix `error_analysis_router` rule dispatch** (15min)
- `webapp/backend/app/routers/error_analysis_router.py:81` : `detect_errors(text)` → `detect_errors(text, lang=req.domain)` pour router correctement vers `rules_es.py` / `rules_it.py` etc.
- Impact actuel : toutes les erreurs ES sont détectées via regex EN (faux positifs massifs ou silence complet)

**Livrable Phase A** : commit unique `[fix] Sprint 5 Phase 5 follow-up — P0 multi-lang fixes`, smoke 14/14, battery ES si possible.

---

### Phase B — P1 hardening (avant le kickoff Wave 2 IT, ~12h total)

**B1. n8n workflows domain-aware** (4h, Dev + QA)
- Patch 4 workflows : `dify-diagnostic`, `dify-snapshot`, `dify-exam-scoring`, `dify-exam-persist` — ajouter `domain` param en query string ou body
- Update SQL queries downstream pour scoper WHERE domain=$X
- **Obligatoire** : patch `workflow_entity.nodes` ET `workflow_history.nodes` (gotcha Session 27, memory `project_n8n_workflow_history`)
- Test e2e : flow Maestro ES end-to-end (onboarding QCM → session → diagnostic persist → snapshot → exam) sans contamination cross-lang

**B2. Consolidation env vars** (2h, DevOps)
- Remplacer `ENABLE_MAESTRO` / `ENABLE_PROFESSORE` / `ENABLE_LEHRER` / ... par un seul `AVAILABLE_AGENTS=teacher,maestro,...` CSV (backward-compat alias pour ne pas casser le déploiement actuel)
- Remplacer 6× `DIFY_KEY_{AGENT}` par un pattern lookup dynamique `f"DIFY_KEY_{agent.upper()}"` dans `chat_router.py`
- Documenter dans `.env.sops.example` + runbook `rotate-secrets-sops.md`

**B3. Validation frontale domain** (2h)
- Backend endpoints (`profile_router`, `onboarding_router`, `settings_router`, `admin_router`, `chat_router`, `error_analysis_router`) : valider que `domain` appartient à un set connu (via helper `is_valid_domain(d)` qui lit `_DOMAIN_REGISTRY` ou config)
- Retourner HTTP 422 explicite au lieu de 200 + payload vide silencieux
- Impact UX : frontend reçoit un signal clair "domain non supporté" au lieu de voir des skeletons infinis

**B4. YAML schemas + validator** (3h)
- JSON Schema pour `rubrics/{lang}.yaml`, `fewshots/{lang}.yaml`, `concept_hints/{lang}.yaml`, `cefr_diagnostics/{lang}.yaml`, `l1_transfer/fr_to_{lang}.yaml`, `curriculum_{lang}.yaml`
- Script `scripts/data/validate_yamls.py --all-langs` : CI-friendly, échoue si un YAML cassé ou clés manquantes
- Helper runtime `LanguageDomain(lang).validate_data_completeness()` qui remonte un warning clair plutôt qu'un silence

**B5. Extension `clone_app.py` pour Wave 2+** (6h, spread sur 2 sessions)
- Accepter `--prompts-file path/to/llm_prompts.md` (les 4 prompts + code_exam_bilan strings dans un seul .md structuré)
- Helper `to_python_code_json_escaped` (mentionné dans les gotchas Session 32 mais introuvable) : unit-tested pour quotes / newlines / unicode escapes
- Pre-flight check `--validate-data-pack {lang}` : vérifier que les 6 YAMLs existent + parsent + ont toutes les clés du schéma
- Fournir template `data/templates/llm_prompts_template.md` pour guider les futurs traducteurs

---

### Phase C — P2 nice-to-have (post-Wave 2 kickoff)

**C1. Reactive stores partout** : auditer les `onMount` restants qui assument `$currentDomain` statique → passer à `$effect`. Scope : 5-10 components à vérifier.

**C2. Agent "Teacher" slug naming** : `slug='teacher'` + `name='Teacher'` + `lang='Anglais'` dans config.ts est ambigu (Teacher EST un agent, mais c'est aussi le nom de famille générique des tuteurs). Décider si on renomme `teacher→en-tutor` ou on garde et on documente clairement. Impact : SEO + brand, pas purement technique.

**C3. CEFR-only labels** : `levelLabels = { A1:'Survie', A2:'Quotidien', ... }` dans `/stats` — mapping fixé EN/ES/IT/DE. Pour Sensei JA (JLPT N5-N1) et Maestro-RU (TORFL TEU-IV), besoin de mapping alternatif. Voir `academie_core/levels.py` (Session 29 Phase 0.7 livré déjà le score-bridge, à wirer côté frontend).

**C4. i18n UI** : 100% FR aujourd'hui. Si on cible des users non-francophones un jour, structure à prévoir (svelte-i18n + locales/*.json). Hors scope immédiat, mais poser le hook dans les YAMLs existants (sibling `_i18n/` placeholder déjà présent côté onboarding).

**C5. Tests multi-lang** : battery `eval_live_battery.py --lang es` (déjà existant, pas ruté post-QCM) + `--lang it/de/ja/ru` stubs (Session 29 Phase 0.5) à remplir. Coverage rules `test_rules_{es,it,de,jp,ru}.py` : ES skeleton existe, IT/DE/JA/RU absents.

**C6. Native speaker review** : ES LLM prompt marqué DRAFT. Pas de reviewer natif (cf memory `project_no_native_reviewers`). Stratégie validation via corpus oracle + LLM consensus + télémétrie alpha en place — à formaliser en runbook.

**C7. Dify graph refactor onboarding-branch** : Session 33 a fixé le wiring via `code_profil_check`, mais la topologie reste "if_profil → false → llm_onboarding direct". Restructurer pour router tout le monde via `code_turn_check` simplifierait future maintenance. Coût : haute (touche 41 nodes + edges), gain : faible tant que le wiring actuel fonctionne.

---

## Checklist répliquable — Ajouter une langue Wave 2+ (ex: IT Professore)

**Prérequis** : ~20-30h dev + 4-6j domain-expert review. Phase A complète, B3+B4 idéalement.

### Étape 1 — Contenu pédagogique (8-12h, linguist/pédagogue)
- [ ] `rubrics/it.yaml` (copier structure `es.yaml`, adapter au framework local — PCIC/CEFR pur/QCER italien)
- [ ] `fewshots/it.yaml` (5 examples/niveau, contexte culturel)
- [ ] `concept_hints/it.yaml` (explications grammaticales, erreurs fréquentes)
- [ ] `cefr_diagnostics/it.yaml` (paliers + questions diagnostic + microtasks)
- [ ] `l1_transfer/fr_to_it.yaml` (erreurs de transfert FR→IT avec multiplicateurs tolérance)
- [ ] `curriculum_it.yaml` (concepts par niveau, groupes thématiques, weights)
- [ ] `onboarding/overlays/it.yaml` (persona + probe phrase FR→IT + regex scoring)

### Étape 2 — Traduction prompts LLM (4-6h, LLM specialist + domain review)
- [ ] Créer `data/professore/it/llm_onboarding.md` (88 lignes FR→IT)
- [ ] Créer `data/professore/it/llm_session.md` (120 lignes)
- [ ] Créer `data/professore/it/llm_exam.md` (110 lignes)
- [ ] Créer `data/professore/it/llm_plan_choice.md` (38 lignes)
- [ ] Créer `data/professore/it/code_exam_bilan_strings.md` (27 strings user-visible)
- [ ] Convertir en `professore_prompts.json` (format `clone_app.py --prompts-override` ou via helper post-B5)

### Étape 3 — Clone Dify (30min, DevOps)
- [ ] `python3 scripts/dify/clone_app.py --source-app-id <teacher> --new-name "Professore" --prompts-override professore_prompts.json --apply`
- [ ] Récupérer nouveau `app_id`, `workflow_id`, `api_key`
- [ ] `scripts/sprint5/11_update_dify_onboarding_qcm.py --only professore` (wire QCM inputs)
- [ ] `scripts/sprint5/13_wire_onboarding_branch.py --only professore` (wire onboarding-branch)
- [ ] `scripts/sprint5/14_strengthen_llm_onboarding_override.py --only professore`
- [ ] Patcher manuel : `code_exam_bilan` user-visible strings + 6 HTTP nodes `domain="it"` (tant que clone_app ne le fait pas auto)

### Étape 4 — Backend wiring (1h, Dev)
- [ ] `chat_router._DOMAIN_REGISTRY["professore"] = ("it", LanguageDomain("it"))` (décommenter)
- [ ] `domain_registry.AGENT_BY_DOMAIN["it"] = "professore"` (décommenter)
- [ ] `academie_core/taxonomy/llm.py` : ajouter `SYSTEM_PROMPT_IT` + entry dans `ANALYSIS_MODEL_BY_LANG` / `SYSTEM_PROMPT_BY_LANG` / `USER_PROMPT_TEMPLATE_BY_LANG`
- [ ] `academie_core/taxonomy/rules_it.py` : étoffer les détecteurs skeleton (Session 29 Phase 0.3)

### Étape 5 — Env vars + config (1h)
- [ ] `webapp/.env.sops` : `DIFY_KEY_PROFESSORE=app-...` + (si pas fait B2) `ENABLE_PROFESSORE=true`
- [ ] Rebuild academie-api
- [ ] `webapp/frontend/src/lib/config.ts` : `professore.available = true`
- [ ] Rebuild academie-frontend

### Étape 6 — n8n workflows (si pas fait B1) (2-3h)
- [ ] Vérifier que les 4 workflows n8n acceptent `domain=it` (sinon patcher — `workflow_entity` + `workflow_history`)

### Étape 7 — Tests + validation (4-6h, QA)
- [ ] Smoke test nouveau user : `/chat/professore` → modal QCM → submit → chat démarre en italien direct
- [ ] `python3 scripts/sprint3/eval_live_battery.py --lang it` (stub existe Session 29)
- [ ] Regression : Teacher EN + Maestro ES toujours OK (`--lang en`, `--lang es`)
- [ ] DB check : 3 users tests (EN + ES + IT) → `profils_eleves` et `learner_profiles` rows bien scopés, zero cross-contamination
- [ ] Smoke deep 20/20

**Total Wave 2 IT** : ~20-30h humain + 4-6j review. Le même process s'applique à DE (Lehrer), JA (Sensei, avec adaptations JLPT), RU (Maestro-RU, avec TORFL).

---

## Séquencement recommandé

```
Session 34 (~4-5h)    : Phase A complète (P0 fixes)  → commit + push
Session 35 (~6-8h)    : Phase B1+B3+B4 (n8n + validation + schemas)
Session 36 (~6-8h)    : Phase B2+B5 (env consolidation + clone_app extensions)
Session 37-40         : Wave 2 IT (checklist ci-dessus) — 4-6 sessions calendaires
Sessions suivantes    : Wave 2 DE (parallèle IT factorisé), Wave 3 JA, Wave 4 RU
```

Phase C reste un backlog opportuniste, à piocher en fonction des feedbacks alpha.

---

## Risques résiduels

- **Pas de reviewer natif** (memory `project_no_native_reviewers`) : validation LLM prompts ES/IT/DE/JA/RU passe par corpus oracle + LLM consensus + télémétrie alpha, pas humain. Accepté.
- **Dify vendor lock-in** : les patches graph SQL direct (Session 32+33) créent une dépendance forte au schéma Dify. Si Dify majorite upgrade, migration nécessaire.
- **n8n workflow_history gotcha** : tant que les patches sont appliqués manuellement aux 2 tables, risque oubli. `scripts/sprint5/02_update_n8n_workflows.py` donne le pattern.
- **i18n UI reporté** : acceptable tant que les users sont 100% francophones. À revisiter si traction non-FR.

---

## Références

- Audit frontend : 3 agents Explore, Session 33 2026-04-20
- Audit backend : idem
- Audit Dify+n8n+data : idem
- Memories pertinentes : `project_dify_variable_wiring`, `project_n8n_workflow_history`, `project_no_native_reviewers`
- Décisions : ADR #17 (QCM pre-chat), `docs/decisions.md`
- Runbook onboarding : `docs/99-runbooks/onboarding-qcm-activation.md`
- Recherche onboarding (7 rapports) : `docs/00-project/onboarding-research-2026-04-20/`
- Roadmap multilang historique : `docs/00-project/multilang_maturity_research.md` + `multilang_execution_roadmap.md`
