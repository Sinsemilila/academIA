---
title: Sprint Maestro ES — Build avant Measure (pivot S55)
date: 2026-05-01
status: active
last_reviewed: 2026-05-01
session_origin: 55
owner: claude
revisions:
  - "2026-05-01 v1 : sprint Oracle measurement-first (DoD score 18-22/24)"
  - "2026-05-01 v2 : PIVOT 'build before measure'. 19/24 = baseline floor, pas MVP DoD. Construction Maestro structural parity Teacher EN d'abord."
---

# Sprint Maestro ES — Build avant Measure (pivot S55)

## ⚠️ PIVOT CRITICAL S55 (acté fin de session)

**Constat Sinse (2026-05-01)** : on a optimisé l'OUTIL DE MESURE (Oracle cross-langue) avant de construire structurellement Maestro à parité Teacher EN. Score 19/24 atteint S55 reste un **baseline floor pré-build**, PAS un MVP DoD légitime.

**Asymétrie structurelle EN vs ES** :

| Composant | Teacher EN (S15-S54, ~40 sessions) | Maestro ES (S20-S55, ~20 sessions) | Gap |
|---|---|---|---|
| Prompt Dify itéré | P0.1 enum S51, scaffolding S35, BIPED S52 + 7 fewshots Lyster S54 P3.5 | **Traduction littérale du EN S32, JAMAIS re-itéré** | ❌ Critique |
| `rules*.py` arch | spaCy NLP + 114 ERROR_CODE refs | regex + 20 detect funcs | ❌ Mature vs early |
| Curriculum | 131 concepts (Hawkins + CEFR Companion + cross-validated) | 98 concepts (PCIC A1-B2 only, **C1-C2 manquant 28 concepts**) | ❌ Incomplete A1-C2 |
| Authority anchors extracted | 4 (Hawkins + CoE Companion + Lyster + Lightbown-Spada) | 1 (PCIC Cervantes A1-B2) | ❌ |
| Books acquired NON extracted | 0 | 3 (DELE A1 modelo + Cronómetro B2 + Preparación B2) | ❌ |

**Implication** : les 5 fails restants du score 19/24 (TOUS `explicit_correction` A1-A2) sont des **vrais signaux pédagogiques cohérents** pointant un défaut systématique du prompt Maestro Dify (pas itéré). Les 19 pass partiellement chanceux sur contextes simples — base structurelle mince.

**Décision** : Phases 0+D livrées (Oracle infra ready cross-langue, réutilisable pour Wave 2 IT/DE) — **conservées**. Mais le sprint pivote vers **construction Maestro structural** avant re-measure légitime.

## Nouvelle DoD MVP Maestro ES (post-pivot)

**Pas un score Oracle isolé**. Set complet build-then-measure :

### Build criteria (must complete BEFORE final Oracle re-measure)

- [ ] **Maestro Dify prompt itéré** : anti-over-explicit A1-A2 + anti-priority-leak + scaffolding policy ES strict (analogue Teacher EN P0.1 enum S51 + S35 scaffolding)
- [ ] **rules_es.py architecture parity** : spaCy migration OR justified divergence documented (effort 5-10j si spaCy migrate)
- [ ] **Curriculum complete A1-C2** : PCIC Vol C extracted (98 → ~150 concepts) + concept_hints aligned + functions A2→C2 expansion
- [ ] **DELE corpus extracted** : 3 books acquired → `mini_exam/es_*.yaml` enrichi + `rubrics_es.yaml` augmenté DELE Criterios (Adecuación/Coherencia/Corrección/Alcance)
- [ ] **CEFR Companion 2020 ES alignment** : audit cross-validation PCIC vs Companion descriptors (1j)

### Measure criteria (after Build complete)

- [ ] Score panel cross-provider ≥ 22/24 (mature Maestro target, vs S54 EN 20/26 = ~77%)
- [ ] AC2 ≥ 0.7 sur 3 dims (cf_move, register, semantic_fidelity)
- [ ] κ Opus super-judge in-chat ≥ 0.7 vs panel sur 3 dims
- [ ] 0 stable structural fail (3 runs consécutifs)
- [ ] 0 `explicit_correction` A1-A2 (Lyster ban respected)
- [ ] 0 priority leak risk scenario

## Phase 0 — Oracle infrastructure (S55 LIVRÉE 2026-05-01) ✅

**Conservée — utile pour Wave 2 IT/DE/JP/RU + future re-measure ES**.

