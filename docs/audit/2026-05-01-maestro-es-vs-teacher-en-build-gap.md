---
title: Audit build gap Maestro ES vs Teacher EN — single source of truth Phase 1+
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 55
tags: [audit, multilang, oracle, methodology]
ai_summary: "Inventaire 18 dimensions structurelles EN vs ES, priorités P0/P1/P2, ordre exécution build-before-measure. Output unique pour décider quoi construire avant re-mesure Oracle."
---

# Audit build gap Maestro ES vs Teacher EN

**Context** : Pivot S55 acté — on a optimisé l'OUTIL DE MESURE (Oracle cross-langue) avant de construire structurellement Maestro à parité Teacher EN. Score 19/24 panel = baseline floor pré-build, PAS MVP DoD légitime. Cet audit recense TOUT ce qui manque ES pour atteindre parité avant re-mesure.

**Source** : Explore agent dispatch S55 + verifications terrain Sinse-validated (counts python yaml.safe_load + grep + wc).

**Usage** : Sinse review item par item, pick TODO autonome, exec petit-à-petit. Re-Oracle final post-build complet.

---

## 1. Data layer YAML (per-language entries)

| YAML | EN entries | ES entries | Gap | Priority |
|---|---|---|---|---|
| `curriculum_<lang>.yaml` | 131 (A1:18 A2:20 B1:31 B2:25 C1:22 C2:15) | 98 (A1:26 A2:12 B1:25 B2:22 C1:8 C2:5) | **-33 dont 22 C1+10 C2** | P1 |
| `concept_hints/<lang>.yaml` | 131 | 103 | **-28** (correlé curriculum gap) | P1 |
| `rubrics/<lang>.yaml` | 76L | 70L | Parity ✅ | — |
| `fewshots/<lang>.yaml` | 14 | 22 | ES MIEUX ✅ | — |
| `cefr_diagnostics/<lang>.yaml` | 37L | 33L | Parity ✅ | — |
| `functions/<lang>.yaml` | 10 (A1+A2 stub) | 42 (A1+A2 PCIC complete) | ES MIEUX A1-A2 ✅, B1-C2 ❌ | P1 |
| `micro_lessons/<lang>.yaml` | présent | présent | Parity ✅ | — |
| `mini_exam/<lang>_*.yaml` | A1-B2 (4 files) | A1-B2 (4 files) | A2-C2 manquants ES ❌ | P1 |
| `l1_transfer/fr_to_<lang>.yaml` | 12 entries | 12 entries | Parity ✅ | — |
| `tolerance_matrix/` | shared lang-agnostic | shared | Parity ✅ | — |
| `onboarding/overlays/<lang>.yaml` | présent | présent | Parity ✅ | — |

**Items P1 à construire** :
- [ ] **G6** : Étendre `curriculum_es.yaml` 98 → ~150 (PCIC Vol C C1-C2, +52 concepts) — *3j WebFetch+extract*
- [ ] **G6.1** : Étendre `concept_hints/es.yaml` 103 → ~180 entries (correlated G6) — *1j*
- [ ] **G7.1** : Étendre `functions/es.yaml` 42 → ~80 entries (B1-C2 expansion PCIC Funciones) — *1.5j*
- [ ] **G7.2** : Étendre `functions/en.yaml` 10 → ~50 entries (CEFR Companion 2020 Ch3 production/interaction full A1-C2) — *1.5j*
- [ ] **G7.3** : DELE A2/B1/C1/C2 modelos acquisition (Sinse manual dele.org) → `mini_exam/es_a2.yaml` ... `es_c2.yaml` — *0.5j Sinse + 1.5j Claude extract*

---

## 2. Authority anchors extracted (`data/extracted/`)

