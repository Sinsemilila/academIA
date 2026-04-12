---
description: Session start — read context, verify state, pick task
---

Session start. Execute in order. No commentary.

## 1. Read workflow
Read `/root/sinse-workspace/AGENTS.md`.

## 2. Detect project
Check `.agent` file OR `pwd`:
- `/opt/academie-worktrees/<agent>/` → project = academie-ia
- Else → ask Sinse.

## 3. Verify branch (safety)
`git branch --show-current` must match agent name.
Mismatch → ABORT + alert Sinse immediately.

## 4. Read project state
- `/root/sinse-workspace/projects/<project>/PROJECT.md`
- Run `docs-list` if available, else `ls projects/<project>/docs/`
- Read docs selectively via `read_when:` front-matter

## 5. Read own handoff
Read `projects/<project>/HANDOFF-<agent>.md`.
Missing → first session, skip.

## 5b. Resume from checkpoint (if present)
Check `.session-progress` file in current dir or $HOME.
Present → restart from STEP indicated.

## 6. Git sync
- `git status -sb`
- `git log --oneline -5`
- `git fetch origin && git merge origin/main`
- Conflict → STOP + ask Sinse.

## 7. Check pending merge requests
`ls projects/<project>/merge-requests/*.md 2>/dev/null`
Count > 0 → alert: "X pending merge requests."

## 8. Smoke-test
`smoke-test --quick`
Fail → alert + STOP.

## 9. Check CLAIMED tasks (continuation)
Read `projects/<project>/TODO.md`, CLAIMED section.
Tasks claimed by `<agent>` → these are continuation priorities.

## 10. List OPEN tasks
From same TODO.md, list OPEN tasks available to claim.

## 11. Summary to Sinse (max 5 lines)
- Current state
- Last session scope (from HANDOFF)
- Smoke-test result
- CLAIMED tasks in progress (if any)
- Pending merge requests count (if any)
- Suggested next action

Wait for instruction.
