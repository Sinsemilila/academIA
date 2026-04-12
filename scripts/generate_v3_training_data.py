#!/usr/bin/env python3
"""
Generate ~5000 training examples for fine-tune v3.
Uses gpt-4o-mini base via LiteLLM to generate diverse error examples.
Weighted: more examples for categories with low recall in v2.
"""

import json
import time
import httpx
import re
import sys
from collections import defaultdict

LITELLM_URL = "http://localhost:4000/v1/chat/completions"
MODEL = "gpt-4o-mini"

# Categories grouped by v2 recall performance
# 0% recall → 120 examples, <70% → 100, >=70% → 60
CATEGORY_TARGETS = {
    # 100% recall in v2 — 60 examples each
    "V:TENSE": 60, "V:SVA": 60, "V:FORM": 60, "V:MODAL": 60, "V:COND": 60,
    "V:ASPECT": 60, "V:AUX": 60, "V:INFL": 60, "V:PASS": 60, "V:EXIST": 60,
    "V:PHRASAL": 60, "N:COUNT": 60, "N:INFL": 60, "N:POSS": 60,
    "ORTH:CASE": 60, "ORTH:SPACE": 60, "SPELL": 60, "SPELL:COGNATE": 60,
    "PREP:CALQUE": 60, "MORPH:DERIV": 60, "PRON:FORM": 60,
    "ADJ:FORM": 60, "ADJ:ORDER": 60, "ADJ:CHOICE": 60, "ADV:CHOICE": 60,
    "DET": 60, "WO:QUEST": 60, "SENT:FRAG": 60, "SENT:MOD": 60,
    "SENT:NEG": 60, "SENT:PARALLEL": 60, "SENT:RUNON": 60, "SENT:SUBORD": 60,
    "REG:PRAGMA": 60, "REG:LEVEL": 60, "REDUND": 60,
    "LEX:COLLOC": 60, "LEX:FALSE": 60, "LEX:IDIOM": 60,
    "DISC:TRANS": 60, "DISC:COHER": 60, "PUNCT:COMMA": 60,
    # <70% recall — 100 examples each
    "ART": 100, "ART:GENERIC": 100, "LEX:CHOICE": 100, "LEX:CALQUE": 100,
    "LEX:ARGSTRUCT": 100, "N:CHOICE": 100, "PRON:CHOICE": 100,
    "PREP": 100, "V:CHOICE": 100, "WO": 100, "MORPH:WORDCLASS": 100,
    "PUNCT:APOST": 100,
    # 0% recall — 120 examples each
    "N:NUM": 120, "ADV:ORDER": 120, "CONJ": 120, "CONTR": 120,
    "DISC:COHES": 120, "DISC:CONNOVER": 120, "LEX:REGISTER": 120,
    "PRON:REF": 120, "PUNCT": 120,
}

