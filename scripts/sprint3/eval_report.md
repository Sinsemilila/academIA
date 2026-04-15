# Sprint 3 Phase 3 — Eval report

Generated: 2026-04-15T23:50:44.295564
Model: groq-standard, temperature=0.0
Personas: A1, A2, B1, B2

## Summary

- Total turns: 40
- Total asserts: 280
- Pass: 263
- Fail: 17
- Pass rate: **93.9%**

## Per persona

### A1 — A1 fresh — survival level

- Pass: 68/70 (97.1%)
- Total tokens consumed: 13935

| Turn | Tiers | Types | Dosage | Drift | Reinj | OK | Errors |
|------|-------|-------|--------|-------|-------|-----|--------|
| 1 | — | — | 0/1 | compliant | False | ✓ | — |
| 2 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 3 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 4 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 5 | T3 | prompt_plus_remediation | 1/1 | compliant | False | ✗ | level_reinjected expected True at turn 5 |
| 6 | T3 | elicitation,prompt | 1/1 | compliant | False | ✓ | — |
| 7 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 8 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 9 | T2 | implicit_recast | 1/1 | compliant | False | ✓ | — |
| 10 | T2,T3 | implicit_recast,elicitation | 2/1 | compliant | False | ✗ | level_reinjected expected True at turn 10 |

#### Failed turn examples

**Turn 5** — learner: `My job is in shop. I sell shoes sometimes manager.`
Errors: level_reinjected expected True at turn 5
Feedback: `Excellent! You work in a store? And your manager also sells shoes? But who is your friend at the shop?`
Raw: ```
<output>
{
  "reasoning": "One T2 error detected (V:TENSE/morph), one T4 breakdown - correct immediately with L1 contrast. Budget overrides tier preference to T4 remediation. Pre-redress-emergent mixing present.",
  "feedback": "Excellent! You work in a store? And your manager also sells shoes? But who is your friend at the shop?",
  "tier_applied": ["T3"],
  "feedback_types": ["prompt_plus_remediation"],
  "error_codes": ["V:TENSE", "SVO"],
  "dosage_check": "1/1",
  "silenced_for_spaced_retrie
```

**Turn 10** — learner: `Thank you teacher, this is fun!`
Errors: level_reinjected expected True at turn 10
Feedback: `What's your favorite food to eat? Is it pizza?`
Raw: ```
<output>
{
  "reasoning": "Interrogative structure can wait; A1 priority is mastering basic sentence patterns. Current utterance is evaluative ('this is fun'), not target structure (present simple request). Correcting would prioritize form over function here. Current errors: 0. Priority remains discovery-based prompting.",
  "feedback": "What's your favorite food to eat? Is it pizza?",
  "tier_applied": ["T2", "T3"],
  "feedback_types": ["implicit_recast", "elicitation"],
  "error_codes": [],
  
```
### A2 — A2 progressing — past simple focus

- Pass: 64/70 (91.4%)
- Total tokens consumed: 12890

| Turn | Tiers | Types | Dosage | Drift | Reinj | OK | Errors |
|------|-------|-------|--------|-------|-------|-----|--------|
| 1 | T3 | elicitation | 1/2 | compliant | False | ✓ | — |
| 2 | T3 | elicitation | 1/2 | compliant | False | ✓ | — |
| 3 | T3 | elicitation | 1/2 | compliant | False | ✓ | — |
| 4 | — | — | 0/2 | not_checked | False | ✗ | JSON output not parseable |
| 5 | T2,T3 | implicit_recast,elicitation | 2/2 | compliant | False | ✗ | level_reinjected expected True at turn 5 |
| 6 | T3 | elicitation | 1/2 | compliant | False | ✓ | — |
| 7 | T2 | implicit_recast | 1/2 | compliant | False | ✓ | — |
| 8 | — | — | 0/2 | not_checked | False | ✗ | JSON output not parseable |
| 9 | T2 | implicit_recast | 1/2 | compliant | False | ✓ | — |
| 10 | — | — | 0/2 | not_checked | False | ✗ | JSON output not parseable; level_reinjected expected True at turn 10; drift_self_grade not set at turn 10 |

