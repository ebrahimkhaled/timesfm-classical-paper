"""JoF revision: insert the post-hoc 'Extended evaluation' section and qualify the D8 claims.

Every number below comes from results/revision/*.csv, results/fm/*.csv and results/*oracle* as
produced by N1-N7; see submission/JoF_revision_tracker.md for the referee comment each part answers.
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

SECTION = r"""\section{Extended evaluation}
\label{sec:extended}

The pre-registered comparison of \sectionref{sec:results} leaves several questions open: how
precise its summaries are, whether stronger or more standard classical benchmarks change them,
whether they describe TimesFM-3 or foundation models more generally, how much they depend on the
configuration of TimesFM-3, and what the intermittent-demand result means once a trivial forecast
is included. This section answers them. Every analysis in it was designed after the main results
were known and is post hoc; the deviation log records each one.

\subsection{Monte Carlo uncertainty}
\label{sec:mcse}

The Monte Carlo standard error of a cell's mean MASE is between 1.5\% and 6.2\% of the mean
(median 3.2\%) for the six methods of the main design; all of them are reported in the Supporting
Information, Table~S2. The summaries that combine cells were bootstrapped by resampling the
replications within each cell (500 draws). The worst ratio of TimesFM-3 to the best method in a
cell is 1.31 (95\% interval 1.28 to 1.36), and the smallest worst ratio among the classical methods,
that of AutoARIMA, is 2.22 (2.05 to 2.38), so the gap between them is not a product of Monte Carlo
noise. The count of cells won is less stable: TimesFM-3's 16 wins have a bootstrap interval of 13
to 20, which is why the paper does not rest any conclusion on the count of 16 against 20.

\subsection{Stronger classical benchmarks and other foundation models}
\label{sec:benchmarks}

Six methods were added: three classical benchmarks, namely dynamic optimised Theta
\citep[DOTM;][]{fiorucci2016dotm}, the Comb benchmark of the M4 competition (the mean of simple,
Holt and damped exponential smoothing on seasonally adjusted data; \citealp{makridakis2020m4}) and
an equal-weight combination of AutoETS, AutoARIMA and DOTM; two further foundation models used
zero-shot, TimesFM-2.5 \citep{timesfm25card} and Chronos-Bolt \citep{ansari2024chronos,
chronosboltcard}, both released under the Apache-2.0 licence; and TimesFM-3 run with the settings
of its developers' own benchmark evaluator (\sectionref{sec:tfm-check}). \tableref{tab:extended}
summarises all twelve methods.

\input{tab_extended}

Three results stand out. First, the stronger classical benchmarks do not change the picture. DOTM
and the M4 Comb benchmark are no more robust than Theta, whose failures they share: on the seasonal
process D4 they rely on a classical seasonal decomposition with fixed seasonal indices, whereas the
seasonally integrated process has a seasonal pattern that evolves, so the fixed indices drift
further from the truth as the series grows. Replacing Theta by DOTM in the combination leaves its
worst ratio at 2.99. TimesFM-3 wins 28 of 29 significant comparisons against DOTM and all 29
against the M4 Comb benchmark, and AutoARIMA remains the only classical method level with it (11
wins to 9).

Second, \textbf{the robustness belongs to TimesFM-3, not to foundation models as a class}. TimesFM-2.5
has a worst ratio of 2.18, no better than AutoARIMA, and Chronos-Bolt one of 3.06. Both are
competitive in some regimes---TimesFM-2.5 wins 11 cells---but neither has the bounded worst case
that distinguishes TimesFM-3. The paper's conclusions about robustness therefore apply to the
model evaluated, as the exploratory framing of \sectionref{sec:intro} anticipated.

Third, Friedman tests with Nemenyi critical differences \citep{koning2005m3tests} on per-series
ranks within each regime give the same ordering as the pairwise tests. TimesFM-3 is tied for the
best mean rank on the linear processes (D1--D3, D9), together with TimesFM-2.5 and AutoARIMA, and
it is tied for the best on the break and saturation processes (D6, D7) with no classical method; AutoARIMA has the best mean rank on the seasonal processes (D4, D5), tied only with
TimesFM-3 under its evaluator settings.

\subsection{Configuration and output of TimesFM-3}
\label{sec:tfm-check}

The main study called the model with the package defaults, which differ from the settings of the
developers' benchmark evaluator in two respects: symmetric averaging of forecasts for the series
and its negation, and a positivity constraint for non-negative series. With the evaluator settings
the worst ratio falls from 1.31 to 1.27 and the mean ratio from 1.059 to 1.054
(\tableref{tab:extended}); no conclusion changes. The model's output was also audited. It returns
a $12 \times 9$ array of deciles with no separate mean column, its point forecast equals the median
decile exactly, and quantile crossing, which the main study removed by sorting, occurs in 32\% to
46\% of forecast steps on the intermittent process D8 and essentially never elsewhere.

