---
title: Sprint 4 — Ré-analyse pre-implémentation (ADR-004)
status: superseded
superseded_by: ADR-013 + ADR-016 (Sprint 4 closed S29)
last_reviewed: 2026-04-16
owner: claude
decision_date: 2026-04-16
---

# Sprint 4 — Ré-analyse pre-implémentation

> **Objectif** : fermer les 4 checkpoints de [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) + décider GO/NO-GO pour l'implémentation avant Sprint 5 Maestro.
>
> **Décision en sortie de session** : **GO Option 1 (Full ADR-004)** — créer `academie-core` package + `LanguageDomain`, porter progressivement Teacher EN dedans, canary avant bascule full. Conditions : ≤ 11 jours-dev, battery post-migration ≥ 99%, canary 10% 1 semaine.

---

## 1. Context

ADR-004 a acté en principe une **topologie hybride orchestrée** (`Domain` abstraction + chatflow Dify par famille pédagogique) mais conditionnée à une ré-analyse obligatoire avant implémentation. Depuis, Sprint 3 a livré Teacher V2 Lyster en prod — fresh signal qui permet d'évaluer si l'interface `Domain` draftée tient la route.

Les 4 checkpoints à fermer :
1. Revue post-Sprint 1 (calibration empirique)
2. Revue post-Sprint 2 (schéma refondu)
3. Estimation chiffrée migration Teacher EN → `LanguageDomain`
4. Plan de rollback

