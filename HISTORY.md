# Project History — Academie-IA

> The engineering journey from bare metal to a multi-AI learning platform.
> This project was built over 8 intensive days (2026-04-04 to 2026-04-12) by a solo developer working with AI coding agents.

---

## Phase 1 — Infrastructure from Scratch (April 4, 2026)

**Starting point**: A NAS running Proxmox with an empty Debian VM called "cosmos".

**Built in one session**:
- Docker Compose stack on `academie-net-bridge` network
- Dify (AI platform) — web, API, worker, plugin-daemon
- LiteLLM proxy — gateway for 5 LLM models (Groq, Mistral, OpenAI)
- PostgreSQL — 4 tables (eleves, profils_eleves, snapshots_session, historique_sessions)
- Redis — cache and Celery broker

**Key decision**: Use LiteLLM as a gateway instead of direct API calls. This enabled free-tier rotation across providers — Groq for daily sessions, Mistral as fallback, OpenAI reserved for exams only. Total LLM cost: ~$0/month for 90% of usage.

**What we learned**: Qdrant (vector DB) and Ollama (local LLM) were deployed then removed — RAG turned out unnecessary for curriculum delivery, and local models couldn't match Groq's free-tier quality.

---

## Phase 2 — AI Integration & Memory System (April 5, 2026)

**Built**:
- n8n workflow orchestrator — 3 webhooks (profil-get, snapshot, profil-update)
- 2-level memory system:
  - Level 1 (session): rolling AI-generated summaries every 10 interactions
  - Level 2 (long-term): persistent pedagogical profiles in PostgreSQL
- Teacher chatflow in Dify — first version with profile injection via Jinja2
- System prompt v2 — 3-phase onboarding (personality → diagnostic → synthesis)

**Key decision**: Dify Chatflow over custom Python LLM backend. The visual 28-node editor enabled rapid prompt iteration — changes that would take hours in code took minutes in the flow editor.

**Key decision**: n8n for orchestration over Python cron scripts. The 3 memory webhooks took 30 minutes to build visually vs estimated 4 hours in Python.

**What surprised us**: The `dify-plugin-daemon` container was unstable for days, then self-stabilized without intervention. We learned not to restart things unnecessarily.

**Also this day**: Claude Code installed on cosmos, sinse-workspace created on GitHub, first Gemini CLI session (curriculum skeleton), `/fin` slash command created.

---

## Phase 3 — Teacher Evolution v1→v14 (April 5-6, 2026)

**The most intense engineering phase.** Teacher went through 14 major versions in 48 hours.

**v1-v3**: Basic chatflow → profile-aware → structured prompts. Root cause found: Jinja2 `jinja2_text` silently overrode the `text` field in LLM nodes.

**v5-v6**: Architecture refactored — 3 LLM paths (plan/session/onboarding) + deterministic concept selection via `code_turn_check`. Principle established: "the system chooses WHAT, the LLM chooses HOW."

**v10-v11**: Exam system built — 6 question types from Cambridge CECRL research (FILL/CORRECT/TRANSFORM/CHOICE/FORM/PRODUCE), modular exams with concept weights, multi-module progression (A1=43q to C2=56q).

**v12-v14**: Production hardening — exam persistence across sessions, resume mid-exam, abort handling, cooldown system (7 days + 5 sessions between exams), scoring fix (critical: Dify API returns messages chronologically, not reversed).

**Key numbers**: 98 concept keys across A1→C2, 28 nodes, 45 edges, 6 conversation variables for exam state.

**Hardest bug**: `var_assigner` in Dify — operation "set" doesn't support `input_type: "variable"`. Had to use "over-write" mode. Found by reading Dify source code directly.

---

## Phase 4 — Custom Webapp (April 7, 2026)

**Why**: Dify's native chat UI couldn't support gamification, custom branding, or the learning experience we wanted.

**Sprints 0-7 in one session** (~12 hours):

