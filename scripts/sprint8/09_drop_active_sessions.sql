-- Refactor 2026-H2 Phase A1-cleanup — DROP active_sessions.
-- Replaced by Redis sessions in Session 46 (commit 941299b). Verified :
--   - 0 rows when this migration was authored (2026-04-23)
--   - sessions.py is the only writer/reader since A1 ship
--   - no FK references to this table from elsewhere
-- Rollback path : recreate from scripts/sprint5/03_create_active_sessions.sql
DROP TABLE IF EXISTS active_sessions;
