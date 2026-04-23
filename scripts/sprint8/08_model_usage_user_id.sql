-- Refactor 2026-H2 Phase A5 — per-user cost-runaway telemetry.
-- Adds user_id column + replaces PK with (usage_date, model, user_id) using
-- NULLS NOT DISTINCT (PG 15+) so NULL = "system / un-attributable" rows
-- (Oracle judge, admin scripts) coexist with real user rows under one PK.
--
-- Idempotent : safe to re-run.
--
-- API impact : internal_router.ingest_model_usage MUST be updated to
-- include user_id in its INSERT and ON CONFLICT target.
ALTER TABLE model_usage_daily
  ADD COLUMN IF NOT EXISTS user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE model_usage_daily DROP CONSTRAINT IF EXISTS model_usage_daily_pkey;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'model_usage_daily_pkey'
      AND conrelid = 'model_usage_daily'::regclass
  ) THEN
    ALTER TABLE model_usage_daily
      ADD CONSTRAINT model_usage_daily_pkey
      PRIMARY KEY (usage_date, model, user_id);
    -- NULLS NOT DISTINCT requires using a UNIQUE INDEX, not a PK directly
    -- because PG forbids NULLs in PK columns. Adjust below.
  END IF;
EXCEPTION WHEN others THEN
  NULL; -- swallow if already exists
END$$;

-- PG forbids NULL in PK columns. Drop the PK attempt and use a UNIQUE INDEX
-- with NULLS NOT DISTINCT instead (functionally equivalent for upsert needs).
ALTER TABLE model_usage_daily DROP CONSTRAINT IF EXISTS model_usage_daily_pkey;

CREATE UNIQUE INDEX IF NOT EXISTS model_usage_daily_uniq
  ON model_usage_daily (usage_date, model, user_id) NULLS NOT DISTINCT;

CREATE INDEX IF NOT EXISTS idx_model_usage_user_date
  ON model_usage_daily (user_id, usage_date DESC) WHERE user_id IS NOT NULL;

COMMENT ON COLUMN model_usage_daily.user_id IS
  'Phase A5 — per-user attribution of LLM token consumption. NULL = system / non-user-attributable call (Oracle judge, admin script, etc.).';
