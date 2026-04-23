-- Refactor 2026-H2 Phase B4 — create dedicated DB for GlitchTip self-hosted.
-- Hosted on the shared postgres-academie instance (alongside academie_db + litellm_db).
-- Idempotent : safe to re-run.
SELECT 'CREATE DATABASE glitchtip_db OWNER sinse'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'glitchtip_db')\gexec

GRANT ALL PRIVILEGES ON DATABASE glitchtip_db TO sinse;
