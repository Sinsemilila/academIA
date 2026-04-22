-- Session 39 Block 1.2 — Phase D télémétrie cache hits.
--
-- Sidecar table in academie_db (NOT litellm_db). LiteLLM's Prisma
-- schema management drops ANY table it doesn't know about in its own
-- database at every restart ; we learned this the hard way by first
-- putting the table in litellm_db and watching it disappear.
--
-- Populated by LiteLLM custom callback → HTTP POST to academie-api
-- → asyncpg INSERT here (academie-api already has a pool for this DB).
--
-- Measures OpenAI prompt caching effectiveness : cached_tokens / prompt_tokens
-- indicates how much of the request hit the warm cache. Post-reorder Phase C
-- we expect this to climb from ~0 to ~15% on multi-turn conversations.
--
-- To apply : docker exec -i postgres-academie psql -U sinse -d academie_db \
--              < scripts/sprint6/16_litellm_cache_stats_schema.sql

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
