"""Assemble the reproduction archive that gets deposited on Zenodo.

The archive is built into release/timesfm-classical/ as a self-contained compendium: the whole
pipeline, every per-series result behind every table and figure, the frozen protocol, the
deviation log, the figures and the manuscript source.

Deliberately EXCLUDED, each for a reason:

  data/m4_raw/                          291 MB of the public M4 competition download. It is
                                        re-fetched automatically by code/07_realdata.py and
                                        redistributing it adds nothing. The seeded 1,000-series
                                        SAMPLE is included, since that is what makes the
                                        real-data tier reproducible.
  results/realdata_classical_misordered.npz
                                        17 MB of forecasts known to be mis-aligned (see
                                        DEVIATIONS.md D-06). The bug, its detection and its
                                        repair are fully documented and the repair script is
                                        included; shipping the broken arrays would only invite
                                        someone to use them.
  template/ajs-public/                  The journal's own LaTeX class, not ours to redistribute.
                                        Fetched from the journal's repository; the URL is in
                                        the README.
  build artefacts                       .aux/.log/.out/.bbl/.blg, __pycache__, .bak files.

Usage:  python code/98_build_release.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REL = ROOT / "release" / "timesfm-classical"

SKIP_EXT = {".aux", ".log", ".out", ".bbl", ".blg", ".synctex.gz", ".pyc", ".bak", ".toc"}
SKIP_NAMES = {"realdata_classical_misordered.npz", ".DS_Store"}
# _out / _build are scratch directories used to rebuild the PDF when the canonical
# one is locked by a viewer; they must never reach the archive.
SKIP_DIRS = {"__pycache__", "m4_raw", "ajs-public", ".git", "_out", "_build"}


def keep(p: Path) -> bool:
    if p.name in SKIP_NAMES or p.suffix in SKIP_EXT:
        return False
    if ".bak_" in p.name:
        return False
    return not any(part in SKIP_DIRS for part in p.parts)


def prefer_fresh_pdfs(src: Path, dst: Path) -> list[str]:
    """Archive manuscript/_out/*.pdf in place of an older canonical PDF of the same name."""
    swapped = []
    scratch = src / "_out"
    if not scratch.is_dir():
        return swapped
    for built in sorted(scratch.glob("*.pdf")):
        canonical = src / built.name
        if canonical.exists() and canonical.stat().st_mtime >= built.stat().st_mtime:
            continue
        shutil.copy2(built, dst / built.name)
        swapped.append(built.name)
    return swapped


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    if not src.exists():
        return 0
    for p in sorted(src.rglob("*")):
        if not p.is_file() or not keep(p):
            continue
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        n += 1
    return n


def _force_remove(func, path, exc_info):
    """rmtree callback: clear the read-only bit and retry.

    Windows raises PermissionError when removing a directory that another process has open
    (indexer, antivirus, an editor). Retrying after clearing the read-only attribute handles
    the common case; anything still locked is reported rather than silently skipped.
    """
    import os
    import stat
    import time

    for delay in (0.1, 0.5, 1.0):
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
            return
        except OSError:
            time.sleep(delay)
    print(f"  ! could not remove {path} (locked); leaving it in place")


def main() -> None:
    # Clear the tree but PRESERVE .git: this directory is the working copy of the public
    # repository, so blowing away .git would detach it from its remote and lose the history.
    # (It did exactly that once.)
    if REL.exists():
        for child in list(REL.iterdir()):
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child, onexc=_force_remove)
            else:
                child.unlink()
        print("  cleared previous contents (.git preserved)")
    REL.mkdir(parents=True, exist_ok=True)

    total = 0
    for sub in ["code", "results", "figures", "manuscript"]:
        n = copy_tree(ROOT / sub, REL / sub)
        print(f"  {sub}/: {n} files")
        total += n
        for name in prefer_fresh_pdfs(ROOT / sub, REL / sub):
            print(f"    ! {sub}/{name}: archived the newer build from _out/ "
                  f"(the canonical file is older -- it is probably open in a viewer)")

    # the seeded M4 sample only, not the raw archive
    sample = ROOT / "data" / "m4_monthly_sample_1000.parquet"
    if sample.exists():
        (REL / "data").mkdir(exist_ok=True)
        shutil.copy2(sample, REL / "data" / sample.name)
        print("  data/: 1 file (the seeded M4 sample; the raw archive is re-fetched by code)")
        total += 1

    for doc in ["README.md", "SPEC.md", "PREREGISTRATION.md", "DEVIATIONS.md",
                "LICENSE", ".zenodo.json", "SHARH_ARABIC.md", "SHARH_ARABIC.pdf",
                "SHARH_ARABIC.html"]:
        src = ROOT / doc
        if src.exists():
            shutil.copy2(src, REL / doc)
            print(f"  {doc}")
            total += 1

    # Exclude .git from the size report: it is the repository's own history, not archive
    # content, and counting it makes the archive look far larger than it is.
    size = sum(f.stat().st_size for f in REL.rglob("*")
               if f.is_file() and ".git" not in f.parts)
    print(f"\nrelease/timesfm-classical/: {total} files, {size / 1e6:.1f} MB (excluding .git)")
    print("next: python code/99_deposit_zenodo.py --dry-run")


if __name__ == "__main__":
    main()
