"""Produce the arXiv web-form metadata from the source being submitted.

The skill's rule: derive the title and abstract from the file actually going up, not from
memory and not from a sibling draft, because a paper folder commonly carries two or three
titles and picking the wrong one is invisible.

Writes arxiv/SUBMISSION_METADATA.md, ready to paste field by field.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARX = ROOT / "arxiv"
TEX = (ARX / "timesfm_vs_classical.tex").read_text(encoding="utf-8")


def brace_arg(cmd: str) -> str:
    m = re.search(r"\\" + cmd + r"\{", TEX)
    if not m:
        return ""
    i = TEX.index("{", m.start())
    depth = 0
    for j in range(i, len(TEX)):
        if TEX[j] == "{":
            depth += 1
        elif TEX[j] == "}":
            depth -= 1
            if depth == 0:
                return TEX[i + 1:j]
    return ""


def delatex(s: str) -> str:
    """Strip LaTeX to the plain text arXiv's abstract field wants."""
    s = re.sub(r"%.*", "", s)
    s = re.sub(r"\\(emph|textbf|textit|code|pkg|proglang|text)\{([^{}]*)\}", r"\2", s)
    s = re.sub(r"\\citep?\{[^}]*\}", "", s)
    s = s.replace(r"\,", " ").replace(r"\%", "%").replace("---", "--")
    s = s.replace(r"$1.31\times$", "1.31x").replace(r"$2.2\times$", "2.2x")
    s = re.sub(r"\$([^$]*)\$", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", "", s)
    s = s.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()


title = re.sub(r"\s+", " ", brace_arg("Plaintitle") or brace_arg("title")).strip()
abstract = delatex(brace_arg("Abstract"))

n_fig = len(re.findall(r"\\begin\{figure\}", TEX))
n_tab = len(re.findall(r"\\begin\{table\}", TEX))
for frag in ARX.glob("tab_*.tex"):
    n_tab += len(re.findall(r"\\begin\{table\}", frag.read_text(encoding="utf-8")))
pages = 23

md = f"""# arXiv submission metadata

Generated from `arxiv/timesfm_vs_classical.tex` -- the file actually being uploaded.

## Title
{title}

## Authors
Ebrahim Khaled Ebrahim

(arXiv format: first names first, comma-separated. NOT the BibTeX "Ebrahim, E. K." form.)

## Abstract  ({len(abstract)} characters; arXiv limit is 1920)
{abstract}

## Categories
- **Primary: `stat.ME`** (Methodology). The author is already endorsed here and his other
  preprints sit in it, so the family clusters in one index. The transferable contribution is
  about how such comparisons should be *designed and evaluated* -- a contamination-free design,
  and a result that reverses between metrics -- which is methodological rather than applied.
- Cross-list: **`stat.AP`** (Applications) -- it is a practical which-method-when study.
- Cross-list: **`cs.LG`** -- the foundation-model audience reads there, and this paper is
  partly addressed to it.

Cross-listing is free and needs no separate endorsement.

## Comments
{pages} pages, {n_fig} figures, {n_tab} tables. Pre-registered protocol; all deviations logged.
Submitted to the Austrian Journal of Statistics. Code, per-series results and the frozen
protocol: [ZENODO CONCEPT DOI -- insert after publishing the deposit]

## Licence
**Recommended: arXiv's perpetual, non-exclusive licence.**

This is IRREVERSIBLE and is the author's decision, not mine. The non-exclusive licence keeps
every downstream option open, gold open access included, and does not complicate a later
copyright transfer. It also matches the licence used for the DeepGOF-1 preprint, so the family
stays consistent. A CC-BY or CC0 choice on v1 cannot be undone.

## Fields to leave BLANK
- **Journal reference** -- blank until the paper is actually published; add it then.
- **External DOI** -- blank. This field is for the published *journal* version only. The Zenodo
  DOI goes in Comments, never here.
- **Report number** -- blank; no institutional report number.
- **MSC/ACM class** -- the paper declares none, so none is invented.

## Overlap declaration
None required. This paper shares no text with the author's thesis or with his goodness-of-fit
preprints (arXiv:2607.15454, arXiv:2607.16344, arXiv:2608.20511); it is his first paper on
forecasting and has no textual overlap with any of them.

## Before pressing submit
1. Upload `arxiv_submission.zip` ({len(list(ARX.iterdir()))} files, flat, no PDF of the paper).
2. Let arXiv process it, then **view arXiv's OWN generated PDF** -- that build, not the local
   one, is what the world sees. Check the title, the author name, all {n_fig} figures, and that
   no reference renders as [?].
3. Submit before 14:00 US Eastern, Mon-Fri, for next-morning announcement.
4. For any later version use **Replace**, never a new submission, so one identifier accrues all
   the citations.
"""

out = ARX / "SUBMISSION_METADATA.md"
out.write_text(md, encoding="utf-8")
print(md)
print(f"\nwritten to {out.relative_to(ROOT)}")
if len(abstract) > 1920:
    print(f"\n!! ABSTRACT IS {len(abstract) - 1920} CHARACTERS OVER THE LIMIT -- trim it")
