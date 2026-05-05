#!/usr/bin/env python3
"""Reset password for a user in academie_db.

Usage (interactive, password not echoed, never written to disk):
    python3 /opt/academia/scripts/reset_admin_password.py sinse

The script :
1. Prompts for a new password (hidden input)
2. Hashes it with bcrypt (matches auth.py production algorithm)
3. Connects to postgres-academie via docker exec
4. UPDATE users SET password_hash = '<new_hash>' WHERE username = '<user>'
5. Prints "OK" on success

Does NOT log the plaintext password. Does NOT persist it anywhere.
"""
from __future__ import annotations

import getpass
import subprocess
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: reset_admin_password.py <username>", file=sys.stderr)
        return 2
    username = sys.argv[1]

    try:
        import bcrypt
    except ImportError:
        print("pip install bcrypt first (or run this script from the academie-api container)",
              file=sys.stderr)
        return 2

    new_pw = getpass.getpass(f"New password for user {username!r}: ")
    confirm = getpass.getpass("Confirm: ")
    if new_pw != confirm:
        print("passwords do not match — aborting", file=sys.stderr)
        return 1
    if len(new_pw) < 8:
        print("password must be >= 8 chars", file=sys.stderr)
        return 1

    hash_bytes = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt(rounds=12))
    hash_str = hash_bytes.decode("utf-8")
    # Zero out the plaintext variable immediately
    new_pw = confirm = None

    # Escape single quotes for SQL safety (bcrypt output contains only base64 + $)
    hash_sql_safe = hash_str.replace("'", "''")
    sql = (
        f"UPDATE users SET password_hash = '{hash_sql_safe}' "
        f"WHERE username = '{username}' RETURNING username, is_admin;"
    )

    # Pipe SQL to psql via docker exec
    result = subprocess.run(
        ["docker", "exec", "-i", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db"],
        input=sql.encode("utf-8"),
        capture_output=True,
    )
    if result.returncode != 0:
        print("SQL error:", result.stderr.decode()[:500], file=sys.stderr)
        return 3
    out = result.stdout.decode()
    if "UPDATE 1" in out:
        print(f"OK — password reset for {username}")
        # Show rows affected (verify correct account)
        for line in out.splitlines():
            if "|" in line and username in line:
                print(f"  row: {line.strip()}")
        return 0
    else:
        print(f"WARN — UPDATE returned unexpected output:\n{out}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