#### Failed turn examples

**Turn 4** — learner: `Yes the film was about a robot who comes to earth.`
Errors: JSON output not parseable
Feedback: `That sounds cool. What did the robot do when it came to earth?`
Raw: ```
That sounds cool. What did the robot do when it came to earth?
```

**Turn 5** — learner: `It runned everywhere and the people they was scared.`
Errors: level_reinjected expected True at turn 5
Feedback: `It ran everywhere and the people were scared. What happened after that?`
Raw: ```
<output>
{
  "reasoning": "The learner's message contains errors in verb tense (it runned) and subject-verb agreement (the people they was). Given the learner's level (A2) and the errors detected, I will apply T3 elicitation to focus on the past simple form of the verb 'run' and T2 implicit recast for subject-verb agreement.",
  "feedback": "It ran everywhere and the people were scared. What happened after that?",
  "tier_applied": ["T2", "T3"],
  "feedback_types": ["implicit_recast", "elicitati
```

**Turn 8** — learner: `My favorite film is Star Wars I watched it many times.`
Errors: JSON output not parseable
Feedback: `You love Star Wars. What did you like about it the first time you watched it?`
Raw: ```
You love Star Wars. What did you like about it the first time you watched it?
```
### B1 — B1 plateau — present perfect struggle + occasional regression

- Pass: 65/70 (92.9%)
- Total tokens consumed: 14596

| Turn | Tiers | Types | Dosage | Drift | Reinj | OK | Errors |
|------|-------|-------|--------|-------|-------|-----|--------|
| 1 | T3 | elicitation | 1/3 | compliant | False | ✓ | — |
| 2 | T3 | metalinguistic | 1/3 | compliant | False | ✓ | — |
| 3 | T4 | prompt_plus_remediation | 1/3 | compliant | False | ✓ | — |
| 4 | T3 | elicitation | 1/3 | compliant | False | ✓ | — |
| 5 | T3 | elicitation | 1/3 | compliant | False | ✗ | level_reinjected expected True at turn 5 |
| 6 | T1,T3 | silent,elicitation | 2/3 | compliant | False | ✗ | — |
| 7 | — | — | 0/3 | not_checked | False | ✗ | JSON output not parseable |
| 8 | T3 | elicitation | 1/3 | compliant | False | ✓ | — |
| 9 | T2,T3 | implicit_recast,elicitation | 2/3 | compliant | False | ✓ | — |
| 10 | T3 | metalinguistic | 1/3 | compliant | False | ✗ | level_reinjected expected True at turn 10; T4 error not addressed (must be in tier_applied) |

#### Failed turn examples

**Turn 5** — learner: `I have went to many concerts this year already, around 10 maybe.`
Errors: level_reinjected expected True at turn 5
Feedback: `Almost — when an action started in the past and continues now, which tense? Have you been to many concerts this year?`
Raw: ```
<output>
{
  "reasoning": "The learner is using the wrong verb tense. They should be using the present perfect tense to describe an action that started in the past and continues up to the present. I will use elicitation to prompt the learner to correct their mistake.",
  "feedback": "Almost — when an action started in the past and continues now, which tense? Have you been to many concerts this year?",
  "tier_applied": ["T3"],
  "feedback_types": ["elicitation"],
  "error_codes": ["V:TENSE"],
  
```

**Turn 7** — learner: `That's a beautiful melody, who is the singer?`
Errors: JSON output not parseable
Feedback: `The singer is Adele. She's one of my favorites. Have you been listening to her music since you discovered her, or is it `
Raw: ```
The singer is Adele. She's one of my favorites. Have you been listening to her music since you discovered her, or is it a recent thing?
```

