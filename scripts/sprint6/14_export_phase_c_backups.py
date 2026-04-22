#!/usr/bin/env python3
"""Session 39 Block 0.1 — Export Dify workflow graphs for Phase C rollback.

Dumps the current graph JSONB of the 4 workflows patched by script 13
(Teacher+Maestro × published+draft) to backups/phase_c_pre_reorder/.

Caveat : the snapshots are POST-reorder (commit dcd7110 already applied).
They cannot restore the pre-reorder state — that window is closed. Their
value is being able to pin the current-known-good state so any FUTURE
change (Phase C-deep, new reorder iteration, prompt edits) remains
revertible to this checkpoint.

Idempotent : each run writes a new timestamped file. Does not delete
prior backups. Companion script `rollback_phase_c.sh` reads the latest.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Same 4 UUIDs as scripts/sprint6/13_reorder_prompt_for_caching.py
TARGETS = [
    ("006cba2d-08b0-449c-91ed-0dda79d414ce", "teacher", "published"),
    ("ed0d1c91-8c9a-48ad-9c3a-063981f8da87", "teacher", "draft"),
    ("d3df0ef0-a28f-4850-9396-d4d1cf6c0e21", "maestro", "published"),
    ("69fc4cf7-8835-44ce-925a-09099af67bc1", "maestro", "draft"),
]

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = REPO_ROOT / "backups" / "phase_c_pre_reorder"


def psql_q(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse",
         "-d", "academie_db", "-t", "-A", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.rstrip("\n")


def export_one(wf_id: str, agent: str, stage: str, ts: str) -> dict:
    stats: dict = {"agent": agent, "stage": stage, "workflow_id": wf_id}
    graph_str = psql_q(f"SELECT graph FROM workflows WHERE id='{wf_id}';")
    if not graph_str:
        stats["error"] = "workflow not found"
        return stats
    # Validate JSON
    try:
        graph = json.loads(graph_str)
    except json.JSONDecodeError as e:
        stats["error"] = f"invalid JSON: {e}"
        return stats

    out = BACKUP_DIR / f"{agent}_{stage}_{ts}.json"
    payload = {
        "workflow_id": wf_id,
        "agent": agent,
        "stage": stage,
        "exported_at": ts,
        "graph": graph,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    stats["path"] = str(out.relative_to(REPO_ROOT))
    stats["bytes"] = out.stat().st_size
    stats["nodes"] = len(graph.get("nodes", []))
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="filter by agent (teacher|maestro) or stage")
    args = ap.parse_args()

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")

    results = []
    for wf_id, agent, stage in TARGETS:
        if args.only and args.only.lower() not in f"{agent}_{stage}":
            continue
        print(f"── {agent} {stage} ({wf_id[:8]}) ──")
        st = export_one(wf_id, agent, stage, ts)
        results.append(st)
        for k, v in st.items():
            print(f"  {k}: {v}")

    errors = sum(1 for s in results if s.get("error"))
    ok = len(results) - errors
    print(f"\n━━━ Summary ━━━")
    print(f"  exported={ok}  errors={errors}  dir={BACKUP_DIR.relative_to(REPO_ROOT)}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
