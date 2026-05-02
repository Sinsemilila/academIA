# TODO — AcademIA
Last updated: 2026-05-02 — Claude (Session 58 — Onboarding Marie + RAG knowledge base 22 PDFs livré end-to-end + profile-building meta)

## 🔝 EN COURS — RESUME AU PROCHAIN /pickup (S59)

### 🎯 Maître Comptable Mode B Phase 1 — LIVRÉ S57 ✅ + RAG livré S58 ✅

Voir [`docs/00-project/sprint-maitre-comptable-2026-05.md`](docs/00-project/sprint-maitre-comptable-2026-05.md) pour roadmap complète.

**État production post-S58** :
- `/chat/maitre_comptable` accessible Marie ✅ (compte `mariejuanes` + CF Zero Trust policy email Marie OK)
- Dify chatflow `4ce8ffe2-0cdf-4fa8-aab4-478e5dd8ac1c` (gpt-4o-mini + vision multimodal + **RAG knowledge node wired**)
- Backend `AccountingDomain` + 5 tools `/internal/compta/tools/*` + 57 tests green
- Frontend agent registered + flag SVG + RGPDDisclaimer one-time
- **RAG dataset `79ab2618-5762-465d-9fab-b5ed54cff214`** : 22 docs / 15,689 chunks / 5.86M words searchable / OpenAI text-embedding-3-small 1536 dims / Qdrant vector store
- Metadata fields populated (authority_priority, domain, valid_from, bc) sur 22/22 docs

### 🔴 P0 IMMÉDIAT S59 — Test live Marie post-RAG + finir P1

- [ ] (sinse + marie + claude, S59 ~30 min) **Test live Marie 12 questions** — critères validation cf `webapp/backend/docs/maitre-comptable-system-prompt.md` §7 (≥10/12 utiles, 0 hallucination, posture Lyster majoritaire, latence <5s). RAG ACTIVÉ donc questions pointues sur PCG/BOFiP/DSN/CNIL devraient être enrichies.
- [ ] (claude, sliding) Iter system prompt Dify selon retours empiriques Marie (push update via API automation pattern S57)

### 🟠 P1 COURT TERME (S59-S60, ~1.5j restants)

- [⚠️] **P1.1 Wire 5 tools backend dans Dify Custom Tools** — **BLOCKED S59 par bug intégration Dify plugin daemon ↔ dify-api inner API** (cf vault/projects/academia-ia/failures.md 2026-05-02 16:30). Progress S59 : (a) Custom Tools provider `compta_tools` registered Dify workspace (provider UUID `855f3981-d9e8-4dd3-b0ce-f69a8c20645a`, OpenAPI spec built `scripts/sprint-maitre-comptable/build_compta_openapi.py`, 5 tools tested OK via `/api/test/pre`), (b) plugin `langgenius/agent:0.0.37` installé via marketplace API, 2 strategies (function_calling + ReAct) registered, (c) `agent_compta` node patcher écrit `dify_patch_maitre_agent_tools.py`, draft+publish OK, MAIS LLM backwards-invoke via plugin daemon retourne `404 /inner/api/invoke/llm` (probably trailing slash bug `dify-plugin-daemon:0.5.3-local` Go binary vs `dify-api:1.14.0` flask-restx strict_slashes=True). (d) Rollback agent → llm_maitre via `dify_rollback_to_llm_node.py`, chatflow live 1.81s. **3 voies next** : (A) backend dispatch tools dans `chat_router.py` post-LLM parsing structured output ~2-3h, no Dify dep ; (B) restart Dify infra Sinse approval (cheap test, no fix guarantee) ; (C) plugin daemon upgrade compat 1.14.0.
- [x] ~~**P1.2 Knowledge base RAG** (~2-3j)~~ ✅ **LIVRÉ S58** (cf SESSION.md S58 Bloc 2). 22 docs ingested (sauf PCG Recueil dropped per D-S58.2), 15689 chunks Qdrant, knowledge node wired chatflow, retrieval testé score 0.78.
- [x] (claude, 2026-05-02, S59) **P1.3 Inject 8 few-shots Lyster compta dans system prompt** ✅ — system prompt Dify chatflow `4ce8ffe2` augmenté 1600→5656 chars via `scripts/sprint-maitre-comptable/dify_patch_maitre_fewshots.py` (pattern API automation S57/S58 réutilisé). 8 few-shots EX1-EX8 injectés (clarification_request, metalinguistic, partial_recast, drill, multimodal, anti-cheating, incertitude assumée). Smoke 2/2 : EX4 concept emprunt reproduit fidèlement (few-shots in-context confirmé), EX2 inversion débit/crédit posture Lyster OK mais diagnostic numérique faux sans tools (argument fort P1.1). Draft hash cb2a5936→dca9d0fdfc65, published OK.

### 🟡 P2 MOYEN TERME (S60-S62, ~5-8j) — Mode A Lessons

- [ ] **P2.1 Mode A "Lessons / pratique guidée" Phase 1 MVP** (~5-8j) — module pivot BC1.4 TVA mécanisme, chatflow séparé `comptable_fr_lessons`, scenarios pasticher Cas Studi pattern, UX combo A+B+E
- [ ] **P2.2 `rules_compta.py` MVP** (~2-3j) — étoffer AccountingDomain Phase 2 detect_errors real impl
- [ ] **P2.3 Tier 6 RE-MEASURE compta** (~1-2j) — battery 12-15 scenarios + multi-judge panel + κ Opus calibration

### 🟢 P3 LONG TERME (S62-S65, ~10-15j) — Polish Mode A

Voir sprint roadmap pour détails P3 (UI custom JournalEntry + CascadingEffects + FSRS rote layer + IRT placement).

### 🔵 P4 POLISH PREMIUM (S65+ optional) — voice + browser ext + anti-cheating avancé

### 🟣 P5 SCALING (S70+) — Multi-apprenants + microentreprise launch + RGPD scope SaaS ADR-018

---

## 🗂️ AUTRES TODOs cross-projet (legacy ou autres sprints)



## ✅ OBSIDIAN MIGRATION CLOSED (2026-04-28)

**Closure formelle Session 50** :
- v0.1 LIVRÉE 2026-04-25 ✅
- v0.2 LIVRÉE 2026-04-26 ✅
- Phase 0 closure 13 items LIVRÉE 2026-04-26 ✅
- Audit intégral + Phase A docs cleanup + tests E2E live LIVRÉS 2026-04-28 ✅
- Syncthing 3 devices opérationnel ✅
- v0.3 différé post-mesure 2-4 sem usage réel
- **Session 52** (2026-04-29) — folder `projects/obsidian-migration/` archived → `archive/obsidian-migration/`

**Lock prochain projet libre** : Sinse choisit explicit P0/P1/P2/P3 ci-dessous.

## 📚 P0 — Bibliothèque acquisition — Session 52 RECAP

**Session 52 (2026-04-29) MASSIVE ingestion** (cf [[../sinse-vault/projects/academia-ia/library-p3-roadmap]]) :
- ✅ Profile Deutsch (Glaboniat 2005 v2.0) acquired
- ✅ 8 Marugoto JP A1→B1 series (covers JFS Standard implementation)
- ✅ JFS Standard pamphlet 2024 + Guidebook 2022
- ✅ Hawkins/Filipović 2012 *Criterial Features in L2 English* (EN authority anchor)
- ✅ PCIC Cervantes A1-A2 + B1-B2 (ES authority anchor)
- ✅ CEFR Companion Volume 2020 ⭐⭐ (cross-lang umbrella authority)
- ✅ 12 free math/ML/stats canon (Hastie, James, Gelman, Murphy, Bishop, MacKay, Hernan, Boyd ×2, Deisenroth, Baker IRT, Jurafsky SLP3, D2L)
- ✅ 8 Anna's Archive Tier 1 (Embretson IRT, Bachman testing, Ortega SLA, DeKeyser practice, Norman DOET, Krug DMMT, Tufte VDQI, Strizver typography)
- ✅ Manning IR + Eisenstein NLP + VanderPlas + Sedgewick + Wickham R4DS + Goodfellow DL ⚠️excerpt + Hernan Causal

**Total** : 38 nouveaux PDFs ingested cosmos + 30 literature notes drafted vault. **85 livres tracked total** (vs 6 pre-Session-52 = +1316%).

### 🔴 P0 RESTANT — Wave-blockers acquisition (cf P3+ roadmap)

- [ ] **CILS Sillabo per livello** (Università per Stranieri Siena) — Wave 2 IT blocker authority anchor
- [ ] **TORFL Lexical/Grammatical Minimums** (Pushkin Institute) — Wave 4 RU blocker authority anchor
- [ ] **PCIC C1-C2** (Plan Curricular Cervantes Niveles C1-C2) — ES flagship A1-C2 gap (3ème volume manquant)

### 🟡 P1 — Strong recommendation

- [ ] **Goodfellow Deep Learning** re-acquire complete (actuel = excerpt 85p, vrai = 800p) — `deeplearningbook.org` HTML free OR Anna's
- [ ] **Marugoto Elementary 2 A2 Rikai/Katsudoo** ambiguity validate (manuel cover/TOC du fichier actuel)
- [ ] **Marugoto B2 source** (série culmine B1) — Tobira ou Quartet candidate pour JP B2 cap
- [ ] **English Vocabulary Profile + Grammar Profile** Excel exports — `englishprofile.org/wordlists` (signup gratuit)
- [ ] **VanderPlas PDSH** verify édition 1st (2016) vs 2nd (2022)

Voir `vault/projects/academia-ia/library-p3-roadmap.md` pour P2/P3 (~36 ouvrages, ~280-540€ cumulé total).

## 🔝 EN COURS — RESUME AU PROCHAIN /pickup

### 🎯 Sprint Oracle EN cohérence — 2026-05 (Session 53+)

**Plan détaillé** : [`docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md`](docs/01-pedagogy/sprint-oracle-en-coherence-2026-05.md)

**DoD** : Oracle EN trustworthy → switch Maestro ES. Score 22-24/26 stable + AC2 ≥ 0.7 + κ vs Sinse ≥ 0.7 + 0 stable structural fail.

#### Phase 0 — Capacity unlock (DONE Session 53)

- [x] (claude, 2026-04-30, S53) Cerebras key + LiteLLM proxy : `cerebras-judge-fast` + `cerebras-judge-deep` + `mistral-medium`
- [x] (claude, 2026-04-30, S53) rpm bump mistral-small 2→100
- [x] (claude, 2026-04-30, S53) Admin `/admin` judge-budget : 7-tier multi-provider display
- [ ] **Sinse ship** : 3 commits granulaires (LiteLLM config / admin tracker / frontend label)

#### Phase 1 — Foundation (Day 1, ~30 min) ✅

- [x] (claude, 2026-04-30, S53) `n_votes 3→5` + judge model → `cerebras-judge-fast` dans `scripts/oracle/config.yaml`
- [x] (claude, 2026-04-30, S53) Gwet's AC2 module : `scripts/oracle/kappa/ac2.py` (binary + bootstrap CI + per-dim/global aggregation)
- [x] (claude, 2026-04-30, S53) Standalone CLI `scripts/oracle/kappa/compute_ac2.py` (inter-run + intra-run modes)
- [x] (claude, 2026-04-30, S53) Tests `test_kappa.py` (9 unit tests green)
- [x] **Exit gate** : pytest 9/9 green + smoke run + AC2 CLI fonctionnel

#### Phase 2 — Multi-judge panel cross-provider (Day 2-3, ~2h) ✅

- [x] (claude, 2026-04-30, S53) Refactor `judges/llm_pairwise.py` : `_call_judge` + `_vote_n` accept `model_override` param
- [x] (claude, 2026-04-30, S53) New `_vote_panel` + `_cross_judge_majority` helpers (per-judge intra-majority → cross-judge majority)
- [x] (claude, 2026-04-30, S53) 3 `_score_X` accept `panel_models: list[str] | None` (backward compat preserved)
- [x] (claude, 2026-04-30, S53) `score_all` accept `panel_models` arg
- [x] (claude, 2026-04-30, S53) CLI flag `harness.py --panel cross-provider`
- [x] (claude, 2026-04-30, S53) `config.yaml` panel block (members + agreement_threshold)
- [x] (claude, 2026-04-30, S53) Tests `test_multi_judge.py` : 10 unit tests green (mock 3 judges + cross-judge majority + failure modes)
- [x] (claude, 2026-04-30, S53) **Validated end-to-end** : smoke panel run sur 6 scenarios → 4 pass / 2 fail / AC2 inter-run = 1.0 sur 5 dims
- [x] **Exit gate** : pytest 39/39 green + smoke panel green + cosmos 16/17

**Insight Phase 2** : panel révèle vraie cross-provider variance — sur `a2_t2_past_simple_001`, 3 modèles donnent 3 moves différents (`partial_recast` / `prompt_plus_remediation` / `full_recast`) — tous dans acceptable_set donc cross-judge cap converge en pass. Single-judge mode masquait cette divergence. Validates Rating Roulette ACL 2025 thesis.

#### Phase 3 — Re-mesure baseline + κ calibration (Day 3, ~2h) ✅

- [x] (claude, 2026-04-30, S53) Full panel battery 24 scenarios × 5 votes × 3 judges = 1080 calls (~30min, 65% Cerebras quota)
- [x] (claude, 2026-04-30, S53) Compare panel vs gemini-only baseline : **22/26 panel** vs 17-19/26 ±1 single-judge S51
- [x] (claude, 2026-04-30, S53) Opus super-judge in-chat (replaces κ Sinse manual — Sinse pas qualifié natif EN)
- [x] (claude, 2026-04-30, S53) `calibration.py --dry-run` flag added, `compute_ac2.py` with inter-run + intra-run modes
- [x] **κ Opus vs panel** : cf_move_set_valid=0.85 / register=1.0 / semantic=1.0 — **all ≥ 0.7 ✅**
- [x] **Exit gate** : DoD ATTEINT — Oracle structurellement aligned avec Lyster taxonomy

**Insights critiques Phase 3** :
- Panel n=17 verdicts définitifs sur 26 cf_move. **9 scenarios "unknown"** (35%) — panel can't reach consensus.
- Cerebras-llama-3.1-8b misclassifie systematic explicit_correction → full_recast à B2/C1. Mistral correct, gemini sparse votes.
- S51 stable fails (`b2_passive`, `b1_prep`) "résolus" via unknown→pass leniency — **PAS un vrai fix**, juste masking.
- Score "strict per spec" = 12-13/26, vs 22/26 leniency-inflated.
- 1 disagreement Opus vs panel : `risk_gravity_comm_breakdown_001` clarification_request not in acc (T4 spec design issue).

#### Phase 3.5 — Judge prompts audit ✅

