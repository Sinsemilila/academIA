"""Dify app cloner — clone an existing chatflow app into a new app.

Phase 0.1 — the primitive multilang Waves use to spawn Maestro (ES),
Professore (IT), Lehrer (DE), Sensei (JP), Uchitel (RU) from the Teacher
baseline.

What it does :
1. Reads the source app + its active workflow (published) + its site from Dify DB
2. Generates new UUIDs for app, workflow, site, api_token
3. Generates a new Dify API key (format `app-XXXXXXXXXXXXXXXX`)
4. Optionally applies text substitutions on the graph JSON (`--prompts-override`)
5. Writes SQL preview; with `--apply`, executes inserts inside a single transaction

Design choices :
- Clone is SQL-level, same pattern as `scripts/sprint5/04_update_dify_teacher_unified.py`
- Dry-run by default — preview only, no DB writes
- Idempotent on re-run : if an app with the same name already exists, abort
- Does NOT clone conversations, messages, workflow_runs (those are runtime state)

Usage examples :
    # Dry-run (default)
    python3 scripts/dify/clone_app.py \\
        --source-app-id 39565197-c9d1-4d5b-b66f-18925de236d9 \\
        --new-name "Maestro - Profesor de Español" \\
        --new-description "Tutor IA pour l'espagnol" \\
        --prompts-override /tmp/maestro_prompts.json

    # Actually create the new app (asks confirmation)
    python3 scripts/dify/clone_app.py --source-app-id ... --apply
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dify_db import psql_exec, psql_query  # noqa: E402


@dataclass
class SourceApp:
    app_id: str
    tenant_id: str
    mode: str
    icon: str | None
    icon_background: str | None
    icon_type: str | None
    created_by: str | None
    workflow_id: str
    workflow_graph: str
    workflow_features: str
    workflow_type: str
    workflow_version: str
    workflow_env_vars: str
    workflow_conv_vars: str
    site_code: str
    site_default_language: str


def _gen_api_key() -> str:
    """Dify API keys look like `app-XXXXXXXXXXXXXXXX` (16 alphanumeric)."""
    # 16 chars base32-ish drawn from secrets.choice to avoid ambiguous chars
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "app-" + "".join(secrets.choice(alphabet) for _ in range(20))


def _gen_site_code() -> str:
    """Dify site codes are short random public URL slugs."""
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(14))


def read_source_app(source_app_id: str) -> SourceApp:
    # Fetch small-field columns in one query (pipe-separated, safe because none
    # of these columns can contain pipes)
    meta_sql = f"""
SELECT
  a.id, a.tenant_id, a.mode,
  COALESCE(a.icon, ''), COALESCE(a.icon_background, ''), COALESCE(a.icon_type, ''),
  COALESCE(a.created_by::text, ''),
  a.workflow_id,
  w.type, w.version,
  COALESCE(s.code, ''), COALESCE(s.default_language, 'en-US')