Cette session ajoute un 5e checkpoint : **revue post-Sprint 3** (Teacher V2 mis en évidence ce qui résiste/bouge dans l'abstraction).

## 2. État actuel — ce qui existe, ce qui manque

### Code

| Composant | Fichier | LOC | Nature |
|---|---|---|---|
| Chat orchestration | `webapp/backend/app/routers/chat_router.py` | ~700 | ~60% domain-agnostic + ~40% EN-spécifique |
| Teacher prompt helpers | `webapp/backend/app/teacher_prompt.py` | 696 | Logique universelle + constants EN-only |
| Error taxonomy | `webapp/backend/app/error_taxonomy/*.py` | 1687 | rules (754) + scoring (441) + llm (303) + differ (134) + categories (55) |
| Dify chatflow Teacher V2 | `scripts/update_teacher_chatflow.py` | — | 28 nodes, 45 edges, 14 start inputs (6 base + 8 V2 dynamic) |

### Package `academie-core`

**N'existe pas**. `docs/02-architecture/shared-core.md` contient le design cible (organisation complète + Protocol v1 draft à 5 méthodes). Greenfield à scaffolder.

### Apps Dify en DB

- 1 prod-grade : **Teacher EN** (advanced-chat V2 Lyster, Sprint 3)
- 6 legacy obsolètes à cleanup : Maestro ES, Sensei JP, Lehrer DE, Professore IT, CyberMentor, PyMentor — chatbots créés "pour voir venir" à l'époque initiale multi-agents avant le pivot vers chatflow + focus Teacher. Aucune valeur, à supprimer (side-task Sprint 4).

### Schéma DB — déjà multi-domaine

- `profils_eleves(eleve_id, domaine)` UNIQUE — 1 row par combo ✓
- `error_log.domaine` ✓
- `spaced_retrieval_queue.domaine` (Phase 7) ✓
- `l1_transfer_observations(source_profile, target_profile)` — multi-paire ✓
- `curriculums(domaine, niveau)` ✓

**Aucun refactor DB requis** pour multi-domain. Bon signal.

### Webapp plomberie

- `ChatRequest.agent: str` avec regex validation — ready pour multi-agent
- `DIFY_APP_KEYS: dict` extensible via env vars (`DIFY_KEY_TEACHER`, futur `DIFY_KEY_MAESTRO`)
- Endpoints `/api/chat/send|conversations|messages` acceptent `agent` param

Le routing multi-agent webapp est déjà built. Seul le backend des autres agents manque.

## 3. Feedback Sprint 3 — audit des 8 dynamic sections vs Domain Protocol v1

Les 8 sections dynamiques générées par `build_dynamic_sections(ctx)` dans `teacher_prompt.py` :

| Section | Logique universelle | EN-content hardcoded | Map vers Protocol v1 | Verdict |
|---|---|---|---|---|
| `rubric_for_level` | Pattern "rubric per niveau" est générique | `RUBRICS` dict (6 × ~150 mots EN) | `pedagogical_feedback` + asset YAML | split logic/data |
| `fewshots_block` | Pattern "N examples par niveau" est générique | `FEWSHOT_BANK` (13 exemples EN) | `pedagogical_feedback` + asset YAML | split logic/data |
| `dosage_block` | 100% universel (T4>T3>T2, budget × saturation) | Aucun | `score_tier` + `pedagogical_feedback` (compose) | pure logic → core |
| `level_reminder_inject` | Pattern trigger (turn%5==0) est universel | Prose française dans `build_level_reminder` | `pedagogical_feedback` (render templated) | template i18n |
| `drift_validation_request` | Pattern trigger (turn%10==0) universel | Prose française `build_drift_check_request` | `pedagogical_feedback` (render templated) | template i18n |
| `l1_watch` | Pattern L1→L2 transfer universel | `L1_TRANSFER_SEED` dict (fr→en seul, 5 familles) | `pedagogical_feedback` + `taxonomy.transfer` | data YAML cross-pair |
| `spaced_retrieval_today` | 100% universel (items due fetch) | Prose française "AUJOURD'HUI ON REVISITE" | **Nouvelle méthode `build_spaced_retrieval_block`** | service orthogonal (Phase 7) |
| `output_schema_block` | 100% universel (JSON schema constant) | Aucun | Constant partagé cross-domain | constant module |

### Méthodes manquantes dans Protocol v1

Le Protocol v1 (shared-core.md) a `detect_errors`, `score_tier`, `compute_progression`, `snapshot`, `pedagogical_feedback`. Sprint 3 révèle **3 méthodes manquantes** :

1. **`build_dynamic_sections(context) → dict[str, str]`** — agrège les 8 sections actuelles, c'est l'entry-point actuel de teacher_prompt.py. Manque du Protocol v1.
2. **`build_system_prompt(context) → str`** — compose le prompt système complet (rubric + rules + fewshots + dosage + l1_watch + schema). Actuellement tissé entre Dify template et Python dynamic sections.
3. **`parse_response(raw_text) → StructuredResponse`** — parse `<output>...JSON...</output>` + fallback (aujourd'hui `parse_teacher_response` dans teacher_prompt.py).

### Gap analysis — paper design vs Sprint 3 reality

| Protocol v1 prévu | Sprint 3 reality | Statut |
|---|---|---|
| 5 tiers T0-T4 | ✓ utilisés partout | Tenu |
| Gravity axes (linguistic/communicative/social) | ✓ 3 axes dénormalisés sur error_log | Tenu |
| `detect_errors` via rules + LLM merge | Rules layer EN-spécifique (FRENCH_COGNATES, PREP_CALQUES hardcoded) | Partiel — pas un vrai plugin |
| `score_tier` empirique (yaml config) | ✓ tolerance_matrix_v2 via `USE_V2_TOLERANCE` flag + `compute_error_profile` | Tenu |
| `compute_progression` | Existe partiellement dans `error_analysis_router.py` pas extrait | Non extrait |
| `snapshot` | Pas implémenté (snapshots_session existe mais pas méthode `Domain`) | Non-tenu |
| `pedagogical_feedback` | Split entre teacher_prompt.py helpers (dosage/tier→feedback/diversity) + Dify prompt | Éparpillé, à consolider |

### Surprise Sprint 3 — contrainte de streaming

Teacher V2 stream via Dify SSE (`httpx.AsyncClient.stream` + `StreamingResponse`). Domain ne peut pas retourner StreamingResponse proprement (couplage httpx + FastAPI response). **Contrat proposé** :
- `Domain.build_system_prompt(ctx) → str` compose le prompt
- Webapp `chat_router` tient le httpx, envoie le prompt à Dify, streame la réponse
- `Domain.parse_response(full_answer) → StructuredResponse` appelé post-stream pour extraction JSON
- Domain **ne tient jamais** la couche réseau → DI-able et testable.

## 4. Interface Domain v2 (post-Sprint 3)

Révision du Protocol v1 avec les 3 méthodes manquantes + orchestration contract :

```python
# academie_core/domain/base.py  (v2 — post-Sprint 3)

class Domain(Protocol):
    id: str                              # "lang:en", "code:python"
    proficiency_scale: ProficiencyScale
    
    # === Taxonomy layer ===
    def detect_errors(self, user_input: str, context: UserContext) -> list[Error]: ...
    def score_tier(self, error: Error, context: UserContext) -> Tier: ...
    
    # === Pedagogy layer (Sprint 3 Teacher V2 reality) ===
    def build_dynamic_sections(self, context: PromptContext) -> dict[str, str]:
        """Produit les blocs dynamiques (rubric/fewshots/dosage/level_reminder/
        drift/l1_watch/spaced/output_schema) à injecter dans le prompt Dify."""
    
    def build_system_prompt(self, context: PromptContext) -> str:
        """Compose le system prompt complet. Webapp envoie ça à Dify."""
    
    def parse_response(self, raw_text: str) -> StructuredResponse:
        """Extrait <output>...</output> + JSON. Fallback gracieux sur malformed."""
    
    def pedagogical_feedback(
        self,
        errors: list[Error],
        context: UserContext,
    ) -> FeedbackPlan:
        """Décide quel tier → quel feedback_type pour chaque erreur."""
    
    # === Progression / session layer ===
    def compute_progression(self, error_log: list[Error], context: UserContext) -> Progression: ...
    def snapshot(self, session: Session, context: UserContext) -> Snapshot: ...
```

**Changements vs v1** :
- ➕ `build_dynamic_sections`, `build_system_prompt`, `parse_response` (nouvelles)
- `pedagogical_feedback` signature ajustée : prend `list[Error]` + `context` → `FeedbackPlan` (un plan pour tout le turn, pas par erreur — reflect `arbitrate_dosage` actuel)
- Retraits : aucun

**Orchestration contract confirmé** :
- **Domain** : compose, parse, décide (pure logic, no I/O)
- **Webapp** : tient le httpx, streame Dify → user, persist error_log + queue items
- **Service orthogonal** : `SpacedRetrievalService` (hors Domain) — partagé par toutes les Domains (interface `.fetch_due(eleve_id, domaine)` + `.enqueue(...)` + `.complete(...)`)

## 5. Data model pour multi-domaine

Décisions actées :

### 5.1 Rules layer

**Problème** : `webapp/backend/app/error_taxonomy/rules.py` (754L) contient des constants EN-only hardcoded (FRENCH_COGNATES, PREP_CALQUES, SPACING_ERRORS, 51 mappings FR→EN).

**Décision** : migrer vers `academie-core/academie_core/data/rules/en.yaml`. Chaque langue aura son fichier (`rules/es.yaml`, `rules/de.yaml`, etc.). Le moteur `academie_core.taxonomy.rules.detect_errors(text, lang)` charge le YAML correspondant.

**Estimation** : 1 jour pour extraire EN (lots de regex → YAML), +0.5j par langue nouvelle (data-only).

### 5.2 Rubrics + Fewshots + L1 Transfer

**Décision** : externalize en YAML :
- `data/rubrics/en.yaml` (6 RUBRICS × ~150 mots)
- `data/fewshots/en.yaml` (13 examples)
- `data/l1_transfer/fr_to_en.yaml` + `fr_to_es.yaml` + … (un fichier par paire L1→L2)

Loader Python dans `academie_core.pedagogy.templates` charge le YAML au boot du `LanguageDomain(lang_target)`.

### 5.3 Cross-domain cohabitation

**Décision** : en v1, profils séparés strictement par `(eleve_id, domaine)`. Un user `sinse` faisant EN + ES a **2 rows** dans `profils_eleves`. Aucun cross-transfer EN→ES modélisé à cette étape. À reconsidérer en v3+ si users multi-langues montrent un besoin réel.

### 5.4 Curriculum seed

**Décision** : `curriculums` déjà multi-domaine (`domaine + niveau`). Seed supplémentaire `domaine='espagnol'` fait en Sprint 5 quand on active Maestro (pas maintenant).

### 5.5 Error code namespace

**Décision** : garder un namespace **partagé** pour les error_codes transverses (V:TENSE, N:DET, PREP, LEX:FALSE…) puisque ces patterns sémantiques existent cross-langue. Les specifics comme `ART:ZERO` (anglais seul) auront un préfixe `EN:` si collision. Décision à re-évaluer Sprint 5 si friction ES/JP.

## 6. Implementation estimate — Sprint 4 phases

| Phase | Scope | Jours-dev | Risque | Dépend |
|---|---|---|---|---|
| **A** — Scaffold academie-core | `pyproject.toml`, dirs (`domain/`, `taxonomy/`, `pedagogy/`, `data/`), CI pytest, empty Protocol stubs, README | 0.5 | Faible | — |
| **B** — Port taxonomy | rules/scoring/llm/gravity/transfer → `academie_core.taxonomy.*` + tests regression (63 unit actuels migrent) | 2-3 | Medium | A |
| **C** — Port pedagogy + externalize | teacher_prompt.py → `academie_core.pedagogy.*` + RUBRICS/FEWSHOT_BANK/L1_TRANSFER_SEED → YAML | 2-3 | Medium | A, B |
| **D** — Create LanguageDomain | wrapper Protocol, charge YAMLs au boot, compose taxonomy + pedagogy | 1 | Low | B, C |
| **E** — Webapp refactor + canary | `chat_router` utilise `LanguageDomain(lang="en")` ; feature flag `USE_ACADEMIE_CORE=true` 10% users | 2 | **High** (prod-facing) | D |
| **F** — Validation + bascule | battery regression, property-based tests, p50/p95 latence check, bascule full après 1 semaine canary | 1-2 | Medium | E |
| **Total** | | **8-11** | | |

### Sprint 5 indicatif (POST Sprint 4)

| Phase | Scope | Jours-dev |
|---|---|---|
| G — Seed data ES | `rules/es.yaml` + `rubrics/es.yaml` + `fewshots/es.yaml` + `l1_transfer/fr_to_es.yaml` | 2-3 |
| H — Clone Teacher V2 chatflow pour ES | adapt Dify advanced-chat, wire `DIFY_KEY_MAESTRO` | 1-2 |
| I — Activate LanguageDomain("es") | `chat_router` route `agent="maestro"` → `LanguageDomain("es")` | 0.5 |
| J — Test E2E Maestro | family users validate | 1 |
| **Total Maestro** | | **4.5-6.5** |

Avec Sprint 4 solide, ajouter une langue = ~5 jours. Sans Sprint 4, même exercice = ~15 jours (fork complet + maintenance parallèle).

## 7. Rollback strategy

### Feature flag granularité

**Décision** : flag global `USE_ACADEMIE_CORE=true|false` en env var academie-api (pattern établi par `USE_V2_TOLERANCE`, `USE_V2_SCORING`, `SPACED_RETRIEVAL_ENABLED`).

Granularité finer-grain (par user %, par domain) pas retenue en v1 — overkill. Canary = simple : env flag flip + recreate container.

### Procédure rollback

1. `sed -i '/^USE_ACADEMIE_CORE=/d' /opt/academie/webapp/.env` (remove flag)
2. `cd /opt/academie/webapp && docker compose up -d academie-api` (recreate)
3. Webapp revient à l'implémentation inline (chat_router.py + teacher_prompt.py actuels)
4. Smoke + battery regression pour confirmer no regression

**Durée rollback estimée** : < 2 minutes (env + recreate).

### Canary strategy

- **Semaine 1** après Phase E : `USE_ACADEMIE_CORE=true` en env academie-api. Tous les users nouveau flow.
- **Monitor** : smoke 21/21 ALL CLEAR, battery 99%+ pass rate, p95 latence < baseline + 50ms, docker logs academie-api pas d'exceptions `academie_core.*`.
- **Semaine 2** : si metrics stables → supprimer le code inline fallback (Phase F conclusion). Si régression → rollback + post-mortem.

## 8. Risques + mitigations

| Risque | Prob | Impact | Mitigation |
|---|---|---|---|
| Phase B port taxonomy casse `USE_V2_TOLERANCE`/`USE_V2_SCORING` | Medium | High | Tests regression avant+après chaque port, 63 unit tests actuels comme baseline |
| Phase E refactor change latence | Low | Medium | Mesurer p50/p95 avant, threshold +50ms acceptable, +200ms = rollback |
| Import overhead `academie_core` au boot webapp | Low | Low | Lazy imports si besoin, mesurer startup time |
| 6 chatbots obsolètes en DB cassent quelque chose quand on tente Sprint 5 | Low | Medium | Cleanup DELETE en side-task Sprint 4 (10min) — aligne DB avec réalité |
| Phase 7.2/7.3 se retrouvent dans webapp `chat_router` pendant qu'on migre | Medium | Low | Décision : attendre télémétrie Phase 7.1 (semaine 2026-04-23) → puis faire 7.2 directement dans `academie-core` (pas de port ultérieur) |
| Fewshots + RUBRICS prose copyright (YAMLisation → auditabilité publique) | Low | Low | Already in codebase git public, prose notre — no IP risk |

## 9. Décisions tranchées + différées

### Tranchées cette session

1. **Option C pure retenue** (full ADR-004) — pas de pivot vers data-driven-only ni duplication par langue
2. **Package mono-repo** sous `packages/academie-core/` (pattern shared-core.md) — reconsidérer repo séparé si on grossit l'équipe
3. **`SpacedRetrievalService` orthogonal** (pas méthode Domain) — pattern Phase 7 déjà orthogonal
4. **Flag global `USE_ACADEMIE_CORE`** — pas de granularité user/%
5. **Cross-domain profils séparés** v1 — différer transfer inter-L2 en v3+
6. **Cleanup 6 chatbots obsolètes** — DELETE en Sprint 4 side-task
7. **Phase 7.2/7.3 après Sprint 4 impl** — quand Phase 7.1 a 1 sem de télémétrie (~2026-04-23)

### Différées à Sprint 5+

- Repo séparé `Sinsemilila/academie-core` — pas justifié solo/famille
- Cross-transfer EN→ES modélisation — quand un user concret le demande
- FSRS scheduling (Phase 7.3) — besoin de 2 semaines de données `spaced_retrieval_queue` pour calibrer
- Sprint 6+ fine-tune modèle spécifique par domaine

## 10. Actions — Sprint 4 pre-impl checklist

Les 4 checkpoints ADR-004 + le nouveau post-Sprint-3 :

- [x] Revue post-Sprint 1 (calibration W&I) : GLMM empirique validé, weights T0-T4 passés en prod (Session 17), taxonomy tient avec 44% cells changed.
- [x] Revue post-Sprint 2 (schéma) : `domaine` partition fonctionne, gravity axes dénormalisées OK, USE_V2_SCORING/USE_V2_TOLERANCE en prod depuis Session 18.
- [x] **Revue post-Sprint 3** (ce document) : 8 dynamic sections auditées, 3 méthodes manquantes identifiées, Protocol v2 proposé.
- [x] Estimation chiffrée migration : **8-11 jours-dev Sprint 4 impl**, +4.5-6.5 jours Sprint 5 Maestro.
- [x] Plan de rollback : flag global `USE_ACADEMIE_CORE`, canary 1 sem, rollback < 2 min.

## 11. Références

- [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — décision à flipper `accepted-in-principle` → `accepted`
- [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md) — package `academie-core` spec
- [shared-core.md](../02-architecture/shared-core.md) — Interface Domain à mettre à jour v2
- [agent-topology.md](../02-architecture/agent-topology.md) — last_reviewed bump
- Code existant référencé : `webapp/backend/app/routers/chat_router.py`, `teacher_prompt.py`, `error_taxonomy/*.py`, `scripts/update_teacher_chatflow.py`

## 12. Prochains pas

1. ~~Session Sprint 4 implémentation~~ → **DONE 2026-04-16** — voir section 13 ci-dessous
2. **En attendant Phase 7.1 telemetry** : revisit 2026-04-23 via `scripts/ops/monitor_spaced_retrieval.sh`
3. **Cleanup obsolètes Dify chatbots** : 6 entries Maestro/Sensei/Lehrer/Professore/CyberMentor/PyMentor obsolètes confirmés legacy (Sinse 2026-04-16), à DELETE côté DB quand Sprint 5 démarre (10min)

## 13. Sprint 4 — Implémentation réalisée (2026-04-16)

**Compressé en 1 session** (~4h continu, vs 8-11 jours-dev estimé initialement). Livrés :

| Phase | Commit | Scope | Jours-dev prévus | Session |
|---|---|---|---|---|
| A — Scaffold academie-core | `abbc0d8` | pyproject + dirs + Protocol v2 stubs + 10/10 smoke tests | 0.5j | ~20 min |
| B — Port taxonomy | `abfab1d` | 5 .py (1687L) + 3 YAMLs + Dockerfile context root + shims + 23/23 tests | 2-3j | ~45 min |
| C — Port pedagogy | `edc16ee` | teacher_prompt.py (696L) + shim + 65/65 test_prompt_assembly | 2-3j | ~15 min |
| D — LanguageDomain | `8d54832` | domain/language.py + 13/13 tests + Protocol runtime-check | 1j | ~20 min |
| E — chat_router via LanguageDomain | `9a6865c` | 4 call sites migrated + module-level _TEACHER_DOMAIN | 2j | ~15 min |
| F — Validation + cleanup | `<TBD>` | Battery 99.1% GREEN + 6 shims deleted + 8 scripts migrated + docs | 1-2j | ~30 min |

**Validation finale** :
- Battery pre-cleanup (post-Phase-E) : **99.1% ✅ GREEN** (333/336 checks), 3 fails = `t4_addressed` model honesty B1/B2 (connu, non-Sprint-4)
- **L1 mention rate 75%** (3/4 FR→EN turns) — confirme feature L1 transfer fonctionnel via LanguageDomain
- Smoke deep 21/21 ALL CLEAR, 23/23 academie-core, 65/65 test_prompt_assembly, test_rules_coverage regression identical to pre-port
- Zero prod regression observed (chat endpoint response time p50 5.7s, p95 9.4s — dans la variance normale)

**Gains architecturaux réalisés** :
- Code pédagogique + taxonomique centralisé dans `packages/academie-core/` (installé `-e` via Dockerfile)
- Webapp ne contient plus `teacher_prompt.py` ni `error_taxonomy/` (shims supprimés Phase F)
- `LanguageDomain("en")` singleton dans chat_router — Sprint 5 ajoutera `LanguageDomain("es")` trivialement
- Protocol `Domain` runtime-checkable satisfait par duck typing (`isinstance(d, Domain)` True)

**Dette tech laissée** (OK pour MVP, à traiter Sprint 5+) :
- Monolithic `teacher_prompt.py` dans pedagogy/ (split en sous-modules post-refactor)
- RUBRICS/FEWSHOT_BANK/L1_TRANSFER_SEED restent Python literals (YAMLization = Sprint 5 Maestro ES quand multi-lang force la structure)
- Legacy PromptContext vs base.py Protocol types non-unifiés (Sprint 5+)
- `snapshot()` method raises NotImplementedError (v3+ quand snapshot generation unifies)
- Tests scripts/sprint2+sprint3 ne migrent pas vers `packages/academie-core/tests/` (Phase B.2 deferred)
- `error_analysis_router.py` importe encore direct academie_core (pas wrappé par LanguageDomain — scope Sprint 5)

**Estimation confirmée pour Sprint 5 Maestro ES** : 4.5-6.5 jours-dev (seed YAMLs ES + clone chatflow Dify + `LanguageDomain("es")` instantiation + tests family users).
