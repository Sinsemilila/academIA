#!/usr/bin/env python3
"""YAML-driven curriculum injection (Session 37).

Reads /packages/academie-core/academie_core/data/curriculum_{domain}.yaml
and upserts the 4 normalized columns into the `curriculums` table:
  - description
  - concept_keys        (jsonb array — consumed by profile/stats/error_analysis)
  - concept_weights     (jsonb object — ready for future weighting systems)
  - concept_groups      (jsonb object — ready for future functional grouping)

The legacy `points_cles` nested jsonb is LEFT UNTOUCHED on UPDATE so historical
EN data (loaded via inject_curriculum_anglais.py Sprint 2-3) is preserved. New
rows get `points_cles = '{}'::jsonb` default.

Usage:
    python3 inject_curriculum.py --domain es                  # inject ES
    python3 inject_curriculum.py --domain es --dry-run        # preview only
    python3 inject_curriculum.py --domain en --force          # override drift guard

EN injection is guarded: `curriculum_en.yaml` (Session 37) has 10 A1 concepts
while the DB has 18 (post-Sprint 2-3 augmentation via inject_concept_keys.py).
Running without --force would silently shrink the EN data. Use --force only
after manually reconciling the YAML with DB content.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg required (run inside academie-api container)", file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
CURRICULUM_DIR = REPO_ROOT / "packages" / "academie-core" / "academie_core" / "data"
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]


# ── YAML parsing + validation ─────────────────────────────────────────

def load_curriculum(domain: str) -> dict:
    path = CURRICULUM_DIR / f"curriculum_{domain}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"No curriculum YAML for domain {domain!r}: {path}\n"
            f"Hint: create the YAML in {CURRICULUM_DIR} following "
            f"curriculum_es.yaml schema.",
        )
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a YAML mapping")
    return data


def validate_schema(data: dict, expected_domain: str) -> None:
    """Raise ValueError on any schema violation."""
    if data.get("domain") != expected_domain:
        raise ValueError(
            f"YAML domain={data.get('domain')!r} does not match --domain {expected_domain!r}",
        )
    for level in CEFR_LEVELS:
        if level not in data:
            raise ValueError(f"Missing CEFR level {level} in YAML")
        block = data[level]
        if not isinstance(block, dict):
            raise ValueError(f"Level {level} must be a mapping, got {type(block).__name__}")
        # Required sub-keys
        for required in ("concept_keys", "concept_weights", "concept_groups"):
            if required not in block:
                raise ValueError(f"Level {level} missing required key {required!r}")
        if not isinstance(block["concept_keys"], list) or not block["concept_keys"]:
            raise ValueError(f"Level {level}: concept_keys must be non-empty list")
        if not isinstance(block["concept_weights"], dict):
            raise ValueError(f"Level {level}: concept_weights must be a mapping")
        if not isinstance(block["concept_groups"], dict):
            raise ValueError(f"Level {level}: concept_groups must be a mapping")
        # concept_weights keys ⊆ concept_keys (tolerate _note annotations)
        keys = set(block["concept_keys"])
        for wk in block["concept_weights"]:
            if wk.endswith("_note"):
                continue
            if wk not in keys:
                raise ValueError(
                    f"Level {level}: concept_weights key {wk!r} not in concept_keys",
                )


def build_rows(data: dict) -> list[dict]:
    """Return 6 row dicts ready for UPSERT."""
    rows = []
    for level in CEFR_LEVELS:
        block = data[level]
        rows.append({
            "domain": data["domain"],
            "niveau": level,
            "description": (block.get("description") or "").strip(),
            "concept_keys": block["concept_keys"],
            # Filter _note annotations out of concept_weights (internal docs)
            "concept_weights": {k: v for k, v in block["concept_weights"].items()
                                if not k.endswith("_note")},
            "concept_groups": block["concept_groups"],
        })
    return rows


# ── DB upsert ─────────────────────────────────────────────────────────

_UPSERT_SQL = """
INSERT INTO curriculums
    (domain, niveau, description, concept_keys, concept_weights, concept_groups, points_cles)
VALUES
    ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, '{}'::jsonb)
ON CONFLICT (domain, niveau) DO UPDATE
  SET description = EXCLUDED.description,
      concept_keys = EXCLUDED.concept_keys,
      concept_weights = EXCLUDED.concept_weights,
      concept_groups = EXCLUDED.concept_groups
      -- points_cles intentionally preserved (legacy nested data for EN)
RETURNING (xmax = 0) AS inserted
"""


async def upsert_rows(rows: list[dict]) -> tuple[int, int]:
    """Execute 6 UPSERTs in a single transaction. Returns (inserted, updated)."""
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL not set in env")
    pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
    inserted = updated = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for r in rows:
                row = await conn.fetchrow(
                    _UPSERT_SQL,
                    r["domain"], r["niveau"], r["description"],
                    json.dumps(r["concept_keys"], ensure_ascii=False),
                    json.dumps(r["concept_weights"], ensure_ascii=False),
                    json.dumps(r["concept_groups"], ensure_ascii=False),
                )
                if row and row["inserted"]:
                    inserted += 1
                else:
                    updated += 1
    await pool.close()
    return inserted, updated


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, help="ISO code of target language (en/es/it/de/ja/ru/...)")
    ap.add_argument("--dry-run", action="store_true", help="Preview rows without writing to DB")
    ap.add_argument("--force", action="store_true", help="Override the EN drift safety guard")
    args = ap.parse_args()

    domain = args.domain.lower().strip()
    if not domain.isalpha() or len(domain) > 16:
        print(f"ERROR: invalid domain code {args.domain!r}", file=sys.stderr)
        return 2

    # Load + validate
    try:
        data = load_curriculum(domain)
        validate_schema(data, domain)
    except Exception as e:
        print(f"SCHEMA ERROR: {e}", file=sys.stderr)
        return 2

    rows = build_rows(data)
    total_concepts = sum(len(r["concept_keys"]) for r in rows)

    # EN drift guard
    if domain == "en" and not args.force:
        print(
            f"⚠️  Aborted: EN injection disabled by default.\n"
            f"    Reason: curriculum_en.yaml ({total_concepts} concepts) may drift from "
            f"the current DB state (18+ concept_keys per level from Sprint 2-3 + "
            f"inject_concept_keys.py augmentation).\n"
            f"    Re-injecting would shrink the EN data silently.\n"
            f"    To proceed anyway: re-run with --force after manually reconciling.",
            file=sys.stderr,
        )
        return 3

    # Dry-run preview
    print(f"📚 Curriculum injection preview — domain={domain!r}")
    print(f"   Source: {CURRICULUM_DIR / f'curriculum_{domain}.yaml'}")
    print(f"   Total concepts across A1-C2: {total_concepts}")
    for r in rows:
        desc_preview = (r["description"] or "")[:60]
        print(
            f"   · {r['niveau']} — {len(r['concept_keys'])} keys, "
            f"{len(r['concept_weights'])} weights, {len(r['concept_groups'])} groups "
            f"— {desc_preview!r}",
        )

    if args.dry_run:
        print("\n[DRY-RUN] No DB write. Re-run without --dry-run to apply.")
        return 0

    # Real upsert
    print()
    inserted, updated = asyncio.run(upsert_rows(rows))
    print(f"✅ Done — inserted={inserted}, updated={updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
