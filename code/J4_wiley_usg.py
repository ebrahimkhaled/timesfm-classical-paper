"""JoF version -> Wiley USG.cls (the "NJD" authoring class used by Statistics in Medicine).

Author's decision (2026-09-23): present the submission in Wiley's own class for a more
professional look. JoF accepts free format, so the class is optional; it is used for presentation.

What the conversion does, following the JoF author guidelines:
  * title page (first page): title, authors with ORCID, affiliations, correspondence, running
    title, keywords (<= 6, "|" separated, Wiley style), abstract, then the acknowledgements and the
    five required statements (data availability, funding, conflict of interest, ethics approval,
    permission to reproduce material) and every author's e-mail; the main text starts on page 2;
  * the MAPE appendix moves to a separate supporting-information file (JoF: "appendices should be
    supplied as separate files"), referred to as Supporting Information, Section S1;
  * a complete list of figure legends follows the references (JoF: legends beneath each figure
    AND as a list in the text);
  * references: author-year (USG option ASNA -> wileyNJD-Chicago.bst). JoF's house style is APA
    and is applied by the typesetter; any consistent style is accepted at submission.

The article-class file is kept as timesfm_jof_article.tex.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "manuscript_jof"
SRC = D / "timesfm_jof.tex"
TEMPLATE = Path(r"C:\Users\ebrah\.gemini\Projects\.agent\skills\wiley-statistics-in-medicine\assets\template")

PREAMBLE = r"""%% Journal of Forecasting submission in Wiley's USG.cls (NJD authoring class, v6.0).
%% Build: pdflatex -> bibtex -> pdflatex -> pdflatex
\documentclass[ASNA]{USG}

\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{array}
\usepackage{graphicx}
\usepackage{xurl}
\usepackage{lineno}
\setlength{\emergencystretch}{2em}

