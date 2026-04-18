"""Normalize NUCLE BEA-2019 M2 into Parquet long-form tables.

The nucle.train.gold.bea19.m2 file contains:
  1. Full NUCLE SGML corpus (ignored here — no CEFR labels per sentence)
  2. M2-formatted section with both ERRANT-style and NUCLE-legacy tags

CEFR assignment: NUS university students → proxy B2 (conservative).
All learners assigned cefr_level=B2, cefr_sublevel=B2.i
(per Dahlmeier et al. 2013: NUS students sat English placement; corpus
represents upper-intermediate to advanced L2 writers)

Output appended to:
  /mnt/cosmos-data/sprint1/data/processed/errors_long.parquet  (merged)
  /mnt/cosmos-data/sprint1/data/processed/learners.parquet     (merged)
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import spacy
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from errant_mapper import ErrantMapper  # noqa: E402

_nlp = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer", "tagger", "parser"])
_nlp.add_pipe("sentencizer")

M2_FILE  = Path("/opt/academie-shared/corpora/nucle/nucle.train.gold.bea19.m2")
OUT      = Path("/mnt/cosmos-data/sprint1/data/processed")
NUCLE_MAP_FILE = Path(__file__).parent / "nucle_to_academie.yaml"

CEFR_PROXY   = "B2"
CEFR_SUB     = "B2.i"
CORPUS_NAME  = "nucle"

# ── Loaders ──────────────────────────────────────────────────────────────────

def _load_nucle_map() -> dict:
    with open(NUCLE_MAP_FILE) as f:
        raw = yaml.safe_load(f)
    return raw["mappings"]

def _is_errant(tag: str) -> bool:
    return tag.startswith(("R:", "M:", "U:", "UNK"))

def _parse_m2_section(path: Path):
    """Yield (sentence_str, tags_list) for each sentence in the M2 section.

    The file starts with SGML content; the M2 section begins at the first
    line starting with 'S ' (after the SGML DOC blocks end).
    We skip the SGML section by scanning for the transition.
    """
    in_m2 = False
    current_sent = None
    current_tags = []

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            if not in_m2:
                # Transition: first "S " line after SGML
                if line.startswith("S "):
                    in_m2 = True
                else:
                    continue
            if line.startswith("S "):
                if current_sent is not None:
                    yield current_sent, current_tags
                current_sent = line[2:]
                current_tags = []
            elif line.startswith("A "):
                parts = line[2:].split("|||")
                if len(parts) >= 2 and parts[1] not in ("noop", "-NONE-"):
                    current_tags.append(parts[1])
            elif line.strip() == "":
                if current_sent is not None:
                    yield current_sent, current_tags
                    current_sent = None
                    current_tags = []

    if current_sent is not None:
        yield current_sent, current_tags


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    errant_mapper = ErrantMapper()
    nucle_map     = _load_nucle_map()

    def map_tag(tag: str) -> tuple[str | None, str | None, str]:
        """Return (academie_code, academie_family, status)."""
        if _is_errant(tag):
            # Strip op prefix (R:, M:, U:)
            bare = tag[2:] if ":" in tag else tag
            entry = errant_mapper.map(bare)
            if entry:
                return entry.academie_code, entry.family, "mapped"
            return None, None, "unmappable"
        else:
            entry = nucle_map.get(tag)
            if entry is None:
                return None, None, "unmappable"
            if entry is None or entry == "null":
                return None, None, "unmappable"
            return entry.get("academie_code"), entry.get("academie_family"), "mapped"

    records = []
    learner_stats: dict[str, dict] = defaultdict(lambda: {
        "n_sentences": 0, "n_tokens": 0, "n_errors": 0
    })

    # NUCLE has no learner IDs in M2 — we treat each essay as one "learner"
    # using doc position as learner_id (nucle_<doc_idx>)
    doc_idx = 0
    sent_idx_global = 0
    sent_in_doc = 0
    prev_sent = None

    print("Parsing M2 section...")
    for sent, tags in _parse_m2_section(M2_FILE):
        # Doc boundary heuristic: essay titles are short ALL-CAPS sentences
        # that precede the main essay. We use sentence position reset.
        n_tok = len(sent.split())
        learner_id = f"nucle_{doc_idx:04d}"

        # Detect new doc: blank sentence or very short title-like sentence
        # after a gap — approximate by checking if sent_in_doc resets
        # We rely on blank lines yielded between sentences for doc separation
        # (heuristic: every 50+ sentences = new doc, or via explicit doc markers)

        for tag in tags if tags else []:
            code, family, status = map_tag(tag)
            records.append({
                "learner_id":       learner_id,
                "text_id":          f"nucle_{doc_idx:04d}_{sent_in_doc}",
                "corpus":           CORPUS_NAME,
                "split":            "train",
                "cefr_level":       CEFR_PROXY,
                "cefr_sublevel":    CEFR_SUB,
                "sentence_idx":     sent_in_doc,
                "n_tokens_sentence": n_tok,
                "errant_tag":       tag,
                "academie_code":    code,
                "academie_family":  family,
                "status":           status,
            })
            learner_stats[learner_id]["n_errors"] += 1

        learner_stats[learner_id]["n_sentences"] += 1
        learner_stats[learner_id]["n_tokens"]    += n_tok
        sent_in_doc  += 1
        sent_idx_global += 1

        # New doc every ~20 sentences (NUCLE essays avg ~20 sentences)
        if sent_in_doc >= 20:
            doc_idx    += 1
            sent_in_doc = 0

    print(f"Parsed {sent_idx_global} sentences → {len(records)} error annotations")
    print(f"Estimated {doc_idx + 1} documents (proxy learners)")

    # ── Build DataFrames ──────────────────────────────────────────────────────
    df_new = pd.DataFrame(records)
    df_learners_new = pd.DataFrame([
        {
            "learner_id":         lid,
            "cefr_level_modal":   CEFR_PROXY,
            "n_texts":            1,
            "n_sentences":        s["n_sentences"],
            "n_tokens":           s["n_tokens"],
            "n_errors":           s["n_errors"],
            "err_per_1k_tokens":  (s["n_errors"] / max(s["n_tokens"], 1)) * 1000,
        }
        for lid, s in learner_stats.items()
    ])

    print(f"\nNUCLE stats:")
    print(f"  Errors total:   {len(df_new)}")
    print(f"  Mapped:         {(df_new['status']=='mapped').sum()}")
    print(f"  Unmappable:     {(df_new['status']=='unmappable').sum()}")
    print(f"  Proxy learners: {len(df_learners_new)}")
    print(f"  ERRANT tags:    {df_new['errant_tag'].apply(_is_errant).sum()}")
    print(f"  NUCLE tags:     {(~df_new['errant_tag'].apply(_is_errant)).sum()}")

    # ── Merge with existing ───────────────────────────────────────────────────
    errors_path  = OUT / "errors_long.parquet"
    learners_path = OUT / "learners.parquet"

    df_existing       = pd.read_parquet(errors_path)
    df_learners_exist = pd.read_parquet(learners_path)

    # Drop any existing nucle rows (idempotent)
    df_existing       = df_existing[df_existing["corpus"] != CORPUS_NAME]
    df_learners_exist = df_learners_exist[~df_learners_exist["learner_id"].str.startswith("nucle_")]

    df_merged          = pd.concat([df_existing, df_new], ignore_index=True)
    df_learners_merged = pd.concat([df_learners_exist, df_learners_new], ignore_index=True)

    df_merged.to_parquet(errors_path, index=False)
    df_learners_merged.to_parquet(learners_path, index=False)

    print(f"\nMerged dataset:")
    print(f"  Total errors:   {len(df_merged)}")
    print(f"  Total learners: {len(df_learners_merged)}")
    print(f"  By corpus:      {df_merged['corpus'].value_counts().to_dict()}")
    print(f"  By CEFR:        {df_merged['cefr_level'].value_counts().to_dict()}")
    print("\n✅ Parquets updated.")

if __name__ == "__main__":
    main()
