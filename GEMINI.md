# Gemini — AcademIA Worktree

READ `/root/sinse-workspace/AGENTS.md` FIRST. It is the single source of truth for all workflow rules.
Then read `/root/sinse-workspace/projects/academie-ia/PROJECT.md` for project context.

## Quick refs

- Worktree: `/opt/academie-worktrees/gemini/`
- Branch: `gemini` (must match `.agent` file)
- Canonical workflow: `/root/sinse-workspace/AGENTS.md`
- Project state: `/root/sinse-workspace/projects/academie-ia/`
- Slash commands: `/pickup` (session start), `/handoff` (session end)

## Key rules

- Use `committer` for commits, NEVER `git commit` or `git add .`
- Lock file system: **REMOVED** (D20). Use `git log` + `HANDOFF-gemini.md` for activity detection.
- `merge-approve` and `merge-reject` are **SINSE-ONLY**. NEVER call them.
- Run `smoke-test --quick` at session start, `smoke-test --deep` before push.
- Tools on PATH: committer, arbiter, smoke-test, merge-to-main, status, log, docs-list, deploy-teacher, pg-backup, restic-backup, rollback-to
