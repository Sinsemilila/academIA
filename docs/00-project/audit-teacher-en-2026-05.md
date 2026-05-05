---
created: 2026-05-05
type: audit
tags: [audit, plan, security, pedagogy, architecture]
status: claude_draft
sessions_validated: [60-2026-05-05]
last_reviewed_human: null
ai_summary: "Audit global Teacher EN cross-cutting (sécurité backend + pédagogie SLA + architecture/cost + normes EU 2026). 17 findings priorisés P0/P1/P2/strat. Top 5 actions semaine."
---

# Audit Teacher EN — comprehensive 2026-05-05

**Méthode** : 4 agents spécialisés dispatchés en parallèle (Explore sécurité, pedagogy-reviewer SLA, Explore architecture/cost, general-purpose web research normes EU 2025-2026). Synthèse cross-cutting Session 60.

**Agents dispatchés** :
- Sécurité backend (Argon2id, sessions, CSRF, CSP, rate-limit, RGPD, secrets, backup, observability)
- Pédagogie Teacher EN (Lyster T1-T4, dosage, CEFR consolidation, scaffolding L1/L2, drift validation, output schema, oracle harness, pink-elephant)
- Architecture infra (Docker /28, Postgres pool, LiteLLM cascade, n8n workflows, GlitchTip, backup, smoke-test, frontend perf, scaling cliff)
- Normes 2025-2026 (AI Act art 50 + Annex III, RGPD edtech CNIL, CEFR Companion 2020, Lyster meta-analyses, retention benchmarks edtech, prompt caching, EAA microenterprise)

---

## 🔴 P0 — Bugs actifs & non-conformités (à fix avant prod public)

### 1. Logout endpoint non-authentifié [SEC]

**Where** : `webapp/backend/app/routers/auth_router.py:178-183`
**Bug** : `/api/auth/logout` ne valide pas `session.user_id == user_from_cookie`. Attacker peut logger n'importe quel user avec cookie forgé.
**Fix** : ajouter vérification ownership session, ~5 lignes Python.

### 2. Rate-limit single-worker assumption [SEC]

**Where** : `webapp/backend/app/rate_limit.py:7`
**Bug** : in-memory token-bucket. Multi-worker uvicorn (8 workers défaut) → bypass trivial, limites ÷N.
**Fix** : migrer slowapi+Redis (roadmap A5 mentionne ça mais pas shippé). Critique avant scale.

### 3. Rubriques A1/A2/B1 = pink-elephant massif [PEDAG]

**Where** : `packages/academie-core/academie_core/data/rubrics/en.yaml:14-19, 30-34, 45-49`
**Bug** : 7+ phrases verbatim bannies ("It should be", "You should say", "You need to add") **à l'intérieur** des directives qui interdisent ces phrases. Session 45 P2g+h+i fix appliqué seulement aux few-shots block, pas à la rubrique YAML.
**Risque** : Teacher A1 dérive vers "you should..." 2× plus fréquemment qu'à C1.
**Fix** : rewrite construction positive-only ("ALWAYS recast inside follow-up question") — aucune mention des phrases bannies.

### 4. Oracle harness 0 scenario A1 + 0 scenario C2 [PEDAG]

**Where** : `scripts/oracle/scenarios/teacher_en/`
**Bug** : 28 scenarios couvrent A2/B1/B2/C1, **rien à A1 ni C2**. A1 = bande la plus risquée (rubric pink-elephant + LLM compliance la plus faible Session 45 P2c). `el_a1_t2_misc_*` dans `_examples/` non promus en goldens runnables. C2 entièrement absent.
**Risque** : fix #3 ne peut pas être regression-testé sans #4.
**Fix** : promote 3-4 A1 + author 3-4 C2 scenarios.

### 5. AI Act Annex III §3 : steering CEFR = high-risk [LEGAL]

