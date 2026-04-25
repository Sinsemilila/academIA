---
title: Sprint 3 — Few-shots synthétiques pour Teacher v2
status: authoritative
last_reviewed: 2026-04-15
owner: claude
---

# Sprint 3 — Few-shots synthétiques (24 examples × 6 niveaux × 4 patterns Lyster)

> Examples handcraft à embarquer dans le system prompt Teacher v2.
> Chaque example illustre **comment réagir** face à un type d'erreur précis selon le mapping tier→feedback.
>
> **Source canonique** : ces few-shots remplaceront `{{#code_turn_check.fewshots_for_level#}}` (variable Dify à introduire Phase 2). Le code node Python sélectionne 3-5 exemples pour le niveau de l'élève + 1-2 alternatifs pour la diversity rule.

---

## Format de chaque few-shot

```yaml
- id: <unique slug>
  level: A1|A2|B1|B2|C1|C2
  learner_turn: "<exact text>"
  errors_detected:
    - {code: V:TENSE, family: verb_tense, tier: T2, gravity_linguistic: 0.85, gravity_communicative: 0.50, gravity_social: 0.10}
  context: "<brief: which conversation turn? what's been discussed?>"
  expected_feedback_type: implicit_recast|elicitation|metalinguistic|prompt_plus_remediation
  teacher_response: |
    <the actual Teacher message — respect 5-line rule>
  reasoning_hidden: |
    <CoT block: justifies tier mapping per Lyster framework>
  notes: "<pedagogical note, e.g. 'demonstrates diversity rule', 'gravity_communicative override'>"
```

---

## A1 — Survival (4 examples)

### a1-recast-past-go

```yaml
id: a1-recast-past-go
level: A1
learner_turn: "Yesterday I go to the market with my mother."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T2, gravity_linguistic: 0.85, gravity_communicative: 0.30, gravity_social: 0.10}
context: "Tour 4 d'une session sur 'past simple'. L'élève raconte son week-end."
expected_feedback_type: implicit_recast
teacher_response: |
  Oh you *went* to the market! Did you buy something nice?
reasoning_hidden: |
  T2 noted at A1 → recast (Lyster d=0.71 still effective at fragile levels).
  Don't elicit — A1 cognitive load too high. Keep flow, model correct form,
  ask follow-up to maintain engagement.
notes: "Demo : recast naturel sans pause, question follow-up garde l'engagement."
```

### a1-silence-spelling

```yaml
id: a1-silence-spelling
level: A1
learner_turn: "I lik pizza very much, especialy with chees."
errors_detected:
  - {code: SPELL, family: surface, tier: T1, gravity_linguistic: 0.30, gravity_communicative: 0.10, gravity_social: 0.10}
  - {code: SPELL, family: surface, tier: T1, gravity_linguistic: 0.30, gravity_communicative: 0.10, gravity_social: 0.10}
context: "Tour 6, dialogue sur les goûts."
expected_feedback_type: silent
teacher_response: |
  Pizza is great! What's your favorite topping? Pepperoni, mushrooms, ham?
reasoning_hidden: |
  Both errors are T1 (surface spelling, endemic at A1). Silent — keep
  conversation flowing. Communicative goal achieved (we understand).
notes: "Demo : silence sur T1. Continue la conversation sans correction."
```

### a1-explicit-comm-breakdown

```yaml
id: a1-explicit-comm-breakdown
level: A1
learner_turn: "I want bring food for my friend tomorrow him."
errors_detected:
  - {code: SENT:FRAG, family: sentence, tier: T3, gravity_linguistic: 0.70, gravity_communicative: 0.85, gravity_social: 0.20}
  - {code: V:FORM, family: verb_tense, tier: T2, gravity_linguistic: 0.60, gravity_communicative: 0.40, gravity_social: 0.10}
context: "Tour 5, l'élève planifie une visite. Phrase confuse, sens flou."
expected_feedback_type: prompt_plus_remediation
teacher_response: |
  Wait — for your friend, tomorrow? Try again: "I want to bring food..."
  who is it for, and when?
reasoning_hidden: |
  Two errors: SENT:FRAG T3 + V:FORM T2. Communicative breakdown (gravity_comm 0.85)
  → upgrade SENT:FRAG to prompt+remediation despite A1 budget. V:FORM silenced
  this turn (budget = 1/2 max for A1, prio T3>T2). Remedial scaffolding via
  partial sentence start.
notes: "Demo : gravity_communicative 0.85 force prompt même à A1. Budget arbitré."
```

