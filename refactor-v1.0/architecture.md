# Architecture — AVANT / APRÈS

> Vue complète de la transformation workflow/workspace entre l'état pré-refactor et le design v1.0.

---

## 1. État AVANT le refactor

### 1.1 Structure fichiers

```
/root/sinse-workspace/                  ← repo git, une seule branche "claude"
├── .gitignore
├── .lock                                ← claude:<timestamp> (sera supprimé D20)
└── context/
    ├── CLAUDE.md (172 lignes)          ← projet-specific, dupliqué avec /opt/academia/CLAUDE.md
    ├── conventions.md (75 lignes)       ← règles workflow, à fusionner dans AGENTS.md
    ├── GEMINI.md (8 lignes)             ← pointer minimaliste
    ├── STATE.md (81 lignes)
    ├── TODO.md (57 lignes, format P1-P5)
    ├── HANDOFF.md (94 lignes, 1 unique)
    ├── CHANGELOG.md (157 lignes, append-only)
    ├── DECISIONS.md (76 lignes, append-only, 70+ entrées)
    ├── fin.md (16 lignes, slash command existant)
    └── claude-settings.json             ← hook Stop (rappel git commit)

/opt/academia/                           ← projet academie-IA (prod)
├── .claude/
│   ├── commands/fin.md                  ← slash command existant
│   ├── settings.json                    ← hook Stop (dupliqué)
│   └── settings.local.json              ← permissions Claude Code
├── .gemini/
│   └── commands/fin.toml                ← slash command Gemini
├── .dify_admin_key                      ← SECRET en clair (à migrer)
├── CLAUDE.md (172 lignes)                ← DOUBLON de context/CLAUDE.md
├── api/                                 ← FastAPI backend Python
├── curriculums/                         ← data pédagogique
├── scripts/ (26 scripts Python)         ← ad-hoc, non CLI-fiés
└── webapp/                              ← SvelteKit frontend + FastAPI backend

~/.claude/projects/-opt-academie/
└── memory/
    └── reference_dify_api.md            ← CONTIENT ADMIN_KEY EN CLAIR (faille sécurité)
```

### 1.2 Outillage actuel

| Composant | État |
|-----------|------|
| Claude Code CLI | ✅ v2.1.101 installé |
| Gemini CLI | ✅ v0.36.0 installé |
| Codex CLI | ❌ Non installé |
| Bash tools maison | ❌ Aucun |
| Slash commands custom | ⚠️ 1 seul (`/fin`) |
| Git hooks | ⚠️ Hook Stop seul (rappel commit) |
| Pre-commit anti-secrets | ❌ Aucun |
| Pre-push validation | ❌ Aucun |
| Backups automatisés | ❌ Git seul |
| Worktrees | ❌ Non utilisés |
| YOLO mode (`--dangerously-skip-permissions`) | ❌ Non activé |

### 1.3 Problèmes structurels

1. **CLAUDE.md dupliqué** : 2 fichiers quasi-identiques (workspace + projet), ~340 lignes cumulées
2. **Monolithique** : toute la doc projet dans un seul fichier CLAUDE.md, lu à chaque session
3. **Mono-IA** : tout le tooling assume qu'une seule IA bosse à la fois
4. **Pas de filet de sécurité** : aucun backup automatisé, aucun test de restore
5. **Pas d'auto-merge** : chaque merge vers main demande intervention humaine de Sinse
6. **Pas d'outillage workflow** : scripts Python ad-hoc difficiles à découvrir et utiliser
7. **Secret en clair** : `.dify_admin_key` dans `/opt/academia/`, ADMIN_KEY dans memory native Claude
8. **Pas de protection anti-erreur** : un `git add .` ou un `rm -rf` mal placé peut tout casser

---

## 2. État APRÈS le refactor (v1.0)

### 2.1 Structure fichiers cible

