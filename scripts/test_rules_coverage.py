#!/usr/bin/env python3
"""Test suite for error detection rules coverage A1-C1."""
import sys
sys.path.insert(0, "/opt/academia/webapp/backend")
from academie_core.taxonomy.rules import detect_errors, ERROR_CODE_TO_FAMILY

TESTS = {
    # ── A1: Surface ──
    "i went to the store": "ORTH:CASE",
    "I like english and french": "ORTH:CASE",
    "I have alot of friends": "ORTH:SPACE",
    "I dont know what to say": "PUNCT:APOST",

    # ── A1: SVA ──
    "He go to school every day": "V:SVA",
    "She have a beautiful cat": "V:SVA",
    "It don't work properly": "V:SVA",
    "There is many people in the park": "V:SVA",

    # ── A1-A2: Irregular past ──
    "I goed to the cinema last night": "V:FORM",
    "She taked the wrong bus": "V:FORM",
    "He runned very fast yesterday": "V:FORM",
    "They bringed us some food": "V:FORM",
    "We leaved the party early": "V:FORM",
    "She buyed a new dress": "V:FORM",

    # ── A2: French calques ──
    "I have 25 years old": "LEX:CALQUE",
    "I am agree with your opinion": "LEX:CALQUE",
    "She did a big mistake": "LEX:CALQUE",
    "I depend of my parents": "PREP:CALQUE",
    "I have been living here since 3 years": "PREP:CALQUE",
    "The informations were very useful": "N:COUNT",

    # ── A2: Questions ──
    "Where you go yesterday?": "WO:QUEST",
    "Why you like this movie so much?": "WO:QUEST",

    # ── A2: Modals ──
    "I must to go now": "V:MODAL",
    "She can to speak three languages": "V:MODAL",

    # ── B1: Conditionals ──
    "If I would have known I would have come": "V:COND",
    "If she would be here she could help": "V:COND",
    "If I will be rich I will travel": "V:COND",

    # ── B1: Gerund/Infinitive ──
    "I enjoy to swim every morning": "V:FORM",
    "She avoids to talk about it": "V:FORM",
    "I look forward to hear from you": "V:FORM",
    "I am used to go there every day": "V:FORM",
    "She keeps to make the same mistake": "V:FORM",

    # ── B1: Say/Tell ──
    "He said me to come early": "V:CHOICE",
    "She told that she was tired": "V:CHOICE",

    # ── B1: Suggest ──
    "She suggested me to try the restaurant": "LEX:ARGSTRUCT",

    # ── B2: Double comparative ──
    "She is more taller than her sister": "ADJ:FORM",
    "It is the most easiest thing ever": "ADJ:FORM",

    # ── B2: Despite ──
    "Despite of the rain we went outside": "PREP",

    # ── B1-C1: Make/Do ──
    "I did a terrible mistake": "LEX:COLLOC",
    "She made her homework last night": "LEX:COLLOC",
    "We need to do a decision quickly": "LEX:COLLOC",

    # ── B1: French cognate spelling ──
    "The environnement is very important": "SPELL:COGNATE",
    "She has a great personnality": "SPELL:COGNATE",
}

passed = 0
failed = 0
for sentence, expected in TESTS.items():
    errors = detect_errors(sentence)
    found = any(e.error_code == expected for e in errors)
    if found:
        passed += 1
        match = [e for e in errors if e.error_code == expected][0]
        family = ERROR_CODE_TO_FAMILY.get(match.error_code, "?")
        print(f"  \u2705 [{match.error_code}] {sentence}")
    else:
        failed += 1
        codes = [(e.error_code, e.original_text) for e in errors]
        print(f"  \u274c {sentence} (expected {expected}, got {codes or 'nothing'})")

print(f"\n{'='*50}")
print(f"  Coverage: {passed}/{passed+failed} ({passed/(passed+failed)*100:.0f}%)")
print(f"  Passed: {passed}  Failed: {failed}")
print(f"{'='*50}")

# Summary by category
from collections import Counter
categories = Counter()
for code in TESTS.values():
    categories[code] += 1
print(f"\n  Categories tested: {len(categories)}")
for code, count in categories.most_common():
    family = ERROR_CODE_TO_FAMILY.get(code, "?")
    print(f"    {code} ({family}): {count} tests")