**Source** : Annex III §3 "evaluate learning outcomes (including when used to steer the learning process)". Article 50 transparence en vigueur 2026-08-02 (sanctions 7.5M€ ou 1.5% CA).
**Bug** : Teacher EN avec CEFR consolidation + mini-exam + drift detection risque classification high-risk → risk mgmt system + tech doc + CE marking obligatoires.
**Mitigation** : positionner UI/legal **comme assistant conversationnel non-évaluatif** (pas "score CEFR officiel", pas "placement decision"). Si pivot évaluatif futur → budgéter compliance ~10-30j + CE marking.
**Sources** : artificialintelligenceact.eu/article/50, /annex/3, EC Code of Practice draft 17 déc 2025.

### 6. Mineurs <15 RGPD : parental consent dur requis [LEGAL]

**Source** : CNIL plan stratégique 2025-2028 (mineurs + IA top 4). France art 8 RGPD = consentement parental <15.
**Bug** : page `/legal/mineurs` existe mais aucun UI/flow blocking <15 sans consent parental.
**Fix** : flow signup avec age gate + parental email confirmation pour <15.

### 7. Postgres pool 14 max — Coach Sportif va crasher [ARCHI]

**Where** : `webapp/backend/app/database.py` (asyncpg pool config)
**Setup** : academie_db min:2 max:10 + litellm_db min:1 max:4 = 14 connexions max. 31 connexions actives observées sous load léger actuel.
**Risque** : Coach Sportif (3-5 containers backend + 100 users cible) → connection pool exhaustion immédiate, cascade Dify/n8n fail.
**Fix** : déploie PgBouncer en transaction mode (1 jour) + tune `max_connections=150`, `shared_buffers=1GB`.

---

## 🟡 P1 — Dette opérationnelle (à traiter sous 4-6 semaines)

| # | Issue | Source/Path | Action |
|---|---|---|---|
| 8 | N8n `dify-snapshot` workflow fail rate **17%** + doublon webhook `dify-diagnostic` (2 IDs même path) | n8n DB execution_data | Archive workflow doublon ; debug node 10 (`/internal/analyze-errors` LLM expensive). Silent profil loss 17% du temps. |
| 9 | `TeacherResponse` est dataclass pas Pydantic strict | `pedagogy/teacher_prompt.py:794-808` | Switch Pydantic v2 + `extra='forbid'` + cross-field validator (ex `feedback_types=["explicit_correction"]` interdit si `tier_applied=["T3"]` à A1). Telemetry contamination potentielle. |
| 10 | L1 transfer FR→EN bare-bones (5 familles, 3 false-friends) vs Granger ICLE / Lardiere ~1500 faux amis | `data/l1_transfer/fr_to_en.yaml` | Augmenter YAML + dériver overlay per-learner depuis `error_log.error_code IN (FALSE_FRIEND, *_CALQUE)`. |
| 11 | Drift self-grade pas de cross-check ground-truth (LLM grade itself) | `pedagogy/teacher_prompt.py` (drift_self_grade) | Ajouter `oracle/judges/deterministic.py` register classifier léger (POS density + lemma-frequency BNC bands ≤A2). Log mismatches. |
| 12 | Anthropic prompt caching jamais activé | Dify chatflow → LiteLLM passthrough | `cache_control` headers. **-70-95% cost LLM**, ROI immédiat (system prompt + Lyster rubric + CEFR ≈3-8K tokens stables = cibles). |
| 13 | Cost runaway race condition + pas de hard kill switch | `internal_router.py:115-126` UPSERT + `admin_router.py` cost_runaway_users | UPSERT race rare (~0.1%) — fix `SELECT FOR UPDATE`. Plus important : middleware pré-LLM check budget restant, retourne 429 si dépassé. |
| 14 | Backup zero restore testing formel + RTO non mesuré | `/opt/academie/docs/04-infra/backup.md` | Quarterly DR drill : pick Niveau aléatoire, restore staging, validate smoke-test, doc temps. Écris `docs/99-runbooks/DISASTER_RECOVERY.md`. |
| 15 | PII scrubber couverture incomplete dans payloads Dify | `pii_scrubber.py` + `chat_router.py:18` | Audit call-sites `maybe_enrich_query` exhaustifs ; assert log "PII scrubbed X/Y hits" sur chaque chat query. |
| 16 | CEFR `infer_level_from_errors` 50% threshold + mini-exam pass 0.75 sans CI | `pedagogy/consolidation.py:172-182` | Threshold 60% + ≥10 errors (Cepeda 2008 stability). Mini-exam 8 items binomial CI ±17% — implémenter re-test si score 5-6/8 marginal. |
| 17 | TOTP Fernet key rotation absente | `webapp/backend/app/totp.py:34` | Document strategy rotation annuelle + re-encrypt audit. Si key compromise → all TOTP broken silently. |

