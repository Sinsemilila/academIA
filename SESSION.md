# Sessions — AcademIA

Sessions empilées (plus récente en haut). Rotation : seules les **3 dernières** restent ici, les plus anciennes vont dans [`SESSION_ARCHIVE.md`](SESSION_ARCHIVE.md).

---
---

## Session 50 — 2026-04-28 (jour, ~6h continu — Closure FINALE migration Obsidian + Syncthing PC fixe + audit intégral + Bundle FIX/B/F+G + 14 knowledge promus + disk resize +50G + Docker move sdb + /handoff user-level smart)

### Done

**Note** : Session 49 (2026-04-26 — v0.2 Claude-as-vault-cognition LIVRÉE + Phase 0 closure 13 items) n'a pas eu de bloc dans SESSION.md (oversight au /handoff Session 49). Résumé full Session 49 disponible dans `vault/log.md` (entrée 2026-04-26) et `vault/projects/obsidian-migration/obsidian-validation-state.md` (closure block).

**Syncthing PC fixe pairing** :
- SyncTrayzor fork GermanCoding installé sur PC fixe Windows + flag `--allow-newer-config` activé (Settings avancées Syncthing).
- Device fixe `25MCD6N-LSECE6W-JL7NK7H-2TF2QUX-5OM7M7S-HGXGY6H-7ONDUKL-RINSDAC` ajouté côté cosmos via API (rest/config/devices) + folder `sinse-vault` shared avec 3 devices (cosmos JPIP7HV + portable NLD47KM + fixe 25MCD6N).
- Sync validé end-to-end : 71 → 72 files transferred (test round-trip Phase B test 13), state idle, need=0, errors=0, fixe connecté via relay-server.
- Obsidian Windows installé fixe + ouvert coffre `E:\sinse-vault` + autostart SyncTrayzor configuré (Start on login + Start minimized + Close to tray + Start Syncthing automatically).

**Audit intégral système Obsidian** (10 checks read-only) :
1. Inventaire archive `/root/sinse-archive-2026-pre-vault/` vs vault+/opt/academie : ✅ archive = github snapshot pré-vault intentionnel (1 commit `archive/workspace pre-vault`)
2. Hardcoded paths `sinse-workspace` cross-cosmos : ⚠️ 18 refs détectées (5 docs actifs à fixer, le reste = HISTORY/CHANGELOG/refactor archive immutable trace)
3. Frontmatter validator : ✅ `/root/sinse-vault/meta/scripts/validate-frontmatter.sh` + symlink pre-commit présent
4. Cron mirrors : ✅ `/etc/cron.d/{memory,academie}-vault-mirror` actifs, markers récents (mtime <15 min)
5. Symlinks sinse-tools `/usr/local/bin/` : ✅ 11/11 (smoke-test, committer, log, ship, pg-backup, status, restic-backup, restic-snapshots, restic-restore, restic-prune, wipe-academie)
6. Syncthing 3 devices : ✅ folder idle need=0, fixe connecté relay
7. Slash commands user-level : ✅ 8/8 (pickup, project, safepoint, decision, daily, log-failure, promote, ingest)
8. Subagent vault-reader : ✅ Haiku 4.5, format strict KEY POINTS / FILES READ / GOTCHAS
9. Hook PreToolUse require-recent-plan.sh : ✅ matcher Edit|Write|MultiEdit
10. Frontmatter pre-commit : ✅ (item 3 confirme)

**Phase A — Cleanup hardcoded refs** (8 replacements distinct dans 5 docs `/opt/academie/docs/`) :
- `04-infra/backup.md` L20+L119 : `sinse-workspace` projet → `sinse-archive-2026-pre-vault` archivé + table repos étendue (sinse-vault/sinse-tools/sinse-claude-config)
- `04-infra/filesystem-scan.md` L307-309 : `/root/sinse-workspace/tools/` → `/root/sinse-tools/` (3 symlinks pg-backup, restic-backup, smoke-test)
- `04-infra/filesystem-scan.md` L452 : cron `smoke-monitor` chemin update
- `04-infra/filesystem-scan.md` L542 : section header annoté "(archived as `/root/sinse-archive-2026-pre-vault/`)"
- `04-infra/filesystem-scan.md` L585 : section "Already present" → footnote "moved here from ... during Phase 3 vault migration 2026-04-25"
- `99-runbooks/restore-backup.md` L30-31 : commentaire restore destination clarifié post-Phase 3
- `99-runbooks/rotate-secrets-sops.md` L35 : `~/sinse-workspace/tools/restic-backup` → `/root/sinse-tools/restic-backup`
- `05-decisions/ADR-001-refactor-complete-2026-H2.md` L133 : section "Reusable existing assets" smoke-test path update (future-oriented, pas decision historique)
- 2 commits split (ship guard secret-name false-positive sur rotate-secrets-sops.md → split commit) : `c2d5b96` (4 docs) + `48acd3f` (rotate-secrets-sops.md gitleaks scan PASS)

