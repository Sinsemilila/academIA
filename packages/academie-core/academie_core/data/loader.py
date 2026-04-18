"""Language data loader — loads rubrics, fewshots, l1_transfer per lang_target.

Caches at module level via @lru_cache (loaded once per process).
Same pattern as scoring.py tolerance matrix loading.
"""
from __future__ import annotations

import yaml
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).parent


@lru_cache(maxsize=16)
def load_rubrics(lang: str) -> dict[str, str] | None:
    """Load rubrics for a target language. Returns None if no YAML found."""
    path = _DATA_DIR / "rubrics" / f"{lang}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("rubrics") if data else None


@lru_cache(maxsize=16)
def load_fewshots(lang: str) -> list[dict] | None:
    """Load fewshot bank for a target language. Returns None if no YAML found."""
    path = _DATA_DIR / "fewshots" / f"{lang}.yaml"
    if not path.exists():
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("fewshots") if data else None


@lru_cache(maxsize=1)
def load_l1_names() -> dict[str, str]:
    """Load ISO-639-1 → English language name mapping."""
    path = _DATA_DIR / "l1_transfer" / "l1_names.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data.get("names", {}) if data else {}


def load_l1_transfers(l1: str, target: str) -> list[tuple[str, float, str]]:
    """Load transfer patterns for a specific L1→target pair.

    Returns a list of (family, multiplier, description) tuples.
    """
    path = _DATA_DIR / "l1_transfer" / f"{l1}_to_{target}.yaml"
    if not path.exists():
        return []
    with open(path) as f:
        data = yaml.safe_load(f)
    if not data or "transfers" not in data:
        return []
    return [
        (t["family"], t["multiplier"], t["description"])
        for t in data["transfers"]
    ]
