---
status: authoritative
last_reviewed: 2026-04-30
authors: [claude-opus, sinse]
tags: [oracle, methodology, plan]
session_origin: 53
---

# Sprint Oracle EN cohérence — 2026-05

**Goal** : Oracle EN trustworthy avant switch Maestro ES. Effort total ~6-7j (1 sprint hebdo).

**Drivers** :
- Capacity unlock 540→166K RPD shipped Session 53 (Cerebras + Mistral via LiteLLM)
- Variance judge actuelle ~38% split rate (Rating Roulette ACL 2025) → cohérence faible
- 2 stable structural fails persistants (b2_passive + b1_prep) → plafond ~24/26
- Architecture cross-langue dépend d'un EN baseline solide

## Définition de fini (DoD)

```
Score                  : 22-24/26 stable cross 3+ runs
Cross-judge AC2        : ≥ 0.7 (panel internal coherence)
Run-to-run AC2         : ≥ 0.7 (vraie reproductibilité)
κ vs Sinse manual      : ≥ 0.7 (validité externe)
Stable structural fails: 0
Capacity               : 5-10 full runs/jour (cache + Cerebras)
```

→ Si ces 5 critères atteints : **switch Maestro ES**, ne pas pousser plus loin sur EN (Goodhart).

---

## Phase 0 — DONE (Session 53, 2026-04-30)

```
✅ Cerebras key /opt/academie-shared/secrets/cerebras-api-key (mode 600)
✅ LiteLLM proxy : cerebras-judge-fast + cerebras-judge-deep + mistral-medium
✅ rpm bump mistral-small 2→100
✅ Admin /admin judge-budget : 7-tier display
✅ Smoke 16/17 stable
```

**Files shipped** :
- `litellm/config.yaml.sops`
- `webapp/backend/app/routers/admin_router.py`
- `webapp/frontend/src/routes/admin/+page.svelte`

---

## Phase 1 — Foundation (Day 1, ~4h)

**Objectif** : tighter measurement avant tout autre changement. Ne pas bouger goldens / Teacher prompts encore.

### 1.1 — `n_votes 3→5` + asymetric threshold

**File** : `scripts/oracle/config.yaml`
```yaml
modes:
  full:
    scenario_count: 24
    n_votes: 5                    # was 3
judge_fail_threshold: 0.7         # already in place
```

### 1.2 — Switch judge primary → cerebras-judge-fast

**File** : `scripts/oracle/config.yaml`
```yaml
judge:
  model: cerebras-judge-fast      # was gemini-3-1-flash-lite
  n_votes: 5
  temperature: 0.0
  max_tokens: 500
  timeout_s: 30
```

### 1.3 — Gwet's AC2 reporting

**New** : `scripts/oracle/kappa/ac2.py`
- Gwet (2008) AC2 : κ-paradox-robust agreement coefficient
- Multi-rater (n_votes=5) collapsed to per-scenario verdict
- Output : ac2_per_dim + ac2_global + bootstrap 95% CI

**Edit** : `scripts/oracle/harness.py`
- Append AC2 metrics to JSON output post-battery

### 1.4 — Test suite

**New** : `scripts/oracle/tests/test_kappa.py`
- 3 unit tests : perfect agreement → 1.0 ; max disagreement → 0 ; skewed binary edge case

### Exit gate Phase 1

- [ ] `pytest scripts/oracle/tests/` green
- [ ] `python3 scripts/oracle/harness.py --agent teacher_en --mode smoke` runs without error
- [ ] AC2 reporting visible in JSON output

---

## Phase 2 — Multi-judge panel cross-provider (Day 2-3, ~1.5j)

**Objectif** : Vraie mesure cohérence (cross-provider agreement, pas self-noise gemini).

### 2.1 — Architecture

3 juges indépendants par scenario × dim :
```
panel_default:
  - cerebras-judge-fast    # llama-3.1-8b
  - mistral-small          # mistral-small-latest
  - gemini-3-1-flash-lite  # baseline κ=0.84 reference
```

Vote logic :
- 3/3 → certif fort
- 2/3 → certif faible
- < 2/3 → unknown pass-through

### 2.2 — Files

**New** : `scripts/oracle/judges/multi_judge_panel.py`
- Class `MultiJudgePanel` : dispatch parallel async via LiteLLM proxy
- Aggregate votes + agreement_ratio + cross-judge AC2

**Edit** : `scripts/oracle/judges/llm_pairwise.py`
- Refactor : accept judge_model param (was hardcoded)
- Backward compat preserved : single judge_model → unchanged behaviour

**Edit** : `scripts/oracle/harness.py`
- CLI flag `--panel cross-provider` (default off)
- Output : per-dim verdict + per-judge votes + agreement_ratio + cross-judge AC2

**Edit** : `scripts/oracle/config.yaml`
```yaml
panel:
  enabled: false                  # opt-in via CLI
  members:
    - cerebras-judge-fast
    - mistral-small
    - gemini-3-1-flash-lite
  agreement_threshold: 0.66       # 2/3 minimum for certif
```

