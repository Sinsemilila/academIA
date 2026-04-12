# Key Design Decisions — Academie-IA

> Architecture Decision Records (simplified). Why we chose X over Y.

| # | Decision | Alternatives Rejected | Rationale |
|---|----------|-----------------------|-----------|
| 1 | **LiteLLM as LLM gateway** | Direct API calls to each provider | Load balancing across free tiers, automatic fallback when Groq rate-limits, single endpoint for all models. Zero cost for the gateway itself. |
| 2 | **Dify Chatflow for Teacher agent** | Custom Python LLM backend with langchain/llamaindex | Visual 28-node chatflow enables rapid prompt iteration. System prompt changes take minutes, not hours. Trade-off: vendor lock-in on Dify, but the chatflow is exportable. |
| 3 | **SvelteKit custom webapp** | Dify's native chat UI | Full control over UX, gamification (XP, streaks, levels), custom branding, PWA support. Dify's UI was limiting for the learning experience we wanted. |
| 4 | **Groq free tier as primary LLM** | OpenAI-only (paid) | Llama 3.3 70B on Groq handles B1-C1 English surprisingly well. Saves ~$50/month. OpenAI reserved for exams only (higher accuracy needed). |
| 5 | **n8n for workflow orchestration** | Custom Python cron scripts | Visual workflow editor, native webhooks, built-in error handling. The 3 memory workflows took 30 min to build vs estimated 4h in Python. |
| 6 | **PostgreSQL for everything** | SQLite + JSON files, or MongoDB | Relational model fits learner profiles perfectly. JSONB for flexible scores. pg_dump for reliable backups. No need for a second database. |
| 7 | **Cloudflare Zero Trust** | WireGuard VPN, Tailscale | Zero client config (WARP app), geolocation filtering (France only), free tier sufficient. Users just install WARP and connect. |
| 8 | **Self-hosted on Proxmox** | AWS/GCP/Vercel cloud | 0 EUR/month hosting. Full infrastructure control. Learning experience in itself. Trade-off: single point of failure (mitigated by 4-level backup). |
| 9 | **2-level memory system** | RAG on conversation history | Session snapshots (rolling summaries) + long-term profiles (pedagogical state). Simpler and more reliable than embedding search on chat logs. |
| 10 | **TTT pedagogy** | Free-form conversation, fixed curriculum | Test-Teach-Test gives structure without rigidity. Deterministic concept transitions ensure coverage. Students can still switch to free mode anytime. |
