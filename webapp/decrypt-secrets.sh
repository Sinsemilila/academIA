#!/usr/bin/env bash
# Decrypt webapp/.env.sops → webapp/.env using age key stored out-of-repo.
# Run this before `docker compose -f docker-compose.webapp.yml up -d`.
# Safe to re-run : overwrites .env every call.
set -euo pipefail

AGE_KEY="${AGE_KEY:-/opt/academie-shared/secrets/age.key}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -r "$AGE_KEY" ]]; then
  echo "ERROR: age key not readable at $AGE_KEY" >&2
  echo "       (restore from password manager if host was wiped)" >&2
  exit 1
fi

SOPS_AGE_KEY_FILE="$AGE_KEY" sops -d \
  --input-type dotenv --output-type dotenv \
  "$HERE/.env.sops" > "$HERE/.env.tmp"

mv "$HERE/.env.tmp" "$HERE/.env"
chmod 600 "$HERE/.env"
echo "Decrypted $HERE/.env.sops → $HERE/.env"
