#!/bin/bash
# Setup Sprint 1 Python environment
# Usage: cd /opt/academie/scripts/sprint1 && ./00_setup.sh
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d venv ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip setuptools wheel
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m spacy download en_core_web_sm

mkdir -p /mnt/cosmos-data/sprint1/data/{raw,processed} /mnt/cosmos-data/sprint1/results

echo "Setup complete. Activate: source /opt/academie/scripts/sprint1/venv/bin/activate"
