---
title: ADR-011 — Systèmes de niveau natifs JLPT (JP) et TORFL (RU) + mapping architectural
status: accepted
last_reviewed: 2026-04-19
decision_date: 2026-04-19
authors: [sinse, claude]
---

# ADR-011 — Systèmes de niveau natifs JLPT (JP) et TORFL (RU)

## Contexte

AcademIA vise une roadmap multi-langue (ES/IT/DE/JP/RU) avec maturité équivalente au Teacher EN. Les analyses Session 27-28 ont montré que forcer CEFR A1-C2 pour JP et RU nécessiterait :

- **JP** : $3-10K externe (annotation humaine I-JAS FR-natif + validation keigo + construction grammar profile CEFR depuis JLPT descriptors).
- **RU** : €33-59K externe (Chemin A : linguiste SLA FR→RU + grammar profile manuel + annotation ERRANT-like) OU plafond B1 via synthetic-only (Chemin B, 25j).

**Contrainte Sinse (Session 29)** : aucune dépense externe possible pour JP/RU.

**Signal clé** : CEFR n'est pas le système de niveau utilisé par les learners JP ou RU. Le monde JP utilise **JLPT** (N5-N1, Japan Foundation), le monde RU utilise **TORFL / ТРКИ** (TEU-IV, Gosstandart). Ces systèmes disposent de ressources pédagogiques officielles complètes en open source.

## Options envisagées

### Option A — Forcer CEFR A1-C2 sur JP et RU (Session 27 original)

- Pour : homogénéité cross-lang, analytics directement comparables.
- Contre : $3-59K externe requis, learners JP/RU ne reconnaissent pas CEFR, construction grammar profile manuel redondante avec standards natifs existants.

### Option B — Systèmes de niveau per-language natifs avec enum différent (no unification)

- Pour : sémantiquement propre, respecte écosystème pédagogique de chaque langue.
- Contre : refactor massif du schéma (level partout), analytics cross-lang compliquées, tolerance_matrix et rubrics.yaml à dupliquer par système.

### Option C — Mapping transparent : niveau natif UI + storage interne CEFR unifié

- Pour : zéro refactor schéma, analytics cross-lang préservées, UI naturelle pour learners JP/RU, ressources officielles open réutilisables.
- Contre : non-bijectivité mapping (JLPT teste plutôt réception, TORFL plus strict que CEFR), nécessite module helper `levels.py`.

## Décision

**Option retenue : C** — Mapping transparent.

- **Storage interne** reste unifié `level ∈ {a1, a2, b1, b2, c1, c2}` pour toutes les langues.
- **UI et prompts Dify** utilisent le système natif par domaine via `display_level(cefr_level, domain)` → JP voit N5-N1, RU voit TEU-IV, autres voient A1-C2.
- **Rubrics YAML** par domaine : contenu rédigé selon descriptors natifs (JLPT grammar points pour JP, Gosstandart ТРКИ pour RU) mais indexé par niveau interne a1-c2.

**Justification** : Option C combine les avantages des Options A et B sans leurs coûts. Homogénéité technique (cross-lang analytics, schéma unchanged) + respect écosystème natif (UI/contenu naturel pour learners) + ressources pédagogiques officielles réutilisables sans traduction CEFR redondante. Le coût = 1 module helper `academie_core/levels.py` (~50 lignes).

Mapping officiel (défini par Japan Foundation et Gosstandart respectivement) :

| Niveau CEFR interne | JLPT (Sensei) | TORFL (Maestro-RU) |
|---|---|---|
| a1 | N5 | TEU (Элементарный) |
| a2 | N4 | TBU (Базовый) |
| b1 | N3 | TORFL-I |
| b2 | N2 | TORFL-II |
| c1 | N1 | TORFL-III |
| c2 | beyond_N1 (opt) | TORFL-IV |

## Conséquences

### Positives

- **0€ externe** pour JP et RU (remplace $3-59K initialement prévus Session 28).
- **Time-to-maturity** réduit : JP de 45-60j → 30-35j, RU de 45-55j → 25-30j.
- **Positionnement produit cohérent** : chaque Teacher parle le langage de niveau que ses learners utilisent déjà.
- **Ressources officielles réutilisables** : Japan Foundation JF Standard, Tae Kim, Imabi, Gosstandart ТРКИ, Lexical/Grammatical Minimum — tout open source.
- **Analytics cross-lang** préservées via niveau interne unifié a1-c2.
- **Wave 3.5 JP supprimée** (N5-N1 désormais complet dans Wave 3 unique).

