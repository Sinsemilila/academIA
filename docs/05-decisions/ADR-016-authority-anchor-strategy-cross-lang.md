---
title: ADR-016 — Authority anchor strategy cross-lang (all-in 5-layer pipeline EN+ES+IT+DE+JP+RU)
status: proposed
last_reviewed: 2026-04-29
decision_date: 2026-04-29
authors: [sinse, claude]
supersedes: null
related: [ADR-013-language-scope-by-tier, ADR-014-structured-knowledge-extraction, ADR-015-jp-productive-evaluation-strategy]
---

# ADR-016 — Authority anchor strategy cross-lang

## Contexte

Session 52 a révélé un gap structurel dans le 5-layer validation pipeline (L141 canonique solo dev sans natifs) :

- **DE/JP/RU/IT** (Wave 2-4) : authority anchors prévus (Profile Deutsch, JFS Standard, TORFL Pushkin, CILS Sillabo)
- **EN/ES** (flagship A1-C2) : **PAS d'authority anchor** historiquement. Designed "à l'instinct + Lyster framework + Lightbown/Spada SLA general"

**Conséquence** : pipeline 5-layer asymétrique — DE/JP/RU/IT à 5 layers, EN/ES à 4. Méthodologie incohérente. Risque marketing/credibility ("designed against authority" plus solide commercialement).

**Justification historique EN/ES sans authority** :
1. **Sunk cost** : EN livré 100% Wave 0, ES Wave 1 ~85%. Tout designé sans authority anchor.
2. **Sinse bilingue FR/EN + bon ES** : validation native directe possible (layer humain implicit), justifie 4-layer suffisant.
3. **DE/JP/RU/IT** : Sinse non-natif, pas de validation directe → 5-layer obligatoire.

Mais cette justification ne tient plus si on vise **uniformité méthodologique cross-lang** + scaling future (équipe non-Sinse-bilingue rejoint, ou pivot collaborateurs).

## Décision

**Adopt all-in authority anchor strategy** : chaque langue AcademIA a son authority anchor formel, pipeline 5-layer uniforme.

### Authority anchor map par langue (Session 52 acquis)

| Lang | Tier | Authority anchor primary | Source | Status |
|------|------|--------------------------|--------|--------|
| **EN** flagship A1-C2 | T1 | **English Profile** (Hawkins/Filipović 2012 *Criterial Features in L2 English*) | Cambridge UP, English Profile Studies | ✅ acquired |
| **ES** flagship A1-C2 | T1 | **Plan Curricular del Instituto Cervantes (PCIC)** A1-A2 + B1-B2 | Cervantes Institute, free | ✅ acquired (C1-C2 missing — gap signalé) |
| **IT** essential A1-B2 | T1 | **CILS Sillabo per livello** (Università per Stranieri Siena) | Guerra Edizioni / online | 🤖 stub-pending-acquisition |
| **DE** essential A1-B2 | T1 | **Profile Deutsch v2.0** (Glaboniat et al. 2005) | Langenscheidt | ✅ acquired |
| **JP** essential A1-B2 | T1 | **JF Standard 2010** + **Marugoto coursebook series** A1→B1 (per ADR-015) | Japan Foundation, free + commercial | ✅ acquired (B2 gap signalé — Tobira/Quartet candidates) |
| **RU** essential A1-B2 | T1 | **TORFL Lexical/Grammatical Minimums** (Pushkin Institute) Gosstandart syllabi TEU/TBU/TRKI-1/TRKI-2 | Pushkin / Zlatoust | 🤖 stub-pending-acquisition (sanctions affectent shipping) |

### Cross-language umbrella anchor

**CEFR Companion Volume 2020** (Council of Europe) = authority anchor cross-lang **transverse**. Updated baseline tous langues. Référence pour validation cohérence inter-langues (descriptors A1-C2 mass).

✅ acquired Session 52 batch 2.

### Pipeline 5-layer post-ADR-016 uniforme

Pour chaque langue (EN/ES/IT/DE/JP/RU), validation methodology :

1. **Layer 1 — Authoritative published curricula** : authority anchor de la table ci-dessus
2. **Layer 2 — Error-tagged learner corpora** : MERLIN/EFCAMDAT/SPLLOC/I-JAS/RLC selon lang
3. **Layer 3 — Academic SLA research** : Lightbown/Spada, Lyster, Pienemann, Ortega, DeKeyser
4. **Layer 4 — LLM cross-validation** : GPT-4o + Claude + Gemini
5. **Layer 5 — Oracle harness behavioral** : test battery sur scenarios live

## Conséquences

### Imminent (Session 52+)

- Literature notes shipped pour 13 authority anchors per-lang + 4 multilang umbrella ✅
- USAGE-MAP/INDEX bulk update ✅
- ADR-013 + ADR-015 reste cohérent (cap A1-B2 IT/DE/JP/RU + flagship A1-C2 EN/ES)

### Phase 1 — EN/ES audit (P1 mai-juin 2026, ~3-5j chacun)

**Pas un rework from scratch**. Audit ciblé "validate against authority" :

- **EN audit** : extract Hawkins/Filipović 2012 CDS + English Vocabulary Profile + English Grammar Profile (online lookup). Compare avec `cefr-can-do-en.yaml` actuel + scenarios EN AcademIA. Flag divergences > 15% comme cibles fix.
- **ES audit** : extract PCIC A1-A2 + B1-B2 inventario nocional/funcional/gramatical. Compare avec `cefr-can-do-es.yaml` + scenarios ES. Flag divergences.

