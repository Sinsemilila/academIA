#!/usr/bin/env bash
# Refactor 2026-H2 Phase A1 — manual smoke test for Redis sessions + CSRF + logout.
# Bypasses Cloudflare Access by hitting backend directly on 127.0.0.1:8000.
# Usage : USERNAME=sinse PASSWORD=xxx TOTP=123456 bash scripts/sprint8/05_test_sessions_redis.sh
set -euo pipefail

API="${API:-http://127.0.0.1:8000}"
USER="${USERNAME:-sinse}"
PASS="${PASSWORD:?Set PASSWORD env var}"
JAR=$(mktemp -t cookie_jar.XXXXXX)
trap 'rm -f "$JAR"' EXIT

echo "=== 1. login (password) ==="
RES=$(curl -sX POST -c "$JAR" -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" \
  "$API/api/auth/login")
echo "  body: $RES"

if echo "$RES" | grep -q '"mfa_required":true'; then
  if [ -z "${TOTP:-}" ]; then
    echo "  ⚠ MFA enrolled but TOTP env not set ; aborting"
    exit 1
  fi
  echo ""
  echo "=== 1b. login-mfa ==="
  RES=$(curl -sX POST -b "$JAR" -c "$JAR" -H 'Content-Type: application/json' \
    -d "{\"username\":\"$USER\",\"password\":\"$PASS\",\"code\":\"$TOTP\"}" \
    "$API/api/auth/login-mfa")
  echo "  body: $RES"
fi

echo ""
echo "=== 2. cookies present in jar ==="
grep -E '__Host-as_session|csrf_token' "$JAR" | awk '{print "  ", $6, "=", substr($7,1,30)"..."}'

echo ""
echo "=== 3. /auth/me with cookies (expect 200) ==="
curl -sw '\n  HTTP %{http_code}\n' -b "$JAR" "$API/api/auth/me"

echo ""
echo "=== 4. POST mutation WITHOUT csrf header (expect 403 CSRF) ==="
curl -sw '\n  HTTP %{http_code}\n' -b "$JAR" -X POST -H 'Content-Type: application/json' \
  -d '{}' "$API/api/me/sessions" || true

echo ""
echo "=== 5. POST mutation WITH csrf header (expect 405 method not allowed = endpoint exists) ==="
CSRF=$(awk '/csrf_token/ {print $7}' "$JAR")
echo "  CSRF cookie value: ${CSRF:0:20}..."
curl -sw '\n  HTTP %{http_code}\n' -b "$JAR" -X POST -H 'Content-Type: application/json' \
  -H "X-CSRF-Token: $CSRF" -d '{}' "$API/api/me/sessions" || true

echo ""
echo "=== 6. /me/sessions list (expect 1 session = current) ==="
curl -s -b "$JAR" "$API/api/me/sessions"
echo ""

echo ""
echo "=== 7. Redis state ==="
docker exec redis-academie redis-cli KEYS 'session:*' | head -3
docker exec redis-academie redis-cli KEYS 'user_sessions:*'

echo ""
echo "=== 8. logout (expect 204 + cookies cleared) ==="
curl -sw '  HTTP %{http_code}\n' -b "$JAR" -c "$JAR" -X POST -H "X-CSRF-Token: $CSRF" \
  "$API/api/auth/logout"

echo ""
echo "=== 9. /auth/me after logout (expect 401) ==="
curl -sw '\n  HTTP %{http_code}\n' -b "$JAR" "$API/api/auth/me"

echo ""
echo "=== 10. Redis state (session purged) ==="
docker exec redis-academie redis-cli KEYS 'session:*' | head -3
echo "✅ Done"
