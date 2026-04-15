"""Download learner corpora for Sprint 1 calibration.

Targets (in priority order):
  1. W&I + LOCNESS (BEA 2019 shared task) — PUBLIC, ~5k essays with CEFR + ERRANT M2
  2. CLC-FCE — via downstream mirror if available
  3. EFCAMDAT — needs academic registration, print instructions only

Output : /mnt/cosmos-data/sprint1/data/raw/
"""
from __future__ import annotations

import hashlib
import sys
import tarfile
from pathlib import Path

import requests
from tqdm import tqdm

RAW = Path("/mnt/cosmos-data/sprint1/data/raw")
RAW.mkdir(parents=True, exist_ok=True)


CORPORA = [
    {
        "name": "wi_locness",
        "url": "https://www.cl.cam.ac.uk/research/nl/bea2019st/data/wi+locness_v2.1.bea19.tar.gz",
        "filename": "wi_locness_v2.1.bea19.tar.gz",
        "expected_min_size_mb": 1,
        "extract": True,
    },
]


def _download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  already present: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB) — skip")
        return True
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with (
            open(dest, "wb") as f,
            tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as pbar,
        ):
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    except Exception as exc:
        print(f"  ❌ download failed: {exc}", file=sys.stderr)
        dest.unlink(missing_ok=True)
        return False
    return True


def _extract_tar(tarball: Path, dest_dir: Path) -> None:
    if (dest_dir / tarball.stem.replace(".tar", "")).exists():
        print(f"  already extracted: {dest_dir / tarball.stem}")
        return
    print(f"  extracting {tarball.name} → {dest_dir}/")
    with tarfile.open(tarball, "r:gz") as tf:
        tf.extractall(dest_dir, filter="data")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> int:
    print(f"Download dir: {RAW}\n")
    rc = 0
    for c in CORPORA:
        print(f"==> {c['name']}")
        dest = RAW / c["filename"]
        ok = _download(c["url"], dest)
        if not ok:
            rc = 1
            continue
        size_mb = dest.stat().st_size / 1e6
        if size_mb < c["expected_min_size_mb"]:
            print(f"  ⚠️ file smaller than expected ({size_mb:.1f} MB < {c['expected_min_size_mb']} MB)")
        print(f"  sha256 prefix: {_sha256(dest)}")
        if c.get("extract"):
            _extract_tar(dest, RAW)

    print("\n==> EFCAMDAT (manual step)")
    print(
        "  EFCAMDAT (1.18M texts, 174k learners, 16 CEFR levels) requires academic registration.\n"
        "  → https://ef-lab.mmll.cam.ac.uk/EFCAMDAT.html\n"
        "  If granted, drop the dump at /mnt/cosmos-data/sprint1/data/raw/efcamdat/\n"
        "  Sprint 1 Path A can complete with W&I alone — Cox PH will be skipped without longitudinal data."
    )
    return rc


if __name__ == "__main__":
    sys.exit(main())
