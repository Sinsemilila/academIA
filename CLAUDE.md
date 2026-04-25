# AcademIA — Claude Code project context

## ENFORCEMENT-CRITICAL (read every session)

### n8n workflow patches
n8n exécute depuis `workflow_history.nodes`, PAS `workflow_entity.nodes`.
Toujours patcher LES DEUX tables sinon le workflow continue d'exécuter
l'ancienne version. Cf. memory `project_n8n_workflow_history.md`.

### Dify variable wiring
Pipeline complet pour ajouter une variable :
1. Start vars (definition)
2. `code_turn_check` node : ajouter au `variables` block + `signature` + `return` + `outputs`
3. LLM node : référencer `{{#code_turn_check.X#}}` (PAS `{{#start.X#}}`)

Skipper l'étape 2 = variable absente runtime, échec silencieux. Cf. memory
`project_dify_variable_wiring.md`.

### Merge workflow
Toujours `git stash` dans `/opt/academie` AVANT pull/merge depuis worktree
externe — sinon conflits silencieux. Cf. memory `feedback_merge_workflow.md`.

## DOCS WORKFLOW

Source-of-truth = `docs/INDEX.md`. Lire au /pickup si la requête est structurelle.

Layout :
- `00-project/` vision, roadmap, glossary
- `01-pedagogy/` taxonomy, CEFR, error gradation, feedback delivery
- `02-architecture/` overview, data-model, agent topology
- `03-domain/` per-language (`en.md`, `es.md`, etc.)
- `04-infra/` deploy, backup, monitoring
- `05-decisions/` ADRs immutable, supersede-based
- `99-runbooks/` operational procedures
- `_legacy/` pré-2026-04-15

YAML header chaque doc : `status: authoritative|draft|needs-review|stale|superseded` + `last_reviewed: YYYY-MM-DD`.

Avant tout changement structurel (schema, architecture, pedagogy) : READ doc + ADR. Après : UPDATE doc OU flip status + nouveau ADR si décision architecturale.

## BUG FIX PROTOCOL

Avant tout `[fix]`/`[hotfix]` commit, écrire bloc diagnostic :
1. SYMPTOMS observed
2. SCOPE files/functions
3. HYPOTHESIS likely cause
4. EDGE CASES could break
5. BLAST RADIUS touches NOT broken
6. PLAN exact changes order

Then write code.

## LLM SEPARATION

- **Workflow** (coding, architecture, research) → Claude (toi)
- **Project** (AcademIA agents : Maestro, Teacher, etc.) → Groq, Mistral, gpt-4o-mini via **LiteLLM uniquement**
- **NEVER** configure Claude comme Dify/LiteLLM backend

## DESTRUCTIVE OPS — toujours demander Sinse

- `DROP`, `TRUNCATE`, migrations DB
- `docker volume rm`, `docker system prune`
- `rm -rf` dans `/opt/`, `/var/`, `/etc/`
- Modification secrets
- Restart prod si users actifs
- `git push --force`, `git reset --hard`

## FRONTEND

Bold accents > gradients. Avoid AI-slop UI.
Design tokens OKLCH (cf. `docs/99-runbooks/b1-design-tokens.md`).

## CONTEXT FILES

- `SESSION.md` updated AT /handoff (done/next/gotchas)
- `TODO.md` updated DURING session
- `CHANGELOG.md` append-only via `log` tool
- `docs/05-decisions/ADR-NNN-*.md` immutable, AI drafts `proposed`, Sinse mark `accepted`

Note : ces fichiers vivent dans `/opt/academie/` (live with code, depuis Phase 2 obsidian migration 2026-04-25).

## VAULT KNOWLEDGE (cross-projet)

Pour patterns cross-projet (auth, dify, n8n, svelte, infra, etc.), dispatch
subagent `vault-reader` (Haiku 4.5) plutôt que load raw `/opt/academie/docs/`
dans Opus context. Économie ~74% tokens vs raw load.

- Vault root : `/root/sinse-vault/`
- Entry point : `/root/sinse-vault/INDEX.md` (MOC racine)
- Knowledge cross-projet : `/root/sinse-vault/knowledge/` (auth-patterns, dify-variable-wiring, n8n-workflow-history)
- Conventions read/write Claude : `/root/sinse-vault/meta/claude-conventions.md`
- CLI mapping exhaustive : `/root/sinse-vault/meta/cli-mapping.md`

Pattern via slash command :
- `/pickup` (workspace orientation, lit vault hot.md + INDEX.md + log.md)
- `/project academia [task-hint]` (deep load + dispatch vault-reader si task identifié)

## STYLE

Telegraph. Noun-phrases ok. Drop grammar. Min tokens. English code, French chat.
