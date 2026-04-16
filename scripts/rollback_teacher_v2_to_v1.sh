#!/bin/bash
# Rollback Teacher workflow: restore published V1 from a backup JSON.
# Usage: ./rollback_teacher_v2_to_v1.sh <backup-v1.json>
# Exits non-zero on any failure. Restarts dify-api after restore.
set -euo pipefail

PUBLISHED_ID="c52a451f-e381-46f1-a23a-077197b0fccb"
BACKUP="${1:-}"

if [[ -z "$BACKUP" || ! -s "$BACKUP" ]]; then
  echo "ERROR: backup file required and must be non-empty: '$BACKUP'"
  exit 1
fi

SIZE=$(wc -c < "$BACKUP")
echo "Backup: $BACKUP ($SIZE bytes)"

# Sanity check: backup must parse as JSON and be V1 (no rubric_for_level).
if grep -q 'rubric_for_level' "$BACKUP"; then
  echo "ERROR: backup appears to contain V2 vars (rubric_for_level found)."
  echo "Refusing to restore a V2 backup as V1."
  exit 2
fi

echo "Restoring published workflow $PUBLISHED_ID from $BACKUP ..."
# pg_read_file requires the postgres user to own/read the file; /tmp inside the
# container is owned by root and blocked for the postgres role. Stage inside
# /var/lib/postgresql/ (postgres home) with correct ownership.
TGT=/var/lib/postgresql/rollback-v1.json
docker cp "$BACKUP" "postgres-academie:$TGT"
docker exec postgres-academie chown postgres:postgres "$TGT"
docker exec postgres-academie psql -U sinse -d academie_db -v ON_ERROR_STOP=1 -c \
  "UPDATE workflows SET graph = pg_read_file('$TGT')::jsonb, updated_at = NOW() WHERE id = '$PUBLISHED_ID';"
docker exec postgres-academie rm -f "$TGT"

echo "Restarting dify-api dify-worker ..."
docker restart dify-api dify-worker >/dev/null

echo "Rollback complete. Verify:"
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT id, LENGTH(graph::text) AS bytes, (graph::text LIKE '%rubric_for_level%') AS has_v2, updated_at FROM workflows WHERE id='$PUBLISHED_ID';"
