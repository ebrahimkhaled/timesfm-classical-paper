"""Revision after supervisor review, part D: real data, operational section, discussion, back matter.

Addresses: the standalone section "When to use which" removed as unnecessary, with its table
moved into the Discussion as a subsection of practical recommendations; opening statements of
subdivisions for the operational section and the Discussion; academic headings; first-person
plural removed; title-only captions with notes for the remaining hand-written tables; a
limitation on the choice of parameter values; the bibliography placed before the appendix, so
the appendix table can no longer float into the reference list.
"""

from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "manuscript" / "timesfm_vs_classical.tex"


def span(s: str, old: str) -> tuple[int, int]:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old.split()[:8]}"
    return matches[0].start(), matches[0].end()


def swap(s: str, old: str, new: str) -> str:
    a, b = span(s, old)
    return s[:a] + new.strip("\n") + s[b:]


REPLACEMENTS = [
    # ---- real data
    (r"""\section{Real data: M4 Monthly}""", r"""\section{Application to M4 monthly data}"""),
    (r"""The simulation tier buys freedom from contamination at the cost of realism. This section pays
some of it back, with the caveat stated up front rather than buried: \textbf{M4 is
contamination-suspect}. It is a widely used public benchmark and is very likely inside
TimesFM-3's pre-training corpus \citep{meyer2025leakage}. Any advantage TimesFM-3 shows here may
therefore be memory rather than skill, which is exactly why the simulation tier carries the
paper's primary claim. This tier answers a different and narrower question: which of the
simulated regimes do real monthly series resemble?""",
     r"""The simulation tier secures freedom from contamination at the cost of realism. This section
complements it with real data, subject to an important caveat: \textbf{the M4 data may be
contaminated}. M4 is a widely used public benchmark and is likely to be contained in TimesFM-3's
pre-training corpus \citep{meyer2025leakage}, so an advantage of TimesFM-3 here may reflect
memorisation rather than forecasting skill; for this reason the simulation tier carries the
primary claim. The real-data tier addresses a narrower question, namely which of the simulated
regimes real monthly series resemble. \sectionref{sec:m4design} describes the sampling and
evaluation design, and \sectionref{sec:m4results} reports the results."""),
    (r"""\subsection{Design}""", r"""\subsection{Sampling and evaluation design}
\label{sec:m4design}"""),
    (r"""We draw a seeded random sample of 1\,000 series from the 32\,581 M4 Monthly series long enough
for the design, and evaluate each at three rolling origins""",
     r"""A seeded random sample of 1\,000 series is drawn from the 32\,581 M4 monthly series long enough
for the design, and each series is evaluated at three rolling origins"""),
    (r"""maximum 1\,808. This is deliberately not toy data.""", r"""maximum 1\,808."""),
    (r"""\subsection{Results}""", r"""\subsection{Empirical results}
\label{sec:m4results}"""),
    (r"""\begin{table}[t!]
\centering
\caption{M4 Monthly, 1\,000 series at up to three rolling origins each (2\,932 windows in all),
$h = 18$. Paired Wilcoxon across
series, Benjamini--Hochberg corrected. The pattern matches the simulation: TimesFM-3 beats every
classical method except AutoARIMA, against which it ties---and here the equal-weight combination
also ties.}
\label{tab:realdata}""",
     r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Comparison of TimesFM-3 with the classical methods on 1\,000 M4 monthly series.}
\label{tab:realdata}"""),
    (r"""vs combination     & 0.907 & 0.996 & 48.5 & 0.27      & tie \\
\bottomrule
\end{tabular}
\end{table}""",
     r"""vs combination     & 0.907 & 0.996 & 48.5 & 0.27      & tie \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Up to three rolling origins per series (2\,932 windows in all), $h = 18$.
Mean MASE is that of the method named in each row; a median ratio below 1 and a share of series
above 50\% favour TimesFM-3. Paired Wilcoxon tests across series, Benjamini--Hochberg corrected.
\end{tablenotes}
\end{threeparttable}
\end{table}"""),
    (r"""First, \textbf{the tiers agree}.""", r"""First, \textbf{the two tiers agree}."""),
    (r"""Real monthly data
sits in the estimable regime, and the real-data result is what \sectionref{sec:results} predicts
for it.""",
     r"""Real monthly data
therefore fall in the estimable regime, and the real-data result is the one that
\sectionref{sec:results} predicts for that regime."""),
    (r"""Second, \textbf{the probabilistic result splits}, and the two halves point opposite ways.""",
     r"""Second, \textbf{the probabilistic results diverge}."""),

    # ---- operational considerations
    (r"""\section{Costs that do not appear in an accuracy table}
\label{sec:licence}

Accuracy is one input to the decision and, for many deployments, not the binding one.""",
     r"""\section{Operational considerations}
\label{sec:operational}

Accuracy is not the only criterion for choosing a forecasting method. This section considers four
further criteria: computational cost (\sectionref{sec:cost}), the licensing of model weights
(\sectionref{sec:licence}), interpretability and diagnostics (\sectionref{sec:interpret}), and
the theoretical basis of prediction intervals (\sectionref{sec:intervals})."""),
    (r"""\subsection{Computational cost, which runs the opposite way to expectation}""",
     r"""\subsection{Computational cost}
\label{sec:cost}"""),
    (r"""It is natural to assume that a 330-million-parameter network is the expensive option and a
three-parameter statistical model the cheap one. On this hardware that is emphatically false.""",
     r"""A 330-million-parameter network might be expected to be more expensive to run than a
statistical model with a handful of parameters. On the hardware used here, the reverse holds."""),
    (r"""\begin{table}[t!]
\centering
\caption{Wall-clock cost per series, each method timed separately on 200 seasonal series of
length 96 ($h = 12$). TimesFM-3 was run on an NVIDIA GTX 1660 Ti; its one-off model load of
3.0\,s is excluded, as are the classical methods' import costs.}
\label{tab:timing}""",
     r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Wall-clock computing time per series.}
\label{tab:timing}"""),
    (r"""\textbf{AutoARIMA} & \textbf{2382.7} & $\mathbf{102.8\times}$ \\
\bottomrule
\end{tabular}
\end{table}""",
     r"""\textbf{AutoARIMA} & \textbf{2382.7} & $\mathbf{102.8\times}$ \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Each method timed separately on 200 seasonal series of length 96
($h = 12$). TimesFM-3 was run on an NVIDIA GTX 1660 Ti; its one-off model load of 3.0\,s is
excluded, as are the classical methods' import costs.
\end{tablenotes}
\end{threeparttable}
\end{table}"""),
    (r"""Memory was also pre-registered as an operational cost, and the honest report is that our
measurement of it is weak.""",
     r"""Memory use was also pre-registered as an operational cost, but its measurement here is limited."""),
    (r"""Two qualifications keep this honest, and the second matters more than the headline ratio.""",
     r"""Two qualifications apply, and the second is more important than the per-series ratio."""),
    (r"""What it is not, on any measure taken here, is the expensive
option.""",
     r"""On none of the measures taken here is it the more expensive
option."""),
    (r"""\subsection{Licensing}""", r"""\subsection{Licensing of model weights}
\label{sec:licence}"""),
    (r"""The practical consequence is absolute and prior to any accuracy consideration:""",
     r"""This restriction takes precedence over any accuracy consideration:"""),
    (r"""We note this not as criticism but because it is routinely omitted from model comparisons, and
it inverts the ranking for an entire class of users.""",
     r"""The point is noted because licensing is routinely omitted from model comparisons, although it
determines which models are admissible for an entire class of users."""),
    (r"""\subsection{Interpretability and diagnosis}""", r"""\subsection{Interpretability and diagnostics}
\label{sec:interpret}"""),
    (r"""\subsection{Prediction intervals}""", r"""\subsection{Theoretical basis of prediction intervals}
\label{sec:intervals}"""),
    (r"""\sectionref{sec:results} shows the learned quantiles are in fact better calibrated on
average---but empirically, on these processes, not by construction, and their behaviour on a
process unlike anything in the pre-training corpus is unknown by definition.""",
     r"""\sectionref{sec:coverage} shows that the learned quantiles are better calibrated on
average, but this holds empirically for these processes rather than by construction, and their
behaviour on a process unlike anything in the pre-training corpus is unknown."""),

    # ---- discussion
    (r"""\section{Discussion}

\subsection{What the evidence supports, and what it does not}""",
     r"""\section{Discussion}
\label{sec:discussion}

This section assesses the pre-registered hypotheses (\sectionref{sec:hypotheses}), interprets the
balance between robustness and peak accuracy (\sectionref{sec:tradeoff}), translates the evidence
into practical recommendations (\sectionref{sec:recommendations}), and states the limitations of
the study (\sectionref{sec:limitations}).

\subsection{Assessment of the pre-registered hypotheses}
\label{sec:hypotheses}"""),
    (r"""That every hypothesis failed in some respect is the strongest argument for having pre-registered
them. Had the predictions been written after the results, this section would have reported five
confirmations.""",
     r"""That every hypothesis failed in some respect illustrates the value of pre-registration: the
hypotheses were stated before any result was available and are assessed here as they were stated."""),
    (r"""\subsection{Interpreting the split decision}""", r"""\subsection{Robustness versus peak accuracy}
\label{sec:tradeoff}"""),
    (r"""It would be easy to read 16 cell wins against 20 as ``the classical methods still win''. That
reading is available but shallow, because the 20 are distributed across five different
methods---AutoARIMA 10, seasonal naive 4, and two each for the others.""",
     r"""A count of 16 cell wins against 20 might be read as evidence that the classical methods remain
superior. That reading overlooks the fact that the 20 wins are distributed across five different
methods: AutoARIMA 10, seasonal naive 4, and two each for the others."""),
    (r"""The honest summary is therefore neither ``foundation models have won'' nor ``classical methods
remain superior''. It is that \textbf{TimesFM-3 buys robustness, not peak accuracy},""",
     r"""The evidence therefore supports neither the conclusion that foundation models have superseded
classical methods nor the conclusion that classical methods remain superior. It supports a
narrower conclusion: \textbf{TimesFM-3 provides robustness rather than peak accuracy},"""),
    (r"""For a forecaster with ten thousand
heterogeneous series and no capacity to diagnose each one, it is the whole argument.""",
     r"""For a forecaster with ten thousand
heterogeneous series and no capacity to diagnose each one, the trade is decisive."""),
    (r"""\subsection{Limitations}

Five limitations bound these conclusions.""",
     r"""\subsection{Limitations}
\label{sec:limitations}

Seven limitations bound these conclusions."""),
    (r"""Fifth, the intermittent-demand analysis of \sectionref{sec:results} is post hoc:""",
     r"""Fifth, the intermittent-demand analysis of \sectionref{sec:croston} is post hoc:"""),
    (r"""so nothing here should be read as a claim about
foundation models in general.""",
     r"""so nothing here should be read as a claim about
foundation models in general.

Seventh, the results are conditional on the parameter values in \tableref{tab:dgps}. The values
were chosen to place each process unambiguously within its regime rather than to sample the
parameter space, and the best method in a given cell may change for parameters closer to the
boundaries of the stationarity region, for weaker intermittency or for smaller structural breaks."""),

    # ---- conclusion
    (r"""\section{Conclusion}""", r"""\section{Conclusion}
\label{sec:conclusion}"""),
    (r"""We compared TimesFM-3 with five classical alternatives""",
     r"""This study compared TimesFM-3 with five classical alternatives"""),
    (r"""on two seasonal cycles, AutoETS lost to a one-line rule by a factor of
2.7 on data it had itself generated.""",
     r"""with two seasonal cycles, AutoETS had a mean MASE 2.7 times that of the
seasonal naive method on data generated by an ETS process."""),
    (r"""TimesFM-3 is 103 times
faster per series than AutoARIMA---the foundation model is the cheap option, not the expensive
one, though parallelising the classical suite across 22 cores narrows the end-to-end gap to
$2.3\times$.""",
     r"""TimesFM-3 is 103 times
faster per series than AutoARIMA, so the foundation model is the less expensive option per series,
although parallelising the classical suite across 22 cores narrows the end-to-end difference to
$2.3\times$."""),
    (r"""For a large class of readers
that second point settles the question before any of the above becomes relevant.""",
     r"""For commercial applications,
this restriction takes precedence over the accuracy comparison."""),

    # ---- computational details
    (r"""Three points of research practice are worth stating explicitly, since they bear on how much
weight the results carry.""",
     r"""Three aspects of research practice bear on the weight the results can carry."""),
    (r"""Every identifier in the bibliography was checked by resolving it, rather than written from
memory. The check parses the bibliography file itself and resolves each DOI through
\code{doi.org} content negotiation, which answers for both registration agencies---necessary
because arXiv DOIs are issued by DataCite and are invisible to the Crossref API. Two traps
motivated this. A title-based Crossref \emph{search} returns the wrong record for several of the
classical references, including the working-paper version of \citet{diebold1995comparing} and a
later reprint of \citet{hodges1963}; and an earlier checker that maintained its own list of DOIs
in parallel with the bibliography silently drifted out of step with it. Works published at
venues that mint no DOI---PMLR, TMLR, OpenReview and the Curran NeurIPS proceedings---are cited
by their proceedings URL, with the preprint identifier given in a note. And the two hypotheses the data refuted are reported in
\sectionref{sec:results} at the same prominence as those it supported.""",
     r"""Every DOI in the bibliography was resolved through \code{doi.org} content negotiation and its
record compared with the entry, and works published at venues that issue no DOI are cited by
their proceedings URL, with the preprint identifier given in a note. Finally, the two hypotheses
refuted by the data are reported in \sectionref{sec:hypotheses} with the same prominence as those
that were partially supported."""),

    # ---- appendix
    (r"""\section{MAPE, and why it is not the headline metric}""",
     r"""\section{Results under the mean absolute percentage error}"""),
    (r"""The D8 row is the argument:""", r"""The D8 row illustrates the problem:"""),
]