Effort total : ~6-10j cumulés. Output : `[fix] curriculum_en/es — align with authority` commits granulaires.

### Phase 2 — Wave 2 IT+DE+RU (P2 mai-juillet 2026)

Build with full pipeline 5-layer :
- IT : CILS Sillabo Layer 1 + CILS Quaderni Layer 2 + MERLIN Layer 2 + Maiden-Robustelli Tier 3
- DE : Profile Deutsch Layer 1 + Goethe Modellsätze Layer 2 + MERLIN-DE Layer 2 + Helbig-Buscha Tier 3
- RU : TORFL Minimums Layer 1 (acquérir post-sanctions)+ Antonova Doroga Layer 2 + RLC HSE Layer 2 + Wade Tier 3

Effort Phase 1 par lang inchangé per ADR-013 (13j IT, 16j DE, 21j RU).

### Phase 3 — Wave 3 JP (P3 août-déc 2026 ou plus tard)

Per ADR-015 : JFS Standard + Marugoto Layer 1 (acquired Session 52) + JLPT 公式問題集 Layer 2 + Tae Kim/Imabi Layer 3 + Makino dict Tier 3. Effort 28-31j.

### Phase 4 — Re-baseline 6 langues uniformes

Tier 1 measurement battery sur les 6 langues post-pipeline complet. Marketing pitch :
> "AcademIA pedagogy is grounded in authority — Cambridge English Profile, Cervantes PCIC, Profile Deutsch, CILS Sillabo, JF Standard, TORFL Pushkin — backed by SLA canon (Lyster, Lightbown/Spada, Pienemann, Ortega) and CEFR Companion 2020."

### Frontend Phase B (parallèle)

Phase B AcademIA design canon désormais grounded :
- **Norman 2013 DOET** + **Krug 2014 DMMT** = UX canon
- **Tufte 2001 VDQI** = info-viz canon (dashboards admin/learner progress)
- **Strizver 2013 Type Rules** = typography canon
- **Material 3 + Apple HIG + WCAG 2.2** = platform conventions

### Math/ML grounding pipelines

- **Baker 2001 IRT + Embretson 2000 IRT** ⭐⭐ = adaptive placement test design
- **Hastie ESL + Bishop PRML + Murphy PML** = ML foundations
- **MacKay ITILA** = LLM-judge confidence calibration info-theoretic
- **Hernán & Robins** = A/B testing rigorous
- **Boyd VMLS** = embeddings + LLM internals

### Risques mitigation

- **Edition staleness** : authority anchors pre-2020 (Profile Deutsch 2005, PCIC 2006, JF Standard 2010, Hawkins 2012) cross-validated against CEFR Companion 2020. Audit annuel.
- **Sources non-acquired** : CILS Sillabo + TORFL Minimums = stubs pending. Bloquant Wave 2 IT + Wave 4 RU démarrage. Mitigation : Sinse acquisition manuelle avant Wave-démarrage.
- **PCIC C1-C2 manquant** : gap pour ADR-013 ES flagship A1-C2. Mitigation : acquérir post-Wave-2.
- **Marugoto B2 manquant** : série culmine B1. Mitigation : acquérir Tobira ou Quartet pour JP B2 si Wave 3 démarre ; sinon JP cap B1 acceptable.

### Effort total impact

- Phase 1 EN/ES audit : +6-10j cumulés (audit pas rework)
- Phase 2-4 Wave : pas de changement vs ADR-013 (sources Layer 1 déjà acquired ou stub-pending plannifiés)
- Phase B frontend : grounding canon, no time impact (passive references)
- Total impact ADR-016 vs status-quo ADR-013 : **+6-10j** seulement (pour audit EN+ES, gain méthodologique cohérence cross-lang).

## Status & validation

`proposed` — ouvert pour Sinse review/accept.

Validation triggers `accepted` :
1. Sinse confirmation strategy all-in vs status-quo
2. Phase 1 EN audit démarrage (mai 2026 ou immediate post-Tier-1-stabilization Session 51)
3. Acquisition completed pour stubs critiques (PCIC C1-C2, CILS Sillabo, TORFL Minimums)

Si Sinse rollback all-in (e.g., scope reduction post-burnout) → ADR-016 reste `proposed` indéfiniment, EN/ES gardent statut historique (4-layer suffit, validation native directe Sinse).

## Cohérence cross-ADR

- **ADR-011** (CEFR rationale per-language) : cohérent — JLPT/TORFL/etc mappings restent valides
- **ADR-013** (scope tier flagship/essential) : cohérent — caps A1-B2 vs A1-C2 maintenus
- **ADR-014** (structured knowledge extraction Layer 1.5) : cohérent — authority anchors = Layer 1 sources canoniques pour extraction lazy
- **ADR-015** (JP productive evaluation) : cohérent — Marugoto = JFS Standard implementation primary, JFS Guidebook 2022 secondary

## Cross-references

- USAGE-MAP : [[../../../../sinse-vault/knowledge/books/USAGE-MAP]]
- Library inventory : [[../../../../sinse-vault/projects/academia-ia/library-inventory]]
- Library conventions : [[../../../../sinse-vault/meta/library-conventions]]
- Multilang validation pipeline (L141) : [[../../../../sinse-vault/knowledge/multilang-validation-without-natives]]