\newcommand{\pkg}[1]{\textsf{#1}}
\newcommand{\proglang}[1]{\textsf{#1}}
\newcommand{\code}[1]{\texttt{#1}}
\providecommand{\sectionref}[1]{Section~\ref{#1}}
\providecommand{\tableref}[1]{Table~\ref{#1}}
\providecommand{\figureref}[1]{Figure~\ref{#1}}

\articletype{Research Article}
\received{}\revised{}\accepted{}
\journal{Journal of Forecasting}
\copyyear{2026}\volume{00}\startpage{1}\articledoi{10.1002/for.0000}

%% Required patches to the Wiley demo template (see the wiley-statistics-in-medicine skill):
%% (a) no "OPEN ACCESS" badge on a subscription submission; (b) no demo journal masthead.
\makeatletter
\def\@@articletype{%
  \rule[-4\@p@t]{4\@p@t}{15\@p@t}%
  \hskip -0\@p@t%
  {\arttypefont\bf\uppercase{\letterspace to 1.15\naturalwidth{\@articletype}}}%
}%
\makeatother
\usepackage{etoolbox}
\makeatletter
\patchcmd{\@maketitle}{\includegraphics[width=56mm]{allergy.eps}}{}{}{}
\makeatother

\begin{document}

\title{Foundation or Formula? A Simulation-Based Comparison of Google's TimesFM-3 and Classical
Time-Series Models}

\author[1]{Ebrahim Khaled Ebrahim}[https://orcid.org/0009-0006-7839-8778]
\author[2]{Somaia Mohamed Ali}[https://orcid.org/0009-0002-0940-8451]
\author[3]{Ahmed El-Kotory}[https://orcid.org/0009-0000-1485-0768]
\authormark{EBRAHIM \textsc{et al.}}
\titlemark{TimesFM-3 versus classical models}

\address[1]{\orgdiv{Department of Applied Statistics, Faculty of Business},
\orgname{Alexandria University}, \orgaddress{\city{Alexandria}, \country{Egypt}}}
\address[2]{\orgdiv{Department of Statistics}, \orgname{Alexandria University},
\orgaddress{\city{Alexandria}, \country{Egypt}}}
\address[3]{\orgname{Alexandria University}, \orgaddress{\city{Alexandria}, \country{Egypt}}}

\corres{Ebrahim Khaled Ebrahim, Department of Applied Statistics, Faculty of Business,
Alexandria University, Alexandria, Egypt. \email{ebrahimkhaled@alexu.edu.eg}}

\keywords{Exponential smoothing | Forecast evaluation | Intermittent demand | Simulation study |
Time-series foundation models | Zero-shot forecasting}

\abstract[Abstract]{ABSTRACT}

\maketitle
\setcounter{secnumdepth}{3}

\noindent\textbf{Running title:} TimesFM-3 versus classical models

\medskip
\noindent\textbf{Author e-mail addresses:} Ebrahim Khaled Ebrahim, ebrahimkhaled@alexu.edu.eg;
Somaia Mohamed Ali, somaia.said@alexu.edu.eg; Ahmed El-Kotory, ahmed.elkatory@alexu.edu.eg.

\medskip
\noindent\textbf{Acknowledgements:} ACK

\medskip
\noindent\textbf{Data availability statement:} DATA

\medskip
\noindent\textbf{Funding statement:} No funding was received for this work.

\medskip
\noindent\textbf{Conflict of interest disclosure:} The authors declare no conflicts of interest.

\medskip
\noindent\textbf{Ethics approval statement:} Not applicable; the study uses simulated data and the
publicly available M4 competition data, and involves no human participants.

\medskip
\noindent\textbf{Permission to reproduce material from other sources:} Not applicable.

\newpage
\linenumbers

"""

SI_HEAD = r"""\documentclass[ASNA]{USG}
\usepackage{amsmath}
\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{array}
\usepackage{graphicx}
\usepackage{xurl}
\providecommand{\tableref}[1]{Table~\ref{#1}}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\makeatletter
\def\@@articletype{\rule[-4\@p@t]{4\@p@t}{15\@p@t}\hskip -0\@p@t%
  {\arttypefont\bf\uppercase{\letterspace to 1.15\naturalwidth{\@articletype}}}}
\makeatother
\usepackage{etoolbox}
\makeatletter
\patchcmd{\@maketitle}{\includegraphics[width=56mm]{allergy.eps}}{}{}{}
\makeatother
\articletype{Supporting Information}
\received{}\revised{}\accepted{}
\journal{Journal of Forecasting}
\copyyear{2026}\volume{00}\startpage{1}\articledoi{10.1002/for.0000}
\begin{document}
\title{Supporting Information for ``Foundation or Formula? A Simulation-Based Comparison of
Google's TimesFM-3 and Classical Time-Series Models''}
\author[1]{Ebrahim Khaled Ebrahim}
\author[2]{Somaia Mohamed Ali}
\author[3]{Ahmed El-Kotory}
\authormark{EBRAHIM \textsc{et al.}}
\titlemark{Supporting Information}
\address[1]{\orgname{Alexandria University}, \orgaddress{\country{Egypt}}}
\address[2]{\orgname{Alexandria University}, \orgaddress{\country{Egypt}}}
\address[3]{\orgname{Alexandria University}, \orgaddress{\country{Egypt}}}
\corres{Ebrahim Khaled Ebrahim. \email{ebrahimkhaled@alexu.edu.eg}}
\abstract[Summary]{This file contains supporting information referred to in the main text as
Section S1 onwards.}
\maketitle
"""


def main() -> None:
    s = SRC.read_text(encoding="utf-8")
    if "\\documentclass[ASNA]{USG}" in s:
        print("already converted")
        return
    shutil.copy2(SRC, D / "timesfm_jof_article.tex")
    for f in ("USG.cls", "wileyNJD-Chicago.bst", "NJDnatbib.sty", "lettersp.sty"):
        shutil.copy2(TEMPLATE / f, D / f)
    if not (D / "images").exists():
        shutil.copytree(TEMPLATE / "images", D / "images")

    abstract = s[s.index("\\begin{abstract}") + len("\\begin{abstract}"):s.index("\\end{abstract}")].strip()
    data = re.search(r"\\textbf\{Data availability statement:\} (.*?)\n\n", s, re.S).group(1).strip()
    ack_block = re.search(r"\\section\*\{Acknowledgements\}\n\n(.*?)\n\\section\*\{Data and code availability\}",
                          s, re.S).group(1).strip()
    ack = " ".join(" ".join(ack_block.split("\n\n")).split())

    body = s[s.index("\\end{abstract}") + len("\\end{abstract}"):]
    body = body[:body.index("\\section*{Acknowledgements}")] + \
        body[body.index("\\section*{Data and code availability}"):]
    app = body[body.index("\\appendix"):body.index("\\end{document}")]
    body = body[:body.index("\\newpage\n\\appendix")] if "\\newpage\n\\appendix" in body else \
        body[:body.index("\\appendix")]
    body = body.replace("\\bibliographystyle{plainnat}\n", "")
    body = body.replace("\\appendixref{app:mape}", "Section~S1 of the Supporting Information")

    captions = re.findall(r"\\begin\{figure\}.*?\\caption\{(.*?)\}\s*\\label\{(fig:[^}]*)\}", body, re.S)
    legend = ["", "\\section*{Figure legends}", "", "\\begin{description}"]
    for i, (cap, lab) in enumerate(captions, 1):
        legend.append(f"\\item[Figure {i}.] {' '.join(cap.split())}")
    legend += ["\\end{description}", ""]

    out = PREAMBLE.replace("ABSTRACT", abstract).replace("ACK", ack).replace("DATA", data) + \
        body.strip() + "\n" + "\n".join(legend) + "\n\\end{document}\n"
    SRC.write_text(out, encoding="utf-8")

    app = app.replace("\\appendix\n", "")
    (D / "supporting_information.tex").write_text(SI_HEAD + app + "\n\\end{document}\n", encoding="utf-8")
    print(f"converted; {len(captions)} figure legends listed; appendix -> supporting_information.tex")


if __name__ == "__main__":
    main()
