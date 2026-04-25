---
status: accepted
date: 2026-04-13
decision-makers: sinse, claude
---

# ADR-0003: Behavior detection via prompt, not backend ML

## Context
Need to detect student emotional states (frustration, confusion, boredom, flow, gaming) and adapt feedback. Research (D'Mello & Graesser, Baker, Pekrun) identifies text-based signals: response length, L1 switching, error repetition, timing. Two approaches: (A) backend ML pipeline that classifies state, (B) instruct the LLM to detect and adapt via prompt.

## Decision
V1: Prompt-based detection. The Teacher LLM already sees the full conversation history — it can detect shortening responses, French intrusion, repeated errors, engagement shifts. We add detailed instructions for 5 behavioral states + escalating correction protocol.

Backend enrichment for signals the LLM can't see: per-turn response latency (turn_response_secs) and error recurrence flag (repeated_errors from last 7 days).

V2 (future): Backend ML classifier if prompt-based detection proves insufficient.

## Consequences
- Zero infrastructure cost for V1 (just a prompt)
- LLM has full conversation context for pattern detection
- Backend adds timing + error history signals (2 Dify inputs)
- Correction protocol escalates: recast → metalinguistic → rule → explicit+L1
- Risk: LLM may not consistently detect all states → acceptable for V1, monitor and iterate
