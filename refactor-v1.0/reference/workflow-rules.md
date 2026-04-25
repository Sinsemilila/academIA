# Workflow Rules — Template AGENTS.md

> Template à copier dans `/root/sinse-workspace/AGENTS.md` en S2.3.1.
> Style : télégraphique anglais strict (D13, D14).
> Contient les 12 sections + 11 ajouts post-audit (D14).

---

## Template complet AGENTS.md

```markdown
# AGENTS.md

Repo = shared memory across AIs (claude / gemini / codex).

## READ ORDER
1. This file (AGENTS.md)
2. projects/<current>/PROJECT.md
3. docs/*.md selectively via `read_when:` (run `docs-list`)

## STYLE
Telegraph. Noun-phrases ok. Drop grammar. Min tokens.
Language: English (historic French in DECISIONS/CHANGELOG preserved — do not retranslate).

## WORKSPACE
Repo: ~/sinse-workspace (GitHub: Sinsemilila/sinse-workspace)
Workflow files: ~/sinse-workspace/{AGENTS.md, docs/, tools/, slash-commands/}
Project state: ~/sinse-workspace/projects/<name>/
Tools on PATH: cly, committer, arbiter, docs-list, smoke-test, status, log, install-slash-commands, init-worktree, merge-to-main, merge-approve, merge-reject, rollback-to, deploy-teacher, pg-backup, restic-backup

## MULTI-AGENT
Branches: claude / gemini / codex (one per AI). Never commit on main directly.
Worktrees: /opt/<project>-worktrees/<agent>/. Always work inside your worktree.
Before edit: `git status/diff`. Unrecognized changes = other agent — leave alone, focus your scope.
Conflicts: call out, pick safer path.
Small commits, ship often.

Branch convention: `<agent>` matches `.agent` file in worktree. Mismatch → ABORT.

Lock file: NONE. Removed in refactor v1.0 (D20). Use git log + HANDOFF-<agent>.md for activity detection.

## GIT
Use `committer` tool, NOT `git commit` directly. Never `git add .`.
Commit format: `[<type>] <message>` where type ∈ {feat, fix, hotfix, docs, refactor, perf, style, test, chore, security, remove, wip}.
Never amend. Never force-push to main. Never `reset --hard` without explicit Sinse OK.
For GitHub URLs (issue/PR): `gh`, NOT web search.
Web: search early; quote exact errors; prefer 2024-2026 sources.

Hooks active:
- pre-commit: gitleaks (blocks secrets)
- pre-push: smoke-test --deep (blocks runtime failures)
- NEVER use `--no-verify` without Sinse explicit permission.

## COMMIT TYPES — PRECISE DEFINITIONS

- `[feat]`     : Adds new functionality. Test: "Does this enable something new?"
- `[fix]`      : Corrects incorrect behavior. Not critical to prod.
- `[hotfix]`   : Critical bug blocking production users NOW. Notifies Sinse immediately.
- `[docs]`     : Documentation only. No code logic changes.
- `[refactor]` : Code restructured, NO behavior change. Same inputs → same outputs.
- `[perf]`     : Performance improvement with MEASURED gain.
- `[style]`    : Cosmetic only (whitespace, formatting, semicolons).
- `[test]`     : Adds/modifies tests only.
- `[chore]`    : Tooling, configs, deps, lockfiles, build scripts.
- `[security]` : Fixes a security vulnerability. ALWAYS requires Sinse approval.
- `[remove]`   : Deletes code/files/features. ALWAYS requires Sinse approval.
- `[wip]`      : Work in progress. NEVER merged.

## AUTO-MERGE RULES (Option E)

When you run `merge-to-main`, the tool classifies by file protection + commit type:

| Commit type | Green files only | Orange/Red files |
|-------------|------------------|-------------------|
| `[docs]` `[style]` `[test]` `[chore]` | AUTO-MERGE | ARBITER (orange) / HUMAN (red) |
| `[fix]` `[refactor]` `[perf]` | AUTO if under threshold, else ARBITER | ARBITER / HUMAN |
| `[feat]` `[hotfix]` | ARBITER always | HUMAN |
| `[security]` `[remove]` | HUMAN always | HUMAN |
| `[wip]` | NEVER MERGE | NEVER MERGE |

Thresholds (D31): fix=30/3, refactor=80/5, perf=50/3 (lines/files).

See `reference/file-protection.md` for the complete file classification.

## TOOLS
See `reference/tools.md` for full list and usage. Key ones:
- `committer "[<type>] <msg>" <files...>` — safe commit (never `git add .`)
- `merge-to-main` — attempt auto-merge per Option E
- `arbiter --branch <name> --type <type>` — cross-review via opposite CLI
- `smoke-test [--quick|--deep|--infra|--all]` — health check
- `status` — multi-AI dashboard
- `rollback-to <tag>` — safe rollback (requires confirmation "ROLLBACK")

## SLASH COMMANDS
- `/pickup` — session start protocol
- `/handoff` — session end protocol (includes merge-to-main attempt)
- `/review` — Claude Code built-in code review

No other slash commands. Use tools instead for everything else.

## MAKE A NOTE
"Make a note" => edit AGENTS.md (shortcut, not blocker). Keep telegraph style.

Context files rules (D36A):
- STATE.md: updated AT merge-to-main success only (global state)
- TODO.md: updated DURING session (claim/complete tasks)
- HANDOFF-<agent>.md: updated AT /handoff (one per AI)
- CHANGELOG.md: updated via `log <type> "<message>"` tool (append-only)
- DECISIONS.md: updated manually ONLY for important decisions (append-only)

## DESTRUCTIVE OPS
See `docs/destructive-ops.md`. ALWAYS ask Sinse before:
- `DROP`, `TRUNCATE`, migrations DB
- `docker volume rm`, `docker system prune`
- `rm -rf` in `/opt/`, `/var/`, `/etc/`
- secret modification
- prod restart while users active
- `git push --force`, `git reset --hard`
- `rollback-to` (requires "ROLLBACK" confirmation anyway)

## SESSION HYGIENE
Run `docs-list` at session start (via /pickup).
Run `smoke-test --quick` at session start (via /pickup).
Run `smoke-test --deep` before push (automatic via pre-push hook).
Update STATE/TODO/HANDOFF in `/handoff`.
Use `committer` — never `git add .`.

## WEB CONTEXT
GitHub URLs → `gh` only (issue, pr, comments, files).
Web search → quote exact errors, prefer 2024-2026 sources, fallback to Firecrawl.

## FRONTEND AESTHETICS (when touching webapp)
Avoid AI-slop UI. Real font (no Inter/Roboto/Arial). Bold accents > gradients.
Webapp design system defined — see projects/academie-ia/docs/webapp.md.

## NATIVE CLAUDE CODE MEMORY (Claude only)
Native memory at `~/.claude/projects/<id>/memory/` exists for Claude.
OK for non-sensitive references. Secrets MUST be by-reference (e.g., `$(cat /opt/shared/secrets/...)`).
Gemini/Codex: no equivalent, use `docs/` instead.

## SUBAGENTS (Claude only)
Native Claude subagents (Task tool): OK for read-only research tasks that would pollute main context.

Rules:
- Read-only only (no file modifications)
- No commits from subagent
- No destructive commands
- Return structured summary to main context

Gemini/Codex: no equivalent, do research manually (acceptable tradeoff).

## LLM SEPARATION (Rule #8)
Workflow LLMs (Claude Pro/Max, Gemini Advanced, future ChatGPT Plus): for arbiter, consultations, /pickup, /handoff — via `claude -p`, `gemini -p`, `codex -p`.
Project LLMs (Groq free, Mistral free, gpt-4o-mini): for academie-IA agents (Teacher, Maestro, etc.) — via LiteLLM ONLY.
NEVER call `claude -p` from a project workflow (n8n, FastAPI endpoint).
NEVER configure Claude Pro as a Dify backend.

## HOOK STOP (existing, keep)
`~/.claude-settings.json` has a Stop hook that checks git diff in sinse-workspace.
If diff present at session end, reminder: "📌 Pense à /handoff". Safety net if AI forgets /handoff.

## HANDOFF OUTPUT (one-line confirmation)
- AUTO_MERGE: "✅ Handoff complete + auto-merged to main (tag: deploy-YYYY-MM-DD-HHMM)"
- ARBITER approved: "✅ Handoff complete + arbiter-approved merge to main (tag: ...)"
- MERGE-REQUEST created: "✅ Handoff complete. N commits pushed. ⚠️ MERGE-REQUEST created — review: projects/<project>/merge-requests/<file>"

No extended reports.

## CONFLICT RESOLUTION
Git conflict: keep best of both, document the resolution in commit message.
AI conflict (two AIs editing same file): last mover aborts and waits, check TODO.md CLAIMED section to avoid re-occurrence.

## PERMISSIONS (reference)
Permissions baseline: `.claude/settings.local.json` defines what Claude can do without asking.
Current allow list: WebFetch github.com/raw.githubusercontent.com/steipete.me, Bash docker/python3/curl specific, Read /root/sinse-workspace.
To add new permission: edit settings.local.json manually, commit as `[chore] permissions: add <description>`.

## CHANGELOG FORMAT (D19)
Append-only. Format:
```
YYYY-MM-DD <AI> — [<type>] <message>
```
Use `log <type> "<message>"` tool. Never edit manually (except [CORRECTION] for historical fixes).

## DECISIONS FORMAT
Append-only. Format:
```
YYYY-MM-DD <AI> — <decision> — <rationale>
```
Manual edit ok. Never delete, use `[CORRECTION]` for fixes.
```

