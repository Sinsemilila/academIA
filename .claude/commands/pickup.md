---
description: Session start — read context, check health, pick task
---

Session start. Execute in order.

## 1. Context
- `git log --oneline -10`
- Read `/root/sinse-workspace/projects/academie-ia/SESSION.md`. Missing → first session, skip.
- Read `/root/sinse-workspace/projects/academie-ia/docs/INDEX.md`. Scan sections relevant to user's expected request.

## 2. Health check
- `smoke-test --quick`
- Fail → STOP + alert Sinse.

## 3. Tasks
- Read `/root/sinse-workspace/projects/academie-ia/TODO.md` — OPEN section.

## 4. Summary (3 lines max)
- Last session scope (from SESSION.md)
- Smoke-test result
- Suggested next action

Wait for instruction.
