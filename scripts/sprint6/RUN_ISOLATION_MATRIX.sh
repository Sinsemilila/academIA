#!/usr/bin/env bash
# Session 39 Block 0.3 — Isolation matrix.
#
# Runs RUN_RECENT_BATTERY.sh --quiet four times with every combination of
# MICRO_LESSON_ENABLED × PRIORITY_CONCEPTS_ENABLED ∈ {false, true}.
# Lets us attribute any future regression to the right feature flag.
#
# LIMITATION : the overrides only bind to Python processes spawned by this
# wrapper (unit tests + local E2E in RUN_RECENT_BATTERY.sh). Tests that
# hit http://localhost:8000 against the live container still honour the
# .env compiled into the last academie-api rebuild. For those, re-run
# with a rebuilt container if the flag actually matters for the assertion.
# Acceptable for Session 39 : the unit/module layer is where regressions
# are most likely to surface, and rebuilding 4× would cost ~20 min for
# little gain.
#
# Exit 0 iff every combination passes.

set -u
REPO="/opt/academie"
cd "$REPO" || exit 2

declare -a RESULTS
BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; NC="\033[0m"

run_combo () {
    local micro="$1"
    local prio="$2"
    local label="MICRO=$micro PRIORITY=$prio"
    echo -e "\n${BOLD}▶ $label${NC}"
    if env \
        MICRO_LESSON_ENABLED="$micro" \
        PRIORITY_CONCEPTS_ENABLED="$prio" \
        SKIP_N8N_BLOCK=1 \
        bash "$REPO/scripts/sprint6/RUN_RECENT_BATTERY.sh" --quiet \
        > "/tmp/isomatrix_${micro}_${prio}.log" 2>&1; then
        RESULTS+=("PASS|$label")
        echo -e "  ${GREEN}✓ PASS${NC}  (log: /tmp/isomatrix_${micro}_${prio}.log)"
    else
        RESULTS+=("FAIL|$label")
        echo -e "  ${RED}✗ FAIL${NC}  (log: /tmp/isomatrix_${micro}_${prio}.log)"
        tail -20 "/tmp/isomatrix_${micro}_${prio}.log" | sed 's/^/    /'
    fi
}

for micro in false true; do
    for prio in false true; do
        run_combo "$micro" "$prio"
    done
done

echo -e "\n${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  ISOLATION MATRIX SCORECARD${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
PASS=0; FAIL=0
for r in "${RESULTS[@]}"; do
    status="${r%%|*}"; label="${r#*|}"
    if [[ "$status" == "PASS" ]]; then
        echo -e "  ${GREEN}✓${NC} $label"
        PASS=$((PASS+1))
    else
        echo -e "  ${RED}✗${NC} $label"
        FAIL=$((FAIL+1))
    fi
done
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  /  4 combinations"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