```
/root/sinse-workspace/                  ← repo workflow tracked git, pushed GitHub
├── AGENTS.md                            ← canonical workflow rules (télégraphique EN)
├── docs/                                ← workflow docs cross-project
│   ├── git-workflow.md                  ← (à créer en S2)
│   ├── multi-ia-collaboration.md        ← (à créer en S2)
│   └── sinse-quickstart.md              ← (français, exception D13, créé S2)
├── tools/                               ← 15 bash tools maison (fichiers ROUGES)
│   ├── cly                              ← wrapper Claude avec window title
│   ├── committer                        ← safe commits avec guardrails
│   ├── arbiter                          ← cross-review IA via claude/gemini CLIs
│   ├── docs-list                        ← walk docs/ + YAML front-matter
│   ├── smoke-test                       ← health check modulaire (quick/deep/infra/all)
│   ├── status                           ← dashboard multi-IA (S3)
│   ├── deploy-teacher                   ← wrapper chatflow update
│   ├── pg-backup                        ← dumps PG horaires
│   ├── restic-backup                    ← offsite Google Drive
│   ├── log                              ← append CHANGELOG avec type
│   ├── install-slash-commands           ← sync source → ~/.claude + ~/.gemini
│   ├── init-worktree                    ← bootstrap nouveau worktree (D37 G3)
│   ├── merge-to-main                    ← auto-merge orchestrator (Option E)
│   ├── merge-approve                    ← approve MERGE-REQUEST
│   ├── merge-reject                     ← reject MERGE-REQUEST
│   └── rollback-to                      ← safe rollback via git revert
├── slash-commands/                      ← source tracked
│   ├── pickup.md                        ← template télégraphique EN
│   └── handoff.md                       ← idem
└── projects/
    └── academie-ia/                     ← state projet spécifique
        ├── PROJECT.md                   ← short overview + pointers
        ├── STATE.md                     ← état global (updated at merge-to-main)
        ├── TODO.md                      ← format CLAIMED
        ├── HANDOFF-claude.md            ← 1 par IA
        ├── HANDOFF-gemini.md            ← futur
        ├── CHANGELOG.md                 ← append-only [type] prefixes
        ├── DECISIONS.md                 ← append-only
        ├── AUDIT-TODO.md                ← squelette audit post-refactor (D37 G10)
        ├── merge-requests/              ← MERGE-REQUEST.md pending
        │   └── archive/                 ← approved/rejected
        ├── docs/                        ← 6 docs projet (read_when:)
        │   ├── infra.md                 ← Docker + nginx + Cloudflare + PG + LiteLLM
        │   ├── dify-teacher.md          ← Dify + Teacher v17 chatflow
        │   ├── n8n-workflows.md         ← 5 workflows + memory system
        │   ├── webapp.md                ← FastAPI + SvelteKit + users
        │   ├── pedagogy.md              ← TTT + taxonomies A1→C2
        │   └── gotchas.md               ← notes importantes + pièges
        ├── archive/                     ← REFACTOR-PLAN-working.md (post-v1.0)
        └── refactor-v1.0/               ← CE DOSSIER (plan stabilisé)

/opt/academia/                           ← prod, branche main (code inchangé)
├── (code webapp, api, scripts) ← D3 règle d'or "Code produit intact"
└── AGENTS.md                            ← pointer: READ /root/sinse-workspace/AGENTS.md + ...

/opt/academia-worktrees/                 ← NOUVEAU
├── claude/                              ← worktree branche claude
│   ├── .agent                           ← "claude"
│   ├── AGENTS.md                        ← pointer vers /root/sinse-workspace/AGENTS.md
│   └── .claude/settings.local.json      ← permissions worktree-spécifiques
├── gemini/                              ← futur (S3)
└── codex/                               ← futur lointain

/opt/academia-shared/                    ← NOUVEAU
└── secrets/
    ├── dify-admin-key                   ← migré depuis /opt/academia/.dify_admin_key
    ├── n8n-encryption-key               ← migré depuis /opt/n8n/encryption.key
    ├── restic-passphrase                ← NOUVEAU (D37 G1)
    ├── google-drive-credentials         ← NOUVEAU (Restic backend)
    └── ... (liste exhaustive en S2.1.5)

~/.claude/commands/                      ← USER-LEVEL (installés par install-slash-commands)
├── pickup.md
└── handoff.md

~/.gemini/commands/                      ← USER-LEVEL
├── pickup.toml                          ← converti depuis markdown
└── handoff.toml

/opt/backups/postgres/                   ← NOUVEAU (D1 niveau 2)
├── 2026-04-12_00.sql.gz
├── 2026-04-12_01.sql.gz
└── ... (rétention 24h + 7d + 4w)

~/.claude/projects/-opt-academie/memory/
└── reference_dify_api.md                ← secret remplacé par référence (D35 35A)
```

### 2.2 Outillage cible

