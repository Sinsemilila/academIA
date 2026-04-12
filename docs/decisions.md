# Key Design Decisions — AcademIA

> Architecture Decision Records (simplified). Why we chose X over Y.
> Decisions are listed chronologically by when they were actually made during development.

| # | Date | Decision | Alternatives Rejected | Rationale |
|---|------|----------|-----------------------|-----------|
| 1 | Apr 4 | **Self-hosted on Proxmox** | AWS/GCP/Vercel cloud | 0 EUR/month hosting. Full infrastructure control. Learning experience in itself. Trade-off: single point of failure (mitigated later by 4-level backup). |
| 2 | Apr 4 | **LiteLLM as LLM gateway** | Direct API calls to each provider | Load balancing across free tiers, automatic fallback when Groq rate-limits, single endpoint for all models. Zero cost for the gateway itself. |
| 3 | Apr 4 | **PostgreSQL for everything** | SQLite + JSON files, MongoDB | Relational model fits learner profiles perfectly. JSONB for flexible scores. pg_dump for reliable backups. No need for a second database. |
| 4 | Apr 4 | **Groq free tier as primary LLM** | OpenAI-only (paid) | Llama 3.3 70B handles B1-C1 English surprisingly well. Saves ~$50/month. OpenAI reserved for exams only. |
| 5 | Apr 5 | **Dify Chatflow for Teacher agent** | Custom Python LLM backend (langchain/llamaindex) | Visual 28-node chatflow enables rapid prompt iteration. Changes take minutes, not hours. Trade-off: Dify lock-in, but chatflow is exportable. |
| 6 | Apr 5 | **n8n for workflow orchestration** | Custom Python cron scripts | Visual editor, native webhooks, built-in error handling. 3 memory workflows built in 30 min vs estimated 4h in Python. |
| 7 | Apr 5 | **2-level memory system** | RAG on conversation history | Session snapshots (rolling summaries) + long-term profiles. Simpler and more reliable than embedding search on chat logs. |
| 8 | Apr 6 | **Deterministic concept selection** | LLM-driven concept choice | "System chooses WHAT, LLM chooses HOW." Prevents concept drift and ensures coverage. LLM still has creative freedom in delivery. |
| 9 | Apr 6 | **Cambridge CECRL exam framework** | Custom exam format | 6 question types (FILL/CORRECT/TRANSFORM/CHOICE/FORM/PRODUCE) grounded in real certification standards. Modular exams with concept weights per level. |
| 10 | Apr 7 | **SvelteKit custom webapp** | Dify's native chat UI | Full control over UX, gamification (XP, streaks, levels), custom branding, PWA support. Dify's UI was limiting for the learning experience we wanted. |
| 11 | Apr 7 | **TTT pedagogy (Test-Teach-Test)** | Free-form conversation, fixed curriculum, PPP method | 70-80% practice / 20-30% explanation optimal for adults. Explanation after failure more effective than before. Research-backed (Duolingo, Busuu, SLA literature). |
| 12 | Apr 7 | **Cloudflare Zero Trust (WARP)** | WireGuard VPN, Tailscale, email OTP | Zero client config, geolocation filtering (France only), free tier. Policy evolved: started with email OTP, switched to WARP+geoloc for frictionless access. |
| 13 | Apr 12 | **Multi-AI worktrees (Claude+Gemini)** | Single AI, shared directory | Isolated git worktrees per AI agent. Prevents file conflicts, enables parallel work. Arbiter cross-review for quality. |
| 14 | Apr 12 | **4-level backup strategy** | Git only | Proxmox vzdump (VM-level) + PG dump hourly + Restic encrypted to Google Drive + Git. Defense in depth — no single point of failure for data. |
| 15 | Apr 12 | **AGENTS.md over CLAUDE.md** | Monolithic per-AI config files | Single canonical file for all AI agents. Pointer pattern in worktrees. Telegraphic English for token efficiency. Inspired by Peter Steinberger's agent-scripts. |
