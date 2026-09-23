"""Length pass, part 6: condensed M4 and operational sections. The rolling-origin table and the
timing table become text (every number kept); the official-test and truncation tables stay."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Application to M4 monthly data}
\label{sec:realdata}

Whether TimesFM-3 has seen the M4 data cannot be settled, but the documented corpus makes it less likely
than for many public benchmarks: its real-world part is the GIFT-Eval pre-training collection (without the
datasets overlapping fev-bench), Wikipedia page views and Google Trends \citep{timesfm3card}, and that
collection is built to exclude the GIFT-Eval test datasets, of which M4 Monthly is one
\citep{aksu2024gifteval, giftevalpretrain}. Because the corpus cannot be inspected, the real-data tier is
secondary evidence. This section reports a rolling-origin evaluation (\sectionref{sec:m4results}), the
official M4 test period (\sectionref{sec:m4official}) and an experiment with truncated histories
(\sectionref{sec:truncation}).

\subsection{Rolling-origin evaluation}
\label{sec:m4results}

A seeded sample of 1\,000 series is drawn from the 32\,581 M4 Monthly series long enough for the design.
Their training periods have a median of 281 observations (interquartile range 198 to 306), against 202 (82
to 306) for all 48\,000 series, so the sample over-represents the long end of the population. Each series is
evaluated at up to three origins 12 months apart with M4's horizon $h = 18$ (2\,932 windows; the shortest
series cannot support a third origin), and methods are compared by paired Wilcoxon tests across series,
the independent units. TimesFM-3 (mean MASE 0.914) significantly outperforms seasonal naive (1.280; better
on 80.1\% of series), Theta (0.970; 56.8\%) and AutoETS (0.951; 54.1\%), and is indistinguishable from
AutoARIMA (0.923; 52.6\%, adjusted $p = 0.27$) and the combination (0.907; 48.5\%, adjusted $p = 0.27$).

This ties TimesFM-3 with AutoARIMA on long, mostly seasonal series, rather than showing the 21\% to 24\%
AutoARIMA advantage found on the simulated D4. The simulated seasonal process is a single, sharply seasonal
model, whereas real series mix trend, seasonality and irregular components in proportions the simulation
does not reproduce (\sectionref{sec:representativeness}); an advantage from contamination cannot be excluded
either. The probabilistic results also diverge: TimesFM-3's 80\% intervals cover 0.765 against 0.801 for the
combination, yet its pinball loss is the lowest of the six methods (0.363, against 0.365 and 0.374 for
AutoARIMA). Its distribution is slightly better overall while its 80\% interval is too narrow, the fragility
of foundation-model calibration reported by \citet{adler2026calibrated}.

\subsection{The official M4 test period}
\label{sec:m4official}

Rolling origins cut from the training data cannot be placed against published M4 results, so the same
series were also forecast for the official 18-month test period from their full histories and scored as in
M4, with the overall weighted average (OWA) of sMAPE and MASE relative to the official Naive2 forecasts
\citep{makridakis2020m4}, for all twelve methods of \sectionref{sec:benchmarks}.

\input{tab_m4official}

Theta and the Comb benchmark improve on Naive2 by 7\% to 9\% in OWA (\tableref{tab:m4official}), in line
with the competition. TimesFM-3 has an OWA of 0.862 (0.857 with its evaluator settings), TimesFM-2.5 0.864,
the two combinations 0.867 and 0.868, and AutoARIMA 0.891. A Friedman test on per-series ranks rejects the
equality of the thirteen methods, but the two combinations, TimesFM-3 in both configurations, TimesFM-2.5
and AutoARIMA lie within the Nemenyi critical difference of the best mean rank \citep{koning2005m3tests}.
On real monthly series with long histories, TimesFM-3 is one of a group of statistically indistinguishable
leading methods, not a clear winner.

\subsection{Truncated histories}
\label{sec:truncation}

The official test period was also forecast from only the last 24, 48 or 96 observations of each training
series, with the full-history MASE denominator so that only the information available to the methods
changes (\tableref{tab:truncation}). The simulation's estimability result reappears: with 24 observations
TimesFM-3 has a mean MASE of 1.046, against 1.175 for AutoARIMA, 1.129 for AutoETS and 1.096 for the best
classical method, the combination; with 48 the combination is level with it (0.955 against 0.961), and with
the full history the leading methods are within 2\% of one another. Truncation also moves the information
set away from the full series a model could have been trained on, although it cannot rule out that the
series were seen.

\input{tab_truncation}

\section{Operational considerations}
\label{sec:operational}

Accuracy is not the only criterion. This section considers computational cost (\sectionref{sec:cost}) and
licensing, interpretability and the basis of prediction intervals (\sectionref{sec:licence}).

\subsection{Computational cost}
\label{sec:cost}

Timed separately on the same 200 seasonal series of length 96, seasonal naive took 3.1\,ms per series,
Theta 9.0\,ms, TimesFM-3 23.2\,ms (batched on an NVIDIA GTX 1660 Ti, excluding a one-off model load of
3.0\,s), AutoETS 102.0\,ms and AutoARIMA 2\,382.7\,ms, 103 times TimesFM-3: automatic ARIMA searches over
orders and fits each candidate by maximum likelihood, separately for every series, whereas TimesFM-3
amortises one forward pass over a batch. The classical methods parallelise trivially, however: in the main
run, all four classical methods over the 7\,200 series took 7.3 minutes on 22 cores, against 3.2 minutes for
TimesFM-3 on one consumer GPU, a ratio of $2.3\times$. CPU_TIMING_SENTENCE Memory cannot be compared
directly, because the profiler used sees neither the compiled kernels of the classical methods nor GPU
memory; structurally, the classical methods hold a handful of parameters per series, whereas TimesFM-3 keeps
its checkpoint of about 1.3\,GB resident, whatever the number of series.

\subsection{Licensing, interpretability and prediction intervals}
\label{sec:licence}

TimesFM-3's weights are released under the TimesFM Non-Commercial License v1.0, which grants use ``solely
for your Non-Commercial Purposes'' and requires a separate licence for any ``commercial or production
activity'' \citep{timesfm3repo, timesfm3card} (accessed 23 September 2026). The source code is Apache-2.0,
as were the weights of TimesFM-2.5 and Chronos-Bolt, but the version-3 weights are not: \textbf{for a
commercial application, TimesFM-3 is not licensed as released}, whatever its accuracy, and the alternatives
are TimesFM-2.5, separate terms or a classical method. Licensing is routinely omitted from model comparisons
although it decides which models an entire class of users may use.

An ARIMA or ETS fit reports its orders, coefficients, smoothing parameters and standard errors, which
support residual diagnostics, tests for remaining structure and an explanation of why a forecast turns
where it does. TimesFM-3 exposes none of this: when it forecasts poorly, there is nothing to inspect. Its
quantiles are learned outputs with no accompanying theory; they were well calibrated on average in the
simulation (\sectionref{sec:coverage}) but not on M4, and their behaviour on a process unlike anything in
the pre-training corpus is unknown. In regulated settings where a forecast must be justified, these
differences may outweigh the accuracy comparison.

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Application to M4 monthly data}")
    b = s.index("\\section{Discussion}")
    s = s[:a] + NEW.replace("CPU_TIMING_SENTENCE ", "") + s[b:]
    P.write_text(s, encoding="utf-8")
    print("M4 and operational sections condensed")


if __name__ == "__main__":
    main()
