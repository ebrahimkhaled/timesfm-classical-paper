"""Length pass, part 5: condensed robustness section. The parameter-range table (Table S9) and the
parameter-response figure (Figure S2) move to the Supporting Information; all numbers are kept."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Representativeness and robustness of the design}
\label{sec:robustness}

Simulation conclusions are conditional on the processes and parameters used. This section asks how
closely the simulated series resemble real ones (\sectionref{sec:representativeness}) and whether the
conclusions survive random parameters and departures from the assumptions (\sectionref{sec:departures}).
Both analyses are post hoc.

\subsection{Representativeness of the simulated series}
\label{sec:representativeness}

Following \citet{kang2017instance}, each series is summarised by four features: normalised spectral
entropy (forecastability), STL trend strength, STL seasonal strength (period 12) and the first
autocorrelation of the first differences. The simulated series at $n = 96$ and the 1\,000 M4 Monthly
series of \sectionref{sec:realdata}, each cut to the last 96 observations of its training period, are
placed in this space with the features standardised on the M4 series. An M4 series is \emph{covered} when
some simulated series lies at least as close to it as the 95th percentile of the distance from an M4
series to its nearest other M4 series.

\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig11_instance_space.pdf}
\caption{Simulated and M4 Monthly series in a four-feature instance space (spectral entropy,
trend strength, seasonal strength and first-order autocorrelation of the differences), first two
principal components. Grey points are M4 series; coloured points are simulated series at
$n = 96$. (a) The fixed-parameter design covers 48.5\% of the M4 series; (b) the randomised-parameter
design covers 75.8\%, with coverage defined in \sectionref{sec:representativeness}.}
\label{fig:instance}
\end{figure}

The fixed design covers 48.5\% of the M4 series (bootstrap interval 45.2\% to 51.4\%;
\figureref{fig:instance}): each process forms a compact cluster and the regions between them, which hold
many real series, are empty. The randomised design of \sectionref{sec:departures} covers 75.8\% (73.2\% to
78.4\%) with half as many series. Across thresholds from the 80th to the 99th percentile, lengths of 48,
96 and 200, and a six-feature space adding the first autocorrelation and lumpiness, the randomised design
covers 76\% to 89\% of M4 at the 95th percentile and always more than the fixed design, also when the latter
is subsampled to equal size; conversely, 60\% to 92\% of the randomised series lie within the same distance
of some M4 series, fewest at $n = 200$. The parameter ranges were set before this statistic was first
computed. M4 series are more strongly trending than the simulated ones (median trend strength 0.87 against
0.63), and only 1.5\% lie nearest to D8, because M4 has no intermittent series; the intermittent-demand
results rest on the simulation alone.

\subsection{Randomised parameters and departures from the assumptions}
\label{sec:departures}

Every series now draws its own parameters uniformly from wide ranges containing the fixed values of
\tableref{tab:dgps} (Supporting Information, Table~S9): autoregressive coefficients up to 0.95,
intermittency from lumpy ($p = 0.1$) to nearly continuous ($p = 0.6$), breaks of three to fifteen noise
standard deviations in either direction. Four versions use the same 7\,200 parameter draws (200 per process
and length): \emph{random parameters} with Gaussian innovations; \emph{heavy tails}, Student-$t_3$
innovations of the same variance built from the same normal draws (negative binomial sizes on D8);
\emph{outliers}, each context point shifted with probability 0.03 by four to six robust standard deviations
(a demand multiplied by five on D8), with the held-out values left clean; and \emph{estimated period}, in
which the classical methods receive the period chosen by the 90\% autocorrelation test of the M4
benchmarks \citep{makridakis2020m4}, applied when at least three cycles are observed. TimesFM-3 never
receives a period, so its forecasts are unchanged in the last version.

\input{tab_robust_design}

In the three versions with a known period the conclusions were consistent with the main design, within
Monte Carlo error and within the ranges examined (\tableref{tab:robust-design}). TimesFM-3 is the best
method in 14 to 16 cells and within 4\% of the best in the median cell; its worst ratio rises to 1.49 to
1.56 (bootstrap intervals up to about 1.75), always on the logistic process D7 at $n = 96$, while the
smallest classical worst ratio is 2.09 to 2.32. With the Benjamini--Hochberg family per opponent, as in the
main design, TimesFM-3 wins 93 to 101 of 180 comparisons and loses 27 to 29, AutoARIMA again being the
opponent it does not clearly beat (7--7, 6--7, 10--4 and 8--6 across the four versions). AutoARIMA's
advantage on D4 with at least four cycles persists (21\% to 26\%; 5\% at two of three lengths with
outliers), and the Croston family keeps the lower RMSSE on D8 in every version.

\textbf{When the classical methods must estimate the period, the gap closes}: their smallest worst ratio is
1.58 (1.48 to 1.67), level with TimesFM-3's 1.55 (1.41 to 1.71), because the largest classical failures come
from imposing a seasonal model on two cycles. Estimating the period does not rescue the two-cycle case,
however: at $n = 24$ the seasonality test cannot be applied, every series is treated as non-seasonal, and
non-seasonal AutoETS has a mean MASE of 2.55 on D5 and 4.25 on D4, against 1.13 and 1.09 for seasonal naive
with the true period and 1.11 and 1.45 for TimesFM-3. With two cycles, neither imposing nor dropping the
seasonality works for the automatic classical methods.

A response-surface regression of the per-series $\log_2$ ratio of TimesFM-3's MASE to AutoARIMA's on the
standardised parameters, $\log_2 n$ and the version (Supporting Information, Tables~S5 and~S6, and
Figure~S2) shows that the dependence on the settings is modest. The largest systematic effect is length:
each doubling of $n$ moves the ratio against TimesFM-3 by 20\% on D4 and 11\% on D5, and in its favour on D6
and D8. Outliers favour TimesFM-3 on the seasonal processes (14\% and 10\%); the other version effects are
at most 0.09 in absolute value. Among the parameters only the demand probability of D8 has a large effect;
the ratio is flat in the autoregressive coefficient of D1 and the GARCH persistence of D9, grows in favour of
TimesFM-3 with the size of the break in D6, and changes sign with the inflection point of D7. The
regressions explain little of the per-series variation ($R^2 \leq 0.26$).

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Representativeness and robustness of the design}")
    b = s.index("\\section{Application to M4 monthly data}")
    s = s[:a] + NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("robustness section condensed")


if __name__ == "__main__":
    main()
