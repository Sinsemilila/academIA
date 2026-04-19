"""Corpus normalizer framework — cross-lang Phase 0.2.

Each source corpus has its own annotation schema. These modules normalize
raw learner-corpus files into a common DataFrame contract consumed by
`04b_glmm_data_prep.py`:

    columns: [learner_id, text_id, corpus, cefr_level, sentence_idx,
              source_tag, academie_code, academie_family, status,
              n_tokens_sentence]

Supported sources (status as of Phase 0.2) :

| source    | lang  | status        | file        |
|-----------|-------|---------------|-------------|
| errant    | en    | implemented   | errant.py   |
| cows      | es    | stub          | cows.py     |
| merlin    | it,de | stub          | merlin.py   |
| falko     | de    | stub          | falko.py    |
| rlc       | ru    | stub          | rlc.py      |

Stubs raise NotImplementedError; they become real in the Wave that uses
the corresponding corpus (Wave 1 for COWS-L2H, Wave 2 for MERLIN/Falko,
Wave 4 for RLC).

Usage :
    from scripts.sprint1.normalizers import normalize
    df = normalize(source="cows", path="/path/to/cows-l2h.tsv", lang="es")
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


_REGISTRY = {
    "errant": "errant",
    "cows": "cows",
    "merlin": "merlin",
    "falko": "falko",
    "rlc": "rlc",
}


def normalize(source: str, path: str | Path, lang: str) -> "pd.DataFrame":
    """Dispatch to the right per-source normalizer module.

    Raises ValueError for unknown sources. Each backend may raise
    NotImplementedError if the source is not yet wired.
    """
    if source not in _REGISTRY:
        raise ValueError(
            f"unknown corpus source {source!r}; "
            f"expected one of {sorted(_REGISTRY)}"
        )
    module_name = _REGISTRY[source]
    import importlib
    mod = importlib.import_module(f"{__name__}.{module_name}")
    return mod.normalize(path=Path(path), lang=lang)