---

## Instructions pour S2.3.1

Créer le fichier avec :
```bash
cat > /root/sinse-workspace/AGENTS.md <<'EOF'
<template ci-dessus>
EOF
```

Puis commit :
```bash
cd /root/sinse-workspace
git add AGENTS.md
committer "[feat] Create canonical AGENTS.md (D14, D37)" AGENTS.md
```

---

## Règles de mise à jour

AGENTS.md est un fichier **ROUGE** (D30) : seul Sinse peut le modifier directement, ou via une IA avec accord explicite.

**Exceptions** :
- "Make a note" pattern : une IA peut ajouter une note courte à AGENTS.md comme side effect, en style télégraphique, avec Sinse présent en session.
- Commit type obligatoire : `[chore] agents: <description>` ou `[docs] agents: <description>`.
- Reviewer : Sinse en direct (HUMAN_REQUIRED toujours sur AGENTS.md).

---

## Prochaines évolutions attendues

Au fil de l'usage :
- Le "Make a note" pattern va enrichir AGENTS.md avec des gotchas découverts
- Les règles peuvent être ajustées après quelques semaines d'usage réel
- Nouveau projet → ajouter un pointer vers `projects/<new-project>/PROJECT.md` dans la section READ ORDER

AGENTS.md **doit rester court** : idéalement < 300 lignes. Si ça grossit, réfléchir à déplacer du contenu dans `docs/` avec `read_when:`.
