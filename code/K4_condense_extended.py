"""Length pass, part 4: condensed Extended evaluation section (all numbers kept)."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Extended evaluation}
\label{sec:extended}

This section asks how precise the summaries of \sectionref{sec:results} are (\sectionref{sec:mcse}),
whether stronger benchmarks and other foundation models change them (\sectionref{sec:benchmarks}), how
much they depend on the configuration of TimesFM-3 (\sectionref{sec:tfm-check}), what the
intermittent-demand result means once a trivial forecast is included (\sectionref{sec:d8-extended}),
and whether conformal intervals improve coverage (\sectionref{sec:conformal}). All of it is post hoc.

\subsection{Monte Carlo uncertainty}
\label{sec:mcse}

The Monte Carlo standard error of a cell's mean MASE is 1.5\% to 6.2\% of the mean (median 3.2\%;
Supporting Information, Table~S2). Bootstrapping the replications within each cell (500 draws), the worst
ratio of TimesFM-3 to the cell-best method is 1.31 (95\% interval 1.28 to 1.36) and the smallest worst
ratio among the classical methods, AutoARIMA's, is 2.22 (2.05 to 2.38), so that gap is not Monte Carlo
noise. The count of cells won is less stable---TimesFM-3's 16 has an interval of 13 to 20---and no
conclusion rests on it.

\subsection{Stronger classical benchmarks and other foundation models}
\label{sec:benchmarks}

Six methods were added (\tableref{tab:extended}): dynamic optimised Theta \citep[DOTM;][]{fiorucci2016dotm};
the Comb benchmark of M4, the mean of simple, Holt and damped exponential smoothing on seasonally adjusted
data \citep{makridakis2020m4}; a combination of AutoETS, AutoARIMA and DOTM; TimesFM-2.5 \citep{timesfm25card}
and Chronos-Bolt \citep{ansari2024chronos, chronosboltcard}, both zero-shot and Apache-2.0 licensed; and
TimesFM-3 with its developers' evaluator settings (\sectionref{sec:tfm-check}).

\input{tab_extended}

The stronger classical benchmarks do not change the picture. DOTM and the Comb benchmark share Theta's
failure on D4, where a classical decomposition with fixed seasonal indices meets a seasonal pattern that
evolves, and replacing Theta by DOTM leaves the combination's worst ratio at 2.99. TimesFM-3 wins 28 of 29
significant comparisons against DOTM and all 29 against the Comb benchmark; AutoARIMA remains the only
classical method level with it (11 wins to 9). \textbf{The robustness belongs to TimesFM-3, not to
foundation models as a class}: TimesFM-2.5 has a worst ratio of 2.18, no better than AutoARIMA, and
Chronos-Bolt 3.06, although TimesFM-2.5 wins 11 cells. Friedman tests with Nemenyi critical differences
\citep{koning2005m3tests} within each regime agree with the pairwise tests: TimesFM-3 is tied for the best
mean rank on the linear processes (with TimesFM-2.5 and AutoARIMA) and on the break and saturation
processes (with no classical method), and AutoARIMA has the best mean rank on the seasonal processes,
tied only with TimesFM-3 under its evaluator settings.

\subsection{Configuration and output of TimesFM-3}
\label{sec:tfm-check}

The developers' benchmark evaluator averages the forecasts of a series and its negation and constrains
non-negative series to non-negative forecasts, whereas the main study used the package defaults. With
the evaluator settings the worst ratio falls from 1.31 to 1.27 and the mean ratio from 1.059 to 1.054; no
conclusion changes. The output is a $12 \times 9$ array of deciles whose median equals the point forecast
exactly; quantile crossing, removed in the main study by sorting, occurs in 32\% to 46\% of steps on D8
and essentially never elsewhere. Given the month of the year as past-and-future covariates
($\sin 2\pi t/12$, $\cos 2\pi t/12$) on D4 and D5---the information the classical methods receive through
their period---TimesFM-3's mean MASE rises in seven of the eight cells (for example 1.124 to 1.194 on D4
at $n = 96$), so AutoARIMA's seasonal advantage is not explained by the period being withheld. Using the
mean of the deciles instead of the median as point forecast changes no process by more than 0.01 except
D6 (0.835 to 0.875) and D8.

\subsection{Intermittent demand re-examined}
\label{sec:d8-extended}

Because MASE rewards the conditional median, which on D8 is near zero, the trivial all-zero forecast
belongs in the comparison. \tableref{tab:d8ext} adds it, with the scaled mean error (bias) and periods in
stock \citep[PIS;][]{wallstrom2010pis}, which accumulates forecast errors as a stock position would.

\input{tab_d8ext}

\textbf{The all-zero forecast has the lowest MASE at every length} (0.668 to 0.718), below TimesFM-3's
median forecast (0.683 to 0.780). The MASE advantage of \sectionref{sec:regimes} is thus the advantage of
a forecast close to zero: its bias ($-0.58$ to $-0.67$ MASE units) and PIS ($-74$ to $-81$) are close to
those of the all-zero forecast and imply persistent stock-outs, so it is not evidence of useful accuracy.
With the mean of its deciles as point forecast, TimesFM-3 has an RMSSE of 0.694 to 0.760, level with the
best Croston-family method at each length, and a bias within 0.06 of zero. Its clearest advantage is the
predictive distribution: a scaled pinball loss of 0.288 to 0.325, about 15\% below the best classical
method at each length (0.340 to 0.380). On intermittent demand TimesFM-3 offers a better distribution from
which a point forecast suited to the decision can be taken, not a better default point forecast.

\subsection{Conformal intervals}
\label{sec:conformal}

The classical intervals are analytic Gaussian intervals, so their coverage reflects the Gaussian
assumption as well as the model. Split-conformal intervals \citep{vovk2005algorithmic}, computed by
\pkg{StatsForecast} from two 12-step calibration windows where the context allows ($n \geq 96$), cover only
53\% to 66\% of outcomes at nominal 80\%, against 66\% to 98\% for the Gaussian intervals (Table~S4): two
windows give too few residuals per horizon step. Averaged over the design, the 80\% intervals of TimesFM-3
cover 0.814 (Monte Carlo SE 0.003), TimesFM-2.5 0.812, Chronos-Bolt 0.834 and AutoARIMA 0.794 (Table~S3).

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Extended evaluation}")
    b = s.index("\\section{Representativeness and robustness of the design}")
    s = s[:a] + NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("extended section condensed")


if __name__ == "__main__":
    main()
