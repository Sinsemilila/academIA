# Teacher EN dogfood — setup + checklist (Session 39)

**Goal** : organic browser parity check with Maestro ES. The full ES pipeline
has been validated end-to-end ; Teacher EN is lang-agnostic by design but
never got a human browser run.

## Prep (already done)

- [x] Fix ES three-strikes mapping (`1eb6a3f`) applied — both langs now share
      the same detection path ; EN already worked.
- [x] Phase D telemetry active (`ab99e61`) — cache hits will show in
      `litellm_cache_stats` in real time.
- [x] YAML validator (`0c0e336`) — data pack schemas now enforced.
- [x] `/admin/cache-stats` dashboard live (`207450d`).
- [x] `MICRO_LESSON_ENABLED=true` and `PRIORITY_CONCEPTS_ENABLED=true` already
      ON since Session 38 (see `webapp/.env`).

## Environment toggles for the session

Optional (only if replaying the same scenario twice) :

```bash
# Bypass three_strikes 3-day dedup so the same verb_tense scenario can
# fire the micro-lesson twice in one session :
export THREE_STRIKES_DEDUP_BYPASS=true
cd /opt/academie/webapp && docker compose -f docker-compose.webapp.yml up -d --build academie-api
```

Remember to unset + rebuild after the session.

## Scenario script

1. Open `http://localhost:3001` → login → reset EN domain via `/admin` (or
   use a fresh disposable user).
2. QCM onboarding A1 : pick "zero_ou_presque" self-eval, self_efficacy ≤ 2,
   FLA moderate (speaking 3, mockery 3, freeze 3).
3. 10 turns of chat ; inject these 3 errors **consecutively** at turns 5-7 :
   - Turn 5 : "Yesterday I go to the market with my mum."
   - Turn 6 : "She eat breakfast at 7 every day."
   - Turn 7 : "We did goed home after school."
4. Continue turns 8-10 to observe dedup behavior.
5. Check `/admin/cache-stats` mid-session — cached_tokens should climb.

## Checklist (a) through (e)

- [ ] **(a) `observed_level`** : from turn 3+, inspect the Dify message JSON
      (`SELECT answer FROM messages ORDER BY created_at DESC LIMIT 5` in
      `academie_db`) — each should contain `"observed_level": "A1"` or
      similar CEFR, never empty.
- [ ] **(b) Micro-lesson fires at turn 7** : after the 3rd verb_tense error,
      next tutor reply should naturally incorporate a past-tense clarification
      (e.g. "yesterday → *went*") **without** sounding like a lesson block.
      Verify : `SELECT * FROM micro_lesson_log ORDER BY injected_at DESC LIMIT 1;`
      — one row for (eleve_id, 'en', 'verb_tense', 'A1').
- [ ] **(c) Dedup holds** : turn 8 should NOT re-inject even if another
      verb_tense error appears. `micro_lesson_log` stays at 1 row.
- [ ] **(d) priority_concepts never spoken** : the bot must NOT say anything
      like "today we'll focus on X, Y, Z" — weaving only.
- [ ] **(e) Tier mix sane** : trivial errors (spelling, articles) should get
      T1 (silent) or T2 (recast). Structural errors get T3 (elicit) on target
      structures, T4 only on comm breakdowns.

## Notes sink

Drop observations in `/tmp/dogfood_en_findings.md`. Anything surprising →
paste a message ID or log line. Non-P0 bugs → TODO.md, not fix today.

## Known limits

- CLI simulation (`scripts/sprint6/15_dogfood_simulation.py`) already confirmed
  mechanism level (detection + block render + dedup + A1 no-jargon) works.
- Browser session adds : (a) LLM integration feel, (b) UI flow quality,
  (c) real-time observation of the overall experience. Can't be automated.

## If micro-lesson doesn't fire

1. Check env : `docker exec academie-api env | grep MICRO_LESSON_ENABLED` → `true`.
2. Check codes : `SELECT error_code, count(*) FROM error_log WHERE eleve_id=$me AND domain='en' ORDER BY created_at DESC LIMIT 10;` — need 3 consecutive verb_tense codes (V:TENSE / V:SVA / V:FORM / V:INFL).
3. Check detection live : `docker exec academie-api python3 -c "import asyncio, asyncpg, os; from academie_core.pedagogy.three_strikes import detect_three_strikes_family; asyncio.run((lambda: (await (await asyncpg.connect(os.environ['DATABASE_URL'])).fetchval('SELECT 1'))))"` (or run the dogfood simulation script with your eleve_id).
