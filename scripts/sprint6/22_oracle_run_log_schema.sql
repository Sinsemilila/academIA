-- Session 42 O2 — Oracle run log sidecar table for dashboard analytics.
--
-- One row per (oracle run, scenario, dim). Rows grouped by run_hash
-- to aggregate a single run across scenarios/dims.
--
-- Populated by scripts/oracle/harness.py post-run (best-effort INSERT,
-- swallow errors so oracle never fails because of telemetry).
--
-- Indexed on (agent, mode, started_at DESC) for dashboard "recent runs"
-- queries, and (dim, started_at DESC) for per-dim trend charts.

CREATE TABLE IF NOT EXISTS oracle_run_log (
  id            BIGSERIAL PRIMARY KEY,
  run_hash      TEXT NOT NULL,           -- groups scenario rows of one run
  started_at    TIMESTAMPTZ NOT NULL,
  agent         TEXT NOT NULL,           -- teacher_en | maestro_es
  mode          TEXT NOT NULL,           -- lint | smoke | full
  scenario_id   TEXT NOT NULL,
  dim           TEXT NOT NULL,           -- dim name (or 'lint' for lint-layer)
  verdict       TEXT NOT NULL,           -- pass | fail | skip | unknown
  score         REAL,                    -- optional numeric score
  judge_votes   JSONB,                   -- raw majority-vote outputs
  reasoning     TEXT,                    -- 1-line summary
  sha           TEXT                      -- git SHA at run time
);

CREATE INDEX IF NOT EXISTS oracle_run_log_agent_mode_time_idx
  ON oracle_run_log (agent, mode, started_at DESC);
CREATE INDEX IF NOT EXISTS oracle_run_log_dim_time_idx
  ON oracle_run_log (dim, started_at DESC);
CREATE INDEX IF NOT EXISTS oracle_run_log_run_hash_idx
  ON oracle_run_log (run_hash);