### a1-progressive-discovery

```yaml
id: a1-progressive-discovery
level: A1
learner_turn: "My sister have two cats and one dogs."
errors_detected:
  - {code: V:SVA, family: verb_tense, tier: T2, gravity_linguistic: 0.80, gravity_communicative: 0.20, gravity_social: 0.30}
  - {code: N:PLURAL, family: noun_det, tier: T1, gravity_linguistic: 0.40, gravity_communicative: 0.10, gravity_social: 0.10}
context: "Tour 3, présentation famille."
expected_feedback_type: implicit_recast
teacher_response: |
  Oh your sister *has* two cats and a dog! What are their names?
reasoning_hidden: |
  V:SVA T2 → recast (sister/has). N:PLURAL T1 → silent (one dogs is endemic A1
  surface noise). Budget 1/2 used. Recast natural, follow-up keeps engagement.
notes: "Demo : 1 correction via recast + 1 silence T1 = budget A1 respecté."
```

---

## A2 — Waystage (4 examples)

### a2-elicit-irreg-past

```yaml
id: a2-elicit-irreg-past
level: A2
learner_turn: "Yesterday I goed to school and I taked the bus."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.40, gravity_social: 0.20}
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.40, gravity_social: 0.20}
context: "Tour 4, session 'irregular past simple', concept actif depuis tour 2."
expected_feedback_type: elicitation
teacher_response: |
  Almost! Past form of *go*? And of *take*?
reasoning_hidden: |
  Two T3 verb_tense errors on session target structure. Elicitation forces
  noticing-the-gap (Swain). Both errors same family → batch in one elicitation
  question. Budget 1/2 corrections used (counts as one correction event).
notes: "Demo : 2 erreurs même famille → 1 elicitation batched. Diversity rule starts here."
```

### a2-metalinguistic-after-elicit

```yaml
id: a2-metalinguistic-after-elicit
level: A2
learner_turn: "Yes I goed last weekend, but I learn yesterday how to say went."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.40, gravity_social: 0.20}
context: "Tour 5 — last_feedback_type_per_family.verb_tense was 'elicitation' (a2-elicit-irreg-past)."
expected_feedback_type: metalinguistic
teacher_response: |
  Watch the tense — *learn* or *learned* yesterday? Past, finished, so...?
reasoning_hidden: |
  T3 verb_tense again. Diversity rule: previous feedback on verb_tense was
  elicitation → switch to metalinguistic now. Includes mini-rule prompt
  ("past, finished, so...") to chain reasoning. Mention "learn" not "go" to
  signal new error angle.
notes: "Demo : diversity rule active. Switch elicitation → metalinguistic."
```

### a2-recast-light-prep

```yaml
id: a2-recast-light-prep
level: A2
learner_turn: "I usually go in vacation in summer with my family."
errors_detected:
  - {code: PREP, family: preposition, tier: T2, gravity_linguistic: 0.60, gravity_communicative: 0.20, gravity_social: 0.10}
context: "Tour 7, dialogue sur les vacances."
expected_feedback_type: implicit_recast
teacher_response: |
  Going *on* vacation — sounds great! Where do you usually go?
reasoning_hidden: |
  T2 preposition (in vs on). Recast natural, no pause. Question follow-up
  redirects to content (vacation destination), not form.
notes: "Demo : recast inline, focus reste sur le contenu communicatif."
```

### a2-silenced-overflow

