---
description: Session end — save state, commit, push
---

Session end. Execute in order.

## 1. Pre-check
- `smoke-test --deep`
- Fail → STOP + fix before continuing.

## 2. Update state
- `/opt/academie/TODO.md`: mark completed tasks as DONE.
- `/opt/academie/CHANGELOG.md`: append via `log <type> "<message>"` tool.
- **Docs consistency check**: for each structural change this session (schema, architecture, pedagogy rules, infra), verify the corresponding `docs/*.md` was updated in the same session. If not, update `last_reviewed` OR flip `status: needs-review`. For new architectural decisions, create `docs/05-decisions/ADR-NNN-<slug>.md` from template.

## 3. Update SESSION.md
**Prepend** (don't overwrite) a new session block at the top of `/opt/academie/SESSION.md`, after the header line.
Keep previous sessions below.

**Rotation** : SESSION.md ne contient que les **3 dernières sessions**. Après avoir prepended la nouvelle, si le fichier contient >3 sessions, déplacer la plus ancienne (celle en bas) vers le haut de `SESSION_ARCHIVE.md` (aussi newest-on-top). L'archive n'est jamais lue au pickup mais reste disponible pour consultation manuelle.
```
---

## Session N — YYYY-MM-DD

### Done
- bullet list of what was accomplished

### Next
- bullet list of suggested next steps

### Gotchas
- bullet list of risks/issues (if any, omit section if none)
```

## 4. Commit + push
- `committer "[<type>] <message>" <files...>` for project code (in /opt/academie/)
- `committer "[docs] Session handoff" <files...>` for workspace state (in /opt/academie/)
- `git push origin main` (both repos if changed)

## 5. Confirmation
One-line confirmation only.
