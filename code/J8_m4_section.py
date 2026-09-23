"""JoF revision: rewrite the M4 section (official test period, OWA, MCB, truncation, corpus note).

Sources: results/realdata_*.csv (rolling-origin tier, unchanged), results/m4_official/*.csv (N3).
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

HEAD_OLD_START = "\\section{Application to M4 monthly data}"
HEAD_OLD_END = "\\subsection{Sampling and evaluation design}"
HEAD_NEW = r"""\section{Application to M4 monthly data}
\label{sec:realdata}

The simulation tier secures freedom from contamination at the cost of realism. This section
complements it with real data. Whether TimesFM-3 has seen the M4 data cannot be settled, but the
documented corpus makes it less likely than for many public benchmarks: according to the model card,
the real-world part of the pre-training corpus is the GIFT-Eval pre-training collection (without the
datasets that overlap with fev-bench), Wikipedia page views and Google Trends \citep{timesfm3card},
and the GIFT-Eval pre-training collection is built to exclude the GIFT-Eval test datasets, of which
M4 Monthly is one \citep{aksu2024gifteval, giftevalpretrain}. The corpus itself, and its synthetic
and augmented part, cannot be inspected, so the real-data tier is reported as secondary evidence and
the simulation tier carries the primary claims. \sectionref{sec:m4design} describes the sampling and
the rolling-origin design, \sectionref{sec:m4results} its results, \sectionref{sec:m4official} the
official M4 test period and \sectionref{sec:truncation} an experiment with truncated histories.

"""

LEN_OLD = r"""68 windows are dropped rather than shortened. The sampled series are substantial: median
length 299 observations, upper quartile 324, maximum 1\,808."""
LEN_NEW = r"""68 windows are dropped rather than shortened. The sampled series are long: the training
periods have a median of 281 observations (interquartile range 198 to 306), against 202 (82 to 306)
for all 48\,000 M4 Monthly series, so the sample over-represents the long, estimable end of the
population."""

AGREE_OLD_START = r"""Two observations follow.

First, \textbf{the two tiers agree}."""
AGREE_OLD_END = r"""The fragility of foundation-model calibration reported by \citet{adler2026calibrated} is visible
in the coverage half of this result."""
AGREE_NEW = r"""Two observations follow.

First, the real-data result is \emph{consistent with} the simulation's estimable regime, with an
important difference. M4 Monthly series are long and mostly seasonal, and there TimesFM-3 ties with
AutoARIMA and the combination instead of losing to AutoARIMA by the 21\% to 24\% that the simulation
found on the seasonal process D4 with at least four cycles. The simulated seasonal process is a
single, sharply seasonal model; real monthly series mix trend, seasonality and irregular components
in proportions the simulation does not reproduce (\sectionref{sec:representativeness}), so the size
of a classical advantage found on one simulated process should not be expected to carry over to a
heterogeneous real collection. A possible advantage from contamination cannot be excluded either.

Second, the probabilistic results diverge. TimesFM-3's interval coverage does not carry over: on
simulated data it was among the best calibrated, whereas here it covers 0.765 against a nominal
0.80, while the combination achieves 0.801. On the scaled pinball loss over the nine deciles,
TimesFM-3 is the best of the six methods (0.363, against 0.365 for the combination and 0.374 for
AutoARIMA). The two measures answer different questions: coverage asks whether the truth falls
inside one interval, whereas the pinball loss scores the whole predictive distribution. Here
TimesFM-3's distribution is slightly better overall while its 80\% interval is too narrow, which is
the fragility of foundation-model calibration reported by \citet{adler2026calibrated}.

\subsection{The official M4 test period}
\label{sec:m4official}

The rolling origins above are cut from the M4 training data, so their accuracy cannot be placed
against published M4 results. The same 1\,000 series were therefore also forecast for the official
18-month test period from their full training histories and scored exactly as in M4, with the overall
weighted average (OWA) of sMAPE and MASE relative to the official Naive2 forecasts
\citep{makridakis2020m4}. All twelve methods of \sectionref{sec:benchmarks} were included.

\input{tab_m4official}

\tableref{tab:m4official} places the classical benchmarks where the M4 competition found them:
Theta and the Comb benchmark improve on Naive2 by 7\% to 9\% in OWA. TimesFM-3 has an OWA of 0.862
(0.857 with its evaluator settings), TimesFM-2.5 0.864, the two combinations 0.867 and 0.868, and
AutoARIMA 0.891. The multiple-comparison test confirms that these differences are small: a Friedman
test on the per-series ranks rejects equality of the thirteen methods, but the two combinations, TimesFM-3 in
both configurations, TimesFM-2.5 and AutoARIMA are all within the Nemenyi critical difference of the best
mean rank \citep{koning2005m3tests}, while AutoETS, Chronos-Bolt, DOTM, Theta, the Comb benchmark,
Naive2 and seasonal naive are behind it. On real monthly data with long histories, TimesFM-3 is
therefore one of a group of statistically indistinguishable leading methods, not a clear winner.

\subsection{Truncated histories}
\label{sec:truncation}

To connect the two tiers directly, the official test period was also forecast from only the last
24, 48 or 96 observations of each training series, keeping the full-history MASE denominator so
that only the information available to each method changes (\tableref{tab:truncation}). The
simulation's estimability result reappears on real data. With 24 observations, TimesFM-3 has a mean
MASE of 1.046, against 1.175 for AutoARIMA, 1.129 for AutoETS and 1.096 for the best classical
method, the combination; with 48 observations the combination is level with it (0.955 against
0.961), and with the full history the leading methods are within 2\% of one another. The foundation model's advantage is concentrated where the
classical methods have little data from which to estimate a model, as in the simulation. Truncation
also moves the information set away from the full training series on which a model could have been
trained, although it does not remove the possibility that the series were seen.

\input{tab_truncation}
"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index(HEAD_OLD_START)
    b = s.index(HEAD_OLD_END, a)
    s = s[:a] + HEAD_NEW + s[b:]
    assert s.count(LEN_OLD) == 1
    s = s.replace(LEN_OLD, LEN_NEW)
    a = s.index(AGREE_OLD_START)
    b = s.index(AGREE_OLD_END) + len(AGREE_OLD_END)
    s = s[:a] + AGREE_NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("M4 section rewritten")


if __name__ == "__main__":
    main()
