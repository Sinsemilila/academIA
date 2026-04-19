"""Tests for the cross-lang corpus normalizer framework (Phase 0.2)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SPRINT1 = Path(__file__).resolve().parents[2]
if str(_SPRINT1) not in sys.path:
    sys.path.insert(0, str(_SPRINT1))

from normalizers import normalize  # noqa: E402


class TestDispatch:
    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="unknown corpus source"):
            normalize(source="zzz", path="/tmp/fake", lang="en")


class TestStubs:
    def test_errant_not_callable(self):
        with pytest.raises(NotImplementedError, match="02_normalize.py"):
            normalize(source="errant", path="/tmp/fake", lang="en")

    def test_cows_stub(self):
        with pytest.raises(NotImplementedError, match="Wave 1"):
            normalize(source="cows", path="/tmp/fake", lang="es")

    def test_merlin_it_stub(self):
        with pytest.raises(NotImplementedError, match="Wave 2"):
            normalize(source="merlin", path="/tmp/fake", lang="it")

    def test_merlin_de_stub(self):
        with pytest.raises(NotImplementedError, match="Wave 2"):
            normalize(source="merlin", path="/tmp/fake", lang="de")

    def test_merlin_wrong_lang_rejected(self):
        with pytest.raises(ValueError, match="no 'es' subcorpus"):
            normalize(source="merlin", path="/tmp/fake", lang="es")

    def test_falko_stub(self):
        with pytest.raises(NotImplementedError, match="Wave 2"):
            normalize(source="falko", path="/tmp/fake", lang="de")

    def test_falko_wrong_lang_rejected(self):
        with pytest.raises(ValueError, match="DE-only"):
            normalize(source="falko", path="/tmp/fake", lang="it")

    def test_rlc_stub(self):
        with pytest.raises(NotImplementedError, match="Wave 4"):
            normalize(source="rlc", path="/tmp/fake", lang="ru")

    def test_rlc_wrong_lang_rejected(self):
        with pytest.raises(ValueError, match="RU-only"):
            normalize(source="rlc", path="/tmp/fake", lang="en")
