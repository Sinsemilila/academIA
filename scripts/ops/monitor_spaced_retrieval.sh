#!/bin/bash
# Monitor spaced retrieval queue — Sprint 3 Phase 7.1 telemetry.
#
# Usage: ./monitor_spaced_retrieval.sh
#
# Prints a TOTAL row + per-eleve breakdown :
#   - enqueued         : rows inserted so far
#   - completed        : rows marked complete by the Teacher
#   - completion_pct   : completed / enqueued (target: trending up to ≥50% after 1w)
#   - hours_since_first: age of the oldest row (sanity — should grow with time)
#
# Thresholds to revisit around 2026-04-23 (7 days post-activation):
#   - If enqueued = 0 → no silenced errors detected → feature may not fire. Check academie-api logs
#   - If completion_pct = 0 → Teacher V2 never emits spaced_retrieval_addressed → prompt tuning needed
#   - If enqueued grows too fast (>10/user/day) → add dedupe cron (Phase 7.2)
set -euo pipefail

docker exec -i postgres-academie psql -U sinse -d academie_db <<'SQL'
\echo ── TOTAL ──
SELECT
  COUNT(*) AS enqueued,
  SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed,
  ROUND(100.0 * SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1) AS completion_pct,
  ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) / 3600.0, 1) AS hours_since_first
FROM spaced_retrieval_queue;

\echo ── PER ELEVE (top 20 by enqueued) ──
SELECT
  eleve_id,
  COUNT(*) AS enqueued,
  SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed,
  ROUND(100.0 * SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1) AS completion_pct
FROM spaced_retrieval_queue
GROUP BY eleve_id
ORDER BY enqueued DESC
LIMIT 20;

\echo ── BY ERROR FAMILY (top 10) ──
SELECT
  concept_key,
  COUNT(*) AS enqueued,
  SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS completed
FROM spaced_retrieval_queue
GROUP BY concept_key
ORDER BY enqueued DESC
LIMIT 10;
SQL
