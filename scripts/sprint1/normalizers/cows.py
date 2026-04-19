"""COWS-L2H (Spanish) normalizer — stub for Wave 1.

Source : Corpus Of Written Spanish by L2 and Heritage speakers, UC Davis.
URL    : https://github.com/ucdaviscl/cowsl2h (or the canonical mirror)
Size   : ~500 essays, 6 error-type annotations by native speakers
License: CC BY-SA (check actual release at wave kickoff)

Expected input : TSV or JSONL export with columns
    [essay_id, learner_id, cefr_level, sentence_idx, original, correction,
     cows_error_type, offset_start, offset_end]

Expected output (DataFrame contract) :
    [learner_id, text_id, corpus, cefr_level, sentence_idx, source_tag,
     academie_code, academie_family, status, n_tokens_sentence]

Mapping file : scripts/sprint1/mappings/cows_to_academie_es.yaml
"""
from __future__ import annotations

from pathlib import Path


def normalize(path: Path, lang: str = "es"):
    raise NotImplementedError(
        "COWS-L2H normalizer is a Wave 1 ES deliverable. "
        "Implement when the corpus is downloaded and inspected. "
        "See docstring for the expected input/output contract."
    )
