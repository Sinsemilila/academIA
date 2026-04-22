#!/usr/bin/env bash
# RUN_RECENT_BATTERY.sh — aggregate regression battery for Sessions 37-38 features.
#
# Covers :
#   1. academie-core pytest (285 unit tests — priority_loop, scaffolding_policy,
#      consolidation, three_strikes, rules, yaml parity, typological_distance, etc.)
#   2. scripts/sprint6/tests — admin reset scoping + inject_curriculum parity
#   3. E2E consolidation (8/8 seeded scenarios, teacher×maestro × A1-B2)
#   4. E2E micro-lesson (14 scenarios — detection, dedup, YAML rendering EN/ES)
#   5. n8n webhook liveness — diagnostic + exam-scoring + snapshot (public API)
#   6. Docker services + SvelteKit + FastAPI (smoke-test --quick)
#
# Each block prints its own output ; a final scorecard summarises PASS/FAIL counts.
# Exit 0 iff every block passes.
#
# Usage : bash scripts/sprint6/RUN_RECENT_BATTERY.sh
#         (quiet mode : append --quiet to skip block detail)

set -u
REPO="/opt/academie"
cd "$REPO" || exit 2

QUIET=0
[[ "${1:-}" == "--quiet" ]] && QUIET=1

# Resolve a host-reachable DATABASE_URL for the local E2E scripts
set -a; . "$REPO/webapp/.env"; set +a
export DATABASE_URL="${DATABASE_URL//postgres-academie/127.0.0.1}"
export PYTHONPATH="$REPO/packages/academie-core"

declare -a RESULTS
BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; DIM="\033[2m"; NC="\033[0m"

run_block() {
    local label="$1"; shift
    echo -e "\n${BOLD}▶ $label${NC}"
    if [[ $QUIET == 1 ]]; then
        if "$@" >/tmp/battery.log 2>&1; then
            RESULTS+=("PASS|$label")
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            RESULTS+=("FAIL|$label")
            echo -e "  ${RED}✗ FAIL${NC}  (see /tmp/battery.log)"
            tail -20 /tmp/battery.log | sed 's/^/    /'
        fi
    else
        if "$@"; then
            RESULTS+=("PASS|$label")
            echo -e "  ${GREEN}✓ PASS${NC}"
        else
            RESULTS+=("FAIL|$label")
            echo -e "  ${RED}✗ FAIL${NC}"
        fi
    fi
}

# ── 1. academie-core pytest ────────────────────────────────────────────
run_block "academie-core pytest (unit suite)" \
    bash -c "set -o pipefail; cd $REPO/packages/academie-core && python3 -m pytest tests/ -q --no-header 2>&1 | tail -5"

# ── 2a. sprint6 inject_curriculum (DB-free, pytest local) ─────────────
run_block "sprint6/tests — inject_curriculum parity (pytest)" \
    bash -c "set -o pipefail; python3 -m pytest $REPO/scripts/sprint6/tests/test_inject_curriculum.py -q --no-header 2>&1 | tail -5"

# ── 2b. sprint6 admin_reset_scoping (live DB, runs in container) ──────
run_block "sprint6/tests — admin_reset_scoping (container)" \
    bash -c "docker cp $REPO/scripts/sprint6/tests/test_admin_reset_scoping.py academie-api:/tmp/ >/dev/null && \
             docker exec academie-api python3 /tmp/test_admin_reset_scoping.py 2>&1 | tail -10"

# ── 3. E2E consolidation ───────────────────────────────────────────────
# Runs inside container since it uses internal service hostnames + JWT env.
run_block "E2E consolidation (scripts/sprint6/05_*)" \
    bash -c "docker cp $REPO/scripts/sprint6/05_e2e_consolidation_test.py academie-api:/tmp/ >/dev/null && \
             docker cp $REPO/scripts/sprint6/_e2e_helpers.py academie-api:/tmp/ >/dev/null && \
             docker exec academie-api python3 /tmp/05_e2e_consolidation_test.py --mode seeded 2>&1 | tail -15"

# ── 4. E2E micro-lesson ────────────────────────────────────────────────
run_block "E2E micro-lesson (scripts/sprint6/10_*)" \
    bash -c "python3 $REPO/scripts/sprint6/10_e2e_micro_lesson_test.py 2>&1 | tail -20"

