---
title: curriculum_es.yaml audit C1+C2 vs PCIC Vol C — gap analysis for Tier 3.G6.D expansion
date: 2026-05-01
status: authoritative
last_reviewed: 2026-05-01
session_origin: 56
tags: [audit, multilang, methodology, plan]
ai_summary: "Audit curriculum_es 8 C1 + 5 C2 concepts vs PCIC Vol C inventario gramática. ~50 gaps identified. Tier 3.G6.D target: expand to ~30 C1 + ~22 C2."
---

# curriculum_es.yaml C1+C2 audit vs PCIC Vol C (S56 Tier 2 G6.C)

## TL;DR

- Current `curriculum_es.yaml` C1 = 8 concepts, C2 = 5. Total ES = 98.
- PCIC Vol C (extracted S56 G6.A) has **15 macro-sections × 2 niveaux** with ~80-100 distinct grammatical points across C1+C2.
- **Coverage gap : ~85% of PCIC C1-C2 inventory absent from curriculum_es**.
- Tier 3.G6.D target : expand C1 8→~30 + C2 5→~22 (+39 concepts) → total ES 137.
- Cumul with B2 polish + A2 splits : final target ~150 concepts (per execution roadmap).

## Current C1+C2 in curriculum_es

```yaml
C1 (8):
  - colocaciones_avanzadas
  - registros_formal_informal
  - modismos
  - inversion_enfatica
  - subjuntivo_estilo
  - marcadores_discursivos_c1
  - lexico_preciso
  - construcciones_focales

C2 (5):
  - estructuras_hendidas
  - discurso_referido_complejo
  - ironia_pragmatica
  - matiz_perfectivo_imperfectivo
  - literatura_referencial
```

**Observation** : 8/8 C1 concepts are **lexico-pragmatic / discourse-level** (registres, marqueurs, idioms, focal constructions). Aucune couverture des points grammaticaux PCIC C1 fondamentaux (cuyo relativo, condicional irréalité passé, perífrasis aspectuelles complexes, etc.). C2 = 5 entries mostly stylistic-rhetorical — same gap.

## PCIC Vol C C1+C2 macro-sections coverage check

Per PCIC `extracted/cervantes-2006-plan-curricular-c1-c2/grammar-by-level.yaml` (S56 G6.A) :

| PCIC C1 macro-section | curriculum_es coverage | Gap status |
|---|---|---|
| 1. El sustantivo (apellidos plurales, género contraste) | ❌ 0/4 PCIC entries | **NEW C1 needed** |
| 2. El adjetivo (cuyo, anteposición valor cuantif, superlativo irreg) | partiel via `subjuntivo_estilo`?? non | **NEW C1 needed** : `posesivo_relativo_cuyo`, `adjetivo_anteposicion_valor`, `superlativo_absoluto_irregular` |
| 3. El artículo (lo neutro sustantivador, valor enfático) | partiel via `inversion_enfatica` | **NEW C1 needed** : `articulo_neutro_lo_sustantivador`, `articulo_indefinido_enfatico` |
| 4. Los demostrativos (anafórico discursivo, despectivo) | absent | **NEW C1 needed** : `demostrativos_anaforicos_c1` |
| 5. Los posesivos (cuantificacional, neutro lo + posesivo) | absent | **NEW C1 needed** : `posesivos_cuantificacional_c1` |
| 6. Los cuantificadores (cuanto relativo, gradativos comparativos) | absent | **NEW C1 needed** : `cuanto_relativo_c1`, `comparativos_gradativos_c1` |
| 7. El pronombre (relativos avanzados el cual, leísmo de cosa) | partiel `construcciones_focales` | **NEW C1 needed** : `pronombre_relativo_el_cual`, `leismo_loismo_normativo` |
| 8. El adverbio (-mente restricciones, evaluativos, conjuntivos) | partiel `marcadores_discursivos_c1` | **EXTEND** : split en `adverbios_evaluativos_c1`, `adverbios_conjuntivos_c1` |
| 9. El verbo — Indicativo (imperfecto censura/sorpresa, condicional rechazo) | absent | **NEW C1 needed** : `imperfecto_valores_pragmaticos_c1`, `condicional_simple_rechazo_c1`, `futuro_perfecto_objecion_c1` |
| 9. Subjuntivo (subordinación compuesta, finales con locuciones) | partiel `subjuntivo_estilo` | **EXTEND** : split en `subjuntivo_subordinacion_compuesta_c1`, `subjuntivo_finales_locuciones_c1` |
| 9. Imperativo (irónico, condicional, ponderativos lexicalizados) | absent | **NEW C1 needed** : `imperativo_pragmatico_c1` |
| 9. Formas no personales (infinitivo modalizado, participio absoluto) | partiel `construcciones_focales` | **EXTEND** : `infinitivo_modalizado_c1`, `participio_absoluto_c1` |
| 10. SN (núcleo elíptico, nominalizaciones) | absent | **NEW C1 needed** : `sn_nucleo_eliptico_c1`, `nominalizaciones_c1` |
| 11. SAdj (interrogativas indirectas, atípicas) | absent | **NEW C1 needed** : `sadj_complementos_c1` |
| 12. SV (perífrasis aspectuales avanzadas, copulativas atípicas) | absent | **NEW C1 needed** : `perifrasis_aspectuales_c1`, `copulativas_atipicas_c1` |
| 13. Oración simple (concordancia ad sensum, dislocación) | partiel | **NEW C1 needed** : `concordancia_ad_sensum_c1`, `dislocacion_topicalizacion_c1` |
| 14. Coordinación (asíndeton, polisíndeton, mas adversativo) | absent | **NEW C1 needed** : `coordinacion_avanzada_c1` |
| 15. Subordinación (relativas yuxtapuestas, condicionales remotas) | partiel | **NEW C1 needed** : `subordinacion_relativas_avanzadas_c1`, `condicionales_remotas_c1` |