Phases 0.A à 0.I + Phase D livrées :
- Judge code cross-lang fix (`d038dd9` `1ccc53c`)
- Re-record 24 goldens
- Lyster acceptable_set audit ES (`c11ee25`)
- PAIRWISE_PROMPT multi-error tolerance G4 (`38ff69f`)
- CF_MOVE_PROMPT 5 ES Lyster fewshots G3 (`9a589cb`)
- Battery 19/24 panel + cache (`e3a3692`)
- Opus calibration κ documented (`scripts/oracle/baselines/2026-05-01-opus-supervisor-scores-es.yaml`)

**Score atteint** : 19/24 (79%) panel certified — **acté comme baseline floor pré-build**, pas MVP DoD.

## Phase 1 — Build Maestro Dify prompt (P0 NEXT, ~2j)

### 1.A — Audit prompt Maestro Dify actuel (~2h)

Workflow `47b0529c` version `d3df0ef0`. Identifier sections manquantes vs Teacher EN itéré :

- Anti-over-explicit A1-A2 directive : présente Teacher EN ? Absent Maestro ES ? Quel format ?
- Anti-priority-leak (no-error → no recast) : présente Teacher EN ? Absent ?
- Scaffolding L1/L2 ratio enforce A1-A2 ≥85-90% L2 : présent Teacher EN block format ?
- BIPED Step 2 (Tier 2 EN sprint S52) wired ES ?
- 7 fewshots Lyster cross-tier present in `llm_session` system prompt ?

### 1.B — Patch Maestro Dify prompt (~1j)

Mutations workflow_entity + workflow_history (gotcha CLAUDE.md project pattern n8n). Backup + dual-patch + republish + smoke.

Cible scenarios à fix :
- `a1_t2_concord_gender_001`, `a1_t2_ser_estar_loc_001`, `a1_t2_hay_tener_001` : explicit_correction A1 (Lyster ban)
- `a2_t2_a_personal_001`, `a2_t2_preterite_001` : explicit_correction A2/T2 (Lyster ban T2)
- `risk_comm_breakdown_b1_es_001` : explicit_correction non acceptable B1 risk

### 1.C — Re-record goldens + smoke validation (~30 min)

Si Phase 1.B change réponses sur ≥3/6 smoke scenarios, re-record 24 goldens. Sinon goldens preserved.

DoD Phase 1 : smoke 6/6 ≥ 5/6 + 0 explicit_correction A1-A2 detected.

## Phase 2 — DELE corpus extraction (P0 NEXT, ~2.5j)

3 books acquired pending :
- `cervantes-dele-suite` (DELE A1 Modelo official 40p) → `mini_exam/es_a1.yaml` enrichi + `rubrics/es.yaml` augmenté DELE 4 dims (Adecuación/Coherencia/Corrección/Alcance)
- `bech-tormo-2013-cronometro-dele-b2` (Edinumen 217p) → `mini_exam/es_b2.yaml` task bank
- `alzugaray-2013-preparacion-dele-b2-soluciones` (companion answer key 26p) → rubric calibration B2

## Phase 3 — PCIC Vol C C1-C2 extraction (P1, ~3j)

WebFetch `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/` (technique S53 Vol A+B). Extract → `extracted/cervantes-...c1-c2/`. Audit + patch :
- `curriculum_es.yaml` 98 → ~150 concepts (+52 C1+C2)
- `concept_hints/es.yaml` 103 → ~180 entries
- `functions/es.yaml` 42 → ~80 entries (A2 → C2)

## Phase 4 — DELE A2/B1/C1/C2 acquisition Sinse + injection (P1, ~2j)

- Sinse signup `dele.org` + DL 5 PDFs (~10 min × 5)
- Extract `mini_exam/es_a2.yaml` ... `es_c2.yaml`

## Phase 5 — rules_es.py spaCy migration (P2, ~5-10j)

Alignment EN architecture mature. Lourd refactor — defer post Phase 1+2+3+4 si Phase 1 prompt fix améliore déjà score significativement.

## Phase 6 — CEFR Companion 2020 ES alignment audit (P2, ~1j)

Audit cross-validation PCIC vs Companion 2020 descriptors. Documenter divergences éventuelles.

## Phase 7 — RE-MEASURE Oracle (post Build complete)

Battery panel cross-provider + cache + κ Opus calibration sur Maestro mature. Forecast 22-24/24 (parity Teacher EN MVP S54 20/26).

## Effort cumul (post-pivot)

