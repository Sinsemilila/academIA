---
title: ADR-004 — Architecture hybride orchestrée pour la topologie des agents
status: accepted
last_reviewed: 2026-04-16
decision_date: 2026-04-15
accepted_date: 2026-04-16
authors: [sinse, claude]
---

# ADR-004 — Architecture hybride orchestrée pour la topologie des agents

## Statut : accepted (depuis 2026-04-16)

**Décision acceptée après ré-analyse Sprint 4** (2026-04-16). Voir [sprint4_preimpl_review.md](../00-project/sprint4_preimpl_review.md) pour le détail des 4 checkpoints fermés + feedback post-Sprint-3 + estimation chiffrée 8-11 jours-dev pour l'implémentation + plan rollback canary.

**GO Option C (full)** : package `academie-core` + `LanguageDomain` + ports progressifs depuis `webapp/backend/app/{teacher_prompt,error_taxonomy}/*.py`. Sprint 4 impl débute quand Sinse donne GO après lecture. Sprint 5 (Maestro ES) ensuite — gain marginal estimé ~5 jours par langue vs ~15j sans factorisation.

## Contexte

Le projet prévoit 7+ agents : **Teacher (EN), Maestro (ES), Sensei (JP), Lehrer (DE), Professore (IT), PyMentor (Python), CyberMentor (cybersec)**. Potentiellement plus (compta, système/réseau…).

Teacher EN existe actuellement comme **un chatflow Dify dédié** avec sa pédagogie propre. Question : comment architecturer l'ajout des autres agents ?

## Options envisagées

### Option A — Un Dify chatflow par agent (extension du status quo)

- Pour : isolation totale, pédagogie 100% custom par agent, déploiement indépendant
- Contre : **duplication massive**. Améliorer la logique pédagogique (ex : refonte feedback Lyster) = répéter 5 fois pour les 5 langues. Anti-pattern à l'échelle 7+ agents.

### Option B — Un Dify chatflow universel pour tous

- Pour : factorisation maximale
- Contre : **impossible pédagogiquement**. Un Teacher (Lyster prompts, dialogue socratique) et un PyMentor (debug, exec sandbox, stack trace) n'ont rien à voir. Forcer un seul chatflow = compromis médiocre partout.

### Option C — Hybride orchestré (retenu)

Factorisation par **famille pédagogique**, pas par agent ni universellement.

```
SvelteKit Frontend
        │
        ▼
FastAPI orchestrator (webapp/backend)
        │
        ├──► LanguageDomain (Lyster prompts, CECRL, gravity axes, L1 transfer)
        │      └──► 1 seul Dify chatflow "language-tutor"
        │           paramétré : {lang_target, level, L1, mode}
        │
        ├──► CodeDomain (Bloom-like, sandbox exec, error trace)
        │      └──► 1 Dify chatflow "code-mentor"
        │           paramétré : {programming_lang, level}
        │
        ├──► CyberSecDomain (NICE framework, scenarios)
        │      └──► 1 Dify chatflow "cybersec-mentor"
        │
        └──► (futur) AccountingDomain, etc.

Tous implémentent l'interface Domain de academie-core (cf. ADR-005)
```

## Décision

**Option C (Hybride orchestré) acceptée en principe**.

**Justification** :
1. **Factorisation intelligente** : les 5 langues partagent 1 chatflow Dify paramétré. Update pédagogique = 1 modif propagée aux 5 langues.
2. **Spécialisation cohérente** : Code, cybersec, compta ont chacun leur chatflow — leur pédagogie diffère réellement.
3. **Abstraction Domain** (ADR-005) : webapp parle à `Domain` sans savoir si c'est Teacher ou PyMentor. Dashboard unifié gratuit.
4. **Migration progressive** : Teacher EN actuel devient `LanguageDomain(lang="en")` sans rewrite. Pas de flag-day.

## Risques identifiés (à analyser avant implémentation)

### Risque #1 — Dify chatflow paramétré devient un monstre à variables

**Mitigation préliminaire** : garder le chatflow Dify minimal (juste le rendu/streaming LLM), mettre la logique dans `academie-core` Python. Dify ne fait que recevoir un prompt pré-construit.

### Risque #2 — Abstraction Domain prématurée

Les vrais besoins ES/JP/DE/IT/Python ne sont pas connus. L'interface `Domain` conçue aujourd'hui peut ne pas matcher les réels.

**Mitigation** : conception minimale de l'interface (seulement ce que Teacher EN a besoin aujourd'hui + ce que la taxonomie v2 exige), extension incrémentale au fur et à mesure.

