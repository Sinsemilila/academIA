"""
AcademIA Error Taxonomy — Step 2: Diff engine
Compares original and corrected text to extract minimal edit spans.
Deterministic, zero cost, no LLM.
"""

import re
from dataclasses import dataclass, field


@dataclass
class EditSpan:
    """A single difference between original and corrected text."""
    original: str
    corrected: str
    context: str  # the full original sentence for LLM fallback
    position: int = 0  # character offset in original


def extract_edits(original: str, corrected: str) -> list[EditSpan]:
    """
    Extract minimal edit spans between original and corrected text.
    Uses token-level alignment for better granularity than character diff.
    """
    orig_tokens = _tokenize(original)
    corr_tokens = _tokenize(corrected)

    if orig_tokens == corr_tokens:
        return []

    edits = []
    # Use sequence matcher on tokens
    import difflib
    matcher = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            continue

        orig_chunk = " ".join(orig_tokens[i1:i2])
        corr_chunk = " ".join(corr_tokens[j1:j2])

        if op == "replace":
            # Try to break down multi-token replacements into individual edits
            sub_edits = _break_down_replacement(
                orig_tokens[i1:i2], corr_tokens[j1:j2], original
            )
            edits.extend(sub_edits)
        elif op == "insert":
            # Something was added in correction (missing in original)
            edits.append(EditSpan(
                original="",
                corrected=corr_chunk,
                context=original,
            ))
        elif op == "delete":
            # Something was removed (unnecessary in original)
            edits.append(EditSpan(
                original=orig_chunk,
                corrected="",
                context=original,
            ))

    return _deduplicate(edits)


def _break_down_replacement(orig_tokens: list[str], corr_tokens: list[str], context: str) -> list[EditSpan]:
    """
    Break a multi-token replacement into individual token-level edits where possible.
    E.g., "i lived in paris" → "I have lived in Paris" should produce:
      - "i" → "I"
      - "lived" → "have lived"
      - "paris" → "Paris"
    Not one big replacement.
    """
    edits = []

    if len(orig_tokens) == len(corr_tokens):
        # Same number of tokens — compare pairwise
        for orig, corr in zip(orig_tokens, corr_tokens):
            if orig != corr:
                edits.append(EditSpan(original=orig, corrected=corr, context=context))
    elif len(orig_tokens) == 1 and len(corr_tokens) == 1:
        edits.append(EditSpan(
            original=orig_tokens[0], corrected=corr_tokens[0], context=context
        ))
    else:
        # Different token counts — try sub-alignment
        import difflib
        sub = difflib.SequenceMatcher(None, orig_tokens, corr_tokens)
        for op, i1, i2, j1, j2 in sub.get_opcodes():
            if op == "equal":
                continue
            orig_part = " ".join(orig_tokens[i1:i2])
            corr_part = " ".join(corr_tokens[j1:j2])
            edits.append(EditSpan(
                original=orig_part,
                corrected=corr_part,
                context=context,
            ))

    return edits


def _tokenize(text: str) -> list[str]:
    """
    Simple tokenizer that preserves punctuation as separate tokens.
    "I don't" → ["I", "don't"]
    "She's" → ["She's"]
    """
    # Split on whitespace, keep contractions together
    tokens = []
    for word in text.split():
        # Separate trailing punctuation (but keep apostrophes inside words)
        match = re.match(r"^(.*?)([.,!?;:]+)$", word)
        if match and match.group(1):
            tokens.append(match.group(1))
            tokens.append(match.group(2))
        else:
            tokens.append(word)
    return tokens


def _deduplicate(edits: list[EditSpan]) -> list[EditSpan]:
    """Remove duplicate edits (same original→corrected)."""
    seen = set()
    result = []
    for e in edits:
        key = (e.original.lower(), e.corrected.lower())
        if key not in seen:
            seen.add(key)
            result.append(e)
    return result
