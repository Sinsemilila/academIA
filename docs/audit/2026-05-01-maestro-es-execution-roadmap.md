---
title: Maestro ES execution roadmap — chronological action plan to MVP DoD legitimate
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 55
tags: [audit, multilang, methodology, plan]
ai_summary: "Plan exécution chronologique Maestro ES Phase 1+ : 5 tiers ordonnés avec dépendances + parallélisation + milestones hebdomadaires + RE-MEASURE Oracle final."
---

# Maestro ES — execution roadmap (chronological action plan)

**Context** : Synthèse exécutable des 2 SoT canoniques shipped S55 :
- **Build-gap audit** (`33f842e` ne passe pas — l'autre commit `aa75165`) : 16 items priorisés P0-P3, tracking shippable
- **Teacher EN reference architecture** (`33f842e`) : template how-to-build per-lang

**End goal** : Maestro ES MVP DoD légitime = Re-Oracle final score 22-24/24 panel certified avec κ Opus ≥0.7 — POST construction structurelle parity Teacher EN.

**Constraint** : Le score 19/24 atteint S55 = baseline floor pré-build, **pas MVP**. Il a été atteint en optimisant l'OUTIL de mesure avant le sujet à mesurer (anti-pattern Goodhart). Re-Oracle final ne sera valable que post-Build complet.

---

# 🎯 5 Tiers chronologiques

## Tier 1 — Quick wins prompt fix (~2-3j) [P0 BLOQUANT]

**Goal** : éliminer les 5 fails restants du baseline floor 19/24 (tous explicit_correction A1-A2 par Maestro Dify prompt non-itéré).

**Forecast** : score battery 19→**22-23/24** sans toucher data layer (validation ciblée du fix prompt).

### Items
| ID | Action | Effort | Dépendances | File(s) modifiés |
|---|---|---|---|---|
| G5.1 | Maestro Dify `llm_session` : add `=== REGLAS LYSTER POR NIVEL CEFR ===` (anti-A1-A2 metalinguistic + anti-explicit) + `=== ANTI-PRIORITY-LEAK ===` | 1j patch + 0.5j smoke validation | aucune | `workflows.graph` (DB UPDATE Dify draft + published EN+ES) |
| G5.2 | Teacher EN `llm_session` apply same directives (cross-langue consistency, prevent EN regression) | 0.5j | G5.1 (méthode validée) | idem (Teacher EN workflow) |
| G5.3 | Doc Dify prompt version control runbook (procedure dual-patch backup → patch → republish → smoke) | 0.3j | aucune | `docs/99-runbooks/dify-prompt-patch.md` |

### DoD Tier 1
- Smoke maestro_es 6/6 ≥ 5/6 + 0 explicit_correction A1-A2 detected
- Smoke teacher_en 6/6 ≥ 5/6 (no regression)
- Battery maestro_es ≥22/24 (forecast 22-23)

### Output
- 3 ships granulaires
- Si 22-23/24 atteint → Tier 1 = SUFFISANT pour CONTINUE Build (Tier 2+3+4) sans urgence prompt
- Si <22/24 → reprendre Phase 1.B audit prompt avec scope élargi

---

## Tier 2 — Authority anchor extraction (parallel, ~5-7j cumul) [P1]

**Goal** : Acquérir + extraire toutes les sources d'autorité ES pending pour pouvoir construire data layer complète A1-C2.

**Parallélisable** : 3 streams indépendants (peuvent s'exécuter en parallèle ou séquentiel selon bandwidth).

### Stream A : PCIC Vol C C1-C2 (Claude WebFetch, ~2-3j)
| ID | Action | Effort | File(s) |
|---|---|---|---|
| G6.A | WebFetch `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/` Vol C Gramática inventario C1+C2 | 0.5j | `extracted/cervantes-2006-plan-curricular-c1-c2/grammar-by-level.yaml` |
| G6.B | WebFetch Vol C Funciones C1+C2 | 0.5j | `extracted/cervantes-2006-plan-curricular-c1-c2/funciones-by-level.yaml` |
| G6.C | Audit doc PCIC Vol C vs current curriculum_es 98 | 1j | `webapp/backend/docs/audit/2026-05-XX-curriculum-es-vs-pcic-c1c2.md` |

### Stream B : DELE corpus acquired (Claude extract, ~2.5j)
3 books déjà téléchargés dans library, juste extract :
| ID | Action | Effort | File(s) |
|---|---|---|---|
| G7.3a | DELE A1 Modelo official extraction | 0.5j | `extracted/cervantes-dele-a1/` (rubric_dele_a1 + mini_exam_a1) |
| G7.3b | Cronómetro B2 (Edinumen 217p) extraction | 1.5j | `extracted/bech-tormo-2013-cronometro-dele-b2/` (mini_exam_b2 task bank) |
| G7.3c | Preparación B2 Soluciones extraction (companion 26p) | 0.3j | rubric calibration B2 |

### Stream C : DELE A2/B1/C1/C2 acquisition (Sinse manual, ~50 min total)
| ID | Action | Effort | File(s) |
|---|---|---|---|
| G7.3d | Sinse signup `dele.org` + DL 5 PDFs | 50 min Sinse | `library/dele-modelo-{a2,b1,c1,c2}.pdf` + companion files |
| G7.3e | Claude extract → mini_exam YAMLs A2-C2 | 1.5j Claude | `mini_exam/es_a2.yaml` ... `es_c2.yaml` |

### Critical path Tier 2
Stream A (PCIC C1-C2) **bloque** Tier 3.G6 + Tier 3.G7.1 (curriculum & functions C1-C2 expansion).
Stream B+C **NE bloque PAS** Tier 3 (DELE rubric + mini_exam = enrichment, pas curriculum-blocking).

### DoD Tier 2
- 4 PDFs extracted (PCIC C1-C2 + 3 DELE acquired)
- 5 PDFs acquired Sinse (DELE A2/B1/C1/C2)
- 3-4 audit docs livrés

---

## Tier 3 — Data layer expansion (parallel post-Tier-2 Stream A, ~5-6j cumul) [P1]

**Goal** : Étendre les YAMLs ES à parité Teacher EN A1-C2 + Functions parité.

**Parallélisable** : 3 streams indépendants post Stream A Tier 2 (PCIC Vol C extracted).

### Stream D : Curriculum + concept_hints expansion ES C1-C2
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G6.D | Patch `curriculum_es.yaml` 98→~150 (+52 concepts C1+C2) | 1j | Tier 2.A | `curriculum_es.yaml` |
| G6.E | Sync `concept_hints/es.yaml` 103→~180 entries | 1j | G6.D | `concept_hints/es.yaml` |
| G6.F | Test parity range update `test_curriculum_es_total_concepts_reasonable` 80-130→100-200 | 0.1j | G6.D | `tests/test_yaml_schema.py` |

### Stream E : Functions ES B1-C2 + EN expansion
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G7.1 | Étendre `functions/es.yaml` 42→~80 (PCIC Funciones B1-C2 from Tier 2.A) | 1.5j | Tier 2.A | `functions/es.yaml` |
| G7.2 | Étendre `functions/en.yaml` 10→~50 (CEFR Companion 2020 Ch3 production/interaction full A1-C2) | 1.5j | aucune (déjà extract S53) | `functions/en.yaml` |

### Stream F : DELE rubric integration
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G7.3.f | Patch `rubrics/es.yaml` ajouter dimensions DELE (Adecuación/Coherencia/Corrección/Alcance) | 1j | Tier 2.B | `rubrics/es.yaml` |

### DoD Tier 3
- `curriculum_es` 150 concepts validated (test parity)
- `concept_hints/es` 180 entries 100% coverage curriculum
- `functions/es` 80 entries A1-C2 PCIC-aligned
- `functions/en` 50 entries CEFR Companion-aligned
- `rubrics/es` augmenté DELE Criterios

---

## Tier 4 — Rules detector + L1 transfer (parallel, ~5j cumul) [P1]

**Goal** : Étendre rules_es.py architecture parity Teacher EN + L1 calques expansion.

**Parallélisable** avec Tier 3 (independent).

### Items
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G8.1 | Étendre `rules_es.py` couverture 12 codes manquants (V:TENSE/V:FORM/V:SVA/V:ASPECT/V:AUX/V:MODAL/V:COND/V:INFL/V:PHRASAL/V:PASS/V:EXIST/V:CHOICE) | 3j | aucune | `taxonomy/rules_es.py` |
| G8.3 | Étendre FP whitelists ES (PROPER_NOUNS_ES + CONTRACTIONS_ES "al/del" + LEX_CALQUE_ES + FRENCH_COGNATES_ES) | 1j | aucune | `taxonomy/rules_es.py` |
| G8.4 | Compléter `l1_transfer/fr_to_es.yaml` 12→25+ entries (FR→ES specific calques : por/para, a/al, ser/estar, gustar inversion, subjuntivo triggers) | 1j | aucune | `l1_transfer/fr_to_es.yaml` |

### DoD Tier 4
- `rules_es.py` cover 16+ error codes (parity Teacher EN ERROR_CODE_TO_FAMILY)
- FP whitelists ES nouvelles
- `l1_transfer/fr_to_es.yaml` 25+ entries
- pytest test_rules_coverage_es.py green

### Note
G8.2 (rules_es spaCy migration) **DEFER P3** — strategic decision : si Tier 1+3+4 résout déjà signaux, defer indefiniment. Architecture regex acceptable si coverage error codes parity.

---

## Tier 5 — Oracle scenarios + quality gates (parallel, ~5-6j cumul) [P1+P2]

**Goal** : Rebalance + extend Oracle scenarios ES pour battery measure post-Build trustworthy.

### Stream G : ES scenarios rebalance
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G9.1 | Rebalance ES — demote 2-3 A1 surplus (5 actuels vs EN 1) + add 3-4 C1 scenarios post Tier 3.G6 | 1.5j | Tier 3.G6 (curriculum C1-C2 done) | `scripts/oracle/scenarios/maestro_es/` |
| G9.2 | Add 2-3 ES B2 edge cases (parity EN coverage) | 1j | aucune | idem |
| G9.3 | Add 2-3 ES multi-turn scenarios (parity EN 8 multi/risk) | 1j | aucune | idem |

### Stream H : Judge fewshots ES expand
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G10.1 | Étendre `CF_MOVE_PROMPT` ES fewshots 5→10+ (Lyster cross-tier C1+C2 added) | 0.5j | Tier 1 done | `scripts/oracle/judges/llm_pairwise.py` |

### Stream I : Tolerance matrix validation
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G11.1 | Tolerance matrix ES validation kappa drift check vs EN baseline | 0.5j | Tier 4.G8.1 done | `tolerance_matrix_v2_overrides.yaml` |

### Stream J : Refactor + tests (P2 nice-to-have)
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| G12.1 | Refactor unify `build_scenarios.py` + `build_scenarios_maestro_es.py` lang-parametrized | 2j | aucune | `scripts/oracle/build_scenarios.py` |
| G13.1 | Create `test_judges_cf_move_es.py` kappa ES error pairs validation | 0.5j | Tier 5.H done | `scripts/oracle/tests/test_judges_cf_move_es.py` |

### DoD Tier 5
- 28-30 ES scenarios (vs 24 actuels, +4-6 added)
- κ drift Tolerance matrix ES validated
- (P2) build_scenarios refactored + test_judges_cf_move_es

---

## Tier 6 — RE-MEASURE Oracle (FINAL, ~2-3j) [Validation]

**Goal** : Battery panel cross-provider + cache + κ Opus calibration sur Maestro **mature** post Tier 1-5. Score reflète maintenant le potentiel target, pas le sous-mature.

### Items
| ID | Action | Effort | Dépend | File(s) |
|---|---|---|---|---|
| RM.1 | Re-record 24-30 ES goldens post-Build complet | 0.5j | Tier 1-5 done | `scenarios/maestro_es/golden/` |
| RM.2 | Battery `--mode full --panel cross-provider --cache on` | 0.5j | RM.1 | `baselines/2026-05-XX-maestro-es-final.json` |
| RM.3 | κ Opus super-judge in-chat scoring 28-30 ES scenarios | 1h Opus chat | RM.2 | `baselines/2026-05-XX-opus-supervisor-scores-es-final.yaml` |
| RM.4 | Compute AC2 Gwet + per-dim metrics | 0.2j | RM.2+RM.3 | terminal output |
| RM.5 | Audit doc final Maestro ES MVP COMPLETE + lessons learned | 0.5j | RM.1-4 | `webapp/backend/docs/audit/2026-05-XX-maestro-es-mvp-complete.md` |

### DoD MVP Maestro ES (FINAL)
- Score panel cross-provider **≥ 22/24** (parity Teacher EN MVP S54 20/26)
- AC2 ≥ 0.7 sur 3 dims (cf_move, register, semantic_fidelity)
- κ Opus vs panel ≥ 0.7 sur 3 dims
- 0 stable structural fail (3 runs consécutifs)
- 0 `explicit_correction` A1-A2 (Lyster ban respected)
- 0 priority leak risk scenario

---

# 📅 Calendrier indicatif (5-6 sessions, ~22-30j cumul effort)

## Session N+1 (Tier 1 — quick wins ~2-3j)
- [x] G5.1 Maestro Dify prompt fix — Lyster CEFR caveat inline + ❌/✅ examples + anti-priority-leak (S56, scripts/sprint-maestro-es/02_*.py v2). Smoke 5/6 ≥5/6 ✅, 0 explicit_correction A1-A2 ✅. 1 fail `a2_t2_a_personal_001` semantic_fidelity = golden obsolete (recast vs old elicitation).
- [x] G5.1.C Re-record 24 goldens post-patch (S56). Smoke 6/6 ✅ confirmed.
- [x] G5.2 Teacher EN apply same — script 03_*.py FR/EN equivalent (S56). Smoke 6/6 ✅ post re-record 26 goldens. No regression EN.
- [x] G5.3 Runbook Dify patch — `docs/99-runbooks/dify-prompt-patch.md` (S56). 6-step procedure, dual-patch, $$-quoting, cache gotchas, rollback.
- [x] Battery quick post Tier 1 (S56) — **16/24 (67%) ❌ GATE FAIL** (forecast 22-23 raté, regression vs baseline 19/24). Postmortem : `webapp/backend/docs/audit/2026-05-01-maestro-es-tier1-battery-postmortem.md`. 8 fails / 4 patterns identifiés. **Phase 1.B v3 patch needed avant Tier 2** per gate L264-265.
- [x] **Phase 1.B v3** (S56, ~0.5j) — refactor v2 blocks (4 fixes Pattern 1+2+3+4). Scripts 04+05. Smoke ES 6/6 + EN 6/6 ✅. Battery v3 = **18/24 (75%)** : +2 vs v2, -1 vs baseline. Postmortem : `webapp/backend/docs/audit/2026-05-01-maestro-es-tier1-v3-postmortem.md`.

**Milestone final S56 — Tier 1 close partial** : Per Option C strict (<19 → scope-cap), prompt iteration locked at v3 floor 18/24. Tier 2 unblocked. Les 6 fails restants (3 ANTI-LEAK silent + 1 false_friend bypass + 2 acceptable_set) seront résolus par Tier 5 (acceptable_set rebalance) + Tier 6 RE-MEASURE post Build complet.

## Session N+2 to N+3 (Tier 2+3+4 parallel — ~10-14j)

**Stream A → D path** (PCIC C1-C2 → curriculum/hints/functions ES expansion) :
- [x] G6.A WebFetch PCIC Vol C Gramática (S56) — `extracted/cervantes-2006-plan-curricular-c1-c2/grammar-by-level.yaml` 15 macro-sections × 2 niveaux
- [x] G6.B WebFetch PCIC Vol C Funciones (S56) — `funciones-by-level.yaml` macro-sections 1-4 (sections 5+6 truncated, fallback acquisition flagged)
- [x] G6.C Audit PCIC Vol C vs curriculum_es (S56) — `webapp/backend/docs/audit/2026-05-01-curriculum-es-vs-pcic-c1c2.md`. Gap : 22 NEW C1 + 17 NEW C2 concepts identified for G6.D.
- [x] G6.D `curriculum_es.yaml` 98→**137** (S56, +39 NEW C1+C2 PCIC Vol C). 13 polish A2-B2 deferred (separate stratification sprint). Tests es_content_pack + yaml_parity green.
- [x] G6.E `concept_hints/es.yaml` 103→**142** (S56, +39 entries 1:1 with curriculum_es C1+C2 expansion). FR-oriented hints with PCIC examples. Tests green.
- [x] G7.1 `functions/es.yaml` 42→**75** (S56, +33 entries B1/B2/C1/C2 PCIC Vol B + Vol C funciones). Sub-target 80 — sections 4-6 truncated par WebFetch (fallback acquisition flagged).
- [x] G7.2 `functions/en.yaml` 10→**41** (S56, +31 entries B1/B2/C1/C2 from CEFR Companion 2020 + Threshold/Vantage 1990). Sub-target 50.

**Stream B+C** (DELE corpus, parallel) :
- [~] G7.3a DELE A1 modelo extraction (S56 partial) — `extracted/cervantes-dele-a1/rubric.yaml` (structure + 4 Criterios + calibration recommendations). Full item bank extraction (25 lectura + 25 auditiva + 2 escritura + 4 oral = 56 items) deferred to dedicated sprint (~2-3j Claude work).
- [ ] G7.3b Cronómetro B2 (Edinumen 217p) extraction → `extracted/bech-tormo-2013-cronometro-dele-b2/`
- [ ] G7.3c Preparación B2 Soluciones extraction (companion 26p) → rubric calibration B2
- [~] G7.3d Sinse acquisition DELE A2-C2 (S56 — Sinse downloaded **hojas de respuestas** instead of **modelos de examen** — re-DL needed for full content. Hojas useful for structural calibration only)
- [ ] G7.3e Claude extract DELE A2-C2 mini_exam (blocked on G7.3d full re-DL)
- [x] G7.3f Patch `rubrics/es.yaml` DELE Criterios (S56) — 4 dimensions (Adecuación / Coherencia / Corrección / Alcance) avec indicators_by_level A1-C2 + scoring_template 0-3. RubricPack schema relaxed to _Lax (forward-compat). Tests green.

**Tier 4** (rules + L1, parallel) :
- [x] G8.1 `rules_es.py` +12 codes (S56) — V:TENSE, V:FORM, V:SVA, V:ASPECT, V:AUX, V:MODAL, V:COND, V:INFL, V:PHRASAL, V:PASS, V:EXIST, V:CHOICE. Regex-light high-precision low-recall. Tests 14/14 patterns. ERROR_CODE_TO_FAMILY pre-registered S51 — auto-integrates with tolerance_matrix pipeline.
- [x] G8.3 FP whitelists ES (S56) — PROPER_NOUNS_ES expanded (countries/cities/regions/monuments) + CONTRACTIONS_ES (al/del) + LEX_CALQUE_ES_WHITELIST (cognates) + FRENCH_COGNATES_ES whitelist (defensive infrastructure for future calque detectors).
- [x] G8.4 `l1_transfer/fr_to_es.yaml` 14→**30** (S56, +16 entries — tener_age, gender_calque_cognat, 3 subjuntivo families, estar_progresivo, acabar_venir_de, imperativo_pronombres, cleft_sentences, possessive_placement, acentuacion_diacritica + 5 more).

**Milestone** : data layer ES parity Teacher EN + DELE corpus integrated + rules detector mature.

## Session N+4 (Tier 5 — Oracle scenarios + quality gates ~5-6j)

- [ ] G9.1 Rebalance ES + add C1 scenarios post-G6
- [ ] G9.2 ES B2 edge cases
- [ ] G9.3 ES multi-turn scenarios
- [ ] G10.1 CF_MOVE fewshots ES 5→10+
- [ ] G11.1 Tolerance matrix ES validation
- [ ] (P2) G12.1 build_scenarios refactor
- [ ] (P2) G13.1 test_judges_cf_move_es

**Milestone** : Oracle infra ready pour mesure trustworthy post-Build.

## Session N+5 (Tier 6 — RE-MEASURE Oracle FINAL ~2-3j)

- [ ] RM.1 Re-record 28-30 ES goldens
- [ ] RM.2 Battery panel + cache
- [ ] RM.3 κ Opus calibration in-chat
- [ ] RM.4 Compute AC2 + per-dim metrics
- [ ] RM.5 Audit doc final + lessons learned

**Milestone** : **Maestro ES MVP COMPLETE legit** (score ≥22/24 + κ ≥0.7 + 0 stable structural fail).

→ Wave 2 IT/DE authorize (mêmes étapes appliquées Wave 2).

---

# 🚦 Decision gates par Tier

## Gate Tier 1 (post G5.1+G5.2 + smoke)
- ✅ Smoke 5/6 + 0 explicit A1-A2 → CONTINUE Tier 2
- ⚠️ Smoke <5/6 → Phase 1.B prompt audit étendu (~+1-2j)

## Gate Tier 2 (post extractions)
- ✅ 4 PDFs extracted (PCIC + 3 DELE acquired) → CONTINUE Tier 3
- ⚠️ PCIC Vol C inaccessible → fallback Sinse manual scrape ; DELE alt sources

## Gate Tier 3 (post curriculum + hints + functions expansion)
- ✅ test_yaml_schema 49/49 green + lint 24/24 → CONTINUE Tier 4-5
- ⚠️ schema validation fails → fix before progress

## Gate Tier 4 (post rules + L1)
- ✅ pytest test_rules_coverage_es green + smoke parity → CONTINUE Tier 5
- ⚠️ regression rules → triage et patch

## Gate Tier 5 (post scenarios rebalance)
- ✅ 28-30 scenarios validated lint → CONTINUE Tier 6
- ⚠️ scenario lint fail → fix YAML

## Gate Tier 6 (FINAL DoD)
- ✅ ≥22/24 + AC2 ≥0.7 + κ ≥0.7 → MVP COMPLETE → Wave 2 IT/DE authorize
- ⚠️ <22/24 → diagnostic per-dim, decide Phase 7 (additional iterations) OR scope-cap
- ⚠️ κ <0.7 → re-calibrate panel (panel members switch ?) OR Opus prompt re-run

---

# 🎯 Items hors scope (defer ou future Wave)

| ID | Action | Reason defer |
|---|---|---|
| G8.2 | rules_es.py spaCy migration | Strategic decision Tier 4 — defer si regex coverage suffisante post G8.1+G8.3 |
| G14 | Anti-patterns ES bank | Future P2 si fewshots insuffisants pour judge |
| G15 | Mediation dimension NEW 2020 (CEFR Companion Ch3) | Sprint dédié post-MVP (cross-lang feature, ~3-4j) |
| G16 | Skills-based reorganization (Reception/Production/Interaction/Mediation) | Major design refactor, post-MVP |

---

# 🔗 Cross-references

- **SoT 1** : `docs/audit/2026-05-01-maestro-es-vs-teacher-en-build-gap.md` — items granulaires P0-P3
- **SoT 2** : `docs/audit/2026-05-01-teacher-en-reference-architecture.md` — template how-to-build per-lang
- **Sprint plan** : `docs/00-project/sprint-maestro-es-2026-05.md` — sprint v2 pivot Build avant Measure
- **Audit Phase 0.H** : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- **Audit Phase C ES (S53)** : `webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`
- **ADRs** : 013 (language scope) / 014 (knowledge extraction) / 015 (JP eval) / 016 (authority anchor)

---

# 📊 Summary

| Tier | Effort | Output | DoD |
|---|---|---|---|
| 1 — Quick wins prompt | 2-3j | Score 22-23/24 sans data touch | smoke 5/6 ES, no regression EN |
| 2 — Authority extract | 5-7j | 4 PDFs extracted + 5 acquired | docs livrés |
| 3 — Data layer expansion | 5-6j | Curriculum 150 + hints 180 + functions 80 | tests parity green |
| 4 — Rules + L1 | 5j | rules_es 16+ codes + 25+ l1 transfers | pytest green |
| 5 — Scenarios + quality | 5-6j | 28-30 scenarios + judge ext + tests | lint 28-30 green |
| 6 — RE-MEASURE Oracle | 2-3j | Final battery + κ Opus + audit doc | **MVP COMPLETE** ≥22/24 + κ≥0.7 |
| **TOTAL** | **~22-30j** | **Maestro ES MVP legit** | |

**Forecast** : 5 sessions focused (~5-6j chacune) → MVP COMPLETE legit. Wave 2 IT/DE authorize après.

**Si parallélisation max** : Sinse + Claude work parallel → ~3-4 weeks calendaires si focus 50% (refactor v1.0 dependency).

**Critical path** : Tier 1 (prompt fix) → Tier 2.A (PCIC C1-C2) → Tier 3.D-E (curriculum/functions ES) → Tier 5 (scenarios) → Tier 6 (RE-MEASURE).

Tier 2.B-C + Tier 3.F + Tier 4 = parallélisables au critical path.
