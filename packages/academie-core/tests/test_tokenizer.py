"""Tests for academie_core.taxonomy.tokenizer — fallback + stubs."""
from __future__ import annotations

import pytest

from academie_core.taxonomy.tokenizer import Token, tokenize


class TestFallbackEnglish:
    def test_simple_sentence(self):
        tokens = tokenize("I love books.", lang="en")
        texts = [t.text for t in tokens]
        assert texts == ["I", "love", "books", "."]

    def test_offsets(self):
        tokens = tokenize("Hello world", lang="en")
        assert tokens[0] == Token("Hello", 0, 5)
        assert tokens[1] == Token("world", 6, 11)

    def test_empty_string(self):
        assert tokenize("", lang="en") == []

    def test_default_lang_is_en(self):
        assert tokenize("cat") == tokenize("cat", lang="en")


class TestFallbackRomance:
    def test_spanish_accents_and_enye(self):
        tokens = tokenize("La niña comió pan.", lang="es")
        texts = [t.text for t in tokens]
        assert "niña" in texts
        assert "comió" in texts

    def test_italian_apostrophe(self):
        tokens = tokenize("L'acqua è fresca.", lang="it")
        texts = [t.text for t in tokens]
        # L'acqua treated as clitic+noun — the fallback splits on apostrophe
        # as a non-word character; this is fine for rule-based detection.
        assert "acqua" in texts or "L'acqua" in texts


class TestFallbackGerman:
    def test_german_umlauts_and_esszett(self):
        tokens = tokenize("Ich heiße Müller.", lang="de")
        texts = [t.text for t in tokens]
        assert "heiße" in texts
        assert "Müller" in texts


class TestJpStub:
    def test_jp_raises(self):
        with pytest.raises(NotImplementedError, match="fugashi"):
            tokenize("こんにちは", lang="jp")

    def test_ja_alias_raises(self):
        with pytest.raises(NotImplementedError):
            tokenize("東京", lang="ja")


class TestRuStub:
    def test_ru_raises(self):
        with pytest.raises(NotImplementedError, match="pymorphy2"):
            tokenize("Привет", lang="ru")


class TestUnsupported:
    def test_unknown_lang_raises(self):
        with pytest.raises(ValueError, match="unsupported lang"):
            tokenize("text", lang="xx")


class TestCaseInsensitiveLang:
    def test_uppercase_lang_normalized(self):
        assert tokenize("hello", lang="EN") == tokenize("hello", lang="en")
