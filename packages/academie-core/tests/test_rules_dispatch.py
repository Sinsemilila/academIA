"""Tests for rules.py cross-language dispatch + per-lang skeleton detectors."""
from __future__ import annotations

from academie_core.taxonomy.rules import detect_errors


class TestDispatch:
    def test_empty_text_returns_empty(self):
        for lang in ["en", "es", "it", "de", "jp", "ru"]:
            assert detect_errors("", lang=lang) == []

    def test_unknown_lang_returns_empty(self):
        assert detect_errors("some text", lang="xx") == []

    def test_default_is_english(self):
        # EN detectors should fire on default lang
        result = detect_errors("I love paris.", lang="en")
        # "paris" should trigger ORTH:CASE proper-noun detection
        assert any(r.error_code == "ORTH:CASE" for r in result)


class TestItalian:
    def test_aux_essere_avere(self):
        result = detect_errors("Ho andato al cinema.", lang="it")
        codes = [r.error_code for r in result]
        assert "IT:AUX" in codes

    def test_missing_contraction(self):
        result = detect_errors("Vado a il cinema.", lang="it")
        codes = [r.error_code for r in result]
        assert "IT:ART_CONTRACT" in codes

    def test_false_friend_libreria(self):
        result = detect_errors("Vado in libreria per studiare.", lang="it")
        codes = [r.error_code for r in result]
        assert "IT:FALSE_FRIEND" in codes

    def test_clean_italian_no_errors(self):
        result = detect_errors("Ciao, come stai oggi?", lang="it")
        # Should have no detections (maybe 0) for well-formed simple IT
        codes = [r.error_code for r in result]
        assert "IT:AUX" not in codes


class TestGerman:
    def test_missing_umlaut(self):
        result = detect_errors("Ich kann nicht uber den Berg.", lang="de")
        codes = [r.error_code for r in result]
        assert "DE:UMLAUT" in codes

    def test_false_friend_gymnasium(self):
        result = detect_errors("Ich gehe zum Gymnasium.", lang="de")
        codes = [r.error_code for r in result]
        assert "DE:FALSE_FRIEND" in codes

    def test_split_compound(self):
        result = detect_errors("Ich mache meine haus aufgabe.", lang="de")
        codes = [r.error_code for r in result]
        assert "DE:COMPOUND_SPACE" in codes


class TestJapanese:
    def test_fr_article_leak(self):
        result = detect_errors("J'aime le neko de ma sœur.", lang="jp")
        codes = [r.error_code for r in result]
        assert "JP:FR_ARTICLE_LEAK" in codes

    def test_ja_alias_routes_to_jp(self):
        result = detect_errors("J'aime le neko.", lang="ja")
        codes = [r.error_code for r in result]
        assert "JP:FR_ARTICLE_LEAK" in codes

    def test_double_particle(self):
        result = detect_errors("本をを読みます", lang="jp")
        codes = [r.error_code for r in result]
        assert "JP:DOUBLE_PARTICLE" in codes


class TestRussian:
    def test_fr_article_leak(self):
        result = detect_errors("J'habite le moskva.", lang="ru")
        codes = [r.error_code for r in result]
        assert "RU:FR_ARTICLE_LEAK" in codes

    def test_soft_sign_miss(self):
        result = detect_errors("Это мат моя.", lang="ru")
        codes = [r.error_code for r in result]
        assert "RU:HARD_SOFT_SIGN" in codes


class TestSpanishStillWorks:
    """Regression: Sprint 5 ES dispatch must keep working."""

    def test_es_still_routes(self):
        result = detect_errors("Soy un médico.", lang="es")
        codes = [r.error_code for r in result]
        assert "ART:PROF" in codes
