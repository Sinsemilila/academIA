---
title: Sprint 5 — Plan d'exécution multi-langue (long-term architecture)
date: 2026-04-18
status: in-progress
last_reviewed: 2026-04-18
author: Claude (Opus 4.7) — Session 26
---

# Sprint 5 — Plan d'exécution

**Contexte** : Session 26, validation utilisateur D1-D6 en version long-terme (pas de contrainte prod, on optimise pour zéro dette).

**Référence audit** : [`sprint5_multilang_audit.md`](sprint5_multilang_audit.md)

---

## Décisions verrouillées (D1-D6)

| # | Décision | Impact |
|---|---|---|
| **D1** | Unify ISO codes (`domain` en anglais, values `"en"`/`"es"`/`"it"`/`"de"`/`"ja"`/`"python"`/`"cybersec"`) | Rename `domaine`→`domain` sur 8 tables, migrate `'anglais'`→`'en'` partout |
| **D2** | L1 user-global (`eleves.l1`), `l1_watch_enabled` reste per-profile | Move column from `profils_eleves.l1` to `eleves.l1` |
| **D3** | Fine-tune v3 pour EN, base `gpt-4o-mini` pour ES (Option B) | `ANALYSIS_MODEL_BY_LANG` dispatch dans `llm.py` |
| **D4** | Store `currentAgent`/`currentDomain` créé en Phase 1 frontend | `lib/stores/navigation.ts` nouveau |
| **D5** | Un seul chatflow Dify `language-tutor`, Teacher migré dedans | Nouveau app Dify + migration + switch `_DOMAIN_REGISTRY` |
| **D6** | CEFR sourcé manuellement depuis références natives (PCIC/CILS/Profile Deutsch/JF Standard) | Jamais LLM-translate |

---

## Plan des 4 phases

### PHASE 1 — Foundation refactor (~3-4j)
Cross-cutting D1 + D2 + backend + frontend + n8n string updates.

| Sous-étape | Effort | Rollback |
|---|---|---|
| 1.1 DB migration unifiée (rename+ISO+L1 move+error_log) | ~3h | Script SQL inverse prêt |
| 1.2 Backend refactor (11 SQL + endpoints + `_DOMAIN_REGISTRY` ISO) | ~1j | `git revert` |
| 1.3 Frontend store + fixes callers | ~0.5j | `git revert` |
| 1.4 n8n workflows string updates | ~0.5j | Re-import JSON depuis backup |

**Gate de validation Phase 1** :
- `pytest` 140+ tests pass
- `smoke-test --deep` 21/21 ALL CLEAR
- E2E manuel : login → chat Teacher 3 turns → profil charge avec `domain='en'` → stats OK
- Battery Teacher re-run (cible ≥97%)

### PHASE 2 — Infra multi-domain (~1-1.5j)

| Sous-étape | Effort |
|---|---|
| 2.1 `taxonomy/llm.py` dispatch `MODEL_BY_LANG` + `PROMPT_BY_LANG` | 0.5j |
| 2.2 Dify Teacher paramétré minimal (Start node inputs) | 1j |

**Gate** : Teacher continue de fonctionner identique, `analyze_transcript("en")` inchangé, `analyze_transcript("es")` retourne empty proprement.

### PHASE 3 — language-tutor unified Dify (~2-3j)

| Sous-étape | Effort |
|---|---|
| 3.1 Clone Teacher → nouveau app Dify `language-tutor` | 0.5j |
| 3.2 Paramétrer tout (persona, concepts, diagnostics via HTTP) | 1j |
| 3.3 Backend endpoints `/api/curriculum/concept-hints?domain=` + `/cefr-diagnostics?domain=` | 0.5j |
| 3.4 Test parallèle `language-tutor` avec `lang="en"` | 0.5j |
| 3.5 Switch `_DOMAIN_REGISTRY` teacher → nouveau app, archiver ancien | 0.25j |

**Gate** : Battery Teacher re-run sur `language-tutor` ≥ 97%, ancien Teacher archivé mais récupérable.

### PHASE 4 — Content pack ES (~6-7j, autonomie partielle)

**Merged sur main avec feature flag** (pas de branche long-lived, voir memory `feedback_merge_with_flag`).

| Sous-étape | Autonomie | Effort |
|---|---|---|
| 4.1 `data/rubrics/es.yaml` drafté depuis PCIC online | 🟢 Autonome | 1.5j |
| 4.2 `data/fewshots/es.yaml` 14 exemples CEFR | 🟢 Autonome | 1j |
| 4.3 `data/l1_transfer/fr_to_es.yaml` (por/para, genre, subjuntivo) | 🟢 Autonome | 0.5j |
| 4.4 `data/concept_hints/es.yaml` + `cefr_diagnostics/es.yaml` | 🟢 Autonome | 1j |
| 4.5 `SYSTEM_PROMPT_ES` dans `llm.py` | 🟢 Autonome | 0.5j |
| 4.6 `rules_es.py` squelette (5-10 règles de base) | 🟡 Squelette autonome, review native requise | 1j |
| 4.7 `curriculum_es.yaml` ~50 concepts squelette | 🟡 Idem | 1.5j |
| 4.8 `LanguageDomain("es")` activation + tests | 🟢 Autonome | 0.25j |

