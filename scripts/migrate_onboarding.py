#!/usr/bin/env python3
"""
Migration onboarding : colonnes profils_eleves + FK repair users↔eleves.
Safe to run multiple times (IF NOT EXISTS, ON CONFLICT DO NOTHING).
"""
import subprocess
import sys

CONTAINER = "postgres-academie"
DB = "academie_db"
USER = "sinse"


def psql(sql: str, label: str = "") -> str:
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
    print("=== Migration onboarding ===\n")

    # --- 1. Add columns to profils_eleves ---
    print("[1/3] Adding columns to profils_eleves...")
    psql(
        "ALTER TABLE profils_eleves "
        "ADD COLUMN IF NOT EXISTS details_par_competence JSONB, "
        "ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMPTZ, "
        "ADD COLUMN IF NOT EXISTS diagnostic_justification TEXT, "
        "ADD COLUMN IF NOT EXISTS auto_eval_level VARCHAR(4), "
        "ADD COLUMN IF NOT EXISTS diagnostic_exchange_count INTEGER;",
        "columns added",
    )

    # --- 2. Fix orphan users (no eleve_id) ---
    print("\n[2/3] Fixing orphan users...")
    orphans_out = psql(
        "SELECT id, username FROM users WHERE eleve_id IS NULL;",
    )
    if "0 rows" in orphans_out or "(0 rows)" in orphans_out:
        print("  No orphan users found — skipping")
    else:
        # Create missing eleves entries and link
        psql(
            "INSERT INTO eleves (username) "
            "SELECT u.username FROM users u "
            "WHERE u.eleve_id IS NULL "
            "AND NOT EXISTS (SELECT 1 FROM eleves e WHERE e.username = u.username) "
            "ON CONFLICT DO NOTHING;",
            "eleves entries created",
        )
        psql(
            "UPDATE users SET eleve_id = e.id "
            "FROM eleves e WHERE e.username = users.username "
            "AND users.eleve_id IS NULL;",
            "users linked to eleves",
        )

    # --- 3. Add FK constraint (if not exists) ---
    print("\n[3/3] Adding FK constraint users.eleve_id → eleves.id...")
    existing = psql(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_name = 'fk_users_eleve' AND table_name = 'users';",
    )
    if "(0 rows)" in existing:
        psql(
            "ALTER TABLE users "
            "ADD CONSTRAINT fk_users_eleve "
            "FOREIGN KEY (eleve_id) REFERENCES eleves(id);",
            "FK constraint added",
        )
    else:
        print("  FK constraint already exists — skipping")

    # --- Verify ---
    print("\n=== Verification ===")
    psql_out = psql(
        "SELECT u.id, u.username, u.eleve_id FROM users u ORDER BY u.id;",
        "user→eleve mapping",
    )
    print(psql_out)

    cols = psql(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'profils_eleves' "
        "AND column_name IN ('details_par_competence', 'onboarding_completed_at', "
        "'diagnostic_justification', 'auto_eval_level', 'diagnostic_exchange_count') "
        "ORDER BY column_name;",
        "new columns",
    )
    print(cols)

    print("\n=== Migration complete ===")


if __name__ == "__main__":
    main()
