#!/bin/bash
# R1 fix S59 — Dify inner-API auth config to enable plugin daemon backwards-invocation.
#
# Root cause: dify-api 1.14.0 reads INNER_API + INNER_API_KEY_FOR_PLUGIN env vars
# (Pydantic Settings BaseSettings). On our cosmos these were never set, defaulting
# to INNER_API=False (entire /inner/api/* blueprint disabled at runtime —
# `plugin_inner_api_only` decorator returns abort(404) when PLUGIN_DAEMON_KEY
# unset OR INNER_API_KEY_FOR_PLUGIN mismatch). The plugin daemon sends
# X-Inner-Api-Key=$DIFY_INNER_API_KEY (which IS set on cosmos
# = "nk0oHgBInsUrBbjcATzs6P-FBWGgyaAxwoJr4qxUNqA") but dify-api expects
# the same value at INNER_API_KEY_FOR_PLUGIN, which was unset → defaulted to
# the literal "inner-api-key" → mismatch → abort(404) → flask-restx renders
# the misleading "did you mean /inner/api/invoke/llm" 404 page that looked
# like a routing failure (cf vault/projects/academia-ia/failures.md
# 2026-05-02 16:30 — original misdiagnosis).
#
# This fix patches the Pydantic Settings DEFAULTS in dify-api Python config
# so the values stick even without env vars. Two locations in
# /app/api/configs/feature/__init__.py :
#
#   INNER_API: bool                     default=False  → True
#   INNER_API_KEY_FOR_PLUGIN: str       default="inner-api-key"
#                                       → "<daemon DIFY_INNER_API_KEY value>"
#
# Persistence note: hot-patch on the dify-api container's filesystem.
# Survives `docker restart`. LOST at `docker rm + run` (image rebuild).
# When/if cosmos rebuilds dify-api image, re-run this script. Long-term
# proper fix : add env vars at deploy time (compose/run).
#
# Validated S59 2026-05-02: agent_compta + langgenius/agent function_calling
# strategy now executes tool calls (verify_partie_double, lookup_pcg,
# verify_calcul_tva, verify_compte_classe, lookup_studi_module) end-to-end.
# Workflow trace confirms `action_name=lookup_pcg` etc with valid `observation`
# returns from academie-api.
#
# Rollback: docker cp ${ORIG_BACKUP} dify-api:/app/api/configs/feature/__init__.py
#           docker restart dify-api
#
# Usage: ./fix_r1_dify_inner_api.sh
set -e

DAEMON_KEY=$(docker exec dify-plugin-daemon env | grep '^DIFY_INNER_API_KEY=' | cut -d= -f2)
if [ -z "$DAEMON_KEY" ]; then
    echo "ERROR: DIFY_INNER_API_KEY not set in dify-plugin-daemon" >&2
    exit 1
fi
echo "Daemon key fingerprint: ${DAEMON_KEY:0:20}..."

ORIG=/tmp/feature_init_orig_$(date +%s).py
docker cp dify-api:/app/api/configs/feature/__init__.py "$ORIG"
echo "Backup → $ORIG"

PATCHED=/tmp/feature_init_patched.py
cp "$ORIG" "$PATCHED"
python3 <<EOF
src = open("$PATCHED").read()
src = src.replace(
    'INNER_API_KEY_FOR_PLUGIN: str = Field(description="Inner api key for plugin", default="inner-api-key")',
    'INNER_API_KEY_FOR_PLUGIN: str = Field(description="Inner api key for plugin", default="${DAEMON_KEY}")  # S59 R1 hot-patch — match daemon DIFY_INNER_API_KEY'
)
src = src.replace(
    '    INNER_API: bool = Field(\n        description="Enable or disable the internal API",\n        default=False,\n    )',
    '    INNER_API: bool = Field(\n        description="Enable or disable the internal API",\n        default=True,  # S59 R1 hot-patch — required for plugin daemon backwards-invocation\n    )'
)
open("$PATCHED", "w").write(src)
EOF

if ! diff -q "$ORIG" "$PATCHED" > /dev/null; then
    docker cp "$PATCHED" dify-api:/app/api/configs/feature/__init__.py
    echo "Patched applied. Restarting dify-api..."
    docker restart dify-api
    for i in 1 2 3 4 5 6 7 8 9 10; do
        sleep 3
        status=$(docker exec dify-api curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health 2>/dev/null)
        echo "  iter $i health=$status"
        if [ "$status" = "200" ]; then break; fi
    done
    echo
    echo "Verification:"
    docker exec dify-api python3 -c "from configs import dify_config; print('  INNER_API:', dify_config.INNER_API); print('  INNER_API_KEY_FOR_PLUGIN[:20]:', dify_config.INNER_API_KEY_FOR_PLUGIN[:20])"
else
    echo "No diff — patches already applied or signatures changed."
fi
