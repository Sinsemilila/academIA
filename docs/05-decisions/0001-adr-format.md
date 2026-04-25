---
status: accepted
date: 2026-04-13
decision-makers: sinse, claude
---

# ADR-0001: Adopt MADR-lite for architecture decisions

## Context
Project has 70+ decisions in an append-only DECISIONS.md. Works for quick notes but lacks rationale/consequences structure for significant choices. Need a format that AI agents can draft and humans can approve.

## Decision
Use MADR-lite (this format) for significant architectural decisions. Keep DECISIONS.md for quick one-liners.

- Files in `docs/decisions/NNNN-short-title.md`
- 4 fields: Context, Decision, Consequences, Status
- Status: proposed → accepted | deprecated
- AI drafts with status "proposed", Sinse marks "accepted"
- Threshold: only document decisions that would take >5 min to re-derive

## Consequences
- Decisions are traceable with rationale
- AI agents read ADRs at pickup for context
- Minimal overhead (4 fields, not 10)
- DECISIONS.md continues for quick notes