| PCIC C2 macro-section | curriculum_es coverage | Gap status |
|---|---|---|
| 1. Sustantivo (cultismos plurales, antropónimos articulados) | absent | **NEW C2 needed** : `cultismos_pluralizacion_c2` |
| 2. Adjetivo (color compuestos, anteposición literaria/irónica, -érrimo) | absent | **NEW C2 needed** : `adjetivo_anteposicion_literaria_c2`, `superlativo_culto_c2` |
| 3. Artículo (sustantivador atributivo, distribucional con propios) | absent | **NEW C2 needed** : `articulo_sustantivador_atributivo_c2` |
| 4. Demostrativos (sorpresa, posnominal vaya) | absent | **NEW C2 needed** : `demostrativos_pragmaticos_c2` |
| 5. Posesivos (intensificadores, expresiones fijas) | absent | **NEW C2 needed** : `posesivos_pragmaticos_c2` |
| 6. Cuantificadores (focales hasta/apenas, ordinales decenas) | absent | **NEW C2 needed** : `cuantificadores_focales_c2` |
| 7. Pronombre (dativo ético, expresiones fijas con átonos) | absent | **NEW C2 needed** : `dativo_etico_c2`, `expresiones_fijas_atonos_c2` |
| 8. Adverbio (modalidad coloquial, focalizadores particularizadores) | absent | **NEW C2 needed** : `adverbios_modus_c2` |
| 9. Indicativo (presente volitivo, futuro emfático, condicional periodístico) | absent | **NEW C2 needed** : `tiempos_pragmaticos_c2` |
| 9. Subjuntivo (futuro literario "a quien correspondiere") | absent | **NEW C2 needed** : `subjuntivo_futuro_literario_c2` |
| 9. Imperativo (concesivo, lexicalizados pragmáticos) | partiel `ironia_pragmatica` | **EXTEND** : `imperativo_concesivo_c2` |
| 12. SV (haber de obligativo, ser sin adjetivo filosófico) | absent | **NEW C2 needed** : `haber_de_obligativo_c2` |
| 13. Oración simple (interrogativas retóricas, figurativas) | partiel `ironia_pragmatica` | already covered |
| 15. Subordinación (relativas no específicas con -quiera, enfáticas disjointed) | partiel `estructuras_hendidas` | **EXTEND** : `relativas_quiera_c2` |

## Recommendations Tier 3.G6.D — `curriculum_es.yaml` 98→~150

### Priority 1 — Add 22 NEW C1 concepts (8→30)

```yaml
# Grammatical core (NOT lexico-pragmatic) — closes structural gap
- posesivo_relativo_cuyo                      # PCIC C1 §2.1.3, §15.2
- adjetivo_anteposicion_valor                 # PCIC C1 §2.4
- superlativo_absoluto_irregular              # PCIC C1 §2.5
- articulo_neutro_lo_sustantivador            # PCIC C1 §3.1
- articulo_indefinido_enfatico                # PCIC C1 §3.2
- demostrativos_anaforicos_c1                 # PCIC C1 §4
- posesivos_cuantificacional_c1               # PCIC C1 §5
- cuanto_relativo_c1                          # PCIC C1 §6.1, §7.2
- pronombre_relativo_el_cual                  # PCIC C1 §7.2
- leismo_loismo_normativo                     # PCIC C1 §7.1.2-3
- adverbios_evaluativos_c1                    # PCIC C1 §8.3
- adverbios_conjuntivos_c1                    # PCIC C1 §8.5
- imperfecto_valores_pragmaticos_c1           # PCIC C1 §9.1.2 (censura/sorpresa)
- condicional_simple_rechazo_c1               # PCIC C1 §9.1.5
- futuro_perfecto_objecion_c1                 # PCIC C1 §9.1.9
- subjuntivo_subordinacion_compuesta_c1       # PCIC C1 §9.2.1
- imperativo_pragmatico_c1                    # PCIC C1 §9.3
- infinitivo_modalizado_c1                    # PCIC C1 §9.4.1
- participio_absoluto_c1                      # PCIC C1 §9.4.3
- nominalizaciones_c1                         # PCIC C1 §10.1
- perifrasis_aspectuales_c1                   # PCIC C1 §12.1
- subordinacion_finales_locuciones_c1         # PCIC C1 §15.3.5
```

