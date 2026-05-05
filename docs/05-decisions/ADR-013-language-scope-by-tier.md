---
title: ADR-013 — Language scope by tier (EN+ES flagship A1-C2 / IT+DE+JP+RU cap A1-B2)
status: accepted
last_reviewed: 2026-04-29
decision_date: 2026-04-29
authors: [sinse, claude]
---

# ADR-013 — Language scope by tier

## Contexte

AcademIA cible 6 langues à terme : EN (Wave 0 livré), ES (Wave 1 ~85% livré Session 51), IT + DE (Wave 2 prévu), JP (Wave 3), RU (Wave 4).

Session 51 a livré recherche approfondie pour les 4 langues Wave 2-4. Phase 1 estimates par langue : IT 17j, DE 20.5j, JP 36j, RU 26-28j. Total combined ~100j.

**Signaux ayant motivé re-scoping** :

1. **Voice recognition feature roadmap** : speech-to-text (Whisper-class ASR) + pronunciation evaluation prévus comme features futures. Tooling actuel performe bien à A1-B2 mais **degrade sharply C1/C2** : phonetic precision requise (forced alignment Praat/MFA, prosody analysis, accent reduction), spécialisée 10x plus complexe que stack ASR généraliste.
2. **Market reality** : 95% des learners atterrissent à B2 maximum. Cambridge/Goethe/CILS/JLPT-N2/TORFL-2 = certifications majoritaires. C1/C2 = niche "excellence linguistique".
3. **Pédagogie** : au-delà de B2, error-correction Lyster s'applique moins directement — la pédagogie devient curated authentic input + stylistic refinement, paradigme différent.
4. **Research ecosystem mature jusqu'à B2** : MERLIN-IT cap B1, JP I-JAS limité N3 niveaux supérieurs, RLC HSE majoritairement TRKI-1/2. Au-delà = corpus séparés (Falko-DE, ressources ad-hoc) → effort exponentiel.
5. **Effort réduction substantielle** : -25-30% Phase 1 par langue × 4 langues (IT/DE/JP/RU) ≈ ~22-25j économisés.

**Cas spécial EN + ES** :
- EN : déjà investi A1-C2 (sunk cost, scenarios + rubrics + fewshots écrits). Maintenir flagship cohérent.
- ES : 500M+ speakers, 2ème langue la plus apprise mondialement après EN. Justifie traitement flagship A1-C2 (différenciation marché + power users).

## Options envisagées

### Option A — Toutes langues A1-C2 (statu quo per multilang-roadmap original)

- Pour : exhaustivité, différenciation vs Duolingo/Babbel (qui cap B1-B2), pas de path dependency
- Contre : effort cumulé ~100j Phase 1 multi-lang, voice features impossibles C1/C2 avec tooling current, plateau pédagogique B2→C1 mal scaffoldé sans investissement spécialisé, ROI faible (5% market)

### Option B — Toutes langues A1-B2 (drop C1/C2 universel incluant EN/ES)

- Pour : -33% scope, alignement total tooling voice, mass-market positioning Duolingo-like
- Contre : EN sunk cost throwaway (~20% existant EN dropped), perte différenciation marché, ES avec 500M speakers mérite traitement plus profond, signalement régression aux users existants

### Option C — Tiered scope : EN+ES A1-C2 / IT+DE+JP+RU A1-B2 (RETENU)

- Pour : sunk cost EN respecté + ES différenciation, voice features atterrissent A1-B2 sur 4 langues, effort réduit ~22-25j sur Wave 2-4, path dependency mitigée (research C1/C2 existe = future re-extension possible)
- Contre : asymétrie scope entre langues (UX consistency à gérer côté frontend), 2 catégories de langues à maintenir, justification "pourquoi pas IT C1/C2" à expliciter sur landing page

## Décision

**Option C retenue** — tiered scope.

**Justification** : alignement simultané sur 4 axes (voice tooling capability + market reality + pédagogie applicability + effort budget) sans throwaway des investissements existants (EN) et sans sous-investir les marchés à fort volume (ES). Asymétrie scope est un coût acceptable vs alternatives.

EN + ES = "flagship" tier (A1-C2 full curriculum) — différenciation produit, profondeur pédagogique, support power users + utilisateurs natifs/quasi-natifs en perfectionnement.

IT + DE + JP + RU = "essential" tier (A1-B2 cap) — voice features depuis le ship, pédagogie Lyster pleinement applicable, effort raisonnable par langue.

## Conséquences

