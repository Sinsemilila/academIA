---
summary: "Known issues, traps, workarounds, and things that break"
read_when: "Debugging unexpected behavior, or before making infrastructure changes"
---

# Gotchas — AcademIA

## Dify

- dify-plugin-daemon was unstable, self-stabilized 2026-04-04. Don't restart unless needed.
- dify-sandbox required for Jinja2 in LLM code nodes. Deployed 2026-04-05.
- dify-api/dify-worker recreated with ADMIN_API_KEY_ENABLE=true.
- sys.user_id in Chatflow = UUID of connected Dify account, NOT a username.

## LiteLLM

- Groq rate limits: groq-standard (Llama 3.3 70B) can 429 under load. Fallback: mistral-small.
- CJK: groq-standard and groq-snapshot do NOT support CJK. Use groq-qwen for Japanese.
- Gemini: free quota exhausted without billing enabled (~10 req/day max).

## PostgreSQL

- Password: stored in `/opt/academia-shared/secrets/` — never commit in clear
- PG data on /mnt/cosmos-data/postgres/ (bind mount, 850G disk, separate from boot).
- Dump restore: "already exists" errors on constraints are normal and harmless.

## Webapp

- Cloudflare Zero Trust: policy changed from Allow (email OTP) → Bypass (require WARP + France). No more login screen.
- profil_manager.py: tested and functional (save_profil + get_profil + format_profil_for_injection).

## Infrastructure

- Boot disk (50G): was 83% full before S1. Freed ~9.5G via docker builder prune. Monitor with smoke-test --infra.
- Data disk (850G): /mnt/cosmos-data/, 99% free. PG data + backups stored here.
- 2 physical SSDs in Proxmox: boot SSD (119G) + storage SSD (932G). Vzdump backups on boot SSD = different disk from VM.

## n8n

- n8n encryption key: if lost, ALL workflows become unreadable. Triple-stored in secrets.
- Access UI requires SSH tunnel: ssh -L 5678:127.0.0.1:5678 cosmos

## Secrets

- .dify_admin_key and encryption.key migrated to /opt/academia-shared/secrets/ with symlinks (S2.1, 2026-04-12).
- Claude native memory had ADMIN_KEY in clear — replaced by reference.
