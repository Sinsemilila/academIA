# Sessions — AcademIA

Sessions empilées (plus récente en haut). Rotation : seules les **3 dernières** restent ici, les plus anciennes vont dans [`SESSION_ARCHIVE.md`](SESSION_ARCHIVE.md).

---
---

## Session 53 — 2026-04-30 (~12h continu — Library ingest 8 stubs + skim batch 74/85 + EN/ES authority anchor audit Phase A+B+C+D1 LIVRÉE 17 commits academia + vault)

### Done

**Library ingest S53 — 13 stubs acquired** (commits vault `7afc301`) :
- 8 stubs `stub-pending-acquisition` → `acquired-pending` (TORFL ×4 lexical minimums + Goethe B1+B2 + telc B2 + DELE A1 oficial)
- 5 nouvelles literature notes (CILS C1+C2 Quaderni + El Cronómetro B2 DELE + Makova-Uskova Vol.3 + Preparación DELE B2 Soluciones)
- 14 PDFs déplacés inbox→processed/, 4 duplicates supprimés (CILS B1 = vedovelli dup + Cyrillic filename dups)
- USAGE-MAP : 90 total entries trackés

**Skim batch S53 COMPLET — 74/85 books skimmed (87% library)** (15 commits vault Vagues 1-15) :
- 11 stubs restants `stub-pending-acquisition` (Sinse acquisition pending — telc B1, JLPT N5 vol1, DELE A2/B1/C1/C2, PCIC C1-C2, CILS Sillabo, TORFL Grammar Min)
- Distribution post-skim : ~9 HIGH ⭐⭐ extraction queue + ~25 HIGH ⭐ scheduled per Wave + ~5 MEDIUM + ~25 LOW lookup-only-deferred + 2 in-use/extracting
- Tracking note `skim-batch-pending.md` finale (74/85 cumulative skims)

**Phase A — P0 quick wins** (5 commits academia : `c94d896`, `af891e1`, `895d32f`, `3e53dba`, `876f1f1`) :
- TODO.md per-language book incorporation roadmap (~106L ajoutées) — Phase B/C/D + Wave 2-4 + Cross-language activations
- `concept_hints/en.yaml` expansion 20→**105 entries** (100% curriculum_en coverage A1-C2, FR-oriented avec faux amis flagged)
- `curriculum_es.yaml` flag 10 PCIC gaps inline + honest header annotation
- `curriculum_en+es` honest source attribution + l1_transfer integration path docs
- Phase A3 `phrasal_verbs` stratification deferred Phase B5 (cross-system migration scope : tolerance_matrix v1+v2 + profile_router.py + Dify workflow + scripts)

**Phase B — EN flagship audit** (4 commits : `8fbf718`, `c4307b2`, `a9d884f`, `9925400`) :
- Hawkins/Filipović 2012 Ch 9.1 horizontal summary extracted → `extracted/hawkins-filipovic-2012-criterial-features-l2-english/criterial-features-by-level.yaml` (5 niveaux A2-C2 + criterial features per niveau + modal auxiliaries + lexical progression + error type improvements)
- CEFR Companion 2020 App 1 (salient features) + App 7 (changes 2001→2020) extracted → 2 YAMLs (App 1 + App 2 self-assessment grid bonus)
- Audit doc `webapp/backend/docs/audit/2026-04-30-curriculum-en-vs-authority.md` (105 concepts vs Hawkins criterial — 26 additions + 14 refines + C2 wording fix identified)
- Patch `curriculum_en.yaml` 105→**131 concepts** (+26 criterial features : raising, extraposition, cleft, pseudocleft, genitive embeddings) + sync `concept_hints/en.yaml` 105→131 entries + C2 description "near-native" → "highly successful learner" (per Companion 2020 App 1)

