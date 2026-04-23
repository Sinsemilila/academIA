-- Refactor 2026-H2 Phase A4b polish — WebAuthn / Passkeys scaffolding.
-- Schema only; activation behind WEBAUTHN_ENABLED feature flag. Real impl
-- planned Phase 2 (post-beta) per ADR-001 décision #7.
-- Idempotent.
CREATE TABLE IF NOT EXISTS webauthn_credentials (
  id              SERIAL PRIMARY KEY,
  user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  credential_id   BYTEA NOT NULL UNIQUE,
  public_key      BYTEA NOT NULL,
  sign_count      BIGINT NOT NULL DEFAULT 0,
  aaguid          UUID,
  transports      TEXT[],
  nickname        VARCHAR(100),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_webauthn_user ON webauthn_credentials(user_id);
COMMENT ON TABLE webauthn_credentials IS
  'Phase A4b polish — Passkeys/WebAuthn scaffolding. Activation Phase 2 post-beta.';
