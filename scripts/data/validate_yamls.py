#!/usr/bin/env python3
"""Standalone CLI validator for academie_core YAML data packs.

Mirrors the pytest suite at `packages/academie-core/tests/test_yaml_schema.py`
but usable as a one-shot check from the terminal without pytest setup.
Useful when editing a single YAML and wanting a <1s validation loop.

Usage :
  python3 scripts/data/validate_yamls.py --all-langs
  python3 scripts/data/validate_yamls.py --lang es
  python3 scripts/data/validate_yamls.py --lang en --lang es --strict-only

Exit code : 0 if every pack validates, 1 on any failure.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "packages" / "academie-core"))

from academie_core.data.schemas import (  # noqa: E402
    CEFRDiagnosticsPack,
    ConceptHintsPack,
    CurriculumPack,
    FewshotPack,
    L1NamesPack,
    L1TransferPack,
    MicroLessonPack,
    MiniExamBank,
    RubricPack,
)

DATA_DIR = REPO / "packages" / "academie-core" / "academie_core" / "data"
ALL_LANGS = ["en", "es", "it", "de", "ja", "ru"]
ACTIVE_LANGS = {"en", "es"}  # Wave 1 — must pass
EXAM_LEVELS = ["A1", "A2", "B1", "B2"]

# (label, path_template, loader) — loader returns None if OK, raises on failure
_PACKS: list[tuple[str, str, Callable[[dict], None]]] = [
    ("rubrics",          "rubrics/{lang}.yaml",          lambda r: RubricPack.model_validate(r)),
    ("fewshots",         "fewshots/{lang}.yaml",         lambda r: FewshotPack.model_validate(r)),
    ("concept_hints",    "concept_hints/{lang}.yaml",    ConceptHintsPack.validate_mapping),
    ("cefr_diagnostics", "cefr_diagnostics/{lang}.yaml", lambda r: CEFRDiagnosticsPack.model_validate(r)),
    ("curriculum",       "curriculum_{lang}.yaml",       CurriculumPack.validate_mapping),
    ("micro_lessons",    "micro_lessons/{lang}.yaml",    MicroLessonPack.validate_mapping),
]


class Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: list[tuple[str, str]] = []  # (label, message)

    def add_pass(self):    self.passed += 1
    def add_skip(self):    self.skipped += 1
    def add_fail(self, label: str, err: str):
        self.failed += 1
        self.errors.append((label, err))

    def status_line(self) -> str:
        return f"{self.passed} ✓  {self.failed} ✗  {self.skipped} skipped"


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    with path.open() as f:
        return yaml.safe_load(f)


def _validate_pack(label: str, path: Path, loader, is_active: bool, r: Result) -> None:
    raw = _load(path)
    if raw is None:
        if is_active:
            r.add_fail(label, f"{path.relative_to(REPO)} missing (active lang, required)")
        else:
            r.add_skip()
        return
    try:
        loader(raw)
        r.add_pass()
    except Exception as e:
        r.add_fail(label, f"{path.relative_to(REPO)} → {type(e).__name__}: {e}")


def validate(langs: list[str]) -> Result:
    r = Result()
    for lang in langs:
        is_active = lang in ACTIVE_LANGS
        for label, template, loader in _PACKS:
            path = DATA_DIR / template.format(lang=lang)
            _validate_pack(f"{label}[{lang}]", path, loader, is_active, r)
        # Mini-exam : active langs only, parameterized on CEFR level
        if is_active:
            for level in EXAM_LEVELS:
                path = DATA_DIR / "mini_exam" / f"{lang}_{level}.yaml"
                _validate_pack(
                    f"mini_exam[{lang}_{level}]", path,
                    lambda raw: MiniExamBank.model_validate(raw),
                    False, r,  # mini-exam is optional even for active langs
                )
        # L1 transfer (fr → lang)
        path = DATA_DIR / "l1_transfer" / f"fr_to_{lang}.yaml"
        _validate_pack(
            f"l1_transfer[fr→{lang}]", path,
            lambda raw: L1TransferPack.model_validate(raw),
            False, r,
        )
    # l1_names (lang-agnostic, once)
    path = DATA_DIR / "l1_transfer" / "l1_names.yaml"
    _validate_pack("l1_names", path, lambda raw: L1NamesPack.model_validate(raw), True, r)
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all-langs", action="store_true", help="validate every known lang")
    grp.add_argument("--lang", action="append", help="validate a specific lang (repeatable)")
    ap.add_argument("--quiet", action="store_true", help="suppress per-pack logs, keep scorecard only")
    args = ap.parse_args()

    langs = ALL_LANGS if args.all_langs else args.lang
    if not langs:
        ap.error("--all-langs or --lang required")

    r = validate(langs)

    if r.failed:
        print("FAILED :")
        for label, msg in r.errors:
            print(f"  ✗ {label:<30} {msg}")
        print()
    elif not args.quiet:
        print("All YAMLs validated.")
    print(f"Scorecard : {r.status_line()}  ({len(langs)} lang)")
    return 1 if r.failed else 0


if __name__ == "__main__":
    sys.exit(main())
