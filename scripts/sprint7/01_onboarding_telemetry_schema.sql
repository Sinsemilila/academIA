-- Session 43 P5 — Onboarding telemetry event stream.
--
-- One row per client-emitted event. A "session" = unique session_id
-- (UUIDv4 generated client-side, persisted in localStorage under
-- `academie:onboarding:session:{domain}`). Session_id survives reload
-- so a user who aborts and comes back is the same session.
--
-- Events :
--   step_enter : user navigated onto a step. Payload includes step_id
--                (item identifier or 'intro'/'summary') + step_order.
--   complete   : QCM submitted successfully. Emits from onComplete.
--   abort      : beforeunload fired before complete. Emits via
--                navigator.sendBeacon.
--
-- Funnel computation (admin endpoint) : per session_id, derive the
-- furthest step_order reached + completion flag. Aggregates give
-- step-to-step conversion.
--
-- Write path is unauthenticated : sendBeacon cannot attach
-- Authorization headers, and the abort event is the most valuable
-- signal. session_id shape is validated (UUIDv4) and eleve_id is
-- recorded when the current JWT is present, but not required.

CREATE TABLE IF NOT EXISTS onboarding_telemetry_events (
  id            BIGSERIAL PRIMARY KEY,
  session_id    TEXT NOT NULL,
  eleve_id      INTEGER,
  domain        TEXT NOT NULL,
  event         TEXT NOT NULL CHECK (event IN ('step_enter','complete','abort')),
  step_id       TEXT,
  step_order    INTEGER,
  total_steps   INTEGER,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS onboarding_telemetry_session_idx
  ON onboarding_telemetry_events (session_id);
CREATE INDEX IF NOT EXISTS onboarding_telemetry_domain_time_idx
  ON onboarding_telemetry_events (domain, created_at DESC);
CREATE INDEX IF NOT EXISTS onboarding_telemetry_event_time_idx
  ON onboarding_telemetry_events (event, created_at DESC);