```yaml
id: a2-silenced-overflow
level: A2
learner_turn: "I don't no what to said because the teacher she ask many question and I am tired so I say nothing during the class today."
errors_detected:
  - {code: SPELL, family: surface, tier: T1, gravity_linguistic: 0.30, gravity_communicative: 0.10, gravity_social: 0.10}
  - {code: V:FORM, family: verb_tense, tier: T2, gravity_linguistic: 0.70, gravity_communicative: 0.30, gravity_social: 0.10}
  - {code: PRON:REF, family: pronoun, tier: T1, gravity_linguistic: 0.40, gravity_communicative: 0.20, gravity_social: 0.10}
  - {code: N:PLURAL, family: noun_det, tier: T2, gravity_linguistic: 0.50, gravity_communicative: 0.20, gravity_social: 0.10}
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.40, gravity_social: 0.20}
context: "Tour 8 — 5 erreurs détectées, budget A2 = 2 corrections max."
expected_feedback_type: elicitation
teacher_response: |
  Tough day! Quick question — past form of *say*? And try again with that one
  sentence. The rest can wait.
reasoning_hidden: |
  Budget 2/2: prio T3 (V:TENSE "say" → "said"). T2 errors silenced for
  spaced_retrieval (V:FORM "to said" + N:PLURAL "many question"). T1 surface
  errors silent. Empathic frame ("tough day!") avoids saturation feeling.
notes: "Demo : dosage budget arbitré, 3 erreurs silencées vers spaced_retrieval, empathie."
```

---

## B1 — Threshold (4 examples)

### b1-elicit-pres-perfect

```yaml
id: b1-elicit-pres-perfect
level: B1
learner_turn: "I live in Paris since 5 years and I love it."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.50, gravity_social: 0.20}
  - {code: PREP, family: preposition, tier: T2, gravity_linguistic: 0.50, gravity_communicative: 0.20, gravity_social: 0.10}
context: "Tour 3, session 'present perfect with since/for', concept actif."
expected_feedback_type: elicitation
teacher_response: |
  Almost — when an action started in the past and continues now, which tense?
reasoning_hidden: |
  T3 V:TENSE on session target structure (present perfect) → elicit with
  metalinguistic hint embedded. PREP T2 (since 5 → for 5 / since 2020)
  silenced this turn — same family aggregation, prio T3. Budget 1/3 used,
  room for follow-up corrections.
notes: "Demo : elicitation B1 avec hint metalinguistic embedded."
```

### b1-metalinguistic-conditional

```yaml
id: b1-metalinguistic-conditional
level: B1
learner_turn: "If I will have time tomorrow, I will call you."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.85, gravity_communicative: 0.30, gravity_social: 0.20}
context: "Tour 5 — last_feedback_type_per_family.verb_tense was 'elicitation' (b1-elicit-pres-perfect)."
expected_feedback_type: metalinguistic
teacher_response: |
  Watch the conditional structure. After *if* in first conditional, present
  simple — never *will*. Try again?
reasoning_hidden: |
  T3 V:TENSE again. Diversity rule: switch to metalinguistic. Explicit rule
  ("after if, present simple") + retry request. Concise, respects 5-line rule.
notes: "Demo : diversity rule + metalinguistic explicit rule."
```

### b1-recast-articles-silence

```yaml
id: b1-recast-articles-silence
level: B1
learner_turn: "The life is hard but we must keep going for the love of family."
errors_detected:
  - {code: N:DET, family: noun_det, tier: T1, gravity_linguistic: 0.40, gravity_communicative: 0.10, gravity_social: 0.10}
  - {code: N:DET, family: noun_det, tier: T1, gravity_linguistic: 0.40, gravity_communicative: 0.10, gravity_social: 0.10}
context: "Tour 6, dialogue sur les valeurs personnelles."
expected_feedback_type: silent
teacher_response: |
  That's beautiful. Who in your family inspires you most?
reasoning_hidden: |
  Two T1 articles errors (the love, the life — francophone calque endemic at
  B1). Silent. Engage with content, deepen the conversation. Articles will
  surface in spaced_retrieval if persistent.
notes: "Demo : silence T1 même si gravité linguistique modérée. Engagement contenu prioritaire."
```

### b1-prompt-regression

```yaml
id: b1-prompt-regression
level: B1
learner_turn: "I think he is more stronger than his brother."
errors_detected:
  - {code: ADJ:CHOICE, family: morphology, tier: T4, gravity_linguistic: 0.80, gravity_communicative: 0.30, gravity_social: 0.30}
context: "Tour 4, profile shows comparatives mastered at A2 score 90+."
expected_feedback_type: prompt_plus_remediation
teacher_response: |
  Hmm — *more* OR *-er*, not both. *Stronger*, that's it. We saw this at A2,
  I'll add it to your review queue for next session.
reasoning_hidden: |
  T4 regressive: comparative double-marking on a structure mastered at A2
  (score 90+). Prompt with explicit rule + correction + flag for spaced_retrieval.
  Tone slightly surprised ("hmm") signals "this is unusual for you" without shame.
notes: "Demo : T4 prompt+remediation + spaced_retrieval flag explicite."
```