| Phase | Effort | État |
|---|---|---|
| 0+D — Oracle infra | ~3j | ✅ S55 LIVRÉE (baseline floor 19/24) |
| 1 — Maestro Dify prompt iteration | 2j | **À FAIRE NOW** (P0) |
| 2 — DELE corpus extraction | 2.5j | À faire |
| 3 — PCIC Vol C extraction | 3j | À faire |
| 4 — DELE A2-C2 acquisition + inject | 2j | Sinse manual + extract |
| 5 — rules_es.py spaCy migration | 5-10j | Defer si Phase 1 résout déjà |
| 6 — CEFR Companion 2020 ES audit | 1j | À faire |
| 7 — RE-MEASURE Oracle (post Build) | 1j | Final validation |
| **TOTAL Build → Measure** | **~12-17j** | **MVP légitime cible** |

## Cross-references

- Audit Phase 0.H : [`webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`](../../webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md)
- Audit Phase C ES (S53) : [`webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`](../../webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md)
- Sprint EN parallèle (S54) : [`docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`](../01-pedagogy/sprint-oracle-en-coherence-2026-05.md)
- ADR-013 language scope : [`docs/05-decisions/ADR-013-language-scope-by-tier.md`](../05-decisions/ADR-013-language-scope-by-tier.md)
- ADR-016 authority anchor : [`docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`](../05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md)
- Vault books ES inventory : `vault/knowledge/books/USAGE-MAP.md`
- Vault failures S55 : `vault/projects/academia-ia/failures.md`

---

**Lessons learned S55** : ne pas optimiser l'outil de mesure (Oracle) avant que le sujet à mesurer (Maestro) soit mature à parité Teacher EN. "Build before measure" — sinon le score Oracle reflète l'état sous-mature plutôt que le potentiel target.

## Phase 0 — Foundation (S55 LIVRÉE 2026-05-01)

### Phase 0.A-0.D ✅
- A : Audit prompts Dify Maestro ES — STRUCTURELLEMENT IDENTIQUES Teacher EN (juste traduction). Pb pas dans le prompt LLM.
- B : Diff prompts EN vs ES confirmé.
- C-D : OBSOLETED (audit révèle pb dans judge code, pas prompt)

### Phase 0.E ✅ — Fix judge code cross-lang (commits `d038dd9` + `1ccc53c`)
- `_l2_word_ratio` : default `l2_code='en'`, accent regex EN-only comptait tous accents ES comme FR
- `METALINGUISTIC_PATTERNS` + `EXPLICIT_CORRECTION_PATTERNS` : EN-only, ne détectaient pas patterns ES
- 3 dicts par-target lang ajoutés (en/es/it/de) + `_scenario_lang(scenario)` helper
- 2e gotcha cascadé : typo `scenario.key` au lieu de `scenario.scenario_key` (Pydantic schema field) — fallback silent à 'en' invisible. Fix `1ccc53c`.
- Smoke 1/6 → 3/6 (50%)
- 49/49 oracle tests green

### Phase 0.F ✅ — Full battery 24 baseline post-fix
- Score : **12/24 (50%)** vs 4/24 baseline (+200%)
- Fail breakdown : 9 cf_move + 7 semantic_fidelity + 2 cf_move_partial

### Phase 0.G ✅ — Re-record 24 goldens
- S51 goldens stales vs S53 changes (curriculum_es 51→98, hints 34→103, functions 42 entries)
- 24/24 re-recorded post-fix codebase

### Phase 0.H ✅ — Audit Lyster acceptable_set ES (commits `4c09654` + `c11ee25`)
- Audit doc : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- 7/9 cf_move fails patched (cross-langue Lyster expansion) :
  - +`prompt_plus_remediation` A2/T2 (Doughty & Varela 1998)
  - +`full_recast` B1+/B2/T2-T3 L1-transfer (Lyster Ch4 §3.1)
  - +`explicit_correction` B2-C1/T3 (Lyster + Lira-Gonzales 2024 + Ellis & Sheen 2006)
- 2/9 KEEP forbidden = real Maestro pedagogy issues (defer Phase 1)
- Forecast post-patch : ~19/24 (79%)

### Phase 0.I (en cours) — Re-run battery measure
- Battery 24 × 5 votes single-judge cerebras-fast en cours

## Phase 1 — Maestro Dify prompt fix (à faire)

3 vrais signaux pédagogiques identifiés Phase 0 — fix Dify prompt Maestro `47b0529c` workflow `d3df0ef0` :

