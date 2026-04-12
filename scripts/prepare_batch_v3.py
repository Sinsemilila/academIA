#!/usr/bin/env python3
"""
Prepare OpenAI Batch API JSONL for generating ~5000 training examples.
One request per category batch → ~120 requests total.
Output: /tmp/batch_v3_requests.jsonl
"""

import json

MODEL = "gpt-4o-mini"

# Weighted targets by v2 recall performance
CATEGORY_TARGETS = {
    # 100% recall in v2 — 60 examples
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
    # <70% recall — 100 examples
    "ART": 100, "ART:GENERIC": 100, "LEX:CHOICE": 100, "LEX:CALQUE": 100,
    "LEX:ARGSTRUCT": 100, "N:CHOICE": 100, "PRON:CHOICE": 100,
    "PREP": 100, "V:CHOICE": 100, "WO": 100, "MORPH:WORDCLASS": 100,
    "PUNCT:APOST": 100,
    # 0% recall — 120 examples
    "N:NUM": 120, "ADV:ORDER": 120, "CONJ": 120, "CONTR": 120,
    "DISC:COHES": 120, "DISC:CONNOVER": 120, "LEX:REGISTER": 120,
    "PRON:REF": 120, "PUNCT": 120,
}

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
    "N:NUM": "regular singular/plural error (many student → students, two dog → dogs). NOT uncountable nouns — those are N:COUNT.",
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


def make_batch_request(custom_id, category, description, count):
    """Create one Batch API request line."""
    prompt = f"""Generate {count} UNIQUE English sentences containing exactly ONE error of type {category}.

Error type: {description}

Context: French speaker learning English. Sentences should be realistic, varied topics, varied difficulty.

RULES:
- Each sentence must contain EXACTLY one {category} error
- Do NOT mix with other error types
- Vary sentence length (short and long)
- Vary topics (daily life, work, travel, school, hobbies)
- Make errors natural (things a French speaker would actually say)

Output as a JSON object with key "examples". Each item:
{{"sentence": "the erroneous sentence", "original": "the error span", "correction": "the fix", "reasoning": "brief explanation"}}"""

    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a linguistics expert generating training data for an error classification model. Output only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.9,
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},
        }
    }


def main():
    requests = []
    batch_size = 40

    for cat, target in sorted(CATEGORY_TARGETS.items()):
        desc = CATEGORY_DESCRIPTIONS.get(cat, cat)
        batches_needed = (target + batch_size - 1) // batch_size

        for b in range(batches_needed):
            remaining = target - (b * batch_size)
            n = min(batch_size, remaining)
            custom_id = f"{cat}_batch{b}_{n}ex"
            requests.append(make_batch_request(custom_id, cat, desc, n))

    out_path = "/tmp/batch_v3_requests.jsonl"
    with open(out_path, "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    total_target = sum(CATEGORY_TARGETS.values())
    print(f"Prepared {len(requests)} batch requests for ~{total_target} examples")
    print(f"Written to: {out_path}")
    print(f"File size: {len(open(out_path).read()) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
