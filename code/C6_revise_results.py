"""Revision after supervisor review, part C: the simulation results section.

Addresses: an opening statement of the section's subdivisions; academic noun-phrase subsection
headings in sentence case; first-person plural removed; the pairwise-comparison table given a
title-only caption with a note; rhetorical phrasing replaced by measured statements; figures
placed with [!htbp].

Two substantive corrections of wording are made against the data. (1) The effect-size paragraph
referred to "the metric disagreement above", which is reported later; it now cites that
subsection. (2) The Croston subsection said TimesFM-3 beats the purpose-built methods "by a wider
margin" than the general-purpose set. On mean MASE its reduction relative to the best Croston-
family method is 19.6-25.7% against 21.7-26.5% relative to the best general-purpose method, so
the margins are similar, and the text now says that.
"""

from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "manuscript" / "timesfm_vs_classical.tex"


def swap(s: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old.split()[:8]}"
    m = matches[0]
    return s[:m.start()] + new.strip("\n") + s[m.end():]


REPLACEMENTS = [
    (r"""\section{Results}
\label{sec:results}

The design yields 7\,200 series, and with six methods and three horizon slices, 129\,600
per-series evaluations. \tableref{tab:mase} reports mean MASE over the full horizon
$h = 1,\dots,12$; \figureref{fig:ratio} shows the same information as the accuracy of
TimesFM-3 relative to the best classical method in each cell.""",
     r"""\section{Simulation results}
\label{sec:results}

This section reports the results of the simulation study. \sectionref{sec:overall} summarises
overall accuracy and the pairwise comparisons, \sectionref{sec:effects} reports effect sizes and a
sensitivity analysis, and \sectionref{sec:estimability} examines the role of estimability.
\sectionref{sec:regimes} and \sectionref{sec:croston} analyse the seasonal and intermittent
regimes, the latter with purpose-built intermittent-demand baselines. \sectionref{sec:horizon}
and \sectionref{sec:coverage} consider accuracy across forecast horizons and the coverage of
prediction intervals, and \sectionref{sec:combination} and \sectionref{sec:mape} report two
robustness analyses.

The design yields 7\,200 series and, with six methods and three horizon slices, 129\,600
per-series evaluations. \tableref{tab:mase} reports mean MASE over the full horizon
$h = 1,\dots,12$, and \figureref{fig:ratio} displays the accuracy of TimesFM-3 relative to the
best classical method in each cell on a logarithmic scale, which shows the pattern across
processes and lengths more directly than the table."""),
    (r"""\begin{figure}[t!]
\centering
\includegraphics[width=\textwidth]{../figures/fig2_mase_ratio.pdf}""",
     r"""\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig2_mase_ratio.pdf}"""),

    # ---- overall accuracy
    (r"""\subsection{The headline is a split decision, not a rout}""",
     r"""\subsection{Overall accuracy and pairwise comparisons}
\label{sec:overall}"""),
    (r"""Those ``versus best classical'' $p$-values should be read as descriptive rather than as valid
tests, and we flag this rather than let the reader assume otherwise.""",
     r"""These ``versus best classical'' $p$-values are descriptive rather than valid tests."""),
    (r"""That is the cautious reading. The more useful reading emerges from the 180 pairwise
comparisons, of which 132 are significant, 113 favouring TimesFM-3 and 19 the classical
method. Broken down by opponent, the pattern is stark:""",
     r"""The 180 pairwise comparisons with a fixed opponent are more informative. Of these, 132 are
significant, 113 favouring TimesFM-3 and 19 the classical method; \tableref{tab:opponents} gives
the breakdown by opponent."""),
    (r"""\begin{table}[t!]
\centering
\caption{Significant pairwise comparisons at $h = 1,\dots,12$, Benjamini--Hochberg corrected
within each opponent family. TimesFM-3 dominates every classical method except AutoARIMA,
against which it is close to even.}
\label{tab:opponents}""",
     r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Significant pairwise comparisons of TimesFM-3 with each classical method at
$h = 1,\dots,12$.}
\label{tab:opponents}"""),
    (r"""Combination        & 30 & 27 & 3 \\
\bottomrule
\end{tabular}
\end{table}""",
     r"""Combination        & 30 & 27 & 3 \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Paired Wilcoxon signed-rank tests in the 36 (process, length) cells,
Benjamini--Hochberg corrected within each opponent family.
\end{tablenotes}
\end{threeparttable}
\end{table}"""),
    (r"""\tableref{tab:opponents} carries the study's central message. \textbf{AutoARIMA is the only
classical method that holds its own}; against everything else---including the combination of
all three---TimesFM-3 wins the large majority of significant comparisons. A practitioner who
reliably selects AutoARIMA loses nothing by staying classical. A practitioner who does not, or
cannot, is materially better off with the foundation model.""",
     r"""\tableref{tab:opponents} shows that \textbf{AutoARIMA is the only classical method that performs
comparably with TimesFM-3}; against every other method, including the combination of all three,
TimesFM-3 wins the large majority of significant comparisons. A practitioner who reliably selects
AutoARIMA therefore loses little by remaining with a classical method, whereas one who cannot make
that selection is better served by the foundation model."""),

    # ---- effect sizes
    (r"""\subsection{Effect sizes, and a sensitivity check that matters}""",
     r"""\subsection{Effect sizes and sensitivity to the choice of test}
