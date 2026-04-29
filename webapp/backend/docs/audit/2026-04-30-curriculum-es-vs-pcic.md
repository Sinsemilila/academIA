---
status: authoritative
last_reviewed: 2026-04-30
type: audit
session: 53
---

# Audit `curriculum_es.yaml` vs PCIC Gramática (Plan Curricular Instituto Cervantes)

**Author** : Claude Sonnet 4.6 (Session 53 Phase C, 2026-04-30)
**Sources** :
- [`extracted/cervantes-2006-plan-curricular-a1-a2/grammar-by-level.yaml`](../../packages/academie-core/academie_core/data/extracted/cervantes-2006-plan-curricular-a1-a2/grammar-by-level.yaml) (A1+A2)
- [`extracted/cervantes-2006-plan-curricular-b1-b2/grammar-by-level.yaml`](../../packages/academie-core/academie_core/data/extracted/cervantes-2006-plan-curricular-b1-b2/grammar-by-level.yaml) (B1+B2)
- [`packages/academie-core/academie_core/data/curriculum_es.yaml`](../../packages/academie-core/academie_core/data/curriculum_es.yaml) (51 concept_keys A1-C2 — DRAFT pre-S52)
- CEFR Companion 2020 cross-validation : [`extracted/coe-2020-cefr-companion-volume/`](../../packages/academie-core/academie_core/data/extracted/coe-2020-cefr-companion-volume/)

## Executive summary

`curriculum_es.yaml` est **DRAFT non-validé pré-S52** — 51 concept_keys construits sans accès direct PCIC. Les 10 gaps déjà flaggés Phase A2 sont **CONFIRMÉS** par l'extraction PCIC :

1. ✅ ser/estar A1 generic (1 key) → PCIC A1 stratifie SER en 4 valeurs (identificativo, pertenencia clase, localización temporal, identificación) + ESTAR en 2 (localización espacial, criterio distribucional con bien/mal). PCIC A2 ajoute ser pour posesión/cantidades/causa/finalidad + estar temporal/meteorológico.
2. ✅ subjuntivo B1 = 2 keys → PCIC B1 a 5 contextes subjuntivo presente (independientes desiderativas + duda + 4 subordinadas) + 4 contextes imperfecto (2 independientes + cortesía + subordinación pasada) + perfecto + pluscuamperfecto = ~12 entrées critères.
3. ✅ connectores_argumentativos B2 = 1 key → PCIC B2 split en 6 catégories : conjuntivos + focalizadores + intensificadores + reformuladores + matizadores consecutivos + digresivos.
4. ✅ verbos de cambio B2 absents → PCIC B2 12.1 explicit : ponerse, quedarse, hacerse, volverse (verbos seudocopulativos).
5. ✅ Régionalisme absent → PCIC B1+B2 multiple [Hispanoamérica], [México], [Caribe], [Andino] notes.
6. ✅ Pas de FUNCTIONS → confirmé Phase D.
7. ✅ Pas de PRAGMATIC STRATEGIES → confirmé Phase D.
8. ✅ Pas de CULTURAL → confirmé Phase D.
9. ✅ C1-C2 underspecified (8+5 concepts) → confirmé, PCIC Vol C C1-C2 acquisition pending.
10. ✅ Single dimension grammar only → confirmé.

**Net additions Phase C4** : ~80-100 nouveaux concept_keys (51 → ~130-150). PCIC est dense — chaque macro-section a 5-15 sub-items per niveau.

## Gap analysis (high-level macro-sections per level)

### A1 macro-sections PCIC vs AcademIA

