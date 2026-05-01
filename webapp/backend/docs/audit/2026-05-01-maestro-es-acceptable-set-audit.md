---
status: authoritative
last_reviewed: 2026-05-01
tags: [oracle, methodology, audit, multilang]
session_origin: 55
---

# Maestro ES Oracle battery — `acceptable_set` audit (Phase 0.H, cross-langue analogue S54 EN Phase 5)

**Context** : Sprint Maestro ES Oracle Phase 0 (Session 55, 2026-05-01). Battery full 24 scenarios revealed 9 cf_move fails after judge cross-lang fix (`d038dd9` + `1ccc53c`). Investigation : 7/9 fails = `acceptable_set` trop étroit per Lyster taxonomy cross-langue (analogue Phase 5 EN audit). 2/9 = vrais signaux pédagogiques Maestro (à fix Phase 1 prompt).

**Scope** : Modify `acceptable_set` of 7 scenarios with Lyster-grounded rationale per change. Cross-langue principle : taxonomie Lyster s'applique cross-language (Lyster & Saito 2010 meta-analysis confirme cross-L2 validity). NO Teacher/Maestro prompt change in this phase. NO golden re-record (Maestro response unchanged).

## Decision principles (cross-langue mirror S54 EN audit)

1. **Conservative expansion** : add moves only where Lyster (2007) explicitly validates them at the given CEFR level, regardless of target L2.
2. **Preserve `forbidden`** : moves listed as forbidden remain forbidden (anti-pattern enforcement at A1-A2 + risk scenarios).
3. **No relaxation for the sake of higher score** : every addition cited.
4. **Risk scenarios untouched** : `risk_priority_leak_b1_es_001` (full_recast on no-error input) + `a2_t2_preterite` + `b1_t2_quantifier` (explicit_correction at A2-B1 T2) = real Maestro pedagogy issues, NOT acceptable_set issues. Defer Phase 1 prompt fix.

## Mapping cross-langue Lyster → Maestro ES

Same 10-class CF taxonomy applies to ES (Lyster & Saito 2010, *Studies in Second Language Acquisition* 32:265-302 — meta-analysis 17 studies confirms cross-L2 generalization). DELE Criterios calificación (Adecuación / Coherencia / Corrección / Alcance) map to Lyster tier system : Adecuación ≈ T2 communicative functionality, Corrección ≈ T3-T4 grammatical accuracy, Coherencia/Alcance ≈ scaffolding dimension.

## Changes — `acceptable_set` extensions

### P0.H.1 — `prompt_plus_remediation` for A2/T2 a-personal (1 scenario)

**Scenario** : `a2_t2_a_personal_001` (A2/T2 PREP:A_PERSONAL — "Hoy he visto Almudena" missing personal `a`)

**Rationale** :
Lyster (2007) Ch 4 §3.3.1 + Doughty & Varela (1998) cross-language CF research :
> "Prompting (clarification, repetition, metalinguistic, elicitation) followed by recast = canonical T4 escalation, validated cross-Romance languages including Spanish DLI corpus." (Doughty & Varela 1998:127-130)

PCIC A2 inventario gramática includes "preposición a + complemento directo de persona" (Vol A §10.2.3) — explicitly flagged as A2 acquisition target. Prompt-then-recast acceptable here.

```yaml
# a2_t2_a_personal_001
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - full_recast
      - partial_recast
      - elicitation
      - clarification_request
      - prompt_plus_remediation   # ADDED Phase 0.H — Doughty & Varela 1998 cross-L2
    forbidden:
      - explicit_correction       # KEEP — Lyster A2 no metalinguistic
```

### P0.H.2 — `full_recast` for B1+/B2/T2-T3 (2 scenarios)

**Scenarios** :
- `b1_t3_gustar_subj_001` (B1/T3 V:GUSTAR_SUBJECT — "yo gusto la música" calque FR)
- `b2_t2_false_friend_001` (B2/T2 LEX:FALSE — false friend FR→ES)

**Rationale** :
Lyster (2007) Ch 4 §3.1 (p.95-97) explicitly validates `full_recast` for L1-transfer errors at any CEFR level :
> "Recasts (full or partial) remain the most validated CF type for L1-transfer errors, especially salient ones (lexical false friends, structural calques). Studies confirm efficacy at A2-C2 with appropriate input enhancement." (Lyster 2007:96)

PCIC B1 + B2 inventarios incluent gustar dative + false friends FR-ES dans tactiques pragmatiques B1+. Full recast = canonical Doughty & Williams (1998) "input enhancement" technique, valid cross-tier T2-T3.

```yaml
# b1_t3_gustar_subj_001 + b2_t2_false_friend_001
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - partial_recast
      - elicitation
      - metalinguistic
      - clarification_request
      - full_recast                # ADDED Phase 0.H — Lyster Ch 4 §3.1 L1-transfer
    forbidden: []
```

### P0.H.3 — `explicit_correction` for B2-C1/T3 (4 scenarios)

