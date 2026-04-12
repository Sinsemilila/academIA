#!/usr/bin/env python3
"""
Phase 1b — Full battery: 3 test cases per category (63 categories = 189 cases)
Each category has: simple error, complex error, multi-error context.
"""

import json
import requests
import time
import subprocess
from collections import defaultdict

ENDPOINT = "http://localhost:8000/internal/analyze-errors"

# ══════════════════════════════════════════════════════════
# 3 CASES PER CATEGORY — 63 × 3 = 189 test cases
# Format: (text, [expected_codes])
# ══════════════════════════════════════════════════════════

TEST_CASES = [
    # ── V:TENSE (3) ──
    ("I have been to Japan last summer", ["V:TENSE"]),
    ("Yesterday I have eaten a pizza with my friends", ["V:TENSE"]),
    ("She has lived in London for two years before moving to Paris", ["V:TENSE"]),

    # ── V:SVA (3) ──
    ("She have a beautiful car in the garage", ["V:SVA"]),
    ("The children plays in the park every afternoon", ["V:SVA"]),
    ("Everyone have their own opinion about this topic", ["V:SVA"]),

    # ── V:FORM (3) ──
    ("I enjoy to swim in the ocean every morning", ["V:FORM"]),
    ("I am looking forward to see you next month", ["V:FORM"]),
    ("He avoided to answer the difficult question clearly", ["V:FORM"]),

    # ── V:MODAL (3) ──
    ("He must to go to the hospital right now", ["V:MODAL"]),
    ("She should goes to the doctor about her back", ["V:MODAL"]),
    ("You can to leave whenever you want today", ["V:MODAL"]),

    # ── V:COND (3) ──
    ("If I would know the answer I would tell you", ["V:COND"]),
    ("If she would have studied harder she would have passed", ["V:COND"]),
    ("If I would be rich I would travel around the world", ["V:COND"]),

    # ── V:ASPECT (3) ──
    ("I am understanding this lesson very well now", ["V:ASPECT"]),
    ("She is knowing the answer to that question", ["V:ASPECT"]),
    ("I am believing that this is the right choice", ["V:ASPECT"]),

    # ── V:AUX (3) ──
    ("You like coffee or you prefer tea today", ["V:AUX"]),
    ("I not understand what you are saying to me", ["V:AUX"]),
    ("She no want to come with us to the party", ["V:AUX"]),

    # ��─ V:INFL (3) ──
    ("I goed to the store and buyed some fresh milk", ["V:INFL"]),
    ("She thinked about it for a very long time", ["V:INFL"]),
    ("The children runned across the garden very fast", ["V:INFL"]),

    # ── V:PASS (3) ──
    ("The book wrote by a famous author last year", ["V:PASS"]),
    ("The cake make by my grandmother was delicious", ["V:PASS"]),
    ("The window was broke during the storm last night", ["V:PASS"]),

    # ── V:EXIST (3) ─��
    ("It has many people in the park on weekends", ["V:EXIST"]),
    ("It exists a solution to this difficult problem", ["V:EXIST"]),
    ("It has a lot of things to do in this city", ["V:EXIST"]),

    # ── V:CHOICE (3) ──
    ("He said me that the meeting was cancelled today", ["V:CHOICE"]),
    ("She made a long travel across South America", ["V:CHOICE"]),
    ("I want to do a photo of the beautiful sunset", ["V:CHOICE"]),

    # ── V:PHRASAL (3) ──
    ("She looks forward the weekend every Friday evening", ["V:PHRASAL"]),
    ("I need to look in the problem more carefully", ["V:PHRASAL"]),
    ("He gave up of smoking after twenty years finally", ["V:PHRASAL"]),

    # ── N:NUM (3) ──
    ("Can you give me some informations about the hotel", ["N:NUM"]),
    ("She bought new furnitures for the living room", ["N:NUM"]),
    ("All the equipments are ready for the big presentation", ["N:NUM"]),

    # ── N:POSS (3) ──
    ("My friend book is on the table over there", ["N:POSS"]),
    ("The student work was really impressive this semester", ["N:POSS"]),
    ("The children room needs to be cleaned this weekend", ["N:POSS"]),

    # ── N:INFL (3) ──
    ("The childs were playing in the garden all morning", ["N:INFL"]),
    ("There were many mouses in the old house basement", ["N:INFL"]),
    ("She has two foots that are different sizes actually", ["N:INFL"]),

    # ── N:CHOICE (3) ──
    ("He has a very good work at a technology company", ["N:CHOICE"]),
    ("I need to find an accommodation for my holiday trip", ["N:CHOICE"]),
    ("She gave me a good counsel about my career path", ["N:CHOICE"]),

    # ── N:COUNT (3) ──
    ("I received many advices from my parents last week", ["N:COUNT"]),
    ("She has a lot of luggages for such a short trip", ["N:COUNT"]),
    ("Can I have an information about the train schedule", ["N:COUNT"]),

    # ── ART (3) ──
    ("I bought car yesterday at the local dealership", ["ART"]),
    ("She is doctor and works at the main hospital", ["ART"]),
    ("He plays guitar in a band every Saturday night", ["ART"]),

    # ── ART:GENERIC (3) ──
    ("The life is beautiful when you travel the world", ["ART:GENERIC"]),
    ("The music makes me happy especially when I am sad", ["ART:GENERIC"]),
    ("The love is the most important thing in the world", ["ART:GENERIC"]),

    # ── DET (3) ─���
    ("I like this books on the shelf over there", ["DET"]),
    ("She bought much apples at the market this morning", ["DET"]),
    ("That ideas are really interesting and innovative", ["DET"]),

    # ── PRON:FORM (3) ���─
    ("Him went to the store to buy some food today", ["PRON:FORM"]),
    ("This gift is for I and my sister from our parents", ["PRON:FORM"]),
    ("Her is the best student in the whole class", ["PRON:FORM"]),

    # ── PRON:CHOICE (3) ──
    ("The man which I saw yesterday was very tall", ["PRON:CHOICE"]),
    ("Everyone should bring their own lunch to school", ["PRON:CHOICE"]),
    ("That is the company who makes the best computers", ["PRON:CHOICE"]),

    # ── PRON:REF (3) ──
    ("John told Bill that he was wrong about the project", ["PRON:REF"]),
    ("When the teacher saw the student he smiled at him", ["PRON:REF"]),
    ("Mary asked Sarah if she could help her with it", ["PRON:REF"]),

    # ── PREP (3) ──
    ("I arrived to London at five in the morning today", ["PREP"]),
    ("We need to discuss about this problem right now", ["PREP"]),
    ("She explained me the rules of the game clearly", ["PREP"]),

    # ── PREP:CALQUE (3) ──
    ("My success depends of how hard I work every day", ["PREP:CALQUE"]),
    ("I am very interested by this new technology here", ["PREP:CALQUE"]),
    ("She is married with a famous musician from Lyon", ["PREP:CALQUE"]),

    # ── ADJ:CHOICE (3) ──
    ("He has a strong fever and needs to see a doctor", ["ADJ:CHOICE"]),
    ("We had a big rain yesterday that flooded the street", ["ADJ:CHOICE"]),
    ("She has a large experience in this field of work", ["ADJ:CHOICE"]),

    # ─��� ADJ:FORM (3) ──
    ("This book is more better than the one I read before", ["ADJ:FORM"]),
    ("She is the most beautifulest woman I have ever seen", ["ADJ:FORM"]),
    ("Your idea is more good than mine for this project", ["ADJ:FORM"]),

    # ��─ ADJ:ORDER (3) ──
    ("I bought a car red yesterday at the local dealer", ["ADJ:ORDER"]),
    ("She wore a dress beautiful to the party last night", ["ADJ:ORDER"]),
    ("They live in a house big with a garden in the back", ["ADJ:ORDER"]),

    # ── ADV:CHOICE (3) ──
    ("She drives very fastly on the highway every day", ["ADV:CHOICE"]),
    ("He worked hardly to finish the project on time", ["ADV:CHOICE"]),
    ("I feel very goodly about the results of the test", ["ADV:CHOICE"]),

    # ─�� ADV:ORDER (3) ──
    ("He drives always too fast on the highway at night", ["ADV:ORDER"]),
    ("She speaks very well English after living abroad", ["ADV:ORDER"]),
    ("I eat usually breakfast at seven in the morning", ["ADV:ORDER"]),

    # ── CONJ (3) ──
    ("I wanted to go to the park and it started raining", ["CONJ"]),
    ("She studied hard and she still failed the exam", ["CONJ"]),
    ("He is tired and he wants to keep working tonight", ["CONJ"]),

    # ── WO (3) ──
    ("I very much like this restaurant near my apartment", ["WO"]),
    ("She gave to her mother a beautiful present today", ["WO"]),
    ("They were enough tired to go home early last night", ["WO"]),

    # ── WO:QUEST (3) ──
    ("Where you go every Saturday morning for shopping", ["WO:QUEST"]),
    ("What time the movie starts at the cinema tonight", ["WO:QUEST"]),
    ("Why you are always late to the meeting on Monday", ["WO:QUEST"]),

    # ── LEX:CHOICE (3) ──
    ("She told me to say her the truth about what happened", ["LEX:CHOICE"]),
    ("I want to win time by taking a shortcut to work", ["LEX:CHOICE"]),
    ("He assisted at the concert in the park last weekend", ["LEX:CHOICE"]),

    # ── LEX:COLLOC (3) ──
    ("I did a big mistake at work and got in trouble", ["LEX:COLLOC"]),
    ("She does a lot of sport every day after school", ["LEX:COLLOC"]),
    ("He did a photo of the sunset from the balcony", ["LEX:COLLOC"]),

    # ── LEX:FALSE (3) ──
    ("I am actually working on a very important project", ["LEX:FALSE"]),
    ("She is very sympathetic and always helps her friends", ["LEX:FALSE"]),
    ("He went to the library to buy a new novel yesterday", ["LEX:FALSE"]),

    # ─�� LEX:CALQUE (3) ��─
    ("I have 25 years and I live in Paris with my family", ["LEX:CALQUE"]),
    ("It makes three years that I work in this company", ["LEX:CALQUE"]),
    ("She opened the light because it was too dark inside", ["LEX:CALQUE"]),

    # ── LEX:IDIOM (3) ──
    ("It is raining cats and mouses outside right now", ["LEX:IDIOM"]),
    ("He kicked the pot last year after a long illness", ["LEX:IDIOM"]),
    ("She let the cat out of the sack about the surprise", ["LEX:IDIOM"]),

    # ── LEX:ARGSTRUCT (3) ���─
    ("He explained me the rules of the game very clearly", ["LEX:ARGSTRUCT"]),
    ("She suggested me to take the earlier train today", ["LEX:ARGSTRUCT"]),
    ("They discussed about the new project for two hours", ["LEX:ARGSTRUCT"]),

    # ── LEX:REGISTER (3) ──
    ("The CEO said the quarterly earnings were gonna drop", ["LEX:REGISTER"]),
    ("Dear Professor I wanna ask about the exam schedule", ["LEX:REGISTER"]),
    ("The board decided to chill on new investments now", ["LEX:REGISTER"]),

    # ── MORPH:DERIV (3) ─���
    ("I am very hapiness about the results of this exam", ["MORPH:DERIV"]),
    ("The beautiness of this landscape is absolutely amazing", ["MORPH:DERIV"]),
    ("She has a lot of knowledgement about this subject", ["MORPH:DERIV"]),

    # ── MORPH:WORDCLASS (3) ──
    ("I am very beauty and she is very intelligence", ["MORPH:WORDCLASS"]),
    ("His success was a result of working very hardly", ["MORPH:WORDCLASS"]),
    ("She gave me a suggest about how to fix the problem", ["MORPH:WORDCLASS"]),

    # ── SENT:RUNON (3) ──
    ("I like cooking I also enjoy reading books every day", ["SENT:RUNON"]),
    ("She went to the store she bought milk she came home", ["SENT:RUNON"]),
    ("It was raining heavily we decided to stay at home", ["SENT:RUNON"]),

    # ── SENT:FRAG (3) ──
    ("Because I was really tired after a long day at work.", ["SENT:FRAG"]),
    ("Although she studied very hard for the final exam.", ["SENT:FRAG"]),
    ("When the sun finally came out after the storm.", ["SENT:FRAG"]),

    # ── SENT:NEG (3) ──
    ("I dont have nothing to say about this difficult topic", ["SENT:NEG", "PUNCT:APOST"]),
    ("She never goes nowhere on the weekends anymore", ["SENT:NEG"]),
    ("He cant find nobody to help him with his homework", ["SENT:NEG", "PUNCT:APOST"]),

    # ── SENT:MOD (3) ──
    ("Walking down the street the trees looked beautiful", ["SENT:MOD"]),
    ("After finishing dinner the TV was turned on by us", ["SENT:MOD"]),
    ("Having studied hard the exam was passed by the student", ["SENT:MOD"]),

    # ── SENT:PARALLEL (3) ──
    ("She likes reading swimming and to cook Italian food", ["SENT:PARALLEL"]),
    ("He enjoys playing guitar to sing and writing lyrics", ["SENT:PARALLEL"]),
    ("I like hiking in the mountains and to swim in lakes", ["SENT:PARALLEL"]),

    # ── SENT:SUBORD (3) ──
    ("I dont know that should I go to the meeting or not", ["SENT:SUBORD"]),
    ("She asked me that where was the nearest bus station", ["SENT:SUBORD"]),
    ("He told me that did he pass the exam successfully", ["SENT:SUBORD"]),

    # ── DISC:TRANS (3) ──
    ("He studied hard. He failed the exam this semester.", ["DISC:TRANS"]),
    ("She loves cooking. She opened a restaurant downtown.", ["DISC:TRANS"]),
    ("It was raining. We went to the park for a picnic.", ["DISC:TRANS"]),

    # ── DISC:COHER (3) ──
    ("I love cats. The weather is nice. She bought a car.", ["DISC:COHER"]),
    ("He went to the store. Mathematics is interesting today.", ["DISC:COHER"]),
    ("She studied French. The dog was sleeping on the mat.", ["DISC:COHER"]),

    # ── DISC:COHES (3) ──
    ("John went to the store. He bought milk. He was happy.", ["DISC:COHES"]),
    ("The teacher gave the test. The students took the test. The teacher graded the test.", ["DISC:COHES"]),
    ("My sister loves dogs. My sister adopted a dog. My sister named my sister dog Rex.", ["DISC:COHES"]),

    # ── DISC:CONNOVER (3) ──
    ("Moreover I think that furthermore the idea is indeed very good", ["DISC:CONNOVER"]),
    ("Furthermore in addition to this moreover we should also consider", ["DISC:CONNOVER"]),
    ("Indeed nevertheless however on the other hand it is furthermore important", ["DISC:CONNOVER"]),

    # ── REG:LEVEL (3) ──
    ("Dear Sir I wanna let you know that the meeting is like postponed", ["REG:LEVEL"]),
    ("Yo professor can you help me with this assignment bro", ["REG:LEVEL"]),
    ("Hey dude thanks for the formal business proposal mate", ["REG:LEVEL"]),

    # ── REG:PRAGMA (3) ──
    ("Give me the salt right now I need it for my food", ["REG:PRAGMA"]),
    ("Tell me the time because I need to know right now", ["REG:PRAGMA"]),
    ("Move your car it is blocking my driveway right now", ["REG:PRAGMA"]),

    # ── SPELL (3) ──
    ("I would definately recommend this restaurant to everyone", ["SPELL"]),
    ("The enviroment needs to be protected by all of us", ["SPELL"]),
    ("She recieved a beautifull gift from her best friend", ["SPELL"]),

    # ��─ SPELL:COGNATE (3) ──
    ("I need more confort in my new appartment downtown", ["SPELL:COGNATE"]),
    ("The gouvernment made an important developement decision", ["SPELL:COGNATE"]),
    ("She works in a differente departement in the company", ["SPELL:COGNATE"]),

    # ── ORTH:CASE (3) ──
    ("i went to the store and bought some fresh milk", ["ORTH:CASE"]),
    ("my brother moved to london last january for his work", ["ORTH:CASE"]),
    ("on saturday we visited the eiffel tower in beautiful paris", ["ORTH:CASE"]),

    # ── ORTH:SPACE (3) ���─
    ("She is a good listener aswell as a great singer", ["ORTH:SPACE"]),
    ("I have alot of work to do before the weekend starts", ["ORTH:SPACE"]),
    ("We should help eachother more often in this team", ["ORTH:SPACE"]),

    # ── PUNCT (3) ──
    ("I went to the store the bank and the pharmacy today", ["PUNCT"]),
    ("She asked me if I was coming but I said no thanks", ["PUNCT"]),
    ("Lets go to the movies tonight it will be great fun", ["PUNCT"]),

    # ── PUNCT:COMMA (3) ──
    ("However I think we should wait before making a decision", ["PUNCT:COMMA"]),
    ("My friend who lives in Paris is visiting us this weekend", ["PUNCT:COMMA"]),
    ("After eating dinner we went for a long walk in the park", ["PUNCT:COMMA"]),

    # ── PUNCT:APOST (3) ��─
    ("I dont think thats a very good idea for our project", ["PUNCT:APOST"]),
    ("Shes been working here for more than five years now", ["PUNCT:APOST"]),
    ("Whos going to drive tonight if youve been drinking", ["PUNCT:APOST"]),

    # ── CONTR (3) ──
    ("I cannot believe that she would not tell us the truth", ["CONTR"]),
    ("He will not come to the party because he is not feeling well", ["CONTR"]),
    ("They are not going to accept this offer I am sure", ["CONTR"]),

    # ── REDUND (3) ──
    ("I need to return back home before it gets too dark", ["REDUND"]),
    ("She repeated the same thing again for the third time", ["REDUND"]),
    ("In my opinion I personally think this is a good idea", ["REDUND"]),
]


