-- Sprint 5 Phase 1.1 — Unified DB migration for multi-language support
--
-- D1 : Rename `domaine` → `domain` on 6 tables + migrate values 'anglais' → 'en'
-- D2 : Move `l1` from profils_eleves to eleves (user-global), keep `l1_watch_enabled` per-profile
-- Add : error_log.domain column (+backfill + NOT NULL + index)
-- Rename : constraints/indexes that reference "domaine" for cleanliness
--
-- Forward migration — idempotent where possible, transactional as a whole.
-- Rollback available at 01_rollback_domain_iso.sql

BEGIN;

-- ───────────────────────────────────────────────────────────────────────
-- PART 1 — D1 : Rename `domaine` column to `domain` on all 6 tables
-- ───────────────────────────────────────────────────────────────────────

ALTER TABLE profils_eleves               RENAME COLUMN domaine TO domain;
ALTER TABLE spaced_retrieval_queue       RENAME COLUMN domaine TO domain;
ALTER TABLE snapshots_session            RENAME COLUMN domaine TO domain;
ALTER TABLE snapshots_session_v1_archive RENAME COLUMN domaine TO domain;
ALTER TABLE historique_sessions          RENAME COLUMN domaine TO domain;
ALTER TABLE curriculums                  RENAME COLUMN domaine TO domain;

-- ───────────────────────────────────────────────────────────────────────
-- PART 2 — D1 : Migrate values 'anglais' → 'en' (ISO 639-1)
-- ───────────────────────────────────────────────────────────────────────

UPDATE profils_eleves               SET domain = 'en' WHERE domain = 'anglais';
UPDATE spaced_retrieval_queue       SET domain = 'en' WHERE domain = 'anglais';
UPDATE snapshots_session            SET domain = 'en' WHERE domain = 'anglais';
UPDATE snapshots_session_v1_archive SET domain = 'en' WHERE domain = 'anglais';
UPDATE historique_sessions          SET domain = 'en' WHERE domain = 'anglais';
UPDATE curriculums                  SET domain = 'en' WHERE domain = 'anglais';

-- Verify no 'anglais' remains
DO $$
DECLARE
  anglais_count INT;
BEGIN
  SELECT (
    (SELECT COUNT(*) FROM profils_eleves               WHERE domain = 'anglais') +
    (SELECT COUNT(*) FROM spaced_retrieval_queue       WHERE domain = 'anglais') +
    (SELECT COUNT(*) FROM snapshots_session            WHERE domain = 'anglais') +
    (SELECT COUNT(*) FROM snapshots_session_v1_archive WHERE domain = 'anglais') +
    (SELECT COUNT(*) FROM historique_sessions          WHERE domain = 'anglais') +
    (SELECT COUNT(*) FROM curriculums                  WHERE domain = 'anglais')
  ) INTO anglais_count;
  IF anglais_count > 0 THEN
    RAISE EXCEPTION 'Migration failed: % rows still have domain=''anglais''', anglais_count;
  END IF;
END $$;

-- ───────────────────────────────────────────────────────────────────────
-- PART 3 — Rename indexes/constraints that reference "domaine" in name
-- ───────────────────────────────────────────────────────────────────────

ALTER INDEX profils_eleves_eleve_domaine_unique RENAME TO profils_eleves_eleve_domain_unique;
ALTER INDEX curriculums_domaine_niveau_key      RENAME TO curriculums_domain_niveau_key;

-- Note : the constraint names (pg_constraint) are auto-aliased via index rename
-- because these are UNIQUE constraints backed by those indexes.

-- ───────────────────────────────────────────────────────────────────────
-- PART 4 — D2 : Move `l1` from profils_eleves to eleves (user-global)
-- ───────────────────────────────────────────────────────────────────────

-- Add column to eleves with default
ALTER TABLE eleves ADD COLUMN l1 VARCHAR(2) DEFAULT 'fr';

-- Copy l1 from profils_eleves (take any row per user since currently only 1 profile each)
UPDATE eleves e SET l1 = COALESCE(
  (SELECT p.l1 FROM profils_eleves p WHERE p.eleve_id = e.id LIMIT 1),
  'fr'
);

-- Enforce NOT NULL
ALTER TABLE eleves ALTER COLUMN l1 SET NOT NULL;

-- Drop l1 from profils_eleves (l1_watch_enabled stays per-profile)
ALTER TABLE profils_eleves DROP COLUMN l1;

-- ───────────────────────────────────────────────────────────────────────
-- PART 5 — Add `domain` column to error_log with backfill
-- ───────────────────────────────────────────────────────────────────────

-- Add nullable first
ALTER TABLE error_log ADD COLUMN domain VARCHAR(10);

-- Backfill : all 137 current rows belong to users with only 'en' profiles
-- (verified pre-migration, see audit Session 26)
UPDATE error_log SET domain = 'en' WHERE domain IS NULL;

-- Verify no NULLs remain
DO $$
DECLARE
  null_count INT;
BEGIN
  SELECT COUNT(*) INTO null_count FROM error_log WHERE domain IS NULL;
  IF null_count > 0 THEN
    RAISE EXCEPTION 'Backfill failed: % rows still have domain=NULL', null_count;
  END IF;
END $$;

-- Enforce NOT NULL
ALTER TABLE error_log ALTER COLUMN domain SET NOT NULL;

-- Index for multi-domain analytics
CREATE INDEX idx_error_log_eleve_domain
  ON error_log(eleve_id, domain, created_at DESC);

-- Add non-unique index on profils_eleves(eleve_id, domain) for query perf
CREATE INDEX IF NOT EXISTS idx_profils_eleves_eleve_domain
  ON profils_eleves(eleve_id, domain);

COMMIT;

-- ───────────────────────────────────────────────────────────────────────
-- POST-MIGRATION VALIDATION (run manually after COMMIT)
-- ───────────────────────────────────────────────────────────────────────
-- SELECT DISTINCT domain FROM profils_eleves;        -- expect {'en'}
-- SELECT DISTINCT l1 FROM eleves;                    -- expect {'fr'}
-- SELECT COUNT(*) FROM error_log WHERE domain='en';  -- expect 137
-- SELECT COUNT(*) FROM information_schema.columns WHERE column_name='domaine' AND table_schema='public';  -- expect 0
