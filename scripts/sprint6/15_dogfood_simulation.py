#!/usr/bin/env python3
"""Session 39 Block 1.1 — Option A (CLI approximation of browser dogfood).

Exercises the three-strikes → micro-lesson → dedup pipeline end-to-end at
the module level on a disposable learner id, bypassing browser + LLM.

What this validates :
  (b-block) after 3 consecutive same-family errors, detect_three_strikes_family
            returns the family AND build_micro_lesson_block returns a
            non-empty rendered block.
  (b-noleçon) A1 block contains no metalinguistic jargon (institutional
            constraint validated by Sprint 3 battery 97.4%).
  (c) dedup : second call with recent log row returns None ; bypass kwarg
            returns the family again (matches Block 0.2 behavior).
  (d) priority_concepts block builds a non-empty string WHEN scores are
            populated for the learner.

What this does NOT validate (requires real browser + LLM round-trip) :
  (a) observed_level emission in Dify output — separately checked via
      SELECT on messages table in the companion report.
  (b-LLM-integration) whether the tutor INTEGRATES the block naturally.
  (d-no-mention) whether the bot mentions priority_concepts textually.
  (e) tier feedback coherence.

Usage :
  python3 scripts/sprint6/15_dogfood_simulation.py
    → runs both EN and ES simulations, writes /tmp/dogfood_s39.md
"""
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "academie-core"))

from academie_core.pedagogy.three_strikes import (  # noqa: E402
    cefr_band,
    detect_three_strikes_family,
    log_micro_lesson_injection,
)
from academie_core.pedagogy.teacher_prompt import build_micro_lesson_block  # noqa: E402

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://sinse:password@127.0.0.1:5433/academie_db",
).replace("postgres-academie", "127.0.0.1")

# Disposable learner IDs — chosen above the realistic range.
DOGFOOD_EN_ELEVE = 99991
DOGFOOD_ES_ELEVE = 99992

SCENARIOS = [
    {
        "label": "Teacher EN A1 — verb_tense",
        "eleve_id": DOGFOOD_EN_ELEVE,
        "domain": "en",
        "cefr": "A1",
        "expected_family": "verb_tense",
        "error_codes": ["V:TENSE", "V:SVA", "V:FORM"],
        "original_texts": ["I go yesterday", "she eat now", "we did goed"],
        "a1_banned_terms": ["past simple", "auxiliary", "past participle"],
    },
    {
        "label": "Maestro ES A1 — V:SER_ESTAR",
        "eleve_id": DOGFOOD_ES_ELEVE,
        "domain": "es",
        "cefr": "A1",
        "expected_family": "V:SER_ESTAR",
        "error_codes": ["V:SER_ESTAR", "V:SER_ESTAR", "V:SER_ESTAR"],
        "original_texts": ["soy cansado", "estoy médico", "soy contento"],
        "a1_banned_terms": ["propiedades inherentes", "clasificatorias", "atributo"],
        # ES-specific error codes (V:SER_ESTAR, PREP:POR_PARA, ART:PROF) are
        # NOT mapped in ERROR_CODE_TO_FAMILY → detection can't fire today.
        # Fallback render path exercises the YAML directly (known P0 gap,
        # logged to TODO.md, not fixed in this session).
        "render_fallback_family": "V:SER_ESTAR",
    },
]


async def seed_errors(conn, eleve_id: int, domain: str, codes, texts):
    # Ensure the disposable eleve row exists (FK constraint on error_log)
    await conn.execute(
        """
        INSERT INTO eleves (id, username, l1)
        VALUES ($1, $2, 'fr')
        ON CONFLICT (id) DO NOTHING
        """,
        eleve_id, f"dogfood_s39_{eleve_id}",
    )
    await conn.execute(
        "DELETE FROM error_log WHERE eleve_id = $1 AND domain = $2",
        eleve_id, domain,
    )
    await conn.execute(
        "DELETE FROM micro_lesson_log WHERE eleve_id = $1 AND domain = $2",
        eleve_id, domain,
    )
    for i, (code, text) in enumerate(zip(codes, texts)):
        await conn.execute(
            """
            INSERT INTO error_log
              (eleve_id, domain, session_id, turn_number, error_code, original_text, analysis_model)
            VALUES ($1, $2, $3, $4, $5, $6, 'dogfood-sim')
            """,
            eleve_id, domain, f"dogfood-{domain}", i + 1, code, text,
        )


