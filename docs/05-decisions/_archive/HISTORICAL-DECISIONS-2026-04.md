# Decisions — AcademIA

Append-only. Format: `YYYY-MM-DD AI — decision — rationale`
Full historical detail: see `archive/pre-migration-snapshots/` and `refactor-v1.0/decisions.md`
Portfolio-facing ADRs: see `/opt/academia/docs/decisions.md` (15 backdated entries)

## Historical summary (2026-04-04 → 2026-04-07)

2026-04-04 Claude — Remove Qdrant + Ollama — RAG unnecessary, Groq free tier faster
2026-04-04 Claude — 2-level memory (snapshot + profile) — cost-effective vs full RAG
2026-04-05 Claude — n8n over Flask API — visual workflows, native webhooks
2026-04-05 Claude — Workspace on GitHub — multi-machine sync + history
2026-04-05 Gemini — Dedicated curriculums table — granular milestone tracking
2026-04-06 Claude — Deterministic concept selection — LLM drifted to out-of-scope concepts
2026-04-06 Claude — TTT pedagogy (Test-Teach-Test) — research-backed, 70/80 practice ratio
2026-04-06 Claude — Cambridge CECRL exam framework — 6 question types, modular scoring
2026-04-06 Claude — Dify var_assigner: "over-write" not "set" — found in Dify source code
2026-04-07 Claude — SvelteKit + FastAPI custom webapp — Dify UI too limiting for gamification
2026-04-07 Claude — TTT 4 adaptive modes per concept — DISCOVERY/REINFORCEMENT/PRACTICE/MAINTENANCE
2026-04-07 Claude — Promotion guard days_seen >= 2 — sleep consolidation (neuroscience)
2026-04-07 Claude — Groq-standard over mistral-small — rate limit fix, better reliability
2026-04-07 Claude — Cloudflare Zero Trust WARP — replaced email OTP, zero-friction

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Refactor v1.0 (2026-04-12) — Structured format below
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2026-04-12 Claude — Refactor v1.0: 37 decisions (D1-D37) — see refactor-v1.0/decisions.md for full list
2026-04-12 Claude — 3-tier model routing (T1/T2/T3) — optimize token budget across haiku/sonnet/opus + flash/pro
2026-04-12 Claude — challenge tool (3-round debate) — Claude position → Gemini adversarial → Claude synthesis
2026-04-12 Claude — BUG FIX PROTOCOL in AGENTS.md — 6-step diagnostic before any [fix] commit

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Workflow simplification (2026-04-13)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2026-04-13 Claude — Single-agent workflow — worktrees+arbiter+Gemini retired, Claude works directly on main
2026-04-13 Claude — Removed merge-to-main/approve/reject tools — no branches to merge, direct commits on main
2026-04-13 Claude — Simplified /pickup + /handoff — claude-centric, no multi-agent coordination
