---
title: Add a new agent / domain
status: draft
last_reviewed: 2026-04-15
---

# Add a new agent / domain

> Procédure pour ajouter un nouvel agent (ex : Maestro ES, PyMentor Python, CyberMentor) à AcademIA.

**Statut** : `draft` — sera solidifié après Sprint 5 (première vraie implémentation de l'architecture hybride orchestrée, cf. [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md)).

## Pré-requis

- `academie-core` package scaffolded et publié en interne
- Teacher EN migré vers `LanguageDomain(lang="en")` + `language-tutor` chatflow (Sprint 5)
- Pour langues : sources CECRL criterial features disponibles (EGP-like)
- Pour code/cybersec : taxonomie propre au domaine définie

## Ajouter une nouvelle **langue** (ex : Maestro ES)

### Étapes

1. **Data : remplir `academie-core/data/cefr_criterial_features/es.yaml`**
   - Depuis [Plan Curricular del Instituto Cervantes](https://cvc.cervantes.es/ensenanza/biblioteca_ele/plan_curricular/indice.htm)
   - Structure identique à `en.yaml` : concept_key → {emergence_level, mastery_level, family, metadata}
   - Effort : 1-2 jours de mapping (extraction depuis PCIC)

2. **Data : remplir `academie-core/data/tolerance_matrix/es.yaml`**
   - Copier la structure de `en.yaml`
   - Adapter gravity axes si spécificité ES (ex : subjonctif plus central que EN)
   - Priors initiaux, calibration empirique plus tard avec CEDEL2

3. **Data : ajouter paires L1→ES dans `l1_transfer_multipliers.yaml`**
   - `fr_to_es`, `en_to_es`, `it_to_es`, etc.
   - Priors via URIEL/lang2vec distances
   - Calibration empirique après accumulation de données

4. **Webapp : instancier `LanguageDomain(lang="es")`**
   - Router : `/api/chat/send?agent=maestro` route vers `LanguageDomain("es")`
   - Pas de nouveau chatflow Dify — réutilise `language-tutor` paramétré

5. **Curriculum DB : peupler `curriculums` et `curriculum_concepts` pour `domaine='espagnol'`**

6. **UI : ajouter Maestro dans le sélecteur d'agents (`/`)**
   - Nouvel agent card, accent color, slug
   - `LocalStorage` user default agent si préférence user

7. **Test E2E** : onboarding complet avec user test, vérification profil créé en DB

8. **Documentation** :
   - Créer `docs/03-domain/languages/es.md`
   - Mentionner dans `docs/INDEX.md` et `docs/00-project/vision.md`
   - ADR de migration si choix architectural impactant

### Effort estimé par langue

- **EGP-rich** (EN baseline) : ~5 jours une fois data-in-hand
- **Nouvelle langue** : ~8-15 jours incluant data gathering

## Ajouter un **domaine non-linguistique** (ex : PyMentor)

### Étapes additionnelles

Le framework est prévu mais **pas encore validé** (prévu Sprint long-terme).

1. **Créer `CodeDomain(programming_lang="python")`** dans `academie-core/domain/code.py`
   - Implement interface `Domain` : `detect_errors`, `score_tier`, `compute_progression`, etc.
   - Adapter : pas de CECRL mais Bloom ou custom proficiency scale
   - Errors viennent de stack traces d'exécution + analyse LLM, pas de rules layer NLP

2. **Créer un nouveau chatflow Dify `code-mentor`**
   - Paramétré par `programming_lang`
   - Intègre une node exécution sandbox (Dify-sandbox ou externe)
   - Prompt différent de `language-tutor` (pédagogie Bloom, pas Lyster)

3. **Webapp** : router `/api/chat/send?agent=pymentor` vers `CodeDomain("python")`

4. **Data** : taxonomie d'erreur Python par niveau (SyntaxError / IndentationError → débutant ; AttributeError contextuel → intermédiaire ; async/design → avancé)
   - Inspirée de [NICE Framework](https://www.nist.gov/document/nist-nice-framework-measuring-cybersecurity-workforce-capabilities) ou Bloom
   - Pas de corpus CECRL-like ; à construire

5. **Documentation** : `docs/03-domain/code/python.md` + ADR pour décision majeures

### Effort estimé pour PyMentor

~20-30 jours (nouvelle architecture domain + chatflow + data from scratch).

## Ajouter un domaine **cybersec** (CyberMentor)

Similaire à PyMentor mais :
- Framework de compétences : NICE Framework (NIST)
- Pédagogie : scenarios / Capture-the-Flag light / questions concrètes
- Moins d'exécution code, plus d'analyse situationnelle

## Post-ajout — ce qu'il faut surveiller

Dans les 2 premières semaines après ajout d'un nouvel agent :
- Taux d'erreurs LLM (hallucinations, overcorrection) — ajuster prompt si > 10% observations user
- Latence : si chatflow nouveau plus lent, investiguer node par node
- Profil utilisateur : vérifier que les snapshots se génèrent correctement (requête `SELECT COUNT(*) FROM snapshots_session WHERE domaine=...`)
- Cross-domain interference : si user a déjà un profil dans autre domaine, pas de corruption

## Références

- [ADR-004](../05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) — topologie
- [ADR-005](../05-decisions/ADR-005-academie-core-shared-library.md) — shared-core
- [02-architecture/shared-core.md](../02-architecture/shared-core.md) — interface `Domain`
- [01-pedagogy/taxonomy-framework.md](../01-pedagogy/taxonomy-framework.md) — framework abstrait