### Phase 1.A — Anti-over-correction A1-A2 (~1j)
- Add directive Dify prompt llm_session : "À A1-A2, JAMAIS d'`explicit_correction` ni de `metalinguistic`. Recast implicite uniquement (Lyster Ch 4 §3.1)."
- Cible scenarios : `a2_t2_preterite_001`, `b1_t2_quantifier_001`
- Test : smoke ≥ 4/6 + cf_move_partial = 0 fail explicit_correction A1-A2

### Phase 1.B — Anti-priority-leak (no-error → no recast) (~0.5j)
- Add directive : "Si le learner produit une phrase CORRECTE, ne recast PAS. Réponds au sens, pose une question follow-up."
- Cible scenario : `risk_priority_leak_b1_es_001`
- Test : risk_priority_leak passe en pass post-fix

### Phase 1.C — Apply panel + cache + κ Opus measurement (~1j)
- Run `--panel cross-provider --cache on` sur full battery
- κ Opus super-judge in-chat scoring 24 ES scenarios
- AC2 Gwet inter-run + per-dim
- DoD : κ Opus vs panel ≥ 0.7 sur 3 dims

## Phase 2 — Stable fails + scaffolding (post Phase 1)

### Phase 2.A — Scaffolding L2 ratio fix (~1j)
- Investigation pourquoi Maestro mixe trop de FR (L2 ratio 0.70-0.83 vs target 0.85-0.95)
- Hypothèses : `learner_profile_summary` injecte FR text qui leak ; `l1_watch` block en EN bias bot ; `rubrics_es.yaml` content
- Patch scaffolding policy ES strict (cf `packages/academie-core/academie_core/pedagogy/scaffolding_policy.py`)

### Phase 2.B — Re-record goldens + final E2E validation
- Battery 24 final post Phase 1+2
- 3 runs consécutifs sans régression (DoD)

## Phase 3 — Inject DELE corpus (P1, ~2.5j)

Books acquired pending extraction (cf vault inventaire books ES) :
- `cervantes-dele-suite` (DELE A1 Modelo) → `mini_exam/es_a1.yaml` + DELE rubric Adecuación/Coherencia/Corrección/Alcance
- `bech-tormo-2013-cronometro-dele-b2` (217p) → `mini_exam/es_b2.yaml` task bank
- `alzugaray-2013-preparacion-dele-b2-soluciones` (26p companion) → rubric calibration

## Phase 4 — PCIC Vol C C1-C2 (P1, ~3j)

WebFetch `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/` (technique S53 Vol A+B). Extract → `extracted/cervantes-...c1-c2/`. Audit + patch :
- `curriculum_es.yaml` 98 → ~150 concepts
- `concept_hints/es.yaml` 103 → ~180 entries
- `functions/es.yaml` 42 → ~80 entries (A2 → C2)

DoD : ES flagship A1-C2 complete (gap actuel = C1-C2 underspecified).

## Phase 5 — DELE A2/B1/C1/C2 acquisition + injection (P1, ~2j)

- Sinse signup `dele.org` + DL 5 PDFs (~10 min × 5)
- Extract `mini_exam/es_a2.yaml` ... `es_c2.yaml`
- DoD : exam coverage A1-C2 complete

## Effort cumul

| Phase | Effort | Status |
|---|---|---|
| 0.A-0.H | ~3j | ✅ S55 LIVRÉE |
| 0.I | <1j | 🔄 en cours |
| 1.A-1.C | 2.5j | À faire |
| 2.A-2.B | 1.5j | À faire |
| 3 | 2.5j | À faire (books acquired) |
| 4 | 3j | À faire (WebFetch only) |
| 5 | 2j | À faire (Sinse 50min DL) |
| **TOTAL** | **~14.5j** | dont ~3j MVP critical (Phase 0+1) |

**Phase 0+1 = MVP Oracle Maestro ES** → switch authorize Wave 2 IT/DE.
**Phase 2-5 = enrichissement A1-C2 flagship** à étaler.

## Cross-references

- Audit doc Phase 0.H : [`webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`](../../webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md)
- Audit doc Phase C ES (S53) : [`webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`](../../webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md)
- Sprint EN parallèle (S54) : [`docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`](../01-pedagogy/sprint-oracle-en-coherence-2026-05.md)
- ADR-013 language scope : [`docs/05-decisions/ADR-013-language-scope-by-tier.md`](../05-decisions/ADR-013-language-scope-by-tier.md)
- ADR-016 authority anchor : [`docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`](../05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md)
- Vault books ES inventory : `vault/knowledge/books/USAGE-MAP.md`
- Vault failures S55 : `vault/projects/academia-ia/failures.md`