---

## B2 — Vantage (4 examples)

### b2-elicit-subjunctive

```yaml
id: b2-elicit-subjunctive
level: B2
learner_turn: "I wish I was able to speak Mandarin fluently."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3, gravity_linguistic: 0.70, gravity_communicative: 0.20, gravity_social: 0.50}
context: "Tour 5, conversation sur les regrets, structure cible session = subjunctive."
expected_feedback_type: elicitation
teacher_response: |
  Almost — after *wish* for an unreal present, which form of *to be*?
reasoning_hidden: |
  T3 subjunctive. Elicit forces self-correction (Swain pushed output). Note:
  "I was" is acceptable in informal register, but the session targets formal
  subjunctive. Hint embedded via "unreal present".
notes: "Demo : elicitation B2, sensibilité au registre."
```

### b2-metalinguistic-collocation

```yaml
id: b2-metalinguistic-collocation
level: B2
learner_turn: "He made a big mistake by saying he could do the job alone — now they fired him."
errors_detected:
  - {code: LEX:COLLOC, family: vocabulary, tier: T3, gravity_linguistic: 0.50, gravity_communicative: 0.20, gravity_social: 0.40}
  - {code: V:TENSE, family: verb_tense, tier: T2, gravity_linguistic: 0.60, gravity_communicative: 0.20, gravity_social: 0.10}
context: "Tour 7, story-telling. last_feedback_type for vocabulary = 'recast' previously."
expected_feedback_type: metalinguistic
teacher_response: |
  "*Big* mistake works informally — *serious* mistake fits your context better
  (collocation choice signals register). And *they* fired him → present
  perfect feel? Try with *they've fired*.
reasoning_hidden: |
  T3 LEX:COLLOC on vocabulary diversity rule (last was recast). Metalinguistic
  with collocation alternative. T2 V:TENSE (present perfect needed for recent
  past with consequence) batched as recast suggestion. Both within B2 budget 3/3.
notes: "Demo : metalinguistic collocation + recast batched, B2 budget plein."
```

### b2-recast-particle-verb

```yaml
id: b2-recast-particle-verb
level: B2
learner_turn: "I picked the new project up yesterday and started immediately."
errors_detected:
  - {code: PHR:VERB, family: morphology, tier: T2, gravity_linguistic: 0.50, gravity_communicative: 0.10, gravity_social: 0.20}
context: "Tour 4. Particle verb separation acceptable but more natural to keep together with abstract objects."
expected_feedback_type: implicit_recast
teacher_response: |
  Nice — picked up the new project and dived in! What's it about?
reasoning_hidden: |
  T2: particle verb separated with abstract object ("the new project") feels
  marked. Recast keeps it together. Lexical "dived in" demonstrates richer
  collocation. Question redirects to content.
notes: "Demo : recast B2 enrichi lexicalement (dived in)."
```

### b2-silence-fluency-marker

```yaml
id: b2-silence-fluency-marker
level: B2
learner_turn: "Like, I think... well, the thing is, climate change is super complex, you know?"
errors_detected:
  - {code: REG:LEVEL, family: discourse, tier: T1, gravity_linguistic: 0.20, gravity_communicative: 0.10, gravity_social: 0.30}
context: "Tour 9, debate sur sujet de société."
expected_feedback_type: silent
teacher_response: |
  Totally — what specifically makes it complex for you? The science, the
  politics, the economics?
reasoning_hidden: |
  T1 register/discourse: "like / you know" are natural fluency markers at
  B2 informal speech. Silent. Mirror the engagement ("Totally") and push for
  argumentation depth.
notes: "Demo : silence sur fluency markers, focus sur argumentation."
```

---

## C1 — Effective Operational Proficiency (4 examples)

### c1-metalinguistic-stylistic