| Source | EN | ES |
|---|---|---|
| Hawkins-Filipović 2012 (criterial features L2 EN) | ✅ extracted | n/a |
| CoE 2020 CEFR Companion | ✅ extracted | n/a (cross-lang utilisé) |
| Lyster 2007 counterbalanced | ✅ extracted (cf-taxonomy) | shared cross-lang ✅ |
| Lightbown-Spada 2021 | ✅ Ch5+6 extracted | shared cross-lang ✅ |
| Cervantes PCIC A1-A2 | n/a | ✅ extracted (S53 grammar-by-level) |
| Cervantes PCIC B1-B2 | n/a | ✅ extracted (S53 grammar-by-level) |
| Cervantes PCIC C1-C2 | n/a | ❌ **PENDING acquisition** |
| DELE A1 oficial Modelo | n/a | ⚠️ acquired pending extract |
| DELE B2 Cronómetro | n/a | ⚠️ acquired pending extract |
| DELE B2 Preparación soluciones | n/a | ⚠️ acquired pending extract |

**Items P1** :
- [ ] **G6** : PCIC Vol C C1-C2 extraction via WebFetch `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/` (technique S53) → `extracted/cervantes-2006-plan-curricular-c1-c2/` — *2j*
- [ ] **G7** : Extract 3 DELE books acquired :
  - `extracted/cervantes-dele-a1/` (Modelo officiel 40p) → `rubric_dele_a1.yaml` 4 dims (Adecuación/Coherencia/Corrección/Alcance) + `mini_exam/es_a1.yaml` enrichi — *0.5j*
  - `extracted/bech-tormo-2013-cronometro-dele-b2/` (Edinumen 217p) → `mini_exam/es_b2.yaml` task bank — *1.5j*
  - `extracted/alzugaray-2013-preparacion-dele-b2/` (companion 26p) → rubric calibration — *0.3j*

---

## 3. Rules detector code (`taxonomy/`)

| Métrique | `rules.py` (EN) | `rules_es.py` (ES) | Gap |
|---|---|---|---|
| LOC | 839 | 785 | similaire |
| Architecture | spaCy NLP + regex hybrid + 1 detect func + 114 ERROR_CODE refs | regex + 20 detect funcs + 21 ERROR_CODE refs | ❌ **Architectures différentes** |
| Error codes covered | V:TENSE, V:FORM, V:SVA, V:ASPECT, V:AUX, V:MODAL, V:COND, V:PRET, V:INFL, V:PHRASAL, V:PASS, V:EXIST, V:CHOICE, V:SUBJ, V:GUSTAR_SUBJECT, L:FALSE (16+) | V:PRET, V:SER_ESTAR, V:SUBJ, V:GUSTAR_SUBJECT, PREP:A_PERSONAL, CONCORD:GEN (S51 4 nouveaux) | -10+ codes ES |
| FP whitelists | PROPER_NOUNS (29) + SPACING (10) + CONTRACTION_MAP (26) + PREP_CALQUES (12) + LEX_CALQUE (14) + FRENCH_COGNATES (91) | partial — à audit | ❌ |
| L1 transfer FR→target patterns | mature (calques FR-EN) | partial (S51 Wave 2 P0+P2) | ⚠️ |

**Items P0-P2** :
- [ ] **G8.1** (P0 si on garde regex arch ES) : Étendre `rules_es.py` couverture error codes manquants (V:TENSE/V:FORM/V:SVA/V:ASPECT/V:AUX/V:MODAL/V:COND/V:INFL/V:PHRASAL/V:PASS/V:EXIST/V:CHOICE) — ES specific patterns (subjuntivo triggers, ser/estar discrimination, mood/aspect ES) — *3-4j linguistic*
- [ ] **G8.2** (P3 — strategic decision) : Migration `rules_es.py` regex → spaCy NLP architecture parity Teacher EN — *5-10j gros refactor, defer si Phase 1 prompt fix résout déjà signaux*
- [ ] **G8.3** : Étendre FP whitelists ES (PROPER_NOUNS_ES, CONTRACTIONS_ES "al/del", LEX_CALQUE_ES, FRENCH_COGNATES_ES) — *1j*
- [ ] **G8.4** : Compléter `l1_transfer/fr_to_es.yaml` 12 → 25+ entries (FR→ES specific calques : por/para, a/al, ser/estar, gustar inversion, subjuntivo triggers) — *1j*

