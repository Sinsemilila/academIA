---
title: ADR-017 — AccountingDomain scope (Studi RNCP41653 complementary tutor)
status: proposed
last_reviewed: 2026-05-01
owner: claude
---

# ADR-017 — AccountingDomain : Tuteur compta complémentaire formation Studi RNCP41653

## Status

**Proposed** (S57, 2026-05-01). Pending Sinse acceptance + Phase 1 kickoff.

## Context

Premier domaine non-linguistique d'AcademIA. Use case primaire concret : Marie (proche Sinse) suit la formation **Studi Pré-Graduate Assistant Comptable** (RNCP41653, 380h sur 9 mois). Architecture AcademIA déjà domain-agnostic (cf taxonomy-framework.md, ADR-005), mais aucune instance non-langue concrète à ce jour.

3 questions structurelles :
1. Scope formation : référentiel cible + blocs + modules
2. Positionnement vs formation existante (Studi a IA intégrée)
3. Architecture detect/judge : LLM-heavy comme Teacher/Maestro, ou rules-first ?

## Decisions

### D1 — Référentiel cible définitif : **RNCP41653 Studi**

Pas RNCP31677 ni Bac Pro AGOrA. Cible = **RNCP41653 "Assistant comptable" Studi** (décision France Compétences 27/11/25), 3 blocs officiels :
- BC1 : Traiter les travaux comptables courants et de clôture
- BC2 : Préparer les éléments de paie et les déclarations fiscales
- BC3 : Gérer l'accueil et les travaux administratifs courants du service comptable

**Drivers** :
- Cohérence directe avec parcours Marie (use case primaire)
- RNCP41653 tout récent (decision 27/11/25) → référentiel à jour, durée vie longue
- Équivalences/passerelles RNCP41653 ↔ RNCP37121 (TP Comptable Assistant) ↔ RNCP38043 → réutilisable post-Marie pour autres apprenants

### D2 — Positionnement : **TUTEUR COMPLÉMENTAIRE**, pas remplaçant

Studi fournit déjà : cours, vidéos, ~111 Cas pratiques, classes virtuelles, accompagnement humain 24h ouvrées, IA intégrée modules dédiés.

L'agent AcademIA ne duplique PAS Studi. Il est **tuteur perso 24/7** complémentaire pour :
- Récap concepts (5 min vs 45 min cours)
- Génération cas-similaires-pas-identiques pour pratique illimitée (vs ~111 cas Studi finis)
- Explication "pourquoi" sur demande immédiate (vs 24h forum)
- Drill QCM blocs avant examens
- Simulation étude de cas finale 45 min
- Coaching motivation autodidacte

**Différenciation** : pratique illimitée + feedback Lyster pédagogique (scaffolds vs explicit-correction Studi) + format conversationnel intime.

### D3 — Architecture detection : **rules-first 80%, LLM 20%**

Contrairement à `LanguageDomain` (LLM-heavy : Teacher EN, Maestro ES), `AccountingDomain` utilise :
- **Détection déterministe** rules-based (80% des cas) :
  - Vérification partie double (débit total = crédit total)
  - Vérification calcul TVA (HT × taux = TVA)
  - Vérification compte PCG (4 premiers chiffres dans table valid)
  - Vérification taux TVA officiels (5.5 / 10 / 20 / autres)
  - Vérification dates (cohérence pièce/saisie/exigibilité)
- **LLM judge** seulement pour :
  - Diagnostic profond ("pourquoi tu as choisi ce compte ?")
  - Génération exercices contextualisés
  - Feedback Lyster narratif
  - Cas ambigus (ex: classement compte 6064 vs 6067 sans contexte clair)

**Drivers** :
- Compta = domaine "fermé" (réponse exacte vs production libre)
- Cost LLM panel cross-provider (S55-S56 budget) inutile pour validations déterministes
- Validation déterministe = κ=1.0 trivial (pas de noise inter-rater)
- Concentre le LLM budget sur la valeur (pédagogie) pas la mécanique (calcul)

### D4 — Proficiency scale : **Blocs RNCP × N0-N3**

Pas CEFR, pas Bloom. **Blocs RNCP (BC1/BC2/BC3) × niveau acquisition (N0/N1/N2/N3)**.

```
N0 decouverte    : concept exposé, pas autonome
N1 guide         : autonome avec aide ponctuelle
N2 autonome      : tâche routine sans aide  ← cible certif RNCP41653
N3 expert_assist : gestion exceptions + auto-vérif
```

Mapping interne CEFR-like pour réutiliser infra existante (DB schema, judge prompts paramétrés) : `N0≈A1, N1≈A2, N2≈B1, N3≈B2`. Cible certif = N2 sur les 3 blocs.

### D5 — Authority anchor : mono-source officielle

