#!/usr/bin/env bash
# Decrypt secrets/shared.yaml.sops → one file per key under
# /opt/academie-shared/secrets/<name> (chmod 600, trailing \n added).
# Consumers: scripts/*, restic-backup, n8n, etc. — they read file paths,
# not env vars, so we reproduce the original layout exactly.
set -euo pipefail

AGE_KEY="${AGE_KEY:-/opt/academie-shared/secrets/age.key}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/shared.yaml.sops"
TARGET_DIR="/opt/academie-shared/secrets"

if [[ ! -r "$AGE_KEY" ]]; then
  echo "ERROR: age key not readable at $AGE_KEY" >&2
  exit 1
fi
if [[ ! -r "$SRC" ]]; then
  echo "ERROR: encrypted bundle not found at $SRC" >&2
  exit 1
fi

# Decrypt to a temp file once, then iterate keys.
PLAIN="$(mktemp)"
trap 'rm -f "$PLAIN"' EXIT
SOPS_AGE_KEY_FILE="$AGE_KEY" sops -d \
  --input-type yaml --output-type yaml "$SRC" > "$PLAIN"

written=0
# Parse KEY: 'VALUE' lines (yaml single-quoted strings, '' escapes a single quote).
while IFS= read -r line; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  key="${line%%:*}"
  # strip leading space after colon + surrounding single quotes
  raw="${line#*: }"
  # unquote if wrapped in single quotes
  if [[ "$raw" == \'*\' ]]; then
    raw="${raw:1:${#raw}-2}"
    raw="${raw//\'\'/\'}"  # unescape doubled single quotes
  fi
  dst="$TARGET_DIR/$key"
  tmp="$(mktemp "${dst}.tmp.XXXXXX")"
  printf '%s\n' "$raw" > "$tmp"
  chmod 600 "$tmp"
  # preserve original ownership if the target file already exists
  if [[ -e "$dst" ]]; then
    chown --reference="$dst" "$tmp"
  fi
  mv "$tmp" "$dst"
  written=$((written + 1))
done < "$PLAIN"

echo "Wrote $written secret files to $TARGET_DIR/ (chmod 600, trailing \\n)"
