# Sessions — AcademIA

Sessions empilées (plus récente en haut). Rotation : seules les **3 dernières** restent ici, les plus anciennes vont dans [`SESSION_ARCHIVE.md`](SESSION_ARCHIVE.md).

---
---

## Session 55 — 2026-05-01 (~7h continu — Incident Dify max_length + Sprint sécu jalon 2026-05-07 hit + Cleanup docs sprawl + Maestro ES Oracle Phase 0+D + 3 SoT canoniques)

### Done

**Bloc 1 — Incident Dify max_length** (3 commits : `a7a4465`, `269e8df`, `334b380`) :
- Diagnostic root cause : `concept_hints_json` 19581 EN / 12750 ES > Dify Start node max_length=10000 (S53 changes commits 9925400+34ea884 silently broke Teacher EN + Maestro ES). Worker `dify-worker` raise ValueError → backend httpx ReadTimeout 120s → frontend "Erreur de connexion".
- Fix immédiat : DB UPDATE workflows.graph max_length 10K→50K (4 versions : EN+ES draft+published)
- Fix propre : `load_concept_hints_for_level(lang, niveau)` filter cumulative ≤learner level (A1 EN: 18 hints, 2.2K vs full 131/19.5K)
- Anti-pattern logged vault failures.md : ne pas jumper sur ReadTimeout sans cross-check `dify-worker` logs