- [x] (claude, 2026-04-30, S53) Refactor `CF_MOVE_PROMPT` v1→v2 : decision tree (Step 1 explicit flagging? → Step 2 recast family → Step 3 sequenced moves) + critical disambiguation table explicit_correction vs full_recast + 7 few-shot examples (Lyster-grounded EX1-EX7)
- [x] (claude, 2026-04-30, S53) A/B test on 9 unknown scenarios via direct cerebras-judge-fast call : 4 explicit_correction cases ALL FIXED (0% → 100%), 6/9 top-vote correct, 18/27 votes correct
- [x] (claude, 2026-04-30, S53) Smoke validation : 4/6 pass identical (no regression on simple cases), 39/39 oracle tests green
- [x] **Exit gate** : Cerebras-llama explicit_correction accuracy 0% → 100%. Worst-case dimension fixed.
- Artifacts saved : `baselines/2026-04-30-cf-move-prompt-v2-ab-test.py` + `*-results.txt`

**Misclassifications restantes (non-blockers, scenario design)** :
- `el_a1_t2_misc_002` → partial vs implicit (borderline, both pedagogically defensible)
- `multi_b2_modal_no_uptake_001` → explicit_correction vs prompt_plus_remediation (golden review needed)
→ tackled in Phase 5 scenario audit

#### Phase 5 — Battery V1 audit (PRIORITY UPGRADE — Phase 3 surfaced design issues)

Identified specific scenarios where `acceptable_set` is too narrow per Lyster taxonomy :

- [ ] B1+ T2/T3 scenarios : add `prompt_plus_remediation` to acceptable_set
  - `b1_t2_articles_001`, `b1_t3_conditional_midfla_001`, `b2_t2_collocations_001`
- [ ] T4 scenarios : add `clarification_request` to acceptable_set (Lyster Ch 4 §4 communication breakdown)
  - `risk_gravity_comm_breakdown_001`
- [ ] B2/C1 scenarios with `forbidden=[]` : decide if `explicit_correction` should be allowed (Lira-Gonzales 2024 supports for advanced)
  - `b2_t3_modal_deduction_001`, `b2_t3_passive_001`, `c1_t3_conditional_mix_001`, `c1_t3_false_friend_assister_001`
- [ ] A1 scenarios : decide on `implicit_recast` — currently NOT in acc but Lyster considers it valid (low salience caveat)
  - `el_a1_t2_misc_002`, `_003`, `_004`

#### Phase 4 — Fix 2 stable structural fails (Day 4-5, ~2j)

- [ ] `b2_t3_passive_001` : add 2-3 fewshots `implicit_recast` Lyster B2-passive + re-record golden
- [ ] `b1_edge_t2t3_prepositions_001` : add fewshot `partial_recast` B1-preposition + re-record golden
- [ ] **Exit gate** : 2 fails passent en `pass` sur 3 runs consécutifs + 0 régression

#### Phase 5 — Battery V1 audit ✅

- [x] (claude, 2026-04-30, S53) Audit doc `webapp/backend/docs/audit/2026-04-30-oracle-battery-v1-acceptable-set-audit.md` with full Lyster citations (Ch 4 §3.1 + §3.3.1) + Doughty & Varela 1998 + Ellis & Sheen 2006 + Lira-Gonzales 2024
- [x] (claude, 2026-04-30, S53) 8 scenarios patched conservatively :
  - **+`prompt_plus_remediation`** for B1+ T2/T3 (3 scenarios) : `b1_t2_articles_001`, `b1_t3_conditional_midfla_001`, `b2_t2_collocations_001`
  - **+`explicit_correction` + `prompt_plus_remediation`** for B2/T3 + C1/T3 (4 scenarios) : `b2_t3_modal_deduction_001`, `b2_t3_passive_001`, `c1_t3_conditional_mix_001`, `c1_t3_false_friend_assister_001`
  - **+`implicit_recast`** for `el_a1_t2_misc_004` (A1/T2)
- [x] (claude, 2026-04-30, S53) Lint 26/26 + pytest 39/39 green
- [x] **Exit gate** : 4 panel fails + 4 unknown→pass leniency expected resolved post-changes (full battery validation pending re-run)

#### Phase 6 — Cache verdicts hash-based ✅

- [x] (claude, 2026-04-30, S53) New `scripts/oracle/cache.py` : SQLite-based content-addressed (sha256 of messages JSON + model). None results NOT memoized.
- [x] (claude, 2026-04-30, S53) `_call_judge` cache lookup pre-call, write post-call (relative import `from .. import cache as _cache`).
- [x] (claude, 2026-04-30, S53) `harness.py --cache on|off` CLI flag override config.
- [x] (claude, 2026-04-30, S53) `config.yaml` cache: block + ttl_days=30. `.gitignore` `scripts/oracle/.cache/`.
- [x] (claude, 2026-04-30, S53) 10 unit tests `test_cache.py` (key determinism, hit/miss, None handling, purge, unicode).
- [x] **Exit gate** : 4× speedup smoke (43s → 12s) ; 49/49 tests green ; expected 80% intra-run hit on full mode (n_votes=5 same messages).

═══════════════════════════════════════════════════════════
✅ **MVP Oracle EN trustworthy** — switch Maestro ES authorized.
═══════════════════════════════════════════════════════════

#### Phase 7 — V2 battery seed (post-MVP)

- [ ] Plan doc `docs/01-pedagogy/oracle-v2-battery-design.md` (skeleton only)
- Implementation différée post-Maestro ES launch.

═══════════════════════════════════════════════════════════
✅ MVP Oracle EN trustworthy → **switch Maestro ES**
═══════════════════════════════════════════════════════════

---

**Session 51 (2026-04-28/29) livré** :
- ✅ P0.1 — harness/prod scope alignment (`build_full_dify_inputs`, commit `7a7fae1`). Découverte : harness mesurait Teacher EN lobotomized (2 inputs vs 11 prod).
- ✅ P0.2 — scoring stabilization tier 0 : judge retry/back-off (`2b76917`), Dify temp 0.7→0.2 (SQL direct), goldens re-recorded (`535c09b`).
- 📊 Nouveau baseline aligned : **18-19/26 ±1** (vs 20/26 lobotomized). 2 stable cf_move fails identifiés (b1_edge prepositions full_recast, b2_t3_passive explicit_correction).
- 📚 Research synthesis : `vault/inbox/2026-04-29-teacher-en-improvement-research-bibliography.md` (alignment drift Cuenca-Jiménez 2025, BIPED two-step ACL 2024, Rating Roulette judge variance, SGLang deterministic).

**Lock prochain horizon** : Tier 1 scoring stabilization avant Maestro ES (architecture réutilisable cross-langues).

### 🎯 Teacher EN improvement roadmap (research-backed, Session 51 synthesis)

