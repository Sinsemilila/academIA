#!/usr/bin/env bash
# Decrypt /opt/academie/litellm/config.yaml.sops → /opt/litellm/config.yaml.
# Run before `docker restart litellm-proxy` whenever config or keys change.
# Safe to re-run; writes atomically via temp file + mv.
set -euo pipefail

AGE_KEY="${AGE_KEY:-/opt/academie-shared/secrets/age.key}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/config.yaml.sops"
DST="/opt/litellm/config.yaml"

if [[ ! -r "$AGE_KEY" ]]; then
  echo "ERROR: age key not readable at $AGE_KEY" >&2
  echo "       (restore from password manager if host was wiped)" >&2
  exit 1
fi
if [[ ! -r "$SRC" ]]; then
  echo "ERROR: encrypted config not found at $SRC" >&2
  exit 1
fi

TMP="$(mktemp "${DST}.tmp.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

SOPS_AGE_KEY_FILE="$AGE_KEY" sops -d \
  --input-type yaml --output-type yaml "$SRC" > "$TMP"

chmod 644 "$TMP"
mv "$TMP" "$DST"
trap - EXIT
echo "Decrypted $SRC → $DST ($(wc -l <"$DST") lines)"
echo "Restart LiteLLM to apply: docker restart litellm-proxy"
