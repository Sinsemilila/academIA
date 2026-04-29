---
title: ADR-015 — Wave 3 JP productive evaluation strategy (JFS Standard + custom rubrics)
status: proposed
last_reviewed: 2026-04-29
decision_date: 2026-04-29
authors: [claude]
supersedes: null
related: [ADR-011-language-cefr-rationale, ADR-013-language-scope-by-tier]
---

# ADR-015 — Wave 3 JP productive evaluation strategy

## Contexte

Session 52 a ingéré 5 sources JP (4 JLPT 公式問題集 / Tsutsui mock / LogicStack reading drill) + 3 Makino dictionaries. **Découverte structurelle** lors literature notes drafting :

**JLPT (Japanese-Language Proficiency Test) ne teste QUE 2 macro-skills** :
1. Language Knowledge (vocabulary + grammar + reading)
2. Listening

JLPT **ne contient PAS** de production écrite ni orale. Asymétrie majeure vs autres certifications AcademIA target :

| Suite | Reading | Listening | Writing | Speaking | # macro-skills |
|---|---|---|---|---|---|
| **JLPT (JP)** | ✅ | ✅ | ❌ | ❌ | **2** |
| TORFL (RU) | ✅ | ✅ | ✅ | ✅ + Lex/Gram | 5 |
| DELE (ES) | ✅ | ✅ | ✅ | ✅ | 4 |
| Goethe-Zertifikat (DE) | ✅ | ✅ | ✅ | ✅ | 4 |
| CILS (IT) | ✅ | ✅ | ✅ | ✅ + Análisi | 5 |
| Cambridge English | ✅ | ✅ | ✅ | ✅ + UoE | 5 |

**Implication** : si AcademIA copie le pattern Wave 2 IT/DE/Wave 4 RU (= certif officielle comme authority anchor pour Lyster framework rubrics), Wave 3 JP n'a **aucune authority anchor productive**. Lyster T1-T4 cf-moves (recasts, elicitation, prompts, metalinguistic) supposent production learner observable — sans cela, framework s'appuie sur quoi ?

## Options envisagées

### Option A — Custom AcademIA rubrics productive (no authority anchor)

Designer rubrics writing/speaking JP-specifically en interne. Lyster T1-T4 + Hattie criteria + Cepeda spaced repetition appliqués sans authority externe.

- ➕ Indépendance, customizable précisément AcademIA Lyster framework
- ➖ Pas d'authority → judge variance non-grounded, +5-7j Wave 3 design rubrics
- ➖ Risque drift over time sans benchmark externe

### Option B — Cap formellement Wave 3 JP à receptive only

AcademIA JP teste juste reading+listening (cohérent JLPT). Production = "feature post-MVP" différée indéfiniment.

- ➕ Coût additionnel 0j, 100% authority-anchored (JLPT + JFS receptive)
- ➖ Product diminished vs RU/ES/IT (qui ont 4 skills)
- ➖ Voice features Whisper-class roadmap inutile JP en pratique
- ➖ Signalement régression marketing — "JP only reads/listens"

### Option C — JFS Standard 2010 + custom rubrics dérivés *(recommended)*

Adopter **JF Standard for Japanese-Language Education (2010)** comme authority anchor. Designed by Japan Foundation explicitly to extend JLPT receptive-only with **all 4 skills CEFR-aligned**, 6 niveaux A1-C2 publiquement documentés. Pas un exam authentique mais **authoritative descriptors framework** (équivalent fonctionnel `Profile Deutsch` pour DE).

JFS structure :
- 3 Stages × 2 sub-levels = A1/A2 (Beginner) / B1/B2 (Intermediate) / C1/C2 (Advanced)
- "Can-do statements" (CDS) ~440 descriptors couvrant production+reception
- Topics + Communicative Tasks definitions
- Self-assessment rubrics + portfolio approach

**Acquisition** : JFS website `jfstandard.jp` accès libre + livret PDF officiel gratuit (~120 pages)

- ➕ Authority anchor present (Japan Foundation own publication, post-JLPT modernization)
- ➕ 4 skills CEFR-aligned native (pas de bridge required)
- ➕ Cohérent ADR-013 RU cap A1-B2 — JFS A1-B2 subset directement applicable Wave 3 JP
- ➕ Cohérent L141 5-layer validation pipeline : JFS = Layer 1 authoritative curriculum (équivalent CILS Sillabo IT, Profile Deutsch DE)
- ➕ Effort ~3j Wave 3 Phase 1 (vs +5-7j Option A)
- ➖ JFS = descriptors framework, pas de scenarios/items concrets — il faut rules_jp.py + fewshots créer scenarios depuis CDS
- ➖ JFS unit-test kit not as comprehensive as Goethe Modellsätze