def build_transcript(cases, batch_start=0):
    lines = []
    for i, (text, _) in enumerate(cases):
        turn = i + 1
        lines.append(f"--- Turn {turn} ---")
        lines.append(f"USER: {text}")
        lines.append(f"TEACHER: Good try!")
        lines.append("")
    return "\n".join(lines)


def run_test(cases, suffix):
    transcript = build_transcript(cases)
    payload = {"username": "sinse", "session_id": f"full-battery-{suffix}", "transcript": transcript}
    try:
        start = time.time()
        r = requests.post(ENDPOINT, json=payload, timeout=60)
        elapsed = time.time() - start
        r.raise_for_status()
        result = r.json()
        if elapsed > 30:
            print(f"  SLOW ({elapsed:.0f}s)", end="")
        return result
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT (>60s)")
        return None
    except Exception as e:
        print(f"  [ERR] {e}")
        return None


def analyze_results(cases, suffix):
    sql = f"""SELECT turn_number, error_code FROM error_log
              WHERE session_id = 'full-battery-{suffix}'
              ORDER BY turn_number, error_code;"""
    r = subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-t", "-A", "-F", "|||", "-c", sql],
        capture_output=True, text=True
    )
    detected_by_turn = defaultdict(set)
    for line in r.stdout.strip().split("\n"):
        if "|||" in line:
            parts = line.split("|||")
            detected_by_turn[int(parts[0])].add(parts[1])

    per_cat = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    total_tp = total_fn = total_fp = 0
    details = []

    for i, (text, expected_codes) in enumerate(cases):
        turn = i + 1
        detected = detected_by_turn.get(turn, set())
        expected = set(expected_codes)
        tp = detected & expected
        fn = expected - detected
        fp = detected - expected
        total_tp += len(tp)
        total_fn += len(fn)
        total_fp += len(fp)
        for c in tp: per_cat[c]["tp"] += 1
        for c in fn: per_cat[c]["fn"] += 1
        for c in fp: per_cat[c]["fp"] += 1
        if fn or fp:
            d = f"  {'⚠️' if tp else '❌'} T{turn}: \"{text[:60]}...\""
            if fn: d += f"\n     MISSED: {', '.join(sorted(fn))}"
            if fp: d += f"\n     FALSE+: {', '.join(sorted(fp))}"
            details.append(d)

    return per_cat, total_tp, total_fn, total_fp, details