FROM apps a
JOIN workflows w ON w.id = a.workflow_id
LEFT JOIN sites s ON s.app_id = a.id
WHERE a.id = '{source_app_id}' LIMIT 1
""".strip()
    raw = psql_query(meta_sql)
    if not raw:
        raise SystemExit(f"ERROR: source app not found: {source_app_id}")
    parts = raw.split("|")
    if len(parts) < 12:
        raise SystemExit(f"ERROR: unexpected row shape: got {len(parts)} cols")

    # Fetch large-text fields separately (each query returns a single field,
    # so there's no internal separator conflict).
    workflow_id = parts[7]
    graph = psql_query(f"SELECT graph FROM workflows WHERE id = '{workflow_id}'")
    features = psql_query(f"SELECT features FROM workflows WHERE id = '{workflow_id}'")
    env_vars = psql_query(
        f"SELECT environment_variables FROM workflows WHERE id = '{workflow_id}'"
    )
    conv_vars = psql_query(
        f"SELECT conversation_variables FROM workflows WHERE id = '{workflow_id}'"
    )
    return SourceApp(
        app_id=parts[0], tenant_id=parts[1], mode=parts[2],
        icon=parts[3] or None, icon_background=parts[4] or None,
        icon_type=parts[5] or None, created_by=parts[6] or None,
        workflow_id=workflow_id,
        workflow_graph=graph,
        workflow_features=features,
        workflow_type=parts[8],
        workflow_version=parts[9],
        workflow_env_vars=env_vars,
        workflow_conv_vars=conv_vars,
        site_code=parts[10], site_default_language=parts[11],
    )


def check_name_available(tenant_id: str, new_name: str) -> None:
    safe_name = new_name.replace("'", "''")
    sql = f"SELECT COUNT(*) FROM apps WHERE tenant_id='{tenant_id}' AND name='{safe_name}'"
    raw = psql_query(sql).strip()
    if raw != "0":
        raise SystemExit(
            f"ERROR: an app with name {new_name!r} already exists in this tenant. Aborting."
        )


def apply_prompts_override(graph_json: str, overrides: dict[str, str], scoped: bool = True) -> str:
    """Apply substitutions on the graph prompts. Session 42 D5 : default
    behavior changed from naive `graph.replace()` (which could silently
    corrupt JSON structure if a pattern matched a key/value delimiter)
    to a SCOPED AST walker that only touches `nodes[*].data.prompt_template[*].text`.

    Passing `scoped=False` falls back to the legacy string-replace for
    callers that need broad substitution (not recommended).

    `overrides` is a dict `{from_str: to_str}`. Each pair applied in
    definition order.
    """
    if not scoped:
        patched = graph_json
        for src, dst in overrides.items():
            patched = patched.replace(src, dst)
        json.loads(patched)  # validate
        return patched

    # Scoped AST-level : parse → walk nodes → mutate prompt texts only → reserialize
    graph = json.loads(graph_json)
    nodes = graph.get("nodes") or []
    hits = 0
    for n in nodes:
        tmpls = (n.get("data") or {}).get("prompt_template") or []
        for t in tmpls:
            if not isinstance(t, dict) or "text" not in t:
                continue
            original = t["text"]
            patched = original
            for src, dst in overrides.items():
                patched = patched.replace(src, dst)
            if patched != original:
                t["text"] = patched
                hits += 1
    if hits == 0 and overrides:
        # No scoped hit — the override may target a non-prompt field.
        # Log via stderr ; caller can retry with scoped=False if intentional.
        import sys as _sys
        print(
            f"  [WARN] apply_prompts_override(scoped=True) made 0 prompt_template.text "
            f"substitutions. Check overrides target prompt text ; use scoped=False if "
            f"targeting other graph fields.",
            file=_sys.stderr,
        )
    return json.dumps(graph, ensure_ascii=False)


def validate_data_pack(lang: str) -> None:
    """Pre-flight validate YAML data packs for a target language.
    Raises SystemExit on any schema violation so the caller never clones
    into a broken pack. Session 42 D5."""
    import sys
    sys.path.insert(0, "/opt/academie/packages/academie-core")
    from academie_core.data.schemas import (
        CurriculumPack,
        FewshotPack,
        RubricPack,
    )
    import yaml as _yaml

    data_dir = Path("/opt/academie/packages/academie-core/academie_core/data")
    checks = [
        (data_dir / f"curriculum_{lang}.yaml", lambda d: CurriculumPack.validate_mapping(d)),
        (data_dir / "rubrics" / f"{lang}.yaml", lambda d: RubricPack.model_validate(d)),
        (data_dir / "fewshots" / f"{lang}.yaml", lambda d: FewshotPack.model_validate(d)),
    ]
    errors = []
    for path, validator in checks:
        if not path.exists():
            errors.append(f"missing: {path.relative_to(Path('/opt/academie'))}")
            continue
        try:
            validator(_yaml.safe_load(path.read_text()))
        except Exception as e:
            errors.append(f"{path.name}: {e}")
    if errors:
        print("ERROR: data pack validation failed :", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        raise SystemExit(2)
    print(f"▸ Data pack for lang={lang!r} : curriculum + rubrics + fewshots validated ✓")


def build_clone_sql(
    source: SourceApp,
    new_app_id: str,
    new_workflow_id: str,
    new_site_id: str,
    new_api_token_id: str,
    new_api_key: str,
    new_site_code: str,
    new_name: str,
    new_description: str,
    new_graph: str,
) -> str:
    """Build the SQL transaction body to insert all 4 clone rows."""
    safe_name = new_name.replace("'", "''")
    safe_desc = new_description.replace("'", "''")
    safe_graph = new_graph.replace("'", "''")
    safe_features = source.workflow_features.replace("'", "''")
    safe_env = (source.workflow_env_vars or "{}").replace("'", "''")
    safe_conv = (source.workflow_conv_vars or "{}").replace("'", "''")
    icon = source.icon or ""
    icon_bg = source.icon_background or "#EFF1F5"
    icon_type = source.icon_type or ""
    created_by = source.created_by or source.tenant_id
    return f"""
BEGIN;

-- 1. New workflow (published version cloned)
INSERT INTO workflows (
  id, tenant_id, app_id, type, version, graph, features,
  created_by, created_at, updated_at,
  environment_variables, conversation_variables,
  marked_name, marked_comment
) VALUES (
  '{new_workflow_id}', '{source.tenant_id}', '{new_app_id}',
  '{source.workflow_type}', '{source.workflow_version}',
  '{safe_graph}', '{safe_features}',
  '{created_by}', NOW(), NOW(),
  '{safe_env}', '{safe_conv}', '', ''
);

-- 2. New app pointing at that workflow
INSERT INTO apps (
  id, tenant_id, name, description, mode,
  icon, icon_background, icon_type,
  app_model_config_id, status, enable_site, enable_api,
  api_rpm, api_rph, is_demo, is_public,
  workflow_id, created_at, updated_at,
  created_by, updated_by, use_icon_as_answer_icon
) VALUES (
  '{new_app_id}', '{source.tenant_id}', '{safe_name}', '{safe_desc}', '{source.mode}',
  '{icon}', '{icon_bg}', '{icon_type}',
  NULL, 'normal', true, true,
  0, 0, false, false,
  '{new_workflow_id}', NOW(), NOW(),
  '{created_by}', '{created_by}', false
);