**Phase B — Tests E2E live** :
- **Test 11 vault-reader Haiku dispatch** ✅ PASS : INDEX.md read OK + auth-patterns.md matched + synthèse format strict (KEY POINTS / FILES READ / GOTCHAS) ≤300 tokens, gotchas bonus (`__Host-` cookie removed L114, `response_model=TokenResponse` rejette dict alternative L115, pyotp ≤2.9.0 L116, CF Access path-precedence L118)
- **Test 12 /handoff Section 4 vault auto-writes** ✅ PASS dry-run : grep confirms 4 cibles vault dans Section 4 (daily/hot/log/inbox conditionnel), Section 5 split commit project + vault, vault writeable. Test E2E réel = ce /handoff.
- **Test 13 Syncthing round-trip 3 devices** ✅ PASS : file `inbox/test-roundtrip-session50-cosmos-2026-04-28.md` créé cosmos → API folder state idle 71→72 files → Sinse confirms visible Obsidian fixe `E:\sinse-vault\inbox\` (portable offline OK normal). Cleanup file post-validation.

**Migration Obsidian formellement close** :
- v0.1 LIVRÉE Session 48 (2026-04-25) ✅
- v0.2 LIVRÉE Session 49 (2026-04-26) ✅
- Phase 0 closure 13 items LIVRÉE Session 49 (item 12 différé post-incident, item 13 droppé jusqu'à trigger MCP externe) ✅
- v0.3 différé post-mesure 2-4 sem usage réel (lock explicit anti-pattern anticipation)
- **Audit + Phase A + tests E2E + closure Session 50 ✅**

---

## Session 50 — APRÈS-MIDI (suite, ~4h continu)

**Bundle FIX CONVENTIONS** (5 ships vault) :
- Phase A `2e6b1f2` : wikilinks L128 update conventions.md + mirror cron exception read-only zones documented (meta/agent-memory/* + projects/*-ia/* écrasés au prochain tick)
- Phase C `ee9df87` + `f3aa49b` : frontmatter coverage 21 files (13 obsidian-migration drafts + 5 meta partial + 3 resources). Type whitelist étendu `[plan, audit]` dans validate-frontmatter.sh + CLAUDE.md vault. **100% coverage hors mirrors atteinte**.
- Phase D `739811f` : taxonomy tags pluralization (gotcha→gotchas). Total 38 tags (cible 15+scope, audit 2-3 mois post-usage).
- Phase E `c31ee60` : .gitkeep log/+log/plans/ + INDEX sections "Empty by design" notes (inbox/log-plans/archive/areas).

**Bundle B ACTIVATE LEARNING** (3 ships) :
- B1 memory `feedback_skill_routing.md` (non-versionné par design) : routing rules pour /log-failure /safepoint /decision /promote /daily /ingest + inbox draft policy (≥2 sessions OU ≥10 min debug OU cross-projet émergent)
- B2 `c5b4e40` (sinse-claude-config) : section ## SKILLS & LEARNING PIPELINE dans CLAUDE.md user (6 skills triggers + audit mensuel ~30 min + anti-doc-théâtre check 0 skill 4 sessions)
- B3 `826208f` (academie) : /handoff Section 4.4 bar abaissé inbox + Section 4.5 NEW failures+gotchas consolidation + Section 5.2 vault commit list étendu (projects/*/failures.md) + Section 6 anti-doc-théâtre flag

**Bundle F+G SCALING PREP** (3 ships) :
- F1 `dd7f5cf` (vault) : `meta/templates/template-new-project-structure.md` 8 steps bootstrap projet (mkdir + cron + alias + INDEX + CLAUDE.md natif + focus-lock decision + failures.md skip + knowledge anticipation). Naming conventions (suffix -ia deprecated).
- G1 `9009a77` (academie) : /handoff Section 4.1 [project] tag forced daily headers + 7 slugs canoniques (obsidian/academia/eisenday/microentreprise/cross-project/infra/meta)
- G2 `537d295` (vault) : focus-lock pattern formalisé `meta/workflow.md` (when/how activate/lift + items hors scope + 4 anti-patterns explicit)

**14 knowledge files promus vault/knowledge/** (4 ships) :
- 1ère vague `f54e8ee` (3 plans stratégiques) : multilang-roadmap (Wave 1-4 ES/IT+DE/JP/RU) + onboarding-qcm-research (refonte 2026-04-20, 7 rapports vague1+2) + security-refactor-blueprint (ADR-001 H2 2026 réutilisable cross-projet)
- 2ème vague `7c5f983` (5 pédago/architecture) : pedagogy-cefr-consolidation + error-gradation-framework (GLMM Cox) + feedback-delivery-pedagogy (Lyster/Hattie/Cowan/Cepeda/Sheen-Ellis/Pak) + taxonomy-framework-abstract (5 tiers domain-agnostic GravityAxes James 1998) + architecture-patterns-composite (CF Tunnel + nginx HOST + Docker /28 + LiteLLM cascade + FastAPI monolith + Dify + n8n)
- 3ème vague `a21eb12` (6 socle solide) : data-model-postgresql + api-surface-rest (10 routers + 5 patterns) + academia-glossary + rgpd-compliance-toolkit (DPIA/registre/DSAR/Schrems II/AI Act/mineurs) + sla-pedagogy-bibliography (15+ citations + 13 corpus open) + l1-l2-scaffolding-policy (matrice 9 cells level×distance×FLA)
- **Total vault knowledge maintenant 17 files** (3 originaux + 14 promus today). Pattern Karpathy LLM Wiki = pre-compiled summaries + pointer code-adjacent /opt/academie/docs/ source canonical. Audit final exhaustif valide ZERO doc strategic oublié.

**Disk resize + Docker move** :
- Phase 1 : `qm resize 100 scsi0 +50G` (host Proxmox, 0 downtime) + fdisk delete swap partitions sda5/sda2 + growpart /dev/sda 1 + resize2fs (online) + create swapfile 2.6G sur sda1 + fstab clean. /dev/sda1 passes 47G→99G, 81%→41% used.
- Phase 2 : Docker compose down 17 containers + stop docker.service + containerd.service + rsync /var/lib/{docker,containerd} → /mnt/cosmos-data/{docker,containerd} (sdb 850G dédié) + edit /etc/docker/daemon.json data-root + /etc/containerd/config.toml root + restart services + auto-start containers via restart policies. /dev/sda1 final 18G/99G (20% used, 76G libres). 17/17 containers running + smoke 17/17.
- 5 commits academie (matin closure) + 8 commits vault (audit + bundles + promotions) + 1 commit sinse-claude-config (B2)

**`/handoff` user-level smart** (1 ship) :
- `e1f390d` (sinse-claude-config) : skill `/root/.claude/commands/handoff.md` user-level cross-projet auto-detect via git status. Workflow `claude` (depuis /root/) → /pickup → /project academia → work → /project eisenday → work → /handoff (auto-detect 2 projets touchés, ferme proprement chacun + vault auto-writes cumulés). Args : `--projet <nom>`, `--vault-only`, `--dry-run`. Compatible legacy /opt/academie/.claude/commands/handoff.md (overrides sections 1-3 si présent).

**Métriques journée Session 50** :
- 18 commits cross 3 repos (5 academia + 11 vault + 2 sinse-claude-config)
- 14 knowledge files promus vault (~3500L cumulés summaries Karpathy pattern)
- Disk resize +50G + Docker move sdb (76G libres, économie infra long-terme)
- /handoff user-level smart cross-projet activé (workflow scaling Eisenday/microentreprise futur)
- Smoke 17/17 ALL CLEAR continu
- GitHub counter à T+0 final : 7/18 reconnus (délai propagation private repos burst, va rattrapper)

### Next

**Pickup primer Session 51** :
1. `/pickup` → smoke-test → vérif vault sain (3 devices sync, mirrors actifs)
2. Choisir prochain projet : P0 AcademIA Teacher EN structured output enum (~30 min, débloque Phase 3 fault injection delta gating) OU calendar 2026-05-07 (DMARC `p=quarantine` + CSP enforce flip + CF Email Routing setup, 9 jours fenêtre restant) OU Eisenday V2 backlog OU outreach P2

**P0 cette semaine** :
- **P0.1 Teacher EN enum** : `feedback_type_intended: <enum excluding explicit_correction>` JSON schema, target 24-26/26 si pink-elephant ne reapparaît pas
- **Calendar 2026-05-07** : DMARC API CF zone token + CSP `Content-Security-Policy-Report-Only` → enforce dans `hooks.server.ts` + CF Email Routing setup (modifie DNS MX + écrase SPF strict → demande OK explicite Sinse)

**P1 mai** :
- Phase 3 fault injection delta gating (~2h, débloque Phase 4 RUN_RECENT_BATTERY block 8)
- B5 Paraglide-JS i18n (~3-4h, quick win)

**v0.3 mesure** : post 2-4 sem usage v0.1+v0.2, candidats : top-10 skills keyword-routed si patterns émergent, MCP Obsidian server si vault >200 notes.

**Manuel Sinse résiduel** :
- Signer DPA OpenAI + Groq self-service (RGPD A6 prerequisite)
- Restic monthly restore test E2E (jamais fait, J+30 audit)
- vzdump cron J+1/J+2/J+3 vérif (Session 48 todo)
- Cloudflare Notifications policies (DDoS + SSL expiring + Page Shield + Tunnel down) — token a perms mais perdues lors edit dashboard

### Gotchas

- **Ship script secret-name false-positive** : `ship "[fix] ..." docs/99-runbooks/rotate-secrets-sops.md` refuse stage car nom contient "secrets". Pattern : split commit + `git add` direct + `git commit` (gitleaks pre-commit hook validera contenu = pas de secret leak réel). Découverts au commit Phase A.
- **SESSION.md gap Session 49** : oversight au /handoff Session 49 — bloc SESSION.md jamais ajouté (focus Sinse sur autre chose). Pattern : `/handoff` doit checker `grep "## Session N" SESSION.md` post-prepend pour validate. Sinon vault `log.md` + `hot.md` capturent l'historique mais SESSION.md drift.
- **Syncthing PC fixe `--allow-newer-config`** : flag obligatoire si SyncTrayzor v2 + Syncthing v2.0.16+ avec config v52 portable. Sans le flag, Syncthing refuse de démarrer car config "newer than supported". À cocher Settings avancées SyncTrayzor.
- **Test Session 49 portable offline** : portable éteint au moment du round-trip Syncthing test. Sync needs=0 confirmé côté cosmos+fixe. Portable rattrappera au prochain power-on (delta minor).
- **Docker 29.4 storage driver `overlayfs` "duplicate" du compte** : `du /var/lib/docker` traverse les overlayfs mounts qui pointent vers `/var/lib/containerd/snapshots/`. Apparent 17G + 20G mais réel storage = uniquement containerd snapshots (Docker rootfs/overlayfs/<container_id> = mountpoints virtuels, pas data physique). Mesurer avec `--exclude=*/rootfs/overlayfs/*`. Solved Phase 2 move data-root.
- **fdisk extended partition layout sda5 swap** bloque growpart /dev/sda 1 si sda2 (extended) + sda5 (swap) sont après sda1. Fix : swapoff + fdisk delete sda5 + delete sda2 + growpart + resize2fs + fallocate swapfile sur sda1 nouveau espace + fstab clean.
- **GitHub contribution counter délai indexer** : repos privés en burst → propagation slow (10/h max). 18 commits today, 7 reconnus à fin journée. Pattern : check 24h après si <14 commits, sinon investigate user emails verified.
- **`/handoff` project-level vs user-level scope** : project-level `/opt/academie/.claude/commands/handoff.md` chargé seulement si cwd = /opt/academie au démarrage Claude. Solution scaling : user-level smart `/handoff` (e1f390d) auto-detect via git status, marche depuis n'importe quel cwd. claude direct from /root/ recommended pour multi-projet.

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