\label{sec:effects}"""),
    (r"""The evaluation protocol promised a Hodges--Lehmann estimate and a paired $t$-test alongside every
rank test, and both are reported here rather than left in the results files.""",
     r"""As specified in the protocol, each rank test is accompanied by a Hodges--Lehmann estimate and a
paired $t$-test."""),
    (r"""Against AutoARIMA the typical difference is about one hundredth of
a MASE unit---detectable in places, but not a difference a forecaster would notice.""",
     r"""Against AutoARIMA the typical difference is about one hundredth of
a MASE unit, statistically detectable in some cells but of little practical consequence."""),
    (r"""The 17 disagreements are not noise and one pattern among them is
substantive:""",
     r"""The 17 disagreements include one systematic pattern:"""),
    (r"""The two tests are answering different questions.
The mean difference is large because a minority of series produce very large errors for seasonal
naive; the median difference is near zero because on most individual series the two methods are
close. On intermittent data, where the error distribution is heavily skewed, this gap is expected,
and it is a further reason---beyond the metric disagreement above---to treat the D8 result as
conditional rather than decisive.""",
     r"""The two tests answer different questions. The mean difference is large because a minority of
series produce very large errors for seasonal naive, whereas the median difference is near zero
because the two methods are close on most individual series; on 64.5--72.0\% of series, depending on
length, TimesFM-3 is marginally less accurate. Such a gap is expected when the error distribution
is heavily skewed, as it is on intermittent data, and it is a further reason, beyond the
disagreement between error measures reported in \sectionref{sec:regimes}, to treat the D8 result
as conditional rather than decisive."""),

    # ---- estimability
    (r"""\subsection{Specification is not estimability}""",
     r"""\subsection{Correct specification versus estimability}"""),
    (r"""\textbf{H1 is refuted in that form, and the reason is instructive.}""",
     r"""\textbf{H1 is refuted in that form.}"""),
    (r"""The seasonal cells make the point unmistakable.""",
     r"""The seasonal processes show the effect most clearly."""),
    (r"""The
correctly specified model lost to a one-line rule by a factor of nearly three.""",
     r"""The
correctly specified model therefore had a mean MASE 2.7 times that of the seasonal naive method."""),
    (r"""Where specification is right but estimation is starved, automatic
classical methods do not merely lose---they fail loudly, and TimesFM-3 degrades gracefully
instead.""",
     r"""Where the specification is correct but the data are insufficient for
estimation, the errors of automatic classical methods can become very large, whereas the accuracy
of TimesFM-3 deteriorates only gradually."""),
    (r"""We use the ratio to the cell's best method rather than the absolute worst MASE because the
absolute measure is uninformative here:""",
     r"""The ratio to the best method in the cell is used rather than the absolute worst MASE because the
absolute measure is uninformative here:"""),

    # ---- seasonal and intermittent regimes
    (r"""\subsection{Two decisive regimes, one of which depends on the metric}""",
     r"""\subsection{Seasonal and intermittent regimes}
\label{sec:regimes}"""),
    (r"""Away from the ties, two regimes separate at every length. One of them is not as clean as a
single metric makes it appear, and we report that rather than the favourable number alone.""",
     r"""Beyond the ties, two regimes produce consistent differences at every length; in one of them,
the direction of the difference depends on the error measure."""),
    (r"""\textbf{Strong seasonality with enough data to estimate it (D4): use AutoARIMA.}""",
     r"""\textbf{Strong seasonality with sufficient data (D4).}"""),
    (r"""The recommendation reverses at $n = 24$, and the reversal is instructive.""",
     r"""The recommendation reverses at $n = 24$."""),
    (r"""\textbf{Intermittent demand (D8): the metrics disagree, and the disagreement is the finding.}""",
     r"""\textbf{Intermittent demand (D8).}"""),
    (r"""This is not a contradiction in the data; it is a known property of intermittent series, and it
has a mechanism.""",
     r"""This disagreement is not a contradiction in the data but a known property of intermittent
series, with an identifiable mechanism."""),
    (r"""This is
exactly the trap \citet{kolassa2016count} documents for count-valued retail demand, and it means
no single number settles the intermittent case.""",
     r"""\citet{kolassa2016count}
documents the same phenomenon for count-valued retail demand, and it implies that no single error
measure settles the intermittent case."""),
    (r"""What can be said honestly is narrower than our pre-registered hypothesis H2 anticipated:""",
     r"""The supported conclusion is therefore narrower than pre-registered hypothesis H2 anticipated:"""),
    (r"""one that is quadratic favours the latter. We resisted the temptation to headline the
MASE result alone.""",
     r"""one that is quadratic favours the latter."""),

    # ---- Croston-family baselines
    (r"""\subsection{Adding the right tool for the job: Croston-family baselines}""",
     r"""\subsection{Croston-family baselines for intermittent demand}