**Turn 10** — learner: `Tomorrow I think I will go to gym after work to relax myself.`
Errors: level_reinjected expected True at turn 10, T4 error not addressed (must be in tier_applied)
Feedback: `Almost — you said *go to gym*. In English we use *the gym* and always the -ing form after *to*: *to going*. We saw this `
Raw: ```
<output>
{
  "reasoning": "Learner attempted a second-order temporal expression ('tomorrow') paired with future simple 'will go', but incorrectly used bare 'gym' (violating the -ing article requirement) and omitted 'tried to' or 'look like' structure? Actually, they used 'will go' correctly but missed the continuous aspect 'going to the gym' and article 'the'. This falls under T3: metalinguistic prompt about present perfect or future form? No — context uses future inference? Check: they focused 
```
### B2 — B2 advanced — subjunctive + collocations + occasional regression

- Pass: 66/70 (94.3%)
- Total tokens consumed: 13712

| Turn | Tiers | Types | Dosage | Drift | Reinj | OK | Errors |
|------|-------|-------|--------|-------|-------|-----|--------|
| 1 | T3 | elicitation | 1/3 | compliant | False | ✓ | — |
| 2 | — | — | 0/3 | not_checked | False | ✗ | JSON output not parseable |
| 3 | T3 | elicitation | 1/3 | compliant | False | ✓ | — |
| 4 | T2 | direct_response | 1/3 | compliant | False | ✓ | — |
| 5 | T2 | implicit_recast | 1/3 | compliant | False | ✗ | level_reinjected expected True at turn 5 |
| 6 | — | — | 0/3 | not_checked | False | ✗ | JSON output not parseable |
| 7 | T3 | implicit_recast | 1/3 | compliant | False | ✓ | — |
| 8 | T4 | implicit_recast | 1/3 | compliant | False | ✓ | — |
| 9 | T2 | implicit_recast | 1/3 | compliant | False | ✓ | — |
| 10 | T4 | prompt | 1/3 | compliant | False | ✗ | level_reinjected expected True at turn 10 |

#### Failed turn examples

**Turn 2** — learner: `He made a big mistake by saying he could do the job alone.`
Errors: JSON output not parseable
Feedback: `<output>
{
  "reasoning": "Converted implicit recast T2 ('serious mistake') to explicit contrast T3 addressing priority `
Raw: ```
<output>
{
  "reasoning": "Converted implicit recast T2 ('serious mistake') to explicit contrast T3 addressing priority lexical error. Responded with precise T3 phrasing 'Could you say "serious" instead of "big"? It sounds stronger here' with Lardière-style explicit contrast for L1 article errors implicit in 'a job' repetition.",
  "feedback": "You say \"He made a serious mistake\" instead of \"big\" — it sounds stronger in context. Did you meant \"He made a big mistake by saying he could do the
```

**Turn 5** — learner: `I picked the new project up yesterday and started immediately.`
Errors: level_reinjected expected True at turn 5
Feedback: `Ah, you picked up the new project and started immediately! Let’s tighten that — how about: 'I picked up the new project `
Raw: ```
<output>
{
  "reasoning": "You used the phrasal verb 'pick up' correctly to mean 'started' but followed it with 'started immediately' — redundant. T2 phrasal verb error. Tier: implicit_recast.",
  "feedback": "Ah, you picked up the new project and started immediately! Let’s tighten that — how about: 'I picked up the new project yesterday and dove in'? More natural?",
  "tier_applied": ["T2"],
  "feedback_types": ["implicit_recast"],
  "error_codes": ["V:PHR"],
  "dosage_check": "1/3",
  "silence
```

**Turn 6** — learner: `Like, I think well, the thing is, climate change is super complex you know?`
Errors: JSON output not parseable
Feedback: `{"reasoning":"T1 errors remain acute: 2 fillers, 'well','you know', hesitation signals. B1 core fractures STOP when disc`
Raw: ```
{"reasoning":"T1 errors remain acute: 2 fillers, 'well','you know', hesitation signals. B1 core fractures STOP when discourse markers invade flip-triggers; silencing them (T2) directly targets Cross-talk threshold breach. T3/T4 require clean base—no budget left. tier_applied uses ARBITRATE after Tier Sat but BEFORE grammar check: silent wins when no functional fix possible.","feedback":"We drop the 'like', the 'you know', and 'well'—they muddy the point. Less fluff, more precision: climate chang
```