---

## 4. Pedagogy modules (`packages/academie-core/academie_core/pedagogy/`)

✅ **Tous les modules sont déjà multi-lang aware** (params `lang_target` / `target_lang`) :
- `scaffolding_policy.py` : lang-aware (90% L2 par défaut FR-ES close)
- `consolidation.py` : dispatch lang-aware
- `cf_classifier.py` : multi-lang LLM-based
- `three_strikes.py` : language-agnostic logic
- `typological_distance.py` : FR-ES distance computed
- `priority_loop.py` : ES support OK
- `teacher_prompt.py` : `build_full_dify_inputs(scenario, agent)` lang-parameterized

**Pas d'items à construire** sur cette dimension.

---

## 5. Backend chat router (`webapp/backend/app/routers/chat_router.py`)

✅ **Architecture polymorphe** — pas de hardcoded `maestro_es` vs `teacher_en` branches. Routing via `agents_config.py` lang-aware. `build_full_dify_inputs(scenario, agent)` lang-parameterized.

**Pas d'items.**

---

## 6. agents_config.py

✅ **Both registered** :
- `AgentDef("teacher", "en", "DIFY_KEY_TEACHER", "Teacher — English", "39565197-c9d1-4d5b-b66f-18925de236d9")`
- `AgentDef("maestro", "es", "DIFY_KEY_MAESTRO", "Maestro — Spanish", "47b0529c-b3a3-4651-8717-759e666172c9")`

**Pas d'items.**

---

## 7. Dify workflow LLM nodes (4 flows × 2 langs)

Diff structurellement parity (extracted `/tmp/maestro-es-audit/`) :

| Flow | EN size | ES size | Diff |
|---|---|---|---|
| `llm_plan_choice` | 60L | 60L | identical structure |
| `llm_session` | 144L | 144L | **identical structure**, ES = traduction |
| `llm_onboarding` | 168L | 169L | identical (+1L localisation) |
| `llm_exam` | 94L | 101L | DIVERGENT personas (CECRL EN vs MCER/DELE ES) — acceptable |

**Items à construire** :
- [ ] **G5.1** (P0 — vrai signal) : Add anti-over-explicit A1-A2 directive + anti-priority-leak directive dans `llm_session` Maestro ES (le mapping TIER → metalinguistic actuel ne distingue pas niveau CEFR) — *1j patch + smoke validation*
- [ ] **G5.2** (P1) : Audit + add même directives dans `llm_session` Teacher EN (cross-langue applicable, prevent EN regression) — *0.5j*
- [ ] **G5.3** (P2) : Document Dify prompt version control strategy (currently ad-hoc DB UPDATE workflows.graph) — *0.3j doc*

---

## 8. Dify workflow code nodes

✅ **Pas de JS hardcoded language strings détectés** dans les graphs JSON. Code logic shared cross-lang.

**Pas d'items.**

---

## 9. Oracle scenarios

| | EN | ES |
|---|---|---|
| Total scenarios | 26 | 24 |
| Per CEFR | A1:1, A2:3, B1:5, B2:5, C1:4, C2:0, +multi/risk:8 | A1:5, A2:3, B1:3, B2:3, C1:1, C2:0, +multi:4, risk:5 |
| Goldens recorded | S54 2026-04-30 | S55 2026-05-01 (re-recorded post G3+G4) |

**Asymétrie** : ES skewed toward A1 (5 vs 1) + sparse C1 (1 vs 4).

**Items P1-P2** :
- [ ] **G9.1** : Rebalance ES scenarios — demote 2-3 A1 surplus + add 3-4 C1 scenarios post G6 (PCIC Vol C extraction donne le matériel) — *1.5j*
- [ ] **G9.2** : Add 2-3 ES B2 edge cases (parité EN coverage) — *1j*
- [ ] **G9.3** : Add 2-3 ES multi-turn scenarios (parité EN 8 multi/risk) — *1j*

---

## 10. Oracle judge prompts (`scripts/oracle/judges/llm_pairwise.py`)

