"""Build the Journal of Forecasting upload bundle (submission/jof_upload/ and jof_upload.zip).

Wiley Research Exchange, LaTeX route: "Main Document - LaTeX .tex File", "Main Document - LaTeX PDF",
and every \\input file, class/style file, .bib/.bbl and figure as "LaTeX Supplementary File"; the
Supporting Information PDF and the cover letter separately. Figure paths ../figures/x.pdf are rewritten to
figures/x.pdf so the bundle compiles on its own; the bundle is compiled here to prove it.
"""

import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "manuscript_jof"
OUT = ROOT / "submission" / "jof_upload"


def main():
    # Clear files, not folders: Windows may hold a lock on an open folder.
    if OUT.exists():
        for f in sorted(OUT.rglob("*"), reverse=True):
            if f.is_file():
                f.unlink()
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    tex = (SRC / "timesfm_jof.tex").read_text(encoding="utf-8")
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{\.\./figures/([^}]+)\}", tex)
    tex = tex.replace("{../figures/", "{figures/")
    (OUT / "timesfm_jof.tex").write_text(tex, encoding="utf-8")
    for f in figs:
        shutil.copy2(ROOT / "figures" / f, OUT / "figures" / f)
    inputs = re.findall(r"\\input\{([^}]+)\}", tex)
    for i in inputs:
        shutil.copy2(SRC / f"{i}.tex", OUT / f"{i}.tex")
    for f in ["USG.cls", "NJDnatbib.sty", "lettersp.sty", "wileyNJD-Chicago.bst", "refs.bib"]:
        shutil.copy2(SRC / f, OUT / f)
    shutil.copytree(SRC / "images", OUT / "images", dirs_exist_ok=True)
    for step in (["xelatex", "-interaction=nonstopmode", "timesfm_jof.tex"], ["bibtex", "timesfm_jof"],
                 ["xelatex", "-interaction=nonstopmode", "timesfm_jof.tex"],
                 ["xelatex", "-interaction=nonstopmode", "timesfm_jof.tex"]):
        subprocess.run(step, cwd=OUT, capture_output=True)
    log = (OUT / "timesfm_jof.log").read_text(encoding="utf-8", errors="ignore")
    errors = len(re.findall(r"^!", log, re.M))
    undefined = len(re.findall(r"undefined", log, re.I))
    for ext in (".aux", ".log", ".blg", ".out", ".pag"):
        p = OUT / f"timesfm_jof{ext}"
        if p.exists():
            p.unlink()
    shutil.copy2(SRC / "supporting_information.pdf", OUT / "supporting_information.pdf")
    shutil.copy2(ROOT / "submission" / "cover_letter_JoF.pdf", OUT / "cover_letter_JoF.pdf")
    z = ROOT / "submission" / "jof_upload.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(OUT))
    n = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"bundle: {n} files, {len(figs)} figures, {len(inputs)} inputs; compile errors {errors}, "
          f"undefined {undefined}; {z.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
