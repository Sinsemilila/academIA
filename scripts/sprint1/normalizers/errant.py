"""ERRANT (English) normalizer — wraps the existing 02_normalize.py pipeline.

Phase 0.2 — no refactor of the working EN pipeline; this module documents the
contract and provides a thin programmatic entry-point for the framework
dispatcher. The heavy lifting still lives in `02_normalize.py` (executed as
script with hardcoded EN paths).

If a future refactor makes the EN pipeline purely library-callable, move the
logic here.
"""
from __future__ import annotations

from pathlib import Path


def normalize(path: Path, lang: str = "en"):
    """Not directly callable — EN normalization runs via the script entrypoint.

    To produce the EN DataFrame, invoke:
        python3 scripts/sprint1/02_normalize.py

    This reads W&I+LOCNESS from `/mnt/cosmos-data/sprint1/data/raw/` and writes
    the parquet outputs to `/mnt/cosmos-data/sprint1/data/processed/`.
    """
    raise NotImplementedError(
        "EN ERRANT normalization is driven by the existing "
        "scripts/sprint1/02_normalize.py script (hardcoded EN paths). "
        "Run it directly; the library-callable form is a TODO for Wave 2+ "
        "when cross-lang refactor becomes a critical path."
    )