### 2.3 — Tests

**New** : `scripts/oracle/tests/test_multi_judge.py`
- Mock 3 judges → verify majority vote logic
- Failure mode : 1 provider 429 → continue with 2/3 partial vote

### Exit gate Phase 2

- [ ] `pytest scripts/oracle/tests/test_multi_judge.py` green
- [ ] Smoke run avec `--panel cross-provider` complete sans crash
- [ ] Token usage ≤ 5K tokens (smoke 6 scenarios × 3 dims × 3 judges)

---

## Phase 3 — Re-mesure baseline + κ calibration (Day 3, ~4h)

### 3.1 — Battery full panel

```bash
python3 scripts/oracle/harness.py \
  --agent teacher_en --mode full \
  --panel cross-provider \
  --output /tmp/baseline-multi-judge-$(date +%s).json
```

Expected : 24 scenarios × 5 votes × 3 dims × 3 judges = ~1080 calls × ~1K tokens = **~1M tokens**, ~25 min via Cerebras + Mistral parallel.

### 3.2 — Compare vs gemini-only baseline (S51 18-19/26 ±1)

Metrics :
- Score brut (N/26) : panel vs gemini-only
- Stable fails persistants
- Cross-judge AC2 (panel internal)
- Run-to-run AC2 (panel × 2 runs)

### 3.3 — Sinse manual κ calibration

```bash
python3 scripts/oracle/export_for_manual.py > /tmp/oracle_manual_scoring.md
# Sinse fills /tmp/oracle_sinse_scores.yaml (~30-45 min)
python3 scripts/oracle/calibration.py \
  --manual /tmp/oracle_sinse_scores.yaml \
  --oracle /tmp/baseline-multi-judge-*.json
```

### Exit gate Phase 3

- [ ] κ panel vs Sinse manual ≥ 0.7 → continue Phase 4
- [ ] 0.5 ≤ κ < 0.7 → inject Phase 3.5 avant Phase 4
- [ ] κ < 0.5 → STOP, deep judge prompt audit (Phase 3.5 mandatory)

---

## Phase 3.5 — Judge prompts audit (conditional, Day 4)

**Trigger** : Phase 3 κ < 0.7 vs Sinse manual.

### 3.5.1 — Audit 3 prompts judge

**Source** : `scripts/oracle/judges/llm_pairwise.py` (3 dims LLM-évaluées : `cf_move_set_valid`, `register_cefr_alignment`, `semantic_fidelity_pairwise`)

Checklist :
- [ ] Output schema strict JSON `{verdict, reasoning, confidence}`
- [ ] Chain-of-thought explicite (3 steps minimum)
- [ ] Few-shots disambiguating dans le prompt (≥ 2 exemplars per edge case)
- [ ] Acceptable_set + forbidden formulés en termes opérationnels
- [ ] Pas de "near-native", "highly proficient" → expressions Companion 2020 verbatim

### 3.5.2 — A/B test

```bash
python3 scripts/oracle/harness.py --agent teacher_en --mode smoke --panel cross-provider --judge-prompt v1
python3 scripts/oracle/harness.py --agent teacher_en --mode smoke --panel cross-provider --judge-prompt v2
```

Compare cross-judge AC2 v1 vs v2. Si v2 +0.1 → ship v2.

### Exit gate Phase 3.5

- [ ] κ vs Sinse manual ≥ 0.7 (re-measured post-prompt-fix)

---

## Phase 4 — Quality fixes : stable fails (Day 4-5, ~2j)

**Objectif** : Score absolu baseline 22-24/26 stable.

### 4.1 — Fix `b2_t3_passive_001`

**Symptôme** : Teacher fait `explicit_correction` au lieu de `implicit_recast` sur passé passif B2.

**Diagnostic** :
- Read golden : `scripts/oracle/scenarios/teacher_en/golden/b2_t3_passive_001.json`
- Read rubric Dify : Teacher EN workflow → "Session interactive" node → fewshots block B2
- Count fewshots `implicit_recast` dans cellule B2-passive

**Fix path** :
1. Add 2-3 fewshots `implicit_recast` typés Lyster pour B2-passive dans rubric prompt Teacher
2. Re-record golden : `record_golden.py --only b2_t3_passive_001 --apply`
3. Re-run battery → verify scenario pass

**Files** : Dify workflow JSON via `scripts/update_teacher_chatflow.py` + golden re-record.

### 4.2 — Fix `b1_edge_t2t3_prepositions_001`

Symétrique : `partial_recast` fewshot pour B1-preposition.

### Exit gate Phase 4

- [ ] 2 stable fails passent en `pass` sur 3 runs consécutifs
- [ ] Aucune régression sur les 22 autres scenarios
- [ ] Cross-judge AC2 stable

---

## Phase 5 — Battery V1 audit (Day 5, ~1j)

**Objectif** : Identifier scenarios où acceptable_set trop strict cause des faux fails.

