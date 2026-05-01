#!/usr/bin/env bash
# Re-applies the runtime Dify Start-node max_length bump 10000→50000 for the
# `concept_hints_json` variable on Teacher EN + Maestro ES workflows.
#
# Context : S54 incident 2026-05-01 — concept_hints_json YAML expanded past
# default Dify cap (en 19.5K / es 12.7K vs cap 10K) → worker ValueError →
# backend SSE ReadTimeout → frontend "Erreur de connexion".
#
# Backend commit a7a4465 added load_concept_hints_for_level filter, so payload
# usually fits under 10K for ≤B1 learners. This bump remains a safety net for
# B2+ learners (worst case 19.5K EN C2). Re-run after any Dify reset / DB
# restore that loses the in-place workflow edit.
#
# Usage : bash scripts/runbooks/dify_bump_concept_hints_max_length.sh
set -euo pipefail

EN_APP=39565197-c9d1-4d5b-b66f-18925de236d9
ES_APP=47b0529c-b3a3-4651-8717-759e666172c9

for app_id in "$EN_APP" "$ES_APP"; do
  for ver in "draft" "2026-04-20 10:21:44.230845"; do
    docker exec postgres-academie psql -U sinse -d academie_db -c \
      "UPDATE workflows SET graph = replace(graph,
         '\"variable\": \"concept_hints_json\", \"max_length\": 10000',
         '\"variable\": \"concept_hints_json\", \"max_length\": 50000'),
       updated_at = NOW()
       WHERE app_id = '${app_id}' AND version = '${ver}';"
  done
done

# Verify
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT app_id, version,
          position('\"variable\": \"concept_hints_json\", \"max_length\": 50000' IN graph) > 0 AS patched
   FROM workflows
   WHERE app_id IN ('${EN_APP}', '${ES_APP}')
     AND version IN ('draft', '2026-04-20 10:21:44.230845')
   ORDER BY app_id, version;"
