# AUDIT-TODO — AcademIA (post-refactor)

> Items to review. Priority: normal.

## Code organization

- [ ] Scripts `/opt/academia/scripts/` (26 files): CLI-fy with typer? Group by function? Move to tools/?
- [ ] `/opt/academia/curriculums/`: organize by domain
- [ ] `/opt/academia/api/` vs `/opt/academia/webapp/backend/`: clarify split

## Configuration cleanup

- [ ] `/opt/academia/.claude/`: keep settings.local.json, remove old commands/fin.md
- [ ] Remove stale `/opt/academia/.gemini/` dir if present
- [ ] Remove `/opt/academia/context` symlink if broken

## Security

- [ ] PG password: verify stored only in /opt/academia-shared/secrets/
- [ ] Claude native memory: verify no secrets remain in clear
- [ ] .gitignore: ensure .env, secrets, and keys are excluded

## Documentation

- [ ] Cross-reference docs/ files with actual code paths
- [ ] Add read_when: triggers to any new docs
- [ ] Verify 6 project docs are still accurate after feature changes

Updated: 2026-04-13 — Claude (workflow refonte cleanup)