### 5.1 — Re-read 26 scenarios

Pour chaque scenario, vérifier vs Hughes 2020 + Lyster 2007 + CEFR Companion 2020 :
- `acceptable_set` cohérent avec cellule CEFR × tier ?
- `forbidden` pédagogiquement défendable ?
- `target_tier` (T2/T3) correspond à l'erreur (gravité × developmental readiness) ?

### 5.2 — Document anomalies

**New** : `webapp/backend/docs/audit/2026-05-XX-oracle-battery-v1-audit.md`
- Liste scenarios litigeux + justification fix
- Pattern : "scenario X expects Y but Lyster 2007 p.123 supports also Z"

### 5.3 — Patches conservatifs

Argument académique fort requis. Pas de relâchement systematique pour booster score.

### Exit gate Phase 5

- [ ] Audit doc commit
- [ ] Si patches : re-record goldens affectés + re-mesure battery
- [ ] Score stable 22-24/26 avec n_votes=5 + panel

---

## Phase 6 — Cache verdicts hash-based (Day 6, ~1j)

**Objectif** : Efficiency. Permet runs 5-10×/jour vs 1×/jour.

### 6.1 — Architecture

**New** : `scripts/oracle/cache.py`
```python
import sqlite3, hashlib

CACHE_DB = "scripts/oracle/.cache/verdicts.sqlite"

def cache_key(scenario_id, teacher_response, dim, judge_prompt_version, judge_model):
    raw = f"{scenario_id}|{hash(teacher_response)}|{dim}|{judge_prompt_version}|{judge_model}"
    return hashlib.sha256(raw.encode()).hexdigest()
```

### 6.2 — Edit `harness.py` + `judges/llm_pairwise.py`

- Pre-call : cache lookup → if hit, skip LLM call
- Post-call : cache write
- CLI flag `--no-cache` (CI / fault-injection)

### 6.3 — TTL + invalidation

- TTL = 30 jours
- Invalidation auto si `judge_prompt_version` bump (incrément manuel dans config.yaml)
- `oracle/scripts/cache_purge.py` pour nettoyage manuel

### Exit gate Phase 6

- [ ] Cache hit rate ≥ 50% sur 2è run identique
- [ ] `pytest scripts/oracle/tests/test_cache.py` green
- [ ] `--no-cache` flag fonctionne

---

## Phase 7 — V2 battery seed (post-MVP, post-Maestro ES)

**Pas un blocker MVP**. Skeleton plan only.

### 7.1 — Extract criterial scenarios

Sources :
- `data/extracted/hawkins-filipovic-2012-criterial-features-l2-english/`
- `data/extracted/coe-2020-cefr-companion-volume/`

**Cible** : 30-50 scenarios criterion-referenced (vs 26 V1 handcrafted), 5-10 par niveau A1→C2 weighted by error frequency (MERLIN-DE / EVP / VALICO research).

### 7.2 — Plan

`webapp/backend/docs/01-pedagogy/oracle-v2-battery-design.md` (plan only Phase 7).

---

## Gates de transition globale

```
Phase 0 ✅
   ↓ ship 3 commits
Phase 1 — n_votes + AC2 [4h]
   ↓ pytest + smoke green
Phase 2 — Multi-judge panel [1.5j]
   ↓ smoke panel green
Phase 3 — Baseline + κ Sinse [4h]
   ↓ if κ ≥ 0.7
Phase 4 — Fix 2 stable fails [2j]
   ↓ 3 runs consécutifs pass
Phase 5 — Battery V1 audit [1j]
   ↓ audit doc commit
Phase 6 — Cache verdicts [1j]
   ↓ hit rate ≥ 50%
═══════════════════════════════════════════
✅ MVP Oracle EN trustworthy → switch Maestro ES
═══════════════════════════════════════════
Phase 7 (post-MVP)
```

## Risks identifiés

| Risk | Phase | Mitigation |
|---|---|---|
| Cerebras rate limit unexpected sur run intensif | 3 | Mistral fallback préconfiguré, panel = robustness build-in |
| κ Sinse manual révèle judge prompts cassés | 3 → 3.5 | 1j buffer prévu |
| Fix stable fails régresse autres scenarios | 4 | 3 runs consécutifs gate avant ship |
| Cache invalidation foireux → faux pass cached | 6 | TTL 30j conservateur + version key explicit |
| V1 audit surface plus de problèmes que prévu | 5 | Patches conservatifs only |

## Refs

- Vault `projects/academia-ia/knowledge/oracle-harness-conventions.md`
- Vault `projects/academia-ia/knowledge/teacher-en-improvement-research.md`
- Session 51 `7a7fae1` (build_full_dify_inputs harness/prod alignment)
- Session 51 `2b76917` (judge retry/back-off)
- Lyster 2007 *Counterbalanced Approach* (CF taxonomy)
- Gwet 2008 *Computing inter-rater reliability and its variance in the presence of high agreement* (AC2)
- Rating Roulette ACL 2025 (judge variance LLM)