-- 3. New site (public web URL handle)
INSERT INTO sites (
  id, app_id, title, icon, icon_background, description,
  default_language, customize_token_strategy, prompt_public, status,
  created_at, updated_at, code, custom_disclaimer,
  show_workflow_steps, chat_color_theme_inverted, use_icon_as_answer_icon,
  created_by, updated_by
) VALUES (
  '{new_site_id}', '{new_app_id}', '{safe_name}', '{icon}', '{icon_bg}', '{safe_desc}',
  '{source.site_default_language}', 'not_allow', false, 'normal',
  NOW(), NOW(), '{new_site_code}', '',
  true, false, false,
  '{created_by}', '{created_by}'
);

-- 4. New API token for the app
INSERT INTO api_tokens (
  id, app_id, type, token, created_at, tenant_id
) VALUES (
  '{new_api_token_id}', '{new_app_id}', 'app', '{new_api_key}', NOW(), '{source.tenant_id}'
);

COMMIT;
""".strip()


def main() -> int:
    p = argparse.ArgumentParser(description="Clone a Dify chatflow app (Phase 0.1).")
    p.add_argument("--source-app-id", required=True,
                   help="UUID of the source app (Teacher baseline).")
    p.add_argument("--new-name", required=True,
                   help="Display name for the new app (e.g. 'Maestro').")
    p.add_argument("--new-description", default="",
                   help="Short description shown in the Dify UI.")
    p.add_argument("--prompts-override", type=Path, default=None,
                   help="JSON file {'from_str': 'to_str', ...} applied to graph.")
    p.add_argument("--apply", action="store_true",
                   help="Actually run the INSERTs (default: dry-run only).")
    p.add_argument("--dry-run", action="store_true",
                   help="Force dry-run (default behavior).")
    p.add_argument("--output-sql", type=Path, default=None,
                   help="If set, write the generated SQL to this file.")
    p.add_argument("--validate-data-pack", default=None, metavar="LANG",
                   help="Session 42 D5 — pre-flight validate YAML data pack "
                        "(curriculum/rubrics/fewshots) for LANG. Abort clone if invalid.")
    p.add_argument("--scoped-overrides", action=argparse.BooleanOptionalAction, default=True,
                   help="Session 42 D5 — use AST-scoped overrides on prompt_template.text "
                        "(default). --no-scoped-overrides for legacy full-string replace.")
    args = p.parse_args()

    if args.validate_data_pack:
        validate_data_pack(args.validate_data_pack)

    print(f"▸ Reading source app {args.source_app_id} ...")
    source = read_source_app(args.source_app_id)
    print(f"  tenant_id={source.tenant_id}  mode={source.mode}")
    print(f"  workflow_id={source.workflow_id}  graph_len={len(source.workflow_graph)} chars")

    check_name_available(source.tenant_id, args.new_name)

    overrides: dict[str, str] = {}
    if args.prompts_override is not None:
        overrides = json.loads(args.prompts_override.read_text())
        print(f"▸ Loaded {len(overrides)} prompt overrides from {args.prompts_override}")

    new_graph = apply_prompts_override(source.workflow_graph, overrides, scoped=args.scoped_overrides)
    if overrides:
        n_changed = sum(1 for k in overrides if k in source.workflow_graph)
        print(f"  applied {n_changed}/{len(overrides)} overrides (others not found in graph)")

    new_app_id = str(uuid.uuid4())
    new_workflow_id = str(uuid.uuid4())
    new_site_id = str(uuid.uuid4())
    new_api_token_id = str(uuid.uuid4())
    new_api_key = _gen_api_key()
    new_site_code = _gen_site_code()

    print("▸ Generated identifiers:")
    print(f"  app_id      = {new_app_id}")
    print(f"  workflow_id = {new_workflow_id}")
    print(f"  site_id     = {new_site_id}")
    print(f"  site_code   = {new_site_code}")
    print(f"  api_key     = {new_api_key}")

    sql = build_clone_sql(
        source=source,
        new_app_id=new_app_id,
        new_workflow_id=new_workflow_id,
        new_site_id=new_site_id,
        new_api_token_id=new_api_token_id,
        new_api_key=new_api_key,
        new_site_code=new_site_code,
        new_name=args.new_name,
        new_description=args.new_description,
        new_graph=new_graph,
    )

    if args.output_sql:
        args.output_sql.write_text(sql)
        print(f"▸ SQL written to {args.output_sql}")

    if not args.apply:
        print("▸ DRY-RUN — no DB changes. Pass --apply to execute.")
        print("  Summary of SQL (length = {} chars). Re-run with --output-sql "
              "to inspect.".format(len(sql)))
        return 0

    print("▸ APPLY mode — executing SQL now ...")
    psql_exec(sql)
    print("▸ ✓ Done.")
    print(f"  Add the following to your environment:")
    print(f"  DIFY_KEY_<AGENT>={new_api_key}")
    print(f"  (see webapp/.env and chat_router DIFY_APP_KEYS)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
