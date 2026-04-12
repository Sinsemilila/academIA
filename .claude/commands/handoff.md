---
description: Session end — update state, commit, push, merge
---

Session end. Execute in order. No extended report.

## 1. Pre-checks
- `smoke-test --deep`
- Fail → STOP + fix before continuing. Do NOT proceed.
- `git status -sb`

## 2. Update project state
- `STATE.md`: current state snapshot (if significant global change)
- `TODO.md`: CLAIMED → DONE where completed, keep CLAIMED for unfinished
- `CHANGELOG.md`: append via `log <type> "<message>"` tool (D19)
- `DECISIONS.md`: append only if important decision made

## 3. Write HANDOFF-<agent>.md
Overwrite `projects/<project>/HANDOFF-<agent>.md` with 7-section template (D18):

```
# HANDOFF — <agent> — <YYYY-MM-DD HH:MM>

## 1. Scope/Status
- <bullets>

## 2. Working tree
- Branch: <name>
- Modified: <count>
- Unpushed: <count>
- Clean: yes/no

## 3. Branch/PR/CI
- Ahead of main: <N> commits
- PR: <link or none>
- CI: <status or none>

## 4. Tests/checks
- smoke-test --deep: <result>
- Manual: <what>

## 5. Next steps
1. ...
2. ...

## 6. Risks/gotchas
- ...

## 7. Open questions
- Waiting for Sinse on: ...
```

## 4. Stage + commit
Use `committer` — NEVER `git add .` or `git commit` direct.
`committer "[<type>] <message>" <file1> <file2> ...`
Pre-commit hook runs gitleaks → blocks if secret detected.

## 5. Push
`git push origin <branch>`
Pre-push hook runs `smoke-test --deep` → blocks if fail.

## 6. Attempt merge (MANDATORY in /handoff)
Run `merge-to-main`.
Option E applies (D27-D32). Three possible outcomes:

**Outcome A — AUTO_MERGE:**
"✅ Handoff complete + auto-merged to main (tag: deploy-YYYY-MM-DD-HHMM)"

**Outcome B — ARBITER approved (after cross-review):**
"✅ Handoff complete + arbiter-approved merge to main (tag: deploy-YYYY-MM-DD-HHMM)"

**Outcome C — MERGE-REQUEST created (HUMAN_REQUIRED or ARBITER_NO_GO):**
"✅ Handoff complete. <N> commits pushed. ⚠️ MERGE-REQUEST created — review: projects/<project>/merge-requests/<file>"

## 7. Cleanup
- Remove `.session-progress` file (checkpoint) if present
- One-line confirmation only. No extended report.
