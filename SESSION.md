# Sessions — AcademIA

Sessions empilées (plus récente en haut). Rotation : seules les **3 dernières** restent ici, les plus anciennes vont dans [`SESSION_ARCHIVE.md`](SESSION_ARCHIVE.md).

---
---

## Session 48 — 2026-04-25 (jour, ~5h45 continu, 18+ commits / 4 repos pushed — Migration Obsidian Phase 0a/0b/0c + 1 + 2 + 3 LIVRÉE + Claude-as-vault-cognition v0.1 architecturale)

### Done

**Migration Obsidian COMPLÈTE** — 4 phases massives en single session :

**Phase 0a sécurité (4/4 — base hardening)** :
- `~/.claude/settings.json` purgé (drop `defaultMode: auto` + `skipAutoPermissionPrompt: true` + wildcards `permissions.allow: ["*"]`). Source-of-truth enforcement permissions.deny désormais honorée.
- **Mistral key migration end-to-end** : ancienne clé compromise rotée + SOPS source `config.yaml.sops` migré vers `os.environ/MISTRAL_API_KEY` + container LiteLLM relauncher avec `-e MISTRAL_API_KEY` + smoke live HTTP 200.
- **rclone config encryption** : master pwd 32 random base64 dans `/opt/academie-shared/secrets/rclone-master-password` + `RCLONE_PASSWORD_COMMAND` env dans restic-backup.sh + restic-restore-test.sh + token gdrive rotation OAuth re-auth via Windows + verify end-to-end (4 snapshots accessibles).
- **Hardening cosmos** : `/etc/sysctl.d/99-hardening.conf` (kptr_restrict=2, ptrace_scope=2, rp_filter=1, syncookies, log_martians) + auditd installed/enabled + unattended-upgrades + `/etc/apt/apt.conf.d/20auto-upgrades`.

**Phase 1 Obsidian (foundations)** :
- Vault structure créée `/root/sinse-vault/` avec 5 folders Option C (projects/areas/resources/archive/meta) + `.gitignore` + `.stignore` + git init + GitHub repo `sinse-vault` privé + push initial.
- `sinse-tools` repo init `/root/sinse-tools/` + GitHub repo (sinse-tools- typo renamed via gh CLI) + push.
- `sinse-workspace-archive` rename via gh CLI (cohérent migration future).
- CLAUDE.md natifs déployés : `/opt/academie/CLAUDE.md` (project, 84 lignes) + `~/.claude/CLAUDE.md` (cross-project user-level, 56 lignes).
- Aliases bash : `claude-academie`, `claude-eisen`, `tmux-academie`, `tmux-eisen`.
- Memory mirror cron `/etc/cron.d/memory-vault-mirror` toutes 15 min : `rsync -a --delete /root/.claude/projects/-opt-academie/memory/ → /root/sinse-vault/meta/agent-memory/` + 16 files mirrored initial.
- Eisenday cloné `/opt/eisenday/` depuis github.com/Sinsemilila/Eisenday-app.
- Syncthing cosmos installed + service active + pairing devices laptop ↔ cosmos + folder shared `sinse-vault` bidir TLS Up to Date validé E2E.

**Wikilinks flip L128** (multi-agent research 5 agents, lock decision flip) :
- Research community + tooling 2025-2026 : token-cheaper Claude (3 vs 8-12 tokens/lien), MCP servers wikilink-native (jacksteamdev, cyanheads), bugs markdown documentés Obsidian staff (mobile/Android, unlinked-mentions, parent-paths).
- L97 (markdown links) → L128 (wikilinks default zéro exception). Settings Obsidian Windows : `Use Wikilinks ON` + `New link format = Shortest path when possible`.
- Tous fichiers vault wikilinks, simplification choix Sinse (anti-drift discipline manuelle).

**Phase 2-3 obsidian migration** (8 + 4 steps + Step 8.5 safety) :
- Backup pré-migration : restic snapshot `c2cd7070` (1.3 GiB tag pre-obsidian-migration-phase2) + git tags pre-phase2-migration sur 4 repos.
- Step 1 : 114 files AcademIA project docs `/root/sinse-workspace/projects/academie-ia/` → `/opt/academie/` (8 .md root + docs/ rsync 78 files merged into existing 41 = 119 total zero collision sur 00-project, 01-pedagogy, 05-decisions, 99-runbooks après merge + 4 sub-dirs historique archive/challenges/merge-requests/refactor-v1.0).
- Step 2 : 5 hardcoded refs critiques fixed (CLAUDE.md ligne 80, slash commands handoff/pickup paths, simulate_personas.py lignes 12+24, AGENTS.md projet drop, oracle/README.md:5 relative link).
- Step 3 : workspace meta → vault `resources/` (4 files: git-workflow, sinse-quickstart, file-protection, tools) + 3 ADRs workspace docs/decisions/ → `/opt/academie/docs/05-decisions/`.
- Step 4 : planning Obsidian → vault `projects/obsidian-migration/` (audit-phase0/ 9 files + 4 obsidian-*.md + roadmap-sinse + phase2-3-plan).
- Step 5 (CRITIQUE) : tools/ migration avec cron pause + symlinks recreate `/opt/academie-shared/scripts/` → `/root/sinse-tools/` + atomicity check 4/4 OK + restic-backup paths split staging Phase 2 (sinse-vault + sinse-tools UNIQUEMENT) vs Phase 3 (+ sinse-archive).
- Step 6-8 : cleanup workspace (AGENTS.md drop + tools/ rm) + commits + validation E2E.
- Step 8.5 PRÉ-rename safety audit : grep hardcoded refs critique `/etc/cron.d/`, code, slash commands → tous clean. TODO.md WIP paths fixed `/root/sinse-workspace/planning/` → `/root/sinse-vault/projects/obsidian-migration/`.
- Phase 3 : `mv /root/sinse-workspace/ /root/sinse-archive-2026-pre-vault/` + restic add archive path (Step 11 split staging) + final smoke 17/17 ALL CLEAR.

