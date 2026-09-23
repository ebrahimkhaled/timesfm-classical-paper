"""Length pass, part 3: condensed pre-registered results section.

Moved to the Supporting Information (numbers kept in the text): the D8 metrics table (Table S7), the
Croston-family table (Table S8) and the horizon figure (Figure S1). The MAPE subsection becomes one
sentence. Every result and number of the section is kept.
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Simulation results}
\label{sec:results}

This section reports the pre-registered comparison: overall accuracy and the pairwise tests
(\sectionref{sec:overall}), effect sizes (\sectionref{sec:effects}), the role of estimability
(\sectionref{sec:estimability}), the seasonal and intermittent regimes (\sectionref{sec:regimes}), and
interval coverage and the combination rule (\sectionref{sec:coverage}). Statements about TimesFM-3
describe the behaviour of its forecasts; where an explanation is offered, it is an interpretation.
\tableref{tab:mase} reports mean MASE over $h = 1, \dots, 12$ for the 7\,200 series, and
\figureref{fig:ratio} shows TimesFM-3 relative to the best classical method in each cell.

\input{tab_mase}

\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig2_mase_ratio.pdf}
\caption{Accuracy of TimesFM-3 relative to the best classical method in each cell, on a
$\log_2$ scale. Bars below zero mark cells where TimesFM-3 is more accurate. The label under
each process names the family correctly specified for it by construction.}
\label{fig:ratio}
\end{figure}

\subsection{Overall accuracy and pairwise comparisons}
\label{sec:overall}

TimesFM-3 has the lowest mean MASE in 16 of the 36 (DGP, length) cells and the classical methods in 20:
AutoARIMA 10, seasonal naive 4, and two each for Theta, AutoETS and the combination. Against the best
classical method of each cell, 18 differences survive Benjamini--Hochberg correction, 7 favouring
TimesFM-3 and 11 the classical method; because that comparator is selected on the same replications,
these $p$-values are descriptive only. The inferential claims rest on the 180 comparisons with a fixed
opponent (\tableref{tab:opponents}): 132 are significant, 113 favouring TimesFM-3. \textbf{AutoARIMA is
the only classical method that performs comparably with TimesFM-3}; against every other method, the
combination included, TimesFM-3 wins the large majority of significant comparisons.

\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Significant pairwise comparisons of TimesFM-3 with each classical method at
$h = 1,\dots,12$.}
\label{tab:opponents}
\small
\begin{tabular}{lccc}
\toprule
Opponent & Significant comparisons & TimesFM-3 wins & Opponent wins \\
\midrule
AutoARIMA          & 20 & 11 & 9 \\
Seasonal naive     & 26 & 22 & 4 \\
AutoETS            & 27 & 25 & 2 \\
Theta              & 29 & 28 & 1 \\
Combination        & 30 & 27 & 3 \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Paired Wilcoxon signed-rank tests in the 36 (process, length) cells,
Benjamini--Hochberg corrected within each opponent family.
\end{tablenotes}
\end{threeparttable}
\end{table}

\subsection{Effect sizes and sensitivity to the choice of test}
\label{sec:effects}

The Hodges--Lehmann shifts in MASE across the 36 cells are $-0.010$ against AutoARIMA, $-0.091$ against
the combination, $-0.133$ against seasonal naive, $-0.183$ against AutoETS and $-0.227$ against Theta
(negative favours TimesFM-3), so against AutoARIMA the typical difference is about one hundredth of a
MASE unit. A paired $t$-test agrees with the Wilcoxon test in 163 of 180 comparisons (90.6\%). The one
systematic disagreement is on the intermittent process D8 against seasonal naive: the $t$-test finds
TimesFM-3 better at every length ($p < 0.0001$), the signed-rank test finds no difference ($p = 0.11$ to
$0.92$). The mean difference is driven by a minority of series on which seasonal naive fails badly,
whereas on 64.5--72.0\% of series TimesFM-3 is marginally less accurate---the two tests estimate
different quantities of a heavily skewed error distribution (\tableref{tab:ademp}).

\subsection{Correct specification versus estimability}
\label{sec:estimability}

Pre-registered hypothesis H1 held that correctly specified classical models would win on their home
ground, most clearly at short lengths; \textbf{it is refuted in that form}. On D1 and D2 TimesFM-3 is at
least as accurate as the correctly specified AutoARIMA at every length except D2 at $n = 200$, the only
significant difference. Correct specification bought AutoARIMA nothing detectable on short and moderate
series. A post-hoc \emph{Oracle ARIMA}, which knows the true orders and estimates only the parameters by
Gaussian maximum likelihood, shows why: on D1--D3 at $n = 24$ AutoARIMA pays a 9.9\% to 13.9\% penalty
for order selection, and on D4 at $n = 24$ about 81\% (indicative only, since 156 of the 200 oracle fits
fail to converge there), while the oracle beats TimesFM-3 in 15 of the 16 ARIMA cells (for example 1.351
against 1.417 on D1 at $n = 24$). The short-sample deficit of the automatic methods is thus largely one
of model selection, not of the model structure.

The seasonal processes show the effect most clearly. With two complete cycles ($n = 24$), AutoETS scores
a mean MASE of \textbf{3.03 on D5, data an ETS process generated}, against 1.14 for seasonal naive and 1.15
for TimesFM-3: the correctly specified model has 2.7 times the error of the naive rule. The operative
distinction is therefore whether a model is \emph{estimable} from the series at hand, not whether it is
correctly specified. \tableref{tab:robust} quantifies the resulting asymmetry with each method's mean MASE
as a multiple of the best in the same cell---a relative measure, because D3 is hard for every method and
would dominate absolute worst cases. \textbf{TimesFM-3 is never worse than $1.31\times$ the best method of
a cell}, and within 0.8\% of it in the median cell, whereas every classical method is at least $2.2\times$
worse somewhere: AutoARIMA $2.22\times$ and AutoETS $3.50\times$ (both on D4 at $n = 24$), Theta
$4.69\times$, seasonal naive $5.65\times$.

\input{tab_robust}

\subsection{Seasonal and intermittent regimes}
\label{sec:regimes}

\textbf{Strong seasonality with sufficient data (D4).} At $n = 48$, 96 and 200 AutoARIMA is better than
TimesFM-3 by 21.8\%, 21.1\% and 23.7\% (adjusted $p < 0.0001$), and D5 shows the same more mildly. Once at
least four cycles are observed, AutoARIMA recovers the seasonal structure and TimesFM-3 does not match
it. With two cycles the ranking reverses: the best classical method is seasonal naive (1.029), and
TimesFM-3 beats AutoARIMA by 42\% (1.321 against 2.284).

\textbf{Intermittent demand (D8).} On MASE TimesFM-3 reduces error against the best general-purpose
method by 21.7\% to 26.5\% at the four lengths (adjusted $p < 0.0001$) and is best on the pinball loss,
but it \emph{loses} on RMSSE at every length (Supporting Information, Table~S7); sMAPE, which scores a zero
forecast of a zero outcome as perfect, is not informative here. About 70\% of D8's observations are zero:
MASE is minimised by the conditional median, which is zero or near it, RMSSE by the conditional mean,
which is positive, so a median-like forecast wins MASE and loses RMSSE \citep{kolassa2016count}. The same
holds against six purpose-built intermittent-demand methods, added post hoc: Croston's classic and
optimised variants, the Syntetos--Boylan approximation, ADIDA, IMAPA and TSB (with StatsForecast's fixed
TSB constants $\alpha_d = \alpha_p = 0.2$; Table~S8). TimesFM-3 beats all six on MASE at every length
(24/24 significant; median ratios 0.70 to 0.82), while ADIDA and Croston-SBA have the lowest RMSSE
(0.694--0.769, against 0.774--0.806 for TimesFM-3). \sectionref{sec:d8-extended} shows that the MASE
advantage is matched by the all-zero forecast and should not be read as useful accuracy.

Across horizons ($h = 1$, $1$--$6$ and $1$--$12$) every method degrades and no ranking reverses
(Supporting Information, Figure~S1). Averaged within regimes, TimesFM-3 has the lowest mean MASE even among
the correctly specified processes, because a few catastrophic classical cells (Theta at 4.16 on D4 at
$n = 200$, AutoETS at 3.03 on D5 at $n = 24$) move a mean far more than several narrow classical wins.

\subsection{Coverage of intervals and the combination rule}
\label{sec:coverage}

\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig3_coverage.pdf}
\caption{Empirical coverage of the nominal 60\% and 80\% intervals, averaged over all nine
processes, against series length. The nominal level is dashed. TimesFM-3's 80\% coverage stays
within 0.802--0.834 across every length; the classical methods under-cover at $n = 24$ and
over-cover from $n = 96$.}
\label{fig:coverage}
\end{figure}

Averaged over the processes (\figureref{fig:coverage}), TimesFM-3's 80\% coverage stays between 0.802 and
0.834 at every length, closer to nominal than any other method. Averaging lets over- and under-coverage
cancel, however; the mean per-cell absolute deviation from nominal is 0.047 for TimesFM-3, 0.066 for
AutoARIMA, 0.089 for the combination, 0.101 for AutoETS, 0.127 for Theta and 0.144 for seasonal naive, and
TimesFM-3's per-cell 80\% coverage ranges from 0.583 to 0.921. No method delivers reliable 80\% intervals on
all nine processes. The classical intervals rest on Gaussian innovations, violated by construction on D8
(Bernoulli occurrence with Poisson sizes) and D9 (conditionally Gaussian but unconditionally heavy-tailed
errors). On the structural break D6 every classical method covers 0.966 to 0.999, because the break
inflates the estimated variance and the intervals become very wide (scaled widths 4.8 to 10.4); TimesFM-3
covers 0.828 to 0.889 with intervals about half as wide (3.0 to 5.1).

TimesFM-3 beats the pre-registered mean combination in 27 of 30 significant comparisons. Because the mean
is not robust to a failing member such as Theta, a \emph{median} combination of the same three methods was
also tried (post hoc); it is slightly worse (mean MASE 1.712 against 1.656, TimesFM-3 1.439), and TimesFM-3
still wins 25 of 29 significant comparisons. With three members the median forgoes the cancellation of
errors that makes the mean combination better than the average of its members in all 36 cells.

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Simulation results}")
    b = s.index("\\section{Extended evaluation}")
    s = s[:a] + NEW + s[b:]
    s = s.replace(r"""MAPE, undefined at zero and unusable on D8
\citep{hyndman2006mase, kolassa2016count}, is reported only in the Supporting Information (Section~S1).""",
                  r"""MAPE, undefined at zero---for 9.96\% of all evaluations, every one on D8
\citep{hyndman2006mase, kolassa2016count}---is reported only in the Supporting Information (Section~S1).""")
    P.write_text(s, encoding="utf-8")
    print("results section condensed")


if __name__ == "__main__":
    main()
