# Oracle V1 goldens — all recorded via onboarding flow, systemic issue

**Status** : finding documented, Session 42 fix planned.

## The finding

Pedagogical review of the 5 C1/C2 scenarios added this session revealed
that **3 of 5 goldens are 100% French onboarding responses** — no CF
feedback, no engagement with the learner error, pivot to "what's your
name and why learn English?".

## Root cause (hypothesis)

All goldens are recorded via `record_golden.py` which calls Dify public
API with `conversation_id=""` — i.e. a **fresh conversation**. Dify's
Teacher EN / Maestro ES workflows routes a fresh conversation through
the `llm_onboarding` node (designed for QCM-less first contact), not
`llm_session` (the tutoring session node that honors `observed_level`,
`scaffolding_block`, `priority_concepts`, etc.).

Even with an `observed_level` hint in the scenario, the workflow's
`code_profil_check` sees no learner profile (no QCM done) and routes
to onboarding.

## Implication — broader than C1/C2

If 3/5 C1/C2 goldens are broken, the same mechanism affects **all
scenarios across both agents** :
- 29 Teacher EN goldens (Session 40 B2)
- 24 Maestro ES goldens (Session 41 B3)
- 5 C1/C2 goldens (Session 41 this block)

Total : 58 potentially compromised goldens.

The lint layer catches structural issues (JSON wrapper, A1 jargon,
priority leak) but can't tell that the bot is in "onboarding mode" vs
"session mode". Noise floor + dim scoring operate on compromised goldens.

## What this means for Oracle V1

- **Lint gate** (block 8 + 9 in battery) : still valuable, catches
  JSON / A1 jargon / priority leak regardless of flow.
- **Full-mode pairwise-vs-golden** : currently compares "current
  onboarding reply" to "frozen onboarding reply" — detects bot
  doctrine evolution within onboarding flow, not session flow.
  Useful signal but not the ideal one.
- **Fault injection** : already invalidated by LiteLLM bypass
  (Session 41 findings doc). Dify-based fault injection would face the
  same onboarding-flow issue.

## Session 42 fix — options

### Option A : force session flow via conversation seeding (best)

Pre-create a Dify conversation by :
1. Inserting a `learner_profiles` row with QCM completed for a test
   user
2. Calling Dify once with that user_id → Dify creates a conversation
3. Capture conversation_id
4. Use that conversation_id for all subsequent golden recordings → bot
   routes through `llm_session` properly

Complexity : moderate. Requires one-time bootstrap + seeded test
user. ~2h effort.

### Option B : patch Dify workflow to skip onboarding for oracle users

Add a condition in `code_profil_check` : if `user` starts with
`oracle-`, set `profil_present=true` and route to `llm_session`.
Requires a Dify script similar to `04_qcm_users_skip_llm_onboarding.py`.
~1h effort.

### Option C : accept current goldens as "onboarding regression corpus"

Rename to "oracle onboarding corpus", acknowledge that it measures
onboarding-flow drift specifically (still useful), and build a separate
session-flow corpus later. Zero effort, but confusing and misleading.

## Recommendation

Option B (Dify patch for oracle users) — one-shot script, aligned with
how Session 36 already patched `code_profil_check` for QCM users.
Enables clean session-flow goldens for all agents. Session 42 Block 1.

## Actioned this session

- DROP 3 broken C1/C2 scenarios (register_drift, subjunctive_suggest,
  passive_overuse) — scenarios + goldens removed.
- KEEP 2 C1 scenarios (false_friend_assister, conditional_mix) flagged
  as pending re-record with proper session state.
- Oracle V1 corpus is now **26 Teacher EN + 24 Maestro ES + 2 C1
  pending** = 52 scenarios with gold standard pending rebuild.

## What's still usable today

The **lint layer** in battery block 8 + 9 is uncompromised by this
finding — it validates structural invariants independent of onboarding
vs session flow. That's the only gate currently trusted. Full-mode
scoring is noisy but still directionally useful for exploration.
