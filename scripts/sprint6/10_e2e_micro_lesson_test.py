#!/usr/bin/env python3
"""E2E test — Session 38 micro-lesson feature against live Postgres.

Exercises :
  1. Detection on 3 consecutive same-family errors in error_log
  2. Empty result when <3 errors
  3. Empty result when families mixed
  4. YAML template rendering for A1 / A2 / B1 CEFR bands (EN + ES)
  5. Dedup : after log_micro_lesson_injection, same family re-detection returns None
  6. Dedup expires for different family immediately
  7. Full scaffolding_block append pattern (simulates chat_router logic)

Uses a disposable test learner (username='__e2e_micro_lesson__'). Cleans up
on success AND failure.

Run :
    python3 scripts/sprint6/10_e2e_micro_lesson_test.py
Exit 0 on success, 1 on first failure.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import traceback

import asyncpg

from academie_core.pedagogy.three_strikes import (
    detect_three_strikes_family,
    log_micro_lesson_injection,
)
from academie_core.pedagogy.teacher_prompt import build_micro_lesson_block


DB_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://sinse@127.0.0.1:5432/academie_db",
)
TEST_USERNAME = "__e2e_micro_lesson__"


class E2EFailure(RuntimeError):
    pass


def check(cond: bool, label: str) -> None:
    if cond:
        print(f"  ✅ {label}")
    else:
        raise E2EFailure(f"FAIL: {label}")


async def _ensure_learner(conn) -> int:
    """Create (or reuse) the e2e test learner and return its eleve_id."""
    eleve_id = await conn.fetchval(
        "SELECT id FROM eleves WHERE username = $1", TEST_USERNAME,
    )
    if eleve_id:
        return int(eleve_id)
    eleve_id = await conn.fetchval(
        "INSERT INTO eleves (username) VALUES ($1) RETURNING id",
        TEST_USERNAME,
    )
    return int(eleve_id)


async def _wipe(conn, eleve_id: int) -> None:
    await conn.execute("DELETE FROM error_log WHERE eleve_id=$1", eleve_id)
    await conn.execute("DELETE FROM micro_lesson_log WHERE eleve_id=$1", eleve_id)


async def _seed_errors(conn, eleve_id: int, domain: str, codes: list[str]) -> None:
    """Insert one error row per code, most recent last. created_at is auto-set;
    we stagger manually to guarantee ORDER BY created_at DESC."""
    # Reverse so first arg appears oldest, last appears newest — we insert in
    # order with NOW() - offsets to control ordering.
    for i, code in enumerate(codes):
        offset = len(codes) - i
        await conn.execute(
            """
            INSERT INTO error_log
              (eleve_id, session_id, error_code, original_text, domain, created_at)
            VALUES ($1, $2, $3, $4, $5, NOW() - ($6 || ' seconds')::interval)
            """,
            eleve_id, "e2e-session", code, "test", domain, str(offset),
        )


async def run() -> int:
    conn = await asyncpg.connect(DB_DSN)
    eleve_id = None
    try:
        eleve_id = await _ensure_learner(conn)
        print(f"Test learner eleve_id={eleve_id}")

        # ── Scenario 1 : clean slate, no errors → None ─────────────────
        await _wipe(conn, eleve_id)
        fam = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam is None, "empty error_log → detection None")

        # ── Scenario 2 : 2 errors same family → None ───────────────────
        await _seed_errors(conn, eleve_id, "en", ["V:TENSE", "V:SVA"])
        fam = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam is None, "2 same-family errors → below threshold")

        # ── Scenario 3 : 3 errors same family → verb_tense ─────────────
        await _wipe(conn, eleve_id)
        await _seed_errors(conn, eleve_id, "en", ["V:TENSE", "V:SVA", "V:FORM"])
        fam = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam == "verb_tense", f"3 consecutive verb errors → verb_tense (got {fam})")

        # ── Scenario 4 : mixed recent 3 → None ─────────────────────────
        await _wipe(conn, eleve_id)
        await _seed_errors(conn, eleve_id, "en", ["V:TENSE", "N:COUNT", "V:FORM"])
        fam = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam is None, "mixed recent 3 families → None")

        # ── Scenario 5 : dedup — same family re-injected within 3d blocked ─
        await _wipe(conn, eleve_id)
        await _seed_errors(conn, eleve_id, "en", ["V:TENSE", "V:SVA", "V:FORM"])
        fam = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam == "verb_tense", "pre-log detection OK")
        await log_micro_lesson_injection(conn, eleve_id, "en", "verb_tense", "A1")
        fam2 = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam2 is None, "post-log same-family dedup → None")

        # ── Scenario 6 : different family not blocked by prior dedup ───
        await _wipe(conn, eleve_id)
        # Prior verb_tense log still present (we don't wipe micro_lesson_log here)
        await log_micro_lesson_injection(conn, eleve_id, "en", "verb_tense", "A1")
        await _seed_errors(conn, eleve_id, "en", ["N:COUNT", "ART", "DET"])
        fam3 = await detect_three_strikes_family(conn, eleve_id, "en")
        check(fam3 == "noun_det", f"different family unaffected by prior dedup (got {fam3})")

        # ── Scenario 7 : YAML template rendering, A1 EN (no metalanguage) ──
        block_a1 = build_micro_lesson_block("verb_tense", "A1", "en")
        check("went" in block_a1.lower(), "A1 EN block contains concrete example")
        check("past simple marks" not in block_a1.lower(),
              "A1 EN block avoids technical term 'past simple marks'")

        # ── Scenario 8 : YAML rendering B1 EN (full metalinguistic) ────
        block_b1 = build_micro_lesson_block("verb_tense", "B1", "en")
        check("past simple" in block_b1.lower(),
              "B1 EN block includes metalinguistic term 'past simple'")

        # ── Scenario 9 : YAML rendering ES A1 ser/estar ────────────────
        block_es_a1 = build_micro_lesson_block("V:SER_ESTAR", "A1", "es")
        check("ser" in block_es_a1.lower() and "estar" in block_es_a1.lower(),
              "ES A1 ser_estar block contains both verbs")

        # ── Scenario 10 : YAML rendering ES B1 por/para ────────────────
        block_es_b1 = build_micro_lesson_block("PREP:POR_PARA", "B1", "es")
        check("por" in block_es_b1.lower() and "para" in block_es_b1.lower(),
              "ES B1 por_para block contains both prepositions")

        # ── Scenario 11 : marker fences present ────────────────────────
        check("=== MICRO-LEÇON CIBLÉE" in block_a1, "opening marker fence")
        check("=== END MICRO-LEÇON ===" in block_a1, "closing marker fence")

        # ── Scenario 12 : scaffolding_block append pattern (simulated) ─
        scaffolding = "=== EXISTING SCAFFOLDING ===\nContent.\n=== END ==="
        combined = f"{scaffolding}\n\n{block_b1}" if scaffolding else block_b1
        check("=== EXISTING SCAFFOLDING ===" in combined
              and "=== MICRO-LEÇON CIBLÉE" in combined,
              "scaffolding_block + micro_lesson_block compose correctly")

        # ── Scenario 13 : unknown family returns "" ────────────────────
        block_unk = build_micro_lesson_block("totally_made_up_family", "A1", "en")
        check(block_unk == "", "unknown family → empty block")

        # ── Scenario 14 : None family returns "" ───────────────────────
        check(build_micro_lesson_block(None, "A1", "en") == "",
              "None family → empty block")

        print("\n✅ ALL 14 E2E SCENARIOS PASSED")
        return 0

    except E2EFailure as e:
        print(f"\n❌ {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        return 1
    finally:
        # Cleanup : wipe error_log + micro_lesson_log + the test learner
        if eleve_id is not None:
            try:
                await _wipe(conn, eleve_id)
                await conn.execute("DELETE FROM eleves WHERE id = $1", eleve_id)
                print(f"  (cleaned up test learner {eleve_id})")
            except Exception as _e:
                print(f"  cleanup warning: {_e}")
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