**Feature flag architecture** :
- Tout merger sur main avec `_DOMAIN_REGISTRY["maestro"]` **commenté ou gated par env var**
- `config.ts` : `maestro.available: false` par défaut
- Activation = env var `ENABLE_MAESTRO=true` + config.ts flip + redeploy

**Gate** : STOP après 4.8 → checkpoint humain avant activation prod. Tous les files merged mais inactifs.

---

## Protocole d'exécution autonome

### Checkpoints obligatoires
Je m'arrête et reporte à Sinse après :
1. **Fin Phase 1** : commits pushés, smoke + battery pass
2. **Fin Phase 2** : idem
3. **Fin Phase 3** : idem + test conversation language-tutor complet
4. **Fin Phase 4.8** : drafts mergés avec feature flag OFF, STOP avant activation

### Règles autonomes
- **JAMAIS** : `DROP TABLE`, `DROP COLUMN` sans migration rollback-ready prête
- **JAMAIS** : `git push --force`, `reset --hard`, amend sur commits pushés
- **JAMAIS** : flip `available: true` Maestro / activation prod sans OK explicite Sinse
- **TOUJOURS** : smoke test avant push
- **TOUJOURS** : commit atomique par sous-étape, message Co-Authored-By
- **TOUJOURS** : mettre à jour TODO.md + CHANGELOG.md au fil de l'eau

### Rollback par phase

| Phase | Rollback |
|---|---|
| 1.1 DB | Script SQL inverse exact prêt avant migration |
| 1.2 Backend | `git revert` + rebuild academie-api |
| 1.3 Frontend | `git revert` + rebuild frontend |
| 1.4 n8n | Re-import workflow JSON backups pré-migration |
| 2.1 llm.py | `git revert` |
| 2.2 Dify Teacher | Restore via Dify DB backup de `workflows.graph` |
| 3 language-tutor | Delete le nouveau app Dify, `_DOMAIN_REGISTRY` garde ancien Teacher |
| 4 Content ES | Feature flag OFF = aucun impact, code dormant |

---

## Timeline estimée

- **Phase 1-2** : ~4-5j (15h-20h effectif)
- **Phase 3** : ~2-3j (10h-15h)
- **Phase 4** : ~6-7j drafts (jusqu'à review native speaker)

**Total jusqu'à Maestro alpha** : ~15j (avec review humain ES en parallèle).

---

## Suivi d'exécution

_(Mis à jour au fil des commits)_

| Phase | Status | Commit | Gate validée |
|---|---|---|---|
| 1.1 DB migration | ✅ done | `830a8b4` | 140/140 tests + 21/21 smoke |
| 1.2 Backend refactor | ✅ done | `830a8b4` | intégré commit 1.1 |
| 1.3 Frontend | ✅ done | `830a8b4` | intégré commit 1.1 |
| 1.4 n8n | ✅ done | `830a8b4` + `feda228` | workflow_history gotcha fixed |
| 2.1 llm.py dispatch | ✅ done | `eb43cb8` | backward-compat aliases OK |
| 2.2 Dify Teacher ISO | ✅ done | `eb43cb8` | HTTP 200 chat |
| 3 language-tutor unified | ✅ done | `c42aa16` | HTTP 200 existing + new users |
| 4.x Content ES (DRAFT gated) | ✅ done | `5ab1cc4` | 155 tests pass, feature flag validated |

### Phase 4 Note — DRAFT content merged with feature flag

Toutes les 6 YAML + rules_es.py + SYSTEM_PROMPT_ES + USER_PROMPT_TEMPLATE_ES mergés sur main. Activation via `ENABLE_MAESTRO=true` + `DIFY_KEY_MAESTRO` env vars. Native-speaker review OBLIGATOIRE avant activation prod (YAMLs draftés par Claude basé sur PCIC — structure correcte, contenu à valider).

Post-activation restants pour Maestro alpha :
1. Review native speaker hispanophone C2 des 6 YAML + prompts ES
2. Création nouvelle app Dify "Maestro - Profesor de Español" (clone Teacher + traduction prompts)
3. Set `DIFY_KEY_MAESTRO` env var
4. Flip `ENABLE_MAESTRO=true` + rebuild academie-api
5. Flip `maestro.available=true` dans `frontend/src/lib/config.ts` + rebuild frontend
6. Famille test alpha FR→ES A1-A2

### Phase 3 Note (résolution après debug ~1h30)

Dify architecture : le graph est chargé depuis DB à chaque request, aucun cache persistent. La VariablePool runtime est populée par les outputs effectifs des code nodes, pas par un schéma pré-compilé.

Mon UPDATE DB direct du graph fonctionnait structurellement, mais llm_onboarding s'exécute sur une branche qui bypass code_turn_check → les refs `{{#code_turn_check.X#}}` y échouent pour les nouveaux users. Solution : paramétrer uniquement llm_plan_choice + llm_session (post-code_turn_check). Pour Maestro ES, un nouveau Dify app dédié sera créé avec son propre onboarding ES natif.

---

## Références

- Audit 5 surfaces : [`sprint5_multilang_audit.md`](sprint5_multilang_audit.md)
- Roadmap multi-lang : [`roadmap_multilang.md`](roadmap_multilang.md)
- Commit Sprint 5 infra (base) : `33a862a`
- Commit NUCLE/GLMM : `0bc40f8`
- Session 26 handoff : `SESSION.md`
