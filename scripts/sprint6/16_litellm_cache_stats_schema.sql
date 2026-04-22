-- Session 39 Block 1.2 — Phase D télémétrie cache hits.
--
-- Sidecar table (not ALTER on LiteLLM_SpendLogs — LiteLLM Prisma can
-- re-migrate it on upgrade and drop added columns). Populated by a
-- custom callback registered in litellm/config.yaml.
--
-- Measures OpenAI prompt caching effectiveness : cached_tokens / prompt_tokens
-- indicates how much of the request hit the warm cache. Post-reorder Phase C
-- we expect this to climb from ~0 to ~15% on multi-turn conversations.

CREATE TABLE IF NOT EXISTS litellm_cache_stats (
  request_id    TEXT PRIMARY KEY,
  started_at    TIMESTAMPTZ NOT NULL,
  model         TEXT NOT NULL,
  prompt_tokens INT  NOT NULL,
  cached_tokens INT  NOT NULL DEFAULT 0,
  user_id       TEXT,
  endpoint      TEXT
);

CREATE INDEX IF NOT EXISTS litellm_cache_stats_started_at_idx
  ON litellm_cache_stats (started_at DESC);
CREATE INDEX IF NOT EXISTS litellm_cache_stats_model_idx
  ON litellm_cache_stats (model);