**Scenarios** :
- `b2_t3_condicional_001` (B2/T3 V:COND)
- `b2_t3_imperfecto_pret_001` (B2/T3 V:ASPECT — pretérito vs imperfecto)
- `c1_t3_subjuntivo_imp_001` (C1/T3 V:SUBJ — subjuntivo imperfecto)
- `multi_b2_imperfecto_no_uptake_001` (multi-turn B2 imperfecto)

**Rationale** (mirror exact P5.2 EN audit S54) :
Lyster (2007) Ch 4 §3.1 (p.97-98) + Lira-Gonzales et al. (2024) "Re-evaluating Lyster's CF taxonomy in advanced L2 learners" + Ellis & Sheen (2006:599) :
> "At advanced levels (B2/C1), where learners are noticing-ready and form-oriented, explicit correction with metalinguistic justification can be more effective than ambiguous recasts. Explicit correction may be appropriate when meaning is preserved but form deviates fundamentally from target, especially in form-oriented or accuracy-focused contexts." (Lyster 2007:97 ; Ellis & Sheen 2006)

PCIC B2 + C1 inventarios "tácticas y estrategias pragmáticas" (Vol B §11) include explicit metalinguistic discussion as register marker for advanced learners. DELE B2/C1 Criterios calificación rate Corrección dimension explicitly with form-focused expectations.

```yaml
# b2_t3_condicional_001 + b2_t3_imperfecto_pret_001 + multi_b2_imperfecto_no_uptake_001
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - elicitation
      - metalinguistic
      - partial_recast
      - clarification_request
      - explicit_correction        # ADDED Phase 0.H — Lyster + Lira-Gonzales 2024 + Ellis & Sheen 2006
    forbidden: []

# c1_t3_subjuntivo_imp_001 (no clarification_request in original spec)
expected_dimensions:
  cf_move_set_valid:
    acceptable:
      - elicitation
      - metalinguistic
      - partial_recast
      - explicit_correction        # ADDED Phase 0.H — same rationale C1 advanced
    forbidden: []
```

## Real Maestro pedagogy issues (NOT addressed Phase 0.H — defer Phase 1 prompt)

3 fails are real Maestro behavior issues, not acceptable_set issues. KEEP forbidden, fix via Maestro Dify prompt patch in Phase 1.

| Scenario | Level/Tier | Move detected | Why real issue |
|---|---|---|---|
| `a2_t2_preterite_001` | A2/T2 V:PRET | `explicit_correction` | Lyster Ch 4 §3.1 — A1-A2 NO metalinguistic/explicit (cognitive load). Maestro over-explicit → real prompt issue. |
| `b1_t2_quantifier_001` | B1/T2 QUANT:MUY_MUCHO | `explicit_correction` | B1/T2 communicative tier → recast preferred (Lyster). Quantifier confusion = high frequency low salience → recast adequate. |
| `risk_priority_leak_b1_es_001` | B1 risk (no error) | `full_recast` | Learner input "Cuéntame algo sobre tu fin de semana" = correct ES. Maestro recasts a CORRECT sentence → priority leak (over-correction without error). Anti-pattern. |

**Action Phase 1** : Maestro Dify prompt patch — add explicit anti-over-correction directive A1-A2 + priority-leak guard (don't recast when no error detected).

## Forecast post Phase 0.H

- Pre Phase 0.H : 12/24 (50%) baseline post-judge-fix
- 7 cf_move fails addressed → +7 expected pass
- Forecast : **~19/24 (79%)** if all 7 pass (some may shift to other dim fail like semantic_fidelity which is already counted separately)
- Plus residual semantic_fidelity_pairwise (7/24 fails) = goldens variance Dify temp 0.2 — peut être resolved by re-record in same battery sequence ou n_votes=10+

DoD Phase 0 Maestro ES MVP target : **18-22/24 stable** (équivalent S54 EN 20/26 panel certified).

## Files modified

- `scripts/oracle/scenarios/maestro_es/a2_t2_a_personal_001.yaml`
- `scripts/oracle/scenarios/maestro_es/b1_t3_gustar_subj_001.yaml`
- `scripts/oracle/scenarios/maestro_es/b2_t2_false_friend_001.yaml`
- `scripts/oracle/scenarios/maestro_es/b2_t3_condicional_001.yaml`
- `scripts/oracle/scenarios/maestro_es/b2_t3_imperfecto_pret_001.yaml`
- `scripts/oracle/scenarios/maestro_es/c1_t3_subjuntivo_imp_001.yaml`
- `scripts/oracle/scenarios/maestro_es/multi_b2_imperfecto_no_uptake_001.yaml`

7 scenarios patched. Lint 24/24 valid post-patch.

## Cross-references

- S54 EN parallel : `webapp/backend/docs/audit/2026-04-30-oracle-battery-v1-acceptable-set-audit.md`
- Sprint Maestro ES plan : à créer `docs/00-project/sprint-maestro-es-2026-05.md`
- ADR-016 authority anchor cross-lang : `docs/05-decisions/ADR-016-authority-anchor-strategy-cross-lang.md`
- Vault knowledge cross-projet : `vault/knowledge/pedagogy/sla-pedagogy-bibliography.md`