**Positives** :
- Phase 1 effort recalibré : IT ~13j, DE ~16j, JP ~28j, RU ~21j → **~78j combined** (vs 100j Session 51 estimate). Économie ~22j.
- Voice feature roadmap unblocké (toutes langues atteignent B2 ceiling où Whisper performe).
- Battery oracle réduite : ~20 scenarios non-flagship (vs 24-26 flagship) → moins judge calls + RPD breathing room.
- ADR explicite = position défendable sur landing page si question "pourquoi A1-B2 only en allemand?".

**Négatives / acceptées** :
- Asymétrie scope inter-langues (UX consistency à gérer côté frontend `agents_config.ts` + landing page).
- Re-extension future C1/C2 sur IT/DE/JP/RU = path dependency. Research Session 51 prévient (les 4 fichiers research couvrent jusqu'à C2).
- Léger signalement positionnement : AcademIA = pédagogie research-driven mais avec scope-by-market décision pragmatique.

**Neutres (à surveiller)** :
- Engagement metric par tier post-launch : si tier-essentiel users demandent C1/C2 (signal LinkedIn/Twitter/email feedback), trigger re-extension pondéré par volume.
- Si voice tooling C1/C2 mature (Praat-as-a-service, MFA cloud, etc.) dans 2-3 ans, re-évaluer extension.

## Actions de mise en œuvre

- [ ] Update `vault/knowledge/teacher-creation-recipe.md` : default recipe = A1-B2, flagger EN/ES exception A1-C2
- [ ] Update les 4 fichiers `vault/knowledge/multilang-{italian,german,japanese,russian}-research.md` : marquer sections C1/C2 comme "Future scope (post-voice-feature ship, post-volume-signal)"
- [ ] Update `vault/knowledge/multilang-roadmap.md` : Phase 1 estimates recalibrés + tiered scope reflété
- [ ] Update `/opt/academia/docs/00-project/multilang_research_plan.md` + `roadmap_multilang.md` : tiered scope mention
- [ ] Maestro ES : pas de drop scope (reste full A1-C2), confirmer scenarios oracle 24 → 24 (no change)
- [ ] Frontend `agents_config.ts` : marquer per-agent `max_level: "B2" | "C2"` field pour UX gating future
- [ ] Landing page draft mention asymmetry quand commercialization

## Re-évaluation

- **Trigger short-term (3 mois post-IT/DE ship)** : si feedback users tier-essentiel demande C1/C2 explicitement (≥10 emails ou comments) → re-évaluer extension d'une langue.
- **Trigger long-term (12 mois)** : si voice tooling C1/C2 mature (Praat-cloud, MFA serverless) → re-évaluer extension globale.
- **Trigger market** : si pivot commercialization premium tier targeting power users → flagship pattern peut s'étendre à toutes langues.

## Références

### Papers / sources
- Sheen-Ellis 2011 — focused vs unfocused CF, B2→C1 plateau dangerous
- Cambridge/Goethe/CILS/JLPT/TORFL distribution data — B2 = "professional/academic-ready" certif majoritaire
- Whisper (OpenAI) — ASR performance dégrade idiomatique C1+ (voir issues GitHub openai/whisper)
- MERLIN-IT cap B1 (cf. [[multilang-italian-research]] §2)
- I-JAS NINJAL FR-L1 limité ~280 productions (cf. [[multilang-japanese-research]] §2)

### ADRs liés
- ADR-005 — academie-core shared library (per-language assets matrix)
- ADR-011 — native level systems JLPT/TORFL (orthogonal à scope tier — JP/RU restent JLPT-N5-N2 / TORFL TEU-TRKI-2 dans tier essential)

### Fichiers vault impactés
- `vault/knowledge/teacher-creation-recipe.md`
- `vault/knowledge/multilang-{italian,german,japanese,russian}-research.md`
- `vault/knowledge/multilang-roadmap.md`

### Fichiers code à anticiper
- `webapp/frontend/src/lib/config.ts` (agent metadata `max_level` field)
- `packages/academie-core/academie_core/data/curriculum_{lang}.yaml` (cap B2 pour IT/DE/JP/RU)
- `packages/academie-core/academie_core/data/rubrics/{lang}.yaml` (drop C1/C2 sections IT/DE/JP/RU)
- `packages/academie-core/academie_core/data/fewshots/{lang}.yaml` (drop C1/C2 IT/DE/JP/RU)
- `packages/academie-core/academie_core/data/mini_exam/{lang}_*.yaml` (skip C1/C2 IT/DE/JP/RU)