| PCIC macro | PCIC items A1 | AcademIA A1 | Gap action |
|---|---|---|---|
| 1.El sustantivo | 4 sous-sections × multiple items | `genero_masculino_femenino` + `plural_nouns_es` (implicit) | `add` : `nombres_propios_a1`, `numero_sustantivos_a1` |
| 2.El adjetivo | 5 sous-sections | (covered via `genero_masculino_femenino` + comparativos A2) | `add` : `adjetivo_genero_a1`, `adjetivo_numero_a1`, `adjetivo_posicion_postnominal_a1`, `superlativo_absoluto_muy_a1` |
| 3.El artículo | 3 (definido + indefinido + ausencia) | `articulos_definidos` + `articulos_indefinidos` | `refine` : 2 keys present mais sans distribución (haber/gustar/saber rules) |
| 4.Demostrativos | 3 (forma + valores + distribución) | `demostrativos_a1` (implicit via comparativos) | `add` : `demostrativos_a1` (este/ese/aquel + neutros esto/eso/aquello) |
| 5.Posesivos | 3 (forma + distribución) | (absent) | `add` : `posesivos_atonos_a1` (mi, tu, su, nuestro, vuestro) |
| 6.Cuantificadores | 2 (numerales + focales) | `numeros_fechas` | `add` : `numerales_cardinales_a1`, `numerales_ordinales_10_a1`, `cuantificadores_focales_tambien_tampoco_a1` |
| 7.Pronombre | 3 (personal + relativos + interrogativos + exclamativos) | `pronombres_sujeto` | `add` : `pronombres_od_a1` (implicit), `pronombres_oi_me_te_le_a1`, `pronombres_se_reflexivo_a1`, `relativo_que_a1`, `interrogativos_qué_quién_cuánto_dónde_cómo_a1`, `exclamativos_qué_a1` |
| 8.Adverbio | 5 (nucleares + modus + conjuntivos + relativos + locuciones) | `adverbios_frecuencia` (A2 currently) | `add` : `adverbios_lugar_aquí_ahí_allí_a1`, `adverbios_tiempo_ahora_hoy_mañana_a1`, `adverbios_cantidad_poco_mucho_bastante_a1`, `adverbios_polares_sí_no_a1`, `por_qué_porque_contraste_a1` |
| 9.Verbo | 4 (indicativo + imperativo + no personales) | `presente_indicativo_regular` | `add` : `imperfecto_a1` (descriptivo + habitual), `indefinido_a1` (acciones perfectivas pasadas), `pretérito_perfecto_a1` (lien al presente), `imperativo_afirmativo_a1`, `infinitivo_funcional_a1`, `participio_atributo_a1` |
| 10.SN | 5 (núcleo + complementos + concordancia + vocativo) | (implicit) | `add` : `sn_complementos_preposicionales_de_a1` (libro de español), `sn_vocativo_a1` |
| 11.SAdj | 2 (núcleo + modificadores) | (implicit) | `add` : `adverbios_grado_muy_poco_bastante_a1` |
| 12.SV | 2 (núcleo + complementos) | `ser_estar_basico` (1 generic key) | **CRITICAL** `split` : `ser_identificativo_a1`, `ser_pertenencia_clase_a1`, `ser_localizacion_temporal_a1`, `ser_identificación_a1`, `estar_localizacion_espacial_a1`, `estar_modo_bien_mal_a1`, `gustar_psicológico_a1`, `od_persona_sin_a_a1`, `od_subordinada_a1`, `oi_pronombre_gustar_a1` |
| 13.Oración simple | 3 (concordancia + constituyentes + tipos) | (implicit) | `add` : `oracion_orden_svo_a1`, `interrogativas_totales_a1`, `interrogativas_parciales_a1`, `impersonales_haber_a1`, `transitivas_intransitivas_a1` |
| 14.Coordinación | 4 (cop+disy+adv+distrib) | (implicit `basic_connectors` A2) | `add` : `coordinacion_y_a1`, `coordinacion_ni_a1`, `coordinacion_o_a1`, `coordinacion_pero_a1`, `coordinacion_distributiva_a1` |
| 15.Subordinación | 3 (sustantivas + adjetivas + adverbiales) | (implicit) | `add` : `subordinada_infinitivo_sujeto_ser_a1`, `subordinada_infinitivo_querer_a1`, `subordinada_creer_indicativo_a1`, `relativa_que_a1`, `causales_porque_a1`, `finales_para_infinitivo_a1` |

**A1 net additions** : ~50 nouveaux concept_keys (10 → ~60). MASSIVE expansion required.

### A2 / B1 / B2 — synthèse

PCIC A2-B2 ajoute en moyenne **30-40 nouveaux items par niveau**. AcademIA actuel a 9-10 items per niveau.