**Audit cohérence multi-agent (3 agents read-only, 18 findings)** :
- 5 critiques fixés : C1 cron pause systémique pendant Step 5 (race conditions), C2 restic paths split staging clarification, C3 Step 2 grep+sed concret, C4 Step 7/8 réordonnés (validation avant commits), C5 Step 8.5 PRÉ-rename audit safety.
- 8 importants fixés : I1-I8 (simulate_personas paths exact, AGENTS.md projet, oracle README link, time budget recalibré 4h → 4h40, backup cron file, Step 6 ordering, GEMINI.md dead symlink, symlinks atomicity).
- Locks ajoutés L130-L132 (cron pause systémique, restic split staging, audit hardcoded PRÉ-rename obligatoire).

**Architecture Claude-as-vault-cognition v0.1 LIVRÉE** (multi-agent research 4 agents) :
- Research patterns 2025-2026 : Karpathy LLM Wiki (pre-compiled summaries pas RAG), Eleanor Konik flow (inbox → knowledge promote), Anthropic effective-context-engineering, token economics Haiku 4.5 vs Opus 4.7 (5x cheaper), crossover 2K/10K/multi-turn.
- Two-tier slash commands :
  - **`~/.claude/commands/pickup.md`** (NEW user-level, workspace orientation léger ~3-5K tokens) : lit vault hot.md + log.md + INDEX.md + cosmos health + active projects status.
  - **`~/.claude/commands/project.md`** (NEW user-level, switcher avec args + dispatch vault-reader conditionnel) : `/project academia [task-hint] [--no-vault]`, deep load `/opt/<projet>/{CLAUDE,SESSION,TODO,docs/INDEX}.md` + détecte WIP TODO.md + dispatch Haiku si task identifié.
  - **`/opt/academie/.claude/commands/pickup.md`** DELETED (absorbé par /project).
  - **`/opt/academie/.claude/commands/handoff.md`** kept (project-specific finalize).
- **Custom agent `~/.claude/agents/vault-reader.md`** Haiku 4.5 : lit vault Obsidian + synthesize ≤300 tokens cross-projet knowledge. Format strict KEY POINTS / FILES READ / GOTCHAS / UNCERTAINTY (no preamble, hard limit). Économie ~74% tokens vs raw load Opus.
- Vault root files :
  - `vault/CLAUDE.md` (instructions Claude reading vault)
  - `vault/INDEX.md` (MOC racine — topic → file map, entry point retrieval)
  - `vault/hot.md` (500-word semantic snapshot — auto-overwrite par /handoff v0.2)
  - `vault/log.md` (chronological one-liner per session — auto-append par /handoff v0.2)
- Vault meta : `claude-conventions.md` (read/write zones, frontmatter, anti-patterns) + `cli-mapping.md` (inventory exhaustif Claude Code CLI cosmos — slash commands, custom agents, skills, CLAUDE.md hierarchy, settings, memory canonical, tools, status line, aliases, gaps).
- Vault knowledge seeds (3 patterns démontrent pattern) : `auth-patterns.md`, `dify-variable-wiring.md`, `n8n-workflow-history.md`.
- Vault empty zones : `inbox/`, `daily/` avec .gitkeep.
- CLAUDE.md natifs (project + user) référencent vault dispatch pattern + cross-references vers INDEX/conventions/cli-mapping.
- Vault project doc : `vault/projects/obsidian-migration/v0-claude-as-vault-cognition.md` doc canonical complet (vision, architecture, conventions, anti-patterns, roadmap v0.1→v0.3, indicateurs succès).
- Locks ajoutés L133-L135 (architecture two-tier, vault-reader Haiku custom, vault structure root + write zones).

**Side wins** :
- Workflow vault populated end-to-end visible Obsidian Windows (Sinse validé refresh Ctrl+R cache puis voit tout).
- Pre-push hooks fixed `/opt/academie/.git/hooks/pre-push` + `/root/sinse-workspace/.git/hooks/pre-push` (paths smoke-test old → /root/sinse-tools/).
- log tool `/root/sinse-tools/log` CHANGELOG path fixed (post-Phase 2 trouvé au /handoff).

**Métriques finales** : smoke deep 23/23 + smoke quick 17/17 + restic backup pushed `c2cd7070` 1.3 GiB + 18+ commits 4 repos (academia, sinse-vault, sinse-tools, sinse-workspace-archive) + 135 locks accumulés (L1-L135) + 9 documents canonical produced.

### Next

