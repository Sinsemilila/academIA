# Slash Commands Reference

> Templates verbatim des 2 slash commands `/pickup` et `/handoff` (D33).
> Source tracked : `/root/sinse-workspace/slash-commands/{pickup,handoff}.md`
> Targets installés par `install-slash-commands` :
> - `~/.claude/commands/{pickup,handoff}.md` (markdown direct)
> - `~/.gemini/commands/{pickup,handoff}.toml` (converted)

---

## 1. `/pickup` — Session start protocol

Emplacement source : `/root/sinse-workspace/slash-commands/pickup.md`

```markdown
---
description: Session start — read context, verify state, pick task
---

Session start. Execute in order. No commentary.

## 1. Read workflow
Read `/root/sinse-workspace/AGENTS.md`.

## 2. Detect project
Check `.agent` file OR `pwd`:
- `/opt/academia-worktrees/<agent>/` → project = academie-ia
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
```

---

## 2. `/handoff` — Session end protocol

Emplacement source : `/root/sinse-workspace/slash-commands/handoff.md`

```markdown
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
```

---

## Note : WIP partiel sans merger

Si une IA veut sauvegarder du work-in-progress **sans** tenter le merge, elle n'utilise PAS `/handoff`. À la place :

1. `log wip "description of what's in progress"`
2. `committer "[wip] <message>" <file1> <file2>`
3. `git push origin <branch>`

Le `/handoff` implique toujours "prêt à tenter merge" — c'est son contrat.

---

## Conversion MD → TOML pour Gemini CLI

`install-slash-commands` génère automatiquement les fichiers `.toml` pour Gemini :

```toml
description = "Session start — read context, verify state, pick task"
prompt = """
Session start. Execute in order. No commentary.

## 1. Read workflow
Read `/root/sinse-workspace/AGENTS.md`.

... (rest of the markdown content) ...
"""
```

Le script bash de conversion :
```bash
md_to_toml() {
    local md_file="$1"
    local toml_file="$2"

    # Extract description from front-matter
    local desc=$(awk '/^---$/,/^---$/' "$md_file" | grep "^description:" | sed 's/^description: *//')

    # Extract body (after front-matter)
    local body=$(awk '/^---$/{f++; next} f==2' "$md_file")

    # Write TOML
    cat > "$toml_file" <<EOF
description = "$desc"
prompt = """
$body
"""
EOF
}
```
