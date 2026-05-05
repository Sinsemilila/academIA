"""Cross-lang synthetic error generator — Phase 0.8.

Generalizes `scripts/generate_v3_training_data.py` (EN-only) for any
supported target language. Used by Waves to bootstrap fine-tune corpora
when annotated learner corpora are missing (notably JP) or to augment
them (all other langs).

Architecture :
- Descriptors live in `data/synthetic_descriptors/{lang}.yaml`
- Each descriptor = {code, family, level, description, examples_hint}
- GPT-4o-mini (via LiteLLM proxy) generates realistic errors per descriptor
- Output is JSONL in OpenAI fine-tune format

Usage :
    # Dry-run: no OpenAI call, prints n=3 descriptors & prompts
    python3 scripts/synthetic/generate_errors.py --lang es --level a2 --n 3 --dry-run

    # Actual generation (requires LiteLLM running at http://localhost:4000)
    python3 scripts/synthetic/generate_errors.py --lang es --level a2 --n 5 \\
        --output /tmp/train_es_a2.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx
import yaml


LITELLM_URL = "http://localhost:4000/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_DESCRIPTORS_DIR = Path("/opt/academia/data/synthetic_descriptors")


# ── Per-lang prompt templates ──────────────────────────────────────

_SYSTEM_PROMPT_BY_LANG: dict[str, str] = {
    "en": "You analyze English errors by French speakers. Identify every USER error. Output valid JSON.",
    "es": "Eres lingüista hispanohablante. Analizas errores en español cometidos por francófonos. Devuelves JSON válido.",
    "it": "Sei linguista italiano. Analizzi errori in italiano commessi da francofoni. Restituisci JSON valido.",
    "de": "Du bist deutscher Linguist. Du analysierst Fehler im Deutschen von französischsprachigen Lernern. JSON-Ausgabe.",
    "jp": "You analyze Japanese errors by French native speakers. Output valid JSON. Be concise.",
    "ru": "Ты русский лингвист. Анализируй ошибки в русском языке у франкоязычных учеников. Отвечай JSON.",
}

# Short language name used in the user prompt template.
_TARGET_LANG_NAME: dict[str, str] = {
    "en": "English", "es": "Spanish", "it": "Italian",
    "de": "German", "jp": "Japanese", "ru": "Russian",
}


@dataclass
class Descriptor:
    """One error descriptor to generate examples against."""
    code: str
    family: str
    level: str
    description: str
    # Optional free-form hint embedded in the user prompt for variety.
    examples_hint: str | None = None


def load_descriptors(lang: str, descriptors_dir: Path = DEFAULT_DESCRIPTORS_DIR
                     ) -> list[Descriptor]:
    path = descriptors_dir / f"{lang}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"No synthetic descriptors file for lang={lang!r}: {path}"
        )
    with open(path) as f:
        data = yaml.safe_load(f)
    out: list[Descriptor] = []
    for entry in data.get("descriptors", []):
        out.append(Descriptor(
            code=entry["code"],
            family=entry["family"],
            level=entry["level"].lower(),
            description=entry["description"],
            examples_hint=entry.get("examples_hint"),
        ))
    return out


def filter_descriptors(descs: list[Descriptor], level: str | None) -> list[Descriptor]:
    if level is None:
        return descs
    level = level.lower()
    return [d for d in descs if d.level == level]


def build_user_prompt(lang: str, desc: Descriptor, n_examples: int) -> str:
    target_name = _TARGET_LANG_NAME[lang]
    hint = f"\n\nHint: {desc.examples_hint}" if desc.examples_hint else ""
    return f"""Generate {n_examples} UNIQUE {target_name} sentences containing exactly ONE error of type {desc.code}.

Error type: {desc.description}
Family: {desc.family}
CEFR level: {desc.level.upper()}{hint}

Context: French native speaker learning {target_name}. Sentences should be realistic,
varied topics, level-appropriate.