# Descriptions for generation prompts
CATEGORY_DESCRIPTIONS = {
    "V:TENSE": "wrong tense (present perfect with 'yesterday', past simple with 'since')",
    "V:SVA": "subject-verb agreement (she have → has, everyone have → has)",
    "V:FORM": "gerund/infinitive/participle (enjoy to swim → swimming, avoid to go → going)",
    "V:MODAL": "modal verb error (must to go → must go, should goes → should go)",
    "V:COND": "conditional structure (if I would know → if I knew)",
    "V:ASPECT": "progressive misuse with stative verbs (I am understanding → I understand)",
    "V:AUX": "auxiliary/do-support missing (I not understand → I don't understand, You like? → Do you like?)",
    "V:INFL": "irregular verb inflection (goed → went, thinked → thought)",
    "V:PASS": "passive voice error (The book wrote by → was written by)",
    "V:EXIST": "existential construction French calque (It has many people → There are many people)",
    "V:CHOICE": "wrong verb entirely (said me → told me, make a travel → take a trip)",
    "V:PHRASAL": "wrong/missing phrasal verb particle (look in → look into, give up of → give up)",
    "N:NUM": "regular singular/plural error (many student → students). NOT uncountable nouns.",
    "N:POSS": "possessive marking (student book → student's book)",
    "N:INFL": "irregular plural (childs → children, mouses → mice)",
    "N:CHOICE": "wrong noun (a good work → a good job)",
    "N:COUNT": "uncountable noun error (informations → information, furnitures → furniture, advices → advice)",
    "ART": "article error (I bought car → a car, She is doctor → a doctor)",
    "ART:GENERIC": "zero article for generics, French transfer (the life → life, the music → music)",
    "DET": "determiner error (this books → these books, much people → many people)",
    "PREP": "wrong preposition NOT French calque (arrive to → at, discuss about → discuss)",
    "PREP:CALQUE": "French preposition calque (depend of → on, interested by → in, since 5 years → for)",
    "WO": "word order (speaks well English → English well, I very much like → I like very much)",
    "WO:QUEST": "question word order missing do-support (Where you go? → Where do you go?)",
    "ADJ:CHOICE": "wrong adjective (a big temperature → high, a strong rain → heavy)",
    "ADJ:FORM": "comparative/superlative (more big → bigger, most easy → easiest)",
    "ADJ:ORDER": "adjective placement French calque (a car red → a red car)",
    "ADV:CHOICE": "wrong adverb form (drives fastly → fast, worked hardly → hard)",
    "ADV:ORDER": "adverb misplaced (He drives always → He always drives, I eat usually → I usually eat)",
    "PRON:FORM": "pronoun case (Him went → He went, between you and I → me)",
    "PRON:CHOICE": "wrong pronoun (the man which → who, the company who → which)",
    "PRON:REF": "ambiguous pronoun reference (John told Bill he was wrong — who is 'he'?)",
    "SENT:RUNON": "run-on / comma splice (I like cats, I hate dogs → I like cats but I hate dogs)",
    "SENT:FRAG": "sentence fragment (Because I was tired. → incomplete sentence)",
    "SENT:NEG": "double negative (don't have nothing → anything, can't find nobody → anybody)",
    "SENT:MOD": "dangling/misplaced modifier (Walking home, the rain started → While I was walking)",
    "SENT:PARALLEL": "parallelism (likes reading, to swim, and biking → reading, swimming, and biking)",
    "SENT:SUBORD": "subordinate clause error (I don't know that should I go → if I should go)",
    "CONJ": "wrong conjunction (and instead of although/but when contrast is needed)",
    "LEX:CHOICE": "wrong word or French calque (I have 25 years → I am 25, close the TV → turn off)",
    "LEX:COLLOC": "collocation error (do a mistake → make a mistake, do sport → play sport)",
    "LEX:FALSE": "false friend used with French meaning (actually meaning currently, library meaning bookshop)",
    "LEX:CALQUE": "literal French translation (it makes 3 years → it's been 3 years, I have hunger → I'm hungry)",
    "LEX:IDIOM": "idiom error (break a foot → break a leg, it's raining cats and frogs → dogs)",
    "LEX:ARGSTRUCT": "argument structure (explain me → explain to me, suggest me → suggest to me)",
    "LEX:REGISTER": "informal WORD in formal context (gonna/wanna/chill in business writing)",
    "MORPH:DERIV": "derivation error (hapiness → happiness, beautifull → beautiful)",
    "MORPH:WORDCLASS": "wrong word class (I am very happiness → happy, his success was hardly → hard)",
    "DISC:TRANS": "transition/connector error (missing or wrong linking word between ideas)",
    "DISC:COHER": "coherence problem (logical flow, contradictory ideas, non-sequitur)",
    "DISC:COHES": "cohesion problem (repetitive noun instead of pronoun, no cross-sentence reference)",
    "DISC:CONNOVER": "connector overuse French essay style (moreover/furthermore/indeed spam)",
    "REG:LEVEL": "overall text formality mismatch (yo professor, hey dude in formal email)",
    "REG:PRAGMA": "pragmatic error (too direct: Give me the salt → Could you pass the salt)",
    "SPELL": "misspelling NOT French (definately → definitely, enviroment → environment)",
    "SPELL:COGNATE": "French spelling (confort → comfort, gouvernment → government, appartment → apartment)",
    "ORTH:CASE": "capitalization (i → I, paris → Paris, monday → Monday)",
    "ORTH:SPACE": "spacing (aswell → as well, eventhough → even though, alot → a lot)",
    "PUNCT": "punctuation error — period, semicolon, colon misuse (NOT comma, NOT apostrophe)",
    "PUNCT:COMMA": "comma error (missing comma after introductory clause, wrong comma placement)",
    "PUNCT:APOST": "missing apostrophe (dont → don't, cant → can't, its=it is → it's, hes → he's)",
    "CONTR": "contraction error (shouldn't of → shouldn't have, would of → would have)",
    "REDUND": "redundancy (return back → return, repeat again → repeat, advance forward → advance)",
}

