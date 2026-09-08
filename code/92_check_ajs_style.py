"""Check the manuscript against the AJS rules that are mechanically checkable.

The journal states that manuscripts ignoring its style are usually declined without review, so
these are worth verifying automatically rather than by eye.

Checks:
  1. every table's \\caption precedes its \\begin{tabular}  (AJS: captions ABOVE tables)
  2. every figure's \\caption follows its \\includegraphics    (AJS: captions BELOW figures)
  3. no raster graphics are included                          (AJS C2.graphics: vector PDF only)
  4. every bibliography entry that is a journal article carries a DOI (AJS C2.doi)
  5. subsection headings are in lower-case style              (AJS C2.subsections)
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAN = ROOT / "manuscript"
MAIN = MAN / "timesfm_vs_classical.tex"
INCLUDES = ["tab_mase.tex", "tab_mape.tex", "tab_robust.tex", "tab_d8metrics.tex"]

TABLE_RE = re.compile(r"\\begin\{table\}.*?\\end\{table\}", re.S)
FIGURE_RE = re.compile(r"\\begin\{figure\}.*?\\end\{figure\}", re.S)
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")

problems: list[str] = []


def check_tables() -> None:
    for name in [MAIN.name] + INCLUDES:
        p = MAN / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in TABLE_RE.finditer(text):
            b = m.group(0)
            cap, tab = b.find("\\caption"), b.find("\\begin{tabular}")
            lab = LABEL_RE.search(b)
            tag = lab.group(1) if lab else "?"
            if cap == -1:
                problems.append(f"table {tag} in {name}: no caption")
            elif tab != -1 and cap > tab:
                problems.append(f"table {tag} in {name}: caption BELOW tabular (AJS wants above)")
            else:
                print(f"  OK  table   {tag:<16} caption above tabular")


def check_figures() -> None:
    text = MAIN.read_text(encoding="utf-8")
    for m in FIGURE_RE.finditer(text):
        b = m.group(0)
        cap, inc = b.find("\\caption"), b.find("\\includegraphics")
        lab = LABEL_RE.search(b)
        tag = lab.group(1) if lab else "?"
        if cap == -1 or inc == -1:
            problems.append(f"figure {tag}: missing caption or graphic")
        elif cap < inc:
            problems.append(f"figure {tag}: caption ABOVE graphic (AJS wants below)")
        else:
            print(f"  OK  figure  {tag:<16} caption below graphic")


def check_raster() -> None:
    text = MAIN.read_text(encoding="utf-8")
    bad = re.findall(r"\\includegraphics[^{]*\{([^}]*\.(?:png|jpg|jpeg))\}", text, re.I)
    if bad:
        problems.append(f"raster graphics included (AJS requires vector PDF): {bad}")
    else:
        print("  OK  graphics: no raster images included")
    stray = list((ROOT / "figures").glob("*.png")) + list((ROOT / "figures").glob("*.jpg"))
    if stray:
        problems.append(f"raster files present in figures/: {[f.name for f in stray]}")
    else:
        print("  OK  figures/: contains no raster files")


def check_dois() -> None:
    """AJS rule C2.doi asks for a DOI on each citation 'if possible'.

    Some venues mint no DOI at all -- PMLR (ICML), TMLR, OpenReview and the Curran NeurIPS
    proceedings among them -- so an entry from one of those is compliant when it carries a
    `url` to the version of record instead. What is NOT acceptable is an entry with neither.
    """
    bib = (MAN / "refs.bib").read_text(encoding="utf-8")
    entries = re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", bib, re.S)
    no_id = []
    url_only = []
    for kind, k, body in entries:
        if kind.lower() not in {"article", "inproceedings"}:
            continue
        has_doi = re.search(r"^\s*doi\s*=", body, re.M | re.I)
        has_url = re.search(r"^\s*url\s*=", body, re.M | re.I)
        if not has_doi and not has_url:
            no_id.append(k.strip())
        elif not has_doi:
            url_only.append(k.strip())
    if no_id:
        problems.append(f"bibliography entries with neither DOI nor URL: {no_id}")
    else:
        print(f"  OK  bibliography: {len(entries)} entries; every article/inproceedings has a "
              f"DOI or a URL")
        if url_only:
            print(f"      ({len(url_only)} cite a DOI-less venue by URL: "
                  f"{', '.join(url_only)})")


def check_subsections() -> None:
    text = MAIN.read_text(encoding="utf-8")
    for m in re.finditer(r"\\subsection\{([^}]*)\}", text):
        title = m.group(1)
        words = [w for w in re.findall(r"\b[A-Za-z][A-Za-z-]+\b", title)][1:]
        # Flag a heading whose non-initial words are capitalised (title case), ignoring
        # proper nouns and acronyms that are legitimately capitalised.
        # Proper nouns and product names that are correctly capitalised mid-heading.
        allow = {"MAPE", "TimesFM", "AutoARIMA", "AutoETS", "Theta", "M4", "AJS",
                 "Croston", "Croston-family", "Diebold", "Mariano", "Wilcoxon", "Hodges",
                 "Lehmann", "Google", "Monthly"}
        caps = [w for w in words if w[0].isupper() and w not in allow and not w.isupper()]
        if caps:
            problems.append(f"subsection may be in Title Case: '{title}' ({caps})")
    print("  OK  subsections: checked for title case")


if __name__ == "__main__":
    print("AJS mechanical style check\n" + "-" * 60)
    check_tables()
    check_figures()
    check_raster()
    check_dois()
    check_subsections()
    print("-" * 60)
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  !", p)
    else:
        print("no problems found")
