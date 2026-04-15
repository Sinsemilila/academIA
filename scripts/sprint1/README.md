# Sprint 1 — Calibration empirique (Path A)

Scripts de calibration des tiers de gravité d'erreur sur corpus externes (W&I + LOCNESS BEA 2019 + EFCAMDAT si dispo).

## Contexte

Remplace les poids arbitraires `ignored=0.0 / noted=0.3 / penalized=0.8` de
`webapp/backend/app/config/tolerance_matrix.yaml` par des valeurs calibrées via
GLMM + Cox PH sur un corpus externe de plusieurs milliers d'apprenants.

AcademIA interne (9 rows `error_log`) est trop petit pour GLMM random-effects.
On calibre sur corpus externe, et on re-calibrera sur AcademIA au Sprint 1.5
quand la data sera accumulée.

Voir plan complet : `/root/.claude/plans/encapsulated-sprouting-flamingo.md`.
Voir roadmap : `docs/00-project/roadmap.md` § Sprint 1.

## Structure

```
scripts/sprint1/
├── README.md                   (this file)
├── requirements.txt            (Python deps)
├── .gitignore                  (venv, __pycache__, *.pyc, results/)
├── 00_setup.sh                 (venv + install)
├── 01_download_corpus.py       (W&I, CLC-FCE, EFCAMDAT)
├── errant_to_academie.yaml     (28 ERRANT tags → 57 AcademIA codes)
├── 02_normalize.py             (M2 → Parquet)
├── 03_eda.py                   (stats + figures)
├── 04_tier_definition.py       (percentile-based empirical tiers)
├── 05_glmm_fit.py              (NumPyro hierarchical logistic regression)
├── 06_cox_ph.py                (lifelines half-life)
├── 07_generate_v2_draft.py     (write tolerance_matrix_v2_draft.yaml)
└── tests/
    └── test_mapping.py         (pytest coverage ERRANT ≥95%)
```

## Data paths

Raw + processed corpus : `/mnt/cosmos-data/sprint1/data/` (hors git, couvert par
restic niveau 3 via `/mnt/cosmos-data/backups/`).

Results : `/mnt/cosmos-data/sprint1/results/` (JSON + figures).

Output draft matrix : `/opt/academie/webapp/backend/app/config/tolerance_matrix_v2_draft.yaml`

## Usage

```bash
cd /opt/academie/scripts/sprint1
./00_setup.sh                   # create venv, install deps
source venv/bin/activate
python 01_download_corpus.py    # interactive for EFCAMDAT registration
python 02_normalize.py
python 03_eda.py
python 04_tier_definition.py
python 05_glmm_fit.py
python 06_cox_ph.py             # skipped if no longitudinal data
python 07_generate_v2_draft.py
```

## Dépendances externes

- Python 3.13 (système)
- NumPyro + JAX pour GLMM bayésien hiérarchique (pas de R sur le système, pymer4 non utilisé)
- spaCy `en_core_web_sm` (installé au setup)
- ~500 MB disque pour corpus raw + processed

## Impact prod

**Aucun**. Les scripts sont offline. Le fichier `tolerance_matrix.yaml`
actuellement en prod n'est **pas** modifié. La bascule vers `v2_draft` se fait
en Sprint 2 après review.
