-- Session 44 B — Model budget tracker (3-tier waterfall).
--
-- Two tables :
--
--   model_usage_daily   — per-day tokens per model. Populated by the
--                         LiteLLM cache_stats_callback when the model
--                         matches a groq tier. gpt-4o-mini keeps using
--                         its existing token_usage_daily row (pragma :
--                         no migration of historical rows, the budget
--                         endpoint reads both sources and merges).
--
--   model_switch_log    — audit trail of _switch_dify_model() calls.
--                         1 row per transition. The "current tier" is
--                         derived from MAX(at), so same-day restarts
--                         don't lose the active tier.

CREATE TABLE IF NOT EXISTS model_usage_daily (
  usage_date    DATE NOT NULL,
  model         TEXT NOT NULL,
  input_tokens  BIGINT NOT NULL DEFAULT 0,
  output_tokens BIGINT NOT NULL DEFAULT 0,
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (usage_date, model)
);

CREATE INDEX IF NOT EXISTS model_usage_daily_model_date_idx
  ON model_usage_daily (model, usage_date DESC);

CREATE TABLE IF NOT EXISTS model_switch_log (
  id         BIGSERIAL PRIMARY KEY,
  at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  from_model TEXT NOT NULL,
  to_model   TEXT NOT NULL,
  reason     TEXT
);

CREATE INDEX IF NOT EXISTS model_switch_log_at_idx
  ON model_switch_log (at DESC);
