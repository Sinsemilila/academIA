# Sprint 3 Phase 5 — Live Battery Report

_Generated 2026-04-16T12:39:35Z — API_BASE=http://127.0.0.1:8000_

## Summary

- **Pass rate** : 99.1% (333/336 checks)
- **Turns executed** : 46
- **Latency** p50=5712ms, p95=9450ms
- **Verdict** : ✅ GREEN (threshold 95%)
- **L1 contrast mention rate** : 75% (3/4 FR→EN transfer turns) — informational

## Per-persona matrix

### A1 — 100.0% (40/40)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 1 | 1 | 4339ms | 200 | 4/4 |  |
| 2 | 2 | 4522ms | 200 | 4/4 |  |
| 3 | 3 | 3754ms | 200 | 4/4 |  |
| 4 | 4 | 3050ms | 200 | 4/4 |  |
| 5 | 5 | 2540ms | 200 | 4/4 |  |
| 6 | 6 | 2880ms | 200 | 4/4 |  |
| 7 | 7 | 2458ms | 200 | 4/4 |  |
| 8 | 8 | 2282ms | 200 | 4/4 |  |
| 9 | 9 | 2489ms | 200 | 4/4 |  |
| 10 | 10 | 5362ms | 200 | 4/4 |  |

### A2 — 100.0% (90/90)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 11 | 1 | 6045ms | 200 | 9/9 |  |
| 12 | 2 | 6596ms | 200 | 9/9 |  |
| 13 | 3 | 7988ms | 200 | 9/9 |  |
| 14 | 4 | 5470ms | 200 | 9/9 |  |
| 15 | 5 | 6773ms | 200 | 9/9 |  |
| 16 | 6 | 5414ms | 200 | 9/9 |  |
| 17 | 7 | 5129ms | 200 | 9/9 |  |
| 18 | 8 | 5214ms | 200 | 9/9 |  |
| 19 | 9 | 6475ms | 200 | 9/9 |  |
| 20 | 10 | 7030ms | 200 | 9/9 |  |

### B1 — 97.8% (91/93)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 21 | 1 | 6325ms | 200 | 9/9 |  |
| 22 | 2 | 6428ms | 200 | 9/9 |  |
| 23 | 3 | 11499ms | 200 | 9/10 | t4_addressed |
| 24 | 4 | 6264ms | 200 | 9/9 |  |
| 25 | 5 | 5847ms | 200 | 9/9 |  |
| 26 | 6 | 5076ms | 200 | 9/9 |  |
| 27 | 7 | 5663ms | 200 | 9/9 |  |
| 28 | 8 | 5609ms | 200 | 9/9 |  |
| 29 | 9 | 6004ms | 200 | 9/9 |  |
| 30 | 10 | 9450ms | 200 | 10/11 | t4_addressed |

### B2 — 98.9% (93/94)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 31 | 1 | 5876ms | 200 | 9/9 |  |
| 32 | 2 | 6216ms | 200 | 10/10 |  |
| 33 | 3 | 5758ms | 200 | 10/10 |  |
| 34 | 4 | 5666ms | 200 | 9/9 |  |
| 35 | 5 | 8663ms | 200 | 9/9 |  |
| 36 | 6 | 6621ms | 200 | 9/9 |  |
| 37 | 7 | 6341ms | 200 | 9/9 |  |
| 38 | 8 | 6181ms | 200 | 10/11 | t4_addressed |
| 39 | 9 | 8250ms | 200 | 9/9 |  |
| 40 | 10 | 11264ms | 200 | 9/9 |  |

### edge_empty — 100.0% (1/1)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 41 | 1 | 8ms | 422 | 1/1 |  |

### edge_long — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 42 | 1 | 5302ms | 200 | 4/4 |  |

### edge_emoji — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 43 | 1 | 4834ms | 200 | 4/4 |  |

### edge_injection — 100.0% (4/4)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 44 | 1 | 2742ms | 200 | 4/4 |  |

### edge_turn5_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 45 | 6 | 5815ms | 200 | 3/3 |  |

### edge_turn10_trigger — 100.0% (3/3)

| seq | turn | latency | status | checks | fails |
|-----|------|---------|--------|--------|-------|
| 46 | 11 | 4973ms | 200 | 3/3 |  |

## Failed checks (first 20)

- **B1 seq23 turn3** `t4_addressed` — tier_applied=['T2']
  - msg: `My brother is more taller than my sister.`
- **B1 seq30 turn10** `t4_addressed` — tier_applied=['T2']
  - msg: `Tomorrow I think I will go to gym after work to relax myself.`
- **B2 seq38 turn8** `t4_addressed` — tier_applied=['T2']
  - msg: `I'm interested for this position because of the international scope.`
