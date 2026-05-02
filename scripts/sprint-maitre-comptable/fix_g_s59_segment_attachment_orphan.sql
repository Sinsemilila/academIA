-- G-S59 fix — RAG "Invalid upload file" on certain queries.
--
-- Root cause : Dify DatabaseFileAccessController.apply_upload_file_filters
-- (api/core/app/file_access/controller.py L52-58) restricts upload_files
-- lookups to created_by_role=END_USER + created_by=current_user when called
-- via service API (/v1/chat-messages). PDF ingestion S58 created image
-- attachments under Sinse admin account (created_by_role='account'). When
-- knowledge retrieval returns chunks containing these images, LLM node tries
-- to load them via _retriever_attachment_loader.load() → access denied →
-- "Invalid upload file".
--
-- Fix : drop SegmentAttachmentBindings rows for the maitre-comptable dataset.
-- The underlying upload_files (images) remain untouched (re-bindable later
-- if needed via re-indexation). Marie doesn't see images in chat anyway —
-- she's text-only via SvelteKit frontend. Text RAG context preserved.
--
-- Applied 2026-05-02 14:55 UTC (Session 59), affected 4065 rows. Backup
-- table `segment_attachment_bindings_backup_2026_05_02` created in academie_db
-- before delete. Validated post-fix : 4/4 previously-failing queries
-- (Q08/Q09/Q11/Q12) succeed with RAG enabled.
--
-- Rollback : INSERT INTO segment_attachment_bindings SELECT * FROM
-- segment_attachment_bindings_backup_2026_05_02;

BEGIN;

-- 1. Backup
CREATE TABLE IF NOT EXISTS segment_attachment_bindings_backup_2026_05_02 AS
SELECT * FROM segment_attachment_bindings
WHERE segment_id IN (
    SELECT id FROM document_segments WHERE document_id IN (
        SELECT id FROM documents WHERE dataset_id = '79ab2618-5762-465d-9fab-b5ed54cff214'
    )
);

-- 2. Verify backup count
DO $$
DECLARE n INTEGER;
BEGIN
    SELECT COUNT(*) INTO n FROM segment_attachment_bindings_backup_2026_05_02;
    RAISE NOTICE 'Backup rows: %', n;
    IF n = 0 THEN
        RAISE EXCEPTION 'Backup is empty — abort';
    END IF;
END $$;

-- 3. Delete bindings for compta dataset only
DELETE FROM segment_attachment_bindings
WHERE segment_id IN (
    SELECT id FROM document_segments WHERE document_id IN (
        SELECT id FROM documents WHERE dataset_id = '79ab2618-5762-465d-9fab-b5ed54cff214'
    )
);

COMMIT;