Two further checks concern the information TimesFM-3 receives. Given the month of the year as a
pair of past-and-future covariates, $\sin(2\pi t/12)$ and $\cos(2\pi t/12)$, on the seasonal
processes---the information the classical methods receive through their seasonal period---its
mean MASE rises in seven of the eight cells (for example from 1.124 to 1.194 on D4 at $n = 96$), so
AutoARIMA's advantage on well-observed seasonal series is not explained by the period being
withheld from TimesFM-3. And using the mean of its nine deciles as the point forecast, instead of
the median, leaves every process unchanged within 0.01 except the structural break D6 (0.835 to
0.875) and the intermittent process D8, discussed next.

\subsection{Intermittent demand re-examined}
\label{sec:d8-extended}

MASE is minimised by the conditional median, and on D8 the conditional median is zero or close to
it (\sectionref{sec:regimes}). The trivial forecast that predicts zero demand in every period
therefore belongs in the comparison. \tableref{tab:d8ext} adds it, together with two measures from
the intermittent-demand literature: the scaled mean error, which measures bias, and periods in
stock \citep[PIS;][]{wallstrom2010pis}, which accumulates the forecast error over the horizon as a
stock position would.

\input{tab_d8ext}

\textbf{The all-zero forecast has the lowest MASE at every length} (0.668 to 0.718), below TimesFM-3's
median forecast (0.683 to 0.780). The MASE advantage of TimesFM-3 over the Croston family reported in
\sectionref{sec:regimes} and \sectionref{sec:croston} is therefore the advantage of a forecast that
is close to zero: its bias ($-0.58$ to $-0.67$ MASE units) and its periods in stock ($-74$ to $-81$)
are close to those of the all-zero forecast and imply persistent stock-outs. That MASE result is
not evidence of useful accuracy on this process, and the paper no longer presents it as such.

The same model gives a different answer when its point forecast is matched to the loss. With the
mean of its nine deciles as the point forecast, TimesFM-3 has an RMSSE of 0.694 to 0.760, level with
the best Croston-family method at each length, and a bias within 0.06 of zero. Its clearest
advantage lies in the predictive distribution itself: its scaled pinball loss, 0.288 to 0.325, is
about 15\% lower than that of the best classical method at each length (0.340 to 0.380). On intermittent demand, then, what TimesFM-3 offers is a better distribution from
which a point forecast suited to the decision can be taken---not a better default point forecast.

\subsection{Interval methods}
\label{sec:conformal}

The classical intervals of the main study are the models' analytic Gaussian intervals, so their
coverage reflects the Gaussian assumption as well as the model. Split-conformal intervals
\citep{vovk2005algorithmic}, computed by \pkg{StatsForecast} from two 12-step calibration windows
where the context allows it ($n \geq 96$), do not repair this at the series lengths studied here:
their 80\% intervals cover only 53\% to 66\% of outcomes across the processes, against 66\% to 98\%
for the Gaussian intervals (Supporting Information, Table~S4). Two calibration windows give too few
residuals per horizon step to estimate a quantile. The coverage of every method by process is in
Table~S3; averaged over the design, the 80\% intervals of TimesFM-3 cover 0.814 (Monte Carlo SE
0.003), those of TimesFM-2.5 0.812 and Chronos-Bolt 0.834, against 0.794 for AutoARIMA.

"""

D8_OLD = r"""26.2\% at the four lengths, with adjusted $p < 0.0001$ throughout; on the scaled pinball loss it
is likewise best at every length. But on RMSSE it \emph{loses} at every length, and on sMAPE it
is the worst method of the six by a wide margin (\tableref{tab:d8metrics})."""
D8_NEW = r"""26.2\% at the four lengths, with adjusted $p < 0.0001$ throughout; on the scaled pinball loss it
is likewise best at every length. But on RMSSE it \emph{loses} at every length
(\tableref{tab:d8metrics}); sMAPE, which scores a zero forecast of a zero outcome as perfect, is
not informative on this process. \sectionref{sec:d8-extended} shows that the MASE advantage is
matched by the trivial all-zero forecast and should not be read as useful accuracy."""


def main():
    s = P.read_text(encoding="utf-8")
    anchor = "\\section{Representativeness and robustness of the design}"
    if "\\section{Extended evaluation}" not in s:
        assert s.count(anchor) == 1
        s = s.replace(anchor, SECTION + anchor)
        print("section inserted")
    if D8_OLD in s:
        s = s.replace(D8_OLD, D8_NEW)
        print("D8 paragraph qualified")
    P.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    main()