| Prompt | État |
|---|---|
| `CF_MOVE_PROMPT` v2 | ✅ S55 G3 ajout 5 ES Lyster fewshots cross-lang (commit `9a589cb`) |
| `PAIRWISE_PROMPT` | ✅ S55 G4 multi-error tolerance (commit `38ff69f`) |
| `CEFR_REGISTER_PROMPT` | ✅ language-agnostic |

**Items éventuels** :
- [ ] **G10.1** (P2) : Étendre fewshots ES de 5 → 10+ post Phase 1.B Maestro Dify patch (validation) — *0.5j*

---

## 11. Tolerance matrix

✅ **Shared lang-agnostic v2** (codes ES intégrés S51 `tolerance_matrix_v2.yaml` 11 codes ES + override 1).

**Items éventuels** :
- [ ] **G11.1** (P2) : Validation tolerance ES vs EN par batterie (kappa drift check post Phase 1) — *0.5j*

---

## 12. Audit docs livrés

✅ 4 audit docs cumulés :
- `2026-04-30-curriculum-en-vs-authority.md` (Hawkins+CoE Companion EN)
- `2026-04-30-curriculum-es-vs-pcic.md` (PCIC A1-B2 ES)
- `2026-04-30-oracle-battery-v1-acceptable-set-audit.md` (Lyster EN)
- `2026-05-01-maestro-es-acceptable-set-audit.md` (Lyster ES Phase 0.H)
- **CET AUDIT** (`2026-05-01-maestro-es-vs-teacher-en-build-gap.md`)

---

## 13. Sprint plans + ADRs

✅ Plans dédiés (post S55 cleanup convention) :
- `docs/00-project/sprint-maestro-es-2026-05.md` (v2 pivot Build avant Measure)
- `docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md` (S54 EN MVP COMPLETE)

✅ ADRs cross-lang :
- ADR-013 language scope (EN+ES flagship A1-C2 / IT+DE+JP+RU A1-B2)
- ADR-014 structured knowledge extraction
- ADR-016 authority anchor strategy

**Pas d'items.**

---

## 14. Books library

| Authority | Status |
|---|---|
| EN authority anchors | ✅ Hawkins + CoE Companion + Lyster + Lightbown-Spada (4 extracted) |
| ES PCIC A1-B2 | ✅ extracted S53 |
| ES PCIC C1-C2 | ❌ **PENDING acquisition (free `cvc.cervantes.es`)** |
| ES DELE A1 modelo | ⚠️ acquired pending extract |
| ES DELE A2/B1/C1/C2 modelos | ❌ **PENDING acquisition (Sinse signup `dele.org`)** |
| ES DELE B2 Cronómetro | ⚠️ acquired pending extract |
| ES DELE B2 Preparación soluciones | ⚠️ acquired pending extract |
| EN English Profile / Vocabulary Profile | ❌ pending Sinse signup `englishprofile.org` |

Couvert par G6+G7 ci-dessus.

---

## 15. Scripts utilities

| Script | EN | ES | Gap |
|---|---|---|---|
| `build_scenarios.py` (302L) | ✅ EN-specific generator | n/a | — |
| `build_scenarios_maestro_es.py` (187L) | n/a | ✅ ES-specific generator | différents implementations (39% smaller ES) |
| `record_golden.py` (154L) | shared | shared | parity ✅ |
| `record_golden_litellm.py` (164L) | shared | shared | parity ✅ |

**Items P2** :
- [ ] **G12.1** : Refactor unify `build_scenarios*` en 1 script lang-parametrized (DRY) — *2j*

---

## 16. Tests pytest

✅ Tests parity OK :
- `tests/test_yaml_schema.py` parametrized 6 langs (EN+ES active, IT/DE/JA/RU skip)
- `tests/test_es_content_pack.py` (ES-specific schema validation)
- `tests/test_scaffolding_policy.py` lang-aware
- `tests/test_llm_dispatch.py`

