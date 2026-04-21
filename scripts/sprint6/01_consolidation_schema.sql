-- Sprint 6 — CEFR consolidation schema (Session 36)
-- Idempotent : safe to re-run.
--
-- Adds:
--   profils_eleves.niveau_status : 5-value enum (provisoire, calibration_en_cours,
--                                   validé, stabilisation_volontaire, a_recalibrer)
--   profils_eleves.niveau_validated_at
--   profils_eleves.last_consolidation_turn
--   profils_eleves.consolidation_decision_pending (JSONB snapshot of pending decision)
--   profils_eleves.regression_watch_active + regression_watch_started_turn
--   user_sessions.observations_json (JSONB array: [{turn, observed_level, ts}])
--   consolidation_events audit table

BEGIN;

-- profils_eleves additions
ALTER TABLE profils_eleves
  ADD COLUMN IF NOT EXISTS niveau_status VARCHAR(32) DEFAULT 'provisoire',
  ADD COLUMN IF NOT EXISTS niveau_validated_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_consolidation_turn INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS consolidation_decision_pending JSONB,
  ADD COLUMN IF NOT EXISTS regression_watch_active BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS regression_watch_started_turn INTEGER;

-- CHECK constraint added separately so ADD COLUMN stays idempotent
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'profils_eleves_niveau_status_check'
  ) THEN
    ALTER TABLE profils_eleves
      ADD CONSTRAINT profils_eleves_niveau_status_check
      CHECK (niveau_status IN (
        'provisoire','calibration_en_cours','validé',
        'stabilisation_volontaire','a_recalibrer'
      ));
  END IF;
END $$;

-- user_sessions observations buffer
ALTER TABLE user_sessions
  ADD COLUMN IF NOT EXISTS observations_json JSONB DEFAULT '[]'::jsonb;

-- Audit trail
CREATE TABLE IF NOT EXISTS consolidation_events (
  id SERIAL PRIMARY KEY,
  eleve_id BIGINT NOT NULL REFERENCES eleves(id) ON DELETE CASCADE,
  domain VARCHAR(16) NOT NULL,
  triggered_at TIMESTAMPTZ DEFAULT NOW(),
  trigger_reason VARCHAR(32),            -- 'n_turns' | 'error_threshold' | 'dormancy_regression'
  qcm_level VARCHAR(5),
  observed_level VARCHAR(5),
  mini_exam_triggered BOOLEAN DEFAULT false,
  mini_exam_score_pct INTEGER,
  mini_exam_level VARCHAR(5),
  user_decision VARCHAR(32),             -- 'accept_new' | 'stay_current' | 'auto_validate' | 'pending'
  final_level VARCHAR(5),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_consolidation_eleve
  ON consolidation_events(eleve_id, domain, triggered_at DESC);

COMMIT;
