"""Tests for scripts/synthetic/generate_errors.py (no OpenAI calls)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from generate_errors import (  # noqa: E402
    Descriptor,
    _SYSTEM_PROMPT_BY_LANG,
    build_user_prompt,
    filter_descriptors,
    generate_synthetic_errors,
    load_descriptors,
    to_finetune_format,
)


DEFAULT_DIR = Path("/opt/academia/data/synthetic_descriptors")


class TestLoadDescriptors:
    def test_es_loads(self):
        descs = load_descriptors("es", DEFAULT_DIR)
        assert len(descs) >= 5
        assert all(isinstance(d, Descriptor) for d in descs)

    def test_jp_loads(self):
        descs = load_descriptors("jp", DEFAULT_DIR)
        assert len(descs) >= 5
        # Critical: JP has particle descriptors as primary category
        codes = [d.code for d in descs]
        assert any("PARTICLE" in c for c in codes)

    def test_all_5_langs_available(self):
        for lang in ["es", "it", "de", "jp", "ru"]:
            descs = load_descriptors(lang, DEFAULT_DIR)
            assert len(descs) > 0, f"no descriptors for {lang}"

    def test_missing_lang_raises(self):
        with pytest.raises(FileNotFoundError):
            load_descriptors("zz", DEFAULT_DIR)


class TestFilter:
    def test_filter_by_level(self):
        descs = [
            Descriptor("A", "x", "a1", "..."),
            Descriptor("B", "y", "a2", "..."),
            Descriptor("C", "z", "a2", "..."),
        ]
        assert len(filter_descriptors(descs, "a2")) == 2
        assert len(filter_descriptors(descs, None)) == 3
        assert len(filter_descriptors(descs, "c1")) == 0


class TestPromptBuilding:
    def test_prompt_includes_lang_name(self):
        d = Descriptor("TEST", "fam", "a1", "desc")
        prompt = build_user_prompt("es", d, 3)
        assert "Spanish" in prompt
        assert "TEST" in prompt
        assert "3 UNIQUE" in prompt

    def test_hint_included_when_set(self):
        d = Descriptor("X", "fam", "b1", "desc", examples_hint="foo")
        assert "Hint: foo" in build_user_prompt("en", d, 1)

    def test_hint_omitted_when_none(self):
        d = Descriptor("X", "fam", "b1", "desc")
        assert "Hint:" not in build_user_prompt("en", d, 1)


class TestFinetuneFormat:
    def test_well_formed_example(self):
        d = Descriptor("V:TEST", "verb_usage", "a2", "desc")
        ex = {
            "sentence": "wrong sentence",
            "original": "wrong",
            "correction": "right",
            "reasoning": "because",
        }
        out = to_finetune_format("es", d, ex)
        assert out is not None
        assert out["messages"][0]["role"] == "system"
        assert "español" in out["messages"][0]["content"].lower() or "es" in out["messages"][0]["content"].lower()
        # assistant content is JSON-parseable with expected fields
        parsed = json.loads(out["messages"][2]["content"])
        assert parsed["errors"][0]["codes"] == ["V:TEST"]
        assert parsed["errors"][0]["family"] == "verb_usage"

    def test_missing_fields_skipped(self):
        d = Descriptor("X", "f", "a1", "d")
        assert to_finetune_format("en", d, {"sentence": "", "original": "x"}) is None
        assert to_finetune_format("en", d, {"sentence": "x", "original": ""}) is None


class TestDryRun:
    def test_dry_run_yields_nothing(self):
        # dry_run just prints; generator produces no items
        results = list(generate_synthetic_errors(
            lang="es", n_examples_per_descriptor=1,
            level="a2", dry_run=True,
        ))
        assert results == []

    def test_invalid_lang_raises(self):
        with pytest.raises(ValueError, match="unsupported"):
            list(generate_synthetic_errors(
                lang="xx", n_examples_per_descriptor=1, dry_run=True
            ))

    def test_no_descriptors_at_level_raises(self):
        with pytest.raises(ValueError, match="no descriptors"):
            list(generate_synthetic_errors(
                lang="es", n_examples_per_descriptor=1,
                level="c2", dry_run=True,
            ))


class TestSystemPromptsAllLangs:
    def test_all_5_langs_have_system_prompt(self):
        for lang in ["es", "it", "de", "jp", "ru"]:
            assert lang in _SYSTEM_PROMPT_BY_LANG
            assert len(_SYSTEM_PROMPT_BY_LANG[lang]) > 10
