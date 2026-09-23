"""Create the Journal of Forecasting manuscript from the AJS source (one-time conversion).

The AJS version (manuscript/) is left untouched as the record of that submission. The JoF version
lives in manuscript_jof/ and is edited directly after this conversion.

JoF accepts free-format submissions (author guidelines, checked 2026-09-23): one file with all
sections; a PDF alongside any LaTeX source; a title page with a running title under 40
characters, up to six keywords, and the data availability, funding, conflict-of-interest and
ethics statements. Its house reference style is APA; any consistent style is accepted at
submission, so natbib author-year is used.

Conversion:
  * ajs.cls front matter -> article class with an explicit title page
  * the \\pkg, \\proglang, \\code macros are defined locally
  * the reference database is copied and extended (J2 adds the new entries)
  * table fragments are copied beside the source
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "manuscript" / "timesfm_vs_classical.tex"
DST_DIR = ROOT / "manuscript_jof"
DST = DST_DIR / "timesfm_jof.tex"

PREAMBLE = r"""\documentclass[11pt]{article}

%% Journal of Forecasting, free-format submission (Wiley author guidelines).
%% Build: pdflatex -> bibtex -> pdflatex -> pdflatex

\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{setspace}
\usepackage{lineno}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{array}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage[authoryear,round]{natbib}
\usepackage{xurl}
\usepackage[hidelinks]{hyperref}
\usepackage{orcidlink}

\newcommand{\pkg}[1]{\textsf{#1}}
\newcommand{\proglang}[1]{\textsf{#1}}
\newcommand{\code}[1]{\texttt{#1}}
\providecommand{\sectionref}[1]{Section~\ref{#1}}
\providecommand{\tableref}[1]{Table~\ref{#1}}
\providecommand{\figureref}[1]{Figure~\ref{#1}}
\providecommand{\appendixref}[1]{Appendix~\ref{#1}}

\begin{document}

%% ------------------------------------------------------------------ title page
\begin{titlepage}
\begin{center}
{\LARGE\bfseries Foundation or Formula? A Simulation-Based Comparison of Google's TimesFM-3 and
Classical Time-Series Models\par}
\vspace{1.5em}
{\large Ebrahim Khaled Ebrahim\,\orcidlink{0009-0006-7839-8778}$^{1}$,
Somaia Mohamed Ali\,\orcidlink{0009-0002-0940-8451}$^{2}$ and
Ahmed El-Kotory\,\orcidlink{0009-0000-1485-0768}$^{3}$\par}
\vspace{1em}
{\small $^{1}$Department of Applied Statistics, Faculty of Business, Alexandria University,
Alexandria, Egypt\\
$^{2}$Department of Statistics, Alexandria University, Alexandria, Egypt\\
$^{3}$Alexandria University, Alexandria, Egypt\par}
\end{center}

\vspace{1.5em}
\noindent\textbf{Correspondence:} Ebrahim Khaled Ebrahim, Department of Applied Statistics,
Faculty of Business, Alexandria University, Alexandria, Egypt.
Email: \href{mailto:ebrahimkhaled@alexu.edu.eg}{ebrahimkhaled@alexu.edu.eg}

\medskip
\noindent\textbf{Running title:} TimesFM-3 versus classical models

\medskip
\noindent\textbf{Keywords:} time-series foundation models; zero-shot forecasting; simulation
study; forecast evaluation; intermittent demand; exponential smoothing

\medskip
\noindent\textbf{Data availability statement:} DATA_STATEMENT

\medskip
\noindent\textbf{Funding statement:} No funding was received for this work.

\medskip
\noindent\textbf{Conflict of interest disclosure:} The authors declare no conflicts of interest.

\medskip
\noindent\textbf{Ethics approval statement:} Not applicable; the study uses simulated data and
the publicly available M4 competition data, and involves no human participants.

\medskip
\noindent\textbf{Permission to reproduce material from other sources:} Not applicable.
\end{titlepage}

\onehalfspacing
\linenumbers

\begin{center}
{\Large\bfseries Foundation or Formula? A Simulation-Based Comparison of Google's TimesFM-3 and
Classical Time-Series Models\par}
\end{center}

\begin{abstract}
ABSTRACT
\end{abstract}

"""


def main() -> None:
    DST_DIR.mkdir(exist_ok=True)
    if DST.exists():
        raise SystemExit(f"{DST} exists; it is edited by hand after the one-time conversion")
    src = SRC.read_text(encoding="utf-8")

    abstract = re.search(r"\\Abstract\{%\n(.*?)\n\}\n", src, re.S).group(1).strip()
    body = src[src.index("\\begin{document}") + len("\\begin{document}"):].lstrip("\n")

    decl = re.search(r"\\textbf\{Data and code availability\.\}(.*?)\n\n", body, re.S)
    data_statement = " ".join(decl.group(1).split())

    # The declarations move to the title page; the paragraph on the raw forecasts stays as a
    # short "Data and code availability" section.
    body = re.sub(r"\\section\*\{Declarations\}.*?\n\nThe raw forecasts",
                  "\\\\section*{Data and code availability}\n\n" + data_statement.replace("\\", "\\\\")
                  + "\n\nThe raw forecasts", body, count=1, flags=re.S)
    body = body.replace("%% ajs.cls already issues \\bibliographystyle{ajs}; only the database is needed here.\n"
                        "\\bibliography{refs}",
                        "\\bibliographystyle{plainnat}\n\\bibliography{refs}")
    assert "\\bibliographystyle{plainnat}" in body

    out = (PREAMBLE.replace("ABSTRACT", abstract).replace("DATA_STATEMENT", data_statement)
           + body)
    DST.write_text(out, encoding="utf-8")

    for f in (ROOT / "manuscript").glob("tab_*.tex"):
        shutil.copy2(f, DST_DIR / f.name)
    shutil.copy2(ROOT / "manuscript" / "refs.bib", DST_DIR / "refs.bib")
    print(f"wrote {DST.relative_to(ROOT)} ({len(out.splitlines())} lines)")


if __name__ == "__main__":
    main()
