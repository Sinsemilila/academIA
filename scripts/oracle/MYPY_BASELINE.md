---
title: oracle/ mypy baseline
status: active
last_reviewed: 2026-05-01
owner: claude
---

# Oracle/ mypy baseline (S56 incremental strict)

**Established** : 2026-05-01 (S56) post Maestro ES MVP-acceptable

## Setup

```bash
cd /opt/academia/scripts/oracle
python3 -m venv .venv-tools
.venv-tools/bin/pip install ruff mypy types-PyYAML pyyaml pydantic httpx pytest

# Lint + format
.venv-tools/bin/ruff check .

# Type check
.venv-tools/bin/mypy .

# Tests
PYTHONPATH=/opt/academia/scripts .venv-tools/bin/python -m pytest tests -q
```

## Baseline (S57)

- **ruff** : ✅ 0 errors (was 24 pre-S56)
- **mypy** : ✅ 0 errors (was 23 pre-S56, was 7 mid-S57 post types-PyYAML)
- **pytest** : ✅ 49/49 green

## History

- **S56** : ruff 24→0, mypy 23→7 (types-PyYAML stubs killed 13)
- **S57** : mypy 7→0 — schema `ScenarioResult.response_text` field declared explicitement, harness `mode: str` → `Literal[...]`, response var declared `str | None = None` early, `assert isinstance(level, str)` narrow `_cross_judge_majority` generic return, removed 2 obsolete `# type: ignore`

## Policy

**Incremental strict ENFORCED** : 0 nouveaux errors tolérés sur new code. Baseline 0 doit rester à 0.

Pré-commit hook ruff/mypy oracle/ TBD. Run manuel post-changement :

```bash
cd /opt/academia/scripts/oracle
.venv-tools/bin/ruff check . && .venv-tools/bin/mypy .
```
