-- Session 44 V2 — rate-limit snapshot (header-based tracker).
--
-- Last-observed x-ratelimit-* values per model, UPSERTed on every
-- successful LLM response by the LiteLLM callback. 1 row per model.
-- This is the authoritative live counter ; /api/admin/model-budgets
-- prefers this over the Usage API reconcile when available.

CREATE TABLE IF NOT EXISTS model_rate_snapshot (
  model              TEXT PRIMARY KEY,
  limit_requests     BIGINT,
  remaining_requests BIGINT,
  reset_requests_sec INTEGER,
  limit_tokens       BIGINT,
  remaining_tokens   BIGINT,
  reset_tokens_sec   INTEGER,
  observed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
