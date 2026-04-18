-- Sprint 5 Phase 2.2 — Dify Teacher minimal paramétrage (domain ISO)
--
-- Replaces the 6 technical occurrences of `domaine`/`anglais` in the Teacher
-- chatflow graph with new `domain`/`en`. Does NOT touch prompt text like
-- "professeur d'anglais" — that stays as French prose (Phase 3 `language-tutor`
-- will parameterize persona in one-shot).
--
-- Targets both published version (c52a451f...) and draft (ed0d1c91...).
-- Backup: dify_workflows_backup_sprint5 with pre-update graphs.

BEGIN;

-- Backup
CREATE TABLE IF NOT EXISTS dify_workflows_backup_sprint5 AS
SELECT id, version, graph, updated_at AS backed_up_at
FROM workflows
WHERE app_id = '39565197-c9d1-4d5b-b66f-18925de236d9';

-- Apply minimal substitutions to Teacher graph (both published + draft)
UPDATE workflows SET graph = REPLACE(
  REPLACE(
    REPLACE(graph,
      -- URL query param in HTTP node
      '&domaine=anglais', '&domain=en'),
    -- JSON key "domaine" (escaped inside JS code node string literals)
    '\"domaine\"', '\"domain\"'),
  -- JSON value "anglais" (escaped) — safe because prompt text has "anglais"
  -- only as a word inside longer French sentences, never with \" on both sides
  '\"anglais\"', '\"en\"')
WHERE app_id = '39565197-c9d1-4d5b-b66f-18925de236d9';

COMMIT;

-- Verification (run manually)
-- SELECT id, version, (graph LIKE '%&domaine=anglais%') has_old_url,
--                     (graph LIKE '%\"domaine\"%') has_old_key,
--                     (graph LIKE '%\"anglais\"%') has_old_val
-- FROM workflows WHERE app_id = '39565197-c9d1-4d5b-b66f-18925de236d9';
-- All three columns should be 'f' (false).
