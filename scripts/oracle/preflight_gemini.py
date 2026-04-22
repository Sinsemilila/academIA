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

# Observed limits on Sinse's free-tier project, 2026-04-22.
# Google may raise back to 250 RPD at any time — re-check console.
DEFAULT_RPD_LIMIT = 20
DEFAULT_RPM_LIMIT = 5
MODEL = "gemini-flash"

# Oracle run cost approximations (per scripts/oracle/config.yaml) :
#   lint : 0 judge calls
#   smoke : 6 scenarios × 1 vote × 3 LLM dims = 18 judge calls
#   full : 26 scenarios × 3 votes × 3 LLM dims = 234 judge calls
MODE_CALL_ESTIMATES = {
    "lint": 0,
    "smoke": 18,
    "full": 234,
}


def _rpd_used_today() -> int:
    try:
        out = subprocess.check_output(
            [
                "docker", "exec", "-i", "postgres-academie",
                "psql", "-U", "sinse", "-d", "academie_db", "-tAc",
                f"SELECT COUNT(*) FROM litellm_cache_stats "
                f"WHERE model = '{MODEL}' AND started_at::date = CURRENT_DATE;",
            ],
            text=True,
        ).strip()
        return int(out or 0)
    except Exception:
        # No litellm_cache_stats → probably no Gemini calls yet today
        return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mode", choices=["lint", "smoke", "full"], help="Oracle mode")
    g.add_argument("--calls", type=int, help="Raw planned calls count")
    ap.add_argument("--n-votes", type=int, default=3,
                    help="Override N-majority votes (default 3, smoke uses 1)")
    ap.add_argument("--rpd-limit", type=int, default=DEFAULT_RPD_LIMIT,
                    help=f"Daily request cap (default {DEFAULT_RPD_LIMIT})")
    args = ap.parse_args()

    if args.calls is not None:
        planned = args.calls
    elif args.mode == "lint":
        planned = 0
    elif args.mode == "smoke":
        # smoke mode in scripts/oracle/config.yaml uses n_votes=1 by design
        planned = 6 * 1 * 3
    else:  # full
        planned = 26 * args.n_votes * 3

    used = _rpd_used_today()
    remaining = max(args.rpd_limit - used, 0)
    headroom = remaining - planned

    print(f"Gemini Flash — today's budget check")
    print(f"  limit  : {args.rpd_limit} RPD (adjust --rpd-limit if Google raised yours)")
    print(f"  used   : {used}")
    print(f"  remain : {remaining}")
    print(f"  planned: {planned} ({args.mode if args.mode else 'custom'})")
    print(f"  headroom after run : {headroom}")
    if headroom < 0:
        print()
        print(f"  ❌ BLOCK : planned run would exceed RPD by {-headroom} calls.")
        print(f"     Options : reduce --n-votes, wait till 00:00 UTC reset,")
        print(f"     or upgrade to Tier 1 (pay-as-you-go, ~$0.15 per full run).")
        return 1
    elif headroom < args.rpd_limit * 0.1:
        print(f"  ⚠️  TIGHT : you'll have <10% of daily RPD left after this run.")
        return 0
    else:
        print(f"  ✓ CLEAR : safe to launch.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