**Phase C — ES flagship audit** (4 commits : `4fd7fda`, `9c96c5b`, `41222ef`, `34ea884`) :
- PCIC Vol A Gramática inventario A1+A2 extracted via WebFetch `cvc.cervantes.es` (preferred over scanned PDF 515p) → `extracted/cervantes-2006-plan-curricular-a1-a2/grammar-by-level.yaml` (15 macro-sections × 2 niveaux × ~20-30 items)
- PCIC Vol B Gramática inventario B1+B2 extracted → `extracted/cervantes-2006-plan-curricular-b1-b2/grammar-by-level.yaml` (15 macro-sections × 2 niveaux)
- Audit doc `2026-04-30-curriculum-es-vs-pcic.md` (51 concepts vs PCIC Gramática authoritative — 47 additions/splits identified)
- Patch `curriculum_es.yaml` 51→**98 concepts** + sync `concept_hints/es.yaml` 34→103 entries :
  - Split `ser_estar_basico` A1 → 6 keys (4 SER + 2 ESTAR senses + meta contrast)
  - Relabel `pretérito_indefinido` + `pretérito_perfecto` + `imperativo_afirmativo_tu` A2 → A1 per PCIC ordering
  - Split `subjuntivo_presente` + `subjuntivo_temporal` B1 → 6 keys per PCIC trigger taxonomy (volición, emoción, duda, valoración, temporal_futuro, finalidad)
  - Split `por_para` B1 → 2 keys (causa/medio/durée vs finalidad/destino/plazo)
  - Split `conectores_argumentativos` B2 → 6 keys per discourse function (causales, consecutivos, concesivos, finales, temporales, contraargumentativos)
  - Add `verbos_cambio_b2` ⭐ critical gap comblé (ponerse, volverse, quedarse, hacerse, convertirse en)
  - Add `pasiva_perifrástica_b2` vs `pasiva_refleja_b1` distinction
  - C1+C2 deferred (PCIC Vol C acquisition pending Sinse manual cvc.cervantes.es)

**Phase D1 — Functions dimension scaffold** (4 commits : `6bb02fa`, `996407f`, `4a984c5`, `316423c`) :
- Pydantic `FunctionsPack` + `FunctionEntry` schema dans `data/schemas.py`
- `load_functions(lang)` + `build_functions_block(lang, level)` Dify consumer dans `data/loader.py`
- `data/functions/es.yaml` populé via PCIC Funciones inventario A1+A2 (26 A1 + 16 A2 = 42 entries, sourced cvc.cervantes.es WebFetch)
- `data/functions/en.yaml` scaffold A1+A2 (5+5 = 10 entries, sources Hawkins illustrative_language_functions Table 9.1 + CEFR Companion Ch 3 production/interaction)
- `tests/test_yaml_schema.py` add `test_functions_schema` parametrized 6 langs (EN+ES active, IT/DE/JA/RU skip Phase D2)
- Phase D2/D3/D4 deferred : Mediation NEW 2020 (33p extract) + Skills-based reorganization (design-heavy) + PCIC Vol C acquisition

