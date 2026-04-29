---
title: ADR-014 — Structured knowledge extraction from canonical books
status: accepted
last_reviewed: 2026-04-29
decision_date: 2026-04-29
authors: [sinse, claude]
---

# ADR-014 — Structured knowledge extraction from canonical books

## Contexte

Session 51 a compilé une bibliographie exhaustive (~502 livres / 4 fichiers vault `bibliography-*.md`). Sinse acquiert progressivement les ~15 livres canoniques prioritaires identifiés (Wave blockers + SLA framework + assessment design).

**Question structurelle** : comment exploiter ces livres pour AcademIA au-delà d'une lecture humaine + pointers vault ?

3 patterns évalués Session 51 :

| Pattern | Description | Verdict |
|---|---|---|
| **Layer 1** | Vault literature notes (humain-readable + Claude pointers) | ✅ accepté (already implemented `/library-ingest`) |
| **Layer 2** | pgvector dev-time RAG corpus (Claude code work queries embeddings) | ❌ rejeté — ROI marginal, ~10-30 queries/Wave estimés ne justifie pas 3-5j setup + maintenance |
| **Layer 3** | pgvector prod-time RAG (Teacher retrieval at runtime) | ❌ rejeté — Tier 2 BIPED + LoRA Tier 3 sont 10× plus leverage que RAG add-on, current fewshots curated suffisent grounding |
| **Layer 1.5** | Structured YAML extraction code-injectable | ✅ **accepté — pattern principal** |

## Décision

**Adopter Layer 1.5 — structured extraction des livres canoniques en YAML directement consommables par `rules.py` / `tolerance_matrix` / `fewshots` / `dosage_block` / `mini_exam` builders.**

Path canonique : `packages/academie-core/academie_core/data/extracted/<book-slug>/<extraction-name>.yaml`

Counterpart vault `vault/knowledge/books/<book-slug>.md` reste literature note humain-readable.

## Pattern d'extraction

### Triggered by code work, not anticipated batch

Extraction se fait **lazy** quand un besoin code identifié émerge :

| Trigger | Extraction probable | Source livre |
|---|---|---|
| Implementing `rules_de.py` | b1-can-do-statements + grammar-required-de | Profile Deutsch |
| Implementing `rules_it.py` | it-grammar-by-level + cils-error-patterns | CILS Sillabo |
| Implementing `rules_jp.py` | jlpt-grammar-points + register-stratification | JLPT 公式問題集 |
| Implementing `rules_ru.py` | torfl-syllabus + aspect-case-patterns | TORFL TEU/TBU |
| Tier 2 BIPED prompt design | cf-taxonomy + counterbalanced-principle | Lyster 2007 |
| Curating fewshots CEFR×move | recast-cefr-appropriateness | Lyster 2007 + Lightbown/Spada |
| Building `mini_exam_<lang>.yaml` | exam-grammar-items per level | CILS / JLPT / TORFL official materials |
| Dosage_block ordering | acquisition-stages per phenomenon | Pienemann 2005/1998 |
| Vocabulary acquisition Cox model | frequency-tiers + collocation-patterns | Nation 2013 |
| Judge rubric design | implicit-explicit-gradient | Ellis 2009 |

### Schema-validated YAML

Chaque type d'extraction a un schema dans `extracted/_schemas/`. Schemas initialement créés :
- `cf-taxonomy.schema.yaml` (Lyster CF moves + CEFR appropriateness)
- `acquisition-stages.schema.yaml` (Pienemann teachability stages per language)
- `cefr-can-do.schema.yaml` (Profile Deutsch / CILS / JLPT / TORFL can-do + grammar required)

Nouveaux schemas ajoutés au fur à mesure (ex: vocabulary-frequency-tiers, exam-grammar-items, register-stratification).

### Citation-anchored

Chaque entry YAML extracted MUST inclure :
- `source` : `"<Author Year>, ch X, pp. Y-Z"` traceable
- `extracted_by` : `claude | sinse_manual | hybrid`
- `extracted_date` : `YYYY-MM-DD`
- `confidence` : `high (direct quote/table) | medium (paraphrase) | low (inferred)`

## Justification

### Layer 1.5 vs Layer 2 (RAG dev-time)