**Items éventuels** :
- [ ] **G13.1** (P2) : `test_judges_cf_move_es.py` — kappa ES error pairs validation (analogue test EN) — *0.5j*

---

## 17. Backend Dify integration

✅ `chat_router.py:1019-1027` use `load_concept_hints_for_level(lang_target, niveau)` (S55 fix) — lang-parameterized.

`build_full_dify_inputs(scenario, agent)` calls language-aware blocks. Parity OK.

---

## 18. Vault knowledge cross-projet

Cross-references actifs depuis `vault/knowledge/`:
- `cross-project/auth-patterns.md` (shared)
- `cross-project/dify-variable-wiring.md` (shared, gotcha pattern)
- `cross-project/n8n-workflow-history.md` (shared)
- `pedagogy/l1-l2-scaffolding-policy.md` (shared)
- `pedagogy/cefr-consolidation-policy.md` (shared)
- `methodology/multilang-roadmap.md` (cross-lang plan)

**Pas d'items.**

---

# 🎯 SYNTHÈSE PRIORITÉS

## Total effort

| Priority | Effort cumul | Items count |
|---|---|---|
| **P0 (bloque MVP)** | **2-3j** | 1 item (G5 prompt Maestro Dify fix) |
| **P1 (important parité)** | **~12-14j** | 8 items (G6, G7.1, G7.2, G7.3, G8.1, G8.3, G8.4, G9.1) |
| **P2 (qualité gates)** | **~4-5j** | 6 items (G5.3, G9.2, G9.3, G10.1, G11.1, G12.1, G13.1) |
| **P3 (defer)** | **5-10j** | 1 item (G8.2 spaCy migration) |
| **TOTAL Build → Measure** | **~22-30j** | 16 items |

## Ordre exécution recommandé

### Tier 1 — Unblock immediate (P0, ~2-3j)

1. **G5.1** Patch Maestro Dify `llm_session` : anti-over-explicit A1-A2 + anti-priority-leak directives (1j + smoke)
2. **G5.2** Apply same directives Teacher EN llm_session pour cross-langue consistency (0.5j)
3. **G5.3** Document Dify prompt version control strategy doc/runbook (0.3j)

→ **Re-mesure smoke** : forecast 5 fails A1-A2 explicit_correction → 0 ; battery 19/24 → 22-23/24.

### Tier 2 — Foundational parity (P1, ~12-14j, ordre quelconque)

4. **G6** PCIC Vol C extraction → `curriculum_es.yaml` 98→150 + `concept_hints/es.yaml` 103→180 (3j)
5. **G7.1** `functions/es.yaml` 42→80 (PCIC Funciones B1-C2) (1.5j)
6. **G7.2** `functions/en.yaml` 10→50 (CEFR Companion 2020 Ch3) (1.5j)
7. **G7.3** DELE A1 Modelo + Cronómetro B2 + Preparación B2 extraction → `mini_exam/es_*.yaml` + `rubrics/es.yaml` DELE Adecuación/Coherencia/Corrección/Alcance (2.5j)
8. **G8.1** `rules_es.py` étendre 12 codes manquants (V:TENSE/V:FORM/V:SVA/V:ASPECT/V:AUX/V:MODAL/V:COND/V:INFL/V:PHRASAL/V:PASS/V:EXIST/V:CHOICE) (3j)
9. **G8.3** FP whitelists ES (PROPER_NOUNS_ES + CONTRACTIONS_ES + LEX_CALQUE_ES + FRENCH_COGNATES_ES) (1j)
10. **G8.4** `l1_transfer/fr_to_es.yaml` 12→25+ entries (1j)
11. **G9.1** Rebalance ES scenarios (demote 2-3 A1 surplus + add 3-4 C1 post G6) (1.5j)
12. **DELE A2/B1/C1/C2 acquisition Sinse manual** + extract → `mini_exam/es_a2.yaml`...`es_c2.yaml` (Sinse 50 min DL + Claude 1.5j extract)

### Tier 3 — Quality gates (P2, ~4-5j)

