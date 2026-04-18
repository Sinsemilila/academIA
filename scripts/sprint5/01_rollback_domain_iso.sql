-- Sprint 5 Phase 1.1 — ROLLBACK script
-- Reverses 01_migrate_domain_iso.sql step by step
-- Restore eleves.l1 → profils_eleves.l1, values 'en' → 'anglais', column renames

BEGIN;

-- Undo PART 5 — error_log.domain
DROP INDEX IF EXISTS idx_error_log_eleve_domain;
DROP INDEX IF EXISTS idx_profils_eleves_eleve_domain;
ALTER TABLE error_log DROP COLUMN domain;

-- Undo PART 4 — L1 move
ALTER TABLE profils_eleves ADD COLUMN l1 VARCHAR(2) DEFAULT 'fr';
UPDATE profils_eleves p SET l1 = COALESCE((SELECT e.l1 FROM eleves e WHERE e.id = p.eleve_id), 'fr');
ALTER TABLE eleves DROP COLUMN l1;

-- Undo PART 3 — rename indexes back
ALTER INDEX profils_eleves_eleve_domain_unique RENAME TO profils_eleves_eleve_domaine_unique;
ALTER INDEX curriculums_domain_niveau_key      RENAME TO curriculums_domaine_niveau_key;

-- Undo PART 2 — values 'en' → 'anglais'
UPDATE profils_eleves               SET domain = 'anglais' WHERE domain = 'en';
UPDATE spaced_retrieval_queue       SET domain = 'anglais' WHERE domain = 'en';
UPDATE snapshots_session            SET domain = 'anglais' WHERE domain = 'en';
UPDATE snapshots_session_v1_archive SET domain = 'anglais' WHERE domain = 'en';
UPDATE historique_sessions          SET domain = 'anglais' WHERE domain = 'en';
UPDATE curriculums                  SET domain = 'anglais' WHERE domain = 'en';

-- Undo PART 1 — rename column back
ALTER TABLE profils_eleves               RENAME COLUMN domain TO domaine;
ALTER TABLE spaced_retrieval_queue       RENAME COLUMN domain TO domaine;
ALTER TABLE snapshots_session            RENAME COLUMN domain TO domaine;
ALTER TABLE snapshots_session_v1_archive RENAME COLUMN domain TO domaine;
ALTER TABLE historique_sessions          RENAME COLUMN domain TO domaine;
ALTER TABLE curriculums                  RENAME COLUMN domain TO domaine;

COMMIT;
