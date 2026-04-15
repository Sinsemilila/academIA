"""ERRANT → AcademIA mapper.

Loads errant_to_academie.yaml and exposes `map_errant_tag(tag)`.

ERRANT tag format: "OP:CAT[:SUBCAT]"   e.g. "R:VERB:TENSE", "M:PREP", "U:DET".
Operation prefix is stripped before lookup (OP does not change the family).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

_HERE = Path(__file__).parent
_YAML = _HERE / "errant_to_academie.yaml"


@dataclass(frozen=True)
class MappedError:
    errant_tag: str
    academie_code: Optional[str]
    family: Optional[str]
    status: str  # "mapped", "unmappable", "unknown"


class ErrantMapper:
    def __init__(self, yaml_path: Path = _YAML) -> None:
        with open(yaml_path) as f:
            cfg = yaml.safe_load(f)
        self._mappings: dict[str, dict] = cfg["mappings"]
        self._unmappable: dict[str, dict] = cfg.get("unmappable", {})

    @staticmethod
    def _strip_op(tag: str) -> str:
        """Remove leading M:/R:/U: operation prefix."""
        if len(tag) >= 2 and tag[1] == ":" and tag[0] in ("M", "R", "U"):
            return tag[2:]
        return tag

    def map(self, errant_tag: str) -> MappedError:
        core = self._strip_op(errant_tag)
        if core in self._mappings:
            m = self._mappings[core]
            return MappedError(errant_tag, m["academie_code"], m["family"], "mapped")
        if core in self._unmappable:
            return MappedError(errant_tag, None, None, "unmappable")
        return MappedError(errant_tag, None, None, "unknown")


def map_errant_tag(tag: str, _mapper=ErrantMapper()) -> MappedError:
    """Convenience wrapper with a module-level cached mapper."""
    return _mapper.map(tag)