**Tier 1 — Scoring stabilization** (~1-2j, free-tier compatible) — **EN COURS Session 51**
- [x] Judge retry/back-off (commit `2b76917`)
- [x] Dify LLM temp 0.7→0.2 (Session interactive node, SQL direct)
- [x] Goldens re-recorded post-alignment (commit `535c09b`)
- [ ] **n_votes 3→5 + confidence threshold ≥3/5** : `skip` if uncertain (don't penalize Teacher EN for judge noise) → `config.yaml` + `llm_pairwise.py:_majority_*`
- [ ] Gwet's AC2 reporting between runs (κ paradox on skewed batteries) — formula in `oracle/kappa/`
- [ ] **(Future)** SGLang local Qwen3-8B `--enable-deterministic-inference` judge OR two-judge panel (gemini + Llama-3.1 Groq)

**Tier 2 — Architecture refactor BIPED two-step** (~1-2 sem) — **PENDANT Maestro ES**
- [ ] Split Dify "Session interactive" en : (a) CF-move classifier strict JSON enum + reflection field, (b) response generator conditioned on chosen move
- [ ] Many-shot bank stratifié (CEFR × move) — 50-200 exemplars par cellule (12+ minimum). Stratify by failure-mode analysis from current battery (b1 prep + b2 passive priority).
- [ ] Apply architecturalement aux 2 langues simultanément (EN + ES)

**Tier 3 — LoRA fine-tune** (~2-4 sem) — **APRÈS Maestro ES baseline si plateau persiste**
- [ ] Synthetic Lyster-labeled CF corpus (Session 47 `generate_v3_training_data` partial)
- [ ] LoRA Llama-3.1-8B / Qwen3-8B / Mistral-7B (EvalYaks precedent : 96% adherence)
- [ ] Inference cost ÷10 long-terme

### 🌐 Other P0/P1/P2/P3 candidates

- **Calendar 2026-05-07** (DMARC `p=quarantine` + CSP enforce flip + CF Email Routing) — **8 jours fenêtre restant**
- **Eisenday V2 backlog** (dormant, app shortcuts / onboarding / widget / R8)
- ~~**Maestro ES alignment**~~ : ✅ Session 51 — `build_full_dify_inputs(scenario, "maestro_es")` validated, Dify temp 0.7→0.2 patched (workflow `d3df0ef0-...`), 24 goldens re-recorded (commit `d1ed462` sha `f7fb532a1ba4`). Battery measurement awaits judge RPD reset (Groq gemini-3-1-flash-lite 481/540 RPD).
- **v0.3 mesure usage** (post 2-4 sem données réelles, démarrage compteur Session 49 = 2026-04-26)

## 📚 Per-language book incorporation roadmap (post-S53 skim batch)

**Context** : Session 53 skim batch (74/85 books skimmed = 87% library tracked) a révélé que `curriculum_en.yaml` + `curriculum_es.yaml` ont été construits "à l'aveugle" pré-S52 (headers `# Sourced from CEFR Companion + EVP + Hughes` mensongers — aucun de ces books acquired avant S52). Maintenant on a les 4 authority anchors (Hawkins, CEFR Companion 2020, PCIC A1-A2, PCIC B1-B2) et 86 autres books skimmed. Roadmap d'incorporation par langue ci-dessous. Voir `/root/sinse-vault/knowledge/books/USAGE-MAP.md` pour status canonique des 90 books trackés.

### Phase A — P0 quick wins (Session 53, 2026-04-30, ✅ LIVRÉE)

- [x] (claude, 2026-04-30, Session 53, c94d896) TODO.md per-lang book incorporation roadmap (cette section)
- [x] (claude, 2026-04-30, Session 53, 895d32f) `concept_hints/en.yaml` expansion 20→**105** entries (100% curriculum_en coverage A1-C2, FR-oriented hints avec faux amis flagged)
- [x] (claude, 2026-04-30, Session 53, af891e1) `curriculum_es.yaml` flag 10 gaps inline TODO comments + honest header annotation (vs PCIC + CEFR Companion 2020)
- [x] (claude, 2026-04-30, Session 53, 3e53dba) `curriculum_en.yaml` + `curriculum_es.yaml` honest source attribution + document l1_transfer integration path (`teacher_prompt.py:488` consumer)
- [ ] **DEFERRED Phase B** : `phrasal_verbs` stratification (A2/B1/B2/C1 per Hawkins Ch 8) — **scope creep cross-système** (touche `tolerance_matrix.yaml` + `tolerance_matrix_v2.yaml` + `webapp/backend/app/routers/profile_router.py:559` prod code + Dify workflow `concept_hint_map` + `scripts/update_teacher_chatflow.py` + `scripts/sprint6/19_curriculum_en_apply_merge.py` + `scripts/e2e_promo_test.py:42`). Migration multi-system → bundled in Phase B EN audit.

### Phase B — P0 EN flagship audit (Session 53, 2026-04-30, ✅ LIVRÉE 4/4 commits)

- [x] (claude, 2026-04-30, S53, 8fbf718) **Hawkins Ch 9.1 horizontal summary** → `extracted/hawkins-filipovic-2012-criterial-features-l2-english/criterial-features-by-level.yaml`
- [x] (claude, 2026-04-30, S53, c4307b2) **CEFR Companion App 1** salient features + **App 7** changes 2001→2020 → 2 YAMLs
- [x] (claude, 2026-04-30, S53, a9d884f) Audit doc `webapp/backend/docs/audit/2026-04-30-curriculum-en-vs-authority.md` (105 concepts vs Hawkins criterial)
- [x] (claude, 2026-04-30, S53, 9925400) Patch `curriculum_en.yaml` 105→**131 concepts** (+26 criterial features added) + sync `concept_hints/en.yaml` 105→131 entries + C2 wording fix ("near-native" → "highly successful learner")
- [ ] **DEFERRED Phase B5** : Hawkins Ch 7 (22 syntactic features, 22p) full extraction — audit doc covered top-yield, full Ch 7 deferred
- [ ] **DEFERRED Phase B6** : Hawkins Ch 8 lexical/phrasal verb progression (13p) — bundled with phrasal_verbs cross-system migration
- [ ] **phrasal_verbs cross-system migration** : split A2/B1/B2/C1 + tolerance_matrix v1+v2 + profile_router.py:559 + Dify workflow + scripts update + e2e tests + golden re-record (~1-2j)
- [ ] **EVP/EGP signup englishprofile.org** (Sinse manual, gratuit) → Excel data extract

### Phase C — P0 ES flagship audit (Session 53, 2026-04-30, ✅ LIVRÉE 4/4 commits)

- [x] (claude, 2026-04-30, S53, 4fd7fda) **PCIC Vol A Gramática inventario A1+A2** → `extracted/cervantes-2006-plan-curricular-a1-a2/grammar-by-level.yaml` (extraction via WebFetch cvc.cervantes.es — preferred over scanned PDF 515p)
- [x] (claude, 2026-04-30, S53, 9c96c5b) **PCIC Vol B Gramática inventario B1+B2** → `extracted/cervantes-2006-plan-curricular-b1-b2/grammar-by-level.yaml`
- [x] (claude, 2026-04-30, S53, 41222ef) Audit doc `webapp/backend/docs/audit/2026-04-30-curriculum-es-vs-pcic.md` (51 concepts vs PCIC Gramática)
- [x] (claude, 2026-04-30, S53, 34ea884) Patch `curriculum_es.yaml` 51→**98 concepts** (split ser/estar A1 1→6 keys ; split subjuntivo B1 2→6 keys per trigger taxonomy ; split conectores B2 1→6 keys per discourse function ; +verbos_cambio_b2 critical gap ; +pasiva_perifrástica_b2) + sync `concept_hints/es.yaml` 34→103 entries + C1+C2 deferred (PCIC Vol C pending)
- [ ] **PCIC Vol C C1-C2 acquisition** (Sinse manual, gratuit `cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/`) — bloquant ES flagship audit complet A1-C2
- [ ] **DEFERRED Phase C5** : PCIC Funciones B1+B2 extraction (only A1+A2 covered Phase D1)
- [ ] **DEFERRED Phase C6** : PCIC Nociones específicas A1-B2 → `lexical-by-topic-by-level.yaml`
- [ ] **DEFERRED Phase C7** : PCIC Tácticas y estrategias pragmáticas B1+B2 → `pragmatic-strategies.yaml` (cross-ref Lyster cf-taxonomy)
- [ ] DELE A2/B1/C1/C2 oficial Modelos acquisition (dele.org signup gratuit, Sinse manual)

### Phase D — P1 nouvelles dimensions (Session 53 D1 LIVRÉE, D2/D3/D4 deferred)

- [x] (claude, 2026-04-30, S53, 6bb02fa+996407f+4a984c5+316423c) **D1 Functions dimension scaffold** : Pydantic `FunctionsPack` schema + `load_functions(lang)` loader + `build_functions_block(lang, level)` Dify consumer + `data/functions/es.yaml` (26 PCIC Funciones A1 + 16 A2 = 42 entries) + `data/functions/en.yaml` (5 A1 + 5 A2 = 10 entries stub) + tests `test_functions_schema` parametrized 6 langs (EN+ES active, IT/DE/JA/RU skip Phase D2). 4 commits granulaires.
- [ ] **DEFERRED Phase D2** : Functions B1+B2+C1+C2 expansion (PCIC Vol B Funciones + CEFR Companion Ch 3 production/interaction full + Threshold/Vantage 1990) ~3-4j
- [ ] **DEFERRED Phase D3** : Mediation dimension NEW 2020 (CEFR Companion Ch 3 mediation scales pp.90-122 = 33p) → `data/mediation/{en,es}.yaml` + loader + schema (différenciateur marché vs Duolingo/Babbel pre-2020) ~3-4j
- [ ] **DEFERRED Phase D4** : Skills-based reorganization (Reception / Production / Interaction / Mediation per niveau) — major design refactor, requires Sinse decision (parallel structure vs rewrite)
- [ ] **DEFERRED Phase D5** : Cultural inventario (PCIC Referentes culturales + Saberes socioculturales + Habilidades interculturales = 3 inventarios)
- [ ] EN flagship full A1-C2 audit Phase 2 (post-EVP/EGP integration)

### Wave 2 IT (~13j Phase 1, P2 mai-juin 2026)

- [ ] **CILS Sillabo acquisition** (stub pending — payant Guerra Edizioni OU Anna's search)
- [ ] CILS 2006/2010 Quaderni A1-A2 + Vedovelli 2013 → `mini_exam/it_A1.yaml` + `mini_exam/it_A2.yaml` + `mini_exam/it_B1.yaml`
- [ ] Bargallo Traguardo CILS B2 (third-party prep) → `mini_exam/it_B2.yaml`
- [ ] CILS C1+C2 Quaderni acquired (#86-87) → methodology reference only (above ADR-013 cap, deferred extraction)
- [ ] Maiden grammar lookup-only (`rules_it.py` edge cases — clitiques doubles, congiuntivo, ne partitive)
- [ ] Pienemann 1998 PT framework → `rules_it.py` priority gates (PT V2 cross-lang)
- [ ] Profilo della Lingua Italiana acquisition (analogue PCIC IT, free `loescher.it`)

### Wave 2 DE (~16j Phase 1, P2 juin-juillet 2026)

- [ ] **Profile Deutsch Ch 3.2 A1-B2** (~67p data structurée) → `curriculum_de.yaml` + `concept_hints/de.yaml` Kannbeschreibungen
- [ ] **Profile Deutsch Ch 3.5 grammatik** → `rules_de.py` Phase 1 grammar coverage
- [ ] **Goethe B1 Übungssatz officiel** (text PDF, 49p, S53 acquired) → `mini_exam/de_B1.yaml`
- [ ] **Mit Erfolg Goethe B2** (third-party Klett, scanned 99p, S53 acquired) → `mini_exam/de_B2.yaml` supplementary (NOT official Modellsatz — note dans header)
- [ ] **Mit Erfolg Telc B2** (third-party Klett, scanned 193p, S53 acquired) → task variety Sprachbausteine cloze format unique
- [ ] **telc B1 Übungstest officiel acquisition** (Sinse manual telc.net, gratuit) — companion B2 manquant
- [ ] **Goethe B2 Modellsatz officiel acquisition** (Sinse manual goethe.de, gratuit) — replacement third-party Mit Erfolg
- [ ] Helbig-Buscha grammar lookup-only (`rules_de.py` Valenztheorie edge cases)

### Wave 3 JP (~28j Phase 1, P3 août-déc 2026)

- [ ] **JFS Guidebook 2022** (⭐⭐ ADR-015) Ch 2.2 (2) speaking rubrics + Reference Materials 3+4 can-dos → `curriculum_jp.yaml` + `rubrics/jp.yaml`
- [ ] JFS pamphlet 2024 EN (6p exec summary companion JFS Guidebook)
- [ ] **Pienemann 2005 Ch 8 Kawaguchi** (⭐⭐ canonical empirical PT-JP) → `rules_jp.py` PT-JP stages stratification
- [ ] Marugoto série A1→B1 (8 vols S52 acquired) → curriculum content per niveau + productive task templates
- [ ] JLPT N4 vol1+2 + N5 vol2 公式 → `mini_exam/jp_N4.yaml` + `mini_exam/jp_N5.yaml` (note: JLPT = N5/N4/N3 not strict A1/A2/B1)
- [ ] Tsutsui N3 mock (third-party) → supplementary item bank
- [ ] Makino dicos JBJ/JIJ/JAJ lookup-only (`rules_jp.py` particles/te-form/keigo edge cases)
- [ ] **JLPT N5 vol1 公式 acquisition** (stub pending — Bonjinsha ¥800 OU Internet Archive search)

### Wave 4 RU (~21j Phase 1, P3 oct+ 2026)

- [x] (S53 acquired ✅) **TORFL Lexical Min A1/A2/B1/B2** (Pushkin Institute, text PDFs 80/116/199/162p) → `concept_hints/ru.yaml` 780/1200/2300/3000 mots seed par niveau
- [ ] Antonova Doroga 1+2 (S52 acquired, OCR'd) → `curriculum_ru.yaml` A1+A2 primary content + tâches productives
- [ ] Bulgakova/Lysenko verb-government glossary + grammar tables (S52 acquired) → `rules_ru.py` companions Antonova
- [ ] **Lazareva TORFL examiner methodology** (⭐ S52 acquired) → `oracle/judges/` rubric direct seed Wave 4 RU — scoring dims `teacher_ru` Tier-1
- [ ] Makova-Uskova Vol.3 Pt1 (B2 ✅ within ADR-013 cap, S53 acquired) → `mini_exam/ru_B2.yaml` Чтение section seed
- [ ] Makova-Uskova Vol.1 + Vol.3 Pt2 (C1 above cap) → lookup-only-deferred
- [ ] Wade Comprehensive RU Grammar lookup-only (`rules_ru.py` aspect/cas/motion edge cases)
- [ ] Zalyalova RKI exercises (S52 acquired, OCR'd) → exercise pattern source
- [ ] **TORFL Grammar Min stub acquisition** (Sinse manual)

### Cross-language activations (post-flagship audit)

- [x] (Session 52, in-use ✅) **Lyster cf-taxonomy** → `cf_classifier.py` Tier 2 BIPED Step 1 (consommé prod via `BIPED_CF_CLASSIFIER_ENABLED` flag)
- [ ] **Lightbown/Spada Ch6 wire-up** (Ch6 yaml extracted S52, ~1j ship) → `pedagogy/biped_step2_generator.py` Tier 2 BIPED Step 2
- [ ] **Hernán Causal Ch 22 Target Trial** (skimmed S53) → Tier 2 BIPED measurement framework — ITT vs per-protocol + DAGs
- [ ] **Bachman-Palmer AUA Framework Ch 2-3** (skimmed S53 ⭐) → bridge AI Act art.50 compliance — `webapp/backend/app/legal/ai_act.py` automated decision justification
- [ ] **Baker IRT + Embretson Ch 10** (skimmed S53 ⭐⭐) → `psychometrics/placement_test.py` + `cat.py` (5-7j module activation — Rasch 1PL + MLE + CAT canonical + DIF cross-language item bias)
- [ ] **Hughes 2020 Ch 17 New tech** (⭐⭐⭐) → digital testing methodology + AI-assisted scoring guidelines (companion Baker/Embretson)
- [ ] **Nation Four Strands** (skimmed S53 ⭐⭐) → Maestro scenarios design audit — currently skewed input/language-focused, missing fluency/output strands
- [ ] **DeKeyser 2007 Practice** (skimmed) → `dosage_block` declarative→procedural→automatized stage mapping
- [ ] Ortega 2009 SLA — secondary companion Lightbown/Spada (skimmed)

### Anti-doc-théâtre check

**Pre-emptive 6-month review window 2026-10-29** :
- Si ≥50% des skimmed books ne sont pas progressed (extracting OR in-use) → signal sur-skim sans extraction trigger
- Triggers Wave 2 IT/DE début (~mai-juin 2026) → extracting CILS + Profile Deutsch + Pienemann Ch 3 + Maiden lookup
- Triggers Wave 3 JP démarrage (~août-déc 2026) → extracting Marugoto + JFS Guidebook + Pienemann 2005 Ch 8
- Triggers Wave 4 RU (~oct+ 2026) → extracting Antonova + Lazareva TORFL + Wade lookup

**Roadmap macro (vault projects/obsidian-migration/roadmap-sinse-2026-04-25.md)** :
- P0 cette semaine : Teacher EN enum + B4 GlitchTip test browser + Restic monthly + DPA OpenAI/Groq
- P1 mai 2026 : DMARC + CSP enforce + Phase 3 fault injection + B5 Paraglide i18n
- P2 mai-juillet : Phase B AcademIA gros morceaux (B2 Bits UI, B3 PWA, B6) + Maestro ES catchup + outreach
- P3 août-déc : formation cybersec aligné + L26 user non-root trigger-based

## OPEN (any AI can take)

### 🚀 P0 — Refactor 2026-H2 Phase A items restants

ADR-001 livré Session 46 (`docs/05-decisions/ADR-001-refactor-complete-2026-H2.md`). **Phase A 7/7 items livrés (Session 47 ferme A5+A6).** Reste cleanup + polish :

- [x] (claude, 2026-04-23, Session 46) **A1 — Auth migration JWT→sessions opaques Redis + CSRF** — module `sessions.py` Redis store, cookie `as_session` HttpOnly + `csrf_token` JS-readable, middleware csrf_protect, /auth/logout + /auth/logout-all-sessions, frontend retrait complet localStorage. Validé sinse end-to-end. Commits `941299b`, `79041e1`, `567b31e`.
- [x] (claude, 2026-04-23, Session 47) **A1-cleanup** — DROP active_sessions, retrait python-jose + JWT keys (.env + .env.sops via SOPS round-trip), retrait TokenResponse/RefreshRequest models, refactor obsolète sprint6 e2e helpers (NotImplementedError), Redis container recréé avec `--appendonly yes` baked in (DBSIZE=17 préservée via volume). Doc a1-redis-aof.md. Commits `4fce526`, `c374be5`.
- [x] (claude, 2026-04-23, Session 47) **A5 — PII scrubber + cross-user isolation + rate-limit per-user + cost runaway** — module `app/security/pii_scrubber.py` (5 patterns regex EMAIL/PHONE FR/IBAN/NIR/CARD Luhn-validated), injection chat_router avant POST Dify ; rate_limit.py étendu `check_user(scope=user)` + appliqué chat-send 100/60s + 3 consolidation 20-30/300s + onboarding 10/300s ; migration `model_usage_daily.user_id` (NULLS NOT DISTINCT) + LiteLLM callback forward kwargs.user + endpoint `/api/admin/cost-runaway-users?window=24h|7d|30d` (top 20 + outlier flag 5×median) ; chat_router conv ownership check (Alice ne peut plus append à conv Bob via UUID guess) ; 26 pytest verts (23 PII + 3 cross-user). Commits `5103490`, `bc11b84`, `d381a72`, `a85563d`.
- [x] (claude, 2026-04-23, Session 47) **A6 — RGPD docs + endpoints DSAR + age attestation** — 4 runbooks compliance (`dpia.md` + `rgpd-registre.md` + `transfert-impact-assessment.md` + `minors-flow-roadmap.md` self-attest CNIL), bannière AIBanner.svelte AI Act art. 50 sur /chat, pages `/legal/ia` + `/legal/mineurs`, endpoints `/api/me/export-data` (13 sections incl. Dify conv via end_users.session_id) + `/api/me/delete-account` (hard delete cascade, retype confirmation), UI `/settings/privacy` (modal 2-step), migration `users.age_attestation_at` + admin CLI 07. Flow consentement parental mineurs **différé Phase B1** (cf. `minors-flow-roadmap.md`). Commits `cf74121`, `5fe775b`.
- [x] (claude, 2026-04-23, Session 47) **A4b polish** — Fernet at-rest TOTP (`TOTP_FERNET_KEY` env in .env + .env.sops, backward-compat plain detection prefix `gAAAAA`, sinse migré 1 row), endpoint POST `/api/security/totp/regenerate-recovery-codes` + UI bouton, WebAuthn/Passkeys scaffolding (table + 4 endpoints stub 501 derrière `WEBAUTHN_ENABLED=false` + UI placeholder). Force-reset 90j documenté TODO post-alpha. Commit `f64ab5d`.
- [x] (claude, 2026-04-23, Session 47) **A5 followup admin card** — composant CostRunawayCard.svelte monté dans /admin (3 stats + tableau top 20 + flag rouge runaway + window 24h/7d/30d). Migration slowapi+Redis reste TODO si trafic multi-worker requis. Commit `f29594f`.
- [ ] **A6 followup Sinse manuel** — signer DPA OpenAI ([platform.openai.com/account/data-processing-addendum](https://platform.openai.com/account/data-processing-addendum)) + Groq ([groq.com/dpa/](https://groq.com/dpa/)). ~~désigner `dsar@` Cloudflare Email Routing~~ ✅ Session 55 (alias actif `dsar@petit-pont.com` → forward `sinseproduction@gmail.com`).

**Manuel à toi (Sinse)** :
- [x] (claude+sinse, 2026-05-01, Session 55) ~~DMARC bump à `p=quarantine`~~ ✅ jalon 2026-05-07 hit. Record `_dmarc.petit-pont.com` patché via API : `v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@petit-pont.com; pct=100; adkim=s; aspf=s`.
- [x] (claude+sinse, 2026-05-01, Session 55) ~~A3 CSP flip enforce~~ ✅ jalon 2026-05-07 hit. 79 violations 24h = 100% manifest-src (Cloudflare Access bloquait PWA assets). Fix root cause Phase 2 (Access bypass app `/manifest.json + /sw.js + favicons`) puis flip `hooks.server.ts:95` Report-Only → enforce + redeploy frontend. Commits `e1fa359` + Access app id `7eaa58d0-c3df-4e73-bd12-3fb2291a904e`.
- [x] (Session 47) ~~Cloudflare Access app config check (Dify wildcard suspect)~~ → résolu via refactor : 3 apps dédiées (dify/academie/n8n) au lieu de la wildcard accidentelle.
- [x] (claude+sinse, 2026-05-01, Session 55) ~~Cloudflare Email Routing setup~~ ✅ enabled + 3 alias actifs (`security@` + `dmarc-reports@` + `dsar@`) → forward `sinseproduction@gmail.com`. SPF auto-rewrite par CF `-all` → `~all` (soft fail requis pour forwarding sans rejet downstream). DKIM CF `cf2024-1._domainkey` ajouté. 3 MX records `route1/2/3.mx.cloudflare.net`.
- [ ] Cloudflare Notifications policies (DDoS + SSL expiring + Page Shield malicious script + Tunnel down) — token CF account a perms maintenant.
- [ ] Restore restic mensuel testé une fois (audit setup actuel `/opt/academie-shared/secrets/restic-passphrase`).
- [ ] (B4 final test) Browser test public dashboard : Ctrl+Shift+R sur academie.petit-pont.com → console `Promise.reject(new Error('test'))` → vérifier event apparaît dans GlitchTip academie-frontend Issues sous 30s. Pipeline déjà validé serveur-side.

### 🎨 Phase B — Fondations visuelles (Session 47+)

- [x] (claude, 2026-04-23, Session 47) **B1 — Tokens OKLCH + state semantics + L2 serif font** — 36 color tokens hex→OKLCH (visuellement identiques, perceptuellement uniformes pour B2 shadcn variants) + 16 state tokens success/warning/danger/info avec variants -bg/-border/-text + Source Serif 4 self-hosted (50KB latin) wired sur ChatBubble pour assistant L2 (en/es/ja/de/it) + sweep top 2 offenders (chat 31 + privacy 27 / 65 occurrences) + doc référentiel `b1-design-tokens.md`. Commits `1be27fa`, `21cff95`, `ee4c9f2`, `7371d8a`.
- [ ] **B2 — Bits UI + shadcn-svelte (~2.5 sem)** — adoption ~18 composants headless (Dialog, Combobox, Menu, Toast, Select, Checkbox, Radio, Tabs, Accordion, Popover, Tooltip, Toggle, Slider, Progress, Avatar, Badge, Card, Separator). Pinning strict versions.
- [ ] **B3 — Images + PWA Workbox (~1 sem)** — `@sveltejs/enhanced-img` AVIF/WebP/srcset + audit `sw.js` hand-written → Vite PWA + Workbox.
- [x] (claude, 2026-04-23, Session 47) **B4 — GlitchTip + bundle budget + dashboard public CF Access** — Stack 3 containers (glitchtip-web v5.0 + glitchtip-worker + redis-glitchtip dédié) + DB glitchtip_db sur postgres-academie + SDK frontend (@sentry/sveltekit 10.49) + backend (sentry-sdk[fastapi] 2.45 + _scrub_pii) + CI bundle-budget.yml + doc b4-glitchtip-observability.md + dashboard public via Cloudflare Tunnel (tunnel ingress + cosmos route + 4 CF Access apps : academie/dify/n8n dédiés + GlitchTip dashboard PIN-protected) + tunnel /api/sentry-tunnel (FastAPI proxy bypass Cosmos CSP `'self'`) + extract sentry_key auth. End-to-end validé live. Commits `8b5f3dd`→`7bdf1b4`. PRs #21→#27.
- [ ] **B5 — Paraglide-JS 2 i18n (~0.5 sem)** — Vite plugin + strings FR + EN fallback + route `/[lang]/...` ou `Accept-Language`.
- [ ] **B6 — Forms + motion + state (~1 sem)** — Superforms v2 runes + Valibot pour QCM/chat + `svelte/transition` respectant `prefers-reduced-motion` + stores legacy → `.svelte.ts` runes lazy.

### ✅ Refactor 2026-H2 Session 46 — items livrés (réf rapide)

Tous commits sur `main` :
- `20a2baf` ADR-001 roadmap 5-6 mois calendaires + 7 décisions tranchées
- `4e7377b`, `1831ec6` A7 + A7a Cloudflare DNS/SSL/HSTS/WAF/Cache + CI Dependabot/security-audit
- `2222cb7`, `ed3b0d4`, `07ce9ef` A3 CSP report-only collecte 2 sem
- `435abcc` A2 Argon2id silent rehash (validé sinse)
- `69aba81`, `90f4e9c`, `50deb82`, `e536615` A4 MFA TOTP backend + UI + sinse enrolled

### ✅ Sessions 39-42 Oracle V1 trajectory — ARCHIVED (all shipped or superseded)

Full trajectory Sessions 39→42 recorded in SESSION_ARCHIVE.md + commit history :
- Session 39 : stabilisation + Phase D cache telemetry + ES three-strikes fix + dogfood simulation (17 commits)
- Session 40 : Oracle V1 alpha shipped (8 commits, 24 scenarios, lint gate, noise_floor + fault injection infra)
- Session 41 : deferred; merged into Session 42 scope
- Session 42 : autonomous package (11 commits, 5 debts + 4 Oracle + 3 pédago)
  - O3 fault injection LiteLLM-bypass gate FAIL (structural 80% false-alarm floor documented)
  - 3 redesign options recorded : Dify-clone retry / **delta gating** (chosen for Session 46) / distributional invariants

Session 45 P1 re-baselined noise floor with gemini-3-1-flash-lite judge (κ=0.84) ; V5 Teacher EN = 22/26 = 85% (gpt-4o-mini prompt-engineering ceiling identified).


### 🎯 P1 — Session 41+ oracle extensions

- [ ] **Oracle V1 → Maestro ES** (Session 41, ~4h) : 15 scénarios ES spécifiques (ser/estar, por/para, subjuntivo, concordancia, "a personal"). Réutilise harness V1. Calibration κ séparée.
- [ ] **Oracle V2 améliorations** (plus tard, après usage réel) :
  - Jury 2-of-3 cross-vendor (Haiku + Gemini Flash + gpt-4.1-mini)
  - Simulated learner LLM pour multi-turn uptake
  - Hallucination factuality judge (grammar rule correctness)
  - CEFR self-calibration judge
  - Ecological audit process (learner panel monthly)
- [ ] **Phase C-deep prompt reorder** : maintenant qu'on a Oracle V1 comme gate, Phase C-deep devient faisable en Session 42+ avec conditions assouplies : (a) Oracle V1 shippé et stable, (b) Oracle run sur full 24 scénarios avant/après → toutes régressions détectées. Plus besoin de 3 users externes (l'Oracle joue ce rôle de validation). Target : cacheable 19% → 75%, gain -25%/user/mois sur chat principal.
- [x] (claude, 2026-04-22, Session 39) **Phase D v2 dashboard monitoring cache** — `/api/admin/cache-stats` + section `/admin` avec 3 metric cards + SVG sparkline + per-model table + window 24h/7j/30j. Commits `53b04f8` (backend) + `207450d` (frontend).
- [ ] **Phase D v3 alerting** : trigger notif si cache hit rate drop > 20% j/j (signal prompt drift). À faire quand trafic suffisant pour signal stable (~quelques jours de peuplement).

### 🌱 P1 — Distribution / outreach (critique strategist, Session 40+)

**Contexte** : à ~1 user actif (Sinse lui-même), toute optimisation stack est polish de forteresse. La vraie inflection = premier user externe. Bloc complet à planifier sous 2 semaines max.

- [ ] **Loom 5-7min asset outreach** : session dogfood narrée, unedited, montre product en action. Peut être produit en Block 2 Session 39 comme byproduct. Sinon bloc 45min dédié.
- [ ] **Landing explainer 1 page** : "what is AcademIA, who is it for, what does it cost, current status". Force positioning clarity. ~1h.
- [ ] **Liste 20 candidats FR-native testeurs EN/ES** : amis, amis d'amis, Reddit r/learnfrench, Discord polyglottes, Polyglot Club, iTalki learners. ~1h.
- [ ] **Outreach envoi 20 messages personnalisés** : target = 3 appels 20min bookés la semaine suivante. ~2h.
- [ ] **3 appels utilisateurs cibles** : observation sans guide, questions ouvertes. Learnings → doctrine ou pivot. ~3h (3×1h).

### 🚨 P0 — Onboarding QCM follow-ups (Session 35+)

**Contexte** : Session 33 livre refonte QCM + hotfix partiel. Session 34 résout le bug onboarding-branch Dify. **Session 35** : checkup approfondi 3-agents → 2 bugs live-détectés et fixés (P0 rubric level mismatch, P1 greeting L1 drift) + politique L1/L2 adaptative livrée (code+doc+tests). Validé live Maestro FR→ES A1.

- [x] (claude, 2026-04-20, Session 34) **Fix onboarding-branch Dify wiring** — wire via `code_profil_check` (seul node commun aux 2 branches if_profil) + prepend `<learner_profile>` + `QCM_OVERRIDE_v1` à la FIN du system prompt llm_onboarding. Scripts `scripts/sprint5/13_wire_onboarding_branch.py` + `14_strengthen_llm_onboarding_override.py`.
- [x] (claude, 2026-04-20, Session 34) **Conv stuck Maestro ES Sinse** — wipe complet DB (conv + msgs + user_session + learner_profile).
- [x] (claude, 2026-04-21, Session 35) **Fix P0 rubric level mismatch** — `chat_router.py` override `niveau` via `learner_profiles.domain_level.cefr_placement` (priorité QCM sur legacy `profils_eleves.niveau_global`). Validé live : RUBRIC A1 injecté correctement.
- [x] (claude, 2026-04-21, Session 35) **Fix P1 Teacher greeting L1 drift** — script `15_strengthen_qcm_override_l2_example.py` : 2 few-shots L2 explicites avant `=== FIN QCM_OVERRIDE_v1 ===`. Teacher+Maestro draft+published. Validé live.
- [x] (claude, 2026-04-21, Session 35) **Politique L1/L2 adaptative** — matrice level×typological-distance×FLA (9 cells + modulation FLA high). Modules `pedagogy/typological_distance.py` + `scaffolding_policy.py` + 19 tests + wiring `teacher_prompt` + `chat_router` via `learner_profile_summary` append (MVP). Doc `docs/01-pedagogy/l1-l2-scaffolding-policy.md` (10 sections, citations Butzkamm/Cook/Macaro/Ringbom/CEFR 2020/ACTFL/PCIC). Kill switch `SCAFFOLDING_BLOCK_ENABLED`. Validé live FR→ES A1.
- [ ] **Phase 2 scaffolding** — splitter `scaffolding_block` en input Dify Start dédié (script 16, 24 edits workflow) + few-shots sandwich YAML par distance + monitoring `user_sessions.scaffolding_cell`. Architecture propre mais non-bloquant (MVP fonctionne).
- [x] (claude, 2026-04-23, Session 42 O2) **Oracle V1 admin dashboard** — new `oracle_run_log` table + harness post-run persist (best-effort) + `/api/admin/oracle-runs` endpoint + dashboard section (3 metric cards + by_dim table color-coded + recent_runs details). 104 rows persisted on lint run.
- [x] (claude, 2026-04-23, Session 42 O3) **Oracle fault injection run Teacher EN** — 5 faults × 26 scenarios + clean baseline via LiteLLM-bypass. GATE ❌ FAIL as expected (clean false_alarm 80.8%, mean detection 76.9%). Confirms Session 41 finding : LiteLLM-bypass methodology has structural false-positive floor. Detection rates (69-85%) exceed baseline by 5-17 pp — faults detectable above noise but gate calibrated for a true Dify-clone path. Artifacts `docs/oracle/session42_fault_injection_teacher_en.{md,json}`. Commit `127eb8d` (local, push blocked by main protection). Three Session 43+ options documented : Dify clone retry, delta gating, distributional invariants.
- [x] (claude, 2026-04-22, Session 43 O4) **Oracle V1 noise floor V2 Teacher EN** — ran noise_floor.py --runs 2 --mode full. Post-O1 call-path parity fix : semantic_fidelity_pairwise 33% → 7.7% (4× better), cf_move_set_valid_partial 12.5% → 7.7%, register_cefr_alignment 20.8% → 19.2%. recast_saliency stable 0%. Hypothesis validated. Commit `1419ded`.
- [x] (claude, 2026-04-22, Session 45 P1) **Oracle noise floor V2 baseline** — gemini-3-1-flash-lite judge (κ=0.84 inter-rater agreement vs 7-judge majority from κ calibration). cf_move_set_valid FPR 0.154 → 0.0 (16× judge consistency improvement). Baseline persisted in `scripts/oracle/config.yaml`. Made the underlying Teacher EN bug visible : 6 A1/A2 scenarios consistently failing forbidden CF moves (was masked by gpt-4o-mini judge κ=0.33). Doc `docs/oracle/session45_noise_floor_v2_post_judge_migration.md`.
- [x] (claude, 2026-04-22, Session 45 P2) **TIER_TO_FEEDBACK_BY_LEVEL CEFR-gated mapping** — refactored `tier_to_feedback_type()` to accept `level` arg ; A1 T3 collapses to `implicit_recast` (was `elicitation` then `metalinguistic` via diversity, both forbidden at A1). A2/B1 keep `elicitation` default with diversity. C1/C2 default `metalinguistic`. Both callers updated. 26 pytest parametric tests lock down the per-level mapping. Commit `d36c1bb`.
- [x] (claude, 2026-04-22, Session 45 P2d) **B1 rubric HARD BAN + 3 anti-pattern fewshots + L2_ratio band relaxation** — extended A1/A2 treatment to B1 (gpt-4o-mini was defaulting to explicit_correction at B1 too). Added 4 anti-pattern entries (3 B1 + 1 A2 article-injection variant). Relaxed A1 `l2_ratio_band: [0.7, 0.98] → [0.7, 1.0]` on 7 scenarios (the 0.98 was a false positive — forced FR even when no L1-needing item). V5 measurement : 22/26 = 85% pass rate. Commit `5d7b246`.
- [x] (claude, 2026-04-22, Session 45 P4.5) **Admin /admin Oracle judge budget section** — JudgeBudgetBar.svelte component (stacked SVG bar over 3-tier Gemini chain : 2.5 Flash + 3 Flash + 3.1 Flash Lite, 540 RPD cumulated). New `/api/admin/judge-budget` endpoint queries `litellm_cache_stats` per-model. Active tier badge inferred from first-tier-with-budget. CLI preflight command surfaced in footer. Commit `feb4eb9`.
- [x] (claude, 2026-04-22, Session 45 P2g+h+i NEGATIVE) **Pink-elephant priming negative finding** — applied 3 prompt-engineering interventions (P2g 4 new anti-patterns, P2h positive reframing, P2i FINAL SELF-CHECK enumerating banned phrases). V6 measured 5/26 (catastrophic regression from V5's 22/26). Reverted P2i + V7 = 16/26 (still −6 vs V5). Rolled back all 3 to V5 (commit `5d7b246`). Root cause : listing banned phrases verbatim in prompt — even inside "if you catch yourself writing X" frames — primes the LLM to produce them (Jang et al. 2023 negation studies). Doc `docs/oracle/session45_p2ghi_negative_finding.md`. **Lesson for next try : structured output enum constraint (option #1, untried) ; never repeat banned tokens >2× total ; ablate one change at a time.** Commit `656ae09`.
- [ ] **Session 46 — try option #1 structured output enum constraint** for Teacher EN compliance (the untried high-ROI technique from research). Add `feedback_type_intended` enum to JSON schema that excludes `explicit_correction`. LLM must declare type BEFORE writing feedback. ~30 min code + V8.
- [ ] **Session 46 — Phase 3 fault injection redesign (delta gating)** per Session 42 O3 findings — clean baseline + faulted run per scenario, gate on `mean(delta) ≥ 0.4 AND false_positive < 0.20` instead of absolute thresholds. ~2h.
- [ ] **Session 46 — Phase 4 gate-strict flip** : `RUN_RECENT_BATTERY.sh` block 8 `lint strict` → `lint + smoke strict`. Requires P3 done first.
- [x] (claude, 2026-04-22, Session 43 P5) **Onboarding telemetry drop-off funnel** — new table `onboarding_telemetry_events` (session_id, event, step_id/order) + POST `/api/telemetry/onboarding-event` un-authed (sendBeacon-friendly) + GET `/api/admin/onboarding-funnel` aggregating per-session max step + completion flag + conversion rates + Svelte OnboardingModal instrumented with UUIDv4 sessionId persisted in localStorage + step_enter on each step + complete on submit + abort via navigator.sendBeacon on beforeunload + admin dashboard section (4 stats + step table + recent aborts). 5 pytest tests green. Dogfood-validated end-to-end by Sinse: 1 session with abort at step 5 + reprise same session_id + complete = 11 events captured, funnel shows 1/1/1 (started/completed/aborted). Commits `72e2fef`, `799d0ee`.
- [x] (claude, 2026-04-22, Session 43) **Fix learner_profile_summary 2000 char limit** — Dify Start var `learner_profile_summary.max_length` bumped 2000 → 10000 (matching `learner_profile_json`). Root cause : Session 35 MVP appends `scaffolding_block` into summary field to reach both llm_onboarding and llm_session, but with Sessions 38-42 additions (CONCEPTS PRIORITAIRES + L1/L2 MIX + POST-QCM WELCOME) the concat overflowed. Symptom : new users got "Erreur de connexion" on first chat turn post-onboarding. Idempotent patch script + pre-patch backup in `/tmp/dify_backups/`. Commit `6175689`.
- [x] (claude, 2026-04-22, Session 43) **Smoke-test n8n fail rate 13% false alarm** — smoke-test excluded 3 battery-hit workflows (dify-diagnostic + dify-snapshot + dify-exam-scoring) from the 48h error count. They return HTTP 200 immediately then fail downstream on the synthetic test payload, polluting the window with self-generated errors. Filter applied in `/root/sinse-workspace/tools/smoke-test`. Now 0.0%. Commit `7f96f0a` (sinse-workspace repo).
- [x] (claude, 2026-04-22, Session 44) **Admin dashboard redesign — ops pattern** — hero Model Budget waterfall SVG bar (3 tiers stacked, active ring + ETA) + regression row 2-col (Consolidation + Oracle, each with own EN/ES selector + 24h/7d/30d window) + Onboarding funnel full-width + collapsible Prompt caching diagnostic + Users table moved to `/admin/users` route. Removed misleading global domain selector. 3-tier waterfall backend (gpt-4o-mini → groq-standard → groq-snapshot), new tables `model_usage_daily` + `model_switch_log`, `/internal/model-usage` relay populated by LiteLLM callback, `/api/admin/model-budgets` endpoint with per-tier payload + ETA computation. 5 pytest tests. Commits `726b7c0`, `614257d`.
- [x] (claude, 2026-04-22, Session 44 fix) **Chain of fixes post-ship** — (a) `_reconcile_current_dify_model` reads actual workflow graph (survives rebuild), (b) `_teacher_workflow_ids` / `_all_agent_workflow_ids` read `apps.workflow_id` dynamically (was hardcoded to c52a451f which a 04-20 republish made stale), (c) admin endpoint uses `get_gpt4o_usage()` MAX(local, litellm, openai) for gpt-4o-mini tier, (d) groq callback normalizes provider model → model_group (LiteLLM passes raw provider name not alias), (e) safety margin 10% → 2% now that reconcile is authoritative, (f) daily complimentary cap 1.5M → 2.5M (verified real tier 1 limit at console.openai.com/settings/organization/limits) via `OPENAI_COMPLIMENTARY_TPD` env var. Commits `b0e537a`, `0a59e2b`, `5ec8f78`, `74ea7e0`, `bc459ac`.
- [x] (claude, 2026-04-22, Session 44 V2) **Header-based rate-limit tracker** — LiteLLM callback reads `response_obj._response_headers` (x-ratelimit-*), normalizes model aliases, parses reset values in LiteLLM format (`8h32m15s` / `6m0s` / `500ms` / int), POSTs to new `/internal/rate-limit-snapshot` relay, UPSERT in `model_rate_snapshot` table (1 row per model, last-write-wins). `/api/admin/model-budgets` returns `rate_snapshot` field per tier. ModelBudgetBar renders `↻ 8h32m` countdown under each tier card. Provider-attested live counters replacing 15-min Usage-API reconcile latency. Smoke-tested with Dify Teacher call : gpt-4o-mini snapshot populated within ~1s of HTTP response. Commit `a3debe8`.
- [x] (claude, 2026-04-22, Session 44) **Multi-agent tier-chain switch** — `_switch_dify_model` was Teacher-only (hardcoded `TEACHER_APP_ID`) → Maestro kept pounding gpt-4o-mini while Teacher cascaded to groq. `AgentDef` gains `dify_app_id` field populated for Teacher (39565197) + Maestro (47b0529c) + fail-loud assert in `active_agents()`. `_teacher_workflow_ids` → `_all_agent_workflow_ids` iterates every active agent (pub+draft). Verified live : switch patches 4 workflow IDs (Teacher + Maestro × pub/draft). Commit `73812c2`.
- [x] (claude, 2026-04-23, Session 42 P3) **Admin consolidation-events analytics** — `/api/admin/consolidation-events` endpoint (summary + by_decision + by_user + by_trigger) + /admin dashboard section (3 metric cards + decision breakdown table). Mirror cache-stats pattern. 0 events dev → rendu "Aucune donnée"\n- [x] (claude, 2026-04-23, Session 42 P2) **Dormancy regression watch** — pure helper `should_activate_dormancy_watch()` + chat_router activation hook + clear logic on resolution (both paths POST /decide + mini-exam submit). Session 36 avait livré columns + trigger skeleton, activation call site manquait. 9 tests paramétriques verts. Fires quand validé ≥30j + silence ≥7j → watch actif 5 tours.
- [x] (claude, 2026-04-21, Session 37) **QCM dettes d'exploitation — 3 fixes livrés** :
  - [x] **`probe_answer` reinjection** : `_render_nl_summary` ajoute maintenant un bloc "Probe diagnostique (test B1+)" avec réponse apprenant·e (cap 150 chars), score /3, regex_hit, + warning Dunning-Kruger si `probe_flag`. Le tuteur voit les erreurs probe dès turn 1.
  - [x] **`fla_items` granularité** : (a) NL summary surface les 3 items individuels (speaking/mockery/freeze 1–5) en plus de l'agrégat ; (b) `scaffolding_policy.resolve_policy` accepte `fla_items_raw` kwarg et dérive 3 flags pédago : `prefer_written_first` (fla_a≥4), `no_explicit_correction` (fla_b≥4), `provide_chunks_ahead` (fla_c≥4) ; (c) `build_scaffolding_block` rend ces flags comme directives concrètes au tuteur ("Peur corrections publiques → uniquement recasts implicites…"). Wire-through via `PromptContext` + `chat_router`.
  - [x] **Unification scaffolding** : `_compute_tutor_hints` dict local (Session 35 heuristique self_efficacy-only) **supprimé**, remplacé par appel unique `scaffolding_policy.resolve_policy(cefr, distance, fla, self_efficacy, autonomy_pref, fla_items_raw)`. `PolicyRow` gagne champ `scaffolding_intensity` dérivé de la même POLICY_MATRIX que `scaffolding_block`. Shift ±1 intensity : self_eff≤2 → +1, self_eff≥4 + autonomy=autonomous → -1. Single source of truth. 35 tests scaffolding + 18 tests onboarding = 53 tests verts.
- [x] (claude, 2026-04-21, Session 36) **Discussion cadrage QCM ↔ chatflow + MVP consolidation CEFR bienveillante** : 8 décisions produit arrêtées (N=8 turns ou 20 err, mini-exam 8 items, anti-whiplash ±1, 5 états `niveau_status`). Migration schema + module `consolidation.py` (29 tests) + router API + chat_router hook + 3 Svelte components + 4 scripts Dify (observed_level + silence bilan + route QCM→llm_session). Doc `docs/01-pedagogy/cefr-consolidation-policy.md`. Validé live end-to-end.
- [x] (claude, 2026-04-21, Session 37) **E2E test suite consolidation (Option C mixte)** : `scripts/sprint6/05_e2e_consolidation_test.py` + `_e2e_helpers.py` + mini-exam banks B2 EN/ES. **8/8 scénarios seeded verts** ({teacher,maestro}×{A1,A2,B1,B2}) couvrant auto_validate match, mini-exam pass/fail, anti-whiplash clamp ±1. Report `/tmp/consolidation_e2e_final.json`. **Finding Partie A organique** : Maestro émet `observed_level=""` systématiquement (10/10 messages testés) → trigger organique ne peut fire sans prompt tuning. Session 36 avait masqué ça via seed manuel. → nouveau TODO P1 ci-dessous.
- [x] (claude, 2026-04-21, Session 37) **P1 — Maestro prompt tuning `observed_level` emission** : script `06_strengthen_observed_level_v2.py` remplace OBSERVED_LEVEL_v1 par v2 (emission OBLIGATOIRE dès turn 3, 5 few-shots concrets A1→C1, pas d'easy-out ""). Patch teacher_prompt.py OUTPUT_SCHEMA_BLOCK (template `"A2"` vs `""`). Appliqué Teacher+Maestro draft+published (6 nodes × 2 apps). **Validé live** : 10/10 messages organiques émettent désormais CEFR concret (vs 0/10 avant). Trigger consolidation fire organiquement à turn 8. Pipeline end-to-end fonctionnel sans seed manuel.
- [x] (claude, 2026-04-21, Session 37) **Consolidation UX trio** (dogfooding findings Sinse) : (1) post-QCM welcome FR→L2 turn 1 pour A1/A2 via `build_scaffolding_block` extension ; (2) `msg_validation_after_failed_exam` distinct du match path (plus de "tes auto-évaluations étaient justes" sur le fail branch) ; (3) bulle système persistante dans le thread via `consolidation_events.notes` + nouveau endpoint `GET /events/{domain}` + render `system_consolidation` role dans ChatBubble (5 templates FR, architecture L1-indexed `_BUBBLE_TEMPLATES_BY_L1` prête Wave 2+). Backfill Sinse's pre-S37 event. 50 tests verts + 8/8 E2E seeded + smoke 14/14.
- [x] (claude, 2026-04-21, Session 37) **Priority concepts feedback loop + n8n dify-snapshot fix** : (A) nouveau helper `academie_core/pedagogy/priority_loop.py` avec formule Ebbinghaus `priority = weight_norm × (1+sqrt(days/7)) × deficit` → top-3 concepts per turn ; (B) `build_priority_concepts_block` + `PromptContext.priority_concepts` + MVP pipe via scaffolding_block, kill switch `PRIORITY_CONCEPTS_ENABLED=false` par défaut ; (C) `scripts/sprint6/08_refactor_dify_workflows_to_public_api.py` swap console API → public API pour `dify-snapshot` (API console cassée 401 depuis 5j), `cron_snapshot_safety.py` envoie désormais `dify_user_id` + `dify_app_key` per-domain (Teacher/Maestro dispatch) ; (D) validé live : scores_confiance ES repopulé (10 concepts A1 score=100 après snapshot), 17 tests priority_loop verts + 8/8 E2E seeded + smoke 14/14. Ferme la boucle collecte→scoring→prioritisation.
- [x] (claude, 2026-04-22, Session 38) **Refactor `dify-diagnostic` + `dify-exam-scoring` vers Dify public API** — script `scripts/sprint6/09_refactor_diagnostic_exam_to_public_api.py`. Zero modif Dify-side + zero n8n-container restart : résolution du `dify_app_key` en n8n via PG lookup sur `api_tokens` dispatché par `domain`. Nouveau node "Resolve Dify App Key" inséré entre Parse Body et Fetch. Patché workflow_entity + workflow_history (Session 27 gotcha). Validé live : diagnostic retourne profil JSON complet (status=success), exam-scoring passe toutes les étapes HTTP. Commit `ae00b35`.
- [x] (claude, 2026-04-22, Session 38) **Activer `PRIORITY_CONCEPTS_ENABLED=true`** — flip `/opt/academie/webapp/.env` + rebuild academie-api. Env chargé ok, module importable, batterie 7/7 verte. Loop Ebbinghaus désormais active : top-3 concepts injectés chaque tour dans `scaffolding_block`.
- [ ] **Dogfood Teacher EN end-to-end** (15min, Sinse drive browser) : guide ready → `docs/dogfood/teacher-en-setup-2026-04-22.md` (Session 39 commit `472106b`). 5-check checklist + diagnostic commands. Findings commit post-session.
- [ ] **Étendre `_BUBBLE_TEMPLATES_BY_L1` pour EN/IT/DE/JA/RU** (Wave 2+) : ajouter 5 templates traduits par L1 quand non-FR learners apparaissent. Architecture déjà en place, dispatch + FR fallback opérationnels.
- [ ] **Phase D Wave 1 ES battery validation** — run `scripts/sprint3/eval_live_battery.py --lang es` post-fix onboarding-branch Session 34. Target pass rate ≥ 95%.
- [ ] **Re-mesure CDST** J+30 / J+90 (Hiver-Al-Hoorie 2019) — ajouter endpoint `/api/learner-profile/{domain}/remeasure`.
- [x] (claude, 2026-04-23, Session 42 P4) **Probe LLM-as-judge fallback** — nouveau `webapp/backend/app/llm_judge.py` (factor from consolidation_router) avec `judge_passfail` + `judge_probe_score(0-3)`. onboarding POST handler appelle fallback après regex miss si overlay `probe.fallback_judge.enabled=true`. Validé live : perfect answer → 3, off-target → 0. Note : model `gpt-4.1-mini` pas dans LiteLLM config, remplacé par `gpt-4o-mini`.
- [ ] **Telemetry onboarding** — drop-off mid-QCM + durée médiane réelle via localStorage timestamps → seuils runbook J+7.
- [ ] **Cleanup legacy Phase 1 FR** dans prompts Dify `llm_onboarding` une fois QCM_OVERRIDE_v1 + 2 semaines stable.
- [ ] **Obsidian vault meta** — differed Session 33 : pointer `/opt/academie/docs/` + `/root/sinse-workspace/projects/academie-ia/` sans restructure (5 min install). À décider.

### 🚨 P1 — Multi-lang plan d'action (Session 34 audit, exec Session 35+)

**Contexte** : audit 3 agents Explore (frontend/backend/Dify+n8n+data) → `docs/00-project/multilang-action-plan-2026-04-20.md`. 3 P0 visibles déjà fixés Session 34 (profile Teacher hardcoded, stats/concepts onMount, welcome langGenitive). Reste Phase A backend + Phase B hardening.

**Phase A — P0 — DONE Session 37** :
- [x] (claude, 2026-04-21, Session 37) `admin_router.reset_profile()` — param `?domain=en` (query string) + 6 tables per-domain scopées (`profils_eleves`, `error_log`, `snapshots_session`, `learner_profiles`, `consolidation_events`, `spaced_retrieval_queue`). Tables user-global (xp_log, streaks, user_sessions) intactes quand domain spécifié, wipées en global reset. Frontend admin page : `<select>` avec agents disponibles + option "Tous". Toast précise le scope. Intégration test `scripts/sprint6/tests/test_admin_reset_scoping.py` 3/3 verts.
- [x] (claude, 2026-04-21, Session 37) `error_analysis_router:81` — `detect_errors(text, lang=req.domain)` câblé. Validé live : chat ES émet `PREP:POR_PARA` sur "gracias para tu ayuda", EN n'émet rien (correct).
- [x] (claude, 2026-04-21, Session 37) `curriculum_en.yaml` — créé avec schema identique à es.yaml : 53 concepts A1→C2, 33 groupes fonctionnels, weights en minutes. Source : `rubrics/en.yaml` target structures + `concept_hints/en.yaml` 20 keys + `scripts/inject_curriculum_anglais.py`. 13 tests parity parametrés verts (en+es × A1-C2).
- [x] (claude, 2026-04-21, Session 37) **`inject_curriculum.py` YAML-driven** : nouveau script `scripts/inject_curriculum.py --domain X [--dry-run] [--force]`, remplace le legacy hardcoded `inject_curriculum_anglais.py`. Lit `data/curriculum_{domain}.yaml`, UPSERT (domain, niveau) sur les 4 colonnes normalisées (description, concept_keys, concept_weights, concept_groups), laisse `points_cles` legacy intact. EN guard `--force` pour éviter régression drift. **ES injectée** : 6 rows A1-C2, 51 concepts. `/stats/concepts?domain=es` désormais peuplé. 12 tests unitaires verts. Legacy script marqué DEPRECATED avec header.
- [ ] **P2 — Sync `curriculum_en.yaml` avec DB existante** : la DB EN a 98 concept_keys (après Sprint 2-3 + inject_concept_keys.py), mon YAML Session 37 n'a que 53. Décision : extraire DB → enrichir YAML → re-inject `--force`. 1-2h curation humaine.
- [ ] **P3 — Migration `points_cles` legacy** : le dict nested Python dans `inject_curriculum_anglais.py` contient des données (grammaire/vocabulaire/phonologie/competences/erreurs_communes) non-mappées vers le schéma normalisé. **Session 42 D1 audit** : DROP COLUMN `points_cles` **NOT SAFE** — `dify-profil-get` n8n workflow (ID `8NnhEQWCSr0octMS`) consomme encore cette colonne via `SELECT c.points_cles AS curriculum`. Les 6 rows EN ont 3.8-5.1K JSON chacune. Prérequis avant DROP : (a) identifier ce que Dify fait avec cette data `curriculum`, (b) migrer consumers vers `concept_keys/weights/groups` normalisés, (c) alors DROP. Non-bloquant aujourd'hui.
- [x] (claude, 2026-04-21, Session 37) Stubs `fr_to_{it,de,ja,ru}.yaml` — 4 fichiers, 4-5 patterns chacun, markers `STATUS: STUB Wave N`. IT (essere/avere, contractions, false friends, clitiques), DE (cas accus/datif, genre articulaire, V-final), JA (particules wa/ga, SOV, keigo, no articles), RU (6 cas, aspect perfectif/imperfectif). 12 tests parametrés verts.

**Phase B — hardening (~12h)** :
- [ ] **P1 — n8n `dify-diagnostic` + `dify-snapshot` cassés 401** (diagnostiqué Session 37 2026-04-21) : 100% fail depuis ~5 jours. HTTP calls vers `http://dify-api:5001/console/api/apps/...` sans credential (n8n a zéro creds HTTP). Root cause : durcissement Dify auth sur endpoint console. Impact = perte télémétrie snapshot + diagnostic offline (error_log alimenté aussi par rules live → dégradé, pas bloquant). Fix possible : (a) regen session token Dify admin + créer credential n8n, (b) refacto les 2 workflows pour utiliser API publique Dify avec `DIFY_KEY_TEACHER` env var déjà disponible. Option (b) = plus pérenne. À trancher avec l'item ci-dessous (ajout param domain).
- [x] (claude, 2026-04-23, Session 42 D4) **n8n workflows `domain` param** — 3/4 already refactored (Sessions 37-38 : dify-snapshot `08_`, dify-diagnostic + dify-exam-scoring `09_`). **Investigation Session 42** : `dify-exam-persist` has NO Dify API call — its graph is Webhook → Build SQL → SQL Update → Respond (writes local n8n-owned DB only). No refactor needed ; item was based on incorrect 4-workflow symmetry assumption. Closed as no-op.
- [x] (claude, 2026-04-23, Session 42) **Consolidation env vars AVAILABLE_AGENTS CSV** — new `agents_config.py` central registry + `GET /api/agents` endpoint + chat_router.py refactored (removed 5 `ENABLE_MAESTRO` gates, derive DIFY_APP_KEYS from active agents). Backward-compat : ENABLE_* fallback preserved.
- [x] (claude, 2026-04-23, Session 42 D3) **Validation domain centralisée** — nouveau `webapp/backend/app/domain_utils.py` avec `validate_domain_format()` et `validate_active_domain()`. Applied à `get_profile` + `get_my_error_profile` (onboarding already had it, now imports from helper). Unit-tested direct : 'ZZ9' → 422, 'it' (not active) → 422 with list, 'en' → OK.
- [ ] YAML schemas JSON + validator `scripts/data/validate_yamls.py --all-langs`.
- [x] (claude, 2026-04-23, Session 42 D5) **Extension `clone_app.py`** : `apply_prompts_override()` default AST-scoped (parse graph → walk nodes → mutate `prompt_template[*].text` uniquement) ; legacy raw string-replace via `--no-scoped-overrides`. Nouveau `--validate-data-pack LANG` pre-flight via pydantic schemas (curriculum + rubrics + fewshots). `--prompts-file` pas ajouté (redondant avec `--prompts-override` existant). Validé live : `--validate-data-pack en` passe ✓.

### 🚀 P1 — Wave 1 ES Maestro — Phase D + E (ex P0 Session 32, partially superseded by QCM refonte)

**Contexte** : Wave 1 Phases A+B+C livrées Session 32. Session 33 QCM refonte résout les 3 bugs structurellement pour users retournants ; nouveaux users toujours impactés tant que onboarding-branch Dify pas wirée (P0 ci-dessus).

**🐛 Bugs Session 32 — statut post-QCM refonte Session 33** :
- [x] ~~Bug 2 — "ok" loop~~ : résolu structurellement pour users retournants (flow `llm_session`). Pour nouveaux users, attend fix onboarding-branch.
- [x] ~~Bug 3 — bilan sans CEFR~~ : résolu par `cefr_placement` dans `derived_tutor_hints` + injection NL summary.
- [x] ~~Bug 1 — language-mixing FR/ES~~ : résolu par collecte QCM FR déclarative + LLM démarre 100% en L2 post-QCM (pour flows wirés).

- [ ] **Phase D — Battery validation ES** (1-2h) : run `python3 /opt/academie/scripts/sprint3/eval_live_battery.py --lang es` sur 6 personas × 10 turns (A1-C2). Target pass rate ≥ 95%. Les bugs 2/3 ci-dessus bloquent probablement déjà la battery.
- [ ] **Phase E — Alpha monitoring** (passive ~1 semaine calendaire) : POST bugs fix, inviter 2-3 FR-native learners, monitor `error_log` ES populating, collecte feedback.
- [ ] Vérifier conv_vars préservés lors de futurs publish via admin API (gotcha Session 32).
- [ ] Si style values (direct/encourageant/doux/humour) ne fonctionnent pas en ES, revert à FR literals.

### P2 — Security follow-ups (post-Session 31 + quickwins 2026-04-20)

Rotations complètes + filter-repo terminé Session 31 (ADR-012). Quickwins exécutés 2026-04-20 :

- [x] (claude, 2026-04-20) **Pre-commit gitleaks hook** — hook legacy `.git/hooks/pre-commit` déjà en place Session 14. Ajout `.githooks/pre-commit` trackable en git + `git config core.hooksPath .githooks` → survie aux clones frais. Testé E2E commit Phase 2 bloque les leaks.
- [x] (claude, 2026-04-20) **Durcir `pg_hba.conf`** — `trust 127.0.0.1/32` + `::1/128` → `scram-sha-256`. Socket local reste trust (pg-backup via docker exec). Backup `/mnt/cosmos-data/postgres/pg_hba.conf.bak-2026-04-20`. Reload non-disruptif via `pg_reload_conf()`.
- [x] (claude, 2026-04-20) **Fix Dify "Détection profil" short-branch** — 12 outputs défaut ajoutés (`exam_resume_active`, `exam_resume_mode`, `exam_resume_question_num`, `exam_resume_responses`, `exam_resume_module_{index,total,name,concepts}`, `exam_resume_total_questions`, `exam_resume_modules_json`, `exam_scoring_recovered`, `error_exam_eligible`) via admin console API draft patch + publish UI. Published workflow `006cba2d` 2026-04-20 10:21:44.

Restants :
- [ ] **Rotation POSTGRES_PASSWORD superuser** — **ELIGIBLE: 2026-07-22 (trimestriel)** ou immédiat si signal de fuite. Valeur `26051993++Sinse` en clair dans `/mnt/cosmos-data/cosmos-config/backup.cosmos-compose.json` (lisible par user `sinse`, non commité).
- [ ] **Cleanup backups sops** `/tmp/*.bak-2*` — **ELIGIBLE: 2026-04-27**. 9 fichiers : `rm -f /tmp/*.bak-2*`.
- [ ] **Cleanup bundle** `/tmp/academie-pre-filter-backup-*.bundle` — **ELIGIBLE: 2026-04-27**. Restauration DR Phase 3 : `rm -f /tmp/academie-pre-filter-backup-*.bundle`.



### P1 — J-1 SOPS fondation (DONE Session 18)
- [x] (claude, 2026-04-15) sops 3.12.2 + age 1.2.1 installés ; keypair age générée + clé privée out-of-repo chmod 600 + password manager Sinse
- [x] (claude, 2026-04-15) `.sops.yaml` racine + `webapp/.env.sops` dotenv per-var + `webapp/decrypt-secrets.sh` + runbook `rotate-secrets-sops.md` (DR + rotation + anti-patterns)
- [x] (claude, 2026-04-15) `/opt/litellm/config.yaml` → `litellm/config.yaml.sops` (yaml per-value, E2E validé)
- [x] (claude, 2026-04-15) 9 fichiers `/opt/academie-shared/secrets/*` → `secrets/shared.yaml.sops` + `decrypt-shared.sh`
- [x] (claude, 2026-04-15) Test rotation TEST_SECRET lifecycle complet validé
- [x] (claude, 2026-04-15) cosmos-server `AutoUpdate=false` (L1 hardening, supply-chain vector coupé)

### P2 — Cosmos hardening L2/L3 + 1.b (DONE Session 18 ter)
- [x] (claude, 2026-04-15) Pin `cosmos-server` image au digest `sha256:b7faf38ccabd68e0fab4935f03a6126d19e18801a2e534d22bd14c5dec82827e`
- [x] (claude, 2026-04-15) Virer le bind `/var/run/dbus/system_bus_socket` (contrôle systemd inutile)
- [x] (claude, 2026-04-15) `/:/mnt/host` → `:ro` (empêche modif filesystem via cosmos)
- [x] (claude, 2026-04-15) Drop `privileged: true` + `cap_add: NET_ADMIN` (préemptif Constellation)
- [x] (claude, 2026-04-15) Bug bonus : `--hostname cosmos-server` explicite obligatoire (sinon cosmos isInsideContainer check fail → nouveau config vide créé → routes cassées) + `--cgroupns host` par sécurité

### P3 — Cosmos backlog pré-SaaS public
- [x] (claude, 2026-04-16) L4 : `tecnativa/docker-socket-proxy:0.3.0` interposé entre cosmos-server et `/var/run/docker.sock` (cf. [ADR-010](docs/05-decisions/ADR-010-cosmos-L4-docker-socket-proxy.md)). Proxy bloque `/build`, `/commit`, `/services`, `/plugins`, `/secrets`, `/configs` + start d'exec instances (`/exec/{id}/start` → 403). Limitation documentée : `POST /containers/{id}/exec` passe mais l'instance créée est dormant (start bloqué). Rollback script `/opt/academie-shared/secrets/cosmos-pre-L4-rollback.sh` keep 7j jusqu'à 2026-04-23. Smoke deep 21/21 ALL CLEAR, cosmos routes répondent (logs OK).
- [ ] Sinse : valider cosmos.petit-pont.com UI fonctionne (list containers, logs, restart manuel)
- [ ] L5 : remplacer cosmos reverse proxy par traefik ou caddy (refactor DNS + OIDC, ~1-2j) — L4 reste protection partielle en attendant

### P1 — Sprint 3 Teacher Lyster (Session 21 — Phases 0-3 ✅, Phase 4 partial)
- [x] (claude, 2026-04-15) Phase 0a — `sprint3_baseline_prompt.md` (extraction verbatim 4 prompts Dify)
- [x] (claude, 2026-04-15) Phase 0b — `sprint3_design.md` (591 lignes blueprint Lyster + dosage + anti-drift + JSON schema)
- [x] (claude, 2026-04-15) Phase 1 — `sprint3_fewshots.md` (24 examples handcraft × 6 levels)
- [x] (claude, 2026-04-15) Phase 2 — `teacher_prompt.py` (helpers complets) + 63 unit tests + `PROMPT_SESSION_V2` template
- [x] (claude, 2026-04-15) Phase 3 — `eval_personas.py` 4 personas × 10 turns offline LiteLLM, 93.9% pass rate baseline
- [x] (claude, 2026-04-16) Phase 4 partial — script refactor (`if __name__` + CLI flags `--target` + `--use-v2`), chat_router wiring (build_dynamic_sections + 8 dify_inputs), draft deploy V2. **Live test V2 a hangé Dify** → rollback en 30s, V1 restored, prod intacte. Hypothèses post-mortem dans `gotchas.md`.
- [x] (claude, 2026-04-16) Phase 4-bis — debug V2 hang : V2 validé en Preview draft (2.14s), puis en repro contrôlé sur published via chat_router réel (2.72s, 8 inputs populés avec contenu réel). Les 4 hypothèses du post-mortem sont toutes ÉLIMINÉES — le hang Session 21 était **transient** (probable outage LiteLLM/Groq ou race restart+1st call). Script rollback fiable créé (`scripts/rollback_teacher_v2_to_v1.sh`, fix `pg_read_file` via `/var/lib/postgresql/`).
- [x] (claude, 2026-04-16) Phase 5 — publish V2 sur both workflows (published+draft) + battery active `scripts/sprint3/eval_live_battery.py` (4 personas × 10 turns + 6 edge cases = 46 turns, 273 checks). **Pass rate 97.4% ✅ GREEN** (threshold 95%). Latence p50=4.5s, p95=12.8s. 2 timeouts transients (31s A2 t20, 30s B1 t1), 3 `t4_addressed` model-honesty fails (connu Session 21). Auto-detect onboarding ajouté à la battery pour ne pas pénaliser PROMPT_ONBOARDING (intouché par V2). Remplace les 48h passive monitoring prévues (signal trop faible avec 6 users sparse).
- [x] (claude, 2026-04-16) Phase 6 — L1 transfer activation FR→EN : migration `profils_eleves` +`l1 VARCHAR(2) DEFAULT 'fr'` +`l1_watch_enabled BOOLEAN DEFAULT true` (idempotent `scripts/migrate_l1_profile.py`), seed 5 rows `l1_transfer_observations` fr→en (articles/prepositions/false_friends/modals/word_order), hardcode `l1="fr"` chat_router:432 remplacé par lookup profil (fallback 'fr' si null, gate `None` si watch off), endpoints GET/PUT `/api/profile/l1` avec validation ISO-639-1 (profile_router.py, insérés AVANT `{domain}` catch-all pour priorité FastAPI), test integration endpoint 7/7 pass, battery ré-exécutée **99.4% ✅ GREEN** (334/336, +2pts vs Phase 5) + **L1 mention rate 75% (3/4 turns FR→EN)** telemetry informationnelle. 2 seuls fails = `t4_addressed` B1 model honesty connu. p50=5.1s, p95=6.5s (mieux que Phase 5, pas de timeouts transients).
- [x] (claude, 2026-04-16) Phase 7 — spaced retrieval proactif MVP : env flag `SPACED_RETRIEVAL_ENABLED` (default OFF — deploy safe), helpers `_fetch_due_retrieval_items` + `_persist_spaced_retrieval` dans chat_router avec wire pre/post-turn (stream_with_xp parse + enqueue+complete), `spaced_retrieval_addressed` field ajouté à `TeacherResponse` + `OUTPUT_SCHEMA_BLOCK`, intervalle fixe J+1 (FSRS post-MVP), LIMIT 3 items/turn anti-bloat, test d'intégration `test_spaced_retrieval.py` 6/6 pass (enqueue future-dated + fetch skip future + backdate + complete via concept_key + OFF short-circuit). Regression ladder J+3/J+7 reportée : MVP fait un seul passage J+1. Prêt à activer via `SPACED_RETRIEVAL_ENABLED=true` dans env academie-api quand Sinse veut valider en prod. 63 unit + 7 L1 endpoint + 15 smoke tous verts.
- [x] (claude, 2026-04-16) Phase 7.1 — flag `SPACED_RETRIEVAL_ENABLED=true` activé en prod. `/opt/academie/webapp/.env` flipped + `docker compose up -d academie-api` → `chat_router.SPACED_RETRIEVAL_ENABLED=True` confirmé en container. Smoke 15/15, test intégration 6/6 (scenarios ON + OFF). Monitor script `scripts/ops/monitor_spaced_retrieval.sh` + runbook `docs/99-runbooks/phase7-activation.md` (rollback command + seuils J+7). Revisit 2026-04-23 via monitor script.
- [ ] Phase 7.2 (post-MVP) — regression ladder J+3/J+7 + dedupe row cleanup cron + `last_error_summary` column richer than error_code
- [ ] Phase 7.3 (post-MVP) — FSRS scheduling (replace fixed interval)

### P3 — Cleanup backups pristine (DONE 2026-04-18)

- [x] (claude, 2026-04-18) Supprimer `/opt/litellm/config.yaml.backup-pre-sops` (9.9K) — backup pre-SOPS Session 18
- [x] (claude, 2026-04-18) Supprimer `/mnt/cosmos-data/cosmos-config/cosmos.config.json.bak-pre-autoupdate-off` (22K) — backup cosmos Session 18 ter
- [x] (claude, 2026-04-18) Supprimer `/mnt/cosmos-data/cosmos-config/cosmos.docker-compose.yaml.bak-pre-hardening` (2.0K)
- [x] (claude, 2026-04-18) Supprimer `/tmp/published-v1-backup-*.json` (108K) — backup Teacher V1 Session 22
- [x] (claude, 2026-04-18) Supprimer `/tmp/draft-v1-backup-*.json` (115K)
- [ ] **Garder** `/opt/academie-shared/secrets/cosmos-rollback.sh.bak` (919B) jusqu'à 2026-04-22 — puis supprimer

**Rollback** si un fichier s'avère nécessaire ex-post :
```bash
export RESTIC_PASSWORD_FILE=/opt/academie-shared/secrets/restic-passphrase
restic -r "rclone:gdrive:/Backups/academie/restic" restore latest --target /tmp/restore --include "<chemin>"
```

### P2 — Token tracking ABCD (DONE Session 19)
- [x] (claude, 2026-04-15) Schema migration `token_usage_daily` +3 colonnes (`litellm_tokens`, `openai_tokens`, `reconciled_at`)
- [x] (claude, 2026-04-15) A : inclusion fine-tunes `ft:gpt-4o-mini-*` dans le headline `base_tokens` (même quota OpenAI)
- [x] (claude, 2026-04-15) B : safety margin +10% sur le total affiché (`tokens` vs `tokens_raw` exposé pour transparence)
- [x] (claude, 2026-04-15) C : module `openai_reconcile.py` + lazy bg task dans `get_gpt4o_usage` (fire-and-forget si reconcile > 15 min stale, hit `/v1/organization/usage/completions`)
- [x] (claude, 2026-04-15) D : `_load_daily_tokens` seed counter avec MAX(local, litellm, openai) ; bg task bump counter post-reconcile
- [x] (claude, 2026-04-15) Bind RO `/opt/academie-shared/secrets:/run/academie-secrets` dans docker-compose.webapp.yml pour exposer la clé admin sans la baker dans l'image

### P1 — Sprint 2 Phase B3 (DONE Session 18)
- [x] (claude, 2026-04-15) B3 : `USE_V2_SCORING=true` actif en prod, branche `compute_error_profile` lit `row["tier"]` (majority vote) avec fallback matrix lookup si `tier IS NULL`, 5 tests `test_scoring_v2_branch.py`, retrospective 25 rows : v1=2.60 → v2=0.788 (−70% over-pénalisation confirmée)

### P2 — Sprint 2 Phase B+ (follow-ups)
- [x] (claude, 2026-04-15) Property-based tests `pytest-hypothesis` sur scoring invariants — 10 properties (round-trip T-codes, weights monotonicity, band normalization, total_errors ≤ rows, permutation stability, family isolation, majority vote B3, enrich determinism + valid tier, progress_pct bounds). Hypothesis a surfacé l'asymétrie v1/v2 weights (v1 sans `regressive`) → test défensif.
- [ ] Approach C éventuel : LLM-judged gravity (fine-tune nouveau modèle ou appel séparé) — P3, Sprint 6+

### P1 — Sprint 2 Phase B1 + B2 (DONE Session 17)
- [x] (claude, 2026-04-15) B1 : override loader tolerance_matrix_v2_overrides.yaml dans scoring.py + chat_router.py, override `sentence×beginner=noted` actif en prod
- [x] (claude, 2026-04-15) B2 : sections gravity_per_family + criterial_per_family ajoutées à v2.yaml, `enrich_error_fields()` helper, refactor INSERT router (15 cols), backfill 9 rows existantes, flag USE_V2_SCORING (skeleton)

### P1 — Sprint 2 Phase A (DONE Session 16)
- [x] (claude, 2026-04-15) Migration DB schema : error_log +6 cols, 3 new tables, snapshot cut-off ADR-007 option C, idempotent script + runbook 3 niveaux rollback
- [x] (claude, 2026-04-15) Matrix v2 review adversariale 21 cellules : 19 ACCEPT / 1 FLAG (`word_order × A1`) / 1 OVERRIDE (`sentence × beginner`)
- [x] (claude, 2026-04-15) ADR-009 gravity axes + tests régression 14/14 + bascule soft USE_V2_TOLERANCE en prod

### P2 — Features + workflow
- [x] (claude, 2026-04-13) Refonte /handoff et /pickup — claude-centric, workflow cleanup (10 tools supprimés, docs mis à jour)
- [ ] Flashcard / spaced repetition mode — P2
- [x] (claude, 2026-04-15) Admin : estimation dépense ft:gpt-4o-mini (error analysis) — livré via centralisation tracking LiteLLM SpendLogs (Session 12). Widget affiche tokens + coût USD pour tous modèles dès qu'ils ont du trafic.

### ~~P3 — Sprint 1.6 EFCAMDAT registration~~ (ABANDONNÉ)

EFCAMDAT requiert une affiliation universitaire pour l'accès — non applicable.
Alternatives en place : W&I+LOCNESS (2,671 learners) + NUCLE (5,249 learners) = 7,920 total, 412k obs.
Pistes complémentaires éventuelles : PELIC (Pittsburgh, open), FCE corpus (Cambridge open subset).

### P3 — Weekly reports (Option B — email/notifications)
- [ ] n8n weekly CRON workflow + email via Resend/SendGrid — P3
- [ ] /notifications page for report history — P3

### P4 — LLM pool BYOK
- [ ] Collect Groq keys from friends — P4
- [ ] Collect Mistral keys from friends — P4
- [ ] Uncomment blocks in /opt/litellm/config.yaml + restart — P4

### P1 — Sprint 5 Foundation refactor (DONE Session 27, 2026-04-18)

Roadmap complète : [`docs/00-project/roadmap_multilang.md`](docs/00-project/roadmap_multilang.md) + plan [`docs/00-project/sprint5_execution_plan.md`](docs/00-project/sprint5_execution_plan.md).

**Phase 1 — Foundation (commit `830a8b4` + `feda228`)** :
- [x] (claude, 2026-04-18) DB migration unifiée : rename `domaine`→`domain` sur 6 tables, values ISO (`'anglais'`→`'en'`), L1 user-global (eleves.l1), error_log.domain +backfill + index, indexes multi-domaine
- [x] (claude, 2026-04-18) Backend refactor : 11 SQL hardcodés paramétrés, 5 URLs `/chat/teacher` dynamiques via `domain_registry.py` helper, L1 endpoints pointent eleves.l1
- [x] (claude, 2026-04-18) Frontend : store `lib/stores/navigation.ts` (currentAgent/currentDomain ISO), config.ts + domain field, afterNavigate sync, 8 API defaults fixés, 6 links dynamiques
- [x] (claude, 2026-04-18) n8n : 6 workflows + workflow_history patch (gotcha discovered), removed `|| 'anglais'` fallbacks, prompt paramétré

**Phase 2 — Infra multi-domain (commit `eb43cb8`)** :
- [x] (claude, 2026-04-18) `academie_core.taxonomy.llm` : `ANALYSIS_MODEL_BY_LANG` + `SYSTEM_PROMPT_BY_LANG` + `USER_PROMPT_TEMPLATE_BY_LANG` dispatch ; fine-tune v3 EN gardé, backward-compat aliases OK
- [x] (claude, 2026-04-18) Dify Teacher minimal ISO param : URL `?domain=en` + JSON keys `"domain"` + JSON values `"en"`

**Phase 3 — Teacher chatflow lang-agnostic (commit `c42aa16`)** :
- [x] (claude, 2026-04-18) 4 nouvelles Start inputs Dify (`lang_target_name`, `lang_target_prof`, `concept_hints_json`, `cefr_diagnostics_block`), wire complet via code_turn_check (variables[], main sig, return dict, outputs dict)
- [x] (claude, 2026-04-18) llm_plan_choice + llm_session persona paramétrée (`prof {{#code_turn_check.lang_target_prof#}}`)
- [x] (claude, 2026-04-18) llm_onboarding LAISSÉ hardcodé EN — branche contourne code_turn_check pour nouveaux users (→ Maestro ES sera app Dify séparé avec onboarding ES natif)
- [x] (claude, 2026-04-18) Décision D5 actée : **1 chatflow Dify par agent** (pas de coquille universelle). Pour nouvelles langues : clone Teacher + traduction prompts ES natifs

**Phase 4 — Content pack ES Maestro DRAFT (commit `5ab1cc4`)** :
- [x] (claude, 2026-04-18) `rubrics/es.yaml` A1-C2 (PCIC source, DRAFT)
- [x] (claude, 2026-04-18) `fewshots/es.yaml` 14 exemples CEFR (DRAFT)
- [x] (claude, 2026-04-18) `concept_hints/es.yaml` 34 concepts (DRAFT)
- [x] (claude, 2026-04-18) `cefr_diagnostics/es.yaml` paliers + microtasks + persona ES (DRAFT)
- [x] (claude, 2026-04-18) `l1_transfer/fr_to_es.yaml` 7 patterns (por/para, ser/estar, genre, falso amigo, subj, article, pronombres — DRAFT)
- [x] (claude, 2026-04-18) `curriculum_es.yaml` 52 concepts structurés (DRAFT)
- [x] (claude, 2026-04-18) `rules_es.py` SKELETON — 7 régex détecteurs (V:SER_ESTAR, ART:PROF, PREP:POR_PARA, ORTH:NY, PUNCT:INTERROG, LEX:FALSE, PREP:CALQUE) — tous validés par 10 tests
- [x] (claude, 2026-04-18) `SYSTEM_PROMPT_ES` + `USER_PROMPT_TEMPLATE_ES` dans `llm.py` (50+ codes ES : V:SER_ESTAR, PREP:POR_PARA, ADJ:CONCORD, ORTH:NY/ACCENT, LEX:FALSE, N:GEN…)
- [x] (claude, 2026-04-18) `ANALYSIS_MODEL_BY_LANG["es"] = "gpt-4o-mini"` (base model, Option B audit)
- [x] (claude, 2026-04-18) `_DOMAIN_REGISTRY["maestro"]` gated par env var `ENABLE_MAESTRO=true` (dormant par défaut, s'active avec env + `DIFY_KEY_MAESTRO`)
- [x] (claude, 2026-04-18) 155 tests pass (37 core + 10 ES + 5 llm_dispatch + sprint2 + sprint3) ; feature flag vérifié

**RESTE pour activation Maestro alpha** (Session 29 pivot : pas de native reviewer disponible, cf mémoire `project_no_native_reviewers.md`) :
- [x] ~~Native speaker review C2 hispanophone~~ **SUPPRIMÉ** — stratégie validation sans reviewer natif : corpus oracle (PCIC/COWS-L2H) + LLM cross-consensus + télémétrie alpha famille
- [ ] Créer nouvelle app Dify "Maestro - Profesor de Español" via `scripts/dify/clone_app.py` (outil Phase 0.1 ready) + traduire prompts ES natifs + obtenir app key
- [ ] Set env vars `ENABLE_MAESTRO=true` + `DIFY_KEY_MAESTRO=<key>` dans `/opt/academie/webapp/.env`
- [ ] Rebuild academie-api + restart
- [ ] Flip `frontend/src/lib/config.ts` maestro.available=true + rebuild frontend
- [ ] Test alpha famille FR-native démarrent ES A1-A2

### P1 — Multilang strategic planning (DONE Sessions 28-29, 2026-04-18 → 2026-04-19)

**Session 28 — recherche maturité 6 agents parallèles** :
- [x] (claude, 2026-04-18) 6 agents parallèles : IT maturity / DE maturity / JP maturity / RU maturity / synthetic+cross-lingual SOTA / EU-CLARIN+grey-literature
- [x] (claude, 2026-04-18) Document [`docs/00-project/multilang_maturity_research.md`](docs/00-project/multilang_maturity_research.md) produit — verdict initial IT/DE mature 0€, JP plafond $3-10K, RU chemin A €33-59K ou chemin B B1 max

**Session 29 — pivot stratégie native JLPT/TORFL** :
- [x] (claude, 2026-04-19) Validation Sinse : "aucune dépense externe pour JP/RU". Pivot : utilisation systèmes de niveau natifs (JLPT pour JP, TORFL pour RU) au lieu de forcer CEFR → **0€ externe pour toutes langues sauf 40€ Profile Deutsch DE (sourced Sinse)**
- [x] (claude, 2026-04-19) [`multilang_maturity_research.md`](docs/00-project/multilang_maturity_research.md) refondu : §4 JP JLPT-native N5-N1, §5 RU TORFL-native TEU-IV, D12 mapping architectural
- [x] (claude, 2026-04-19) [`multilang_execution_roadmap.md`](docs/00-project/multilang_execution_roadmap.md) refondu : Phase 0 étendue 15j (+0.7 levels.py, +0.8 synthetic pipeline, +0.9 discovery emails), Wave 3 JLPT-native 30-35j (Wave 3.5 supprimée, N5-N1 dans Wave unique), Wave 4 TORFL-native 25-30j (Chemin A €33-59K abandonné par défaut)
- [x] (claude, 2026-04-19) [`multilang_research_plan.md`](docs/00-project/multilang_research_plan.md) refondu : §JP difficulty 4/5 30-35j, §RU difficulty 3.5/5 25-30j (passe de "defer 2027" à "Wave 4 engagée"), tableau récapitulatif + ordre d'exécution révisés
- [x] (claude, 2026-04-19) [`glossary.md`](docs/00-project/glossary.md) enrichi : entrées JLPT, TORFL/ТРКИ, Mapping natif↔CEFR, Profile Deutsch, Gosstandart ТРКИ, Japan Foundation JF Standard

**Décisions actées (D7-D12)** :
- D7 Synthetic two-stage (Latouche EMNLP 2024) dès Wave 1 — budget ~$25-35 OpenAI
- D8 Profile Deutsch acheté 40€ (Sinse sourced) pour DE rubrics
- D9 JP JLPT-native Wave 3 unique (N5-N1 complet)
- D10 RU TORFL-native Wave 4 (Gosstandart ТРКИ ressources open)
- D11 CLARIN/partenariats : discovery emails non-bloquants Phase 0.9
- D12 Mapping architectural `academie_core/levels.py` JLPT/TORFL↔CEFR

**Total multilang** : 5 langues (ES/IT/DE/JP/RU), ~125-150j effort Scénario B hybride, 10-13 mois, coût externe cumulé **40€ + ~$30 OpenAI**.

### P4 — Multilang Waves (post Session 29 pivot)

**Wave 1 ES (Q2 2026, 14-18j)** — Maestro CEFR, drafts déjà mergés + enrichissement.

**Wave 2 IT+DE parallèle (Q3 2026, 39-46j)** — Professore IT CEFR (MERLIN+VALICO+CELI) + Lehrer DE CEFR (MERLIN+Falko+DISKO+Profile Deutsch).

**Wave 3 JP JLPT-native (Q4 2026-Q1 2027, 30-35j)** — Sensei N5-N1 via Japan Foundation + Tae Kim + Imabi + JLPT officiel + I-JAS + Lang-8 + MeCab. **Wave 3.5 supprimée** (N1 inclus dans Wave 3).

**Wave 4 RU TORFL-native (Q2 2027, 25-30j)** — Maestro-RU TEU-IV via Gosstandart ТРКИ + Lexical/Grammatical Minimum + RLC + Дорога в Россию. Russian Wheel UCA Nice discovery non-bloquant.

**Phase 0 infra factorisée (DONE Session 29, 2026-04-19)** — ~13j effort Claude, 7 commits sur main (a2fe223 → 4c1286a) + 1 commit docs emails sinse-workspace. 141 tests pass, smoke deep 21/21.
- [x] (claude, 2026-04-19) 0.7 `academie_core/levels.py` — JLPT/TORFL↔CEFR mapping + score-bridge officiel Japan Foundation déc 2025 (26 tests)
- [x] (claude, 2026-04-19) 0.6 `taxonomy/tokenizer.py` abstraction dispatcher — fallback EN/ES/IT/DE, JP/RU stubs (12 tests)
- [x] (claude, 2026-04-19) 0.4 loader.py — no-op (déjà complet depuis Sprint 5)
- [x] (claude, 2026-04-19) 0.9 4 templates discovery emails (UCLouvain/Eurac/UCA Nice/HU Berlin) — Sinse envoie à son rythme depuis `sinseproduction@gmail.com`
- [x] (claude, 2026-04-19) 0.3 rules dispatch complet — 4 squelettes `rules_{it,de,jp,ru}.py` + extension `rules.detect_errors(lang)` (16 tests + régression ES préservée)
- [x] (claude, 2026-04-19) 0.5 `eval_live_battery.py --lang` — EN rétrocompat via in-code PERSONAS, non-EN via `data/battery/{lang}_personas.yaml` stub ES créé
- [x] (claude, 2026-04-19) 0.2 corpus normalizer framework — `scripts/sprint1/normalizers/` dispatcher + 5 stubs (errant/merlin/falko/cows/rlc) + `scripts/sprint1/mappings/` YAMLs per lang (10 tests)
- [x] (claude, 2026-04-19) 0.1 Dify app cloner — `scripts/dify/clone_app.py` dry-run par défaut + `dify_db.py` wrapper, 4 INSERTs transactionnels (workflows/apps/sites/api_tokens), validé dry-run sur Teacher (8 tests)
- [x] (claude, 2026-04-19) 0.8 synthetic errors pipeline — `scripts/synthetic/generate_errors.py` per-lang prompts + 5 YAML descriptors (`es.yaml` seed PCIC, `jp.yaml` critical Tanos/Bunpro/Polyglossia, it/de/ru placeholders Wave 2/4) (14 tests)

### P5 — Multi-domains non-langue
- [ ] PyMentor (Python): concrete capabilities taxonomy — P5
- [ ] CyberMentor (Cybersec): Beginner→Expert — P5

### P5 — Onboarding renforcé (hors-scope actuel)
- [ ] Réévaluer et renforcer considérablement l'onboarding + évaluation initiale (diagnostic CECRL) — P5

### P5 — Documentation portfolio (S5 remaining)
- [ ] GitHub Profile README (Sinsemilila/Sinsemilila repo) — P5
- [ ] Demo video 60-90s (Loom/screencast) — P5

### P1 — Onboarding refonte (DONE)
- [x] (claude, 2026-04-14) DB migration (5 cols + FK repair) + diagnostic UPSERT fix + profil-get + profile API + prompt rewrite + dashboard bilan + E2E test (24/24) + behavioral validation

### Session 15 — Infra fixes + Sprint 1 + Sprint 1.5 (DONE)
- [x] (claude, 2026-04-15) 7 fixes urgents : delete app cccccccc, archive dup n8n diagnostic, cleanup 820M dangling volumes, pg-backup multi-DB (+ litellm_db + dify_plugin), smoke-test n8n fail rate alert, migration subnet /28 → /27 (30 IPs)
- [x] (claude, 2026-04-15) Sprint 1 Path A — calibration externe W&I+LOCNESS BEA 2019 (2671 learners × 70k errors), tier map empirique, `tolerance_matrix_v2_draft.yaml` (44% cells changed)
- [x] (claude, 2026-04-15) Sprint 1.5 — NumPyro hierarchical GLMM β_tier posterior (R-hat 1.01), weights empiriques ignored=0.00/noted=0.196/penalized=0.394/regressive=0.538 (v1 sur-pénalisait T3 : 0.80 vs empirique 0.39)

## CLAIMED

(none)

### P1 — Sprint 4 ré-analyse (DONE 2026-04-16)

- [x] (claude, 2026-04-16) Ré-analyse pre-impl ADR-004 complétée, GO Option C accepted. Livrable : [`docs/00-project/sprint4_preimpl_review.md`](docs/00-project/sprint4_preimpl_review.md) — audit 8 dynamic sections vs Protocol, 3 méthodes manquantes identifiées, v2 proposée. ADR-004 flipped `accepted-in-principle` → `accepted`. Shared-core.md Domain Protocol v2 + agent-topology.md last_reviewed bumped.
- [x] (claude, 2026-04-16) 4 checkpoints ADR-004 fermés : revues post-Sprint 1/2/3, estimation 8-11 jours-dev, plan rollback canary `USE_ACADEMIE_CORE` flag.

### P1 — Sprint 4 implémentation (DONE 2026-04-16 — compressé en 1 session ~4h)

Estimation initiale 8-11j → livré en 1 session. Battery 99.1% GREEN post-migration. Zero prod regression.

- [x] (claude, 2026-04-16) Phase A — scaffold `packages/academie-core/` (commit `abbc0d8`) — pyproject + dirs + Protocol v2 stubs + 10/10 smoke tests
- [x] (claude, 2026-04-16) Phase B — port taxonomy layer vers `academie_core.taxonomy.*` (commit `abfab1d`) — 5 modules (1687L) + 3 YAMLs + Dockerfile context root
- [x] (claude, 2026-04-16) Phase C — port pedagogy layer vers `academie_core.pedagogy.teacher_prompt` (commit `edc16ee`) — 696L, 65/65 tests préservés via shim
- [x] (claude, 2026-04-16) Phase D — `LanguageDomain` wrapper (commit `8d54832`) — 13/13 unit tests, Protocol runtime-check satisfait
- [x] (claude, 2026-04-16) Phase E — `chat_router` utilise `_TEACHER_DOMAIN = LanguageDomain("en")` (commit `9a6865c`) — 4 call sites migrés
- [x] (claude, 2026-04-16) Phase F — cleanup shims (webapp/backend/app/teacher_prompt.py + error_taxonomy/ supprimés) + migration 8 scripts imports direct + battery 99.1% GREEN + docs fermées (commit TBD)
- [ ] Side-task — DELETE 6 chatbots Dify obsolètes — déféré à Sprint 5 kickoff (pas bloquant)

### P1 — Sprint 5 Maestro ES (on deck, estimation 4.5-6.5 jours-dev)

Sprint 4 rend possible — ajouter une langue = 4 YAMLs data + 1 ligne Python + 1 clone chatflow Dify.

- [ ] Phase 5.0 — DELETE 6 chatbots Dify legacy obsolètes (10min, side-task reporté Sprint 4)
- [ ] Seed `packages/academie-core/academie_core/data/rules/es.yaml` + `rubrics/es.yaml` + `fewshots/es.yaml` + `l1_transfer/fr_to_es.yaml` — 2-3j
- [ ] Cloner Teacher V2 chatflow Dify pour `language-tutor-es` (advanced-chat, PROMPT_SESSION_V2 traduit/adapté ES) — 1-2j
- [ ] `_DOMAINS = {"en": LanguageDomain("en"), "es": LanguageDomain("es")}` dans chat_router + routing par `user.domain` ou `req.agent` — 0.5j
- [ ] Wire env var `DIFY_KEY_MAESTRO` + test E2E avec family users — 1j

### P1 — Sprint 5 Maestro ES (POST Sprint 4 impl, indicatif)

Estimation : 4.5-6.5 jours-dev avec academie-core en place (vs ~15j sans factorisation).

- [ ] Seed `rules/es.yaml` + `rubrics/es.yaml` + `fewshots/es.yaml` + `l1_transfer/fr_to_es.yaml` — 2-3j
- [ ] Cloner Teacher V2 chatflow pour `language-tutor-es` (pas activer l'ancien chatbot Maestro obsolète) — 1-2j
- [ ] Wire `DIFY_KEY_MAESTRO` env var + `LanguageDomain("es")` instantiation — 0.5j
- [ ] Test E2E Maestro avec family users — 1j


## DONE

- [x] (claude, 2026-04-13) Behavior detection (5 states + escalade) + N+1 tracking + ADR setup
- [x] (claude, 2026-04-13) Exam redesign — advisor not gatekeeper, progressive cooldown, error-weighted scoring, adaptive feedback
- [x] (claude, 2026-04-13) Quiz rapide fix + taxonomy × progression reconciliation + mode switch warnings
- [x] (claude, 2026-04-13) Admin page + XP triggers + weekly recap + full reset
- [x] (claude, 2026-04-13) E2E validation — 39 tests (API + functional chat + error pipeline)
- [x] (claude, 2026-04-13) Code audit — 11 CRITICAL+HIGH security fixes
- [x] (claude, 2026-04-13) Honest per-concept scoring (scores_confiance primary, family fallback)
- [x] (claude, 2026-04-13) Real-time error feedback in chat (rules layer, zero LLM cost)
- [x] (claude, 2026-04-12) Model routing 3-tier + challenge tool + delegate + audit-self protocol
- [x] (claude, 2026-04-12) HISTORY.md + backdated ADRs + CHANGELOG separator
- [x] (claude, 2026-04-12) Post-audit cleanup — orphan files removed, content gaps fixed
- [x] (claude, 2026-04-12) Refactor v1.0 complete — S1 to S5 + audit + cleanup
- [x] (claude, 2026-04-12) S5 — README EN/FR + architecture + decisions + API overview
- [x] (claude, 2026-04-12) S4 — Monitoring cron + API tests + quickstart + workflow docs
- [x] (claude, 2026-04-12) S3 — Arbiter tested + Gemini worktree + merge flows
- [x] (claude, 2026-04-12) S2 — AGENTS.md + 16 tools + hooks + worktrees + secrets
- [x] (claude, 2026-04-12) S1 — Backup 4 levels + test restore + smoke-test
- [x] (claude, 2026-04-07) Teacher v17 validated, TTT 9/9, quiz, concept tips
- [x] (claude, 2026-04-07) LiteLLM BYOK config prepared
- [x] (claude, 2026-04-06) Webapp sprints 0-7 complete
