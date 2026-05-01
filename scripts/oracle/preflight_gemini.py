#!/usr/bin/env python3
"""Pre-flight check : can we run an Oracle mode today without hitting
Gemini Flash free-tier RPD quota? Reads live usage from
model_usage_daily (populated by the LiteLLM callback) and compares
against the stated limits.

Usage :
  python3 scripts/oracle/preflight_gemini.py --mode smoke
  python3 scripts/oracle/preflight_gemini.py --mode full --n-votes 1
  python3 scripts/oracle/preflight_gemini.py --calls 50

Exit code : 0 if safe (estimated calls ≤ remaining RPD budget), 1 if
would exceed. Stays quiet on success, loud on risk.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

# Observed per-model limits on Sinse's free-tier project, 2026-04-22.
# Limits are SEPARATE buckets per model → we sum them to get total budget.
# litellm_cache_stats.model is the raw provider name (not the alias),
# so queries use db_model while the chain order matches LiteLLM aliases.
GEMINI_CHAIN = [
    ("gemini-flash",           "gemini-2.5-flash",              20),
    ("gemini-3-flash",         "gemini-3-flash-preview",        20),
    ("gemini-3-1-flash-lite",  "gemini-3.1-flash-lite-preview", 500),
]
CUMULATED_RPD = sum(lim for _, _, lim in GEMINI_CHAIN)


def _rpd_used_today() -> dict[str, int]:
    """Return dict {alias → requests today} from litellm_cache_stats."""
    used = {alias: 0 for alias, _, _ in GEMINI_CHAIN}
    try:
        db_models_csv = ",".join(f"'{dbm}'" for _, dbm, _ in GEMINI_CHAIN)
        out = subprocess.check_output(
            [
                "docker", "exec", "-i", "postgres-academie",
                "psql", "-U", "sinse", "-d", "academie_db", "-tAc",
                f"SELECT model, COUNT(*) FROM litellm_cache_stats "
                f"WHERE model IN ({db_models_csv}) AND started_at::date = CURRENT_DATE "
                f"GROUP BY model;",
            ],
            text=True,
        ).strip()
        db_to_alias = {dbm: alias for alias, dbm, _ in GEMINI_CHAIN}
        for line in out.split("\n"):
            if "|" in line:
                m, n = line.split("|", 1)
                alias = db_to_alias.get(m.strip())
                if alias:
                    used[alias] = int(n.strip() or 0)
    except Exception:
        pass
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mode", choices=["lint", "smoke", "full"], help="Oracle mode")
    g.add_argument("--calls", type=int, help="Raw planned calls count")
    ap.add_argument("--n-votes", type=int, default=3,
                    help="Override N-majority votes (default 3, smoke uses 1)")
    args = ap.parse_args()

    if args.calls is not None:
        planned = args.calls
    elif args.mode == "lint":
        planned = 0
    elif args.mode == "smoke":
        planned = 6 * 1 * 3
    else:
        planned = 26 * args.n_votes * 3

    used = _rpd_used_today()
    total_used = sum(used.values())
    total_remaining = CUMULATED_RPD - total_used
    headroom = total_remaining - planned

    print("Gemini judge chain — budget check (limits are per-model)")
    for alias, _db, limit in GEMINI_CHAIN:
        u = used.get(alias, 0)
        print(f"  {alias:<24} {u:>4} / {limit} RPD")
    print(f"  {'TOTAL':<24} {total_used:>4} / {CUMULATED_RPD} RPD  "
          f"({total_remaining} remaining)")
    print(f"  planned run : {planned} calls ({args.mode or 'custom'}, n_votes={args.n_votes})")
    print(f"  headroom after run : {headroom}")
    if headroom < 0:
        print()
        print(f"  ❌ BLOCK : planned run would exceed cumulated RPD by {-headroom}.")
        print("     Options : reduce --n-votes, wait till 00:00 UTC reset,")
        print("     or upgrade to Tier 1 (pay-as-you-go, ~$0.15 per full run).")
        return 1
    elif headroom < CUMULATED_RPD * 0.1:
        print("  ⚠️  TIGHT : <10% of total RPD left after this run.")
        return 0
    else:
        print("  ✓ CLEAR : safe to launch.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
