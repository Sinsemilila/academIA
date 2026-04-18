#!/usr/bin/env python3
"""Backfill error_log v2 fields (Sprint 2 Phase B2).

Idempotent: only updates rows where tier IS NULL (new fields not set).
For each, computes enrich_error_fields(error_code, learner CEFR level) and
UPDATEs the 6 v2 columns.

Run via host Python (no asyncpg needed): uses docker exec psql.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Reuse scoring.enrich_error_fields by importing it from the backend module.
# Backend uses `app.error_taxonomy.scoring`; we add the path so import works.
sys.path.insert(0, str(Path("/opt/academie/webapp/backend").resolve()))

# Force USE_V2 so override + v2 matrix are loaded, matching prod.
import os as _os
_os.environ.setdefault("USE_V2_TOLERANCE", "true")

from academie_core.taxonomy.scoring import enrich_error_fields  # noqa: E402


def psql(sql: str) -> str:
    out = subprocess.run(
        ["docker", "exec", "postgres-academie",
         "psql", "-U", "sinse", "-d", "academie_db", "-tAF,", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def _esc(val):
    """Escape a value for inline SQL (None → NULL, str quoted, num as-is)."""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    s = str(val).replace("'", "''")
    return f"'{s}'"


def main() -> int:
    rows = psql(
        "SELECT el.id, el.error_code, COALESCE(pe.niveau_global, 'B1') "
        "FROM error_log el "
        "LEFT JOIN profils_eleves pe ON pe.eleve_id=el.eleve_id AND pe.domain='en' "
        "WHERE el.tier IS NULL "
        "ORDER BY el.id;"
    )
    if not rows.strip():
        print("Nothing to backfill (all rows already have tier).")
        return 0

    updated = 0
    for line in rows.splitlines():
        parts = line.split(",")
        if len(parts) < 3:
            continue
        rid, code, niveau = parts[0].strip(), parts[1].strip(), parts[2].strip()
        enrich = enrich_error_fields(code, niveau)
        sql = (
            "UPDATE error_log SET "
            f"tier={_esc(enrich['tier'])}, "
            f"gravity_linguistic={_esc(enrich['gravity_linguistic'])}, "
            f"gravity_communicative={_esc(enrich['gravity_communicative'])}, "
            f"gravity_social={_esc(enrich['gravity_social'])}, "
            f"criterial_level_emergence={_esc(enrich['criterial_level_emergence'])}, "
            f"criterial_level_mastery={_esc(enrich['criterial_level_mastery'])} "
            f"WHERE id={int(rid)};"
        )
        psql(sql)
        updated += 1
        print(f"  updated id={rid} code={code} niveau={niveau} → tier={enrich['tier']}")

    print(f"\n{updated} rows updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