STRICT RULES:
- Each sentence MUST contain the erroneous form (not the correct one)
- The error MUST be of type {desc.code} — no other error types
- The `original` span MUST be a substring of `sentence` (exact match, including punctuation)
- The `correction` MUST differ from `original` (non-null fix)
- If you CANNOT produce a natural sentence containing this specific error, SKIP it and produce fewer examples — better fewer good ones than hallucinated errors
- Vary sentence length (5-20 words) and topic (family, work, food, travel, study…)
- Make errors natural (what a FR→{target_name} learner would actually produce)
- Do NOT include translations or explanations inside the sentence field
- Do NOT label already-correct sentences as having errors

Output as a JSON array. Each item:
{{"sentence": "the erroneous {target_name} sentence", "original": "the error span", "correction": "the fix", "reasoning": "brief explanation in {target_name} (1 sentence)"}}

Output ONLY the JSON array, no other text."""


# ── OpenAI / LiteLLM call ──────────────────────────────────────────

def call_generator(lang: str, desc: Descriptor, n_examples: int,
                   model: str = DEFAULT_MODEL,
                   temperature: float = 0.6) -> list[dict]:
    """Call LiteLLM proxy to generate a batch of examples. Live call."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT_BY_LANG.get(lang, _SYSTEM_PROMPT_BY_LANG["en"])},
            {"role": "user", "content": build_user_prompt(lang, desc, n_examples)},
        ],
        "temperature": temperature,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=180) as client:
        try:
            resp = client.post(LITELLM_URL, json=payload)
            resp.raise_for_status()
        except (httpx.ReadTimeout, httpx.HTTPStatusError) as e:
            print(f"[{desc.code}] API call failed: {type(e).__name__}", file=sys.stderr)
            return []
    content = resp.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            for key in ("examples", "sentences", "errors", "data", "items"):
                if key in parsed:
                    parsed = parsed[key]
                    break
            else:
                parsed = list(parsed.values())[0] if parsed else []
        if not isinstance(parsed, list):
            return []
        return parsed
    except (json.JSONDecodeError, IndexError):
        return []


def validate_example(lang: str, desc: Descriptor, example: dict) -> tuple[bool, str]:
    """Post-filter: reject hallucinated/malformed examples.

    Returns (is_valid, reason_if_not).
    """
    sentence = (example.get("sentence") or "").strip()
    original = (example.get("original") or "").strip()
    correction = (example.get("correction") or "").strip()

    # Basic field presence
    if not sentence or not original:
        return False, "missing sentence or original"
    if not correction:
        return False, "missing correction"
    if original == correction:
        return False, "original == correction (no error)"
    # `original` must be a substring of `sentence` (exact, case-insensitive)
    if original.lower() not in sentence.lower():
        return False, f"original {original!r} not in sentence"

    # Rules-layer validation: if we have a mechanical detector for this code,
    # verify it fires. Catches the most blatant hallucinations (e.g. claiming
    # QUANT:MUY_MUCHO on a correct 'me gusta mucho' sentence).
    if lang == "es":
        try:
            from academie_core.taxonomy.rules_es import detect_errors_es
            detected = detect_errors_es(sentence)
            detected_codes = {d.error_code for d in detected}
            # For codes covered by rules_es, require a matching detection.
            RULES_ES_CODES = {
                "PUNCT:INTERROG", "ORTH:NY", "ART:PROF", "LEX:FALSE",
                "PREP:CALQUE", "V:SER_ESTAR", "PREP:POR_PARA",
                "V:GUSTAR_SUBJECT", "IDIOM:HACE_AGO", "QUANT:MUY_MUCHO",
                "PREP:MOVEMENT", "LEX:FR_RESIDUE", "ASPECT:PERF_OVERUSE",
            }
            if desc.code in RULES_ES_CODES and desc.code not in detected_codes:
                return False, f"rules_es.py does not detect {desc.code} in sentence — likely hallucination"
        except Exception:
            # If rules_es import fails, fall through (don't block generation)
            pass

    return True, "ok"


