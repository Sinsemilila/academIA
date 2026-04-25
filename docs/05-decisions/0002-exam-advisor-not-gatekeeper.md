---
status: accepted
date: 2026-04-13
decision-makers: sinse, claude
---

# ADR-0002: Exam system as advisor, not gatekeeper

## Context
Exam eligibility was gated by concept mastery (80%) AND error family cleanliness. Students couldn't attempt exams until the system decided they were ready. Research (Roediger & Karpicke 2006, Bloom mastery learning, IELTS/DELF precedents) shows that even premature testing enhances learning (testing effect), and blocking access is demotivating.

## Decision
- Student can request exam at ANY mastery level (only cooldown blocks)
- System recommends: "recommended" (80%+), "approaching" (60%+), warns but accepts below
- Error taxonomy shapes exam CONTENT (weighted questions), not exam ACCESS
- Progressive cooldown: 3 days (1st fail), 7 days (2nd), 14 days (3rd+)
- Adaptive feedback by error family: metalinguistic (grammar), explicit+contrast (L1 transfer), recast (surface)

## Consequences
- Students have agency over their learning path (SDT autonomy)
- Failed attempts still provide learning value (testing effect)
- Exams target weak areas via error profile injection
- Risk: students may fail repeatedly and get demotivated → mitigated by progressive cooldown + encouragement
