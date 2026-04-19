"""Thin wrapper around `docker exec postgres-academie psql` for Dify DB ops.

Factored out of `scripts/sprint5/04_update_dify_teacher_unified.py` — all Dify
graph manipulations go through these helpers.
"""
from __future__ import annotations

import subprocess

DB_CONTAINER = "postgres-academie"
DB_USER = "sinse"
DB_NAME = "academie_db"


def psql_query(sql: str) -> str:
    """Run a read SQL statement and return stdout (tab-separated, header-less)."""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER, "psql",
        "-U", DB_USER, "-d", DB_NAME, "-t", "-A", "-c", sql,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.rstrip("\n")


def psql_exec(sql: str) -> None:
    """Execute a block of SQL (pipes to psql stdin to bypass shell escaping)."""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER, "psql",
        "-U", DB_USER, "-d", DB_NAME,
    ]
    subprocess.run(cmd, input=sql, text=True, check=True)


def psql_query_rows(sql: str) -> list[list[str]]:
    """Return list of row lists, each row is a list of column strings."""
    raw = psql_query(sql)
    if not raw:
        return []
    return [row.split("|") for row in raw.split("\n")]
