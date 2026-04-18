"""Retrospective scoring: replay existing error_log rows with v1 vs v2 weights.

Reads the 9 current rows from academie_db.error_log, joined with the essay's
learner level from profils_eleves. Scores each row with v1 and v2 matrices,
compares totals and family breakdown.

Output: /mnt/cosmos-data/sprint1/results/v1_vs_v2_retrospective.json
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

RESULTS = Path("/mnt/cosmos-data/sprint1/results/v1_vs_v2_retrospective.json")
_TM_DIR = Path("/opt/academie/packages/academie-core/academie_core/data/tolerance_matrix")
V2_YAML = _TM_DIR / "tolerance_matrix_v2.yaml"
V1_YAML = _TM_DIR / "tolerance_matrix.yaml"


def _psql(sql: str) -> str:
    return subprocess.run(
        ["docker", "exec", "postgres-academie",
         "psql", "-U", "sinse", "-d", "academie_db", "-tAF,", "-c", sql],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _load(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _code_to_family(code: str, matrix: dict) -> str | None:
    for fam, defn in matrix["families"].items():
        if code in defn.get("codes", []):
            return fam
    return None


def _level_to_band(level: str, matrix: dict) -> str:
    return matrix["cefr_bands"].get(level.strip().upper(), "intermediate")


def _score(rows: list[dict], matrix: dict) -> dict:
    weights = matrix["weights"]
    total = 0.0
    by_family: dict[str, float] = {}
    unscored = 0
    for row in rows:
        fam = _code_to_family(row["error_code"], matrix)
        if not fam or fam not in matrix["matrix"]:
            unscored += 1
            continue
        band = _level_to_band(row.get("niveau_global", "B1"), matrix)
        tier = matrix["matrix"][fam].get(band, "ignored")
        w = weights.get(tier, 0.0)
        total += w
        by_family[fam] = by_family.get(fam, 0.0) + w
    return {"total": total, "by_family": by_family, "unscored": unscored}


@pytest.fixture(scope="module")
def error_log_rows():
    """Fetch 9 rows joined with learner's modal CEFR level."""
    out = _psql(
        "SELECT el.error_code, COALESCE(pe.niveau_global, 'B1') "
        "FROM error_log el "
        "LEFT JOIN profils_eleves pe ON pe.eleve_id = el.eleve_id "
        "  AND pe.domain='en';"
    )
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split(",", 1)
        rows.append({"error_code": parts[0].strip(),
                     "niveau_global": parts[1].strip() if len(parts) > 1 else "B1"})
    return rows


def test_retrospective_v1_vs_v2(error_log_rows):
    assert len(error_log_rows) >= 1, "Need at least 1 error_log row"

    v1 = _load(V1_YAML)
    v2 = _load(V2_YAML)

    s1 = _score(error_log_rows, v1)
    s2 = _score(error_log_rows, v2)

    delta = s2["total"] - s1["total"]
    per_row = s1["total"] / max(len(error_log_rows), 1)

    report = {
        "n_rows": len(error_log_rows),
        "v1": s1,
        "v2": s2,
        "delta_total": delta,
        "delta_relative": delta / s1["total"] if s1["total"] else 0.0,
        "per_row_v1": per_row,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(report, indent=2))

    print("\nRetrospective scoring report:")
    print(f"  Rows scored     : {len(error_log_rows)}")
    print(f"  v1 total        : {s1['total']:.3f}")
    print(f"  v2 total        : {s2['total']:.3f}")
    print(f"  delta           : {delta:+.3f} ({report['delta_relative']:+.1%})")
    print(f"  unscored v1/v2  : {s1['unscored']}/{s2['unscored']}")

    # Assertions:
    # 1. No row becomes completely unscored
    assert s2["unscored"] <= s1["unscored"], \
        f"v2 unscored {s2['unscored']} > v1 {s1['unscored']} (taxonomy regression)"
    # 2. Delta not absurdly large (< 80% drop expected on small sample)
    if s1["total"] > 0:
        assert abs(delta) < s1["total"] * 0.9, \
            f"Delta too extreme: {delta} vs v1={s1['total']}"