def to_finetune_format(lang: str, desc: Descriptor, example: dict) -> dict | None:
    """Convert a generated example to OpenAI fine-tune JSONL format."""
    ok, reason = validate_example(lang, desc, example)
    if not ok:
        return None
    sentence = example["sentence"].strip()
    original = example["original"].strip()
    correction = example["correction"].strip()
    reasoning = (example.get("reasoning") or "").strip()
    user_content = f"Analyze errors:\n--- Turn 1 ---\nUSER: {sentence}\nTEACHER: Good try!"
    assistant_content = json.dumps({
        "errors": [{
            "turn": 1,
            "original": original,
            "correction": correction,
            "codes": [desc.code],
            "family": desc.family,
            "level": desc.level,
            "reasoning": reasoning,
        }]
    })
    system = _SYSTEM_PROMPT_BY_LANG.get(lang, _SYSTEM_PROMPT_BY_LANG["en"])
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


# ── Public API ─────────────────────────────────────────────────────

def generate_synthetic_errors(
    lang: str,
    n_examples_per_descriptor: int,
    *,
    level: str | None = None,
    descriptors_dir: Path = DEFAULT_DESCRIPTORS_DIR,
    seed: int = 42,
    dry_run: bool = False,
    sleep_between: float = 0.1,
) -> Iterator[dict]:
    """Generate fine-tune-formatted examples for a language.

    Yields one JSONL-ready dict per example. Use list(…) to materialize.
    Set `dry_run=True` to print prompts instead of calling OpenAI.
    """
    if lang not in _SYSTEM_PROMPT_BY_LANG:
        raise ValueError(f"unsupported lang: {lang!r}")
    descs = filter_descriptors(load_descriptors(lang, descriptors_dir), level)
    if not descs:
        raise ValueError(
            f"no descriptors matched lang={lang!r} level={level!r} in {descriptors_dir}"
        )
    random.seed(seed)
    random.shuffle(descs)
    stats = {"generated": 0, "kept": 0, "rejected": 0}
    for desc in descs:
        if dry_run:
            prompt = build_user_prompt(lang, desc, n_examples_per_descriptor)
            print(f"── {desc.code} ({desc.family}, {desc.level}) ──")
            print(prompt[:400] + ("..." if len(prompt) > 400 else ""))
            print()
            continue
        examples = call_generator(lang, desc, n_examples_per_descriptor)
        stats["generated"] += len(examples)
        kept_here = 0
        for ex in examples:
            ft = to_finetune_format(lang, desc, ex)
            if ft is not None:
                stats["kept"] += 1
                kept_here += 1
                yield ft
            else:
                stats["rejected"] += 1
        print(f"[{desc.code}] gen={len(examples)} kept={kept_here}/{len(examples)}",
              file=sys.stderr)
        time.sleep(sleep_between)
    if not dry_run:
        print(f"\n=== SUMMARY === generated={stats['generated']} "
              f"kept={stats['kept']} rejected={stats['rejected']} "
              f"filter_rate={stats['rejected']/max(1,stats['generated']):.1%}",
              file=sys.stderr)


# ── CLI ─────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Cross-lang synthetic error generator (Phase 0.8).")
    p.add_argument("--lang", required=True,
                   choices=sorted(_SYSTEM_PROMPT_BY_LANG.keys()),
                   help="Target language.")
    p.add_argument("--level", default=None,
                   help="Filter to descriptors at this CEFR level (a1-c2).")
    p.add_argument("--n", type=int, default=5,
                   help="Examples per descriptor (default 5).")
    p.add_argument("--output", type=Path, default=None,
                   help="Write JSONL here. Defaults to /tmp/synthetic_{lang}.jsonl.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print prompts instead of calling LiteLLM. Free & safe.")
    args = p.parse_args()

    out_path = args.output or Path(f"/tmp/synthetic_{args.lang}.jsonl")
    try:
        examples = list(generate_synthetic_errors(
            lang=args.lang, n_examples_per_descriptor=args.n,
            level=args.level, dry_run=args.dry_run,
        ))
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.dry_run:
        print("▸ Dry-run only — no OpenAI calls made.")
        return 0

    with open(out_path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"▸ Wrote {len(examples)} examples to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
