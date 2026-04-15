#!/usr/bin/env python3
"""Migration Sprint 2 Phase A — schema DB pour taxonomie v2.

Idempotent : re-runnable sans corruption. Toutes les additions utilisent
IF NOT EXISTS / ON CONFLICT.

Changements :
  1. error_log : +6 colonnes (tier, gravity_*, criterial_level_*) + index sur tier
  2. Nouvelles tables : l1_transfer_observations, domain_catalog, spaced_retrieval_queue
  3. snapshot cut-off : archive v1 + schema_version column (ADR-007 option C)

Safety :
  - Prendre pg_dump juste avant (voir docs/99-runbooks/migrate-taxonomy-v2.md)
  - Tous les ALTER TABLE ajoutent des colonnes nullable → aucun rejet de rows
    existantes, aucun impact prod applicatif.
"""
import subprocess
import sys

CONTAINER = "postgres-academie"
DB = "academie_db"
USER = "sinse"


def psql(sql: str, label: str = "", expect_rows: bool = False) -> str:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", USER, "-d", DB, "-c", sql],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  FAIL {label}: {result.stderr.strip()}")
        sys.exit(1)
    out = result.stdout.strip()
    if label:
        print(f"  OK   {label}")
    return out


def main():
    print("=== Migration Sprint 2 Phase A ===\n")

    # ═══════════════════════════════════════════════════════════
    # 1. Extension error_log
    # ═══════════════════════════════════════════════════════════
    print("[1/4] Extending error_log (6 new columns + index)...")
    psql(
        "ALTER TABLE error_log "
        "ADD COLUMN IF NOT EXISTS tier VARCHAR(3), "
        "ADD COLUMN IF NOT EXISTS gravity_linguistic FLOAT, "
        "ADD COLUMN IF NOT EXISTS gravity_communicative FLOAT, "
        "ADD COLUMN IF NOT EXISTS gravity_social FLOAT, "
        "ADD COLUMN IF NOT EXISTS criterial_level_emergence VARCHAR(3), "
        "ADD COLUMN IF NOT EXISTS criterial_level_mastery VARCHAR(3);",
        "6 columns added to error_log",
    )

    # CHECK constraints (named — re-addable only if absent)
    psql(
        "DO $$BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage "
        "WHERE table_name='error_log' AND constraint_name='chk_error_log_tier') THEN "
        "ALTER TABLE error_log ADD CONSTRAINT chk_error_log_tier "
        "CHECK (tier IS NULL OR tier IN ('T0','T1','T2','T3','T4')); "
        "END IF; "
        "END$$;",
        "CHECK constraint chk_error_log_tier",
    )
    psql(
        "DO $$BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage "
        "WHERE table_name='error_log' AND constraint_name='chk_error_log_criterial_emergence') THEN "
        "ALTER TABLE error_log ADD CONSTRAINT chk_error_log_criterial_emergence "
        "CHECK (criterial_level_emergence IS NULL OR criterial_level_emergence IN ('A1','A2','B1','B2','C1','C2')); "
        "END IF; "
        "END$$;",
        "CHECK constraint criterial_level_emergence",
    )
    psql(
        "DO $$BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage "
        "WHERE table_name='error_log' AND constraint_name='chk_error_log_criterial_mastery') THEN "
        "ALTER TABLE error_log ADD CONSTRAINT chk_error_log_criterial_mastery "
        "CHECK (criterial_level_mastery IS NULL OR criterial_level_mastery IN ('A1','A2','B1','B2','C1','C2')); "
        "END IF; "
        "END$$;",
        "CHECK constraint criterial_level_mastery",
    )
    psql(
        "CREATE INDEX IF NOT EXISTS idx_error_log_tier ON error_log(tier);",
        "index idx_error_log_tier",
    )

    # ═══════════════════════════════════════════════════════════
    # 2. Nouvelles tables
    # ═══════════════════════════════════════════════════════════
    print("\n[2/4] Creating new tables...")
    psql(
        "CREATE TABLE IF NOT EXISTS l1_transfer_observations ("
        "  source_profile VARCHAR(10) NOT NULL, "
        "  target_profile VARCHAR(10) NOT NULL, "
        "  error_family VARCHAR(50) NOT NULL, "
        "  n_observations BIGINT NOT NULL DEFAULT 0, "
        "  n_expected BIGINT, "
        "  multiplier FLOAT, "
        "  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(), "
        "  PRIMARY KEY (source_profile, target_profile, error_family)"
        ");",
        "table l1_transfer_observations",
    )

    psql(
        "CREATE TABLE IF NOT EXISTS domain_catalog ("
        "  domain_id VARCHAR(50) PRIMARY KEY, "
        "  domain_type VARCHAR(20) NOT NULL, "
        "  proficiency_scale VARCHAR(20) NOT NULL, "
        "  active BOOLEAN NOT NULL DEFAULT TRUE, "
        "  metadata JSONB NOT NULL DEFAULT '{}'::jsonb, "
        "  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        ");",
        "table domain_catalog",
    )
    psql(
        "INSERT INTO domain_catalog "
        "(domain_id, domain_type, proficiency_scale, active, metadata) "
        "VALUES "
        "('lang:en', 'language', 'CEFR', true, "
        " '{\"name\": \"English\", \"tutor_agent\": \"teacher_en\"}'::jsonb) "
        "ON CONFLICT (domain_id) DO NOTHING;",
        "seed domain_catalog lang:en",
    )

    psql(
        "CREATE TABLE IF NOT EXISTS spaced_retrieval_queue ("
        "  id SERIAL PRIMARY KEY, "
        "  eleve_id INTEGER NOT NULL REFERENCES eleves(id) ON DELETE CASCADE, "
        "  domaine VARCHAR(50) NOT NULL, "
        "  concept_key VARCHAR(100), "
        "  error_code VARCHAR(20), "
        "  scheduled_at TIMESTAMPTZ NOT NULL, "
        "  completed_at TIMESTAMPTZ, "
        "  outcome VARCHAR(20), "
        "  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
        ");",
        "table spaced_retrieval_queue",
    )
    psql(
        "CREATE INDEX IF NOT EXISTS idx_srq_eleve_schedule "
        "ON spaced_retrieval_queue(eleve_id, scheduled_at) "
        "WHERE completed_at IS NULL;",
        "partial index idx_srq_eleve_schedule",
    )

    # ═══════════════════════════════════════════════════════════
    # 3. Snapshot cut-off (ADR-007 option C)
    # ═══════════════════════════════════════════════════════════
    print("\n[3/4] Snapshot cut-off (archive v1 + schema_version)...")

    # 3a. Archive table : structure like original, then copy rows idempotently
    psql(
        "CREATE TABLE IF NOT EXISTS snapshots_session_v1_archive "
        "(LIKE snapshots_session INCLUDING DEFAULTS INCLUDING CONSTRAINTS);",
        "archive table snapshots_session_v1_archive",
    )
    # Explicit column projection: safe even after schema_version added to source
    psql(
        "INSERT INTO snapshots_session_v1_archive "
        "(id, eleve_id, domaine, contenu, created_at) "
        "SELECT s.id, s.eleve_id, s.domaine, s.contenu, s.created_at "
        "FROM snapshots_session s "
        "WHERE NOT EXISTS ("
        "  SELECT 1 FROM snapshots_session_v1_archive a WHERE a.id = s.id"
        ");",
        "archived existing snapshots",
    )

    # 3b. Add schema_version column with default 2
    psql(
        "ALTER TABLE snapshots_session "
        "ADD COLUMN IF NOT EXISTS schema_version INTEGER NOT NULL DEFAULT 2;",
        "schema_version column on snapshots_session",
    )

    # 3c. Backfill: rows created before this migration are v1
    # Use a marker to avoid re-doing on subsequent runs: only touch rows where
    # schema_version=2 AND no v1 marker, using the archive as truth.
    psql(
        "UPDATE snapshots_session SET schema_version = 1 "
        "WHERE id IN (SELECT id FROM snapshots_session_v1_archive) "
        "AND schema_version = 2;",
        "backfilled v1 rows to schema_version=1",
    )

    # ═══════════════════════════════════════════════════════════
    # 4. Verification
    # ═══════════════════════════════════════════════════════════
    print("\n[4/4] Verification...\n")

    print("  error_log columns (expecting 17 = 11 original + 6 new):")
    cols = psql(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'error_log' ORDER BY ordinal_position;",
    )
    for line in cols.split("\n"):
        line = line.strip()
        if line and not line.startswith(("-", "column_name", "(")):
            print(f"    {line}")

    print("\n  New tables present:")
    new_tables = psql(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name IN ('l1_transfer_observations', 'domain_catalog', "
        "'spaced_retrieval_queue', 'snapshots_session_v1_archive') "
        "ORDER BY table_name;",
    )
    for line in new_tables.split("\n"):
        line = line.strip()
        if line and not line.startswith(("-", "table_name", "(")):
            print(f"    ✓ {line}")

    print("\n  domain_catalog seed:")
    seed = psql("SELECT domain_id, domain_type FROM domain_catalog;")
    for line in seed.split("\n")[2:-1]:  # skip headers + count line
        if line.strip() and not line.startswith("-"):
            print(f"    {line.strip()}")

    print("\n  snapshots_session schema_version distribution:")
    dist = psql(
        "SELECT schema_version, COUNT(*) "
        "FROM snapshots_session GROUP BY schema_version ORDER BY schema_version;",
    )
    for line in dist.split("\n")[2:-1]:
        if line.strip() and not line.startswith("-"):
            print(f"    {line.strip()}")

    print("\n  snapshots_session_v1_archive row count:")
    arch = psql("SELECT COUNT(*) FROM snapshots_session_v1_archive;")
    for line in arch.split("\n")[2:-1]:
        if line.strip():
            print(f"    {line.strip()}")

    print("\n=== Migration complete ===")


if __name__ == "__main__":
    main()