---

## 🟢 P2 — Améliorations long-terme (3-6 mois)

| # | Issue | Action |
|---|---|---|
| 18 | `error_log` unbounded growth | Monthly partitioning ou archival cron |
| 19 | CSP `'unsafe-eval'` + `'unsafe-inline'` (forced par SvelteKit hydration) | Investigate Svelte 5 nonce-based CSP |
| 20 | Frontend Core Web Vitals jamais mesurés | Activer Sentry browser SDK metrics + bundle budget CI |
| 21 | WCAG 2.2 AA audit | EAA 28 juin 2025 = microenterprise exempt (<10 employees + 2M€ CA, tu qualifies). Axe scan quarterly par hygiène. |
| 22 | `priority_concepts` weights manuels curriculum | Wire CEFR Companion 2020 frequencies + Hawkins-Filipović 2012 criterial features auto-derive |
| 23 | Smoke-test pas de couverture functional/oracle | `--deep` mode execute corpus-oracle subset 5 scenarios + sample chatflow JSON validation |
| 24 | LiteLLM cascade : Mistral rpm=2 bottleneck | Upgrade tier payant ou drop du fallback chain |

---

## 💡 Stratégique (réflexions produit, pas dette)

### A. Drop streak/XP, miser sur CEFR can-do checkpoints

**Source web research** : Pushwoosh 2025 edtech D30 <3% standard, Duolingo 8.5% conversion (effet leader non reproductible). Streak fatigue documenté (Duolingo a dû ajouter streak freeze −21% churn at-risk). Cible AcademIA = francophones adultes L2.
**Reco** : drop XP/gamification, garder Bayesian self-assessment + surface Dunning-Kruger mismatch comme insight pédagogique (Saito & Trofimovich 2020 longitudinal Japanese EFL : self-assessment training améliore calibration).
**Sources** : businessofapps.com/data/education-app-benchmarks/, thedecisionlab.com/insights/streak-creep, sciencedirect.com/science/article/abs/pii/S1041608020300297

### B. LiteLLM virtual keys hierarchy Org→Team→User

Avec décision Coach Sportif (backend dédié + LiteLLM mutualisé, cf [[coach-sportif-concept-2026-05]] D7), virtual keys per-app = budget caps cumulables daily+monthly per project. Évite cost overflow d'un projet sur l'autre.
**Setup** : ~30 min via LiteLLM admin UI.
**Sources** : docs.litellm.ai/docs/proxy/virtual_keys, /docs/proxy/multi_tenant_architecture

### C. Re-examiner positioning AI Act

Question stratégique avant **2026-08-02** : Teacher EN = "assistant conversationnel" ou "système d'évaluation" ?
- **Non-évaluatif** (façade publique) → échappe Annex III high-risk, économie compliance majeure
- **Évaluatif/placement test** → high-risk obligations (CE marking + risk mgmt + tech doc), 10-30j travail + €€€

Sébastien (avocat famille) potentiellement consultable.

### D. Microenterprise GDPR/EAA documentation

Documente solo dev <10 employees + <2M€ CA → exemption EAA art 4(4) confirmée. Garde papier prêt si auditeur demande. Hygiène compliance B2B future.

---

## TL;DR — 5 actions à shipper cette semaine

