---
title: Dify prompt patch — DB UPDATE workflow procedure
status: authoritative
last_reviewed: 2026-05-01
session_origin: 56
---

# Runbook — Dify prompt patch via DB UPDATE

**Audience** : Claude Code + dev modifying Dify chatflow `system` prompts
without going through the Dify Studio UI (faster, scriptable, idempotent,
diff-able via git).

**Scope** : `system` prompt of any LLM node inside a Dify workflow stored in
the `workflows` table (postgres-academie / academie_db). Tested for
Maestro ES (`47b0529c-...`) and Teacher EN (`39565197-...`).

**Use this when** : you need to mutate a system prompt across draft +
published versions atomically, with backup + idempotent script + verification.

**DO NOT use this for** : node graph topology changes (add/remove nodes,
edges) — those are safer via Studio UI then export/import.

---

## Storage model

Dify workflow data lives in `workflows.graph` as a single JSON blob :

```sql
SELECT id, app_id, version FROM workflows WHERE app_id = '<app_id>' ORDER BY created_at DESC;
```

| `version` value | Meaning |
|---|---|
| `draft` | Editable in Studio "Edit" mode. Used by `chat-messages` API only if app is in draft mode. |
| `<timestamp>` (e.g. `2026-04-20 10:21:44.230845`) | Published version. Latest one = the live workflow served by the API. |

**Maestro ES** has both a `draft` row + a `published` row → **dual-patch
required**. **Teacher EN** has only published rows (no active draft) →
single-patch on the most-recent row.

---

## 6-step procedure

### 1. Identify the LLM node

```sql
SELECT graph->'nodes' FROM workflows WHERE id = '<wid>';
```

Find the node whose `id` matches your target (e.g. `llm_session`,
`llm_plan_choice`, `llm_onboarding`, `llm_exam`). Inside `data.prompt_template`,
the role-`system` entry is what you mutate.

### 2. Backup every row before mutation

Always dump the FULL graph JSON to `/tmp/dify_backups/<TS>_<agent>_pre_<change>.json`
**before any UPDATE**. The patch script does this automatically. Include
**all rows** of the app_id (draft + every published version), not just the
target row — easier rollback.

### 3. Write idempotent patch script

Pattern under `scripts/sprint-maestro-es/` :

```python
V2_MARKER = "REGLAS LYSTER POR NIVEL CEFR (v2)"

def patch_text(text: str) -> tuple[str, str]:
    if V2_MARKER in text:
        return text, "noop_v2_present"     # re-run safe
    # ... do the mutation ...
    return text, "patched"
```

The marker check makes the script re-runnable. The `OLD_MAPPING` /
`NEW_MAPPING` exact-match replacement makes it fail-loud if the upstream
prompt changed.

### 4. Dry-run first

```bash
python3 scripts/sprint-maestro-es/02_dify_maestro_es_lyster_cefr_v2.py --dry-run
```

Confirms : (a) marker not yet present, (b) anchor strings (`OLD_MAPPING`,
`=== FIN MAPPING ===`) still match, (c) post-patch graph size reasonable.

### 5. Apply with $$-quoted UPDATE

```python
psql_exec(f"UPDATE workflows SET graph = $${new_graph_json}$$ WHERE id = '{wid}';")
```

`$$...$$` (PostgreSQL dollar-quoted strings) avoids escaping hell with the
JSON content. Single-quote escaping fails on JSON containing `'` characters.

For Maestro ES (dual row) : update **draft AND published** in same script run.
Dify backend (`dify-api` + `dify-worker`) reads from DB on each
`chat-messages` request — **no server restart needed**. The change is live
within the next request.

### 6. Verify and smoke

Verify markers present in DB :

```sql
SELECT id, position('<marker>' in graph) > 0 AS marker_present FROM workflows WHERE app_id = '<app_id>';
```

Both rows should return `t`. Then smoke :