| Source | Rôle | Acquisition |
|--------|------|-------------|
| Programme Studi RNCP41653 | Référentiel pédagogique opérationnel (curriculum + cas pattern) | ✅ S57 |
| Référentiel RNCP41653 France Compétences | Référentiel officiel certif | P0 fetch web |
| PCG règlement ANC 2014-03 | Plan de comptes officiel | P0 PDF anc.gouv.fr |
| BOFiP TVA fondamentaux | Référentiel fiscal | P0 web scrape ciblé |
| Manuel Grandguillot | Référence pédagogique canon | P1 acquisition |

Pas de débat cross-source (contrairement langues : Companion CEFR vs corpus vs grammars).

### D6 — Phase 1 MVP scope : **BC1 modules 1-5**

Pas full BC1+BC2+BC3 (~25-30j cumul). MVP étroit :
- BC1 modules 1 (objectifs compta) + 2 (CR/bilan présentation) + 3 (écritures + balance) + 4 (TVA mécanisme) + 5 (factures doit/avoir)
- ~20 concepts competency map
- ~10 codes error taxonomy
- 12-15 scenarios oracle
- ChatInput texte pur (UI tableau journal différé Phase 2)

Estimation : **5-8j** (vs 25-30j full).

### D7 — Lyster moves transferable + open `show_balance`

Les 6 CF moves Lyster (recast, partial_recast, explicit_correction, prompt_plus_remediation, metalinguistic, clarification_request) se transfèrent à compta. Phase 1 utilise cette taxonomie identique. Phase 2 : empirically discover si compta a moves spécifiques (ex: `show_balance` = visualisation balance après écriture).

## Consequences

### Positives
- Premier domaine non-langue cohérent et scoped (ouvre PyMentor / CyberMentor / autres post-validation pattern)
- Use case concret immediate (Marie) → feedback empirique réel vs design théorique
- Test transferability framework domain-agnostic (taxonomy-framework.md ligne 132 invariants universels)
- LLM cost optimization (rules-first) → pattern réutilisable autres domaines fermés (code testing, cybersec rule-based)
- Corpus Studi (~111 cas) = template pédagogique pré-existant, pas de cold start curriculum

### Négatives / risques
- Marie = use-case unique → risque sur-fit à son profil specific (atténuation : RNCP41653 standard, autres apprenants potentiels post-MVP)
- UI/UX texte-pur Phase 1 sera limité pour saisie écritures multi-lignes (mitigation : Phase 2 composant journal custom)
- Studi a IA intégrée → différenciation pédago (Lyster scaffolds) doit être manifeste pour justifier l'agent
- Validation formateur humaine obligatoire pré-déploiement (Marie ne peut pas se valider seule, cohérent L141)

### Neutres
- Pas de L1 transfer (vs langues) — simplifie data layer mais perd dimension de personnalisation
- Pas de native-speaker variance — κ judge facile mais perd source de noise utile au design

## Alternatives rejetées

- **A. Bac Pro AGOrA scolaire** : trop large, public différent (élèves 16-19 ans), Marie pas dans ce parcours.
- **B. RNCP31677 TP Comptable Assistant** : ancien référentiel, équivalence vers RNCP41653 mais moins frais.
- **C. Domain-agnostic detection LLM-heavy** : copie pattern Teacher EN. Coût LLM panel inutile sur validations déterministes (debit=credit), perd avantage spécifique compta.
- **D. UI tableau journal Phase 1** : trop scope. ChatInput suffit pour MVP "récap + drill + explain".

## Implementation pointers

- **Doc compta** : `docs/03-domain/comptabilite.md` (S57 draft, Sinse review)
- **Authority data** : créer `webapp/backend/data/compta/` (référentiel + cas patterns) + `webapp/backend/app/data/curriculum_compta.yaml`
- **Agent prompt Comptable_FR** : `webapp/backend/app/prompts/comptable_fr_*.py` (à créer)
- **Detection rules** : `webapp/backend/app/oracle/rules_compta.py` (déterministique-first, mirror pattern rules_es.py mais avec calculs)
- **Scenarios oracle** : `scripts/oracle/scenarios/comptable_fr/bc1_*.yaml`
- **Schemas** : extension `ScenarioKey` pour `bloc: BC1|BC2|BC3` + `module: str` + `level: Literal["N0","N1","N2","N3"]`

## References

- ADR-002 — schéma multi-domaine dès le départ
- ADR-005 — academie-core shared library
- ADR-013 — language scope by tier (parallèle pour langues)
- ADR-016 — authority anchor strategy cross-lang (parallèle, mais mono-source compta vs multi-source langues)
- `docs/01-pedagogy/taxonomy-framework.md` — framework abstrait domain-agnostic
- `docs/03-domain/comptabilite.md` — instance compta détaillée
- Programme Studi RNCP41653 PDF : `library/by-domain/formation marie/`