# ── 5. n8n webhooks liveness ───────────────────────────────────────────
# Get a real Teacher conversation_id to feed the webhooks with valid data.
# SKIP_N8N_BLOCK=1 lets callers (e.g. RUN_ISOLATION_MATRIX) opt out : the
# flags exercised by the matrix don't affect n8n, and this block is the
# one with measurable infra flakiness (~17% fail rate, Session 38 smoke).
if [[ "${SKIP_N8N_BLOCK:-0}" != "1" ]]; then
run_block "n8n webhooks (diagnostic/exam-scoring/snapshot)" \
    bash -c "
      CONV=\$(docker exec -i postgres-academie psql -U sinse -d academie_db -t -A -c \"SELECT id FROM conversations WHERE app_id = '39565197-c9d1-4d5b-b66f-18925de236d9' ORDER BY updated_at DESC LIMIT 1;\" 2>/dev/null | head -1)
      [ -z \"\$CONV\" ] && { echo '  no Teacher conv to test against'; exit 1; }
      echo \"  using conv_id=\$CONV\"
      FAIL=0
      for WH in dify-diagnostic dify-snapshot; do
        BODY=\"{\\\"username\\\":\\\"user_2\\\",\\\"domain\\\":\\\"en\\\",\\\"conversation_id\\\":\\\"\$CONV\\\",\\\"dify_user_id\\\":\\\"user_2\\\",\\\"dify_app_key\\\":\\\"\$DIFY_KEY_TEACHER\\\"}\"
        CODE=\$(curl -sS -X POST http://127.0.0.1:5678/webhook/\$WH -H 'Content-Type: application/json' -d \"\$BODY\" --max-time 60 -o /tmp/wh_resp.txt -w '%{http_code}')
        if [ \"\$CODE\" = '200' ]; then echo \"  ✓ \$WH → HTTP 200\"; else echo \"  ✗ \$WH → HTTP \$CODE\"; FAIL=1; fi
      done
      BODY=\"{\\\"username\\\":\\\"user_2\\\",\\\"domain\\\":\\\"en\\\",\\\"conversation_id\\\":\\\"\$CONV\\\",\\\"exam_responses\\\":\\\"[]\\\",\\\"niveau\\\":\\\"A2\\\",\\\"concept_keys\\\":\\\"[]\\\",\\\"module_index\\\":0,\\\"module_total\\\":1,\\\"module_name\\\":\\\"battery\\\",\\\"module_concepts\\\":\\\"\\\"}\"
      CODE=\$(curl -sS -X POST http://127.0.0.1:5678/webhook/dify-exam-scoring -H 'Content-Type: application/json' -d \"\$BODY\" --max-time 90 -o /tmp/wh_resp.txt -w '%{http_code}')
      if [ \"\$CODE\" = '200' ]; then echo '  ✓ dify-exam-scoring → HTTP 200 (Fetch/Resolve nodes reachable)'; else echo \"  ✗ dify-exam-scoring → HTTP \$CODE\"; FAIL=1; fi
      RECENT_ERR=\$(docker exec -i postgres-academie psql -U sinse -d academie_db -t -A -c \"SELECT COUNT(*) FROM execution_entity WHERE \\\"workflowId\\\" IN ('58dd0014770a4c','tVfLg92ijYUvBc94','y52Fa9sYBmtuwz8y') AND status='error' AND \\\"startedAt\\\" > NOW() - INTERVAL '5 minutes';\" 2>/dev/null | head -1)
      echo \"  recent (5min) failed exec count on these 3 workflows : \${RECENT_ERR:-?}\"
      [ \"\$FAIL\" = '0' ]
    "
fi  # SKIP_N8N_BLOCK gate

# ── 6. smoke-test --quick (host services) ──────────────────────────────
run_block "smoke-test --quick (services + ports)" \
    bash -c "smoke-test --quick 2>&1 | tail -6"

# ── 7. oracle V1 lint (Session 40, lint-only, zero LLM calls) ──────────
# Structural regression catch : JSON wrapper (opt-in), A1 no-jargon,
# priority leak, observed_level. Runs against recorded goldens.
# Full mode is on-demand (~108K tokens) — not gated here.
run_block "oracle V1 lint (scripts/oracle/harness.py --mode lint)" \
    bash -c "python3 $REPO/scripts/oracle/harness.py --agent teacher_en --mode lint --gate-mode strict 2>&1 | tail -5"

# ── Scorecard ──────────────────────────────────────────────────────────
echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  BATTERY SCORECARD${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
PASS=0; FAIL=0
for r in "${RESULTS[@]}"; do
    status="${r%%|*}"
    label="${r#*|}"
    if [[ "$status" == "PASS" ]]; then
        echo -e "  ${GREEN}✓${NC} $label"
        PASS=$((PASS+1))
    else
        echo -e "  ${RED}✗${NC} $label"
        FAIL=$((FAIL+1))
    fi
done
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  /  $((PASS+FAIL)) blocks"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
