#!/usr/bin/env bash
# Session 39 Block 0.1 — Restore a Dify workflow graph from latest backup.
#
# Usage :
#   rollback_phase_c.sh --agent teacher --stage published [--dry-run]
#   rollback_phase_c.sh --all [--dry-run]
#
# Reads latest backup in backups/phase_c_pre_reorder/{agent}_{stage}_*.json
# and applies UPDATE workflows SET graph = ... via docker exec psql.
#
# Safety :
#   - --dry-run mode prints the target file + workflow_id, no DB write.
#   - Pre-write : dumps CURRENT graph to /tmp/rollback_predump_{ts}_{uuid8}.json
#     so the rollback itself is reversible.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
BACKUP_DIR="$REPO/backups/phase_c_pre_reorder"

AGENT=""
STAGE=""
ALL=0
DRY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent) AGENT="$2"; shift 2 ;;
    --stage) STAGE="$2"; shift 2 ;;
    --all) ALL=1; shift ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

declare -A UUIDS=(
  ["teacher_published"]="006cba2d-08b0-449c-91ed-0dda79d414ce"
  ["teacher_draft"]="ed0d1c91-8c9a-48ad-9c3a-063981f8da87"
  ["maestro_published"]="d3df0ef0-a28f-4850-9396-d4d1cf6c0e21"
  ["maestro_draft"]="69fc4cf7-8835-44ce-925a-09099af67bc1"
)

if (( ALL == 1 )); then
  TARGETS=("teacher_published" "teacher_draft" "maestro_published" "maestro_draft")
else
  [[ -z "$AGENT" || -z "$STAGE" ]] && { echo "need --agent + --stage, or --all" >&2; exit 2; }
  TARGETS=("${AGENT}_${STAGE}")
fi

restore_one () {
  local key="$1"
  local uuid="${UUIDS[$key]:-}"
  [[ -z "$uuid" ]] && { echo "unknown key: $key" >&2; return 1; }

  local latest
  latest=$(ls -1t "$BACKUP_DIR/${key}_"*.json 2>/dev/null | head -n1 || true)
  if [[ -z "$latest" ]]; then
    echo "── $key : no backup found in $BACKUP_DIR" >&2
    return 1
  fi
  echo "── $key"
  echo "  uuid:   $uuid"
  echo "  source: $latest"

  if (( DRY == 1 )); then
    echo "  dry-run : no DB write"
    return 0
  fi

  local ts; ts=$(date +%Y-%m-%d-%H%M%S)
  local predump="/tmp/rollback_predump_${ts}_${uuid:0:8}.json"
  docker exec -i postgres-academie psql -U sinse -d academie_db -t -A \
    -c "SELECT graph FROM workflows WHERE id='$uuid';" > "$predump"
  echo "  predump: $predump"

  local graph_json
  graph_json=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(json.dumps(d['graph'], ensure_ascii=False))" "$latest")
  local escaped=${graph_json//\'/\'\'}
  docker exec -i postgres-academie psql -U sinse -d academie_db -v ON_ERROR_STOP=1 \
    -c "UPDATE workflows SET graph='$escaped'::jsonb, updated_at=NOW() WHERE id='$uuid';"
  echo "  restored OK"
}

fail=0
for k in "${TARGETS[@]}"; do
  restore_one "$k" || fail=1
done

(( fail == 0 )) && echo "━━━ rollback OK ━━━" || { echo "━━━ rollback had errors ━━━" >&2; exit 1; }
