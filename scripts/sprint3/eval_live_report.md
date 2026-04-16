# Sprint 3 Phase 5 — Live Battery Report

_Generated 2026-04-16T08:03:09Z — API_BASE=http://127.0.0.1:8000_

## Summary

- **Pass rate** : 97.4% (266/273 checks)
- **Turns executed** : 46
- **Latency** p50=4567ms, p95=12792ms
- **Verdict** : ✅ GREEN (threshold 95%)

## Per-persona matrix

### A1 — 100.0% (40/40)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 1 | 1 | 3044ms | 200 | 4/4 |  |
| 2 | 2 | 2731ms | 200 | 4/4 |  |
| 3 | 3 | 2641ms | 200 | 4/4 |  |
| 4 | 4 | 2703ms | 200 | 4/4 |  |
| 5 | 5 | 3246ms | 200 | 4/4 |  |
| 6 | 6 | 3154ms | 200 | 4/4 |  |
| 7 | 7 | 3182ms | 200 | 4/4 |  |
| 8 | 8 | 2614ms | 200 | 4/4 |  |
| 9 | 9 | 2168ms | 200 | 4/4 |  |
| 10 | 10 | 2107ms | 200 | 4/4 |  |

### A2 — 94.7% (36/38)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 11 | 1 | 2502ms | 200 | 4/4 |  |
| 12 | 2 | 3913ms | 200 | 4/4 |  |
| 13 | 3 | 3334ms | 200 | 4/4 |  |
| 14 | 4 | 2497ms | 200 | 4/4 |  |
| 15 | 5 | 2106ms | 200 | 4/4 |  |
| 16 | 6 | 2429ms | 200 | 4/4 |  |
| 17 | 7 | 2269ms | 200 | 4/4 |  |
| 18 | 8 | 2326ms | 200 | 4/4 |  |
| 19 | 9 | 4643ms | 200 | 4/4 |  |
| 20 | 10 | 31316ms | 0 | 0/2 | http_200, latency_under_15s |

### B1 — 95.3% (81/85)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 21 | 1 | 30026ms | 0 | 0/2 | http_200, latency_under_15s |
| 22 | 2 | 6037ms | 200 | 9/9 |  |
| 23 | 3 | 4636ms | 200 | 9/10 | t4_addressed |
| 24 | 4 | 3789ms | 200 | 9/9 |  |
| 25 | 5 | 4814ms | 200 | 9/9 |  |
| 26 | 6 | 4992ms | 200 | 9/9 |  |
| 27 | 7 | 4991ms | 200 | 9/9 |  |
| 28 | 8 | 5181ms | 200 | 9/9 |  |
| 29 | 9 | 5157ms | 200 | 9/9 |  |
| 30 | 10 | 5423ms | 200 | 9/10 | t4_addressed |

### B2 — 98.9% (90/91)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 31 | 1 | 4938ms | 200 | 9/9 |  |
| 32 | 2 | 4450ms | 200 | 9/9 |  |
| 33 | 3 | 5798ms | 200 | 9/9 |  |
| 34 | 4 | 4499ms | 200 | 9/9 |  |
| 35 | 5 | 4754ms | 200 | 9/9 |  |
| 36 | 6 | 4743ms | 200 | 9/9 |  |
| 37 | 7 | 5151ms | 200 | 9/9 |  |
| 38 | 8 | 5230ms | 200 | 9/10 | t4_addressed |
| 39 | 9 | 12792ms | 200 | 9/9 |  |
| 40 | 10 | 5105ms | 200 | 9/9 |  |

### edge_empty — 100.0% (1/1)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 41 | 1 | 3ms | 422 | 1/1 |  |

### edge_long — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 42 | 1 | 5156ms | 200 | 4/4 |  |

### edge_emoji — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 43 | 1 | 5605ms | 200 | 4/4 |  |

### edge_injection — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 44 | 1 | 2848ms | 200 | 4/4 |  |

### edge_turn5_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 45 | 6 | 6415ms | 200 | 3/3 |  |

### edge_turn10_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 46 | 11 | 12169ms | 200 | 3/3 |  |

## Failed checks (first 20)

- **A2 seq20 turn10** `http_200` — status=0 err=
  - msg: `Last night I dreamed I fly a plane and I see all the city.`
- **A2 seq20 turn10** `latency_under_15s` — 31316ms
  - msg: `Last night I dreamed I fly a plane and I see all the city.`
- **B1 seq21 turn1** `http_200` — status=0 err=
  - msg: `I live in Paris since 5 years and I love it.`
- **B1 seq21 turn1** `latency_under_15s` — 30026ms
  - msg: `I live in Paris since 5 years and I love it.`
- **B1 seq23 turn3** `t4_addressed` — tier_applied=['T2']
  - msg: `My brother is more taller than my sister.`
- **B1 seq30 turn10** `t4_addressed` — tier_applied=['T2']
  - msg: `Tomorrow I think I will go to gym after work to relax myself.`
- **B2 seq38 turn8** `t4_addressed` — tier_applied=['T2']
  - msg: `I'm interested for this position because of the international scope.`
