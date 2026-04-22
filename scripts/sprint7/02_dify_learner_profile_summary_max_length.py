"""Session 43 — bump Dify Teacher EN learner_profile_summary max_length 2000 → 10000.

Root cause : Session 35 MVP (chat_router.py:751-761) appends
scaffolding_block into learner_profile_summary so it reaches both
llm_onboarding and llm_session via the already-wired channel. Over
Sessions 38-42, scaffolding_block grew (CONCEPTS PRIORITAIRES, L1/L2
MIX POLICY, POST-QCM WELCOME) and pushed the concatenation past the
original 2000-char hard limit on the Dify Start input variable.

Effect : new users completing onboarding get "Erreur de connexion" on
the very first chat turn because Dify rejects the payload with
``ValueError: learner_profile_summary in input form must be less than
2000 characters`` at workflow_execute_task entry.

Fix : bump max_length on the `learner_profile_summary` Start variable
from 2000 → 10000 (matching learner_profile_json). Patches both the
published workflow and the draft.

Idempotent : no-op if already at 10000.

Usage :
  python3 scripts/sprint7/02_dify_learner_profile_summary_max_length.py

Rollback : the pre-patch workflow graphs are dumped to
/tmp/dify_backups/teacher_workflow_graphs_<TS>.json. Restore with
``UPDATE workflows SET graph = '<json>' WHERE id = '<wid>';`` per row.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys

APP_ID = "39565197-c9d1-4d5b-b66f-18925de236d9"
DB = ("docker", "exec", "-i", "postgres-academie",
      "psql", "-U", "sinse", "-d", "academie_db")
VARIABLE = "learner_profile_summary"
TARGET = 10000


def psql_tAc(sql: str) -> str:
    return subprocess.check_output([*DB, "-tAc", sql], text=True).rstrip("\n")


def psql_exec(sql: str) -> None:
    p = subprocess.run([*DB, "-v", "ON_ERROR_STOP=1"],
                       input=sql, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"psql failed: {p.stderr}")


def main() -> int:
    wids = psql_tAc(
        f"SELECT id FROM workflows WHERE app_id = '{APP_ID}' "
        f"AND graph LIKE '%{VARIABLE}%' ORDER BY updated_at DESC;"
    ).splitlines()
    if not wids:
        print("No Teacher EN workflows matched — nothing to patch")
        return 0

    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    backup_dir = pathlib.Path("/tmp/dify_backups")
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"teacher_workflow_graphs_{ts}.json"

    backup: dict[str, dict] = {}
    for wid in wids:
        backup[wid] = json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';"))
    backup_path.write_text(json.dumps(backup, ensure_ascii=False))
    print(f"Backup → {backup_path} ({backup_path.stat().st_size} bytes)")

    for wid in wids:
        g = backup[wid]
        start = next(n for n in g["nodes"] if n["data"].get("type") == "start")
        patched = False
        for v in start["data"].get("variables", []):
            if v.get("variable") == VARIABLE and v.get("max_length") != TARGET:
                old = v["max_length"]
                v["max_length"] = TARGET
                patched = True
                print(f"  {wid}: {VARIABLE} max_length {old} → {TARGET}")
        if not patched:
            print(f"  {wid}: already at {TARGET}")
            continue
        sql = (
            "UPDATE workflows SET graph = $SIN$" + json.dumps(g, ensure_ascii=False) +
            f"$SIN$, updated_at = NOW() WHERE id = '{wid}';"
        )
        psql_exec(sql)
        print(f"  {wid}: UPDATE OK")

    print("\nVerification :")
    for wid in wids:
        g = json.loads(psql_tAc(f"SELECT graph FROM workflows WHERE id = '{wid}';"))
        start = next(n for n in g["nodes"] if n["data"].get("type") == "start")
        for v in start["data"].get("variables", []):
            if v.get("variable") == VARIABLE:
                print(f"  {wid}: max_length={v.get('max_length')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