\label{sec:croston}"""),
    (r"""We therefore added them and re-ran the comparison.""",
     r"""They were therefore added and the comparison was repeated."""),
    (r"""\tableref{tab:croston} gives
the result, and it does not soften the earlier finding---it sharpens it in both directions.""",
     r"""\tableref{tab:croston} gives
the result, which reinforces both directions of the earlier finding."""),
    (r"""So the objection that TimesFM-3 was merely beating the
wrong tools does not survive: it also beats the right ones, and by a wider margin than it beat
the general-purpose set.""",
     r"""The MASE advantage of TimesFM-3 therefore does
not depend on the absence of purpose-built methods: its reduction in mean MASE relative to the best
Croston-family method, 19.6--25.7\% across lengths, is similar to its reduction relative to the
best general-purpose method, 21.7--26.5\%."""),
    (r"""On RMSSE the reversal not only persists but becomes cleaner.""",
     r"""On RMSSE the reversal persists."""),
    (r"""This is the
sharpest available confirmation of the mechanism proposed above.""",
     r"""This result
supports the mechanism proposed in \sectionref{sec:regimes}."""),
    (r"""The practical conclusion is correspondingly conditional, and it is now supported by the correct
baselines rather than asserted against inappropriate ones.""",
     r"""The practical conclusion is correspondingly conditional."""),
    (r"""If that cost is closer to quadratic, a Croston-family method is,
and TimesFM-3 should not be used.""",
     r"""If that cost is closer to quadratic, a Croston-family method is
preferable."""),

    # ---- horizons
    (r"""\subsection{Behaviour across the forecast horizon}""",
     r"""\subsection{Accuracy across forecast horizons}
\label{sec:horizon}"""),
    (r"""The figure needs one caution, because read carelessly it appears to contradict
\tableref{tab:mase}.""",
     r"""\figureref{fig:horizon} should be read together with \tableref{tab:mase}."""),
    (r"""yet the cell-by-cell count in
\sectionref{sec:results} gives the classical methods more wins.""",
     r"""yet the cell-by-cell count in
\sectionref{sec:overall} gives the classical methods more wins."""),
    (r"""That gap between the two is the robustness result of
\tableref{tab:robust} seen from another angle, not a separate finding.""",
     r"""The difference between the two summaries is the robustness
result of \tableref{tab:robust} viewed from another angle rather than a separate finding."""),
    (r"""\begin{figure}[t!]
\centering
\includegraphics[width=\textwidth]{../figures/fig4_horizon.pdf}""",
     r"""\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig4_horizon.pdf}"""),

    # ---- interval coverage
    (r"""\subsection{Interval reliability}""",
     r"""\subsection{Coverage of prediction intervals}
\label{sec:coverage}"""),
    (r"""\begin{figure}[t!]
\centering
\includegraphics[width=\textwidth]{../figures/fig3_coverage.pdf}""",
     r"""\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig3_coverage.pdf}"""),
    (r"""That averaged view is, however, flattering to every method, and we state the honest figure
alongside it.""",
     r"""The averaged view nevertheless understates the typical deviation from nominal coverage for
every method."""),
    (r"""No method in this study delivers reliable 80\% intervals
across all nine processes, and it would be wrong to read \figureref{fig:coverage} as saying
otherwise.""",
     r"""No method in this study delivers reliable 80\% intervals
across all nine processes."""),
    (r"""That is not reliability; it is a symptom.""",
     r"""This over-coverage is a symptom of misspecification rather than evidence of reliability."""),

    # ---- combination rule
    (r"""\subsection{Robustness: was the combination a straw man?}""",
     r"""\subsection{Robustness to the combination rule}
\label{sec:combination}"""),
    (r"""We therefore
repeated the comparison against a \emph{median} combination of the same three methods.""",
     r"""The comparison
was therefore repeated against a \emph{median} combination of the same three methods."""),
    (r"""and TimesFM-3 still wins 25 of 29
significant comparisons.""",
     r"""and TimesFM-3 still wins 25 of 29
significant comparisons. The median rule gains robustness at the cost of the averaging that
motivates combination: with three members, the median is the middle of the three forecasts at
each time point, so it forgoes the cancellation of errors from which the mean combination
benefits, and the mean combination is more accurate than the average of its members in all 36
cells."""),

    # ---- MAPE
    (r"""\subsection{What MAPE would have told you}""",
     r"""\subsection{Undefined values of MAPE}
\label{sec:mape}"""),
    (r"""This is the concrete form of a long-standing warning
\citep{hyndman2006mase, kolassa2016count},""",
     r"""This illustrates a well-known limitation of the measure
\citep{hyndman2006mase, kolassa2016count},"""),
]


def main() -> None:
    s = TEX.read_text(encoding="utf-8")
    if "\\label{sec:overall}" in s:
        print("part C already applied")
        return
    for old, new in REPLACEMENTS:
        s = swap(s, old, new)
    TEX.write_text(s, encoding="utf-8")
    print(f"part C applied: {len(REPLACEMENTS)} results-section edits")


if __name__ == "__main__":
    main()
