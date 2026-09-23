"""JoF revision: rewrite the representativeness-and-robustness section with the revised results.

Sources: results/robust/instance_coverage.csv, instance_sensitivity.csv (R3, R6);
robust_claims.csv, robust_boot.csv, robust_tests.csv, robust_response.csv, robust_estperiod.csv,
robust_excluded.csv (R2 at 200 replications, R4, R5).
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Representativeness and robustness of the design}
\label{sec:robustness}

The conclusions of any simulation study are conditional on the processes and parameter values it
uses. This section asks two questions of the design in \sectionref{sec:design}: how closely the
simulated series resemble real series (\sectionref{sec:representativeness}), and whether the
headline conclusions survive when the parameters are drawn at random and the assumptions of
Gaussian, outlier-free data with a known seasonal period are relaxed
(\sectionref{sec:departures}). Both analyses are post hoc.

\subsection{Representativeness of the simulated series}
\label{sec:representativeness}

Following \citet{kang2017instance}, every series is summarised by four features: the normalised
spectral entropy, a measure of forecastability equal to one for white noise; the strength of
trend and the strength of seasonality from an STL decomposition with period 12; and the
first-order autocorrelation of the first differences. The simulated series at $n = 96$ are placed
in this feature space together with the 1\,000 M4 Monthly series of \sectionref{sec:realdata},
each cut to the last 96 observations of its training period, and the features are standardised
with the mean and standard deviation of the M4 series. An M4 series is counted as \emph{covered}
when some simulated series lies at least as close to it as the 95th percentile of the distance
from an M4 series to its nearest other M4 series.

\figureref{fig:instance} shows the first two principal components. The fixed-parameter design of
\tableref{tab:dgps} covers 48.5\% of the M4 series (bootstrap 95\% interval 45.2\% to 51.4\%). Its
processes form compact clusters, because each uses a single parameter vector, and the regions
between them, which contain many real series, are empty. The randomised-parameter design of
\sectionref{sec:departures} covers 75.8\% (73.2\% to 78.4\%), although it contains half as many
series. The M4 series are more strongly trending than the simulated ones (median trend strength
0.87 against 0.63), and almost none of them (1.5\%) lies nearest to the intermittent process D8,
because M4 contains no intermittent series; the intermittent-demand results therefore rest on the
simulation alone and on the literature for that regime \citep{syntetos2005categorization}.

The comparison is not an artefact of the choices behind the statistic. Across thresholds from the
80th to the 99th percentile, series lengths of 48, 96 and 200, and a six-feature space that adds the
first autocorrelation of the series and its lumpiness, the randomised design covers 76\% to 89\% of
M4 at the 95th percentile, and it covers more than the fixed design in every configuration, also
when the fixed design is subsampled to the same number of series. In the reverse direction, 60\% to
92\% of the randomised series lie within the same distance of some M4 series; the share is lowest
at $n = 200$, where the simulated series are less trending than long real series. The parameter
ranges were set before the coverage statistic was first computed.

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

\subsection{Randomised parameters and departures from the assumptions}
\label{sec:departures}

In the second analysis every series draws its own parameter vector uniformly from the ranges in
\tableref{tab:ranges}, each of which contains the fixed value of \tableref{tab:dgps}. The ranges
extend the linear processes towards the stationarity boundary ($\phi$ up to 0.95), cover
intermittency from lumpy ($p = 0.1$) to nearly continuous ($p = 0.6$) demand, and include breaks
from three to fifteen noise standard deviations in either direction. Four versions of the design
are run on the same 7\,200 parameter draws (200 per process and length):

\begin{itemize}
\item \emph{random parameters}: Gaussian innovations, as in the main design;
\item \emph{heavy tails}: Student-$t$ innovations with three degrees of freedom, rescaled to the
      same variance and built from the same normal draws as the first version (common random
      numbers); for D8, negative binomial demand sizes with the same mean and three times the
      Poisson variance;
\item \emph{outliers}: each observation of the context is shifted, with probability 0.03, by four
      to six robust standard deviations of the first differences in a random direction (for D8, a
      demand is multiplied by five), while the held-out values are left uncontaminated; the MASE
      scale is computed from the contaminated context, so MASE levels are comparable within this
      version but not across versions;
\item \emph{estimated period}: the series of the first version, but the classical methods receive
      the seasonal period selected by the 90\% autocorrelation test used for the M4 benchmarks
      \citep{makridakis2020m4}, applied when at least three cycles are observed, instead of the
      true one. TimesFM-3 never receives a period, so its forecasts are unchanged.
\end{itemize}

\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Parameter ranges of the randomised-parameter design.}
\label{tab:ranges}
\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{ll}
\toprule
ID & Parameters, each drawn uniformly on the stated interval \\
\midrule
D1 & $\phi \in [0.10, 0.95]$, $\sigma \in [1, 5]$ \\
D2 & $\phi \in [0.10, 0.90]$, $\theta \in [-0.6, 0.8]$, $\sigma \in [1, 5]$ \\
D3 & $\phi \in [-0.5, 0.8]$, $\theta \in [-0.5, 0.6]$, drift $\in [0, 0.6]$, $\sigma \in [1, 5]$ \\
D4 & $\phi \in [0.1, 0.8]$, $\Phi \in [0.1, 0.8]$, seasonal amplitude $\in [5, 20]$, $\sigma \in [1, 5]$ \\
D5 & $\alpha \in [0.05, 0.5]$, $\beta \in [0.001, 0.03]$, $\gamma \in [0.05, 0.3]$, initial trend $\in [0, 0.5]$, amplitude $\in [5, 20]$, $\sigma \in [1, 5]$ \\
D6 & jump $\in [3, 15]\,\sigma$ with random sign, break at $[0.50, 0.85]\,n$, level noise $\in [0.2, 1]$, $\sigma \in [1, 5]$ \\
D7 & $r \in [0.04, 0.15]$, inflection at $[0.4, 0.8](n + H)$, $K \in [100, 250]$, $\sigma \in [1, 6]$ \\
D8 & demand probability $p \in [0.1, 0.6]$, size $1 + \mathrm{Pois}(\lambda)$ with $\lambda \in [1, 8]$ \\
D9 & $\phi \in [0.1, 0.9]$, $a \in [0.05, 0.15]$, $b \in [0.75, 0.90]$; if $a + b \geq 0.98$, $b$ is set to $0.97 - a$ \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Parameters not listed are as in \tableref{tab:dgps}. The intervals contain the
fixed values of the main design. The rule for D9 keeps the conditional variance stationary and puts
a small point mass at $b = 0.97 - a$. Seeds are disjoint from those of the main design; the four
versions share the parameter draws and, except for the heavy-tailed D8 sizes, the underlying normal
draws.
\end{tablenotes}
\end{threeparttable}
\end{table}

\input{tab_robust_design}

\tableref{tab:robust-design} checks the headline conclusions of \sectionref{sec:results} in each
version; 95\% bootstrap intervals are given where they matter. In each of the three versions with a
known seasonal period, the findings were consistent with those of the main design, within Monte
Carlo error and within the parameter ranges examined.

\begin{itemize}
\item \emph{Robustness rather than peak accuracy.} TimesFM-3 is the best method in 14 to 16 of the
      36 cells and within 4\% of the cell-best method in the median cell. Its worst ratio to the
      cell-best rises from 1.31 in the fixed design to between 1.49 and 1.56 (bootstrap intervals
      from about 1.39 to 1.75), always on the logistic process D7 at $n = 96$, where the
      equal-weight combination is best. The smallest worst ratio among the classical methods is
      2.09 to 2.32 (intervals from 1.96 to 2.54), so the gap persists.
\item \emph{Estimated seasonal period.} When the classical methods must estimate the period, the
      gap closes: their smallest worst ratio falls to 1.58 (1.48 to 1.67), level with that of
      TimesFM-3, 1.55 (1.41 to 1.71). The large classical worst cases of the main design arise
      where a seasonal model is imposed on two cycles, and under the estimated-period procedure
      the worst cases of both families are of similar size.
\item \emph{Pairwise comparisons.} With the Benjamini--Hochberg family defined per opponent as in
      the main design, TimesFM-3 wins 93 to 101 of the 180 comparisons in each version and loses
      27 to 29. AutoARIMA remains the classical method it does not clearly beat (7--7, 6--7, 10--4
      and 8--6 in the four versions).
\item \emph{Seasonality with enough cycles.} AutoARIMA is more accurate than TimesFM-3 on D4 at
      every length from $n = 48$ in three versions, by a median of 21--26\%. With outliers it is
      better at two of three lengths and by only 5\%.
\item \emph{Intermittent demand.} The Croston family has the lower RMSSE at every length in all four
      versions. The MASE comparison is not informative on this process
      (\sectionref{sec:d8-extended}).
\end{itemize}

The estimability result of \sectionref{sec:estimability} is sharpened rather than removed. With
random parameters AutoETS, given the true period, has 1.91 to 2.05 times the mean MASE of seasonal
naive on D5 at $n = 24$. Estimating the period does not rescue it: at $n = 24$ the seasonality test
cannot be applied, every series is treated as non-seasonal, and non-seasonal AutoETS has a mean MASE
of 2.55 on D5 and 4.25 on D4, against 1.13 and 1.09 for seasonal naive with the true period and
1.11 and 1.45 for TimesFM-3. With two observed cycles, neither imposing a seasonal model nor
dropping the seasonality works for the automatic classical methods; the seasonal naive rule and
TimesFM-3 are the methods that remain accurate.

A response-surface regression makes the dependence on the settings explicit. For each process, the
per-series $\log_2$ ratio of the MASE of TimesFM-3 to that of AutoARIMA was regressed on the
standardised drawn parameters, $\log_2 n$ and the version, with heteroskedasticity-robust standard
errors (Supporting Information, Table~S5). The version effects are small except on the seasonal
processes, where outliers favour TimesFM-3 (coefficients $-0.22$ on D4 and $-0.15$ on D5, that is
14\% and 10\% lower relative MASE); the other version effects are at most 0.09 in absolute value. The length effect is the largest systematic one:
each doubling of $n$ moves the ratio against TimesFM-3 by 0.26 on D4 and 0.15 on D5 (20\% and 11\%)
and in its favour on D6 and D8. Among the parameters, only the demand probability of D8 has a large
effect (0.51 per standard deviation); the others move the ratio by at most 0.11. The
regressions explain little of the per-series variation ($R^2$ at most 0.26), so most of the
difference between the two methods on any one series is series-specific noise rather than a
function of the settings.

\figureref{fig:response} shows the same dependence graphically for five processes. It is flat in the
autoregressive coefficient of D1 and the GARCH persistence of D9. On D6 the advantage of TimesFM-3
grows with the size of the break, and on D7 the comparison changes sign with the position of the
inflection point. On D8 the ratio moves strongly with the demand probability, but the MASE ratio on
that process is not informative about useful accuracy (\sectionref{sec:d8-extended}).

\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig12_parameter_response.pdf}
\caption{Median $\log_2$ ratio of the MASE of TimesFM-3 to that of AutoARIMA, by quintile of the
drawn parameter, randomised-parameter design with Gaussian innovations. Values below zero favour
TimesFM-3. For D8 the ratio compares median-type forecasts and is shown for completeness only.}
\label{fig:response}
\end{figure}

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Representativeness and robustness of the design}")
    b = s.index("\\section{Application to M4 monthly data}")
    s = s[:a] + NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("robustness section rewritten")


if __name__ == "__main__":
    main()
