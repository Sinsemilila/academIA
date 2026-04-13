---
description: Session end — save state, commit, push
---

Session end. Execute in order.

## 1. Pre-check
- `smoke-test --deep`
- Fail → STOP + fix before continuing.

## 2. Update state
- `TODO.md`: mark completed tasks as DONE.
- `CHANGELOG.md`: append via `log <type> "<message>"` tool.

## 3. Write SESSION.md
Overwrite `projects/academie-ia/SESSION.md`:
```
# Session — YYYY-MM-DD

## Done
- bullet list of what was accomplished

## Next
- bullet list of suggested next steps

## Gotchas
- bullet list of risks/issues (if any, omit section if none)
```

## 4. Commit + push
- `committer "[<type>] <message>" <files...>` for project code (in /opt/academie/)
- `committer "[docs] Session handoff" <files...>` for workspace state (in ~/sinse-workspace/)
- `git push origin main` (both repos if changed)

## 5. Confirmation
One-line confirmation only.