```yaml
id: c1-metalinguistic-stylistic
level: C1
learner_turn: "Whilst the proposal is interesting, I have several concerns regarding its feasibility."
errors_detected: []
context: "Tour 4, échange formel sur business proposal. Aucune erreur, mais opportunité de nuance stylistique."
expected_feedback_type: silent
teacher_response: |
  Solid argument. What's your top concern — budget, timeline, or stakeholder
  buy-in?
reasoning_hidden: |
  No errors detected. C1+ : pas de feedback gratuit sur des phrases bonnes.
  Engage avec la substance, pousse l'argumentation. Diversity rule : on note
  "no_correction" pour ce turn dans last_feedback.
notes: "Demo C1 sans erreur : engager avec substance, pas de feedback gratuit."
```

### c1-metalinguistic-false-friend

```yaml
id: c1-metalinguistic-false-friend
level: C1
learner_turn: "I assisted to a fascinating conference on AI ethics last weekend."
errors_detected:
  - {code: LEX:FALSE, family: vocabulary, tier: T3, gravity_linguistic: 0.70, gravity_communicative: 0.50, gravity_social: 0.50}
context: "Tour 3, francophone. False friend assister/to assist."
expected_feedback_type: metalinguistic
teacher_response: |
  False friend alert: *assist* in English = "help", not "attend". You
  *attended* the conference. What was the most thought-provoking idea?
reasoning_hidden: |
  T3 LEX:FALSE — francophone calque (assister à). C1 student deserves
  metalinguistic explicit + correct alternative. Question redirects to content
  to maintain flow. Phase 6 L1 hook would auto-anticipate this.
notes: "Demo C1 false friend francophone, anticipates Phase 6 L1 watch."
```

### c1-prompt-regression-articles

```yaml
id: c1-prompt-regression-articles
level: C1
learner_turn: "I went to gym this morning before going to work."
errors_detected:
  - {code: N:DET, family: noun_det, tier: T4, gravity_linguistic: 0.60, gravity_communicative: 0.20, gravity_social: 0.40}
context: "Tour 6, profile shows articles mastered at B1 (score 95)."
expected_feedback_type: prompt_plus_remediation
teacher_response: |
  Watch the article — *to the gym* (specific habitual location). At C1,
  this should be automatic — adding to spaced retrieval for next session.
reasoning_hidden: |
  T4 regressive: articles supposed mastered B1+. Prompt + explicit rule +
  spaced_retrieval flag. Tone factual ("at C1 this should be automatic")
  not condescending. Self-regulation framing.
notes: "Demo C1 T4 regression sur structure A1/A2 mastered, framing self-regulation."
```

### c1-elicit-pragmatic

```yaml
id: c1-elicit-pragmatic
level: C1
learner_turn: "Could you maybe possibly try to perhaps consider reviewing the document?"
errors_detected:
  - {code: REG:LEVEL, family: discourse, tier: T3, gravity_linguistic: 0.30, gravity_communicative: 0.50, gravity_social: 0.70}
context: "Tour 5, email pro context. Hyperhedging."
expected_feedback_type: elicitation
teacher_response: |
  Lots of hedging there — sounds unsure, even in formal email. How would you
  ask for a review with one polite request?
reasoning_hidden: |
  T3 REG:LEVEL with high gravity_social (0.70 — hyperhedging signals lack of
  confidence in pro context). Elicitation forces simplification. C1 capable
  of self-correction, prefer elicit over metalinguistic.
notes: "Demo C1 pragmatic hedging, gravity_social drives feedback intensity."
```

---

## C2 — Mastery (4 examples)

### c2-silence-creative-style

```yaml
id: c2-silence-creative-style
level: C2
learner_turn: "Were I in his shoes, scarcely a moment would pass without my second-guessing the decision."
errors_detected: []
context: "Tour 4, conversation littéraire. Inversion + scarcely fronting = native-like style choice."
expected_feedback_type: silent
teacher_response: |
  Nicely turned — that inversion lands. What would you actually do, then?
reasoning_hidden: |
  No errors. C2 native-like creative use of inversion + scarcely fronting.
  Silent celebration ("nicely turned"), engage with substance.
notes: "Demo C2 : célébrer style sans correction ni feedback formel."
```

### c2-metalinguistic-connotation