**Session 49 picks immédiats** :
- **Test E2E live workflow v0.1** (~10 min) : `claude` depuis SSH cosmos + `/pickup` (workspace orientation) + `/project academia` (deep load + dispatch vault-reader sur task hint si TODO.md WIP marker) + question test pour observer Haiku synthese fonctionne.
- **P0 Teacher EN structured output enum** (~30 min, untried option #1, bloque Phase 3 fault injection delta gating) : ajouter `feedback_type_intended: <enum excluding explicit_correction>` dans JSON schema → LLM declares type AVANT writing feedback. Target 24-26/26 si pink-elephant ne reapparaît pas.
- **B4 GlitchTip browser final test** (~15 min) : Ctrl+Shift+R sur academie.petit-pont.com + `Promise.reject(new Error('test'))` → vérifier event GlitchTip frontend Issues sous 30s. Pipeline serveur-side validé Session 47.

**Calendar 2026-05-07 (12 jours)** :
- DMARC `p=quarantine` flip via API CF zone-token (après 2 sem CSP collecte clean).
- CSP enforce flip dans `hooks.server.ts` (`Content-Security-Policy-Report-Only` → `Content-Security-Policy`).
- CF Email Routing setup `dsar@/security@/dmarc-reports@` (token CF account a perms, **modifies DNS MX + écrase SPF** → demande OK explicite avant exec).

**v0.2 Claude-as-vault-cognition** (~45 min, déclenchable post-test E2E v0.1 OK) :
- `/handoff` extension auto-writes : append `vault/daily/YYYY-MM-DD.md` (project, done, decisions, gotchas, commits) + overwrite `vault/hot.md` (regenerate 500-word snapshot) + append `vault/log.md` (one-liner) + drafts auto dans `vault/inbox/` si new patterns détectés.
- Mirror cron `/etc/cron.d/academia-state-mirror` toutes 15 min : `rsync /opt/academie/{SESSION,TODO,CHANGELOG}.md → /root/sinse-vault/projects/academia-ia/` (read-only mirror, source-of-truth /opt/academie).
- Si vault knowledge manque pour task récurrent → seed nouveau knowledge file.

**v0.3 future (post-mesure 2-4 semaines usage v0.1+v0.2)** :
- Top-10 skills keyword-routed si patterns émergent (auth, dify, n8n, svelte, etc.).
- Promotion pipeline `inbox/` → `knowledge/` (Sinse review process).
- MCP Obsidian server si vault > 200 notes (jacksteamdev ou cyanheads).
- Cache Anthropic prompt cache_control breakpoint pour stable docs.

**Pédagogie Phase 3-4** (post Teacher EN P0) :
- Phase 3 fault injection delta gating (~2h) : Session 42 O3 carryover, clean baseline + faulted run par scenario, gate sur `mean(delta) ≥ 0.4 AND false_positive < 0.20`.
- Phase 4 gate-strict flip : `RUN_RECENT_BATTERY.sh` block 8 `lint strict` → `lint + smoke strict`.

**Phase B AcademIA** (P2 mai-juillet, gros morceaux) :
- B2 Bits UI + shadcn-svelte (~2.5 sem, 18 composants headless).
- B3 Images + PWA Workbox (~1 sem, AVIF/WebP + Vite PWA).
- B5 Paraglide-JS i18n (~0.5 sem, quick win EN fallback).
- B6 Forms + motion + state (~1 sem, Superforms v2 runes).

**Manuel Sinse résiduel** :
- Signer DPA OpenAI ([platform.openai.com/account/data-processing-addendum](https://platform.openai.com/account/data-processing-addendum)) + Groq ([groq.com/dpa/](https://groq.com/dpa/)).
- Restic restore mensuel test E2E (jamais fait, J+30 audit).
- Cloudflare Notifications policies (DDoS + SSL expiring + Page Shield + Tunnel down).

### Gotchas

- **Pre-push hooks hardcoded paths** : `.git/hooks/pre-push` dans /opt/academie + /root/sinse-workspace référençaient `/root/sinse-workspace/tools/smoke-test`. Découverts au push final Phase 2 (smoke-test command not found). Fix sed → `/root/sinse-tools/`. Pattern : tout fichier `.git/hooks/*` n'est pas committed (config locale), reste sur cosmos seulement, doit être patché manuellement post-migration.
- **log tool `/root/sinse-tools/log`** ligne 37 hardcodait `/root/sinse-workspace/projects/academie-ia/CHANGELOG.md` (commit `e652bf3` fixé). Découvert au /handoff Session 48 close.
- **Syncthing folder rescan** : malgré `localFiles=49 globalFiles=50` post-migration, `phase2-3-obsidian-migration-plan.md` apparaissait pas dans Obsidian Windows Files panel. Cache Obsidian Windows. Fix `Ctrl+P → Reload app without saving`. Pattern : après migration vault content, toujours suggest reload Obsidian Windows.
- **Git "dubious ownership"** post-rename `sinse-workspace` → `sinse-archive-2026-pre-vault` : git refuse open repo car owner sinse vs current user root. Fix `git config --global --add safe.directory /root/sinse-archive-2026-pre-vault`. Pattern : si rename dossier git owned par autre user, ajouter safe.directory à toutes les operations git contre archive.
- **Subagent context loss anti-pattern** (audit cohérence research) : vault-reader Haiku ne voit pas le context conversation Opus, brief complete obligatoire dans dispatch prompt (OBJECTIVE, files to read, output format strict). "Lost in synthesis" : Haiku peut omettre détails CRITIQUES (line numbers, edge cases) si dispatch prompt vague. Mitigation : prompt strict + format KEY POINTS / FILES / GOTCHAS / UNCERTAINTY.
- **Auto-Dream conflict** Claude memory native rewrites memory en arrière-plan → vault `meta/agent-memory/` doit rester read-only mirror via cron 15 min (cohérent L9). Source-of-truth memory = `~/.claude/projects/-opt-academie/memory/`, jamais éditer côté vault.
- **Eisenday `/opt/eisenday/`** cloné mais .ai/ doc = doc-théâtre (audit L102 : 4 fichiers, 2 commits seulement 2026-04-02). NE PAS répliquer .ai/ pattern pour AcademIA (cohérent L110 flatten en CLAUDE.md natif + CHANGELOG.md projet).

---

## Session 47 — 2026-04-23 (jour, ~30 commits / 8 PRs main — Phase A 7/7 closed + 4 followups + Phase B1 design tokens + Phase B4 GlitchTip stack + UX nav + CF Access refactor)

### Done

**Phase A — 7/7 livré** (ferme la Phase A sécu de l'ADR-001) :
- **A6 RGPD docs + endpoints DSAR** — 4 runbooks compliance (DPIA, registre art.30, TIA Schrems II, minors-flow-roadmap) + AIBanner.svelte (AI Act art.50) + pages /legal/ia + /legal/mineurs + endpoints `/api/me/export-data` (13 sections incl. Dify conv via end_users.session_id) + `/api/me/delete-account` (hard delete cascade, retype confirmation, cookies cleared) + UI /settings/privacy modal 2-step + migration `users.age_attestation_at` + admin CLI 07. Flow consentement parental mineurs **différé post-beta publique** (cf. minors-flow-roadmap.md). Commits `cf74121`, `5fe775b`. PR #17.
- **A5 PII scrubber + cross-user isolation + rate-limit per-user + cost runaway** — module `app/security/pii_scrubber.py` (5 patterns regex EMAIL/PHONE FR/IBAN/NIR/CARD Luhn-validated), injection chat_router avant POST Dify ; `rate_limit.py` étendu `check_user(scope=user)` via cookie session, appliqué chat-send 100/60s + 3 consolidation 20-30/300s + onboarding 10/300s ; migration `model_usage_daily.user_id` (NULLS NOT DISTINCT PG 16) + LiteLLM callback forward `kwargs.user` → backend resolve user_id + endpoint `/api/admin/cost-runaway-users?window=24h|7d|30d` (top 20 + outlier flag 5×median) ; chat_router conv ownership check (Alice ne peut plus append à conv Bob via UUID guess) ; tests cross-user isolation (3 scénarios) + 23 pytest PII = **26 verts**. Commits `5103490`, `bc11b84`, `d381a72`, `a85563d`. PR #17.

**Phase A followups (4 items, ADR-001 §A) — closed** :
- **A1-cleanup** — DROP `active_sessions` (0 rows), retire `python-jose` + JWT keys (.env + .env.sops via SOPS round-trip), models orphelins, refactor `sprint6/_e2e_helpers.py` + tests obsolètes (NotImplementedError + docstring "needs cookie-session refactor"), Redis `appendonly yes` baked in via container recreate (DBSIZE=17 préservée via volume). Doc `a1-redis-aof.md`. Commits `4fce526`, `c374be5`. PR #18.
- **A4b polish** — Fernet at-rest TOTP (`TOTP_FERNET_KEY` env, backward-compat plain detection prefix `gAAAAA`, sinse 1 row migré ciphertext 140B confirmé), endpoint POST `/api/security/totp/regenerate-recovery-codes` (re-auth password + TOTP, rate-limit 3/h) + UI bouton modal, WebAuthn scaffolding (table `webauthn_credentials` + 4 stubs 501 derrière `WEBAUTHN_ENABLED=false` + UI placeholder "Passkeys bientôt"), force-reset 90j inactivité documenté TODO. Commit `f64ab5d`. PR #18.
- **A5.5 admin frontend card** — `CostRunawayCard.svelte` montée /admin (3 stats + tableau top 20 + flag rouge runaway + window 24h/7d/30d, mirror pattern JudgeBudgetBar). Commit `f29594f`. PR #18.
- **A6.3 minors flow naming** — "Phase B1" → "post-beta publique" dans 3 docs RGPD (ADR-001 réserve B1 = design tokens OKLCH). Commit `e7523aa`. PR #18.

**Phase B1 — Tokens OKLCH + state semantics + L2 serif font** (ADR-001 §B1, fondations visuelles) :
- 36 color tokens hex sRGB → OKLCH (perceptuellement uniformes, préparation B2 shadcn-svelte qui assume OKLCH ; visuellement identiques)
- 16 state semantic tokens (`success/warning/danger/info` × variants `-bg/-border/-text` ; text variants tunés contrast dark vs light)
- Source Serif 4 self-hosted (50KB latin Fontsource subset) + `--font-serif` token + preload `app.html` + ChatBubble.svelte prop `font="sans|serif"` → assistant messages des agents L2 (en/es/ja/de/it) en serif, user + agents code (pymentor/cybermentor) en sans
- Sweep palette → state tokens sur top 2 offenders : `chat/[agent]/+page.svelte` (31) + `settings/privacy/+page.svelte` (27) = 58/65. 6 fichiers restants en TODO opportuniste documenté.
- Doc référentiel `docs/99-runbooks/b1-design-tokens.md` (tokens table, anti-patterns, convention font, TODO migration, notes futures B2 oklch(from)+color-mix). Commits `1be27fa`, `21cff95`, `ee4c9f2`, `7371d8a`. PR #19.

**UX navigation fixes** (3 micro-fixes review sinse) — `/profile` ajout liens "🔐 2FA" + "🛡 Confidentialité" dans section Sécurité + retire Mentions légales doublon footer ; `/legal` nouvelle section "En savoir plus" liens vers /legal/ia + /legal/mineurs + /settings/privacy. Commit `ec98971`. PR #20.

**Phase B4 — GlitchTip self-hosted observability + bundle budget CI** (ADR-001 §B4) :
- Stack 3 containers : `glitchtip-web` v5.0 (uwsgi UI + API, 512M, port 127.0.0.1:8001), `glitchtip-worker` (celery+beat, 384M), `redis-glitchtip` (alpine 96M, broker dédié isolé du redis-academie). DB partagée `postgres-academie` (DB `glitchtip_db` créée). `.env.glitchtip` SECRET_KEY Django + EMAIL_URL=consolemail. Commit `8b5f3dd`. PR #21.
- Backend SDK `sentry-sdk[fastapi]==2.45` + init conditionnel sur `SENTRY_DSN_BACKEND`, FastApiIntegration + StarletteIntegration, `_scrub_pii` callback (drop cookies/csrf/auth headers + body si password/secret, user `<redacted>`), endpoint debug `/api/debug/sentry-test` (retiré post-validation). Commits `7c230b1`, `83e4f75`. PRs #21+22.
- Frontend SDK `@sentry/sveltekit ^10.49` + `hooks.client.ts` (init via `$env/dynamic/public` runtime, replays disabled privacy-first, beforeSend scrub) + `hooks.server.ts` étendu sequence(sentryHandle(), customHandle) + `vite.config.ts` plugin `sentrySvelteKit` sourcemaps upload skip alpha. Commit `afe03ff`. PR #21.
- CI workflow `.github/workflows/bundle-budget.yml` — trigger PR + push main sur `webapp/frontend/`, mesure 4 sections gzipped (entry/chunks/nodes/total), comment PR sticky avec table ✅/⚠️ vs budgets (entry≤80KB chunks≤500KB), warning-only. Commit `19a66fd`. PR #21.
- Doc runbook `b4-glitchtip-observability.md`. Commit `eaa1ac1`. PR #21.

**B4 followup — Dashboard public via Cloudflare Tunnel + Access** :
- Setup superuser + org `academie` + 2 projects (academie-frontend + academie-backend) via Django shell + DSN ajoutées à .env + .env.sops. Commit `f39e0d7` PR #23.
- DNS CNAME `glitchtip.petit-pont.com` → tunnel `proxmox-tunnel` UUID `a57431d7-...` (créé via API CF), tunnel ingress `→ http://192.168.1.181:80` (Cosmos host LXC), Cosmos route ajoutée dans `cosmos.config.json` (Host glitchtip.petit-pont.com → http://localhost:8001), GLITCHTIP_DOMAIN→https://glitchtip.petit-pont.com. **Refactor CF Access** : split de la dify wildcard app (qui couvrait dify+academie+n8n par accident, GOTCHA Session 46) en 3 apps dédiées (dify, academie, n8n). 2 apps bypass GlitchTip (`/api` Sentry SDK + `/_allauth` Django auth). Doc b4-glitchtip-observability.md mis à jour. PR #23.
- **Bug CF Access path-precedence** : la bypass app `academie/sentry-tunnel` ne prenait pas le pas sur l'app main academie quand browser POST avec cookies CF Access → 403 systématique. Pivot final : tunnel via FastAPI `/api/sentry-tunnel` (déjà couvert par CF Access cookie sinse) + extract sentry_key du DSN dans envelope first line + forward avec query param auth `?sentry_version=7&sentry_key=...`. **End-to-end validé autonomous** depuis le serveur (Issue "autonomous-test-final-from-claude" arrivé dans GlitchTip academie-frontend project). Commits `02a11a3`, `c24eb7e`, `e61cbab`, `7bdf1b4`. PRs #24, #25, #26, #27.

**Side wins** :
- **CF account API token** créé (`/opt/academie-shared/secrets/cloudflare-api-token-account`, perms Account Tunnel Edit + Access Apps Edit + Zone DNS Edit) → débloquera B6 Email Routing setup + futurs items CF.
- **asyncpg jsonb codec** registered globally (init=_register_jsonb_codec sur les 2 pools) — fix bug racine du "1010 codes" + recovery code path silently broken depuis A4 ship qui marche maintenant. Commit `acd9ae8` PR #18.
- Display fix `/settings/security` "10/10 codes" via `{@const}` dans `{#if}` (Svelte 5 parser sur `> 1` inline interpolation). Commit `57cdb00` PR #18.

**Métriques finales** : smoke deep 21/21 + 26 pytest verts + 8 PRs mergés sur main (#17→#27 sauf gaps).

### Next

**Session 48 picks** :
- **Phase B5 i18n Paraglide-JS 2** (~0.5 sem, quick win) : extraction strings UI dans messages JSON FR + EN fallback, routes /[lang]/. Investit pour anglophones futurs sans rien traduire encore.
- **Phase B2 Bits UI + shadcn-svelte** (~2.5 sem, gros morceau) : ~18 composants headless (Dialog, Combobox, Menu, Toast, Select, Checkbox, Radio, Tabs, Accordion, Popover, Tooltip, Toggle, Slider, Progress, Avatar, Badge, Card, Separator). Consume bien B1 tokens.
- **Phase B3 Images + PWA Workbox** (~1 sem) : `@sveltejs/enhanced-img` AVIF/WebP + audit `sw.js` hand-written → Vite PWA + Workbox.
- **A6 followup manuel sinse** : signer DPA OpenAI + Groq self-service ; Cloudflare Email Routing setup `dsar@/security@/parents@` (token CF account a maintenant les perms — mais nécessite OK explicite car modifie DNS MX + écrase SPF strict actuel).
- **B4 followup** : test browser-side capture final (Promise.reject avec Ctrl+Shift+R) — pipeline validé serveur-side, devrait juste marcher côté browser maintenant.
- **Phase A3 CSP** : flip `Content-Security-Policy-Report-Only` → enforce dans hooks.server.ts (jalon 2026-05-07, 2 sem collecte).
- **Pédago** : Session 46 P0 Teacher EN structured output enum constraint (~30 min + V8) toujours TODO. Maestro ES catchup différé.

### Gotchas

- **CF Access path-precedence cookie-based** : la doc CF dit "more specific path wins" mais en pratique, quand browser envoie cookies CF Access pour app A (broad), CF prioritise A sur app B (path-specific bypass). Workaround : tunnel via path déjà couvert par cookie existant (ex: /api/* covered by main app cookie de sinse, no bypass app needed).
- **Cosmos hardcode CSP enforce** sur tous les routes SERVAPP (`connect-src 'self'` parmi d'autres). `DisableHeaderHardening: true` + `SmartShield: false` + `ExtraHeaders.Content-Security-Policy: ...` n'override PAS — Cosmos rajoute son CSP par-dessus systématiquement. Solution : tunneler les requests via path same-origin qui passe le `'self'` (ex: /api/sentry-tunnel proxy backend → glitchtip-web internal).
- **GlitchTip ingest auth via query param ?sentry_key=...** : oublier ça → 403 silent. Le SDK Sentry l'ajoute auto, mais un proxy custom doit forward (extract sentry_key = DSN.username from envelope first-line JSON header).
- **academie-frontend container manquait `env_file: .env`** (oubli initial PR21) → `process.env.PUBLIC_SENTRY_DSN_FRONTEND` empty au runtime → SDK init no-op silent. Fix PR24. À garder comme template pour tout futur container SvelteKit qui veut env-injected runtime.
- **gh pr merge avec PR# erroné** échoue silencieusement et le code reste sur la branche → si tu vois "Already up to date" après merge de PR récent, vérifie avec `gh pr view N --json state` que c'est vraiment merged. Pattern safe : `PR=$(gh pr list --head <branch> --json number -q '.[0].number')` puis `gh pr merge $PR ...`.
- **`cfat_` token format** : nouveau format CF tokens (account-owned). Format ~50 chars avec préfixe `cfat_`. Le `/user/tokens/verify` endpoint dit "Invalid API Token" pour ces tokens → ne pas se fier à verify, tester l'endpoint réel qu'on veut utiliser.
- **Tunnel Cloudflare hostname conflict avec CNAME existante** : si on créé une CNAME via API puis qu'on essaie d'ajouter le hostname côté Tunnel UI/API, CF refuse "host already exists". Solution : delete CNAME via API d'abord, le tunnel hostname la recrée auto.

---

## Session 46 — 2026-04-23 (nuit, ~22 commits — Refactor 2026-H2 ADR-001 + Phase A : 6/7 items livrés)

### Done

**ADR-001 refactor complet 2026-H2 (sécu + design system + RGPD)** : roadmap 5-6 mois calendaires en 4 phases (A sécu / B fondations visuelles / C refonte pages / D auto-audit) avant beta privée fermée gratuite. Stack SOTA 2026 (Bits UI + shadcn-svelte + OKLCH + WebAuthn + GlitchTip self-hosted). Budget 0€ — toutes options payantes remplacées par alternatives gratuites. Parallélisation pédago 60/40. Pentest payant différé jusqu'aux premiers revenus. 7 décisions tranchées : JWT localStorage→sessions Redis, Cloudflare déjà en place, 5-6 mois validé, beta privée sans pentest, i18n UI Paraglide, mineurs flow consentement parental, MFA TOTP all users + WebAuthn phase 2. Doc `docs/05-decisions/ADR-001-refactor-complete-2026-H2.md` + entrée 18 dans `docs/decisions.md`. Commit `20a2baf`.

**Phase A — 6/7 items livrés** :

- **A7 Cloudflare DNS/SSL/HSTS/WAF/Cache/Page Shield/Bot Fight** — appliqué via API zone-token : SPF `v=spf1 -all` + DMARC `p=none` phase 1 + SSL Full strict + Always HTTPS + Min TLS 1.2 + TLS 1.3 + HSTS 1 an (no preload tant que A3 enforce stable) + Free Managed WAF Ruleset + Cache Rule `/_app/immutable/` + Bot Fight Mode (toi via dashboard). Page Shield découvert déjà actif. Rate limit `/api/*` reporté A5 backend (free tier = 1 règle prise par leaked credential check). Commits `4e7377b`, `1831ec6`.
- **A7a CI Dependabot + security-audit** — `.github/dependabot.yml` (pip+npm+actions+docker hebdo, groups minor-patch) + `.github/workflows/security-audit.yml` (pip-audit+npm audit+syft SBOM+Trivy fs scan). `dependabot_security_updates` + `vulnerability_alerts` activés via gh API. Commit `4e7377b`.
- **A3 CSP report-only + headers + collecteur** — middleware FastAPI étendu (COOP/CORP/Permissions-Policy 27 features), nouveau `security_router.py` POST `/api/csp-report` rate-limited 60r/min/IP, query-strings stripped, IP SHA256 daily-salted ; SvelteKit `hooks.server.ts` injecte `Content-Security-Policy-Report-Only` + COOP/CORP sur HTML pages, `connect-src wss + dify`, `frame-src dify + Turnstile`, `frame-ancestors 'none'`, `report-uri /api/csp-report`. Migration `csp_violations` + index + vue `csp_violations_24h`. Helper smoke test `scripts/sprint8/02_test_csp_endpoint.sh`. **Fenêtre collecte 2 sem ouverte** → flip enforce visé 2026-05-07. Commits `2222cb7`, `ed3b0d4`, `07ce9ef`.
- **A2 Argon2id silent rehash** — `passlib[bcrypt,argon2]` + `argon2-cffi 23.1.0`, `CryptContext(["argon2","bcrypt"], deprecated="auto", argon2__type="ID")`, `verify_and_rehash()` via `passlib.verify_and_update`, login flow UPDATE password_hash silent à la 1ère connexion réussie. **Validé end-to-end sur sinse** : hash passé `$2b$12$...` → `$argon2id$v=19$m=65536,t=3,p=4`. Commit `435abcc`.
- **A4 MFA TOTP backend + UI + admin enrolled** — `pyotp 2.9.0` + `qrcode[pil] 7.4.2` + module `totp.py` (RFC 6238 verify ±30s, recovery codes 10×10-char base32, hashed argon2id, nullify-in-place anti-reuse). 4 endpoints `/api/security/totp/{status,enroll-start,enroll-confirm,disable}`. Login flow 2-step : `/api/auth/login` retourne `{mfa_required:true, username}` si user has TOTP, `/api/auth/login-mfa` accepte TOTP code OR recovery code. Migration `user_totp` PK user_id. CLI `04_totp_enroll_admin.py` (QR ASCII terminal). UI SvelteKit `/login` step 2 + `/settings/security` (4 vues état-machine : not enrolled / in progress / recovery codes display / enrolled + disable). **Sinse enrôlé sur Aegis, recovery codes notés NordPass, login flow validé end-to-end.** Commits `69aba81`, `90f4e9c`, `50deb82`, `e536615`.
- **A1 Auth migration JWT→sessions opaques Redis + CSRF double-submit** — supprime la vulnérabilité XSS structurelle (JWT en `localStorage`). Module `webapp/backend/app/sessions.py` (Redis store, token urlsafe 48-byte + csrf_token 32-byte, sliding TTL 7j, reverse index `user_sessions:<uid>`, short_id sha1[:16]). `auth.py` : suppression JWT helpers, nouveau `get_current_user(request)` cookie-based. `main.py` : middleware `csrf_protect` (POST/PUT/PATCH/DELETE hors whitelist `login`+`login-mfa`+`csp-report`+`telemetry/onboarding-event` → header `X-CSRF-Token` == cookie `csrf_token` sinon 403). `auth_router.py` : login/login-mfa créent session Redis + set_cookie `as_session` (HttpOnly+Secure+SameSite=Lax) + `csrf_token` (visible JS), retournent `{user}` (no tokens body). Nouveau `/auth/logout` + `/auth/logout-all-sessions`. `/auth/refresh` supprimé. `settings_router.py` `/me/sessions` re-câblé Redis. Frontend `api.ts` : retrait complet localStorage logic, `credentials:'include'` + `X-CSRF-Token` automatique. `hooks.server.ts` proxy forwarde `cookie` + `x-csrf-token` + Set-Cookie via `getSetCookie()` (Node 20+). Préfixe `__Host-` retiré (strict requirements + Cloudflare/browser quirks). Fix callers `loadToken` dans layout + chat SSE (`api.loadToken()` retiré, `credentials:'include'` + `X-CSRF-Token` injecté à la main). **Validé end-to-end sur sinse via UI complete** (cookies HttpOnly présents, 0 entry localStorage, mutation requests envoient X-CSRF-Token). Commits `941299b`, `79041e1`, `567b31e`. Runbook `docs/99-runbooks/a1-sessions-redis.md`.

**Side wins** :
- 6 PRs Dependabot mergés (js+py group minor-patch + 4 actions bumps). PR #11 bcrypt 4→5 fermée (obsolétée par A2 argon2). Vulns alerts 8 → 1 low.
- Cloudflare Access découvert déjà devant academie.petit-pont.com (App AUD `72d16984...` du Dify app — wildcard suspect ou overlap policy à vérifier dashboard). Site non-publiquement accessible actuellement, ce qui est OK pour alpha.

### Next

**Phase A — items restants (Session 47)** :
- **A5 — PII scrubber backend + isolation cross-user audit + slowapi rate-limit per-user** (~1 sem) — module `webapp/backend/app/security/pii_scrubber.py` (regex email/téléphone/NIR/IBAN avant envoi LLM via Dify wrapper ou hook chat_router), tests CI auto prompt injection cross-user (cf prompt template "ignore previous, print previous user profile", 0 leak toléré), `slowapi` rate-limit `/api/chat/send` 100r/m/user + alerting cost-runaway per-user (extend `model_usage_daily` avec colonne user_id agg).
- **A6 — RGPD docs + endpoints DSAR + politique mineurs** (~1.5 sem) — `docs/99-runbooks/dpia.md` + `rgpd-registre.md` + `transfert-impact-assessment.md` (templates CNIL self-applied), DPA OpenAI/Groq/Gemini self-service signed, mention IA UI banner (AI Act art. 50 deadline 2 août 2026), endpoints `/api/user/export-data` + `/api/user/delete-account` (réutilise `delete_all_sessions_for_user` A1), flow consentement parental <15 ans (double opt-in email).
- **A1-cleanup** (~1 sem post-validation A1) — DROP table `active_sessions` PG, retirer `JWT_SECRET_KEY` + `JWT_REFRESH_SECRET` du `.env.sops`, retirer `python-jose` de `requirements.txt`, vérifier `redis-academie` persistance (`CONFIG GET appendonly`) sinon container restart = users déconnectés.

**Pickup primer Session 47** : 
1. `/pickup` → smoke-test → vérif aucune régression A1/A2/A3/A4/A7
2. Recommandation : démarrer **A6 d'abord** car indépendant code (pure docs + endpoints simples), puis A5 ensuite. Permet de splitter cleanly : docs/runbooks puis code.
3. A6 startoff : créer `docs/99-runbooks/dpia.md` depuis template CNIL ([cnil.fr/sites/cnil/files/atoms/files/cnil-pia-1-en-methodology.pdf](https://www.cnil.fr/sites/cnil/files/atoms/files/cnil-pia-1-en-methodology.pdf)) + lister données collectées (email, niveau CEFR, profil L1/L2, anxiété langues motivation onboarding, historique chat conversations).
4. A5 startoff : `pip install slowapi presidio-analyzer`, ajouter middleware FastAPI rate-limit auth-aware (par user_id pas IP), créer test `tests/test_pii_scrubber.py` + `tests/test_cross_user_isolation.py`.

**A4b polish** (post-Phase A immédiate) : régénération recovery codes UI, Fernet at-rest encryption secret TOTP, WebAuthn/Passkeys scaffolding, force-reset 90j inactivité.

**Phase B fondations visuelles** déclenchable en parallèle dès qu'un slot Phase A est complet.

**Pédago Session 46+** (parallélisable 60/40) : P0 Teacher EN structured output enum (~30 min + V8), Phase 3 fault injection delta gating, Maestro ES catchup.

**Manuel à toi** :
- DMARC bump à `p=quarantine` après 2 sem collecte clean (jalon 2026-05-07).
- A3 CSP analyse logs + flip enforce J+14.
- Cloudflare Access app config check (Dify wildcard suspect).
- Cloudflare Email Routing (security@ + dmarc-reports@ + dsar@) — token a perms mais nécessite OK explicite (modifie DNS MX + écrase SPF).
- Cloudflare Notifications policies (DDoS + SSL expiring + Page Shield malicious script + Tunnel down) — token a perms mais perdues lors d'un re-edit dashboard.

### Gotchas

- **Token Cloudflare edit dashboard buggy** : à chaque ré-édition pour ajouter une perm, le dashboard drop des perms account-level préalables (Access, Notifications). Conséquence : créer un nouveau token from scratch plutôt qu'éditer si on perd des perms.
- **Cloudflare Access devant academie.petit-pont.com** : tout curl externe → 403 Cloudflare Access (App AUD `72d16984...` qui matche dify app, suspect wildcard). Tests doivent passer par `127.0.0.1:3001` (frontend) ou `127.0.0.1:8000` (backend) avec `Host:` header bypass.
- **Push GitHub workflow file = scope `workflow` requis** : le token gh CLI n'avait que `gist,read:org,repo`. Refresh manuel via `gh auth refresh -h github.com -s workflow` (interactif, navigateur) — pas auto-élevable par moi.
- **SvelteKit response_model FastAPI** : un endpoint avec `response_model=TokenResponse` rejette tout dict alternative (ex `{mfa_required:true}`) avec ResponseValidationError 500. Solution : retirer le `response_model=` ou Union type.
- **pyotp version max = 2.9.0** (pas 2.10.x). Erreur catch sur build, fix `requirements.txt`.
- **Multi-line copy-paste dans terminal user** : casse les commandes longues (newline injecté). Toujours fournir des commandes monoligne ou des scripts helper.

---