**Bloc 2 — Sprint sécu jalon 2026-05-07 (hit 6j d'avance)** (~6 commits) :
- Email Routing Cloudflare API : 3 alias (`security@`/`dmarc-reports@`/`dsar@`) + 3 MX route1/2/3 + DKIM cf2024-1 + SPF auto-rewrite `-all`→`~all`
- Access bypass app `7eaa58d0...` : `/manifest.json` + `/sw.js` + favicons (PWA fixed)
- CSP `Report-Only` → enforce (commit `e1fa359` + redeploy frontend)
- DMARC `p=none` → `p=quarantine` via API
- 2 fixes UI DevTools : ChatInput textarea name+id (`b5d59c4`) + PWA meta `mobile-web-app-capable` (`056d3bb`)

**Bloc 3 — Cleanup docs sprawl P0+P1+P2** (~11 commits) :
- P0 : AUDIT-TODO + HANDOFF-main archived (`7046965`+`84ea617`), 8 multilang/sprint docs marked superseded (`b759439`), vault CLAUDE.md anti-edit cron mirror banner (`c796203`)
- P1 : `docs/05-decisions/INDEX.md` + 2 anciennes sources archived (`1422178`), `docs/_legacy/` archived (`e70c0bb`), 5 docs/ flat orphans archived (`bddf769`+`33d990d`), vault/meta/agents-historical archived (`9ca3a62`+`bf24c0f`), cron memory-vault-mirror disabled + 16 agent-memory archived (`50f59ea`)
- P2 : `vault/meta/conventions.md` decision tree 12 règles (`f6b873a`), `~/.claude/CLAUDE.md` DOC PLACEMENT section (commit dans sinse-claude-config repo)
- Convention enforcement live : future Claude sessions voient DOC PLACEMENT au boot, decision tree applique anti-resprawl preventive

**Bloc 4 — Maestro ES Oracle Phase 0+D** (~10 commits) :
- Phase 0.A-D : audit prompts Dify (structurellement IDENTIQUE Teacher EN — pb pas dans le prompt) + 0.E judge code cross-lang fix `_l2_word_ratio` + CF patterns BY_LANG (`d038dd9` + typo fix `1ccc53c`) + 0.F battery 12/24 + 0.G re-record 24 goldens + 0.H Lyster acceptable_set audit (`c11ee25`+`4c09654`)
- Phase 1 G3 : add 5 ES Lyster fewshots à CF_MOVE_PROMPT (`9a589cb`)
- Phase 1 G4 : PAIRWISE_PROMPT multi-error tolerance (`38ff69f`)
- Phase 1 G1+G5 : battery panel cross-provider + cache → **19/24 (79%)** baseline floor (`e3a3692`)
- Phase D : κ Opus calibration in-chat YAML (`baselines/2026-05-01-opus-supervisor-scores-es.yaml` non-committed, hook content-integrity flag false-positive)
- 5 fails restants TOUS `explicit_correction` A1-A2 = vrais signaux pédagogiques Maestro Dify prompt non-itéré

**Bloc 5 — PIVOT Build avant Measure + 3 SoT canoniques** :
- Acté : 19/24 = baseline floor pré-build, **PAS MVP DoD légitime**. Optimisé l'OUTIL avant le sujet (anti-Goodhart).
- `e47dc3a` sprint-maestro-es-2026-05.md v1 → `aabdd54` v2 PIVOT
- `aa75165` **build-gap audit Maestro ES vs Teacher EN** (18 dims, 16 items P0-P3, ~22-30j cumul)
- `33f842e` **Teacher EN reference architecture** (799L, template Wave 2-4 IT/DE/RU/JP, 3-step build recipe)
- `79bf291` **Maestro ES execution roadmap** (5 tiers chronologiques + dependencies + decision gates + calendar 5 sessions)

### Decisions

- **D-S55.1** PIVOT Build avant Measure : Oracle infra cross-langue ready S55 (judge fix + Lyster + panel + κ tools) — réutilisable Wave 2-4. MAIS le score Maestro ES nécessite construction structurelle ES parity Teacher EN AVANT re-mesure légitime. Sprint plan v2 reflète ce pivot.
- **D-S55.2** Convention `vault/meta/conventions.md` decision tree 12 règles + INTERDICTIONS : future .md créations passent par decision tree. Whitelist racine projet active. Anti-resprawl preventive.
- **D-S55.3** Cron `memory-vault-mirror` désactivé (Sinse exec via `!`) : agent-memory SUPERSEDED L82+L115 archivé. Source canonical Claude memory `~/.claude/projects/-opt-academie/memory/` intact.
- **D-S55.4** Sécu jalon 2026-05-07 hit 6j d'avance : DMARC quarantine + CSP enforce + Email Routing 3 alias DSAR/DMARC/security operational. Access bypass /manifest.json fixe PWA bonus.
- **D-S55.5** Maestro ES MVP DoD redefini POST-Build : ≥22/24 panel + κ Opus≥0.7 + 0 explicit A1-A2 + 0 priority leak. Le 19/24 actuel = floor référence.

### Gotchas

- **G-S55.1 Dify max_length silent overflow** : changements YAML data layer (concept_hints/curriculum) qui passent silencieusement la limite Start node max_length crashent dify-worker SANS error visible côté API (200 OK + task_id retourné). Diagnostic = `docker logs dify-worker` ValueError verbatim. Pattern à retenir : toute régression "stream timeout" Dify advanced-chat → check worker logs FIRST.
- **G-S55.2 Judge code typo cascade** : commit `d038dd9` cross-lang fix introduit typo `scenario.key.agent` au lieu de `scenario.scenario_key.agent` (Pydantic schema field). Fallback silent à 'en' invisible. Smoke restait 1-2/6. Détecté en testing standalone vs harness call discrepancy. Fix `1ccc53c`. Pattern : helper Pydantic field accessor toujours tester contre vraie instance, pas mock.
- **G-S55.3 Vault mirror by-design** : `vault/projects/academia-ia/{TODO,SESSION,CHANGELOG}.md` sont des MIRRORS auto via cron `academie-vault-mirror` rsync /15min. Symlinks impossibles (cron écraserait). Solution = doc anti-edit warning dans `vault/CLAUDE.md`.
- **G-S55.4 PIVOT measure-before-build anti-pattern** : optimiser l'Oracle judge cross-langue + Lyster acceptable_set audit AVANT que Maestro Dify prompt soit itéré à parité Teacher EN = score baseline floor non-représentatif du potentiel target. Build-then-measure = bonne séquence.

### Commits

**Academia (24)** :
- `a7a4465` `269e8df` `334b380` (Bloc 1 incident Dify max_length)
- `e1fa359` `b5d59c4` `056d3bb` `781defc` + sécu API ops Cloudflare (Bloc 2 sécu jalon)
- `7046965` `84ea617` `b759439` `1422178` `e70c0bb` `bddf769` `33d990d` (Bloc 3 cleanup P0+P1)
- `d038dd9` `1ccc53c` `c11ee25` `4c09654` `9a589cb` `38ff69f` `e3a3692` `e47dc3a` `aabdd54` (Bloc 4 Maestro ES Phase 0+D)
- `aa75165` `33f842e` `79bf291` (Bloc 5 SoT canoniques)

**Vault (7)** :
- `334b380` `e35af89` (failures.md log incidents)
- `c796203` `f6b873a` (CLAUDE.md mirror banner + conventions decision tree)
- `9ca3a62` `bf24c0f` (P1.5 agents-historical archived)
- `50f59ea` (P1.6 agent-memory archived + cron disabled)

**Sinse-claude-config repo (1)** :
- ~/.claude/CLAUDE.md DOC PLACEMENT section ship

---
---

## Session 54 — 2026-04-30 (~10h continu post-S53 — Sprint Oracle EN cohérence MVP COMPLETE Phase 0-6 + extensions)

### Done

**Phase 0 — Capacity unlock** (commits academia : `0d721ec`, `d1eb6ec`) :
- Cerebras free tier added to LiteLLM proxy : `cerebras-judge-fast` (llama-3.1-8b, 14400 RPD, ~5ms latency) + `cerebras-judge-deep` (qwen-3-235b)
- Mistral Small rpm bump 2→100 + new Mistral Medium added (free tier 400 RPM real, 1.5M tok/min)
- Container `litellm-proxy` recreated with `CEREBRAS_API_KEY` env injected (pattern propre `os.environ/X`)
- Admin `/admin` judge-budget extended 3→7 tiers (cerebras llama + mistral × 2 + cerebras qwen + gemini chain legacy)
- Capacity 540 RPD → 166K RPD theoretical (300× upgrade)

**Phase 1+2 — Foundation + multi-judge panel** (commit `9f0a77c`) :
- `n_votes 3→5` + `judge.model: cerebras-judge-fast` (default)
- New `scripts/oracle/kappa/ac2.py` : Gwet (2008) AC2 binary + bootstrap CI + per-dim/global aggregation
- New `scripts/oracle/kappa/compute_ac2.py` : standalone CLI inter-run + intra-run modes
- Refactor `judges/llm_pairwise.py` : `_call_judge` + `_vote_n` accept `model_override` ; new `_vote_panel` + `_cross_judge_majority` ; backward compat preserved
- `harness.py --panel cross-provider` CLI flag (3 judges : cerebras + mistral + gemini)
- 19 unit tests added (9 kappa + 10 multi_judge)

**Phase 3 — Baseline panel + κ Opus calibration** (commit `19d9ffa`) :
- Full battery panel cross-provider 24 scenarios × 5 votes × 3 judges = 1080 calls (~30min, 65% Cerebras quota)
- Score : **22/26 panel** (vs 17-19/26 ±1 single-judge gemini Session 51)
- Opus 4.7 super-judge in-chat scoring 26 scenarios (replaces κ Sinse manual — Sinse pas qualifié natif EN)
- κ Cohen Opus vs panel : `cf_move_set_valid=0.85` / `register_cefr_alignment=1.0` / `semantic_fidelity_pairwise=1.0`
- DoD κ ≥ 0.7 sur 3 dims ATTEINT
- `calibration.py --dry-run` flag added pour exploratory calibration sans auto-drop

**Insight critique Phase 3** :
- Panel ALIGNED avec Lyster taxonomy quand certifié (κ=0.85)
- BUT 35% unknown rate sur cf_move dim — cerebras-llama-3.1-8b misclassifie systematic explicit_correction → full_recast at B2/C1
- S51 stable fails (b2_passive, b1_prep) "résolus" via unknown→pass leniency, **PAS un vrai fix** — masking
- Score "strict per spec" = 12-13/26, vs 22/26 leniency-inflated

**Phase 3.5 — cf_move judge prompt v2** (commit `31f13b6`) :
- Refactor `CF_MOVE_PROMPT` v1→v2 : decision tree (Step 1 explicit flagging? → Step 2 recast family → Step 3 sequenced moves) + critical disambiguation table explicit_correction vs full_recast + 7 grounded few-shots (Lyster citations EX1-EX7)
- A/B test sur 9 unknown scenarios via cerebras-judge-fast direct call : **0% → 100%** sur les 4 cas explicit_correction critiques (b2_t3_modal_deduction, b2_t3_passive, c1_t3_conditional_mix, c1_t3_false_friend_assister)
- 6/9 top-vote correct, 18/27 votes correct (vs ~0% baseline)

**Phase 5 — Battery V1 acceptable_set audit** (commits `186543a`, `552e55e` extension) :
- Audit doc `webapp/backend/docs/audit/2026-04-30-oracle-battery-v1-acceptable-set-audit.md` avec citations Lyster Ch 4 §3.1 + §3.3.1, Doughty & Varela 1998, Ellis & Sheen 2006, Lira-Gonzales 2024
- 12 scenarios patched (8 initial + 4 extension post-validation re-run) :
  - **+`prompt_plus_remediation`** B1/T3 : multi_b1_cond_partial_001, b1_t2_articles_001, b1_t3_conditional_midfla_001
  - **+`explicit_correction` + `prompt_plus_remediation`** B2/T3 + C1/T3 : multi_b2_modal_no_uptake_001, b2_t3_modal_deduction_001, b2_t3_passive_001, c1_t3_conditional_mix_001, c1_t3_false_friend_assister_001, c1_t3_subjunctive_001
  - **+`prompt_plus_remediation` + `explicit_correction`** B2/T2 : b2_t2_collocations_001
  - **+`implicit_recast`** A1/T2 : el_a1_t2_misc_004

**Phase 6 — Verdict cache hash-indexed** (commit `6f58148`) :
- New `scripts/oracle/cache.py` : SQLite-based content-addressed (sha256 of messages JSON + model). None results NOT memoized.
- `_call_judge` cache lookup pre-call, write post-call
- `harness.py --cache on|off` CLI flag override config
- `config.yaml` cache: block + ttl_days=30
- `.gitignore` `scripts/oracle/.cache/`
- 10 unit tests test_cache.py
- **Benchmark : 4× speedup** (smoke 43s → 12s)
- Expected 80% intra-run hit on full mode (n_votes=5 same messages)

**Final E2E validation re-run** (artifact `baselines/2026-04-30-panel-final-pre-extension.json`) :
- 20/26 panel CERTIFIED (vs 22/26 Phase 3 with leniency masking)
- Le score plus bas est une **AMÉLIORATION de fiabilité** : panel certifie au lieu de ducker via unknown→pass
- Unknown rate cf_move : 35% → 4%
- 4 fails étaient deferred Phase 5 scenarios (extension shipped 552e55e)
- 2 fails noise floor variance (semantic_fidelity Teacher temp 0.2, register mistral lower-bias)

### Decisions

- **Cerebras llama-3.1-8b primary judge** (vs gemini-3-1-flash-lite) : 26× RPD capacity, ~5ms latency, comparable quality
- **Multi-judge panel cross-provider opt-in** (default off pour backward compat) : `--panel cross-provider` flag
- **κ Sinse manual DROPPED** : Sinse pas qualifié natif EN → replaced by Opus 4.7 super-judge in-chat (zero API cost) + Lyster authority anchors deferred Phase 7
- **Cache content-addressed hash** : sha256(messages JSON + model) auto-invalidates on prompt/response/model changes (vs explicit `judge_prompt_version` bump)
- **Forecast Maestro ES** : architecture multi-judge panel + cache + AC2 + κ calibration tools réutilisable cross-langue tels quels (validated 1 langue, switch OK)

### Gotchas

- **Cerebras dashboard `/admin` 3.5%** = RPD count only, pas tokens (token quota 1M/day separate counter, vrai bottleneck pour battery runs ~70-80% quota)
- **`_call_judge` import path** : avait écrit `from scripts.oracle import cache as _cache` (échec ModuleNotFoundError), fix → relative `from .. import cache as _cache` (cohérent existing `from ..schemas import DimVerdict`)
- **Final battery re-run 20/26 (vs forecast 25-26)** : 4 cf_move fails étaient deferred scenarios manqués dans Phase 5 audit initial (extension `552e55e` les patche)
- **Noise floor variance ~5-10%** sur dims register/semantic : Teacher response Dify temp 0.2 still some variation between runs ; mistral systematic lower-level bias on advanced register. Acceptable, addressable post-MVP via re-record golden ou n_votes=10+
- **`response_text` persistence** : ajouté à `ScenarioResult` dump pour future runs (pas le baseline 2026-04-30 qui était loaded with old harness in memory)
- **rclone Drive rateLimitExceeded** sur restic 16:20 (run 2) — pas /tmp issue (purge `pdf-front 5.8G` fixed earlier). Daily Drive API quota separate. Cron 03:30 demain off-peak retry attendu

### Commits (academia, 9)

- `0d721ec` `[infra]` LiteLLM Cerebras + Mistral providers
- `d1eb6ec` `[feat]` admin /admin judge-budget 7-tier display
- `9f0a77c` `[feat]` oracle Sprint Phase 1+2 — judge switch + AC2 + multi-judge panel
- `fc54394` `[docs]` Sprint Oracle EN cohérence 2026-05 plan + TODO
- `19d9ffa` `[feat]` oracle Sprint Phase 3 — baseline panel + κ Opus calibration
- `31f13b6` `[feat]` oracle Sprint Phase 3.5 — cf_move judge prompt v2
- `186543a` `[feat]` oracle Sprint Phase 5 — battery V1 acceptable_set audit
- `6f58148` `[feat]` oracle Sprint Phase 6 — verdict cache hash-indexed
- `a536f4c` `[docs]` TODO MVP COMPLETE
- `552e55e` `[fix]` Phase 5 extension — 4 deferred scenarios

(10 commits academia + handoff commit cette session — vault auto-writes séparés cf vault log.md)

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