| Composant | État v1.0 |
|-----------|-----------|
| Claude Code CLI | ✅ v2.1.101 (abonnement Claude Pro/Max de Sinse) |
| Gemini CLI | ✅ v0.36.0 (abonnement Gemini Advanced de Sinse) |
| Codex CLI | ⏳ À installer si/quand Sinse ajoute ChatGPT Plus |
| Bash tools maison | ✅ **15 tools** |
| Slash commands custom | ✅ `/pickup` + `/handoff` (télégraphique EN) |
| Git hooks | ✅ Hook Stop + pre-commit gitleaks + pre-push smoke-test |
| Backups automatisés | ✅ **4 niveaux** (Proxmox + PG + Restic/GDrive + Git) |
| Test restore validé | ✅ Obligatoire avant activation YOLO |
| Worktrees | ✅ 1 actif (claude), 1-2 prévus (gemini, codex futur) |
| YOLO mode | ✅ Activé post-S1 (backup garanti) |
| Auto-merge | ✅ Option E (12 types + fichiers protégés + seuils + arbiter) |
| Rollback safe | ✅ Tool `rollback-to <tag>` |

---

## 3. Tableau de changements critiques

| Domaine | AVANT | APRÈS | Décision |
|---------|-------|-------|----------|
| **Documentation workflow** | CLAUDE.md monolithique dupliqué | AGENTS.md canonical + pointers | D8, D12, D13, D14 |
| **Documentation projet** | Tout dans CLAUDE.md | 6 fichiers avec `read_when:` | D16, D37 G4 |
| **TODO format** | Priorités P1-P5 | OPEN / CLAIMED / DONE | D17 |
| **HANDOFF** | 1 fichier unique | 1 par IA (HANDOFF-<agent>.md) | D18 |
| **CHANGELOG** | Format libre | `[type]` prefix + 12 types | D19, D27 |
| **Lock file** | `.lock` actif | Supprimé | D20 |
| **Backup** | Git seul | 4 niveaux + test restore | D1, D22 |
| **Commits** | `git commit` direct | `committer` bash tool avec guardrails | D10, D25, D30 |
| **Multi-IA** | Même dossier | Worktrees séparés + branches + arbiter | D2, D28 |
| **Auto-merge** | Manuel 100% | Option E : 12 types + fichiers protégés + seuils | D27, D30, D31, D32 |
| **Rollback** | `git revert` manuel | Tool `rollback-to <tag>` safe | D34 |
| **YOLO mode** | Non | `--dangerously-skip-permissions` activé post-backup | D22 (sous-produit) |
| **Secrets** | En clair dans `/opt/academia/` | Migrés dans `/opt/academia-shared/secrets/` | D37 G6 |
| **Langue fichiers .md** | Français | Anglais télégraphique | D13 |
| **Slash commands** | `/fin` seul | `/pickup` + `/handoff` (P2 placement) | D33 |
| **LLMs workflow** | N/A | Claude/Gemini CLIs abonnements Sinse | D28, D29 |
| **LLMs projet** | LiteLLM + Groq/Mistral | **Inchangé** (séparation stricte) | D29 |

---

## 4. Flux d'un merge classique (Option E)

```
[AI edits files in worktree /opt/academia-worktrees/claude/]
    ↓
[committer "[type] message" file1 file2 ...]
    ↓ (committer bash tool)
[git commit created]
    ↓
[pre-commit hook: gitleaks → blocks if secret]
    ↓ (if pass)
[AI runs /handoff]
    ↓
[/handoff executes:]
  1. smoke-test --deep
  2. Update STATE.md, TODO.md, CHANGELOG.md, DECISIONS.md
  3. Write HANDOFF-claude.md
  4. committer "[type] handoff message" context_files
  5. git push origin claude
       ↓
       [pre-push hook: smoke-test --deep → blocks if fail]
       ↓
  6. merge-to-main
       ↓
       [Check files touched → ROUGE? ORANGE? VERT?]
       ↓
       ┌─ All GREEN + auto-merge type → AUTO_MERGE
       │    ↓
       │  [git merge claude + tag deploy-YYYY-MM-DD-HHMM + push main]
       │    ↓
       │  Output: "✅ Handoff complete + auto-merged"
       │
       ├─ All GREEN + [fix/refactor/perf] under threshold → AUTO_MERGE
       │    ↓ (same as above)
       │
       ├─ ORANGE touched OR [feat]/[hotfix] OR over threshold → ARBITER
       │    ↓
       │  [arbiter --branch claude --type <type>]
       │    ↓ (calls gemini -p for cross-review)
       │    ↓ Returns DECISION: GO / NO-GO
       │    ↓
       │    ├─ GO → auto-merge + tag
       │    └─ NO-GO → create MERGE-REQUEST.md + stdout alert + exit
       │
       └─ ROUGE touched OR [security]/[remove]/[wip] → HUMAN_REQUIRED
            ↓
          [create MERGE-REQUEST.md in projects/academie-ia/merge-requests/]
            ↓
          [stdout: "🔴 MERGE REQUEST requires your approval"]
            ↓
          [exit 1 — AI returns to Sinse]
            ↓
          Sinse reviews and runs:
            - merge-approve claude → auto-merge + tag
            - merge-reject claude --reason "..." → archived
```

