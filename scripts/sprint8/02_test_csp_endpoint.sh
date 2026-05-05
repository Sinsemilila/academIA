#!/usr/bin/env bash
# Refactor 2026-H2 Phase A3 — manual smoke test for /api/csp-report.
# Usage : bash scripts/sprint8/02_test_csp_endpoint.sh
set -euo pipefail

API="${API:-http://127.0.0.1:8000}"

echo "=== Test 1 : valid legacy CSP report (expect 204) ==="
PAYLOAD='{"csp-report":{"document-uri":"https://academia.petit-pont.com/test","violated-directive":"script-src","blocked-uri":"https://evil.example.com/x.js","effective-directive":"script-src","disposition":"report"}}'
curl -sX POST -H 'Content-Type: application/csp-report' -d "$PAYLOAD" -w 'HTTP %{http_code}\n' "$API/api/csp-report"

echo ""
echo "=== Test 2 : modern Reporting API (expect 204) ==="
PAYLOAD2='[{"type":"csp-violation","age":10,"url":"https://academia.petit-pont.com/x","body":{"documentURL":"https://academia.petit-pont.com/x","blockedURL":"https://cdn.bad.example/x.js","effectiveDirective":"script-src","violatedDirective":"script-src","disposition":"report","statusCode":200}}]'
curl -sX POST -H 'Content-Type: application/reports+json' -d "$PAYLOAD2" -w 'HTTP %{http_code}\n' "$API/api/csp-report"

echo ""
echo "=== Test 3 : invalid JSON (expect 400) ==="
curl -sX POST -H 'Content-Type: application/csp-report' -d 'not json' -w 'HTTP %{http_code}\n' "$API/api/csp-report"

echo ""
echo "=== DB check (last 5 rows) ==="
docker exec postgres-academie psql -U sinse -d academie_db -c \
  "SELECT id, blocked_uri, effective_directive, disposition, reported_at FROM csp_violations ORDER BY id DESC LIMIT 5;"

echo ""
echo "=== Headers check (HTML page, bypass Cloudflare Access) ==="
curl -sI -H 'Host: academia.petit-pont.com' http://127.0.0.1:3001/ | grep -iE 'content-security|cross-origin|permissions|referrer|x-frame|x-content'