SYSTEM_FT = "You analyze English errors by French speakers. Identify every USER error. Output valid JSON."


def generate_examples(category, description, count):
    """Ask gpt-4o-mini to generate error examples for a category."""
    prompt = f"""Generate {count} UNIQUE English sentences containing exactly ONE error of type {category}.

Error type: {description}

Context: French speaker learning English. Sentences should be realistic, varied topics, varied difficulty.

RULES:
- Each sentence must contain EXACTLY one {category} error
- Do NOT mix with other error types
- Vary sentence length (short and long)
- Vary topics (daily life, work, travel, school, hobbies)
- Make errors natural (things a French speaker would actually say)

Output as a JSON array. Each item:
{{"sentence": "the erroneous sentence", "original": "the error span", "correction": "the fix", "reasoning": "brief explanation"}}

Output ONLY the JSON array, no other text."""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a linguistics expert generating training data for an error classification model. Output only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.9,
        "max_tokens": 8000,
        "response_format": {"type": "json_object"},
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(LITELLM_URL, json=payload)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        parsed = json.loads(content)
        # Handle both {"examples": [...]} and [...] formats
        if isinstance(parsed, dict):
            for key in ["examples", "sentences", "errors", "data", "items"]:
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


def to_finetune_format(category, example):
    """Convert a generated example to OpenAI fine-tuning JSONL format."""
    sentence = example.get("sentence", "")
    original = example.get("original", "")
    correction = example.get("correction", "")
    reasoning = example.get("reasoning", "")

    if not sentence or not original:
        return None

    user_content = f"Analyze errors:\n--- Turn 1 ---\nUSER: {sentence}\nTEACHER: Good try!"
    assistant_content = json.dumps({
        "errors": [{
            "turn": 1,
            "original": original,
            "correction": correction,
            "codes": [category],
            "reasoning": reasoning
        }]
    })

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_FT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def main():
    total_target = sum(CATEGORY_TARGETS.values())
    print(f"Generating ~{total_target} examples across {len(CATEGORY_TARGETS)} categories\n")

    all_examples = []
    failed_cats = []

    for i, (cat, target) in enumerate(sorted(CATEGORY_TARGETS.items())):
        desc = CATEGORY_DESCRIPTIONS.get(cat, cat)
        print(f"  [{i+1}/{len(CATEGORY_TARGETS)}] {cat} ({target} examples)...", end=" ", flush=True)

        cat_examples = []
        # Generate in batches of 40 — OpenAI paid tier allows 500 RPM
        batch_size = 40
        batches_needed = (target + batch_size - 1) // batch_size

        for b in range(batches_needed):
            remaining = target - len(cat_examples)
            if remaining <= 0:
                break
            n = min(batch_size, remaining)
            try:
                examples = generate_examples(cat, desc, n)
                for ex in examples:
                    ft = to_finetune_format(cat, ex)
                    if ft:
                        cat_examples.append(ft)
                time.sleep(0.1)
            except Exception as e:
                print(f"[batch {b} err: {e}]", end=" ")
                time.sleep(1)

        print(f"→ {len(cat_examples)}/{target}")
        if len(cat_examples) < target * 0.5:
            failed_cats.append((cat, len(cat_examples), target))
        all_examples.extend(cat_examples)

    # Split train/val (90/10)
    import random
    random.seed(42)
    random.shuffle(all_examples)
    split = int(len(all_examples) * 0.9)
    train = all_examples[:split]
    val = all_examples[split:]

    # Write JSONL
    with open("/tmp/train_v3.jsonl", "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")
    with open("/tmp/val_v3.jsonl", "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")

    print(f"\n{'='*50}")
    print(f"Generated: {len(all_examples)} total ({len(train)} train, {len(val)} val)")
    print(f"Written to: /tmp/train_v3.jsonl, /tmp/val_v3.jsonl")

    if failed_cats:
        print(f"\n⚠️ Under-generated categories:")
        for cat, got, target in failed_cats:
            print(f"  {cat}: {got}/{target}")


if __name__ == "__main__":
    main()
