---
title: ADR-008 — ERRANT mapping reporté à Sprint 5+ (table de traduction, non-natif)
status: accepted
last_reviewed: 2026-04-15
decision_date: 2026-04-15
authors: [sinse, claude]
---

# ADR-008 — ERRANT mapping reporté à Sprint 5+ (table de traduction, non-natif)

## Contexte

ERRANT (ERRor ANnotation Toolkit, Bryant et al. 2019) est le **standard NLP de facto** pour annotation d'erreurs en grammatical error correction. ~50 codes (`R:VERB:TENSE`, `M:DET`, `U:PREP`, …). Utilisé par :

- BEA 2019 Shared Task
- W&I + LOCNESS corpus
- FCE dataset
- CoNLL shared tasks
- La majorité des benchmarks GEC récents

Question : mapper notre taxonomie sur ERRANT dès maintenant ou plus tard ?

## Options envisagées

### Option A — Adopter ERRANT comme schéma natif

- Pour : interop maximale, pas de conversion
- Contre : ERRANT est anglo-centré, ne couvre pas les gravity axes ni les criterial levels que notre taxonomie v2 vise

### Option B — Mapper notre taxonomie vers ERRANT via table de traduction

- Pour : interop quand besoin (import datasets externes), garder notre modèle riche
- Contre : couche supplémentaire à maintenir

### Option C — Ignorer ERRANT

- Pour : simplicité
- Contre : aucun import gratuit de corpus annotés (W&I Corpus 2024, FCE, etc.)

## Décision

**Option B avec déploiement différé au Sprint 5+**.

**Justification** :
- ERRANT ne résout pas notre problème pédagogique (tiers, gravity axes, L1 transfer), il résout un problème d'interop NLP
- L'interop devient valuable au moment où on importe des corpus externes pour **calibrer empiriquement** la taxonomie (Sprint 5 — EFCAMDAT, W&I Corpus 2024)
- Avant Sprint 5, le coût du mapping (~1-2 jours) est pur dépense sans bénéfice
- La table de traduction `errant_to_family.yaml` peut être ajoutée à tout moment sans casser l'existant

## Conséquences

- Positives : focus sur le socle pédagogique d'abord, interop ajoutée quand pertinente
- Acceptées : impossibilité d'importer des datasets externes avant le Sprint 5
- Neutres : dette technique nulle (table de traduction = ajout additif)

## Actions de mise en œuvre

**Maintenant** :
- [x] Noter le besoin dans cette ADR

**Sprint 5 (ou quand besoin d'import externe)** :
- [ ] Créer `academie-core/data/errant_to_family.yaml` — mapping ~50 codes ERRANT vers nos 12 familles
- [ ] Écrire fonction `import_errant_annotated_corpus(corpus_path)` qui convertit vers notre format
- [ ] Valider via import test du W&I Corpus 2024
- [ ] Documenter dans `05-decisions/ADR-errant-import-validation.md` (nouvelle ADR)

## Re-évaluation

Pas de re-évaluation nécessaire — décision du type "plus tard", non bloquante.

## Références

- [Bryant et al. 2019, BEA](https://www.cl.cam.ac.uk/research/nl/bea2019st/)
- [Write & Improve Corpus 2024](https://www.repository.cam.ac.uk/items/ba155087-0754-4c6b-ade8-68858e1df2f0)
- [ADR-002-schema-from-day-1.md](ADR-002-schema-from-day-1.md)
