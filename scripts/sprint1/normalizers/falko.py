"""Falko (German, advanced learner) normalizer — stub for Wave 2.

Source : Falko — Fehlerannotiertes Lernerkorpus, HU Berlin.
URL    : https://www.linguistik.hu-berlin.de/de/institut/professuren/korpuslinguistik/forschung/falko
Size   : ~1500 textes apprenants advanced (C1-C2 dominant)
License: Research use, requires registration via ANNIS

Multi-layer annotation : ZH1 (target hypothesis), ZH2 (deeper), error-tags on both.
Expected output : same DataFrame contract as ERRANT normalizer.

Mapping file : scripts/sprint1/mappings/falko_to_academie_de.yaml
"""
from __future__ import annotations

from pathlib import Path


def normalize(path: Path, lang: str = "de"):
    if lang != "de":
        raise ValueError(f"Falko is DE-only; got {lang!r}")
    raise NotImplementedError(
        "Falko normalizer is a Wave 2 DE deliverable. "
        "Requires ANNIS registration + tig or relANNIS export. "
        "See docstring for the expected input/output contract."
    )
