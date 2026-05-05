# Sprint 2 Phase A — tests régression

Tests auto pour valider que v2 tolerance matrix ne casse rien vs v1.

## Structure

```
scripts/sprint2/
├── README.md                    (this file)
└── tests/
    ├── test_weights_parse.py              (sanity: v2 yaml loads + codes mapped)
    ├── test_retrospective_v1_vs_v2.py     (score existing error_log with both matrices)
    └── test_synthetic_battery.py          (replay phase1b 189 cases on both)
```

## Run

```bash
cd /opt/academia/scripts/sprint2
../sprint1/venv/bin/pytest tests/ -v
```

Venv réutilisé depuis Sprint 1. pytest + pyyaml + pandas déjà installés.

## Outputs

- `/mnt/cosmos-data/sprint1/results/v1_vs_v2_retrospective.json`
- `/mnt/cosmos-data/sprint1/results/v1_vs_v2_synthetic.json`

## Invariants testés

1. **Parse** : v2 yaml valide, toutes les 12 familles présentes, codes `rules.py` ↔ `matrix` consistants
2. **Retrospective** : delta score v1→v2 sur 9 rows réels dans fourchette raisonnable
3. **Synthetic** : replay 189 cases phase1b, delta par (family, level) cohérent avec direction empirique
