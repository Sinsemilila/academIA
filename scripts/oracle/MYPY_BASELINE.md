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
cd /opt/academie/scripts/oracle
python3 -m venv .venv-tools
.venv-tools/bin/pip install ruff mypy types-PyYAML pyyaml pydantic httpx pytest

# Lint + format
.venv-tools/bin/ruff check .

# Type check
.venv-tools/bin/mypy .

# Tests
PYTHONPATH=/opt/academie/scripts .venv-tools/bin/python -m pytest tests -q
```

## Baseline (S56)

- **ruff** : ✅ 0 errors (was 24 pre-S56, fixed via auto-fix + 6 manual)
- **mypy** : ⚠️ 7 errors remaining (was 23 pre-S56, types-PyYAML killed 13)
- **pytest** : ✅ 49/49 green

## Remaining mypy errors (à fix incremental)

Concentrés dans 2 fichiers, non-blockers oracle harness :

```
harness.py:72   arg-type      tuple shape mismatch on result append
harness.py:145  unused-ignore  # type: ignore obsolete
harness.py:157  arg-type      mode str → Literal['lint','smoke','full']
harness.py:174  assignment    str|None → str
harness.py:186  attr-defined  ScenarioResult.response_text (Pydantic _Lax extra)
harness.py:191  unused-ignore  # type: ignore obsolete
judges/llm_pairwise.py:498  call-overload  dict.get(object, int) variance
```

## Policy

**Incremental strict** : 0 nouveaux errors tolérés sur new code. Baseline 7 doit décroître session par session — never grow.

Touch-points naturels pour fix :
- `harness.py` errors : Pydantic `ScenarioResult` schema cleanup (S57+) — add `response_text` field explicitement OU use `_Lax = True` pattern.
- `llm_pairwise.py:498` : tighten dict typing (~10 min)

Pré-commit hook ruff/mypy oracle/ TBD (S57+). Pour le moment : run manuel post-changement.
