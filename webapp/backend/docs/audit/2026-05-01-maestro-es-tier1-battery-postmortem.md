---
title: Maestro ES Tier 1 battery postmortem — 16/24 (gate fail, regression vs S55 baseline 19/24)
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 56
tags: [audit, oracle, multilang, methodology]
ai_summary: "Tier 1 G5.1-G5.3 patches shipped, smoke 6/6 ✅, but full battery 16/24 < 22/24 DoD. 8 fails diagnosed in 4 patterns. Phase 1.B v3 patch needed before Tier 2."
---

# Maestro ES Tier 1 battery postmortem (S56)

## TL;DR

- **Patches shipped (G5.1 + G5.2 + G5.3)** : Lyster CEFR caveat + ❌/✅ examples + anti-priority-leak applied to Maestro ES (`47b0529c`) + Teacher EN (`39565197`). Runbook `docs/99-runbooks/dify-prompt-patch.md` documented.
- **Smoke 6/6 ES + 6/6 EN ✅** : the 6 A1-A2 fail scenarios from S55 baseline 19/24 are all fixed. 0 explicit_correction A1-A2 detected.
- **Full battery 24 ES — 16/24 ❌ (67%)** : regression vs S55 baseline 19/24 (-3). Tier 1 forecast was 22-23/24.
- **Decision gate per execution-roadmap L264-265** : `<22/24 → Phase 1.B prompt audit étendu (~+1-2j)`.

## Battery output (run_hash `1e8bf444db2e8726`)

```
16 passed / 8 failed / 0 skipped / 24 total
```

Pass : `a1_t2_art_prof_001`, `a1_t2_concord_gender_001`, `a1_t2_hay_tener_001`, `a1_t2_ser_estar_loc_001`, `a1_t2_ser_estar_state_001`, `a2_t2_a_personal_001`, `a2_t3_por_para_001`, `b1_t2_quantifier_001`, `b1_t3_subjuntivo_pres_001`, `b2_t3_condicional_001`, `b2_t3_imperfecto_pret_001`, `c1_t3_subjuntivo_imp_001`, `multi_a1_ser_estar_no_uptake_001`, `multi_a2_por_para_uptake_001`, `multi_b1_subj_partial_001`, `risk_t4_regression_a2_es_001`.

## 8 fails — 4 patterns

### Pattern 1 — Patch over-softens A1 (2 fails)

Notre bloc Lyster v2 dit `PREFERIDO  implicit_recast (T1-T2) y partial_recast (T3)`. Maestro applique strictement implicit_recast / silent. Mais Lyster Ch 4 §3.1 nuance : *"A1 implicit recasts may go unnoticed → prefer FULL or PARTIAL recast for salience"*.

| Scenario | Maestro move | Acceptable_set | Lyster says |
|---|---|---|---|
| `risk_a1_metalinguistic_leak_es_001` | silent | clarif, full_recast, partial_recast | A1 needs salient recast — implicit too low salience |
| `risk_l1_drift_a1_es_001` | implicit_recast | clarif, full_recast, partial_recast | idem |

**Fix v3** : remplacer `PREFERIDO implicit_recast (T1-T2)` par `PREFERIDO partial_recast (T2-T3) — implicit_recast OK seulement si la erreur est mineure et le pattern est récurrent visible (T1)`.

### Pattern 2 — ANTI-PRIORITY-LEAK over-applies to genuine-error B1 (2 fails)

Notre bloc `ANTI-PRIORITY-LEAK` instruit silent quand `error_feedback` vide. Maestro applique silent même quand l'erreur est genuine mais le judge le reclasse comme `silent` move (no visible CF).

| Scenario | Maestro move | Acceptable_set | Issue |
|---|---|---|---|
| `risk_priority_leak_b1_es_001` | silent | clarif, elicit, metaling, partial_recast | Anti-leak block too aggressive — silent even when error present |
| `risk_comm_breakdown_b1_es_001` | prompt_plus_remediation | clarif, elicit, metaling, partial_recast | B1 communication breakdown should clarif/elicit, not prompt+rem |

**Fix v3** : ANTI-PRIORITY-LEAK doit être conditionné par `error_feedback` reading : "SOLO si error_feedback vide. SI error_feedback contient items T2+, ignora este bloc et aplica MAPPING TIER".

### Pattern 3 — Insufficient B1-B2/T2 nuance (3 fails)

Notre caveat est `⚠️ SI niveau A1 ou A2 : JAMAIS metalinguistic/explicit_correction`. Aucun gate pour B1-B2/T2 où Lyster dit aussi "prefer recast over explicit at communicative tier".

| Scenario | Maestro move | Acceptable_set | Lyster Phase 0.H |
|---|---|---|---|
| `a2_t2_preterite_001` | prompt_plus_remediation | clarif, elicit, full_recast, partial_recast | A2/T2 = communicative, prompt+rem too forceful |
| `b1_t3_gustar_subj_001` | explicit_correction | clarif, elicit, full_recast, metaling, partial_recast | B1/T3 acc explicitly excludes explicit_correction |
| `b2_t2_false_friend_001` | explicit_correction | clarif, elicit, full_recast, metaling, partial_recast | B2/T2 acc excludes explicit (T2 = communicative tier even at B2) |

**Fix v3** : étendre caveat à T2 cross-niveau :
```
T3 penalized → ELICITATION ↔ METALINGUISTIC
              ⚠️ SI niveau A1 o A2 : JAMAIS metalinguistic → partial_recast
              ⚠️ SI niveau B1 + tier T2 : JAMAIS metalinguistic/explicit → recast
T4 regressive → PROMPT + REMEDIATION
              ⚠️ SI niveau A1 o A2 : JAMAIS explicit_correction → prompt natural
              ⚠️ SI tier T2 cross-niveau : JAMAIS prompt_plus_remediation → recast (T2 = communicative, T4 escalation forbidden in T2)
```

### Pattern 4 — Register drift (1 fail)

`multi_b2_imperfecto_no_uptake_001` : Maestro répond en register A2 sur learner level B2.

Hypothèse : nos exemples ❌/✅ A1-A2 omniprésents dans le prompt amorcent gpt-4o-mini à softer toujours, même hors A1-A2. Le bloc devrait inclure des exemples B2-C1 explicit_correction pour balance.

**Fix v3** : ajouter 1-2 exemples B2/C1 explicit_correction ✅ pour montrer que le LLM doit varier le register selon niveau.

## Recommended action — Phase 1.B v3 patch

Effort estimé : **0.5j** (refactor existing v2 blocs avec patterns ci-dessus). Smoke + battery quick re-run après.

Forecast post-v3 : 22-23/24 (back to or above baseline).

Si v3 toujours <22/24 : **scope cap** acté — 19-20/24 = floor légitime sans data layer touch ; passer à Tier 2-5 (data layer expansion) pour atteindre les +3-4 fails restants.

## Cross-references

- v2 patches : `scripts/sprint-maestro-es/02_*.py` + `03_*.py`
- Phase 0.H acceptable_set audit : `webapp/backend/docs/audit/2026-05-01-maestro-es-acceptable-set-audit.md`
- Sprint plan v2 : `docs/00-project/sprint-maestro-es-2026-05.md`
- Execution roadmap : `docs/audit/2026-05-01-maestro-es-execution-roadmap.md`
- Battery JSON : `/tmp/oracle_run.json` (run_hash `1e8bf444db2e8726`, 240 rows in `oracle_run_log`)