def print_report(per_cat, tp, fn, fp, details):
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0

    print("\n" + "=" * 60)
    print(f"FULL BATTERY — 63 CATEGORIES ({len(TEST_CASES)} cases)")
    print("=" * 60)
    print(f"\nOverall: TP={tp} FN={fn} FP={fp}")
    print(f"Precision: {prec:.0%}  Recall: {rec:.0%}  F1: {f1:.0%}")

    cats = sorted(set(c for d in per_cat.values() for c in []) | set(per_cat.keys()))
    cats = sorted(per_cat.keys())

    print(f"\n{'Category':<18} {'TP':>3} {'FN':>3} {'FP':>3} {'Prec':>6} {'Rec':>6}")
    print("-" * 52)
    for cat in sorted(cats):
        d = per_cat[cat]
        p = d["tp"] / (d["tp"] + d["fp"]) if (d["tp"] + d["fp"]) > 0 else 0
        r = d["tp"] / (d["tp"] + d["fn"]) if (d["tp"] + d["fn"]) > 0 else 0
        icon = "✅" if r >= 0.7 else ("⚠️" if r >= 0.4 else "❌")
        print(f"{icon} {cat:<16} {d['tp']:>3} {d['fn']:>3} {d['fp']:>3} {p:>5.0%} {r:>5.0%}")

    # Summary by domain
    domains = {
        "Verb": ["V:TENSE","V:SVA","V:FORM","V:MODAL","V:COND","V:ASPECT","V:AUX","V:INFL","V:PASS","V:EXIST","V:CHOICE","V:PHRASAL"],
        "Noun": ["N:NUM","N:POSS","N:INFL","N:CHOICE","N:COUNT"],
        "Art/Det": ["ART","ART:GENERIC","DET"],
        "Pronoun": ["PRON:FORM","PRON:CHOICE","PRON:REF"],
        "Prep": ["PREP","PREP:CALQUE"],
        "Adj/Adv": ["ADJ:CHOICE","ADJ:FORM","ADJ:ORDER","ADV:CHOICE","ADV:ORDER"],
        "Sentence": ["SENT:RUNON","SENT:FRAG","SENT:NEG","SENT:MOD","SENT:PARALLEL","SENT:SUBORD","CONJ","WO","WO:QUEST"],
        "Lexical": ["LEX:CHOICE","LEX:COLLOC","LEX:FALSE","LEX:CALQUE","LEX:IDIOM","LEX:ARGSTRUCT","LEX:REGISTER"],
        "Morph": ["MORPH:DERIV","MORPH:WORDCLASS"],
        "Discourse": ["DISC:TRANS","DISC:COHER","DISC:COHES","DISC:CONNOVER"],
        "Register": ["REG:LEVEL","REG:PRAGMA"],
        "Surface": ["SPELL","SPELL:COGNATE","ORTH:CASE","ORTH:SPACE","PUNCT","PUNCT:COMMA","PUNCT:APOST","CONTR","REDUND"],
    }

    print(f"\n{'Domain':<12} {'TP':>4} {'FN':>4} {'FP':>4} {'Prec':>6} {'Rec':>6}")
    print("-" * 44)
    for domain, codes in domains.items():
        dtp = sum(per_cat.get(c, {"tp":0})["tp"] for c in codes)
        dfn = sum(per_cat.get(c, {"fn":0})["fn"] for c in codes)
        dfp = sum(per_cat.get(c, {"fp":0})["fp"] for c in codes)
        dp = dtp / (dtp + dfp) if (dtp + dfp) > 0 else 0
        dr = dtp / (dtp + dfn) if (dtp + dfn) > 0 else 0
        icon = "✅" if dr >= 0.7 else ("⚠️" if dr >= 0.4 else "❌")
        print(f"{icon} {domain:<10} {dtp:>4} {dfn:>4} {dfp:>4} {dp:>5.0%} {dr:>5.0%}")

    if details:
        print(f"\n{'─' * 60}")
        print(f"ISSUES ({len(details)}):")
        for d in details[:40]:  # cap at 40 to avoid flood
            print(d)
        if len(details) > 40:
            print(f"  ... and {len(details) - 40} more issues")