**Oracle full mode EN post-audit validation** :
- Lint 26/26 ✅ all scenarios validate schema/structural
- Smoke 6/6 ✅ (judges 429-noisy, 5 dims pass mostly)
- Full 24 scenarios × 5 votes battery : **17 passed / 9 failed / 0 skipped / 26 total**
- Baseline Session 51 : 18-19/26 ±1 stable → 17/26 = bas de plage acceptable (variance Groq 11% success rate, 1113 calls 429'd / 138 OK)
- Stable fail `b2_t3_passive_001` (explicit_correction) confirmé S51→S53
- New fail `a2_t2_past_simple_001` (cf_move=implicit_recast rejected) à investiguer (smoke earlier l'avait pass — possible artefact judge variance OR vraie régression subtile)
- Possible amélioration `b1_edge_t2t3_prepositions_001` (S51 stable fail → S53 pass)

### Decisions

- **Phase A3 phrasal_verbs deferred Phase B5** : cross-system migration scope identifiée pre-execution (touche `tolerance_matrix.yaml` v1+v2 + `webapp/backend/app/routers/profile_router.py:559` prod code + Dify workflow `concept_hint_map` hardcoded + `scripts/update_teacher_chatflow.py` + `scripts/sprint6/19_curriculum_en_apply_merge.py` + `scripts/e2e_promo_test.py:42`) → migration multi-system, NOT a quick-win. Bundle dans Phase B5 dedicated session.
- **PCIC extraction strategy pivot** : scanned PDFs Vol A 515p + Vol B 467p impractical OCR (estimate ~80-100p readings × 30-60s each = 1-2h per vol). Pivot **WebFetch direct cvc.cervantes.es HTML free version** = solution efficiente, complète extraction A1-B2 en ~3 fetches.
- **Oracle 17/26 vs baseline 18-19** acceptable : variance Groq 11% success rate explique différence ±1, fails consistents Session 51 préservés (b2_passive). Pas de régression structurelle évidente post-audit.
- **C1+C2 audit deferred** : PCIC Vol C acquisition pending Sinse manual (gratuit cvc.cervantes.es). ES flagship A1-C2 partial → A1-B2 validated, C1-C2 attendre.
- **Phase D2/D3/D4 deferred** : Mediation 33p extract + Skills refactor design-heavy + PCIC Vol C acquisition. Phase D1 livre uniquement Functions A1-A2 scaffold.

### Gotchas

- **PCIC scanned PDF macOS Quartz** : pdftotext échoue (no fonts embedded — image-only scan). Read tool OCR fonctionne mais coût ~30-60s/page × 515p impractical. Pivot WebFetch HTML version gratuit cvc.cervantes.es = ratio 100x meilleur.
- **Groq RPD saturation chronique** : Session 51 reportait 481/540 RPD, Session 53 = 11% success rate (1113 429 / 138 OK) sur full mode. judge_fail_threshold=0.7 protective design (unknowns pass-through) évite false certifications mais limite confidence baseline measurement. Tier upgrade Groq ou alt-provider à considérer pour vraie baseline.
- **a2_t2_past_simple_001 NEW fail post-audit** : smoke 6/6 puis full 9 fails inclut cette scenario. cf_move=implicit_recast rejected by acceptable_set [clarification_request, elicitation, full_recast, partial_recast]. À investiguer judge_variance vs vraie régression (curriculum_en additions préservent semantics existing concept_keys, no removals).
- **b1_edge_t2t3_prepositions_001 amélioration potentielle** : Session 51 stable fail (full_recast) → Session 53 pass. Possible amélioration ou variance judge.
- **Test parity range update needed** : `test_curriculum_en_total_concepts_reasonable` 80-130 → 100-200 post-audit (curriculum_en passe 105→131). Cohérent histoire S41 53→105 + S53 105→131.
- **schemas.py FunctionsPack schema design** : utilise `_Lax` + `validate_mapping` classmethod (cohérent CurriculumPack pattern existing). Permet `_lang_specific` extensions sans breaking schema.

### Commits

**Academia (17)** :
- `c94d896` `af891e1` `895d32f` `3e53dba` `876f1f1` (Phase A 5 commits)
- `8fbf718` `c4307b2` `a9d884f` `9925400` (Phase B 4 commits)
- `4fd7fda` `9c96c5b` `41222ef` `34ea884` (Phase C 4 commits)
- `6bb02fa` `996407f` `4a984c5` `316423c` (Phase D1 4 commits)
- `8460e8b` (TODO mark Phase B+C+D1 LIVRÉE)

**Vault (~17)** :
- 15 commits skim batch S53 Vagues 1-15
- `7afc301` library-ingest S53 8 stubs acquired + 5 new lit notes
- `5ffb9ac` skim-batch-pending tracking note finale
- Plus handoff vault commit (cette session)

---

## Session 52 — 2026-04-29 (~6h30 continu post-reboot mid-session — Library all-in authority anchor pivot + ADR-015 JP + ADR-016 cross-lang + 85 literature notes tracked +1316% vs pre-S52)

### Done

**Library batch 1 — Tasks #1-5 ingestion** (32 notes vault) :
- 5 SLA Tier 1 canon (Pienemann ×2, Nation, Ellis, Hughes 2003) shipped commit vault `04198b5`
- 7 reference grammars per-lang (Maiden IT + Huddleston-Pullum EN + Helbig-Buscha DE + 3× Makino-Tsutsui JP + Hughes 2020) commit `5e5d4ce`
- 10 Wave-deferred exam stubs (Goethe B1+B2, telc, CILS Sillabo, JLPT N5 第一集, TORFL TEU/TBU/TRKI-1/TRKI-2, DELE) commit `194301d`
- 15 PDF literature notes (8 RU Wave 4 + 5 JP Wave 3 + 2 IT Wave 2 + Makino DJVU update) 3 commits granulaires `7b448f4`/`98ed4e2`/`eb60c69`
- USAGE-MAP + INDEX bulk update batch 1 commit `cf20181`

**Library work-of-fond Phase 1-5** (`b80f8ea` + `f6a1648` vault) :
- Phase 1 inventory `library-inventory.md` (17 fichiers cataloged + dedup décisions Antonova/JLPT)
- Phase 2 dedup (Antonova-2019 archived, JLPT N4 split éditions confirmé)
- Phase 3 folder restructure cosmos `by-lang/{ru,jp,it}/{type}/` + 16 files moved+renamed ASCII canonique
- Phase 4 `library-conventions.md` (naming ASCII <220 bytes UTF-8, Cyrillic LoC translit, ingestion workflow)
- Phase 5 `slug-pdf-windows.ps1` Windows-side auto-slug script

**Syncthing desync resolution** :
- Folder `sinse-library` 6 errors → 0
- Cause root identifiée : ext4 NAME_MAX 255 bytes vs Cyrillic UTF-8 2 bytes/char (4 RU PDFs avec metadata libgen 260-300 bytes UTF-8)
- Renames Windows-side (PowerShell template fourni) propagés cosmos via Syncthing rescan API

**Decisions Phase A-C follow-through** (commit vault `51df830`) :
- USAGE-MAP status updates (Makova-Uskova `lookup-only-deferred` above ADR-013 RU cap, LogicStack JLPT N2 `extracting-priority` born-digital EPUB)
- 3 nouveaux statuses ajoutés vocabulary (`stub-pending-acquisition`, `lookup-only-deferred`, `extracting-priority`)
- OCR pass Antonova Doroga 1 (522KB text) + Zalyalova RKI rotated 90° (230KB text) via `ocrmypdf -l rus --deskew --rotate-pages --force-ocr` + TMPDIR=/mnt/cosmos-data/tmp workaround `/tmp` saturation
- **ADR-015** acté (commit `3bf14c6`) — Wave 3 JP productive evaluation strategy : choix C JFS Standard 2010 + custom rubrics dérivés. Comble JLPT structural mismatch (reception only, pas writing/speaking)
- Stub `jfs-standard-2010-jp.md` créé

**Library batch 2 — Authority anchor strategy all-in** (4 commits ingestion + 1 bulk update vault) :
- Sinse pivot stratégique : "rework intégral AcademIA + tous ouvrages nécessaires (même EN/ES)". Cohérence 5-layer pipeline cross-lang
- ~38 nouveaux PDFs acquired Sinse-side (12 free math/ML direct + 6 Marugoto + Profile Deutsch + 8 Anna's Archive payants + 12 free additionnels post-batch incl 3 Marugoto Katsudoo stuck-renamed)
- 30 literature notes drafted batch 2 :
  - **15 quant** (Hastie ESL, James ISL Python, Gelman BDA3, Murphy PML, Bishop PRML, MacKay ITILA, Hernan Causal, Boyd VMLS+CVX, Deisenroth MML, D2L, Goodfellow DL ⚠️excerpt 85p, Wickham R4DS×2, VanderPlas) commit `2049b61`
  - **3 NLP-IR** (Jurafsky SLP3, Eisenstein NLP, Manning IR) inclus commit `2049b61`
  - **1 algos** (Sedgewick & Wayne 4th) inclus commit `2049b61`
  - **2 psychometrics** (Baker IRT ⭐⭐ placement test entry, Embretson IRT applied) inclus commit `2049b61`
  - **4 frontend canon** (Norman DOET, Krug DMMT, Tufte VDQI, Strizver Type Rules) commit `2b02a31`
  - **4 multilang** (Ortega SLA, DeKeyser practice, Bachman testing, **CEFR Companion 2020** ⭐⭐ umbrella authority anchor cross-lang) commit `76a3310`
  - **13 per-lang authority anchors** (1 EN Hawkins/Filipović *Criterial Features in L2 English* + 2 ES PCIC A1-A2/B1-B2 + 2 JP JFS pamphlet/guidebook + 8 Marugoto JP A1→B1 + 1 Glaboniat path update) commit `1b45e88`
- Folders restructure cosmos : `library/by-domain/{math-stats-ml,nlp-ir,algorithms,psychometrics,ux-design,info-viz,typography}/` + `library/by-lang/multilang/{cefr,sla-research,testing-assessment}/` + `library/by-lang/{en,es,de,jp}/curriculum/`
- USAGE-MAP + INDEX bulk update batch 2 commit `9ac9e35` (44 nouveaux entries → 85 livres tracked total)
- **ADR-016** acté (commit `914fb5f`) — Authority anchor strategy cross-lang all-in 5-layer pipeline EN/ES/IT/DE/JP/RU + CEFR Companion 2020 umbrella. +6-10j EN/ES audit Phase 1 (validate-against-authority pas rework from scratch). No impact Wave 2-4 effort

**Vault cleanup** (commits `dbc57e1` + `773de87`) :
- `archive/obsidian-migration/` ← `projects/obsidian-migration/` (Session 50 fermée, 19 fichiers ref historique)
- `archive/books-shopping-lists-session-51/` ← `knowledge/books-{shopping-list,by-tier}-2026-04-29.md` (superseded by USAGE-MAP)
- Delete `Sans titre.canvas` accidental Obsidian default
- INDEX.md links updated archive/

**Library acquisition roadmap P3+** (commit `e1ee9dc`) :
- `library-p3-roadmap.md` ~36 ouvrages organisés P0/P1/P2/P3 avec timing + cost (~280-540€ cumulé total)
- P0 critical : CILS Sillabo (Wave 2 IT) + TORFL Minimums Pushkin (Wave 4 RU) + PCIC C1-C2 (ES flagship gap)
- P1 strong rec : Goodfellow DL re-acquire complete + Marugoto B2 (Tobira/Quartet) + EVP/EGP exports
- P2 nice-to-have : 17 ouvrages stats/causal/voice/Phase B (~150-300€)
- P3 domain expand : 10 ouvrages (~50-100€)

### Decisions

- **ADR-015** (commit `3bf14c6`) — Wave 3 JP productive evaluation strategy = JFS Standard 2010 + custom rubrics dérivés (Choice C combling JLPT structural mismatch reception-only)
- **ADR-016** (commit `914fb5f`) — Authority anchor strategy cross-lang all-in. Pipeline 5-layer uniforme EN/ES + IT/DE/JP/RU. Sinse pivot stratégique uniformité méthodologique
- **L142** — Library structure post-batch-2 : `by-domain/` (math/ML/NLP/UX/typography) + `by-lang/<lang>/<type>/` + `processed/` + `_dedup-archived/`. Conventions canonique `library-conventions.md`
- **L143** — TMPDIR=/mnt/cosmos-data/tmp pour OCR runs (workaround `/tmp` tmpfs saturation, ext4 sdb 768G libres)
- **L144** — Status vocabulary USAGE-MAP étendu (`stub-pending-acquisition`, `lookup-only-deferred`, `extracting-priority`) — extension L139 frontmatter status

### Gotchas

- **ext4 NAME_MAX 255 bytes** hardcoded kernel — Cyrillic UTF-8 2 bytes/char + CJK 3 bytes/char + libgen metadata = bloque file creation cosmos. Naming convention ASCII pur obligatoire (visible via `pdfinfo` + UTF-8 byte count check)
- **Libgen filename year ≠ édition réelle** : Antonova-2019 libgen tag = 2009 5e éd réelle (ISBN 9785865474692 confirmé). Pattern : trust PDF `CreationDate` ou page de garde, pas libgen filename year
- **JLPT structural mismatch** : N5-N1 testent reading+listening UNIQUEMENT (pas writing/speaking). AcademIA Wave 3 JP nécessite authority anchor productive séparée → JFS Standard adopté ADR-015
- **OCR-blocked RU PDFs** : 2 patterns Wave 4 RU sources (Antonova Doroga 1 image-only Adobe Acrobat 9.0 2009 scan + Zalyalova RKI rotated 90° + ghostscript). Fix `ocrmypdf -l rus --deskew --rotate-pages --force-ocr` mais nécessite TMPDIR override (sdb au lieu de /tmp tmpfs) sinon `No space left on device`
- **Goodfellow DL PDF excerpt 85p** vs vrai book 800p. Pattern : verify pagecount post-DL pour PDFs ≥10MB attendus
- **Authority anchor pre-2020 staleness** : Profile Deutsch 2005, PCIC 2006, JF Standard 2010, Hawkins 2012 vs CEFR Companion 2020 update. Cross-validation L1 cross-lang requis
- **Marugoto série culmine B1** — JP B2 cap (ADR-013 essential A1-B2) demande source distincte (Tobira ou Quartet candidates)
- **PCIC C1-C2 manquant** — ADR-013 ES flagship A1-C2 demande 3ème volume PCIC. Acquisition pending P3
- **Marugoto E2 Rikai vs Katsudoo ambiguity** — `marugoto-2016-elementary-2-a2-katsudoo.pdf` peut être Rikai (validate manuel cover/TOC)

### Commits

**Academia (2)** :
- `3bf14c6` [docs] ADR-015 — Wave 3 JP productive evaluation strategy (JFS Standard + custom rubrics, JLPT receptive-only gap)
- `914fb5f` [docs] ADR-016 — Authority anchor strategy cross-lang all-in 5-layer pipeline EN/ES/IT/DE/JP/RU + CEFR Companion 2020 umbrella

**Vault (22)** :
- `04198b5` `5e5d4ce` `b80f8ea` `f6a1648` `194301d` `7b448f4` `98ed4e2` `eb60c69` `cf20181` `51df830` `2049b61` `2b02a31` `76a3310` `1b45e88` `9ac9e35` `dbc57e1` `773de87` `e1ee9dc`

---

## Session 51 — 2026-04-28/29 (~14h continu — P0.1 harness alignment + P0.2 Tier 1 + ES Wave 2 + audit complet + ADR-013 scope tier + 4 multilang research + 7 frontend research + 4 bibliography ~385 books + vault refactor inbox→direct)

### Done

**P0.1 — Harness/prod scope alignment** (commit `7a7fae1`) :
- Découverte structurelle majeure : harness `oracle/judges/dify_client.py:call_agent` ne passait que 2 inputs (learner_profile_summary + learner_profile_json) à Dify alors que `webapp/backend/app/routers/chat_router.py:908` populate 11 sections dynamiques via `lang.build_dynamic_sections(ctx)` (rubric_for_level, fewshots_block, dosage_block, level_reminder_inject, drift_validation_request, l1_watch, spaced_retrieval_today, output_schema_block, scaffolding_block, priority_concepts_block, micro_lesson_block).
- Implémenté `build_full_dify_inputs(scenario, agent)` qui mirror chat_router prod scope.
- Tous scores oracle V1 depuis Session 40 = mesures sur Teacher EN lobotomized (2 inputs vs 11 prod).
- Smoke test post-alignment a2_t2_past_simple_001 : avant "you should say 'I went' instead of 'I goed'..." (explicit_correction). Après : "Oh, you *went* to the cinema! What movie did you see? And you *took* many photos — what did you take pictures of?" (textbook implicit_recast).

**P0.2 — Tier 1 scoring stabilization** (commits `2b76917` + `535c09b` + `d672cbd`) :
- Judge retry/back-off exponential 1s/2s/4s sur HTTP 429 + ReadTimeout dans `oracle/judges/llm_pairwise.py:_call_judge` (élimine bruit free-tier rate-limit Groq gemini-3-1-flash-lite).
- Dify "Session interactive" LLM node `completion_params.temperature` 0.7 → 0.2 (SQL UPDATE workflows table direct, backup `/tmp/teacher-en-enum-session51/graph_original.json`). Smoke test : 2 calls bit-identiques sur même learner input.
- 26 goldens teacher_en re-recorded post-alignment (sha `7a7fae1`) via record_golden refactored to use `build_full_dify_inputs`. Goldens reflètent maintenant aligned harness output (réaction-au-contenu + corrections italicisées).
- n_votes 3→5 + asymmetric `judge_fail_threshold: 0.7` dans `oracle/config.yaml` + `_majority_*` helpers retournent (winner, ratio). Certify "fail" only if winner agreement_ratio ≥ 0.7. Sinon verdict="unknown" (pass-through au scenario aggregation, harness.py:193).
- Baseline aligned mesuré : **18-19/26 ±1** stable (vs 20/26 lobotomized). 2 stable cf_move fails identifiés (b1_edge_t2t3_prepositions_001 full_recast, b2_t3_passive_001 explicit_correction). 10/26 splits run-to-run = variance judge gemini-flash-lite Groq pas strictement déterministe à temp=0.0.

**Maestro ES Wave 2 P0+P2** (commits `d1ed462` + `1974a9d` + `9c912ba`) :
- Audit Wave 2 ES : `LanguageDomain('es').detect_errors()` retournait 0 detections sur Spanish errors évidents (preterite, ser/estar, gender). 6/11 scenarios audités avec coverage gap.
- 4 nouveaux détecteurs `rules_es.py` : V:PRET (preterite irreg fui/vi/hice 30 verbs dict), PREP:A_PERSONAL (a-marker objet humain transitive verbs + 30 animate nouns), CONCORD:GEN (article-noun gender mismatch 50 nouns lexicon), V:SUBJ (subjunctive triggers querer/esperar/para que + indicative form dict 50+ verbs).
- 11 codes ES existants intégrés tolerance_matrix.yaml familles (étaient stranded — latent bug helper+chat_router pre-Session 51 où enrich_error_fields retournait tier=None pour ES codes).
- 8 nouveaux fewshots Lyster cells stratifiés A1/A2/B1/B2/C1 implicit_recast + elicitation + prompt_plus_remediation. ES fewshots 14 → 22 (parité EN count).
- Re-record ES goldens post-rules+matrix+fewshots (sha `f7fb532` + `1974a9d`).

**ADR-013 + scope tier decision** (commit `2549d4a`) :
- Decision Sinse pivot stratégique : EN + ES = flagship A1-C2 (différenciation marché + sunk cost + ES 500M+ speakers), IT + DE + JP + RU = essential A1-B2 cap (JLPT N5-N2 / TORFL TEU-TRKI-2).
- Drivers : voice features tooling cap B2 (Whisper degrade C1/C2 idiomatique) + market reality 95% B2 ceiling + Lyster framework applicability + effort -22 person-days savings sur Wave 2-4.
- Phase 1 effort recalibré : IT 17→13j, DE 20.5→16j, JP 36→28j, RU 26-28→21j. Total combined Wave 2-4 = ~78j (vs 100j original Session 51 estimate).
- Path dependency mitigée : research C1/C2 reste dans 4 multilang research files comme "future scope" — re-extension possible si signal market.

**Wave 2-4 infrastructure prep** (commit `0cd76dc`) :
- Pre-registered 38 error_codes IT/DE/JP/RU dans `rules.py:ERROR_CODE_TO_FAMILY` (8 IT + 10 DE + 11 JP + 9 RU) + tolerance_matrix.yaml 7 familles (verb_tense, verb_usage, morphology, surface, preposition, vocabulary, word_order, discourse).
- L1 transfer files expansion 5→12 entries × 4 langues : `fr_to_it.yaml` (clitiques doubles + congiuntivo + Lei register + ne partitive + cognate orthography), `fr_to_de.yaml` (trennbare Verben + Adjektivdeklination + Genitiv→Dativ + Modalpartikeln + Eszett), `fr_to_ja.yaml` (counters + subject elision + te-form aspect + conditional 4-way + transitivity pairs + kana-kanji-mixing), `fr_to_ru.yaml` (motion verbs directional + reflexive -ся + numeral agreement + soft sign + aspect prefix + ty/vy patronymic).
- 4 langues × 12 entries × validation 5-layer pipeline references (sources Layer 1-3 cited inline).

**Validation methodology without natives** (commit `d3eb101`) :
- Documentation pipeline canonique solo dev : Layer 1 authoritative published curricula + Layer 2 error-tagged learner corpora + Layer 3 academic SLA research peer-reviewed + Layer 4 LLM cross-validation (GPT-4o + Claude + Gemini) + Layer 5 oracle harness behavioral.
- 4 l1_transfer files updated : "needs native speaker review" → "5-layer validation pipeline references". Pas un seul native speaker required pour replication EN/ES pattern.

**TODO.md priority books acquisition** (commit `00d445a`) :
- P0 immediate acquisition list : Profile Deutsch (~48€ Wave 2 DE blocker) + Lightbown & Spada 5e (~30€) + Lyster monographs (~25-35€) + JLPT 公式問題集 (~40-60€ Wave 3) + CILS Sillabo (~60-80€) + TORFL practice volumes (~50-70€). Total ~250-300€ neuf, ~100-150€ second-hand, gratuit si bibliothèque universitaire.

### Decisions

- **L139** : Pattern direct-write knowledge/ avec frontmatter status (Session 51) — drop inbox/ staging zone (modèle pre-Session-51 requérait Sinse manual /promote bottleneck). Anti-friction solo dev pattern. Cohérent L42.
- **ADR-013** : language scope by tier — EN+ES flagship A1-C2 vs IT+DE+JP+RU essential A1-B2 cap. Drivers voice tooling + market + effort + Lyster applicability.
- **L140** : Pre-register error_codes IT/DE/JP/RU dans ERROR_CODE_TO_FAMILY + tolerance_matrix avant rules_{lang}.py implementations land — évite latent bug Session 51 (ES codes étaient stranded).
- **L141** : Validation pipeline 5-layer canonique solo dev sans native speaker — replication EN/ES pattern documentée explicitement (`vault/knowledge/multilang-validation-without-natives.md`).

### Gotchas

- **Harness/prod scope divergence latent depuis Session 40** — `oracle/judges/dify_client.py:call_agent` n'invoquait pas `build_dynamic_sections` qui était pourtant prod-aligned dans chat_router. Tous scores oracle V1 historiques mesuraient "Teacher EN lobotomized". Pattern à généraliser : harness/prod scope parity check obligatoire avant toute baseline measurement.
- **ES error codes stranded dans tolerance_matrix** — 11 ES codes existants (V:SER_ESTAR, V:GUSTAR_SUBJECT, PREP:POR_PARA, etc.) étaient dans `ERROR_CODE_TO_FAMILY` rules.py mais pas dans `tolerance_matrix.yaml` families → `enrich_error_fields` retournait tier=None → helper skippait → errors_detected vide → dosage_block empty. Latent bug pre-Session 51. Fixed Wave 2 ES.
- **Dify openai_api_compatible plugin v0.0.42** : `response_format=json_schema` (string) + `json_schema` (string of schema content) → injecte schema dans system prompt comme texte. **PAS** native OpenAI Structured Output enforcement. Nécessite `structured_output_support: "supported"` dans encrypted credentials pour activer params. Plan A (Tier 2 BIPED) doit en tenir compte.
- **Plan B regression -6** (Session 51 PM) : prompt patch positive STYLE PAR TYPE block avec implicit_recast few-shots A1/A2 a regressé 14/26 (vs baseline 20/26). Cause : few-shots A1/A2 ont biaisé B1/B2/C1 register vers chatty trop bas niveau + parts françaises ("Apprenant :", "Modèle 1") ont leaké dans scaffolding L2_ratio à C1. Smoke test 1 scénario A2 = false positive. Logged failures.md.
- **gemini-3-1-flash-lite Groq judge pas strictement déterministe à temp=0.0** : 38% split rate run-to-run même avec target LLM bit-identical (temp=0.2). Variance vient du judge model. Tier 1 asymmetric threshold 0.7 absorb mais ne résout pas root. SGLang local Qwen3-8B `--enable-deterministic-inference` candidate (Sept 2025).
- **RPD limit 540/day gemini-3-1-flash-lite** : battery n=5 = 390 calls minimum + retries → hit limit après ~2-3 batteries. Tier 1 measurement Session 51 différé post-RPD-reset.
- **Maestro ES temp=0.2 résiduel non-déterministe** : 2 runs ES sur même input différent (vs Teacher EN bit-identical à temp=0.2). Variance résiduelle ES. Tier 1 confidence threshold absorb.
- **Native speakers PAS disponibles solo dev** : validation must use 5-layer pipeline (authoritative curricula + corpora + SLA research + LLM cross-validation + oracle). Replication EN/ES pattern. Documenté dans vault.

### Commits

- `7a7fae1` [fix] oracle harness — align Teacher EN inputs with chat_router prod scope
- `2b76917` [fix] oracle — judge retry/backoff + record_golden via aligned path
- `535c09b` [chore] oracle — re-record 26 teacher_en goldens post-alignment + temp=0.2
- `d672cbd` [fix] oracle Tier 1 — n_votes 3→5 + judge_fail_threshold 0.7 (asymmetric)
- `f7fb532` [docs] TODO Session 51 — P0.1+P0.2 livrés + Tier 1/2/3 roadmap research-backed
- `d1ed462` [chore] oracle — re-record 24 maestro_es goldens post-alignment + temp=0.2
- `90bd135` [docs] TODO — Maestro ES infra parity Session 51
- `ef0c91a` [fix] taxonomy ES — Wave 2 detectors V:PRET + PREP:A_PERSONAL + CONCORD:GEN + ES codes folded in tolerance matrix
- `057e704` [chore] oracle — re-record 24 maestro_es goldens post Wave 2 ES rules + matrix
- `1974a9d` [fix] taxonomy ES — V:SUBJ detector + 8 fewshots recast/elicit per CEFR×move
- `9c912ba` [chore] oracle — re-record 24 maestro_es goldens post Wave 2 P2
- `2549d4a` [docs] ADR-013 — language scope by tier (EN+ES flagship A1-C2 / IT+DE+JP+RU essential A1-B2)
- `0cd76dc` [fix] taxonomy + l1_transfer — pre-register IT/DE/JP/RU codes + expand L1 transfer 5→12 entries each
- `d3eb101` [fix] l1_transfer — replace 'native speaker review' framing with 5-layer validation pipeline references
- `00d445a` [docs] TODO — Session 51 P0 priority books acquisition list

(16 commits academia repo cumulés — vault commits séparés cf vault log.md)

---