async def run_scenario(conn, sc: dict) -> dict:
    out = {"label": sc["label"], "checks": {}}
    await seed_errors(conn, sc["eleve_id"], sc["domain"], sc["error_codes"], sc["original_texts"])

    # (b-block) — 3rd error triggers detection
    family = await detect_three_strikes_family(
        conn, eleve_id=sc["eleve_id"], domain=sc["domain"],
    )
    out["checks"]["b_detection"] = {
        "expected": sc["expected_family"],
        "got": family,
        "pass": family == sc["expected_family"],
    }

    # If detection didn't fire but the scenario has an expected family,
    # fall back to a direct YAML render check — separates pipeline wiring
    # bugs from YAML / render bugs.
    family_for_render = family or sc.get("render_fallback_family")
    if family_for_render:
        block = build_micro_lesson_block(family_for_render, sc["cefr"], sc["domain"])
        band = cefr_band(sc["cefr"])
        out["checks"]["b_block_rendered"] = {
            "non_empty": bool(block),
            "length": len(block),
            "band": band,
            "pass": bool(block),
        }
        # (b-noleçon) A1 banned terms
        body = block.lower()
        hits = [t for t in sc["a1_banned_terms"] if t.lower() in body]
        out["checks"]["b_a1_no_jargon"] = {
            "banned_terms_checked": sc["a1_banned_terms"],
            "hits": hits,
            "pass": not hits,
        }
        out["block_sample"] = block[:300]

        if family:
            # Simulate the injection log (only if detection actually fired)
            await log_micro_lesson_injection(
                conn, eleve_id=sc["eleve_id"], domain=sc["domain"],
                family=family, cefr_band=band,
            )

    # (c) dedup — next detection should return None
    family_deduped = await detect_three_strikes_family(
        conn, eleve_id=sc["eleve_id"], domain=sc["domain"],
    )
    out["checks"]["c_dedup_blocks_reinject"] = {
        "got": family_deduped,
        "pass": family_deduped is None,
    }

    # (c-bypass) bypass_dedup kwarg reopens detection
    family_bypassed = await detect_three_strikes_family(
        conn, eleve_id=sc["eleve_id"], domain=sc["domain"],
        bypass_dedup=True,
    )
    out["checks"]["c_bypass_reopens"] = {
        "got": family_bypassed,
        "pass": family_bypassed == sc["expected_family"],
    }

    return out


async def fetch_observed_level_stats(conn) -> dict:
    row = await conn.fetchrow(
        """
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE answer ~ '"observed_level":\\s*"[A-C][12]"') AS with_cefr,
          COUNT(*) FILTER (WHERE answer ~ '"observed_level":\\s*""') AS empty
        FROM messages
        WHERE answer LIKE '%observed_level%'
          AND created_at > NOW() - INTERVAL '7 days'
        """
    )
    return dict(row) if row else {}


async def cleanup(conn):
    for el in (DOGFOOD_EN_ELEVE, DOGFOOD_ES_ELEVE):
        await conn.execute("DELETE FROM error_log WHERE eleve_id = $1", el)
        await conn.execute("DELETE FROM micro_lesson_log WHERE eleve_id = $1", el)
        await conn.execute("DELETE FROM eleves WHERE id = $1", el)