RECOMMENDATIONS_INTRO = r"""
\subsection{Practical recommendations}
\label{sec:recommendations}

\tableref{tab:decision} translates the evidence into recommendations. They are deliberately
narrow: they apply to the regimes examined, and they name more than one option wherever the
evidence does not support a single preference.

"""


def main() -> None:
    s = TEX.read_text(encoding="utf-8")
    if "\\label{sec:recommendations}" in s:
        print("part D already applied")
        return

    # 1. lift the decision table out of the standalone section, then delete that section
    a, _ = span(s, r"""\section{When to use which}""")
    t0 = s.index("\\begin{table}", a)
    t1 = s.index("\\end{table}", t0) + len("\\end{table}")
    table = s[t0:t1]
    s = s[:a] + s[t1:].lstrip("\n")

    table = swap(table, r"""\begin{table}[t!]
\centering
\caption{When to prefer which family, from the evidence in \sectionref{sec:results}. Bold marks
a preference supported by significant differences; the remaining rows rest on considerations
outside the accuracy comparison.}
\label{tab:decision}""",
                 r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Recommended forecasting family by situation.}
\label{tab:decision}""")
    table = swap(table, r"""\bottomrule
\end{tabular}
\end{table}""",
                 r"""\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Based on the evidence in Sections~\ref{sec:results}--\ref{sec:operational}.