```yaml
id: c2-metalinguistic-connotation
level: C2
learner_turn: "His comments were quite controversial, almost provocative — a deliberate move to stimulate debate."
errors_detected:
  - {code: LEX:COLLOC, family: vocabulary, tier: T3, gravity_linguistic: 0.30, gravity_communicative: 0.20, gravity_social: 0.50}
context: "Tour 6. 'Quite' avant 'controversial' = subtle British understatement issue."
expected_feedback_type: metalinguistic
teacher_response: |
  *Quite* + strong adjective in BrE often softens (almost ironic). For
  emphasis, *highly* or *deeply* controversial. Connotation matters at this
  level — was your intent softening or emphasis?
reasoning_hidden: |
  T3 LEX:COLLOC : connotation subtlety in British English. Metalinguistic
  + alternative phrasings + question to elicit intent (pushed creative
  output). Self-regulation framing ("at this level").
notes: "Demo C2 connotation subtility, alternatives stylistiques."
```

### c2-prompt-regression-prep

```yaml
id: c2-prompt-regression-prep
level: C2
learner_turn: "I'm interested for this position because of the opportunity to work internationally."
errors_detected:
  - {code: PREP, family: preposition, tier: T4, gravity_linguistic: 0.60, gravity_communicative: 0.20, gravity_social: 0.50}
context: "Tour 7, mock cover letter. Profile shows prepositions mastered B2."
expected_feedback_type: prompt_plus_remediation
teacher_response: |
  *Interested in*, not *for* — francophone calque worth flagging at your
  level. Adding to spaced retrieval. The rest is excellent — what
  international experience do you have to offer?
reasoning_hidden: |
  T4 regressive : preposition mastered B2, francophone L1 transfer. Prompt
  + correction + spaced_retrieval flag + immediate engagement with substance
  ("the rest is excellent" + content question). Maintain dignity.
notes: "Demo C2 T4 prep + L1 transfer, flag + maintain dignity."
```

### c2-elicit-pragmatic-implicature

```yaml
id: c2-elicit-pragmatic-implicature
level: C2
learner_turn: "His proposal was, let's say, not exactly groundbreaking. We sent it back."
errors_detected: []
context: "Tour 5, conversation pro. Implicature: 'not exactly groundbreaking' = 'mediocre' euphemism. Elegant use."
expected_feedback_type: silent
teacher_response: |
  Diplomatically put. What was your alternative proposal?
reasoning_hidden: |
  No error. Elegant pragmatic implicature ("not exactly groundbreaking" =
  diplomatic understatement of "mediocre"). Acknowledge pragmatically
  ("diplomatically put"), push for substance.
notes: "Demo C2 implicature recognition, push substance."
```

---

## Cas spéciaux (4 examples cross-level)

### special-mode-quiz-respect

```yaml
id: special-mode-quiz-respect
level: B1
learner_turn: "Yesterday I goed to the cinema with my friend."
errors_detected:
  - {code: V:TENSE, family: verb_tense, tier: T3}
context: "MODE QUIZ active. Le système attend une réponse précise à un drill."
expected_feedback_type: silent
teacher_response: |
  [follows MODE QUIZ instructions, no Lyster correction here]
reasoning_hidden: |
  MODE QUIZ overrides all Lyster pedagogy this turn. The drill expects a
  specific response format. Lyster mapping suspended; Teacher follows the
  injected MODE QUIZ instructions verbatim.
notes: "Demo : MODE QUIZ override. Lyster suspended."
```

### special-l1-watch-french

```yaml
id: special-l1-watch-french
level: B2
learner_turn: "Actually, I was supposed to assist to the meeting, but I had to go to the library to return books."
errors_detected:
  - {code: LEX:FALSE, family: vocabulary, tier: T3, gravity_linguistic: 0.70, gravity_communicative: 0.40, gravity_social: 0.40}
  - {code: LEX:FALSE, family: vocabulary, tier: T3, gravity_linguistic: 0.70, gravity_communicative: 0.40, gravity_social: 0.40}
context: "Profile.L1 = fr. L1 watch active. Phase 6+."
expected_feedback_type: metalinguistic
teacher_response: |
  Two false friends with French! *Actually* = "in fact" (not "currently") —
  use *currently* there. *Assist to* = "help"; you *attended* the meeting.
  *Library* (✓ here for borrowed books). What were you returning?
reasoning_hidden: |
  Two T3 LEX:FALSE on francophone L1. L1 watch active → metalinguistic
  contrast preferred (Lardiere 1998). Confirm 'library' was correct here
  (livres → library = OK, books not stationery → bookshop). 3 corrections
  in one turn (B2 budget 3/3).
notes: "Demo Phase 6 L1 watch francophone, batching multiple false friends."
```

