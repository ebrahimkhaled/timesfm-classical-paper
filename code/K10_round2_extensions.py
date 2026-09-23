"""Second referee round, part 2 (author: "do them all"): the remaining referee items.

  * two newer foundation models (Chronos-2, TiRex) and TimesFM-2.5 with flip/positivity off (N8, N4)
  * the published M4 submissions on the same 1,000 series (L3, N3)
  * a cross-check of AutoARIMA / AutoETS / Theta against R's forecast package (L2)
  * a forest plot of the per-cell pairwise effects (B9)
  * a longer horizon, H = 48 (N9, B10)

Evidence: results/revision/, results/m4_official/, results/round2/r_forecast_check_summary.csv,
results/round2/forest.csv, results/h48/. Blocks are replaced between fixed anchors.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "manuscript_jof" / "timesfm_jof.tex"


def block(s, start, end, new):
    a = s.index(start)
    b = s.index(end, a + len(start))
    return s[:a] + new + s[b:]


def rep(s, old, new):
    assert old in s, f"not found: {old[:70]!r}"
    return s.replace(old, new, 1)


ABSTRACT = r"""\abstract[Abstract]{Time-series foundation models such as Google's TimesFM-3 forecast series they were never
trained on. Whether they should replace classical methods such as ARIMA and exponential smoothing is
difficult to settle on public benchmarks, because few benchmark datasets are absent from every
model's pre-training corpus. This exploratory study describes, under controlled conditions, how
TimesFM-3 behaves relative to classical methods and in which regimes it may be preferred. The
evaluation data are generated from nine known processes, so the model cannot have seen the series.
Across 7\,200 series and a pre-registered protocol with a 12-step horizon, neither family dominates.
TimesFM-3 is never more than 1.31 times worse than the best method in a cell, whereas every classical
method is at least 2.2 times worse somewhere; the largest classical failures occur with only two seasonal
cycles, where the automatic methods fall back to non-seasonal models, and without those cells automatic
ARIMA's worst case is 1.62. With four or more cycles automatic ARIMA is 21--24\% more accurate than
TimesFM-3 on seasonal ARIMA data. Among five foundation models, this
robustness is specific to TimesFM-3, and it is specific to short horizons: at 48 steps, TimesFM-3 and the
other foundation models forecast a decline on a saturating process whose level stays flat, and automatic
ARIMA has the smaller worst case elsewhere. On intermittent demand TimesFM-3 shows no advantage over
simple benchmarks built from the history. In post-hoc checks, randomised parameters, heavy-tailed noise and
outliers leave these patterns qualitatively unchanged, and on the official test period of 1\,000 M4
monthly series TimesFM-3 is level with the fifth- to seventh-ranked M4 entries, behind the four best, and
among ten methods whose ranks cannot be separated. Because TimesFM-3 is a black box, the study characterises
its behaviour, not the reasons for it; the findings are conditional on the processes and horizons examined,
and the model's weights are licensed for non-commercial use only.}

"""

FOREST = r"""
\begin{figure}[!htbp]
\centering
\includegraphics[width=\textwidth]{../figures/fig5_forest.pdf}
\caption{Pairwise comparisons of TimesFM-3 with each classical method, cell by cell: median of the paired
per-series ratios of MASE over $h = 1, \dots, 12$, with 95\% bootstrap intervals, on a logarithmic scale.
Filled markers are significant after Benjamini--Hochberg correction; points left of 1 favour TimesFM-3.
Arrowheads mark medians beyond the plotted range.}
\label{fig:forest}
\end{figure}
"""

OVERALL_ADD = (r"""\figureref{fig:forest} shows the effect behind each count: against AutoARIMA most intervals straddle
1, and the cells where AutoARIMA is ahead are the seasonal processes from $n = 48$, whereas against the other
methods most intervals lie wholly on the side of TimesFM-3.

""")

ESTIM_OLD = (r"""worst ratio is unchanged and AutoARIMA's falls to 1.62 (on D7 at $n = 96$), AutoETS's to 2.72 and the
combination's to 2.08.""")
ESTIM_NEW = (r"""worst ratio is unchanged and AutoARIMA's falls to 1.62 (on D7 at $n = 96$), AutoETS's to 2.72 and the
combination's to 2.08; the last two come from AutoETS on D4 at $n = 96$, a cell in which StatsForecast's
estimation fails (\sectionref{sec:regimes}), and with the value of R's \pkg{forecast} package there AutoETS's
worst ratio would be 2.13, on D7 at $n = 48$.""")

REGIMES_OLD = r"""lengthens (Theta 1.94 at $n = 48$ and 4.16 at $n = 200$). D4 is seasonally integrated, so its seasonal
pattern drifts, whereas classical decomposition estimates one fixed pattern from the whole history; with
additive instead of multiplicative decomposition the failure is almost unchanged (in a check on 60
replications, Theta's mean MASE at $n = 200$ was 3.83 against 3.95), so it concerns the model form rather
than the adjustment."""
REGIMES_NEW = r"""lengthens (Theta 1.94 at $n = 48$ and 4.16 at $n = 200$). D4 is seasonally integrated, so its seasonal
pattern drifts, whereas classical decomposition estimates one fixed pattern from the whole history; with
additive instead of multiplicative decomposition the failure is almost unchanged (in a check on 60
replications, Theta's mean MASE at $n = 200$ was 3.83 against 3.95), so it concerns the model form rather
than the adjustment.

Because the classical results could depend on the implementation, the D4 and D5 cells were refitted with
\code{auto.arima}, \code{ets} and \code{thetaf} of the \proglang{R} package \pkg{forecast}
\citep{hyndman2008forecast}, the reference implementation of the Hyndman--Khandakar procedures (post hoc;
Supporting Information, Table~S13). R reproduces every failure discussed here---AutoARIMA 2.87 and AutoETS
3.95 on D4 at $n = 24$, AutoETS 3.30 on D5 at $n = 24$, Theta 4.09 on D4 at $n = 200$---and, like
StatsForecast, almost never fits a seasonal model with two cycles. Where both choose seasonal forms the two
implementations agree closely, with one exception: on D4 at $n = 96$ StatsForecast's AutoETS has a mean MASE
of 2.41 against 1.04 for R, because its optimiser settles on a near-zero seasonal smoothing parameter where R
finds a high one. That cell is an implementation failure rather than a property of the model."""

EXT_INTRO_OLD = r"""was run with its defaults.

"""
EXT_INTRO_NEW = r"""was run with its defaults. Three further configurations were added afterwards: Chronos-2
\citep{ansari2025chronos2} and TiRex \citep{auer2025tirex}, two newer zero-shot models with 120 and 35 million
parameters, both run with their package defaults, and TimesFM-2.5 with flip invariance and positivity
switched off, which matches the default settings of the main TimesFM-3 runs.

"""

BENCH = r"""The stronger classical benchmarks do not change the picture. DOTM and the Comb benchmark share Theta's
failure on D4, where a classical decomposition with fixed seasonal indices meets a seasonal pattern that
evolves, and replacing Theta by DOTM leaves the combination's worst ratio at 2.99. TimesFM-3 wins 28 of 29
significant comparisons against DOTM and all 29 against the Comb benchmark; AutoARIMA remains the only
classical method it does not clearly beat (11 wins to 9). \textbf{Among the five foundation models,
the robustness belongs to TimesFM-3 alone} (\tableref{tab:extended}): TimesFM-2.5 has a
worst ratio of 2.18 (on D7 at $n = 24$), and 2.26 with its settings switched off, so the difference is not one
of configuration; TiRex has 2.24, Chronos-2 2.75 (on D6 at $n = 24$) and Chronos-Bolt 3.06, against 2.22 for
AutoARIMA. In the median cell every foundation model but Chronos-Bolt is within 2\% to 4\% of the best, and TimesFM-2.5 is the best method in
7 cells, more than any model but AutoARIMA (8). Like TimesFM-3, the newer models do not clearly beat AutoARIMA
(Chronos-2 10--10, TiRex 9--12). Friedman tests with Nemenyi critical differences \citep{demsar2006statistical}
within each regime agree with the pairwise tests: TimesFM-3 is tied for the best mean rank on the linear
processes (with TimesFM-2.5, TiRex and AutoARIMA) and on the break and saturation processes (with no other
method), and AutoARIMA has the best mean rank on the seasonal processes, tied only with TimesFM-3 under its
evaluator settings. Averaged over the design, the 80\% intervals of TimesFM-3 cover 0.814 (Monte Carlo SE
0.003), TimesFM-2.5 0.812, Chronos-2 0.789, TiRex 0.842, Chronos-Bolt 0.834 and AutoARIMA 0.794 (Supporting Information, Table~S3, by process for the models of the
first comparison).

"""

D8_OLD = r"""intervals. The result concerns a process that is independent over time, the case most favourable to
history-based benchmarks."""
D8_NEW = r"""intervals. The other foundation models, Chronos-2 and TiRex included, behave the same way
(\tableref{tab:d8ext}). The result concerns a process that is independent over time, the case most favourable
to history-based benchmarks."""

HORIZON = r"""\subsection{A longer horizon}
\label{sec:horizon48}

Calibration of foundation models is reported to degrade with the horizon \citep{adler2026calibrated}, and the
main design stops at 12 steps. The nine processes were therefore regenerated with the same seeds for a
48-step horizon and forecast by the six pre-registered methods, TimesFM-2.5 and Chronos-2 (Supporting
Information, Section~S7 and Figure~S3). Because the inflection of D7 sits at $0.6(n + H)$, the longer horizon
moves it into the context for $n = 200$, so that the series has already flattened when the forecast starts.
Over the first 12 steps the picture of \sectionref{sec:results} is recovered: without D7, TimesFM-3's worst
ratio to the best method is 1.31 and AutoARIMA's 2.11. Further out it is not. Over steps 25 to 48,
\textbf{AutoARIMA has the smaller worst case} (1.41 against 1.80, D7 excluded), although TimesFM-3 remains
closer to the best method in the median cell (1.075 against 1.109). On D7 at $n = 200$ every foundation model
forecasts a decline while the process stays at its plateau near 200: TimesFM-3's mean forecast falls to 128
by step 48, TimesFM-2.5's to 98 and Chronos-2's to 146, and their mean MASE over the 48 steps is 8.37, 12.22
and 5.30, against 1.11 for seasonal naive and 2.51 for AutoARIMA. What in the models produces the decline
cannot be established here. The coverage of TimesFM-3's 80\% intervals falls from 0.788 over steps 1 to 12 to
0.760 over steps 25 to 48, and AutoARIMA's from 0.760 to 0.720, so both drift away from nominal, as
\citet{adler2026calibrated} report for foundation models. The robustness of \sectionref{sec:estimability} is
thus a property of short horizons.

"""

M4_OLD = r"""if, as its model card suggests, Chronos-Bolt shares that corpus, its M4 forecasts are in-domain rather than
zero-shot."""
M4_NEW = r"""if, as its model card suggests, Chronos-Bolt shares that corpus, its M4 forecasts are in-domain rather than
zero-shot. The corpora of Chronos-2 and TiRex were not checked for M4, and their M4 results are read in the
same way."""

M4OFF = r"""Rolling origins cut from the training data cannot be placed against published M4 results, so the same
series were also forecast for the official 18-month test period from their full histories and scored as in
M4, with the overall weighted average (OWA) of sMAPE and MASE relative to the official Naive2 forecasts
\citep{makridakis2020m4}. The comparison includes the methods of \sectionref{sec:benchmarks} and, post hoc,
the published point forecasts of the ten best M4 submissions, among them the winning hybrid of exponential
smoothing and a recurrent network \citep{smyl2020hybrid} and the feature-based combination FFORMA
\citep{monteromanso2020fforma}; scored on all 48\,000 monthly series, the downloaded files reproduce the
published M4 results.

\input{tab_m4official}

Theta and the Comb benchmark improve on Naive2 by 7\% to 9\% in OWA (\tableref{tab:m4official}), in line
with the competition. \textbf{Four M4 entries are ahead of every foundation model}: FFORMA (OWA 0.831),
Jaganathan and Prakash (0.841), Smyl's hybrid (0.848) and Pawlikowski et al.\ (0.849). TimesFM-3 (0.862;
0.857 with its evaluator settings) is level with the entries ranked fifth to seventh in M4 (0.858 to 0.864),
TiRex (0.855) and Chronos-2 (0.860) are close to it, and the classical combination (0.868) and AutoARIMA
(0.891) follow. On this sample the M4 entries' OWA differs from their published monthly values by up to
0.03, as much as the gaps between them. A Friedman test on per-series ranks, with one configuration per model
and without Naive2 \citep{benavoli2016should}, rejects the equality of the 22 methods, but ten lie within the
Nemenyi critical difference of the best mean rank \citep{demsar2006statistical}: five M4 entries, the
classical combination, TimesFM-3, Chronos-2 and TiRex. On real monthly series with long histories, zero-shot
TimesFM-3 matches good specialised methods of 2018 without per-series tuning, but not the best of them.

\subsection{Truncated histories}
\label{sec:truncation}

The official test period was also forecast from only the last 24, 48 or 96 observations of each training
series, with the full-history MASE denominator so that only the information available to the methods
changes (\tableref{tab:truncation}). The simulation's estimability result reappears: with 24 observations,
where the classical methods again have two cycles for a period of 12, the foundation models lead---TiRex
1.027, TimesFM-3 1.046, TimesFM-2.5 1.050---against 1.096 for the best classical method, the combination,
and 1.175 for AutoARIMA; the difference was not tested. With 48 observations the combination is level with
them (0.955 against 0.952 to 0.972), and with the full history the leading methods are within 2\% of one
another. Truncation also moves the information set away from the full series a model could have been trained
on, although it cannot rule out that the series were seen.

"""

HYP_OLD = r"""The extended evidence qualifies the trade three times. Among the three foundation models evaluated it belongs
to TimesFM-3 alone (\sectionref{sec:benchmarks})."""
HYP_NEW = r"""The extended evidence qualifies the trade four times. Among the foundation models evaluated it belongs to
TimesFM-3 alone (\sectionref{sec:benchmarks}). It holds for short horizons only: at 48 steps AutoARIMA has the
smaller worst case, and every foundation model mistakes a plateau for a decline (\sectionref{sec:horizon48})."""
HYP_OLD2 = r"""And on the M4 test period with long histories, TimesFM-3 is one of a group of leading methods that cannot be
separated (\sectionref{sec:m4official})."""
HYP_NEW2 = r"""And on the M4 test period with long histories, TimesFM-3 is level with good but not the best M4 entries
(\sectionref{sec:m4official})."""

RECS_OLD = r"""\textbf{Intervals, cost and licence.}"""
RECS_NEW = r"""\textbf{Long horizons.} Beyond about a year of monthly steps the evidence turns: AutoARIMA had the smaller
worst case, and every foundation model forecast a decline on a process that had levelled off, so long-horizon
forecasts from these models should be checked against the recent level before use.

\textbf{Intervals, cost and licence.}"""

LIM_OLD2 = r"""Second, the nine process families are
fixed, the horizon is short ($H = 12$), the seasonal period is 12, and the departures from the assumptions
were applied one at a time, so their interactions were not examined; calibration of foundation models is
reported to degrade with horizon \citep{adler2026calibrated}."""
LIM_NEW2 = r"""Second, the nine process families are
fixed, the pre-registered horizon is short ($H = 12$) and the longer one was examined in one secondary check,
the seasonal period is 12, and the departures from the assumptions were applied one at a time, so their
interactions were not examined."""
LIM_OLD4 = r"""Fourth, no method was tuned by hand, and
the classical methods were run in one implementation (\pkg{StatsForecast}) at its defaults; an expert who
identified each process, or another implementation, could select different models."""
LIM_NEW4 = r"""Fourth, no method was tuned by hand, and
the classical methods were run in \pkg{StatsForecast} at its defaults; a cross-check with \pkg{forecast} on the
seasonal processes reproduced the failures but found one implementation failure, and an expert who identified
each process could select better models."""
LIM_OLD5 = r"""Fifth, three foundation
models were evaluated and they behave differently, so conclusions about one do not transfer to the class;
newer models such as Chronos-2 \citep{ansari2025chronos2} and masked-encoder models such as Moirai
\citep{woo2024moirai} were not included."""
LIM_NEW5 = r"""Fifth, five foundation
models were evaluated and they behave differently, so conclusions about one do not transfer to the class;
masked-encoder models such as Moirai \citep{woo2024moirai} were not included."""

CONC_OLD = r"""With at least four seasonal cycles AutoARIMA is 21--24\% more accurate. Among the three foundation models
evaluated this robustness is specific to TimesFM-3, and randomised parameters, heavy tails and outliers
leave it qualitatively unchanged. On intermittent demand TimesFM-3 shows no advantage over simple
benchmarks built from the history."""
CONC_NEW = r"""With at least four seasonal cycles AutoARIMA is 21--24\% more accurate. Among the five foundation models
evaluated this robustness is specific to TimesFM-3, randomised parameters, heavy tails and outliers leave it
qualitatively unchanged, and it holds for short horizons only: at 48 steps AutoARIMA has the smaller worst
case and every foundation model forecasts a decline on a saturated process. On intermittent demand
TimesFM-3 shows no advantage over simple benchmarks built from the history."""
CONC_OLD2 = r"""On 1\,000 M4 monthly series TimesFM-3 is one of five leading methods whose ranks cannot be separated on the
official test period (OWA 0.862), and with only 24 observations of history its mean MASE is 4.6\% below that
of the best classical method."""
CONC_NEW2 = r"""On the official test period of 1\,000 M4 monthly series TimesFM-3 (OWA 0.862) is level with the M4 entries
ranked fifth to seventh and behind the four best, and with only 24 observations of history its mean MASE is
4.6\% below that of the best classical method."""

REPRO_OLD = r"""(revision \code{5d9f166}), the \path{google/timesfm-2.5-200m-pytorch} weights (revision \code{1d95242}),"""
REPRO_NEW = r"""(revision \code{5d9f166}) and \path{amazon/chronos-2} (revision \code{29ec376}), \pkg{tirex-ts}~1.4.2 with
\path{NX-AI/TiRex} (revision \code{63c7409}), the \path{google/timesfm-2.5-200m-pytorch} weights (revision
\code{1d95242}), \proglang{R}~4.4.1 with \pkg{forecast}~9.0.2 for the cross-check,"""


def main():
    s = P.read_text(encoding="utf-8")
    s = block(s, "\\abstract[Abstract]{", "\\maketitle", ABSTRACT)
    # Forest plot after the table of significant comparisons.
    a = s.index("\\label{tab:opponents}")
    e = s.index("\\end{table}", a) + len("\\end{table}")
    s = s[:e] + "\n" + FOREST + s[e:]
    s = rep(s, "\\subsection{Effect sizes and sensitivity", OVERALL_ADD + "\\subsection{Effect sizes and sensitivity")
    s = rep(s, ESTIM_OLD, ESTIM_NEW)
    s = rep(s, REGIMES_OLD, REGIMES_NEW)
    s = rep(s, EXT_INTRO_OLD, EXT_INTRO_NEW)
    s = block(s, "The stronger classical benchmarks do not change the picture.",
              "\\subsection{Configuration and output of TimesFM-3}", BENCH)
    s = rep(s, D8_OLD, D8_NEW)
    s = rep(s, "\\section{Representativeness and robustness of the design}",
            HORIZON + "\\section{Representativeness and robustness of the design}")
    s = rep(s, "intermittent-demand result means once simple benchmarks are included (\\sectionref{sec:d8-extended}). All of\nit is post hoc.",
            "intermittent-demand result means once simple benchmarks are included (\\sectionref{sec:d8-extended}),\n"
            "and what changes at a longer horizon (\\sectionref{sec:horizon48}). All of it is post hoc.")
    s = rep(s, M4_OLD, M4_NEW)
    s = block(s, "Rolling origins cut from the training data cannot", "\\input{tab_truncation}", M4OFF)
    s = rep(s, HYP_OLD, HYP_NEW)
    s = rep(s, HYP_OLD2, HYP_NEW2)
    s = rep(s, RECS_OLD, RECS_NEW)
    s = rep(s, LIM_OLD2, LIM_NEW2)
    s = rep(s, LIM_OLD4, LIM_NEW4)
    s = rep(s, LIM_OLD5, LIM_NEW5)
    s = rep(s, CONC_OLD, CONC_NEW)
    s = rep(s, CONC_OLD2, CONC_NEW2)
    s = rep(s, REPRO_OLD, REPRO_NEW)
    s = rep(s, "thirteen departures from it", "fourteen departures from it")
    s = rep(s, "Theta and AutoETS deteriorate on D4 as the series
lengthens",
            "Theta deteriorates on D4 as the series
lengthens")
    P.write_text(s, encoding="utf-8")
    print("K10 applied")


if __name__ == "__main__":
    main()