### Négatives / acceptées

- **Mapping non bijectif** : JLPT N1 ≠ strictement CEFR C1 (JLPT teste plutôt réception, CEFR production). TORFL-IV plus exigeant que C2 sur cases. Documenté dans glossary + limites honnêtes Sections 4-5 de `multilang_maturity_research.md`.
- **Keigo niveau N1 (JP)** et **aspect verbal III+ (RU)** restent best-effort (patterns standards OK, subtilités littéraires manquées sans native validation).
- **Complexité légère** : 1 module helper `levels.py` + dispatch per domain dans `LEVEL_SYSTEM_BY_DOMAIN`.

### Neutres (à surveiller)

- Si les learners demandent explicitement "mon équivalent CEFR" pour compatibilité européenne (universités, emploi), prévoir affichage secondaire dans UI.
- Re-évaluer si accumulation de données réelles Wave 3/4 montre des gaps qualité non-anticipés → upgrade business-déclenché vers investissement linguiste natif reste possible.

## Actions de mise en œuvre

- [ ] Créer module `academie_core/levels.py` en Phase 0.7 (15j Phase 0 totale) avec :
    - `JLPT_TO_CEFR`, `CEFR_TO_JLPT`
    - `TORFL_TO_CEFR`, `CEFR_TO_TORFL`
    - `LEVEL_SYSTEM_BY_DOMAIN`
    - `display_level(cefr_level, domain) -> str`
    - `parse_user_level(raw, domain) -> cefr_level`
- [ ] Tests unitaires complets (bijection, edge cases, unknown domain fallback)
- [ ] Rubrics JP (Wave 3, Phase B) rédigées en descriptors JLPT natifs, clés internes a1-c2
- [ ] Rubrics RU (Wave 4, Phase B) rédigées en descriptors TORFL natifs, clés internes a1-c2
- [ ] Dify prompts Sensei (Wave 3) et Maestro-RU (Wave 4) injectent niveau natif via `display_level()`
- [ ] UI webapp frontend affiche niveau natif (store navigation + composants profile)
- [ ] Glossary entries JLPT, TORFL, Mapping natif↔CEFR (fait Session 29)

## Re-évaluation

- **Après Wave 3 (Sensei) alpha famille** : évaluer si quality N3-N1 acceptable ou si upgrade humain nécessaire.
- **Après Wave 4 (Maestro-RU) alpha famille** : évaluer si quality TORFL-II-IV acceptable.
- **Si demande utilisateur explicite** d'affichage CEFR secondaire pour compatibilité européenne → ajouter à UI.
- **Si business traction forte sur JP ou RU** : déclencher Chemin A optionnel (linguiste natif + annotation ERRANT) pour lever les plafonds keigo/aspect.

## Références

- [`docs/00-project/multilang_maturity_research.md`](../00-project/multilang_maturity_research.md) — verdict Session 29 et détail ressources par langue
- [`docs/00-project/multilang_execution_roadmap.md`](../00-project/multilang_execution_roadmap.md) — Phase 0.7 + Wave 3/4 refondues
- [`docs/00-project/multilang_research_plan.md`](../00-project/multilang_research_plan.md) — pipeline par langue JLPT/TORFL-native
- [`docs/00-project/glossary.md`](../00-project/glossary.md) — entrées JLPT, TORFL, Mapping natif↔CEFR
- [Japan Foundation JF Standard](https://jfstandard.jp)
- [JLPT Official](https://www.jlpt.jp)
- [Tae Kim's Guide to Japanese Grammar](https://guidetojapanese.org)
- [Imabi.org](https://imabi.org)
- [Gosstandart ТРКИ — Ministère Éducation Russia](https://gct.msu.ru/) (standards officiels TORFL)
- ADR-002 (schema multi-lang dès day-1) — compatible : niveau interne unifié conservé
- ADR-005 (academie-core shared library) — `levels.py` est nouveau module dans `academie_core/`
