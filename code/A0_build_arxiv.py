"""Assemble the arXiv source bundle, flat, and generate the .bbl from the build that ships.

Two things about this paper need care, both of them documented arXiv failure modes.

1. FIGURE PATHS. The manuscript references figures as `../figures/fig1.pdf`. arXiv compiles
   from the root of the submission, so a path that climbs out of the submission directory
   cannot resolve. The fix is to FLATTEN -- copy the figures beside the .tex and strip the
   directory prefix -- not to add them at the zip root while the .tex still names a
   subdirectory, which fails on the server while appearing fine locally.

2. THE CLASS FILE. `ajs.cls` is the Austrian Journal of Statistics class and is NOT in TeX
   Live, so it must travel with the source, along with `oesg.png`, the society logo the class
   includes on the title page. Its own dependencies (booktabs, orcidlink) ARE stock and are
   deliberately not shipped: uploading a copy of a stock package overrides arXiv's and an older
   bundled version meeting a newer kernel is a known failure.

The .bbl is generated inside the bundle directory, from the flattened source, so it matches the
document actually being submitted. `ajs.bst` is used to build it but is not shipped: arXiv does
not run BibTeX when a .bbl is present, and shipping the .bib instead could make it try.

Usage:  python code/A0_build_arxiv.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAN = ROOT / "manuscript"
OUT = ROOT / "arxiv"
MAIN = "timesfm_vs_classical"

# Files that must travel with the source because TeX Live does not have them.
CLASS_FILES = ["ajs.cls", "oesg.png"]
# Generated table fragments the manuscript \inputs.
TABLE_FILES = ["tab_mase.tex", "tab_mape.tex", "tab_robust.tex", "tab_d8metrics.tex",
               "tab_croston.tex"]
FIGURES = ["fig1_example_series.pdf", "fig2_mase_ratio.pdf", "fig3_coverage.pdf",
           "fig4_horizon.pdf"]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)

    # --- 1. the main source, with figure paths flattened -------------------------------
    tex = (MAN / f"{MAIN}.tex").read_text(encoding="utf-8")
    before = tex.count("../figures/")
    tex = tex.replace("../figures/", "")
    print(f"flattened {before} figure path(s): ../figures/X.pdf -> X.pdf")
    (OUT / f"{MAIN}.tex").write_text(tex, encoding="utf-8")

    # --- 2. everything the build needs -------------------------------------------------
    for name in CLASS_FILES + TABLE_FILES:
        src = MAN / name
        if not src.is_file():
            raise SystemExit(f"missing required file: {src}")
        shutil.copy2(src, OUT / name)
    for name in FIGURES:
        src = ROOT / "figures" / name
        if not src.is_file():
            raise SystemExit(f"missing figure: {src}")
        shutil.copy2(src, OUT / name)
    print(f"copied {len(CLASS_FILES)} class file(s), {len(TABLE_FILES)} table fragment(s), "
          f"{len(FIGURES)} figure(s)")

    # --- 3. build IN the bundle, so the .bbl matches what ships -------------------------
    # ajs.bst and refs.bib are needed to RUN bibtex; they are removed afterwards so the
    # shipped bundle carries the .bbl alone.
    shutil.copy2(MAN / "ajs.bst", OUT / "ajs.bst")
    shutil.copy2(MAN / "refs.bib", OUT / "refs.bib")

    print("compiling in the bundle directory ...")
    for step, cmd in [("pdflatex", ["pdflatex", "-interaction=nonstopmode", f"{MAIN}.tex"]),
                      ("bibtex", ["bibtex", MAIN]),
                      ("pdflatex", ["pdflatex", "-interaction=nonstopmode", f"{MAIN}.tex"]),
                      ("pdflatex", ["pdflatex", "-interaction=nonstopmode", f"{MAIN}.tex"])]:
        r = run(cmd, OUT)
        if step == "bibtex" and ("Warning" in r.stdout or "error" in r.stdout.lower()):
            for line in r.stdout.splitlines():
                if "arning" in line or "rror" in line:
                    print(f"   bibtex: {line.strip()}")

    log = (OUT / f"{MAIN}.log").read_text(encoding="utf-8", errors="replace")
    errors = [l for l in log.splitlines() if l.startswith("!")]
    undefined = set(re.findall(r"(?:Citation|Reference) `([^']+)' on page", log))
    pages = re.search(r"Output written on .*? \((\d+) pages", log)
    print(f"   errors: {len(errors)}   undefined: {len(undefined)}   "
          f"pages: {pages.group(1) if pages else '?'}")
    for e in errors[:5]:
        print(f"   ! {e}")
    if undefined:
        print(f"   undefined: {sorted(undefined)[:8]}")

    bbl = OUT / f"{MAIN}.bbl"
    if not bbl.is_file() or bbl.stat().st_size < 500:
        raise SystemExit("the .bbl was not produced; arXiv would have no bibliography")
    print(f"   {MAIN}.bbl produced ({bbl.stat().st_size} bytes)")

    # --- 4. strip build litter, the PDF, and the bib/bst -------------------------------
    drop_ext = {".aux", ".log", ".out", ".blg", ".toc", ".synctex.gz", ".pdf"}
    keep_pdf = set(FIGURES)
    removed = []
    for p in sorted(OUT.iterdir()):
        if p.name in keep_pdf:
            continue
        if p.suffix in drop_ext or p.name in {"ajs.bst", "refs.bib"}:
            p.unlink()
            removed.append(p.name)
    print(f"removed {len(removed)} build/aux file(s): {', '.join(removed)}")

    files = sorted(p.name for p in OUT.iterdir() if p.is_file())
    size = sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())
    print(f"\narxiv/ contains {len(files)} files, {size / 1e6:.2f} MB:")
    for f in files:
        print(f"   {(OUT / f).stat().st_size:>9d}  {f}")
    print("\nnext: python code/A1_verify_arxiv.py   (clean-room compile in an empty directory)")


if __name__ == "__main__":
    main()