| Sprint | Deliverables |
|--------|-------------|
| 0-2 | SvelteKit + FastAPI + Docker, JWT auth, dashboard, SSE streaming chat |
| 3 | Stats page — concept gauges, session history, exam results |
| 4 | Gamification — XP, 9 badges, ranks (Debutant→Maitre), level-up toasts |
| 5 | Polish — responsive mobile, skeleton loading, favicon, 404/500 pages |
| 6 | SaaS hardening — rate limiting, security headers, refresh tokens, CSP, PWA manifest, service worker, Docker healthchecks, structured logging, input validation |
| 7 | 30 UX features — daily goal ring, weekly recap, celebration confetti, command palette Cmd+K, progression graph, dual theme, session timer, changelog page |

**Key decision**: SvelteKit over React/Next.js — faster to build, better DX for a solo dev, native SSR.

**Infrastructure added**: nginx reverse proxy with security headers + static caching, Cloudflare Tunnel for public access, multi-hostname routing (academie/dify/n8n).

---

## Phase 5 — Multi-User & Polish (April 7, 2026 — Sessions 15-19)

**Session 15**: Avatars in chat, persistent Dify conversations per user, absence detection (1h/1d/7d tiers), streaming cursor animation, daily goal ring, snapshot safety cron.

**Session 16**: TTT (Test-Teach-Test) pedagogy implemented — 4 modes per concept (Discovery/Reinforcement/Practice/Maintenance), promotion guard (days_seen ≥ 2), LiteLLM BYOK config prepared for friends.

**Session 17**: TTT validated (9/9 turns correct), Quiz button, structured/free mode toggle, concept tips with personalized advice, Teacher migrated from mistral-small to groq-standard (Llama 3.3 70B).

**Session 18**: Cloudflare Zero Trust policy changed from email OTP to WARP + France geolocation — zero-friction access for users.

**Session 19**: 6th user account created. Platform stable with daily active usage.

**Users onboarded**: sinse (admin), nico, julien, noz_project, waigosan, 0tha.

---

## Phase 6 — Workflow Refactor v1.0 (April 11-12, 2026)

**Problem identified**: The development workflow was artisanal — no backups beyond git, no multi-AI collaboration, monolithic documentation, no safety nets.

**Planning phase** (~8 hours): 37 decisions, 8 golden rules, 18 discussion points resolved, 10 gaps filled. Inspired by Peter Steinberger's agentic engineering patterns (AGENTS.md, committer, pointer pattern).

**Execution** (~4 hours, 5 sessions):

| Session | Deliverables |
|---------|-------------|
| S1 | 4-level backup (Proxmox vzdump + PG hourly + Restic/GDrive + Git), restore tests, smoke-test |
| S2 | AGENTS.md, 16 bash tools, /pickup + /handoff, git hooks (gitleaks), worktrees, secrets migration |
| S3 | Arbiter cross-review (Claude↔Gemini), Gemini worktree, merge flow validation |
| S4 | Monitoring cron, API tests, quickstart guide, workflow documentation |
| S5 | Professional README EN/FR, architecture diagrams, ADRs, API overview |

**Post-audit**: Full structural audit, 5 orphan files cleaned, content migration verified.

**Result**: From artisanal solo-AI setup to professional multi-AI workflow with automated backups, cross-review, and intelligent merge classification.

---

## By the Numbers

| Metric | Value |
|--------|-------|
| Development time | 8 days (est. ~80 hours effective) |
| Teacher chatflow versions | 17 (v1→v17) |
| Chatflow nodes | 28 |
| Chatflow edges | 45 |
| English concepts (A1→C2) | 98 |
| Webapp features | 50+ |
| Bash tools | 16 |
| Docker containers | 13 |
| Active users | 6 |
| LLM models in rotation | 5 |
| Backup levels | 4 |
| Monthly hosting cost | 0 EUR |
| Monthly LLM cost | ~0 EUR (free tiers) |

---

## What's Next

- Admin dashboard for sinse (user management, global stats)
- XP triggers (exam pass +200, promotion +500)
- Flashcard / spaced repetition mode
- Weekly progress reports via n8n
- Multi-domain expansion (Spanish, Japanese, German, Italian, Python, Cybersec)
- LLM pool expansion (friends bring their own API keys)