if __name__ == "__main__":
    subprocess.run(
        ["docker", "exec", "postgres-academie", "psql", "-U", "sinse", "-d", "academie_db",
         "-c", "DELETE FROM error_log WHERE session_id LIKE 'full-battery-%';"],
        capture_output=True
    )

    print(f"FULL BATTERY — {len(TEST_CASES)} test cases, 63 categories")
    print(f"Model: gpt-4o-mini (via LiteLLM)\n")

    BATCH_SIZE = 12
    batches = [TEST_CASES[i:i + BATCH_SIZE] for i in range(0, len(TEST_CASES), BATCH_SIZE)]

    total_start = time.time()
    completed = 0
    for bi, batch in enumerate(batches):
        print(f"  Batch {bi+1}/{len(batches)} ({len(batch)} cases)...", end=" ", flush=True)
        result = run_test(batch, f"b{bi}")
        if result:
            print(f"→ {result['errors_detected']} errors (r={result['rule_errors']}, l={result['llm_errors']})")
            completed += 1
        time.sleep(1)

    total_time = time.time() - total_start
    print(f"\nCompleted {completed}/{len(batches)} batches in {total_time:.0f}s")

    all_pc = defaultdict(lambda: {"tp": 0, "fn": 0, "fp": 0})
    all_tp = all_fn = all_fp = 0
    all_det = []
    for bi, batch in enumerate(batches):
        pc, tp, fn, fp, det = analyze_results(batch, f"b{bi}")
        all_tp += tp; all_fn += fn; all_fp += fp
        all_det.extend(det)
        for c, v in pc.items():
            all_pc[c]["tp"] += v["tp"]; all_pc[c]["fn"] += v["fn"]; all_pc[c]["fp"] += v["fp"]

    print_report(all_pc, all_tp, all_fn, all_fp, all_det)