| # | Action | Effort | ROI |
|---|---|---|---|
| 1 | Fix logout auth bypass | 5 lignes Python | Sec critique |
| 2 | Rewrite rubrics A1/A2/B1 positive-only | 1-2h | Fix pink-elephant Lyster |
| 3 | Promote 3 A1 + author 3 C2 oracle scenarios | 1-2h | Débloque regression test rubric |
| 4 | Activer Anthropic prompt caching Dify→LiteLLM | 30 min config | -70-95% cost LLM immédiat |
| 5 | PgBouncer deploy | 1 jour | Débloque Coach Sportif scale |

**Total : ~2 jours de travail** pour amélioration cross-cutting (sécurité + qualité pédago + cost + scaling).

---

## Références sources

### Code paths critiques

- `webapp/backend/app/routers/auth_router.py` (logout, login, sessions)
- `webapp/backend/app/rate_limit.py` (in-memory token-bucket)
- `webapp/backend/app/routers/internal_router.py` (model-usage UPSERT)
- `webapp/backend/app/routers/admin_router.py` (cost_runaway_users)
- `webapp/backend/app/totp.py` (Fernet at-rest)
- `webapp/backend/app/pii_scrubber.py`
- `packages/academie-core/academie_core/pedagogy/teacher_prompt.py` (system prompt + dynamic sections)
- `packages/academie-core/academie_core/pedagogy/consolidation.py` (CEFR transitions)
- `packages/academie-core/academie_core/pedagogy/three_strikes.py`
- `packages/academie-core/academie_core/pedagogy/scaffolding_policy.py`
- `packages/academie-core/academie_core/data/rubrics/en.yaml` ⚠️ pink-elephant
- `packages/academie-core/academie_core/data/fewshots/en.yaml`
- `packages/academie-core/academie_core/data/l1_transfer/fr_to_en.yaml`
- `scripts/oracle/scenarios/teacher_en/` ⚠️ A1/C2 gap
- `scripts/oracle/config.yaml`

### Docs ADRs / pédagogie

- `docs/01-pedagogy/cefr-consolidation-policy.md`
- `docs/01-pedagogy/l1-l2-scaffolding-policy.md`
- `docs/01-pedagogy/oracle-v1-fault-injection-findings-2026-04-23.md`
- `docs/05-decisions/ADR-001-monolith-vs-microservices.md`
- `docs/05-decisions/ADR-002-schema-from-day-1.md`
- `docs/05-decisions/ADR-006-litellm-byok-familial.md`

### Vault knowledge

- [[MOC-architecture]], [[MOC-pedagogy]], [[MOC-academia-ia]]
- [[auth-patterns]], [[rgpd-compliance-toolkit]], [[dify-variable-wiring]]
- [[teacher-en-improvement-research]], [[oracle-harness-conventions]]

### Sources web normes 2025-2026

- AI Act art 50 + Annex III : artificialintelligenceact.eu, twobirds.com Code of Practice draft analysis
- CNIL plan 2025-2028 + IA recommendations + TIA guide Jan 2025
- CEFR CV 2020 : rm.coe.int (Council of Europe)
- Lyster meta-analyses : Lyster & Saito 2010 (15 études, 827 sujets), confirmé non-invalidé post-2010
- LLM tutor papers : GPTCoach arxiv 2405.06061, TeachLM arxiv 2510.05087, Training LLM tutors 2503.06424
- Edtech retention : businessofapps.com/data/education-app-benchmarks/, Pushwoosh 2025
- Anthropic prompt caching : platform.claude.com/docs/en/build-with-claude/prompt-caching
- LiteLLM virtual keys : docs.litellm.ai/docs/proxy/virtual_keys
- EAA microenterprise : twobirds.com/en/insights/2024/global/european-accessibility-act, taylorwessing.com/en/interface/2025/accessibility/

---

## Cross-references

- Parent MOC : [[MOC-academia-ia]]
- Voir aussi : [[teacher-en-improvement-research]] (Tier 1/2/3 roadmap research)
- Voir aussi : [[coach-sportif-concept-2026-05]] (D7 backend séparé + LiteLLM mutualisé impact action B stratégique)
- Sprint pending : `sprint-next-S60-decision-pending-2026-05.md` (5 options ROI)
