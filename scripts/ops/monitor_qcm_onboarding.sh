#!/bin/bash
# Sprint 5 Phase 5 — QCM onboarding activation monitoring.
# Usage : bash scripts/ops/monitor_qcm_onboarding.sh

set -euo pipefail

echo "=== learner_profiles inserts ==="
docker exec postgres-academie psql -U sinse -d academie_db -c "
SELECT
  domain,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE completed_at > NOW() - INTERVAL '1 hour') AS last_1h,
  COUNT(*) FILTER (WHERE completed_at > NOW() - INTERVAL '24 hours') AS last_24h,
  MAX(completed_at) AS latest
FROM learner_profiles
GROUP BY domain
ORDER BY domain;
"

echo ""
echo "=== Recent completed QCM (last 10) ==="
docker exec postgres-academie psql -U sinse -d academie_db -c "
SELECT id, eleve_id, domain,
       derived_tutor_hints->>'cefr_placement' AS cefr,
       derived_tutor_hints->>'fla_category'   AS fla,
       derived_tutor_hints->>'tutor_style'    AS style,
       completed_at
FROM learner_profiles
ORDER BY completed_at DESC
LIMIT 10;
"

echo ""
echo "=== Users WITH profils_eleves but WITHOUT learner_profiles (Session 32 legacy) ==="
docker exec postgres-academie psql -U sinse -d academie_db -c "
SELECT pe.eleve_id, pe.domain, pe.niveau_global, e.l1
FROM profils_eleves pe
JOIN eleves e ON e.id = pe.eleve_id
LEFT JOIN learner_profiles lp ON lp.eleve_id = pe.eleve_id AND lp.domain = pe.domain
WHERE lp.id IS NULL
ORDER BY pe.eleve_id, pe.domain;
"

echo ""
echo "=== academie-api warnings (last 50 'learner_profiles' log lines) ==="
docker logs academie-api 2>&1 | grep -i 'learner_profiles\|onboarding' | tail -50 || echo "(none)"

echo ""
echo "=== Rollback : flip flag + rebuild frontend ==="
echo "  sed -i \"s/QCM_ONBOARDING_ENABLED = true/QCM_ONBOARDING_ENABLED = false/\" /opt/academia/webapp/frontend/src/lib/config.ts"
echo "  cd /opt/academia/webapp && docker compose -f docker-compose.webapp.yml build academie-frontend && docker compose -f docker-compose.webapp.yml up -d academie-frontend"