| Critère | L1.5 structured | L2 RAG dev-time |
|---|---|---|
| Précision | Exact (parsed structure) | Flou (embedding retrieval) |
| Code-injectable | Oui directement | Non (LLM intermediation requise) |
| Versionné git | Oui | Non (DB) |
| Testable unit tests | Oui (YAML schema validation) | Difficile |
| Cohérent archi rules-as-code | 100% (s'inscrit dans pattern existant data/) | Partiel |
| Effort par livre | 1-2j Claude extraction targeted | 0.5j chunk+embed batch |
| ROI utilisation | Code injecté immédiatement | Queries ad-hoc, value flou |

### Layer 1.5 vs Layer 3 (RAG prod-time)

Layer 3 ajoute latency runtime (+200-500ms) + tokens injection (1-2K/tour) pour edge cases meta-grammaticaux marginaux. Architecture actuelle Teacher (system prompt + dosage_block + fewshots stratifiés CEFR×move + L1 transfer + scaffolding) couvre déjà les use cases routine. L1.5 alimente directement ces structures sans round-trip retrieval.

### Cohérence architecturale AcademIA

L'architecture actuelle est **rules-as-code + curated structured data** (cf `tolerance_matrix.yaml`, `l1_transfer/*.yaml`, `fewshots/*.yaml`, `curriculum_*.yaml`, `mini_exam/*.yaml`). Layer 1.5 = **autre source de structured data** alimentant les mêmes consumers. Aucun nouveau paradigme infra (pas de DB vector, pas de retrieval middleware, pas de chunking strategy à choisir).

## Conséquences

### Positives

- **Knowledge from books devient versionned, testable, audit-able** (git diff sur extraction = traçable)
- **Solo dev sans native speakers** continue d'avoir une validation pipeline 5-layer cohérente (cf ADR + L141) — Layer 1 authoritative curricula extracted explicitly
- **Wave 2-4 unblocked** : Profile Deutsch/CILS/JLPT/TORFL extracted feeds directly into rules + curriculum + mini_exam
- **Audit triviale** : annual review check `grep -r "load_extracted" packages/` → si extraction jamais consommée 6+ mois, candidate removal (cohérent vault L116 audit pattern)

### Négatives / Risques

- **Effort cumulé** : ~1-2j Claude par livre canonique × 10-15 livres = ~10-25j cumulé sur 6-12 mois. À répartir lazy au fur à mesure des Waves.
- **Lossiness** : structured YAML ne capture pas la nuance prose des chapters (Sinse lecture humaine reste valeur unique pour rationale/intuition)
- **Maintenance schema** : si un schema doit évoluer breaking-change, migration requise (mitigation : `schema_version` field permet branches loader)

### Limitations explicit

- **Pas de RAG runtime prévu** dans cette ADR. Si un besoin futur émerge (ex: meta-questions learner non-couvertes par fewshots), revisiter avec ADR séparée.
- **Reference grammars + frequency dicts skip** : extraction trop coûteuse vs ROI (PDFs restent reference lookup, pas extraction systématique)

## Alternatives considérées (rejetées)

### Alt A — Acquisition + lecture humaine seule (no Claude extraction)

- Pour : zéro effort Claude, vault literature notes pointer suffit
- Contre : Sinse seul ne peut pas physiquement lire 15 livres × 30h = 450h sans bottleneck. Knowledge reste enfermé PDF, code work doit re-Read on-demand chaque fois (cher).

### Alt B — RAG dev-time (Layer 2 seul)

Cf décision principale. Rejeté ROI marginal.

### Alt C — RAG prod-time (Layer 3 seul)

Cf décision principale. Rejeté leverage faible vs Tier 2 BIPED.

### Alt D — Hybrid all 3 layers

- Pour : exhaustif
- Contre : sur-engineering pour solo dev, doc-théâtre risk (cohérent CLAUDE.md anti-pattern), maintenance combinatoire

## Cross-references

- **ADR-013** : language scope by tier (EN+ES flagship A1-C2, IT+DE+JP+RU essential A1-B2) — extracted YAMLs respectent ce scope par défaut
- **ADR-009** : gravity axes schema (taxonomy framework) — extracted CF taxonomy aligne
- **ADR-005** : academie-core shared library — `extracted/` vit dans `packages/academie-core/academie_core/data/`
- **L141** : 5-layer validation pipeline solo dev sans native — extraction = Layer 1 (authoritative curricula) traçable
- **CLAUDE.md vault** : pattern direct-write knowledge/ (Session 51 L139) — extraction folder cohérent
- **Vault literature notes** : `/root/sinse-vault/knowledge/books/` (counterpart humain-readable)
- **Slash command** : `/library-ingest` (handles literature note creation; structured extraction triggered separately by code work)

## Statut

**Accepted 2026-04-29.** Implementation initiale : folder structure + 3 schemas examples (cf-taxonomy, acquisition-stages, cefr-can-do) + README pattern doc + literature note template updated.

Première extraction réelle attendue lors du prochain code work consumer (probablement Wave 2 IT démarrage OR Tier 2 BIPED prompt design, ~Mai 2026).

Annual review : 2027-04-29 — check usage `load_extracted` consumers, prune extractions jamais consommées 12+ mois.