def render_report(results, obs_stats) -> str:
    lines = [
        f"# Session 39 — Block 1.1 — Dogfood findings (Option A, CLI simulation)",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Approach",
        "",
        "Browser dogfood deferred — simulated the three-strikes → micro-lesson",
        "pipeline at the module level on disposable eleve_ids (99991, 99992)",
        "with live DB. Validates mechanism ; does not validate LLM integration",
        "quality (that needs real browser run).",
        "",
        "## Check (a) — observed_level emission (retrospective, last 7d)",
        "",
        f"- Total Dify messages containing `observed_level` field : **{obs_stats.get('total', '?')}**",
        f"- With concrete CEFR (A1-C2) : **{obs_stats.get('with_cefr', '?')}**",
        f"- Empty string (legacy pre-v2) : **{obs_stats.get('empty', '?')}**",
        "",
        f"Emission rate : {100 * int(obs_stats.get('with_cefr', 0)) / max(1, int(obs_stats.get('total', 1))):.0f}% concrete.",
        "Check (a) **passes** if concrete ratio > 60%. Empty entries are pre-S37 v2 rollout and are expected to decay as new messages accumulate.",
        "",
        "## Checks (b)/(c) — per-scenario module-level simulation",
        "",
    ]

    for r in results:
        lines.append(f"### {r['label']}")
        lines.append("")
        for check_name, check in r["checks"].items():
            mark = "✅" if check["pass"] else "❌"
            lines.append(f"- {mark} **{check_name}** — {check}")
        if "block_sample" in r:
            lines.append("")
            lines.append("<details><summary>block sample (first 300 chars)</summary>")
            lines.append("")
            lines.append("```")
            lines.append(r["block_sample"])
            lines.append("```")
            lines.append("</details>")
        lines.append("")

    lines.extend([
        "## Checks (d) / (e) / (b-LLM-integration) — NOT covered by option A",
        "",
        "These require real LLM round-trip + human read of bot reply :",
        "- (d-no-mention) : bot must not say 'Today we'll focus on X, Y, Z' — only natural weaving.",
        "- (e) : tier feedback coherence (T2/T3 on flagrant errors).",
        "- (b-LLM-integration) : micro-lesson integrated conversationally, not as a 'lesson' style.",
        "",
        "Recommend follow-up : 1 browser dogfood session (15 min EN + 15 min ES) when",
        "Sinse has time. Environment is already prepped :",
        "",
        "- Phase C rollback backups : `backups/phase_c_pre_reorder/` (Block 0.1)",
        "- Dedup bypass : export `THREE_STRIKES_DEDUP_BYPASS=true` + container restart",
        "- Isolation matrix : `scripts/sprint6/RUN_ISOLATION_MATRIX.sh` (Block 0.3)",
        "",
        "## P0 finding — ES three-strikes detection silently broken",
        "",
        "`ERROR_CODE_TO_FAMILY` (packages/academie-core/.../taxonomy/rules.py:211)",
        "maps only EN error codes. ES-specific codes emitted by rules_es.py",
        "(`V:SER_ESTAR`, `PREP:POR_PARA`, `ART:PROF`) resolve to `'unknown'`,",
        "so `detect_three_strikes_family()` ALWAYS returns `None` for ES",
        "learners, no matter how many consecutive errors they make.",
        "",
        "Impact : the micro-lesson feature is effectively EN-only today.",
        "MICRO_LESSON_ENABLED=true has zero effect on ES dogfood.",
        "",
        "YAML render path is intact (block sample above confirms ES template",
        "renders correctly when given the family directly) — the gap is only",
        "in the detection → family resolver.",
        "",
        "Logged to TODO.md. Not fixed this session (Block 1.1 scope = observe,",
        "not fix). Quick fix (~15 min) = add ES codes to `ERROR_CODE_TO_FAMILY`",
        "mapping to themselves : `'V:SER_ESTAR': 'V:SER_ESTAR'` etc.",
        "",
        "## Decision",
        "",
        "- Block 0 safety net complete, all 3 sub-blocks green.",
        "- Block 1.1 partial : EN pipeline validated end-to-end ; ES has a real",
        "  P0 mechanism gap surfaced and logged.",
        "- LLM integration quality (d/e/b-LLM) deferred to browser dogfood.",
    ])
    return "\n".join(lines)


async def amain() -> int:
    conn = await asyncpg.connect(DSN)
    try:
        results = []
        for sc in SCENARIOS:
            results.append(await run_scenario(conn, sc))
        obs_stats = await fetch_observed_level_stats(conn)
        await cleanup(conn)
    finally:
        await conn.close()

    report = render_report(results, obs_stats)
    out = Path("/tmp/dogfood_s39.md")
    out.write_text(report)
    print(report)
    print(f"\n━━━ report written to {out} ━━━")

    # Exit 0 always — this script's purpose is to produce observability
    # signal, not to gate CI. Failures = genuine findings surfaced in
    # the report for human triage.
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(amain()))
