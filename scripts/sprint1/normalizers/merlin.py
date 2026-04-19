"""MERLIN (Italian + German) normalizer — stub for Wave 2.

Source : Multilingual Platform for European Reference Levels.
URL    : https://www.merlin-platform.eu
Size   : ~813 IT textes, ~1000 DE textes, CEFR-annotated with 70 error features
License: CC BY-SA 4.0

Expected input : XML or TSV export from CLARIN release.
Expected output (DataFrame contract) :
    [learner_id, text_id, corpus, cefr_level, sentence_idx, source_tag,
     academie_code, academie_family, status, n_tokens_sentence]

Mapping files :
- scripts/sprint1/mappings/merlin_to_academie_it.yaml
- scripts/sprint1/mappings/merlin_to_academie_de.yaml
"""
from __future__ import annotations

from pathlib import Path


def normalize(path: Path, lang: str):
    if lang not in {"it", "de"}:
        raise ValueError(f"MERLIN has no {lang!r} subcorpus; expected 'it' or 'de'")
    raise NotImplementedError(
        f"MERLIN {lang.upper()} normalizer is a Wave 2 deliverable. "
        "See docstring for the expected input/output contract."
    )