### Priority 2 — Add 17 NEW C2 concepts (5→22)

```yaml
- cultismos_pluralizacion_c2                  # PCIC C2 §1.3
- adjetivo_anteposicion_literaria_c2          # PCIC C2 §2.4
- superlativo_culto_c2                        # PCIC C2 §2.5 (-érrimo, requete-)
- articulo_sustantivador_atributivo_c2        # PCIC C2 §3.1
- demostrativos_pragmaticos_c2                # PCIC C2 §4 (vaya + relativa)
- posesivos_pragmaticos_c2                    # PCIC C2 §5
- cuantificadores_focales_c2                  # PCIC C2 §6.2 (hasta, apenas)
- numerales_distributivos_c2                  # PCIC C2 §6.1 (sendos)
- dativo_etico_c2                             # PCIC C2 §7.1.3
- expresiones_fijas_atonos_c2                 # PCIC C2 §7.1.2 (¡No te fastidia!)
- adverbios_modus_pragmaticos_c2              # PCIC C2 §8.4 (acaso, por ahí)
- focalizadores_particularizadores_c2         # PCIC C2 §8.6 (máxime, meramente)
- tiempos_indicativo_pragmaticos_c2           # PCIC C2 §9.1 (volitivo, periodístico)
- subjuntivo_futuro_literario_c2              # PCIC C2 §9.2.5
- imperativo_concesivo_c2                     # PCIC C2 §9.3 (Grita lo que quieras)
- haber_de_obligativo_c2                      # PCIC C2 §12.1
- relativas_quiera_c2                         # PCIC C2 §15.2 (dondequiera, etc.)
```

### Priority 3 — Tier 3.G6.D bundle items

- ~13 B1-B2 polish (gaps already flagged in curriculum_es.yaml header — ser/estar A1 stratification, subjuntivo B1 12-15 triggers split, connectores B2 split, verbos cambio B1-B2)

**Total** : 22 (C1) + 17 (C2) + 13 (polish) = **52 NEW concepts** → curriculum_es 98→150 ✅ matching execution roadmap target.

## Concept_hints/es.yaml impact (Stream E G6.E)

`concept_hints/es.yaml` 103 entries currently. After G6.D: should be 150 (1:1 with curriculum_es). Each new concept_key needs 1 entry in concept_hints with FR-oriented translation hint + 1-2 example sentences.

## Functions/es.yaml impact (Stream E G7.1)

`functions/es.yaml` 42 entries currently (A1+A2 only). PCIC Funciones extracted S56 G6.B covers C1+C2 macro-sections 1-4 (sections 5+6 pending). Tier 3.G7.1 will merge:
- B1+B2 funciones (need separate WebFetch — already roadmapped)
- C1+C2 funciones (extracted S56)
- Sections 5+6 C1+C2 (pending fallback acquisition)

Target G7.1 : 42→~80 entries.

## Acquisition gates flagged

- ✅ PCIC Vol C Gramática C1+C2 — extracted via WebFetch (`grammar-by-level.yaml`, 15 macro-sections × 2 niveaux)
- ⚠️ PCIC Vol C Funciones C1+C2 — partial (sections 1-4 extracted, 5+6 truncated by WebFetch)
- ❌ PCIC Vol B (B1+B2) Funciones — NOT YET extracted (S53 only did A1+A2). Need WebFetch on `05_funciones_inventario_b1-b2.htm` before Tier 3.G7.1.

## Cross-references

- PCIC C1+C2 Gramática extraction : `packages/academie-core/academie_core/data/extracted/cervantes-2006-plan-curricular-c1-c2/grammar-by-level.yaml` (S56 G6.A)
- PCIC C1+C2 Funciones extraction : `packages/academie-core/academie_core/data/extracted/cervantes-2006-plan-curricular-c1-c2/funciones-by-level.yaml` (S56 G6.B)
- Existing curriculum : `packages/academie-core/academie_core/data/curriculum_es.yaml`
- S53 audit ES vs PCIC A1+B1 : `webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md`
- Execution roadmap : `docs/audit/2026-05-01-maestro-es-execution-roadmap.md`
- Tier 3.G6.D target : `curriculum_es.yaml` 98→150 concepts