---

## 5. Flux d'un rollback urgent

```
[Sinse discovers bug in production after last merge]
    ↓
[Sinse finds the last known good deploy tag]
  git tag --list "deploy-*" | tail -5
  → deploy-2026-04-12-1800 (last known good)
  → deploy-2026-04-12-2000 (current, broken)
    ↓
[Sinse runs:]
  rollback-to deploy-2026-04-12-1800
    ↓
[rollback-to tool:]
  1. Verify tag exists
  2. Verify on main branch
  3. Fetch latest
  4. Show preview (commits to revert, files changed)
  5. Prompt "Type ROLLBACK to confirm"
    ↓ (Sinse types ROLLBACK)
  6. Create backup-before-rollback-<timestamp> branch
  7. git revert $TAG..HEAD (creates revert commits, no force push)
  8. Create rollback tag rollback-<timestamp>-from-<original>
  9. git push origin main + tags
  10. smoke-test --deep post-rollback
  11. Prompt Sinse to restart affected containers
    ↓
[Production restored to known good state]
```

---

## 6. Cohérence avec les 8 règles d'or

| Règle | Vérifié ? | Mécanisme |
|-------|-----------|-----------|
| **#1 Backup avant tout** | ✅ | Session 1 entièrement dédiée backup + test restore obligatoire avant YOLO |
| **#2 Prod intouchable** | ✅ | Le refactor ne touche jamais au code prod (webapp, Teacher). Seulement l'infra autour |
| **#3 Code produit intact** | ✅ | D21 confirme que `profil_manager.py` et scripts academie ne sont pas touchés |
| **#4 Tester chaque brique** | ✅ | Smoke-test S1, worktree claude validé S2, premier Gemini test S3 |
| **#5 Documenter en temps réel** | ✅ | REFACTOR-PLAN.md working (pendant planification), puis decisions.md + archive |
| **#6 Aucun destructif sans confirmation** | ✅ | `docs/destructive-ops.md` créé en S2, `rollback-to` demande "ROLLBACK" explicite |
| **#7 Plan v1.0 avant exécution** | ✅ | Ce dossier `refactor-v1.0/` est la preuve |
| **#8 Séparation LLM workflow vs projet** | ✅ | D29 formalise. arbiter utilise `claude -p`/`gemini -p` (workflow). LiteLLM reste projet |

---

## 7. Zones qui restent hors scope du refactor workflow

**Important** : ces zones ne sont PAS traitées par le refactor workflow v1.0. Elles feront l'objet d'un audit séparé post-refactor (voir `projects/academie-ia/AUDIT-TODO.md`).

- `/opt/academia/CLAUDE.md` projet (sera remplacé par pointer en S2, mais le contenu migrera vers `docs/`)
- `/opt/academia/scripts/*.py` (les 26 scripts Python ad-hoc, à CLI-fier post-refactor)
- `/opt/academia/api/` code FastAPI (intact)
- `/opt/academia/webapp/` code SvelteKit (intact)
- Configs LiteLLM (sauf déplacement secrets)
- Workflows n8n (intacts)
- Chatflows Dify (intacts, sauf rollback-snapshot prévu en S2)
- Curriculums, data pédagogique (intacts)
- Features MVP v2 (admin, XP triggers, flashcards — traitées post-refactor en priorité normale)

Le refactor workflow v1.0 vise à **établir le socle solide pour faire ces travaux** avec un meilleur outillage, pas à les faire lui-même.
