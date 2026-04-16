# academie-core

> Package Python partagé pour AcademIA — pédagogie, taxonomie, psychométrie, abstraction `Domain`.

**Statut** : Sprint 4 Phase A — scaffold. Protocol stubs uniquement, pas d'implémentation.

**Cible** : porter progressivement la logique `webapp/backend/app/teacher_prompt.py` + `webapp/backend/app/error_taxonomy/*.py` ici, conformément à [ADR-004](../../docs/05-decisions/ADR-004-hybrid-orchestrated-agent-topology.md) + [shared-core.md](../../docs/02-architecture/shared-core.md).

## Install (dev)

```bash
pip install --break-system-packages -e ./packages/academie-core[dev]
```

## Run tests

```bash
pytest packages/academie-core/
```

## Organisation

```
academie_core/
├── domain/          # Protocol Domain + implémentations concrètes (LanguageDomain, etc.)
├── taxonomy/        # rules, scoring, gravity, transfer
├── pedagogy/        # feedback, dosage, templates
├── psychometrics/   # IRT, BKT, spaced repetition, calibration
└── data/            # YAMLs : rules/, rubrics/, fewshots/, l1_transfer/, tolerance_matrix/
```

## Roadmap

- [x] Phase A — scaffold (0.5j)
- [ ] Phase B — port taxonomy layer (2-3j)
- [ ] Phase C — port pedagogy layer + YAMLize constants (2-3j)
- [ ] Phase D — `LanguageDomain` Protocol-concrete (1j)
- [ ] Phase E — webapp refactor + flag `USE_ACADEMIE_CORE` canary (2j)
- [ ] Phase F — battery + bascule full (1-2j)

Voir [sprint4_preimpl_review.md](../../docs/00-project/sprint4_preimpl_review.md) pour le détail.