```bash
python3 scripts/oracle/harness.py --agent <agent> --mode smoke --panel cross-provider --cache off --gate-mode relaxed
```

If smoke responses changed substantially (≥3/6 different content) : re-record goldens :

```bash
python3 scripts/oracle/record_golden.py --agent <agent> --apply
```

Then re-smoke. DoD is `6/6` post re-record (or `5/6` minimum if 1 fail is a
non-cf_move dim like `semantic_fidelity_pairwise` — the golden_obsolete failure mode
is normal whenever Maestro/Teacher response moves to a different CF tier family).

---

## Cache & limits gotchas

- **OpenAI prompt cache (`CACHE_REORDER_v1` marker)** : the system prompt
  has a fixed prefix marker `=== CONTEXTE DE CE TOUR ===`. Inserts ABOVE
  this marker stay in the cacheable region (good — same input hash → cache
  hit on subsequent turns). Inserts BELOW invalidate the cache and inflate
  per-turn input cost. Always insert directives ABOVE the marker.

- **Dify Start node `max_length`** : Dify validates input strings against
  the Start node `variables` declarations. `concept_hints_json` and
  `learner_profile_summary` were bumped to 50K chars after the S55 incident.
  If you grow either input, double-check the Start node `max_length`. The
  `concept_hints_json` payload is pre-filtered by CEFR level via
  `load_concept_hints_for_level(lang, niveau)` (commit `a7a4465`) so prod
  payload stays bounded even if YAMLs grow.

- **Dify worker silent failures** : if `dify-worker` raises a `ValueError`
  (e.g. input exceeds `max_length`), the `chat-messages` POST returns
  `200 OK` with a stuck `task_id` and the frontend shows "Erreur de
  connexion" / `httpx ReadTimeout`. **Always** check `docker logs
  dify-worker --tail 50` first when investigating Dify regressions —
  don't trust the API status code.

---

## Rollback

```bash
# Find your backup file
ls -la /tmp/dify_backups/ | grep <agent>

# Restore each row from the JSON dump
python3 -c "
import json, subprocess
with open('/tmp/dify_backups/20260501-143238_maestro_es_pre_lyster_v2.json') as f:
    d = json.load(f)
for wid, graph in d.items():
    sql = f\"UPDATE workflows SET graph = \$\${json.dumps(graph, ensure_ascii=False)}\$\$ WHERE id = '{wid}';\"
    subprocess.run(['docker', 'exec', '-i', 'postgres-academie', 'psql', '-U', 'sinse', '-d', 'academie_db'],
                   input=sql, text=True, check=True)
"
```

Backups live in `/tmp/` so they survive the session but not a host reboot.
For permanent archival, copy into `vault/projects/academia-ia/` after
session close (or commit a stripped-down version of the patch + a comment
referencing the backup hash).

---

## File layout

| Purpose | Path |
|---|---|
| Patch scripts (per agent + per change) | `scripts/sprint-<topic>/NN_dify_<agent>_<change>.py` |
| Backups | `/tmp/dify_backups/<TS>_<agent>_pre_<change>.json` |
| This runbook | `docs/99-runbooks/dify-prompt-patch.md` |
| Oracle smoke harness | `scripts/oracle/harness.py --agent <agent> --mode smoke` |
| Goldens re-record | `scripts/oracle/record_golden.py --agent <agent> --apply` |

---

## Cross-references

- Maestro ES Tier 1 G5.1 + G5.2 patches (S56) : `scripts/sprint-maestro-es/02_*.py` + `03_*.py`
- S55 incident bloc 1 (max_length) : `scripts/runbooks/dify_bump_concept_hints_max_length.sh`
- Backend Dify input builder : `webapp/backend/app/routers/chat_router.py` line ~920 `build_dynamic_sections`
- Vault gotcha cross-projet : `/root/sinse-vault/knowledge/cross-project/dify-variable-wiring.md`
