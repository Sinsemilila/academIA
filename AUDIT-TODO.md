# AUDIT-TODO — AcademIA (post-refactor)

> Items to review. Priority: normal.

## Code organization

- [ ] Scripts `/opt/academie/scripts/` (26 files): CLI-fy with typer? Group by function? Move to tools/?
- [ ] `/opt/academie/curriculums/`: organize by domain
- [ ] `/opt/academie/api/` vs `/opt/academie/webapp/backend/`: clarify split

## Configuration cleanup

- [ ] `/opt/academie/.claude/`: keep settings.local.json, remove old commands/fin.md
- [ ] Remove stale `/opt/academie/.gemini/` dir if present
- [ ] Remove `/opt/academie/context` symlink if broken

## Security

- [ ] PG password: verify stored only in /opt/academie-shared/secrets/
- [ ] Claude native memory: verify no secrets remain in clear
- [ ] .gitignore: ensure .env, secrets, and keys are excluded

## Documentation

- [ ] Cross-reference docs/ files with actual code paths
- [ ] Add read_when: triggers to any new docs
- [ ] Verify 6 project docs are still accurate after feature changes

Updated: 2026-04-13 — Claude (workflow refonte cleanup)