13. **G9.2** Add 2-3 ES B2 edge cases (1j)
14. **G9.3** Add 2-3 ES multi-turn scenarios (1j)
15. **G10.1** Étendre CF_MOVE_PROMPT ES fewshots 5→10+ post Phase 1.B validation (0.5j)
16. **G11.1** Tolerance matrix ES validation kappa drift (0.5j)
17. **G12.1** Refactor unify `build_scenarios*` lang-parametrized (2j)
18. **G13.1** `test_judges_cf_move_es.py` (0.5j)

### Tier 4 — Defer (P3)

19. **G8.2** `rules_es.py` regex → spaCy migration (5-10j) — strategic decision : si Phase 1 prompt fix + Tier 1 résout score ≥22/24, defer indéfiniment.

### Tier FINAL — RE-MEASURE

20. **G_FINAL** Battery panel cross-provider + cache + κ Opus calibration sur Maestro mature post Tier 1+2+3. **Forecast 22-24/24** (parity Teacher EN MVP S54 20/26). DoD MVP Maestro ES COMPLETE.

---

# 📋 ITEMS À PICKER (TODO autonome)

Sinse pick line par line, exec petit-à-petit. Chaque item shippable indépendamment :

## P0
- [ ] G5.1 — Maestro Dify llm_session : anti-A1-A2 metalinguistic + anti-priority-leak directives
- [ ] G5.2 — Teacher EN llm_session : same directives cross-langue
- [ ] G5.3 — Doc Dify prompt version control runbook

## P1
- [ ] G6 — PCIC Vol C C1-C2 extraction → curriculum_es 98→150 + hints 103→180
- [ ] G7.1 — functions/es.yaml 42→80 (PCIC Funciones B1-C2)
- [ ] G7.2 — functions/en.yaml 10→50 (CEFR Companion Ch3 production/interaction)
- [ ] G7.3a — DELE A1 Modelo extraction → rubric DELE 4 dims + mini_exam/es_a1
- [ ] G7.3b — Cronómetro B2 extraction → mini_exam/es_b2 task bank
- [ ] G7.3c — Preparación B2 extraction → rubric calibration
- [ ] G8.1 — rules_es.py étendre 12 codes manquants
- [ ] G8.3 — FP whitelists ES (PROPER_NOUNS + CONTRACTIONS + LEX_CALQUE + COGNATES)
- [ ] G8.4 — l1_transfer/fr_to_es.yaml 12→25+ entries
- [ ] G9.1 — Rebalance ES scenarios (demote A1 + add C1 post G6)
- [ ] DELE A2-C2 modelos acquisition Sinse manual + extract

## P2
- [ ] G9.2 — Add 2-3 ES B2 edge case scenarios
- [ ] G9.3 — Add 2-3 ES multi-turn scenarios
- [ ] G10.1 — Étendre CF_MOVE_PROMPT ES fewshots 5→10+
- [ ] G11.1 — Tolerance matrix ES validation
- [ ] G12.1 — Refactor unify build_scenarios* lang-parametrized
- [ ] G13.1 — test_judges_cf_move_es.py

## P3 (defer)
- [ ] G8.2 — rules_es.py regex → spaCy migration

## RE-MEASURE FINAL
- [ ] G_FINAL — Battery panel + cache + κ Opus post Build complete (forecast 22-24/24)

---

## Cross-references

- Sprint plan : `docs/00-project/sprint-maestro-es-2026-05.md` (v2 pivot Build avant Measure)
- Audit Phase 0.H : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- Audit S53 PCIC : `webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`
- ADR-013 language scope : `docs/05-decisions/ADR-013-language-scope-by-tier.md`
- ADR-016 authority anchor : `docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`
- Vault books : `vault/knowledge/books/USAGE-MAP.md`
- Vault failures S55 : `vault/projects/academia-ia/failures.md`
- Sprint EN MVP S54 : `docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`

---

**Single source of truth pour Phase 1+ Maestro ES**. Mise à jour incrémentale : check items au fil de l'exécution. Re-Oracle final = G_FINAL post Build complet.