Bold marks a preference supported by significant differences; the remaining rows rest on
considerations outside the accuracy comparison.
\end{tablenotes}
\end{threeparttable}
\end{table}""")
    table = swap(table, r"""But WORSE on RMSSE and sMAPE (D8)""", r"""but worse on RMSSE and sMAPE (D8)""")
    table = swap(table, r"""AutoARIMA is even with TimesFM-3 (11--9) and is free, interpretable and diagnosable""",
                 r"""AutoARIMA and TimesFM-3 are close (11--9 significant comparisons); AutoARIMA is free to use, interpretable and diagnosable""")

    # 2. all other edits
    for old, new in REPLACEMENTS:
        s = swap(s, old, new)

    # 3. the recommendations subsection sits before the limitations
    a, _ = span(s, r"""\subsection{Limitations}""")
    s = s[:a] + RECOMMENDATIONS_INTRO.lstrip("\n") + table + "\n\n" + s[a:]

    # 4. references before the appendix, so the appendix table cannot float into them
    bib = "%% ajs.cls already issues \\bibliographystyle{ajs}; only the database is needed here.\n\\bibliography{refs}\n"
    assert s.count(bib) == 1, "bibliography block not found"
    s = s.replace(bib, "", 1)
    a = s.index(chr(10) + chr(92) + "appendix" + chr(10)) + 1  # the command itself, not appendixref
    s = s[:a] + bib + "\n\\newpage\n" + s[a:]

    TEX.write_text(s, encoding="utf-8")
    print(f"part D applied: section removed, table moved, {len(REPLACEMENTS)} edits, "
          "bibliography before appendix")


if __name__ == "__main__":
    main()