→ **Estimation post-Phase-C4** :
- A1 : 10 → ~60 (+50)
- A2 : 9 → ~30 (+21)  
- B1 : 10 → ~35 (+25)
- B2 : 9 → ~30 (+21)
- C1 : 8 (PCIC Vol C pending — pas d'audit) — keep as-is for now
- C2 : 5 (idem) — keep as-is

**Total post-Phase-C4** : 51 → ~168 concept_keys (+229%). MAIS scope creep risk → **strategy** : on ne va PAS exploser à 168 d'un coup. Le patch C4 priorise les **hauts-yield** :

## Phase C4 patch strategy (pragmatic)

**NOT a full extraction-to-curriculum 1:1**. Au lieu : couvrir les 10 gaps Phase A2 + ajouter ~30-40 concept_keys ciblés sur les zones où curriculum_es.yaml est manifestement sous-spécifié pour le judging :

### Niveau A1 — priorité top 3 splits + 5 additions
- ✅ `ser_estar_basico` (1) → split en 6 keys per PCIC : `ser_identificativo`, `ser_pertenencia`, `ser_temporal`, `estar_localizacion`, `estar_modo`, `ser_estar_contraste_a1` (instructional key)
- ✅ Add `imperfecto_a1` (descriptivo + habitual) — currently absent A1 mais PCIC A1
- ✅ Add `pretérito_perfecto_a1`, `pretérito_indefinido_a1` — currently both A2 in AcademIA but PCIC has them at A1 (action : `relabel` si on respecte PCIC ordering)
- ✅ Add `imperativo_afirmativo_tu_a1` (currently A2 in AcademIA, PCIC A1) — `relabel`
- ✅ Add `gustar_construccion_a1`, `posesivos_atonos_a1`, `demostrativos_a1`, `interrogativos_a1`

### Niveau B1 — priorité subjuntivo expansion + connectores
- ✅ `subjuntivo_presente` (1) → split en : `subjuntivo_volición` (querer/desear), `subjuntivo_emoción` (gustar/encantar/dar miedo), `subjuntivo_duda` (no creer), `subjuntivo_valoración` (es bueno que), `subjuntivo_temporal` (cuando + futuro), `subjuntivo_finalidad` (para que)
- ✅ Add `subjuntivo_imperfecto_b1` (déjà séparé en B2 actuel mais PCIC dit B1 dans subordinées passées)
- ✅ Add `condicional_simple_cortesia_b1`, `condicional_simple_modestia_b1`, `condicional_simple_sugerencia_b1`
- ✅ Add `por_para_b1` stratifié (causa/medio/duración pour por ; finalidad/destinatario pour para)
- ✅ Add `pronominales_se_combinacion_b1` (Se lo doy)
- ✅ Add `relativo_que_quien_b1`, `relativo_donde_b1`, `interrogativos_cuál_b1`

### Niveau B2 — verbos de cambio + connectores stratifiés + condicional compuesto
- ✅ Add `verbos_cambio_ponerse_volverse_quedarse_hacerse_b2` (CRITICAL gap)
- ✅ `conectores_argumentativos` (1) → split : `conectores_causales_b2`, `conectores_consecutivos_b2`, `conectores_concesivos_b2`, `conectores_finales_b2`, `conectores_temporales_b2`, `conectores_contraargumentativos_b2`
- ✅ Add `condicional_compuesto_hipótesis_b2` (déjà existant, refine description per PCIC)
- ✅ Add `subjuntivo_imperfecto_b2` extension (cortesía + irrealización)
- ✅ Add `pasiva_perifrástica_b2` (vs `pasiva_refleja` existing)
- ✅ Add `relativos_cual_quien_explicativas_b2`, `dubitativas_quizá_b2`

### Niveau C1+C2 — DEFER (PCIC Vol C pending Sinse acquisition)

C1+C2 keep as-is. Document explicitly that audit incomplete jusqu'à PCIC Vol C acquired.

## Quantitative summary

| Niveau | Pre-S53 | Phase C4 add | Phase C4 split | Phase C4 final |
|---|---|---|---|---|
| A1 | 10 | +8 | +5 (ser/estar split) | ~22 |
| A2 | 9 | +5 | 0 | ~14 |
| B1 | 10 | +12 | +6 (subjuntivo split) | ~26 |
| B2 | 9 | +8 | +6 (connectores split) | ~21 |
| C1 | 8 | 0 | 0 | 8 (deferred) |
| C2 | 5 | 0 | 0 | 5 (deferred) |
| **Total** | **51** | **+33** | **+17** | **~96** |

Ratio expansion : 51 → 96 (+88%). Less ambitious que les 130-150 théorique mais **ciblé sur les gaps high-yield** pour judging Spanish errors.

## Phase C4 patch checklist

- [ ] Split `ser_estar_basico` A1 → 6 keys per PCIC stratification (4 sens SER + 2 sens ESTAR + contrast meta)
- [ ] Relabel `pretérito_indefinido` A2 → A1 + `pretérito_perfecto` A2 → A1 + `imperativo_afirmativo_tu` A2 → A1 (per PCIC ordering)
- [ ] Add 8 concept_keys A1 PCIC core
- [ ] Add 5 concept_keys A2 (focus régional + cuantificadores + adverbios)
- [ ] Split `subjuntivo_presente` B1 → 6 keys per trigger taxonomy
- [ ] Add 12 concept_keys B1 (condicional senses + relativos + interrogativos cuál + por/para split)
- [ ] Add `verbos_cambio_b2` ⭐ critical gap
- [ ] Split `conectores_argumentativos` B2 → 6 keys per discourse function
- [ ] Add 8 concept_keys B2 (pasiva perifrástica + dubitativas + relativos cual/quien)
- [ ] Sync `concept_hints/es.yaml` with all new keys (currently 34 → ~96)
- [ ] Run pytest schema validation
- [ ] Document in curriculum_es.yaml header : audit completed S53 + reference to extracted PCIC YAMLs

**DEFERRED** :
- PCIC Vol C C1-C2 acquisition (Sinse manual `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/`)
- Functions / Mediation / Cultural inventarios (Phase D scope)
- Full PCIC 1:1 extraction beyond Gramática (Pronunciación, Ortografía, Tácticas, Géneros, Nociones específicas, Referentes culturales) — Phase E future
