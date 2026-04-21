-- Session 38 — micro-lesson dedup log.
-- Tracks which (eleve, domain, family) has received a micro-lesson when,
-- so the `three_strikes` detector can skip families re-injected within
-- the last 3 days. Idempotent.

CREATE TABLE IF NOT EXISTS micro_lesson_log (
    id           BIGSERIAL PRIMARY KEY,
    eleve_id     INTEGER NOT NULL,
    domain       VARCHAR(10) NOT NULL,
    family       VARCHAR(40) NOT NULL,
    cefr_band    VARCHAR(3)  NOT NULL,
    injected_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_micro_lesson_log_eleve_family
    ON micro_lesson_log (eleve_id, domain, family, injected_at DESC);
