#!/usr/bin/env bash
# PgBouncer deployment + bootstrap (Phase 1.5).
# Generates runtime config under /opt/academia-shared/pgbouncer/ then starts container.
# Re-run safe: stops + removes existing pgbouncer container.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="/opt/academia-shared/pgbouncer"
AGE_KEY="${AGE_KEY:-/opt/academia-shared/secrets/age.key}"

mkdir -p "$RUNTIME_DIR"
cp "$HERE/pgbouncer.ini" "$RUNTIME_DIR/pgbouncer.ini"

# Generate userlist.txt from Postgres (uses SCRAM hash, never plain password)
HASHED=$(docker exec postgres-academie psql -U sinse -d postgres -t -A \
  -c "SELECT rolpassword FROM pg_authid WHERE rolname='sinse';")

cat > "$RUNTIME_DIR/userlist.txt" <<EOF
"sinse" "${HASHED}"
EOF
chmod 644 "$RUNTIME_DIR/userlist.txt"  # readable by container postgres user (uid 70)

docker rm -f pgbouncer 2>/dev/null || true
docker run -d \
  --name pgbouncer \
  --network academie-net-bridge \
  --restart unless-stopped \
  -v "$RUNTIME_DIR/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini:ro" \
  -v "$RUNTIME_DIR/userlist.txt:/etc/pgbouncer/userlist.txt:ro" \
  -p 127.0.0.1:6432:6432 \
  edoburu/pgbouncer:latest

sleep 3
docker logs pgbouncer 2>&1 | tail -5