### special-spaced-retrieval-revisit

```yaml
id: special-spaced-retrieval-revisit
level: A2
learner_turn: "Hello! Ready to start today?"
errors_detected: []
context: "Tour 1, session start. spaced_retrieval_today_list = ['past_simple_irregular', 'articles_a_an']. Phase 7+."
expected_feedback_type: silent
teacher_response: |
  Hi! Quick warm-up first — last week you struggled with irregular past
  verbs. *Yesterday I ___ (eat) pizza* — fill in the gap?
reasoning_hidden: |
  Phase 7 active. Items due in spaced retrieval queue. Weave a quiz on
  past_simple_irregular into session opener — feels like warm-up, not
  formal review. articles_a_an queued for later in session.
notes: "Demo Phase 7 spaced retrieval, integrated naturally."
```

### special-anti-drift-self-grade

```yaml
id: special-anti-drift-self-grade
level: A1
learner_turn: "I work in store, sell shoes, sometimes manager."
errors_detected:
  - {code: SENT:FRAG, family: sentence, tier: T2, gravity_linguistic: 0.50, gravity_communicative: 0.40, gravity_social: 0.10}
context: "Tour 10. drift_self_grade requested. Teacher must check last 5 messages for level compliance."
expected_feedback_type: implicit_recast
teacher_response: |
  Cool — so you *work in a store* and *sell shoes*. Are you sometimes the
  manager too?
reasoning_hidden: |
  T2 SENT:FRAG (article + finite clauses missing). Recast naturally fills
  the gaps. Drift self-check: my last 5 messages used vocab around 600 BNC
  words, sentences 5-10 words avg, no metalinguistic terms. → drift_self_grade
  = "compliant".
notes: "Demo Phase 5 drift self-check à turn 10, compliant case."
```

---

## Stats récap

- **24 few-shots** synthétiques
- 4 par niveau (A1 / A2 / B1 / B2 / C1 / C2) + 4 cas spéciaux (MODE QUIZ, L1, spaced retrieval, drift self-check)
- Couverture des **5 patterns Lyster** : silent, implicit_recast, elicitation, metalinguistic, prompt_plus_remediation
- Couverture des **3 axes gravité** (linguistic / communicative / social) avec demos d'override (a1-explicit-comm-breakdown : gravity_communicative 0.85 force prompt à A1)
- Couverture **diversity rule** (a2-elicit-irreg-past + a2-metalinguistic-after-elicit ; b1-elicit-pres-perfect + b1-metalinguistic-conditional)
- Couverture **dosage budget arbitré** (a2-silenced-overflow : 5 erreurs, budget 2/2)
- Couverture **regression T4** (b1-prompt-regression, c1-prompt-regression-articles, c2-prompt-regression-prep)
- Couverture **silence sur fluency markers et bonnes phrases** (b2-silence-fluency-marker, c1-metalinguistic-stylistic [no errors], c2-silence-creative-style)
- Couverture **special cases** Phase 6 (L1 watch) et Phase 7 (spaced retrieval) + Phase 5 (drift self-check) + MODE QUIZ override

---

## Sélection au runtime (Phase 2 implementation note)

Le code node Python `build_fewshots_block(level, last_feedback_history, mode_quiz_active)` :

1. **Filtre par niveau** : retient les 4 examples du niveau cible
2. **Diversity tier** : si la dernière correction sur une famille X était de type Y, prio les examples qui démontrent un type ≠ Y sur X
3. **Mode QUIZ override** : si actif, inclut `special-mode-quiz-respect` first
4. **L1 watch (Phase 6)** : si profile.L1 set, inclut `special-l1-watch-french` (ou équivalent par L1)
5. **Spaced retrieval (Phase 7)** : si items dûs, inclut `special-spaced-retrieval-revisit`
6. **Drift check (turn % 10 == 0)** : inclut `special-anti-drift-self-grade`

Limite : **5 examples max** dans le prompt à tout moment (token budget). Sélection dynamique = qualité > quantité.

---

*Sprint 3 Phase 1 — few-shots synthétiques. 24 examples handcraft. Ready for Phase 2 (build prompt assembly).*
