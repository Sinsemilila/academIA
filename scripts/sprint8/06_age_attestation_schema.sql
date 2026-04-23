-- Refactor 2026-H2 Phase A6 — age attestation column for users.
-- RGPD art. 8 / French law 15+ : self-attestation for alpha private. Full
-- parental consent flow deferred to Phase B1 (cf. minors-flow-roadmap.md).
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS age_attestation_at TIMESTAMP NULL;

COMMENT ON COLUMN users.age_attestation_at IS
  'Timestamp of the user attestation "I am 15+ or have parental authorization". '
  'NULL = legacy account pre-A6, manually backfilled by admin script if needed.';
