"""Normalize W&I M2 + JSON into Parquet long-form tables.

Output:
  /mnt/cosmos-data/sprint1/data/processed/errors_long.parquet
    columns: [learner_id, text_id, corpus, cefr_level, cefr_sublevel,
              sentence_idx, errant_tag, academie_code, academie_family,
              status, n_tokens_sentence]
  /mnt/cosmos-data/sprint1/data/processed/learners.parquet
    columns: [learner_id, cefr_level_modal, n_texts, n_sentences,
              n_tokens, n_errors, err_per_1k_tokens]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import spacy

sys.path.insert(0, str(Path(__file__).parent))
from errant_mapper import ErrantMapper  # noqa: E402

_nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "tagger", "parser"])
_nlp.add_pipe("sentencizer")

RAW = Path("/mnt/cosmos-data/sprint1/data/raw/wi+locness")
OUT = Path("/mnt/cosmos-data/sprint1/data/processed")
OUT.mkdir(parents=True, exist_ok=True)


def _coarse_cefr(sub: str) -> str:
    """A1.i → A1, B2.ii → B2, C2+ → C2, N → N."""
    if sub == "N":
        return "N"
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        if sub.startswith(level):
            return level
    return sub


def _load_json_essays(split_tag: str, json_path: Path) -> list[dict]:
    """Load JSON file; yield essays with split tag for provenance."""
    with open(json_path) as f:
        essays = [json.loads(line) for line in f]
    for e in essays:
        e["_split"] = split_tag
        e["_corpus"] = "wi" if "N" not in json_path.stem[:1] else "locness"
    return essays


def _parse_m2(m2_path: Path):
    """Yield (text_id, sentence_idx, tokens, tag_list) from M2 file.

    M2 format:
      S source sentence
      A start end|||TAG|||correction|||REQUIRED|||-NONE-|||annotator
      (blank line between sentences)
    Text boundary heuristic: sentences are grouped by (file order).
    Since W&I M2 files don't carry text_id, we match by split order against JSON.
    """
    with open(m2_path) as f:
        lines = f.read().split("\n")
    sentence_idx = 0
    current_sent: str | None = None
    current_tags: list[str] = []
    for line in lines:
        if line.startswith("S "):
            if current_sent is not None:
                yield sentence_idx, current_sent, current_tags
                sentence_idx += 1
            current_sent = line[2:]
            current_tags = []
        elif line.startswith("A "):
            # A start end|||TAG|||...
            parts = line[2:].split("|||")
            if len(parts) >= 2:
                current_tags.append(parts[1])
        elif line.strip() == "":
            # Sentence boundary: flush if we have content
            if current_sent is not None:
                yield sentence_idx, current_sent, current_tags
                sentence_idx += 1
                current_sent = None
                current_tags = []
    if current_sent is not None:
        yield sentence_idx, current_sent, current_tags


# Canonical file pairs — JSON provides userid+CEFR, M2 provides sentence-level tags.
# Mapping follows BEA 2019 README layout.
FILE_PAIRS = [
    ("wi", "A", "train", "json/A.train.json", "m2/A.train.gold.bea19.m2"),
    ("wi", "B", "train", "json/B.train.json", "m2/B.train.gold.bea19.m2"),
    ("wi", "C", "train", "json/C.train.json", "m2/C.train.gold.bea19.m2"),
    ("wi", "A", "dev", "json/A.dev.json", "m2/A.dev.gold.bea19.m2"),
    ("wi", "B", "dev", "json/B.dev.json", "m2/B.dev.gold.bea19.m2"),
    ("wi", "C", "dev", "json/C.dev.json", "m2/C.dev.gold.bea19.m2"),
    ("locness", "N", "dev", "json/N.dev.json", "m2/N.dev.gold.bea19.m2"),
]


def main() -> int:
    mapper = ErrantMapper()
    rows = []
    learner_stats: dict[str, dict] = defaultdict(lambda: {
        "cefr_levels": Counter(),
        "n_texts": 0,
        "n_sentences": 0,
        "n_tokens": 0,
        "n_errors": 0,
    })

    for corpus, level_group, split, json_rel, m2_rel in FILE_PAIRS:
        json_path = RAW / json_rel
        m2_path = RAW / m2_rel
        if not json_path.exists() or not m2_path.exists():
            print(f"Skipping {level_group}.{split} (files missing)")
            continue

        # Load essays and M2 in parallel — same order per BEA split.
        with open(json_path) as f:
            essays = [json.loads(line) for line in f]

        # Parse M2 all at once, group by text via sentence count per essay.
        all_sentences = list(_parse_m2(m2_path))

        essay_lengths = [
            len(list(_nlp(e["text"]).sents))
            for e in essays
        ]

        # Sanity check: total sentences from M2 ~= sum(essay_lengths)
        total_m2 = len(all_sentences)
        total_essays = sum(essay_lengths)
        ratio = total_m2 / max(total_essays, 1)
        if abs(ratio - 1.0) > 0.05:
            # Distribute overshoot proportionally so every learner still gets attribution
            scale = total_m2 / total_essays
            essay_lengths = [max(1, round(n * scale)) for n in essay_lengths]
            # Trim overshoot to exact total
            diff = total_m2 - sum(essay_lengths)
            if diff != 0:
                essay_lengths[-1] += diff
            print(f"  {level_group}.{split}: m2={total_m2} essays_est={total_essays} rescaled (ratio {ratio:.2f})")

        # Consume M2 sentences in essay order
        m2_iter = iter(all_sentences)
        for e, n_sents in zip(essays, essay_lengths):
            learner_id = str(e.get("userid", f"anon_{e.get('id')}"))
            cefr_sub = e.get("cefr", "unknown")
            cefr_lvl = _coarse_cefr(cefr_sub)
            text_id = str(e.get("id"))

            learner_stats[learner_id]["cefr_levels"][cefr_lvl] += 1
            learner_stats[learner_id]["n_texts"] += 1
            learner_stats[learner_id]["n_sentences"] += n_sents

            for _ in range(n_sents):
                try:
                    sent_idx, sentence, tags = next(m2_iter)
                except StopIteration:
                    break
                n_tokens = len(sentence.split())
                learner_stats[learner_id]["n_tokens"] += n_tokens
                real_errors = [t for t in tags if t != "noop"]
                learner_stats[learner_id]["n_errors"] += len(real_errors)
                for tag in real_errors:
                    mapped = mapper.map(tag)
                    rows.append({
                        "learner_id": learner_id,
                        "text_id": text_id,
                        "corpus": corpus,
                        "split": split,
                        "cefr_level": cefr_lvl,
                        "cefr_sublevel": cefr_sub,
                        "sentence_idx": sent_idx,
                        "n_tokens_sentence": n_tokens,
                        "errant_tag": tag,
                        "academie_code": mapped.academie_code,
                        "academie_family": mapped.family,
                        "status": mapped.status,
                    })

    # Errors long
    df_err = pd.DataFrame(rows)
    df_err.to_parquet(OUT / "errors_long.parquet", index=False, compression="zstd")
    print(f"\nerrors_long.parquet : {len(df_err):,} rows, {df_err['learner_id'].nunique():,} learners")
    print("  mapped/unmappable/unknown:", df_err["status"].value_counts().to_dict())
    print("  by cefr_level:", df_err["cefr_level"].value_counts().sort_index().to_dict())

    # Learners wide
    learner_rows = []
    for lid, stats in learner_stats.items():
        modal = stats["cefr_levels"].most_common(1)[0][0] if stats["cefr_levels"] else "unknown"
        n_tokens = stats["n_tokens"]
        n_errors = stats["n_errors"]
        learner_rows.append({
            "learner_id": lid,
            "cefr_level_modal": modal,
            "n_texts": stats["n_texts"],
            "n_sentences": stats["n_sentences"],
            "n_tokens": n_tokens,
            "n_errors": n_errors,
            "err_per_1k_tokens": 1000.0 * n_errors / n_tokens if n_tokens else 0.0,
        })
    df_learner = pd.DataFrame(learner_rows)
    df_learner.to_parquet(OUT / "learners.parquet", index=False, compression="zstd")
    print(f"\nlearners.parquet : {len(df_learner):,} learners")
    print("  by cefr_level_modal:", df_learner["cefr_level_modal"].value_counts().sort_index().to_dict())
    print(f"  median err/1k tokens: {df_learner['err_per_1k_tokens'].median():.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
