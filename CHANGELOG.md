# Changelog — AcademIA

Append-only. Format: `YYYY-MM-DD AI — [type] message`
Full historical detail: see `HISTORY.md` in /opt/academie/ and `archive/pre-migration-snapshots/`

## Historical summary (2026-04-04 → 2026-04-07)

2026-04-04 Claude — [feat] Phase 1: Docker stack deployed (Dify + LiteLLM + PostgreSQL + Redis)
2026-04-05 Claude — [feat] Phase 2: n8n + 3 workflows + 2-level memory system + Teacher chatflow v1
2026-04-05 Gemini — [feat] Curriculum table created + English A1-C2 skeleton injected
2026-04-05 Claude — [feat] Claude Code + sinse-workspace installed, /fin command created
2026-04-06 Claude — [feat] Phase 3: Teacher v5→v14 (28 nodes, exam system, CECRL scoring, 98 concepts)
2026-04-06 Claude — [feat] Phase 4: Webapp sprints 0-6 (SvelteKit + FastAPI + gamification + SaaS hardening)
2026-04-07 Claude — [feat] Sprint 7: 30 UX features + Teacher v15 (spaced repetition, absence-aware)
2026-04-07 Claude — [feat] Sessions 15-17: avatars, persistence, TTT pedagogy, quiz, concept tips
2026-04-07 Claude — [feat] Sessions 18-19: Cloudflare Zero Trust WARP, 6 users onboarded

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Refactor v1.0 (2026-04-12) — Structured format below
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2026-04-12 Claude — [feat] S1 — Backup 4 levels (vzdump + PG hourly + Restic/GDrive + git) + test restore
2026-04-12 Claude — [feat] S2 — AGENTS.md + 16 tools + /pickup + /handoff + hooks + worktrees + secrets
2026-04-12 Claude — [feat] S3 — Arbiter tested (Claude→Gemini GO) + Gemini worktree + merge flows
2026-04-12 Claude — [chore] S4 — Monitoring cron + API tests + quickstart FR + workflow docs
2026-04-12 Claude — [docs] S5 — README EN/FR + Mermaid architecture + 15 ADRs + API overview
2026-04-12 Claude — [chore] Post-audit — orphan files cleaned, content gaps fixed
2026-04-12 Claude — [feat] Model routing 3-tier (T1/T2/T3) + challenge + delegate + audit-self protocol
2026-04-12 Claude — [docs] HISTORY.md project timeline + backdated ADRs + CHANGELOG restructured
2026-04-12 Claude — [security] Git history purged via git-filter-repo — all secrets removed from all commits
2026-04-12 Claude — [docs] CHANGELOG + DECISIONS restructured — archived raw history, clean summaries
2026-04-12 Claude — [feat] academie-claude wrapper updated for refactor v1.0 (worktree + cly + YOLO)
2026-04-12 Claude — [feat] AcademIA renamed, GitHub repos reorganized (sinse-workspace private, academIA portfolio public)
2026-04-12 Claude — [fix] Timeout + fallback on all cross-AI tools (challenge, arbiter, delegate, restic, pg-backup)
2026-04-12 Claude — [security] sinse-workspace set to private, academIA public portfolio repo created (no source code)
2026-04-12 Claude — [chore] cly: remove --dangerously-skip-permissions, use settings.json allowlist (root-compatible)
2026-04-12 Claude — [fix] merge-to-main + merge-approve: replace broken worktree lookup with checkout (sinse-workspace has no main worktree)
2026-04-12 Claude — [feat] model indicator — visible tier/model line before every dispatch (T1/T2/T3/challenge/delegate)
2026-04-12 Claude — [fix] pre-push hook created — smoke-test --deep now blocks push on failure
2026-04-12 Claude — [fix] pickup: git sync conditionnel (no remote) + indicateur T2 session start
2026-04-12 Claude — [fix] settings.local.json: suppression commentaire JSON invalide (// test)
2026-04-12 claude — [chore] WSL2 setup + SSH cosmos config + Claude Code statusline (model/ctx/rate limits)
2026-04-12 claude — [fix] slash commands installés pour user sinse — /pickup et /handoff opérationnels
2026-04-13 unknown — [refactor] Workflow audit v1.1 — 12 fixes, arbiter always, concurrency safety, Gemini parity
2026-04-13 unknown — [feat] Fine-tune v3 deployed (85% F1), 6 category fusions (57 effective), rules layer enriched, tolerance matrix design finalized
2026-04-13 unknown — [feat] Phase 2+3 — tolerance matrix implemented, scoring engine, error-profile API, frontend integration, eleve merge fix, login drift guard
2026-04-13 unknown — [feat] Unified progression system — error-based scoring, concept mapping, E2E validated
2026-04-13 unknown — [feat] Shadow families activated progressively, credentials moved to env vars, progress bar = concept average
2026-04-13 unknown — [docs] Full platform audit — competitive analysis + blind spots + priority action plan
2026-04-13 claude — [fix] Honest per-concept scoring — scores_confiance as primary source, family fallback
2026-04-13 claude — [feat] Real-time error feedback in chat — rules layer injected into Teacher prompt, zero LLM cost
2026-04-13 claude — [security] Code audit — 11 CRITICAL+HIGH fixes: JWT env vars, endpoint auth, DOMPurify, CORS, security headers, streak race fix
2026-04-13 claude — [test] E2E validation script — 29 tests covering auth, security, scoring, gamification, CORS
2026-04-13 claude — [feat] Admin page — user table, create/reset/delete, online presence, sidebar link
2026-04-13 claude — [feat] XP triggers — +200 exam pass, +500 promotion via /internal/exam-result
2026-04-13 claude — [feat] Weekly recap — always visible, Monday highlight badge
2026-04-13 claude — [fix] Admin reset — full wipe (profile, XP, streaks, sessions, Dify conversations)
2026-04-13 claude — [fix] Quiz rapide — no correction between questions, only at bilan
2026-04-13 claude — [feat] Exam system redesign — advisor not gatekeeper, progressive cooldown 3/7/14j, on-demand exams
2026-04-13 claude — [feat] Adaptive feedback by error family — metalinguistic/explicit/recast per Lyster & Ranta
2026-04-13 claude — [feat] Exam scoring uses student error profile — n8n SQL node injects top errors into LLM prompt
2026-04-13 claude — [feat] Behavior detection — 5 emotional states + escalating correction protocol + backend timing/error signals
2026-04-13 claude — [feat] N+1 tracking — libre mode concepts scored by snapshot, preserved on promotion, shown in profile
2026-04-13 claude — [docs] ADR setup — MADR-lite format, 3 initial decisions (format, exam redesign, behavior detection)
2026-04-13 claude — [fix] E2E audit fixes — conn leak, N+1 SQL, behavior signals passthrough, last_seen debounce, transactions, try/except
2026-04-13 claude — [test] E2E suite extended to 50 tests — admin, next_level, exam result, behavior signals
2026-04-13 unknown — [fix] Fixed academie-claude launcher — pointed to deleted worktree, now /opt/academie
2026-04-13 unknown — [fix] n8n exam scoring — 3 bugs fixed: dify-admin-key prefix, empty SQL chain break, wrong $json ref in Fetch Exam Messages
2026-04-13 unknown — [remove] Workflow refonte cleanup — 10 dead tools, 1077 lines removed, docs updated
2026-04-14 unknown — [feat] Onboarding refonte — DB migration, diagnostic plumbing, prompt rewrite (2 FR + 5-7 EN + auto-eval + micro-tasks), dashboard bilan card, E2E test 24/24
2026-04-14 unknown — [fix] UUID→username resolution — n8n resolves dify_user_id to real username, prevents phantom eleves after profile reset
2026-04-14 unknown — [feat] Onboarding refonte + UUID fix + error pipeline + stats coherence
2026-04-14 unknown — [fix] UUID→username resolution for all n8n workflows (profil-get, diagnostic, snapshot, exam-scoring, exam-persist, error-analysis)
2026-04-14 unknown — [fix] Stats coherence — sessions, minutes, progress aligned between home and stats
2026-04-14 unknown — [docs] Inventaire 24 features + audit error taxonomy + audit personnalité
2026-04-14 unknown — [feat] Adaptation personnalité — ton adaptatif, profilage progressif, contextes par intérêts, objectif, settings webapp, onboarding tour 3
2026-04-14 unknown — [fix] Stats coherence, error pipeline, UUID resolution, snapshot niveau_global protection
2026-04-14 unknown — [style] Dashboard stats — concepts vus (X/total) au lieu de maîtrisés dans le bloc stats
2026-04-14 unknown — [feat] Rules expansion A1-C1 — 17 codes, 43 tests, 98% coverage + tolerance_matrix filtering in real-time
2026-04-14 unknown — [fix] 5 bugs phase 3 — snapshot JSON repair, derniere_session removed from diagnostic, is_first_turn, EVAL_READY wording, tolerance_matrix key
2026-04-14 unknown — [fix] F1 EVAL_READY — enforce French conclusion, 40/40 features PASS
2026-04-14 unknown — [feat] Switch chatbot Teacher sur gpt-4o-mini (free tier) + token budget daily 1.5M avec fallback groq + compteur persistant PostgreSQL + widget admin
2026-04-14 unknown — [fix] Token tracking — missing await corrigé
2026-04-14 unknown — [docs] SESSION.md cumulative history + handoff command updated to prepend
2026-04-15 unknown — [fix] pickup/handoff commands — absolute paths to /root/sinse-workspace/projects/academie-ia/, removed user-level duplicates
2026-04-15 unknown — [fix] F1 EVAL_READY — deterministic fallback in code_eval_check when LLM sends marker alone
2026-04-15 unknown — [feat] centralized token tracking — LiteLLM SpendLogs as truth, dual-tracking with tiktoken for sub-second auto-switch
2026-04-15 unknown — [docs] session 13 — structure docs/ complete (39 files, 5306 lines), 8 ADRs, scan exhaustif infra via 4 agents parallèles, 2 new docs (api-surface + integrations)
2026-04-15 unknown — [chore] pickup sur Sonnet 4.6, SESSION.md rotation N=3, SESSION_ARCHIVE.md créé
2026-04-15 unknown — [fix] 7 urgent infra fixes — cccccccc app, dup n8n diagnostic, dangling volumes 820M, pg-backup multi-DB, smoke-test n8n alert, subnet /27 migration
2026-04-15 unknown — [feat] Sprint 1 (Path A) — calibration empirique W&I+LOCNESS BEA 2019 (2671 learners × 70k errors), tier map empirique par reach, tolerance_matrix_v2_draft.yaml (44% cells changed vs v1)
2026-04-15 unknown — [feat] Sprint 1.5 — NumPyro hierarchical GLMM β_tier posterior (R-hat 1.01), calibrated weights ignored=0.00/noted=0.196/penalized=0.394/regressive=0.538 replace v1's 0.0/0.3/0.8
2026-04-15 unknown — [feat] bascule soft v2 tolerance matrix activée en prod via USE_V2_TOLERANCE=true (rollback 30s flag off + restart)
2026-04-15 unknown — [feat] sprint 2 Phase A — DB schema migration (error_log +6 cols, 3 new tables, snapshot cut-off ADR-007 option C), ADR-009 gravity axes, runbook 3 niveaux rollback, matrix review adversariale 21 cellules (19/1/1), 14 tests régression
2026-04-15 unknown — [fix] smoke-test LiteLLM check — utiliser /health/liveliness (lightweight) au lieu de /health (250KB JSON timeout-prone)
2026-04-15 unknown — [feat] sprint 2B1 — override loader for tolerance_matrix_v2_overrides.yaml (sentence×beginner=noted active in prod)
2026-04-15 unknown — [feat] sprint 2B2 — populate error_log v2 fields via deterministic enrichment (tier/gravity/criterial), 9 rows backfilled, USE_V2_SCORING flag skeleton
2026-04-15 unknown — [feat] sprint 2 B3 — USE_V2_SCORING actif en prod, compute_error_profile lit row["tier"] (majority vote + fallback matrix), retrospective 25 rows v1=2.60→v2=0.788 (-70%)
2026-04-15 unknown — [test] sprint 2 B+ — 10 property-based tests via pytest-hypothesis (round-trip, weights monotonicity, band norm, permutation stability, family isolation, majority vote, enrich determinism, progress bounds) ; surfacé asymétrie v1/v2 weights
2026-04-15 unknown — [security] J-1 SOPS fondation — sops+age installés, keypair age générée out-of-repo + password manager, webapp/.env.sops dotenv per-var commitable, decrypt-secrets.sh wrapper, runbook rotate-secrets-sops.md
2026-04-15 unknown — [security] J-1 suite — /opt/litellm/config.yaml migré vers SOPS (yaml encrypted_regex, 9 api_key + database_url chiffrés), E2E chat validé post-restart
2026-04-15 unknown — [security] J-1 cleanup — 9 fichiers /opt/academie-shared/secrets/* bundle en secrets/shared.yaml.sops + decrypt-shared.sh, round-trip byte-identical, redondance documentée avec sources canoniques webapp/litellm
2026-04-15 unknown — [security] cosmos AutoUpdate=false (L1 hardening) — supply-chain vector coupé, downtime ~15s, ALL CLEAR post-restart. Reste L2/L3 en session dédiée + L4/L5 pré-SaaS public
2026-04-15 unknown — [security] cosmos hardening L2/L3+1.b — privileged dropped (cap NET_ADMIN), bind dbus retiré, /:/mnt/host:ro, image digest pinnée. Bug bonus : --hostname cosmos-server obligatoire (sinon isInsideContainer check fail → nouveau config vide → routes cassées). --cgroupns host par sécurité. Smoke 15/15 ALL CLEAR.
2026-04-15 unknown — [feat] token tracking ABCD — A: inclusion fine-tunes ft:gpt-4o-mini-* dans headline ; B: safety margin +10% display ; C: lazy reconciliation OpenAI Usage API (15min staleness) ; D: triple safety MAX(local tiktoken, LiteLLM SpendLogs, OpenAI authoritative). Schema +3 cols, bind RO secrets, /admin tokens=219K vs OpenAI dashboard 199K = couvert avec marge.
2026-04-16 unknown — [feat] sprint 3 phases 0-3 — teacher_prompt.py + 63 tests + 24 fewshots + design.md + eval harness 4 personas 93.9% pass
2026-04-16 unknown — [feat] sprint 3 phase 4 partial — script CLI flags + chat_router V2 wiring + draft deploy ; LIVE TEST V2 HANG Dify, rollback OK 30s, prod intacte. Phase 4-bis debug requis (paragraph→text-input, isolation tests, dify-worker logs)
2026-04-16 unknown — [feat] sprint 3 phase 4-bis + 5 — V2 hang transient confirmed, V2 published, live battery 97.4% GREEN
2026-04-16 unknown — [feat] sprint 3 phase 6 — L1 transfer FR→EN activation : migration profils_eleves +l1+l1_watch_enabled, seed l1_transfer_observations 5 rows, chat_router lookup profil, GET/PUT /api/profile/l1, battery 99.4% (+2pts), L1 mention rate 75%
2026-04-16 unknown — [feat] sprint 3 phase 7 — spaced retrieval proactif MVP : flag SPACED_RETRIEVAL_ENABLED (OFF default), helpers _fetch_due + _persist enqueue/complete J+1, integration test 6/6, prêt à activer (regression ladder + FSRS post-MVP)
2026-04-16 unknown — [feat] sprint 3 phase 7.1 — activation SPACED_RETRIEVAL_ENABLED=true en prod + monitor script + runbook. Revisit 2026-04-23.
2026-04-16 unknown — [security] cosmos L4 — tecnativa/docker-socket-proxy:0.3.0 interposé 127.0.0.1:2375, cosmos.docker.sock mount REMOVED + DOCKER_HOST=tcp://... env. Bloque build/commit/services/plugins/secrets/configs + exec start. ADR-010. Rollback script ready.
2026-04-16 unknown — [refactor] sprint 3 — t4_addressed honesty instruction + L1 language names in build_l1_watch (French/English prose vs ISO codes). Battery 98.9% GREEN; 65/65 unit tests.
2026-04-16 unknown — [feat] sprint 4 ré-analyse pre-impl ADR-004 complétée — GO Option C accepted. 8 dynamic sections auditées, Domain Protocol v2 proposé (+3 méthodes), 8-11 jours-dev chiffrés, plan rollback USE_ACADEMIE_CORE canary. Sprint 5 Maestro ~5j post-impl. ADR-004 accepted-in-principle → accepted.
2026-04-16 unknown — [feat] sprint 4 impl DONE — 6 phases A-F compressées en 1 session (~4h). academie-core package shippé (taxonomy+pedagogy+domain/language), chat_router utilise LanguageDomain(en), shims supprimés. Battery 99.1% GREEN, 21/21 smoke, 23/23 academie-core, 65/65 test_prompt_assembly. Sprint 5 Maestro on deck (4.5-6.5j).
2026-04-18 Claude — [data] NUCLE normalization — 02b_normalize_nucle.py + nucle_to_academie.yaml : 5249 learners NUCLE ajoutés au corpus W&I+LOCNESS (total 7920 learners, 412k obs). GLMM recalibré : noted 0.196→0.005, penalized 0.394→0.165, regressive 0.538→0.683. R-hat 1.01, 0 divergences.
2026-04-18 Claude — [feat] sprint 5 infra DONE (one-time multi-langue) — _DOMAIN_REGISTRY dict keyed by agent remplace singleton _TEACHER_DOMAIN ; RUBRICS/FEWSHOT_BANK/L1_TRANSFER_SEED externalisés en YAML (data/rubrics/en.yaml, fewshots/en.yaml, l1_transfer/fr_to_en.yaml + l1_names.yaml) ; build_l1_watch lit YAML dynamiquement ; lang guards rules.py/llm.py. Ajout d'une nouvelle langue = 3 fichiers YAML + 1 ligne registry. 102 tests pass. commit 33a862a.
2026-04-18 Claude — [fix] sprint2 tests — 5 fichiers test_*.py migrés vers nouveau chemin YAML (academie_core/data/tolerance_matrix/ au lieu de webapp/backend/app/config/). 140/140 tests pass après fix.
2026-04-18 Claude — [feat] sprint 5 phase 1 — unified domain refactor (ISO + L1 user-global). Rename `domaine`→`domain` sur 6 tables, values `'anglais'`→`'en'`, L1 déplacée profils_eleves.l1→eleves.l1, error_log.domain ajoutée+backfill+index, 11 SQL backend paramétrés, frontend store navigation.ts + 6 liens dynamiques, n8n 6 workflows + workflow_history patch. 140/140 tests + 21/21 smoke. commit 830a8b4.
2026-04-18 Claude — [fix] sprint 5 phase 1.4 n8n — workflow_history gotcha découvert : n8n exécute depuis workflow_history.nodes (via activeVersionId), pas workflow_entity.nodes. UPDATE direct sur workflow_entity laissait le runtime sur vieille version → "column p.domaine does not exist" en prod. Script 02b_update_workflow_history.sql applique mêmes substitutions. commit feda228.
2026-04-18 Claude — [feat] sprint 5 phase 2 — llm.py per-lang dispatch (ANALYSIS_MODEL_BY_LANG + SYSTEM_PROMPT_BY_LANG, fine-tune v3 gardé pour EN, backward-compat aliases) + Dify Teacher minimal param (URL ?domain=en + JSON keys/values). Fix silent profile-loss bug où Dify envoyait encore ?domaine=anglais post-Phase 1. commit eb43cb8.
2026-04-18 Claude — [feat] sprint 5 phase 3 — Teacher chatflow lang-agnostic (session flow). 4 nouvelles Start inputs Dify (lang_target_name, lang_target_prof, concept_hints_json, cefr_diagnostics_block) wired via code_turn_check (variables[], main sig, return dict, outputs dict). llm_plan_choice + llm_session persona paramétrée. llm_onboarding LAISSÉ hardcodé EN car branche contourne code_turn_check pour nouveaux users. Décision D5 actée : 1 chatflow Dify par agent (pas de coquille universelle). HTTP 200 existing + new users. commit c42aa16.
2026-04-18 Claude — [feat] sprint 5 phase 4 — Content pack ES Maestro DRAFT merged gated. 6 YAML PCIC-sourced (rubrics/fewshots/concept_hints/cefr_diagnostics/fr_to_es_transfer/curriculum_es, 52 concepts) + rules_es.py skeleton (7 détecteurs regex validés) + SYSTEM_PROMPT_ES + USER_PROMPT_TEMPLATE_ES (50+ codes ES). Gated par env var ENABLE_MAESTRO=true + DIFY_KEY_MAESTRO. 155 tests pass. commit 5ab1cc4.
2026-04-19 unknown — [docs] Session 28 — recherche maturité 6 agents parallèles (IT/DE/JP/RU/synthetic+transfer/CLARIN-grey-lit), document multilang_maturity_research.md produit
2026-04-19 unknown — [docs] Session 29 — pivot stratégie native JLPT (JP) + TORFL (RU) → 0€ externe toutes langues sauf 40€ Profile Deutsch (Sinse). Refonte 4 docs : maturity_research, execution_roadmap, research_plan, glossary. D12 mapping architectural academie_core/levels.py
2026-04-19 unknown — [feat] Phase 0 multilang infrastructure — 7 items livrés (0.7 levels.py, 0.6 tokenizer, 0.3 rules dispatch + squelettes IT/DE/JP/RU, 0.5 battery --lang, 0.2 normalizer framework, 0.1 Dify cloner, 0.8 synthetic pipeline) + 4 templates emails discovery. 141 tests pass, smoke deep ALL CLEAR 21/21.
2026-04-19 unknown — [security] Phase 1 security remediation — 3 commits (redact PLAN.md + HISTORY.md PII, fail-fast JWT/INTERNAL_API_TOKEN, env vars for hardcoded scripts). Phase 2 (rotations: Postgres pw + Dify Teacher/admin keys + JWT x2 + INTERNAL_API_TOKEN + maybe LiteLLM master key) et Phase 3 (git filter-repo + force-push) restent à faire par Sinse en prochaine session.
2026-04-20 Claude — [security] Session 31 — Phases 2+3+4+5 remédiation sécurité terminées. 5 secrets prod rotés (Dify Teacher key 2A, Dify ADMIN_API_KEY 2D, JWT×2 2E, INTERNAL_API_TOKEN 2F, Postgres sinse pw 2C). Image academie-api rebuild → fail-fast Phase 1 enfin runtime-actif. n8n `workflow_entity` + `workflow_history` patched pour INTERNAL_API_TOKEN (Session 27 gotcha), + n8n `credentials_entity` "Postgres account" update UI (gotcha découvert à chaud : missing this cause dify-profil-get body vide → cascade Dify crash). `git filter-repo --replace-text + --replace-message` sur 7 patterns (5 leaked + `academie-internal-2026` + `sk-litellm-master-key` placeholder), force-push origin main (ffa761e→b5cfb50). Smoke deep 21/21 ALL CLEAR, live user flow validé (login + chat Teacher). ADR-012 + update runbook rotate-secrets-sops + gotchas opérationnels documentés.
2026-04-20 Claude — [security] Quickwins P2 — 3 items fermés. (1) `.githooks/pre-commit` trackable + `core.hooksPath` setup (survie aux clones frais, complète le legacy `.git/hooks/pre-commit` Session 14). (2) pg_hba.conf durci : `trust` retiré sur `host 127.0.0.1/32` + `::1/128` → `scram-sha-256` (socket local reste trust pour pg-backup docker exec). `pg_reload_conf()` non-disruptif, old pw REJECTED via TCP loopback validé. (3) Dify "Détection profil" short-branch fix : 12 outputs défaut ajoutés (`exam_resume_*`, `exam_scoring_recovered`, `error_exam_eligible`) via admin console API draft patch + publish UI. Published workflow `006cba2d`. Smoke deep 20/20 ALL CLEAR + 1 warning historique n8n.
2026-04-20 Claude — [feat] Session 32 Wave 1 ES Phases A+B+C — **Maestro ES en prod**. Phase A content packs (fr_to_es.yaml 7→19 familles, rules_es.py 7→15 détecteurs avec FP whitelists, rubrics A1+A2 enrichis PCIC gaps, synthetic_descriptors 8→35 A1-C2, battery 12→60 turns A1-C2, 107 tests pass, commit 3bd0cce). Phase B synthetic generator hardening (temp 0.6 + post-filter rules_es + stats) + decision skip fine-tune Wave 1 (quality ~50%, re-fit post-alpha, corpus archivé data/synthetic_corpus/es/, commit d61f459). Phase C Dify Maestro clone via plan-mode : 4 LLM prompts translatés par 4 agents parallèles avec GLOSSARY.md (plan_choice 1.2KB, session 4.6KB, onboarding 5.3KB MCER-calibré, exam 6.2KB DELE-adapté) + code_exam_bilan 12 strings + 7 HTTP domain=en→es, maestro_prompts.json 19 overrides avec helper double-escape Python-code context. App Maestro 47b0529c créé, api_key rotée sops, ENABLE_MAESTRO=true + maestro.available=true + rebuild frontend, smoke 20/20 (commit 25a8ddb). Bonus : bug latent Session 31 Phase 4 découvert — admin API publish strippe conversation_variables → Teacher 006cba2d + Maestro d3df0ef0 + draft ed0d1c91 restored atomiquement depuis c52a451f (3376 chars conv_vars : nb_interactions, exam_*, session_snapshot, review_mode). Phase D battery validation = next session.
2026-04-20 Claude — [security] Quickwins P2 Session 32 — 3 items fermés. (1) .githooks/pre-commit trackable + core.hooksPath (complète legacy Session 14, survit aux clones frais). (2) pg_hba.conf durci : trust 127.0.0.1/::1 → scram-sha-256 (socket local kept pour pg-backup). (3) Dify "Détection profil" short-branch fix 12 outputs défaut. Published 006cba2d.
2026-04-20 unknown — [feat] Sprint 5 Phase 5 — onboarding QCM pre-chat (Karpathy-style curated context) : 8 items Bloc A/B/C, learner_profiles JSONB persist, injection double canal Dify, 3 bugs Session 32 résolus pour Teacher+Maestro, wiring onboarding-branch via code_profil_check + override FIN prompt
2026-04-20 unknown — [feat] UI multi-agent overview + dashboard endpoint : AgentsOverviewRow component sur home+stats, GET /api/me/dashboard merge profils_eleves + learner_profiles QCM fallback, click=select (pas navigate), Reprendre btn stats level card
2026-04-20 unknown — [fix] Frontend multi-lang P0 fixes : profile Teacher hardcoded → currentAgentObj.name, stats/concepts onMount→$effect reactive, home welcome dynamic via langGenitive, top row stats scoped current agent, format minutes compact 101h42
2026-04-20 unknown — [docs] Onboarding research + action plan : 7 rapports recherche reconstitués (vague1 théorie + vague2 appliqué), plan d'action multi-lang consolidé docs/00-project/multilang-action-plan-2026-04-20.md, ADR #17 + runbook onboarding-qcm-activation
2026-04-21 Claude — [fix] Session 35 P0 rubric level mismatch : chat_router priorise `learner_profiles.domain_level.cefr_placement` sur legacy `profils_eleves.niveau_global` souvent vide. Gotcha : rebuild (pas juste restart) académie-api car code baked dans l'image. Validé live.
2026-04-21 Claude — [fix] Session 35 P1 Teacher greeting L1 drift : scripts/sprint5/15_strengthen_qcm_override_l2_example.py injecte 2 few-shots L2 explicites dans QCM_OVERRIDE_v1 (marker `L2_EXAMPLES_v1`). Teacher+Maestro draft+published patchés. Validé live.
2026-04-21 Claude — [feat] Session 35 politique L1/L2 adaptative : matrice level×typological-distance×FLA (9 cells + modulation FLA high, shift +1 bande). Modules `academie_core/pedagogy/typological_distance.py` (table FR-ES close → FR-JP distant) + `scaffolding_policy.py` (POLICY_MATRIX + `build_scaffolding_block()` Butzkamm sandwich + réassurance conditionnelle). 19 tests paramétrés verts. Wiring `teacher_prompt.PromptContext` + `chat_router` via append à `learner_profile_summary` (MVP — Phase 2 splittera en input Dify Start dédié). Kill switch `SCAFFOLDING_BLOCK_ENABLED=true`.
2026-04-21 Claude — [docs] Session 35 doctrine pédagogique `docs/01-pedagogy/l1-l2-scaffolding-policy.md` : 10 sections, citations Butzkamm 2009 + Cook 2001 + Macaro "optimal position" + Hall & Cook 2012 + Ringbom 2007 + CEFR 2020 Companion + ACTFL 2021 softening + Cervantes PCIC + Japan Foundation Marugoto. Justifie abandon "100% L2 turn 1" indéfendable A1 + benchmark marché (9/10 apps utilisent L1 à A1 turn 1).
2026-04-21 Claude — [feat] Session 36 — consolidation CEFR QCM → niveau validé (C hybride bienveillant). Migration `01_consolidation_schema.sql` (6 cols profils_eleves + observations_json + consolidation_events audit table). Module `pedagogy/consolidation.py` : trigger + aggregation + clamp anti-whiplash + 3 messages bienveillants prof (validation/upgrade/downgrade). 29 tests paramétrés verts (matrice 9 cells × FLA shift). Router `/api/consolidation/*` (4 endpoints, LLM-as-judge fallback gpt-4.1-mini). Hook chat_router post-turn. 3 Svelte components runes (LevelBadge + MiniExamModal + ConsolidationDecisionModal) + wiring chat layout. Doc `docs/01-pedagogy/cefr-consolidation-policy.md`.
2026-04-21 Claude — [fix] Session 36 4 scripts Dify : 02_add_observed_level_to_prompts (OBSERVED_LEVEL_v1 dans llm_session/onboarding/plan_choice), 03_silence_legacy_bilan_when_qcm (NO_LEGACY_BILAN_v1), 04_qcm_users_skip_llm_onboarding (code_profil_check: profil_present=true aussi quand learner_profile_summary non-vide → bypass FASE 2 + bilan + boucle goodbye). Teacher+Maestro draft+published, 4 slots × 3 scripts.
2026-04-21 Claude — [fix] Session 36 bugs live session : (1) path YAML mini-exam `/opt/academie/...` hardcodé → `Path(academie_core.__file__).parent / data / mini_exam` ; (2) Svelte 5 runes mode : `export let` + `createEventDispatcher` → `$props` + callbacks ; (3) API_BASE_URL inexistant → URLs relatives ; (4) modals white-on-white → tokens thème adaptatifs (bg-surface/text-text-primary) ; (5) UX Enter-to-next + autofocus + Shift+Enter textarea.
2026-04-21 Claude — [docs] Session 36 — 3 dettes QCM loguées TODO P2 : probe_answer B1+ non réutilisé turn 1, fla_items_raw collapsed en 1 catégorie (3 sliders distincts perdus), scaffolding_level QCM redondant avec scaffolding_block S35 à unifier.
2026-04-21 unknown — [feat] Session 37 — 16 commits: E2E consolidation + observed_level v2 + QCM debts refactor + Phase A multi-lang + consolidation UX trio + YAML-driven curriculum injection + priority concepts Ebbinghaus loop + n8n dify-snapshot public API refactor
2026-04-22 unknown — [feat] Session 38 — n8n dify-diagnostic+exam-scoring public API refactor (ae00b35) ; three-strikes micro-lesson MVP with CEFR-graded YAML templates EN+ES (7d2464f) ; PRIORITY_CONCEPTS+MICRO_LESSON activated in prod ; aggregate regression battery RUN_RECENT_BATTERY.sh 7/7 (bc6f611) ; prompt caching audit Phase A (7a23f9f) + minimal reorder Phase C cacheable 5→900 tok -8.4%/user (dcd7110)
2026-04-22 unknown — [feat] Session 42 — 11-commit autonomous package : 5 dettes techniques + 3 Oracle items + 2 pédago Phase 2
2026-04-22 unknown — [test] Session 42 O3 — Oracle fault injection run Teacher EN (GATE FAIL as expected, LiteLLM-bypass methodology floor confirmed; 5 faults x 26 scenarios)
2026-04-22 unknown — [feat] Session 43 P5 onboarding telemetry (funnel + 2 endpoints + admin section)
2026-04-22 unknown — [chore] Session 43 O4 noise floor V2 — semantic_fidelity 33% → 7.7% post-O1 parity fix
2026-04-22 unknown — [fix] Session 43 Dify learner_profile_summary 2000 → 10000 chars (unblocks chat post-onboarding)
2026-04-22 unknown — [fix] Session 43 smoke-test n8n fail rate false alarm (excluded battery-hit workflows)
2026-04-22 unknown — [feat] Session 44 admin dashboard redesign + 3-tier model budget waterfall
2026-04-22 unknown — [fix] Session 44 chain of budget tracker fixes (workflow IDs dynamic, tier 1 cap 2.5M, callback normalize, margin 2%)
2026-04-22 unknown — [feat] Session 44 V2 header-based rate-limit tracker (provider-attested live counters)
2026-04-22 unknown — [fix] Session 44 multi-agent model switch (Teacher + Maestro patched together)
2026-04-22 unknown — [feat] Session 45 P1 — Oracle noise floor V2 baseline (gemini-3-1-flash-lite judge κ=0.84)
2026-04-22 unknown — [fix] Session 45 P2 — TIER_TO_FEEDBACK_BY_LEVEL CEFR-gated mapping (kills A1 metalinguistic leak)
2026-04-22 unknown — [fix] Session 45 P2d — B1 anti-patterns + L2_ratio band relaxation (Teacher EN 17→22/26)
2026-04-22 unknown — [feat] Session 45 P4.5 — /admin Oracle judge budget section (3-tier Gemini chain visualization)
2026-04-22 unknown — [chore] Session 45 P2g+h+i — pink-elephant priming negative finding, rolled back to V5 baseline
2026-04-22 unknown — [chore] statusline.sh fun gadget — evolution emoji chain 🌱→🌿→🌳→🦋→🐉 + anniversary 🎂
2026-04-23 unknown — [feat] Refactor 2026-H2 Phase A : 5/7 items livrés (ADR-001 + A2 Argon2id + A3 CSP report-only + A4 MFA TOTP + A7 Cloudflare DNS/SSL/HSTS/WAF/Cache + A7a CI Dependabot)
2026-04-23 unknown — [feat] A1 Auth sessions opaques Redis + cookie HttpOnly + CSRF double-submit (validé sinse end-to-end, JWT localStorage XSS éliminé)
2026-04-23 unknown — [feat] Session 46 close — Phase A 6/7 (+A1 sessions Redis JWT XSS éliminé) ; pickup primer A5+A6 prêt pour Session 47
2026-04-23 unknown — [feat] Session 47 (2026-04-23, ~10h) — Phase A 7/7 closed + B1 design tokens OKLCH + B4 GlitchTip observability stack + 4 followups + Cloudflare Access refactor
2026-04-25 unknown — [feat] Session 48 close — Migration Obsidian Phase 0a/0b/0c+1+2+3 complete + v0.1 Claude-as-vault-cognition livrée (two-tier slash commands /pickup + /project, vault-reader Haiku subagent, vault structure, 135 locks accumulés)
2026-04-28 unknown — [fix] Session 50 — closure finale Obsidian: Phase A purge sinse-workspace refs (5 docs/), Syncthing PC fixe paired (3 devices), audit intégral 10 checks PASS, tests E2E vault-reader+/handoff+round-trip ALL PASS
