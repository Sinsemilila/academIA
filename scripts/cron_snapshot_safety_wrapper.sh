#!/bin/bash
# Wrapper to source webapp/.env before running cron_snapshot_safety.py.
# Cron doesn't inherit shell env; this loads DATABASE_URL + DIFY_KEY_* needed by the script.
# S65 — Phase 0.5 rename fix : crontab path was /opt/academie/ broken since rename to /opt/academia/.

set -euo pipefail

ENV_FILE="/opt/academia/webapp/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "[$(date)] FATAL: env file missing at $ENV_FILE" >&2
    exit 2
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

# Cron runs on host, not inside Docker network — replace docker-internal hostname
# `pgbouncer` with the host-mapped 127.0.0.1 (docker port 6432 → 127.0.0.1:6432).
DATABASE_URL="${DATABASE_URL//@pgbouncer:/@127.0.0.1:}"
export DATABASE_URL

exec /usr/bin/python3 /opt/academia/scripts/cron_snapshot_safety.py