### Risque #3 — Coûts de migration sous-estimés

Extraire la logique Teacher actuelle vers `LanguageDomain + language-tutor chatflow paramétré` = refactor non-trivial.

**Mitigation** : estimation détaillée à faire avant Sprint 4, avec fallback possible (garder chatflow EN actuel jusqu'à validation du pattern avec Maestro).

### Risque #4 — Scaling inter-domaines

Si un utilisateur fait EN et ES en parallèle, son profil est-il unifié ? Cross-transfer FR→EN→ES est-il modélisé ? Pas encore tranché.

**Mitigation** : décision différée — consulter la re-analyse data model (Dimension 3).

## Conséquences

- Positives : coût marginal faible pour ajouter une langue (juste des data, pas de nouveau chatflow) ; code pédagogique DRY ; dashboard unifié natif
- Acceptées : un bug dans le chatflow `language-tutor` impacte toutes les langues d'un coup (isolation moins bonne que Option A)
- À mitiger : tests E2E par langue obligatoires, staging recommandé pour déploiement (cf. Dimension 5 — staging à prévoir)

## Actions de mise en œuvre

**Avant Sprint 4 (ré-analyse obligatoire)** ✅ **DONE 2026-04-16** :
- [x] (claude, 2026-04-16) Revue hypothèses Sprint 1 (calibration W&I) — GLMM β-tier weights validés en prod Session 17, taxonomy tient.
- [x] (claude, 2026-04-16) Revue hypothèses Sprint 2 (schéma) — `domaine` partition fonctionne, gravity axes dénormalisées OK, USE_V2_SCORING en prod Session 18.
- [x] (claude, 2026-04-16) **Revue post-Sprint 3** (bonus) — 8 dynamic sections auditées, 3 méthodes manquantes dans Protocol v1 identifiées (`build_dynamic_sections`, `build_system_prompt`, `parse_response`), v2 proposé.
- [x] (claude, 2026-04-16) Estimation chiffrée migration : **8-11 jours-dev Sprint 4**, +4.5-6.5 jours Sprint 5 Maestro ES.
- [x] (claude, 2026-04-16) Plan rollback : flag env `USE_ACADEMIE_CORE=true/false`, canary 1 semaine, rollback < 2 min.

**Sprint 4 (implémentation, DONE 2026-04-16)** :
- [x] (claude, 2026-04-16) Phase A — scaffold `packages/academie-core/` (commit `abbc0d8`)
- [x] (claude, 2026-04-16) Phase B — port taxonomy (commit `abfab1d`)
- [x] (claude, 2026-04-16) Phase C — port pedagogy (commit `edc16ee`)
- [x] (claude, 2026-04-16) Phase D — créer `LanguageDomain` (commit `8d54832`)
- [x] (claude, 2026-04-16) Phase E — webapp `chat_router` via `LanguageDomain("en")` (commit `9a6865c`)
- [x] (claude, 2026-04-16) Phase F — battery 99.1% GREEN + cleanup shims + docs (commit TBD)
- [ ] Side-task DELETE 6 chatbots obsolètes — déféré à Sprint 5 kickoff (10min, pas bloquant)
- YAMLization RUBRICS/FEWSHOT_BANK/L1_TRANSFER_SEED deferred Sprint 5 (quand Spanish force la structure multi-lang)

**Sprint 5 (Maestro ES, POST Sprint 4)** :
- [ ] Seed `rules/es.yaml`, `rubrics/es.yaml`, `fewshots/es.yaml`, `l1_transfer/fr_to_es.yaml` — 2-3j
- [ ] Cloner Teacher V2 chatflow pour `language-tutor-es` (Dify) — 1-2j
- [ ] Activate `LanguageDomain("es")` + env `DIFY_KEY_MAESTRO` — 0.5j
- [ ] Test E2E Maestro avec family users — 1j

## Re-évaluation

- **Impérative** : avant Sprint 4, analyse de risques détaillée (cf. actions ci-dessus)
- **Si bascule actée** : après 1 mois d'exploitation, mesurer vélocité d'ajout de nouveaux domaines vs. architecture alternative

## Références

- [ADR-005-academie-core-shared-library.md](ADR-005-academie-core-shared-library.md) — le package qui porte l'abstraction
- [ADR-002-schema-from-day-1.md](ADR-002-schema-from-day-1.md) — schéma multi-domaine
- [02-architecture/agent-topology.md](../02-architecture/agent-topology.md) — schéma détaillé (à écrire)
