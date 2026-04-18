-- Sprint 5 Phase 1.4 — FIX : n8n uses workflow_history.nodes (via activeVersionId)
-- for execution, not workflow_entity.nodes. Our initial script (02_update_n8n_workflows.py)
-- only touched workflow_entity — executions still ran OLD SQL with `p.domaine`.
--
-- Discovery : execution_data.workflowVersionId points to workflow_history entries
-- that were created at workflow creation time and persist independently of
-- workflow_entity updates. The `activeVersionId` column in workflow_entity
-- points at the history row actually executed.
--
-- This script applies the same string substitutions to workflow_history.
-- Backup: workflow_history_backup_sprint5 (created by first run).

BEGIN;

-- Backup (idempotent)
CREATE TABLE IF NOT EXISTS workflow_history_backup_sprint5 AS
SELECT * FROM workflow_history;

-- Apply substitutions
UPDATE workflow_history SET nodes = REPLACE(
  REPLACE(
    REPLACE(
      REPLACE(
        REPLACE(nodes::text,
          'body.domaine || ''anglais''', 'body.domaine'),
        'body.domain || ''anglais''', 'body.domain'),
      '"anglais"', '"en"'),
    '''anglais''', '''en'''),
  'domaine', 'domain')::json;

COMMIT;

-- Verification (run manually)
-- SELECT name, (nodes::text LIKE '%domaine%') FROM workflow_history;
-- All rows should show 'f' (false).