### Option D — Defer Wave 3 JP entièrement

Focus Wave 2 IT+DE + Wave 4 RU, JP en P3 horizon (août-décembre 2026 → 2027) si signal market.

- ➕ Risk-mitigated, focus on certifications-aligned langues
- ➖ Sources JP déjà acquises (5 PDFs + 3 dicts) en `dormant` — sunk cost
- ➖ Pas d'apprentissage org sur JP-specific pré-2027

## Décision

**Option C** — JF Standard 2010 + custom rubrics dérivés.

Drivers :
1. **Authority anchor disponible** : JFS = Japan Foundation own framework, équivalent fonctionnel Profile Deutsch / CILS Sillabo. Comble exactement le gap JLPT productive.
2. **Cohérent L141 5-layer validation pipeline** sans natifs : JFS Layer 1 + JLPT 公式問題集 Layer 2 (corpora) + Tae Kim/Imabi Layer 3 + LLM cross-validation Layer 4 + oracle Layer 5.
3. **Cohérent ADR-013 cap A1-B2** : utilise JFS subset A1-B2 (pas C1-C2 — voice tooling cap + market 95% B2).
4. **Effort raisonnable** : +3j Wave 3 Phase 1 pour acquisition+extraction JFS CDS (~440 descriptors → `cefr-can-do-jp.yaml`).
5. **Sunk cost respect** : 5 JP sources déjà ingérées Session 52 deviennent extractable Layer 2 dans pipeline cohérent (vs Option D où elles seraient dormantes).

## Conséquences

### Imminentes (Session 52+)

- **USAGE-MAP entry pour JFS Standard** : créer literature note stub `jfs-standard-2010-jp.md` status `stub-pending-acquisition` — Sinse acquisition manuelle (~30 min, free PDF)
- **Wave 3 JP recipe Phase 1** updated dans `vault/knowledge/teacher-creation-recipe.md` : Layer 1 source = JFS Standard (authority) + JLPT receptive items (corpus)
- **ADR-013 not impacted** : JP cap reste A1-B2 (= JFS A1-B2 subset)

### Wave 3 JP Phase 1 (P3 août-déc 2026)

- Extract `cefr-can-do-jp.yaml` from JFS A1-B2 CDS (~150-200 entries × 4 skills)
- Designer `rules_jp.py` 10 quick-win detectors (déjà documenté `multilang-japanese-research.md`)
- Designer `fewshots_jp/` register-stratified 200-300 cells (déjà documenté)
- LogicStack EPUB extraction (Layer 2 corpus N2 reading samples) — methodology source even if N2 above cap
- JLPT 公式問題集 N5+N4 receptive items extraction (Layer 2)
- 5-layer validation pipeline applied identically à EN/ES/IT/DE/RU pattern

### Risques mitigation

- **JFS may evolve** (JF revisions ~5-10 ans cycle) : tracker version `JFS-2010-rev-N` dans frontmatter literature note, audit annuel
- **Productive rubrics judge variance** : SGLang local Qwen3-8B `--enable-deterministic-inference` candidate (Sept 2025, déjà roadmap Tier 2 BIPED)
- **CEFR alignment JFS vs CEFR strict** : JFS uses CEFR levels but adapted JP context — peut diverger sur certains descriptors (e.g., "ren'yōkei" usage at JFS B1 vs CEFR B1). Cross-validation Layer 4 LLM tournée.

### Production roadmap réajusté

| Wave | Lang | Productive auth | Receptive auth | Effort Phase 1 |
|------|------|-----------------|----------------|----------------|
| 1 | ES | DELE | DELE | livré ~85% |
| 2 | IT | CILS Sillabo | CILS Quaderni | 13j |
| 2 | DE | Profile Deutsch | Goethe Modellsatz | 16j |
| 3 | JP | **JFS Standard** | JLPT 公式 | **~31j (28+3)** |
| 4 | RU | TORFL Methodology + Lazareva | TORFL Tests | 21j |

**Total Wave 2-4 = 81j** (vs 78j ADR-013, +3j JP JFS surcharge — acceptable).

## Status & validation

`proposed` — ouvert pour Sinse review/accept.

Validation triggers `accepted` :
1. Sinse acquisition JFS PDF (~30 min, jfstandard.jp gratuit)
2. Première extraction `cefr-can-do-jp.yaml` E2E sur ≥10 CDS (validation pattern reproducible)

Si Wave 3 JP démarrage retardé jusqu'à 2027+, ADR reste `proposed` jusqu'à activation. Pas de pression timeline (P3 horizon).
