-- Refactor 2026-H2 Phase A4 — TOTP MFA enrollment per-user.
--
-- 1 row per user with TOTP enrolled. Absence of row = MFA disabled.
-- Recovery codes stored as bcrypt-hashed list (used-once, then nulled
-- to prevent reuse).
--
-- Phase A4a : secret stored plaintext base32. Acceptable alpha trade-off
-- (DB behind Cloudflare Access + sops-encrypted backups). Phase A4b will
-- migrate to Fernet at-rest encryption with key in webapp/.env.sops.

CREATE TABLE IF NOT EXISTS user_totp (
  user_id              INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  secret               TEXT NOT NULL,
  enrolled_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at         TIMESTAMPTZ,
  recovery_codes       JSONB NOT NULL DEFAULT '[]'::jsonb,
  recovery_codes_used  INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS user_totp_enrolled_at_idx
  ON user_totp (enrolled_at DESC);

COMMENT ON TABLE user_totp IS
  'TOTP MFA enrollment. See refactor 2026-H2 Phase A4 + runbook a4-mfa-totp.md.';
COMMENT ON COLUMN user_totp.recovery_codes IS
  'List of bcrypt-hashed recovery codes (10 codes generated at enrollment). Verified codes are nulled in-place ([null, "$2b$..", null, ...]) to prevent reuse.';
