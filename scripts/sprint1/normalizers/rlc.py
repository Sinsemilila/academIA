"""RLC (Russian Learner Corpus) normalizer — stub for Wave 4.

Source : Russian Learner Corpus, Higher School of Economics Moscow.
URL    : http://web-corpora.net/RLC
Size   : ~7000 textes multi-L1 (FR included but not isolated ; Russian Wheel
         sub-corpus at UCA Nice contains the FR-isolated extract — non-bloquant
         discovery email in Phase 0.9).
License: Open (research, confirm at Wave kickoff)

Expected input : XML or TSV export with RLC error-tag schema.
Expected output : same DataFrame contract as ERRANT normalizer.

Mapping file : scripts/sprint1/mappings/rlc_to_academie_ru.yaml
"""
from __future__ import annotations

from pathlib import Path


def normalize(path: Path, lang: str = "ru"):
    if lang != "ru":
        raise ValueError(f"RLC is RU-only; got {lang!r}")
    raise NotImplementedError(
        "RLC normalizer is a Wave 4 RU deliverable. "
        "See docstring for the expected input/output contract."
    )
