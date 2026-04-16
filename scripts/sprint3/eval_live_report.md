# Sprint 3 Phase 5 — Live Battery Report

_Generated 2026-04-16T10:47:27Z — API_BASE=http://127.0.0.1:8000_

## Summary

- **Pass rate** : 99.4% (334/336 checks)
- **Turns executed** : 46
- **Latency** p50=5152ms, p95=6470ms
- **Verdict** : ✅ GREEN (threshold 95%)
- **L1 contrast mention rate** : 75% (3/4 FR→EN transfer turns) — informational

## Per-persona matrix

### A1 — 100.0% (40/40)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 1 | 1 | 4215ms | 200 | 4/4 |  |
| 2 | 2 | 3883ms | 200 | 4/4 |  |
| 3 | 3 | 3398ms | 200 | 4/4 |  |
| 4 | 4 | 3076ms | 200 | 4/4 |  |
| 5 | 5 | 2178ms | 200 | 4/4 |  |
| 6 | 6 | 2524ms | 200 | 4/4 |  |
| 7 | 7 | 2683ms | 200 | 4/4 |  |
| 8 | 8 | 2726ms | 200 | 4/4 |  |
| 9 | 9 | 3086ms | 200 | 4/4 |  |
| 10 | 10 | 5695ms | 200 | 4/4 |  |

### A2 — 100.0% (90/90)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 11 | 1 | 5801ms | 200 | 9/9 |  |
| 12 | 2 | 5946ms | 200 | 9/9 |  |
| 13 | 3 | 6650ms | 200 | 9/9 |  |
| 14 | 4 | 4759ms | 200 | 9/9 |  |
| 15 | 5 | 6470ms | 200 | 9/9 |  |
| 16 | 6 | 4629ms | 200 | 9/9 |  |
| 17 | 7 | 4699ms | 200 | 9/9 |  |
| 18 | 8 | 5289ms | 200 | 9/9 |  |
| 19 | 9 | 6528ms | 200 | 9/9 |  |
| 20 | 10 | 6077ms | 200 | 9/9 |  |

### B1 — 97.8% (91/93)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 21 | 1 | 5992ms | 200 | 9/9 |  |
| 22 | 2 | 4962ms | 200 | 9/9 |  |
| 23 | 3 | 4373ms | 200 | 9/10 | t4_addressed |
| 24 | 4 | 5481ms | 200 | 9/9 |  |
| 25 | 5 | 5696ms | 200 | 9/9 |  |
| 26 | 6 | 4955ms | 200 | 9/9 |  |
| 27 | 7 | 4784ms | 200 | 9/9 |  |
| 28 | 8 | 5170ms | 200 | 9/9 |  |
| 29 | 9 | 5870ms | 200 | 9/9 |  |
| 30 | 10 | 4832ms | 200 | 10/11 | t4_addressed |

### B2 — 100.0% (94/94)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 31 | 1 | 5371ms | 200 | 9/9 |  |
| 32 | 2 | 5703ms | 200 | 10/10 |  |
| 33 | 3 | 5172ms | 200 | 10/10 |  |
| 34 | 4 | 4908ms | 200 | 9/9 |  |
| 35 | 5 | 4900ms | 200 | 9/9 |  |
| 36 | 6 | 5998ms | 200 | 9/9 |  |
| 37 | 7 | 5405ms | 200 | 9/9 |  |
| 38 | 8 | 5182ms | 200 | 11/11 |  |
| 39 | 9 | 6333ms | 200 | 9/9 |  |
| 40 | 10 | 5879ms | 200 | 9/9 |  |

### edge_empty — 100.0% (1/1)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 41 | 1 | 14ms | 422 | 1/1 |  |

### edge_long — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 42 | 1 | 5182ms | 200 | 4/4 |  |

### edge_emoji — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 43 | 1 | 3743ms | 200 | 4/4 |  |

### edge_injection — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 44 | 1 | 2733ms | 200 | 4/4 |  |

### edge_turn5_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 45 | 6 | 5543ms | 200 | 3/3 |  |

### edge_turn10_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 46 | 11 | 5135ms | 200 | 3/3 |  |

## Failed checks (first 20)

- **B1 seq23 turn3** `t4_addressed` — tier_applied=['T2']
  - msg: `My brother is more taller than my sister.`
- **B1 seq30 turn10** `t4_addressed` — tier_applied=['T2']
  - msg: `Tomorrow I think I will go to gym after work to relax myself.`
