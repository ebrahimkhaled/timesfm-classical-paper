"""Second simulated referee round (four fresh reviewers, 2026-09-23): revisions to the main text.

Evidence for the new statements: results/round2/ (L1_round2_analyses.py), results/robust/robust_cells.csv,
results/robust/robust_response.csv (now clustered by draw, R5), the checkpoint configuration file and
Ansari et al. (2024, Table 2). Each block is replaced between fixed anchors, so a failed match stops the
script instead of silently skipping an edit.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "manuscript_jof" / "timesfm_jof.tex"


def block(s, start, end, new, keep_end=True):
    a = s.index(start)
    b = s.index(end, a + len(start))
    return s[:a] + new + (s[b:] if keep_end else s[b + len(end):])


def rep(s, old, new, count=1):
    assert old in s, f"not found: {old[:70]!r}"
    return s.replace(old, new, count)


ABSTRACT = r"""\abstract[Abstract]{Time-series foundation models such as Google's TimesFM-3 forecast series they were never
trained on. Whether they should replace classical methods such as ARIMA and exponential smoothing is
difficult to settle on public benchmarks, because few benchmark datasets are absent from every
model's pre-training corpus. This exploratory study describes, under controlled conditions, how
TimesFM-3 behaves relative to classical methods and in which regimes it may be preferred. The
evaluation data are generated from nine known processes, so the model cannot have seen the series.
Across 7\,200 series and a pre-registered protocol, neither family dominates. TimesFM-3 is never more
than 1.31 times worse than the best method in a cell, whereas every classical method is at least 2.2
times worse somewhere; the largest classical failures occur with only two seasonal cycles, where the
automatic methods fall back to non-seasonal models, and without those cells automatic ARIMA's worst
case is 1.62. With four or more cycles automatic ARIMA is 21--24\% more accurate than TimesFM-3 on
seasonal ARIMA data, where seasonal naive is also more accurate. Among the three foundation models
evaluated, this robustness is specific to TimesFM-3. On intermittent demand TimesFM-3 shows no
advantage over simple benchmarks built from the history: forecasting zero beats its median forecast on
the mean absolute scaled error, and the empirical deciles of the history match its pinball loss. In
post-hoc checks, randomised parameters, heavy-tailed noise and outliers leave these patterns
qualitatively unchanged, and on the official test period of 1\,000 M4 monthly series TimesFM-3 is among
five leading methods whose ranks cannot be separated. Because TimesFM-3 is a black box, the study
characterises its behaviour, not the reasons for it; the findings are conditional on the processes
examined, and the model's weights are licensed for non-commercial use only.}

"""

MODEL = r"""\subsection{Architecture and pre-training data}
\label{sec:tfm-architecture}

TimesFM-3 is the third generation of the decoder-only TimesFM family \citep{das2024timesfm,
timesfm3blog}. Each input series is normalised by an iterative reversible instance normalisation, with
linear detrending of strongly trending inputs, and divided into non-overlapping patches of 32 time points,
each embedded as a token; 20 transformer layers with model dimension 1280 and 16 attention heads give
about 330 million parameters (the checkpoint loaded here has 330\,710\,976). Layers of causal attention
along time alternate with layers of attention across variates, so target series and covariates can be
processed jointly, and a contiguous patch masking scheme produces the whole horizon in one forward pass,
in output patches of 64 points. For each step the model returns nine quantiles, the 10th to the 90th
percentile, and its point forecast is the median \citep{timesfm3blog, timesfm3card, timesfm3repo}. These
details come from the developers' blog post and model card and from the configuration file of the
checkpoint (accessed 23 September 2026); none has yet been described in a peer-reviewed publication. The
pre-training corpus of more than one trillion time points combines the GIFT-Eval pre-training collection,
Wikipedia page views to November 2023, Google Trends queries to the end of 2022, and synthetic and
augmented series \citep{timesfm3card}.

\subsection{Checkpoint and configuration}
\label{sec:tfm-config}

The weights (\code{google/\allowbreak timesfm-3.0-pytorch} on the Hugging Face Hub, revision
\code{43046b8}) are loaded with version 3.0.1 of the \pkg{timesfm} \proglang{Python} package, which provides
both the \code{timesfm} and \code{timesfm3} modules \citep{timesfm3repo, timesfm3card}, and are licensed for
non-commercial use only (\sectionref{sec:operational}). The model is used zero-shot: it receives only the
raw context, with no fine-tuning, covariates or seasonal period, through \code{predict\_batch} with its
default settings (no symmetric averaging, no positivity constraint, 32-bit arithmetic). Its point forecast is
the model's own median output; the nine deciles are then sorted, which matters only where they cross
(\sectionref{sec:tfm-check}). A context shorter than the model's working length is left-padded with zeros
and masked, so at $n = 24$ the model sees one partly filled patch; the package's maximum context of
15\,360 points truncates no series in this study, and a series forecast alone or inside a batch of other
lengths gives quantiles that agree to within $2 \times 10^{-5}$. Because no quantile outside the 10th and
90th percentiles is available, the widest interval that can be formed is the nominal 80\% interval. The
weights, code and revision are public, so every forecast can be regenerated (\sectionref{sec:repro}); the
developers' own evaluator settings are examined in \sectionref{sec:tfm-check}.

"""

OVERALL = r"""TimesFM-3 has the lowest mean MASE in 16 of the 36 (DGP, length) cells and the classical methods in 20:
AutoARIMA 10, seasonal naive 4, and two each for Theta, AutoETS and the combination. Against the best
classical method of each cell, 18 differences survive Benjamini--Hochberg correction, 7 favouring
TimesFM-3 and 11 the classical method; because that comparator is selected on the same replications,
these $p$-values are descriptive only. The inferential claims rest on the 180 comparisons with a fixed
opponent (\tableref{tab:opponents}): 132 are significant, 113 favouring TimesFM-3. These counts summarise
the tests; they weight every cell equally and depend on the mix of processes, and pooling the tests into a
single family changes them by at most two (Supporting Information, Section~S6). \textbf{AutoARIMA is the
only classical method that TimesFM-3 does not clearly beat}; against every other method, the combination
included, TimesFM-3 wins the large majority of significant comparisons.

"""

EFFECTS = r"""\subsection{Effect sizes and sensitivity to the choice of test}
\label{sec:effects}

The median Hodges--Lehmann shifts in MASE across the 36 cells are $-0.010$ against AutoARIMA, $-0.091$
against the combination, $-0.133$ against seasonal naive, $-0.183$ against AutoETS and $-0.227$ against
Theta (negative favours TimesFM-3), so against AutoARIMA the typical difference is about one hundredth of a
MASE unit. The Monte Carlo standard error of the paired difference between TimesFM-3 and AutoARIMA is 0.8\%
to 4.8\% of AutoARIMA's mean MASE (median 2.1\%), so differences smaller than about 6\% are unlikely to be
detected in a cell: the 11--9 split against AutoARIMA sits at the resolution of the design and does not show
that the two methods are equivalent. A paired $t$-test agrees with the Wilcoxon test in 163 of 180
comparisons (90.6\%). The largest block of disagreements is on the intermittent process D8 against seasonal
naive: the $t$-test finds TimesFM-3 better at every length ($p < 0.0001$), the signed-rank test finds no
difference ($p = 0.11$ to $0.92$). The mean difference is driven by a minority of series on which seasonal
naive fails badly, whereas on 64.5--72.0\% of series TimesFM-3 is marginally less accurate---the two tests
estimate different quantities of a heavily skewed error distribution (\tableref{tab:ademp}).

"""

ESTIM = r"""\subsection{Correct specification versus estimability}
\label{sec:estimability}

Pre-registered hypothesis H1 held that correctly specified classical models would win on their home
ground, most clearly at short lengths; \textbf{it is not supported in that form}. On D1 and D2 TimesFM-3 is
at least as accurate as the correctly specified AutoARIMA at every length except D2 at $n = 200$, the only
significant difference. Correct specification bought AutoARIMA nothing detectable on short and moderate
series. A post-hoc \emph{Oracle ARIMA}, which knows the true orders and estimates only the parameters by
Gaussian maximum likelihood, is consistent with order selection being the cost: on D1--D3 at $n = 24$
AutoARIMA pays a 9.9\% to 13.9\% penalty for selecting the orders, while the oracle beats TimesFM-3 in 15 of
the 16 ARIMA cells (for example 1.351 against 1.417 on D1 at $n = 24$). On D4 at $n = 24$ most oracle fits
did not converge (156 of 200, used as returned), so that cell is not interpreted.

The seasonal processes show the effect most clearly. With two complete cycles ($n = 24$), AutoETS scores
a mean MASE of \textbf{3.03 on D5, data an ETS process generated}, against 1.14 for seasonal naive and 1.15
for TimesFM-3: the correctly specified model has 2.7 times the error of the naive rule. The failure is not an
over-fitted seasonal model but the absence of one: given $m = 12$ and 24 observations, AutoETS chose a
seasonal form for 8.5\% of the D4 series and none of the D5 series, and AutoARIMA for none (Supporting
Information, Table~S11), whereas seasonal naive applies the known period without estimating anything. The
operative distinction is therefore whether a model is \emph{estimable} from the series at hand, not whether
it is correctly specified. \tableref{tab:robust} quantifies the resulting asymmetry with each method's mean
MASE as a multiple of the best in the same cell---a relative measure, because D3 is hard for every method
and would dominate absolute worst cases. \textbf{TimesFM-3 is never worse than $1.31\times$ the best method
of a cell}, and within 0.8\% of it in the median cell, whereas every classical method is at least $2.2\times$
worse somewhere: AutoARIMA $2.22\times$ and AutoETS $3.50\times$ (both on D4 at $n = 24$), Theta
$4.69\times$, seasonal naive $5.65\times$. Leaving out the two cells with two seasonal cycles, TimesFM-3's
worst ratio is unchanged and AutoARIMA's falls to 1.62 (on D7 at $n = 96$), AutoETS's to 2.72 and the
combination's to 2.08. The worst ratio is a descriptive summary defined after the protocol, and it depends on
the methods compared, notably on seasonal naive with the known period (\sectionref{sec:departures}).

"""

ROBUST_TAB = r"""\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Mean MASE relative to the best method in the same cell, summarised over the 36 cells.}
\label{tab:robust}
\small\setlength{\tabcolsep}{4pt}
\begin{tabular}{lrrrlrl}
\toprule
 & & & \multicolumn{2}{c}{All 36 cells} & \multicolumn{2}{c}{Without the two-cycle cells} \\
\cmidrule(lr){4-5}\cmidrule(lr){6-7}
Method & Median & Mean & Worst & Cell & Worst & Cell \\
\midrule
ROWS
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Each entry divides a method's mean MASE by the lowest mean MASE in the same (process,
length) cell, so a value of 1.00 means that the method was the best in that cell; the mean is arithmetic.
The two-cycle cells are D4 and D5 at $n = 24$. Geometric means and 90th percentiles are in the Supporting
Information, Table~S9.
\end{tablenotes}
\end{threeparttable}
\end{table}"""


def robust_table():
    w = pd.read_csv(ROOT / "results" / "round2" / "worst_ratio_variants.csv")
    names = {"SeasonalNaive": "Seasonal naive", "TimesFM3": "TimesFM-3"}
    means = pd.read_csv(ROOT / "results" / "table_mase.csv")
    means = means[means.horizon_slice == "h1_12"].pivot_table(index=["dgp", "n"], columns="method",
                                                             values="mean_MASE")
    ratio = means.div(means.min(axis=1), axis=0)

    def cell(c):
        d, n = c.strip("()").replace("np.int64(", "").replace(")", "").replace("'", "").split(", ")
        return f"{d} $n={n}$"

    rows = []
    for r in w.itertuples():
        nm = names.get(r.method, r.method)
        vals = [f"{r.median_all:.3f}", f"{ratio[r.method].mean():.3f}", f"{r.worst_all:.2f}",
                cell(r.cell_all), f"{r.worst_excl_two_cycle:.2f}", cell(r.cell_excl)]
        if r.method == "TimesFM3":
            nm = "\\textbf{TimesFM-3}"
            vals = [f"\\textbf{{{v}}}" if i in (0, 1, 2, 4) else v for i, v in enumerate(vals)]
        rows.append(nm + " & " + " & ".join(vals) + " \\\\")
    (ROOT / "manuscript_jof" / "tab_robust.tex").write_text(
        "% generated by code/K9_round2_revisions.py\n" + ROBUST_TAB.replace("ROWS", "\n".join(rows)) + "\n",
        encoding="utf-8")


REGIMES = r"""\subsection{Seasonal and intermittent regimes}
\label{sec:regimes}

\textbf{Strong seasonality with sufficient data (D4).} At $n = 48$, 96 and 200 AutoARIMA's mean MASE is
21.8\%, 21.1\% and 23.7\% below TimesFM-3's (adjusted $p < 0.0001$), and D5 shows the same more mildly (4\%
to 12\%). Once at least four cycles are observed, AutoARIMA recovers the seasonal structure and TimesFM-3
does not match it; seasonal naive, which estimates nothing, is also more accurate than TimesFM-3 on D4 at
every length (1.005 to 1.053 against 1.124 to 1.321). With two cycles the ranking among the others reverses:
TimesFM-3 beats AutoARIMA by 42\% (1.321 against 2.284). Theta and AutoETS deteriorate on D4 as the series
lengthens (Theta 1.94 at $n = 48$ and 4.16 at $n = 200$). D4 is seasonally integrated, so its seasonal
pattern drifts, whereas classical decomposition estimates one fixed pattern from the whole history; with
additive instead of multiplicative decomposition the failure is almost unchanged (in a check on 60
replications, Theta's mean MASE at $n = 200$ was 3.83 against 3.95), so it concerns the model form rather
than the adjustment.

\textbf{Intermittent demand (D8).} On MASE TimesFM-3 reduces error against the best general-purpose
method by 21.7\% to 26.5\% at the four lengths (adjusted $p < 0.0001$) and has the lowest pinball loss of
the pre-registered methods, but it \emph{loses} on RMSSE at every length (Supporting Information,
Table~S6); sMAPE, which scores a zero forecast of a zero outcome as perfect, is not informative here. About
70\% of D8's observations are zero: MASE is minimised by the conditional median, which is zero or near it,
RMSSE by the conditional mean, which is positive, so a median-like forecast wins MASE and loses RMSSE
\citep{kolassa2016count, gneiting2011making}. The same holds against six purpose-built intermittent-demand
methods, added post hoc: Croston's classic and optimised variants, the Syntetos--Boylan approximation
\citep{syntetos2005accuracy}, ADIDA \citep{nikolopoulos2011adida}, IMAPA \citep{petropoulos2015imapa} and
TSB \citep{teunter2011tsb}, the last with StatsForecast's fixed constants $\alpha_d = \alpha_p = 0.2$
(Table~S7). TimesFM-3 beats all six on MASE at every length (24/24 significant; median ratios 0.70 to 0.82),
while the Croston family has the lower RMSSE (0.694--0.769, against 0.774--0.806 for TimesFM-3; AutoARIMA is
lowest at $n = 200$). \sectionref{sec:d8-extended} shows that both of TimesFM-3's advantages on D8 are
matched by simple benchmarks built from the history.

Across horizons ($h = 1$, $1$--$6$ and $1$--$12$) every method degrades and no regime-average ranking
reverses (Supporting Information, Figure~S1). Averaged within regimes, TimesFM-3 has the lowest mean MASE
even among the correctly specified processes, because a few catastrophic classical cells (Theta at 4.16 on
D4 at $n = 200$, AutoETS at 3.03 on D5 at $n = 24$) move a mean far more than several narrow classical wins.

"""

COVERAGE = r"""Averaged over the processes (\figureref{fig:coverage}), TimesFM-3's 80\% coverage stays between 0.802 and
0.834 at every length, on average across lengths closer to nominal than any other method, and it does not
deteriorate with the horizon (0.786 at $h = 1$, 0.814 over $h = 1$--12). Averaging lets over- and
under-coverage cancel, however; the mean per-cell absolute deviation from nominal is 0.047 for TimesFM-3,
0.066 for AutoARIMA, 0.089 for the combination, 0.101 for AutoETS, 0.127 for Theta and 0.144 for seasonal
naive, and TimesFM-3's per-cell 80\% coverage ranges from 0.583 to 0.921. No method delivers reliable 80\%
intervals on all nine processes. The classical intervals rest on Gaussian innovations, violated by
construction on D8 (Bernoulli occurrence with Poisson sizes) and D9 (conditionally Gaussian but
unconditionally heavy-tailed errors). An interval score, which rewards narrow intervals and penalises
outcomes outside them (80\% interval, scaled as MSIS), puts TimesFM-3 first in 22 of the 36 cells
(Supporting Information, Table~S12). On the structural break D6 every classical method covers 0.966 to
0.999, because the break inflates the estimated variance and the intervals become very wide (scaled widths
4.8 to 10.4); TimesFM-3 covers 0.828 to 0.889 with intervals about half as wide (3.0 to 5.1) and has the
lowest interval score at every length.

TimesFM-3 beats the pre-registered mean combination in 27 of 30 significant comparisons. Because the mean
is not robust to a failing member such as Theta, a \emph{median} combination of the same three methods was
also tried (post hoc), in the spirit of \citet{petropoulos2020scum}; it is slightly worse (mean MASE 1.712
against 1.656, TimesFM-3 1.439), and TimesFM-3 still wins 25 of 29 significant comparisons. Under absolute
error the mean combination can never be worse than the average of its members, by convexity, a guarantee
the median does not carry.

"""

EXT_INTRO = r"""\section{Extended evaluation}
\label{sec:extended}

This section asks how precise the summaries of \sectionref{sec:results} are (\sectionref{sec:mcse}),
whether stronger benchmarks and other foundation models change them (\sectionref{sec:benchmarks}), how
much they depend on the configuration of TimesFM-3 (\sectionref{sec:tfm-check}), and what the
intermittent-demand result means once simple benchmarks are included (\sectionref{sec:d8-extended}). All of
it is post hoc.

\subsection{Monte Carlo uncertainty}
\label{sec:mcse}

The Monte Carlo standard error of a cell's mean MASE is 1.5\% to 6.2\% of the mean (median 3.2\%;
Supporting Information, Table~S2). Bootstrapping the replications within each cell (2\,000 draws, paired
across methods), the worst ratio of TimesFM-3 to the cell-best method is 1.31 (95\% interval 1.28 to 1.36)
and that of AutoARIMA, the smallest among the classical methods, 2.22 (2.07 to 2.38); their difference has
an interval of 0.75 to 1.05. Because the best method of a cell is chosen on the same replications, the
statistic could be biased upwards; choosing it on one half of the replications and estimating the ratio on
the other gives 1.32, so the bias is small. These intervals reflect Monte Carlo error only, not the choice
of processes and parameters, which \sectionref{sec:robustness} varies. The count of cells won is less
stable---TimesFM-3's 16 has an interval of 13 to 20---and no conclusion rests on it.

\subsection{Stronger classical benchmarks and other foundation models}
\label{sec:benchmarks}

Six methods were added (\tableref{tab:extended}): dynamic optimised Theta \citep[DOTM;][]{fiorucci2016dotm};
the Comb benchmark of M4, the mean of simple, Holt and damped exponential smoothing on seasonally adjusted
data \citep{makridakis2020m4}; a combination of AutoETS, AutoARIMA and DOTM; TimesFM-2.5
\citep{timesfm25card} and Chronos-Bolt (Base, 205 million parameters) \citep{ansari2024chronos,
chronosboltcard}, both zero-shot and Apache-2.0 licensed; and TimesFM-3 with its developers' evaluator
settings (\sectionref{sec:tfm-check}). TimesFM-2.5 was run with the same evaluator settings (symmetric
averaging, positivity, quantile-crossing correction) and a context limit of 512 points, which truncates no
simulated series, so its matched comparison is with the evaluator-settings row of TimesFM-3; Chronos-Bolt
was run with its defaults.

"""

BENCH = r"""The stronger classical benchmarks do not change the picture. DOTM and the Comb benchmark share Theta's
failure on D4, where a classical decomposition with fixed seasonal indices meets a seasonal pattern that
evolves, and replacing Theta by DOTM leaves the combination's worst ratio at 2.99. TimesFM-3 wins 28 of 29
significant comparisons against DOTM and all 29 against the Comb benchmark; AutoARIMA remains the only
classical method it does not clearly beat (11 wins to 9). \textbf{Among the three foundation models
evaluated, the robustness belongs to TimesFM-3 alone}: TimesFM-2.5 has a worst ratio of 2.18 (on D7 at
$n = 24$), no better than AutoARIMA, and Chronos-Bolt 3.06, although TimesFM-2.5 is the best method in 11
cells, more than any other. Friedman tests with Nemenyi critical differences \citep{demsar2006statistical}
within each regime agree with the pairwise tests: TimesFM-3 is tied for the best mean rank on the linear
processes (with TimesFM-2.5 and AutoARIMA) and on the break and saturation processes (with no classical
method), and AutoARIMA has the best mean rank on the seasonal processes, tied only with TimesFM-3 under its
evaluator settings. Averaged over the design, the 80\% intervals of TimesFM-3 cover 0.814 (Monte Carlo SE
0.003), TimesFM-2.5 0.812, Chronos-Bolt 0.834 and AutoARIMA 0.794 (Table~S3).

"""

TFMCHECK = r"""\subsection{Configuration and output of TimesFM-3}
\label{sec:tfm-check}

The developers' benchmark evaluator averages the forecasts of a series and its negation and constrains
non-negative series to non-negative forecasts, whereas the main study used the package defaults. With
the evaluator settings the worst ratio falls from 1.31 to 1.27 and the geometric mean ratio over the twelve
methods from 1.059 to 1.054; no conclusion changes. The output is a $12 \times 9$ array of deciles whose raw
median equals the point forecast exactly; quantile crossing occurs in 32\% to 46\% of steps on D8 and
essentially never elsewhere, so only on D8 does it matter that the main runs take the raw median as point
forecast and the evaluator-settings runs the median after sorting. Given the month of the year as
past-and-future covariates ($\sin 2\pi t/12$, $\cos 2\pi t/12$) on D4 and D5---the information the classical
methods receive through their period---TimesFM-3's mean MASE rises in seven of the eight cells (for example
1.124 to 1.194 on D4 at $n = 96$), so supplying the period in this form did not close AutoARIMA's seasonal
advantage. Using the mean of the deciles instead of the median as point forecast changes no process by more
than 0.01 except D6 (0.835 to 0.875) and D8.

"""

D8EXT = r"""\subsection{Intermittent demand re-examined}
\label{sec:d8-extended}

Because MASE rewards the conditional median, which on D8 is near zero, the trivial all-zero forecast
belongs in the comparison, and because D8 is independent over time, so do benchmarks that simply use the
empirical distribution of the history \citep{willemain2004bootstrap}: its mean as point forecast and its
deciles as predictive distribution. \tableref{tab:d8ext} adds them, with the scaled mean error (bias) and
periods in stock \citep[PIS;][]{wallstrom2010pis}, which accumulates forecast errors as a stock position
would.

\input{tab_d8ext}

\textbf{The all-zero forecast has the lowest MASE at every length} (0.668 to 0.718), below TimesFM-3's
median forecast (0.683 to 0.780). The MASE advantage of \sectionref{sec:regimes} is thus the advantage of
a forecast close to zero: its bias ($-0.67$ to $-0.57$ MASE units) and PIS ($-81$ to $-74$) are close to
those of the all-zero forecast and imply persistent stock-outs, so it is not evidence of useful accuracy.
With the mean of its deciles as point forecast, TimesFM-3 has an RMSSE of 0.694 to 0.760 and a bias within
0.06 of zero, level with the best Croston-family method and with the mean of the history (0.692 to 0.744).
Its pinball loss, 0.288 to 0.325, is about 15\% below that of the classical methods (0.341 to 0.380), but
their quantiles come from Gaussian intervals that put probability on negative demand; the empirical deciles
of the history score 0.282 to 0.314, slightly lower than TimesFM-3 at every length. \textbf{On intermittent
demand, therefore, TimesFM-3 shows no advantage over simple benchmarks}: it behaves much like the empirical
distribution of the history, and its advantage over the classical methods reflects their Gaussian
intervals. The result concerns a process that is independent over time, the case most favourable to
history-based benchmarks.

"""

DEPART = r"""In the three versions with a known period the conclusions were qualitatively consistent with the main
design (\tableref{tab:robust-design}), although TimesFM-3's worst ratio lies outside the main design's
bootstrap interval. TimesFM-3 is the best method in 14 to 16 cells and within 4\% of the best in the median
cell; its worst ratio rises to 1.49 to 1.56 (bootstrap intervals up to about 1.75), always on the logistic
process D7 at $n = 96$, while the smallest classical worst ratio is 2.09 to 2.32. With the
Benjamini--Hochberg family per opponent, TimesFM-3 wins 93 to 101 of 180 comparisons and loses 27 to 29,
AutoARIMA again being the opponent it does not clearly beat (7--7, 6--7, 10--4 and 8--6 across the four
versions). AutoARIMA's advantage on D4 with at least four cycles persists (median over the three lengths 21\%
to 26\%; with outliers it is ahead at two of the three lengths, by 15\% and 5\%), and the Croston family keeps
the lower RMSSE on D8 in every version.

\textbf{When the classical methods test for seasonality, the gap in worst ratios closes, but not because they
forecast better}: their smallest worst ratio is 1.58 (1.48 to 1.67, AutoARIMA), level with TimesFM-3's 1.55
(1.41 to 1.71). AutoARIMA's worst cell is still D4 at $n = 24$, and its mean MASE there is unchanged (2.30);
what changes is the yardstick. At $n = 24$ the test cannot be applied, every series is treated as
non-seasonal, and seasonal naive loses the true period that made it the best method in that cell (mean MASE
4.26 instead of 1.09), so TimesFM-3 (1.45) becomes the cell-best. Much of the classical deficit in worst
ratios is thus measured against seasonal naive with a known period. With two cycles the automatic classical
methods recover the seasonality in neither configuration: non-seasonal AutoETS has a mean MASE of 2.55 on D5
and 4.25 on D4, against 1.13 and 1.09 for seasonal naive with the true period and 1.11 and 1.45 for
TimesFM-3.

A response-surface regression of the per-series $\log_2$ ratio of TimesFM-3's MASE to AutoARIMA's on the
standardised parameters, $\log_2 n$ and the version, with standard errors clustered by parameter draw
(Supporting Information, Tables~S4 and~S5, and Figure~S2), shows that the dependence on the settings is
modest. The largest systematic effect is length: each doubling of $n$ moves the ratio against TimesFM-3 by
20\% on D4 and 11\% on D5, and in its favour on D6 and D8. Outliers favour TimesFM-3 on the seasonal
processes (14\% and 10\%); the other version effects are at most 0.09 in absolute value. Among the
parameters only the demand probability of D8 has a large effect; the ratio is flat in the autoregressive
coefficient of D1 and the GARCH persistence of D9, grows in favour of TimesFM-3 with the size of the break in
D6, and varies with the inflection point of D7 in a way a linear term does not capture (Figure~S2). The
regressions explain little of the per-series variation ($R^2 \leq 0.26$).

"""

M4 = r"""\section{Application to M4 monthly data}
\label{sec:realdata}

Whether TimesFM-3 has seen the M4 data cannot be settled, but the documented corpus makes it less likely
than for many public benchmarks: its real-world part is the GIFT-Eval pre-training collection (without the
datasets overlapping fev-bench), Wikipedia page views and Google Trends \citep{timesfm3card}, and that
collection is built to exclude the GIFT-Eval test datasets, of which M4 Monthly is one
\citep{aksu2024gifteval, giftevalpretrain}. The exclusion works at the level of datasets, and the
synthetic and augmented part of the corpus is not documented. TimesFM-2.5 lists the same sources
\citep{timesfm25card}. The position of Chronos-Bolt differs: the original Chronos models were trained on M4
Monthly with its final 18 observations, the official test period, held out \citep[Table~2]{ansari2024chronos};
if, as its model card suggests, Chronos-Bolt shares that corpus, its M4 forecasts are in-domain rather than
zero-shot. Because no corpus can be inspected, the real-data tier is secondary evidence. This section reports
a rolling-origin evaluation (\sectionref{sec:m4results}), the official M4 test period
(\sectionref{sec:m4official}) and an experiment with truncated histories (\sectionref{sec:truncation}); the
last two are post hoc.

\subsection{Rolling-origin evaluation}
\label{sec:m4results}

A seeded sample of 1\,000 series is drawn from the 32\,581 M4 Monthly series with at least 138 training
observations, enough for a context of 120 and the 18-month horizon. Their training periods have a median of 281 observations (interquartile range 198
to 306), against 202 (82 to 306) for all 48\,000 series, so the sample over-represents the long end of the
population. Each series is evaluated at up to three origins 12 months apart with M4's horizon $h = 18$
(2\,932 windows; the shortest series cannot support a third origin); consecutive windows overlap by six
months, so the errors of a series are averaged over its origins and the series are the independent units of
the paired Wilcoxon tests. TimesFM-3 and the pre-registered classical methods were run on this tier.
TimesFM-3 (mean MASE 0.914) significantly outperforms seasonal naive (1.280; better on 80.1\% of series),
Theta (0.970; 56.8\%) and AutoETS (0.951; 54.1\%), and shows no detectable difference from AutoARIMA (0.923;
52.6\%, adjusted $p = 0.27$) or the combination (0.907; 48.5\%, adjusted $p = 0.27$).

This ties TimesFM-3 with AutoARIMA on long, mostly seasonal series, rather than showing the 21\% to 24\%
AutoARIMA advantage found on the simulated D4. The simulated seasonal process is a single, sharply seasonal
model, whereas real series mix trend, seasonality and irregular components in proportions the simulation
does not reproduce (\sectionref{sec:representativeness}); an advantage from contamination cannot be excluded
either. The probabilistic results also diverge: TimesFM-3's 80\% intervals cover 0.765 against 0.801 for the
combination, yet its pinball loss is the lowest of the six methods (0.363, against 0.365 for the combination
and 0.374 for AutoARIMA). Its distribution is slightly better overall while its 80\% interval is too narrow,
the fragility of foundation-model calibration reported by \citet{adler2026calibrated}.

"""

M4OFF = r"""Rolling origins cut from the training data cannot be placed against published M4 results, so the same
series were also forecast for the official 18-month test period from their full histories and scored as in
M4, with the overall weighted average (OWA) of sMAPE and MASE relative to the official Naive2 forecasts
\citep{makridakis2020m4}, for the twelve methods of \sectionref{sec:benchmarks} and the Naive2 reference.

\input{tab_m4official}

Theta and the Comb benchmark improve on Naive2 by 7\% to 9\% in OWA (\tableref{tab:m4official}), in line
with the competition. TimesFM-3 has an OWA of 0.862 (0.857 with its evaluator settings), TimesFM-2.5 0.864,
the two combinations 0.867 and 0.868, and AutoARIMA 0.891. A Friedman test on per-series ranks rejects the
equality of the thirteen methods, but the two combinations, TimesFM-3 in both configurations, TimesFM-2.5
and AutoARIMA lie within the Nemenyi critical difference of the best mean rank \citep{demsar2006statistical}:
five distinct methods, one of them in two configurations, whose ranks cannot be separated with 1\,000
series. Rank-based comparisons depend on which methods are included \citep{benavoli2016should}, and the set
contains two near-identical combinations and two configurations of TimesFM-3. On real monthly series with
long histories, TimesFM-3 is one of a group of leading methods, not a clear winner.

\subsection{Truncated histories}
\label{sec:truncation}

The official test period was also forecast from only the last 24, 48 or 96 observations of each training
series, with the full-history MASE denominator so that only the information available to the methods
changes (\tableref{tab:truncation}). The simulation's estimability result reappears: with 24 observations,
where the classical methods again have two cycles for a period of 12, TimesFM-3 has a mean MASE of 1.046,
against 1.175 for AutoARIMA, 1.129 for AutoETS and 1.096 for the best classical method, the combination, a
difference of 4.6\% that was not tested; with 48 the combination is level with it (0.955 against 0.961), and
with the full history the leading methods are within 2\% of one another. Truncation also moves the
information set away from the full series a model could have been trained on, although it cannot rule out
that the series were seen.

"""

COST = r"""\subsection{Computational cost}
\label{sec:cost}

Timed separately on the same 200 seasonal series of length 96, seasonal naive took 3.1\,ms per series,
Theta 9.0\,ms, TimesFM-3 23.2\,ms (batched on an NVIDIA GTX 1660 Ti, excluding a one-off model load of
3.0\,s), AutoETS 102.0\,ms and AutoARIMA 2\,382.7\,ms, each classical method on one CPU core: automatic
ARIMA searches over orders and fits each candidate by maximum likelihood, separately for every series,
whereas TimesFM-3 amortises one forward pass over a batch. Per series, Theta and seasonal naive were thus
faster than TimesFM-3 and AutoETS about four times slower, and the classical methods parallelise trivially:
in the main run, all four classical methods over the 7\,200 series took 7.3 minutes on 22 cores, against 3.2
minutes for TimesFM-3 on one consumer GPU, a ratio of $2.3\times$ that is dominated by AutoARIMA and depends
on the hardware. Memory cannot be compared directly, because the profiler used sees neither the compiled
kernels of the classical methods nor GPU memory; structurally, the classical methods hold a handful of
parameters per series, whereas TimesFM-3 keeps its checkpoint of about 1.3\,GB resident, whatever the number
of series.

"""

HYP = r"""\subsection{Assessment of the pre-registered hypotheses}
\label{sec:hypotheses}

\textbf{None of the five hypotheses survives unqualified}: H1 and H5 are not supported, H4 is contradicted,
and H2 and H3 are partially supported. The protocol did not state decision rules, so these verdicts are
judgements on the pattern of pre-registered tests. \textbf{H1} (correctly specified classical models beat
TimesFM-3 on their home ground, most at short lengths) is not supported as stated---at short lengths the gap
runs the other way---and holds only where a model is both correctly specified and estimable (D4 and D5 at
$n \geq 48$). \textbf{H2} (TimesFM-3 wins wherever no classical form is correct) is partially supported:
mildly on breaks; not on the logistic process, where the outcome depends on length; and on intermittent
demand only against the classical methods, not against simple benchmarks built from the history.
\textbf{H3} (on D9 the families tie in the mean and classical intervals under-cover) is partially supported:
they tie, but only AutoARIMA under-covers. \textbf{H4} (the combination beats every classical method and is
TimesFM-3's hardest opponent) is contradicted in both clauses: AutoARIMA beats the combination on mean MASE
and is the harder opponent (11--9 against 27--3). \textbf{H5} (both families under-cover at 80\%, TimesFM-3
more at longer horizons) is not supported: averaged over processes TimesFM-3 is close to nominal, its
coverage does not fall with the horizon, and the classical methods over-cover from $n = 96$; per cell the
deviations are large but not systematically downward.

\subsection{Robustness versus peak accuracy}
\label{sec:tradeoff}

The classical methods' 20 cell wins are spread over five methods, so which classical method wins is not
knowable in advance without the model selection a foundation model is meant to remove. TimesFM-3, one
untuned model, is not significantly worse than the best classical method in 25 of the 36 cells; the best
classical method is ahead in the other 11, over five processes, by small margins on D2 and D3 and by large
ones only on D4, D5 and D7 at $n = 96$ (these comparisons with a selected opponent are descriptive). The
evidence therefore supports neither the conclusion that foundation models have superseded classical methods
nor the opposite, but a narrower one: \textbf{in this design TimesFM-3 behaved robustly rather than with peak
accuracy}. It is rarely the best method and never among the worst, whereas the automatic classical methods
are sometimes excellent and sometimes catastrophic. For one well-understood series that trade is
unattractive; for many heterogeneous series and no capacity to diagnose each one, it favoured TimesFM-3 here.

The extended evidence qualifies the trade three times. Among the three foundation models evaluated it belongs
to TimesFM-3 alone (\sectionref{sec:benchmarks}). Its size depends on the yardstick: much of the classical
deficit is measured against seasonal naive with a known period, and without the two-cycle cells AutoARIMA's
worst ratio is 1.62 against TimesFM-3's 1.31 (\sectionref{sec:estimability}, \sectionref{sec:departures}).
And on the M4 test period with long histories, TimesFM-3 is one of a group of leading methods that cannot be
separated (\sectionref{sec:m4official}).

"""

LIMITS = r"""\subsection{Limitations}
\label{sec:limitations}

First, simulated series are clean and free of the measurement error, calendar effects and regime changes of
applied work; the M4 tier addresses this only in part, and the randomised design still leaves about a
quarter of M4 monthly series, and all other frequencies, outside the regions studied, with coverage in four
features a necessary rather than sufficient condition for similarity. Second, the nine process families are
fixed, the horizon is short ($H = 12$), the seasonal period is 12, and the departures from the assumptions
were applied one at a time, so their interactions were not examined; calibration of foundation models is
reported to degrade with horizon \citep{adler2026calibrated}. Third, TimesFM-3 was used zero-shot and
univariate, leaving its multivariate and covariate capabilities untested; fine-tuning was excluded because
fine-tuning on one series of 24 to 200 points is not meaningful for a model of this size and fine-tuning on
the DGPs would remove the separation between model and test data. Fourth, no method was tuned by hand, and
the classical methods were run in one implementation (\pkg{StatsForecast}) at its defaults; an expert who
identified each process, or another implementation, could select different models. Fifth, three foundation
models were evaluated and they behave differently, so conclusions about one do not transfer to the class;
newer models such as Chronos-2 \citep{ansari2025chronos2} and masked-encoder models such as Moirai
\citep{woo2024moirai} were not included. Sixth, the summaries that carry the robustness finding---worst
ratios and win counts---were defined after the protocol and depend on the methods and cells compared.
Seventh, the protocol was frozen before any forecast but held in the replication archive rather than
deposited with an external registry, and several analyses are post hoc---the Croston and history
benchmarks, the combination rule, the Oracle ARIMA, Sections~\ref{sec:extended} and~\ref{sec:robustness},
and the official-test and truncation analyses of \sectionref{sec:realdata}---and are reported separately from
the pre-registered comparison.

\section{Conclusion}
\label{sec:conclusion}

This study compared TimesFM-3 with classical methods on 7\,200 series from nine known processes under a
pre-registered protocol, in a design where realisation-level contamination is impossible and the model
families searched by AutoARIMA and AutoETS contain the true process of D1--D5. Neither family dominates.
TimesFM-3 wins 113 of 132 significant pairwise comparisons, only AutoARIMA holding its own (11--9), and it
is never more than 1.31 times worse than the best method in a cell (95\% interval 1.28 to 1.36), while every
classical method is at least 2.2 times worse somewhere---mostly with two seasonal cycles, where the
automatic methods fall back to non-seasonal models; without those cells AutoARIMA's worst ratio is 1.62.
With at least four seasonal cycles AutoARIMA is 21--24\% more accurate. Among the three foundation models
evaluated this robustness is specific to TimesFM-3, and randomised parameters, heavy tails and outliers
leave it qualitatively unchanged. On intermittent demand TimesFM-3 shows no advantage over simple
benchmarks built from the history.

On 1\,000 M4 monthly series TimesFM-3 is one of five leading methods whose ranks cannot be separated on the
official test period (OWA 0.862), and with only 24 observations of history its mean MASE is 4.6\% below that
of the best classical method. The finding most likely to transfer concerns the classical side, where the
mechanism can be examined: what matters is whether a classical model is \emph{estimable} from the data, not
only whether it is correctly \emph{specified}---with two cycles AutoETS almost never selected a seasonal form
and had 2.7 times the error of seasonal naive on data from an ETS process. Outside accuracy, TimesFM-3 was
2.3 times faster end to end than the parallelised classical suite on the hardware used, and its weights are
licensed for non-commercial use only, which for commercial users decides the question before accuracy does.

The study is exploratory. It describes how one black-box model behaves on data of known structure, does not
explain that behaviour, and remains conditional on the processes, parameter ranges, horizon and benchmarks
examined. Studies of other foundation models, frequencies and multivariate problems, and of the internal
representations of these models, will be needed before the boundary between learned and parametric
forecasting can be stated in general terms.

\section{Computational details and reproducibility}
\label{sec:repro}

All results were produced with \proglang{Python}~3.13 \citep{python}, \pkg{statsforecast}~2.1.1
\citep{statsforecast}, \pkg{timesfm}~3.0.1 with the \path{google/timesfm-3.0-pytorch} weights (revision
\code{43046b8}) \citep{timesfm3repo}, \pkg{chronos-forecasting}~2.3.2 with \path{amazon/chronos-bolt-base}
(revision \code{5d9f166}), the \path{google/timesfm-2.5-200m-pytorch} weights (revision \code{1d95242}),
\pkg{PyTorch}~2.6.0 with CUDA~12.4 and cuDNN~9.1 \citep{paszke2019pytorch}, \pkg{NumPy}
\citep{harris2020numpy}, \pkg{pandas} \citep{mckinney2010pandas}, \pkg{SciPy} \citep{virtanen2020scipy} and
\pkg{Matplotlib} \citep{hunter2007matplotlib}, on an NVIDIA GTX 1660 Ti (driver 591.86) with a 24-core CPU
and 32\,GB of memory; parallel classical runs use 22 worker processes. The full package list is pinned in the
replication archive. Every simulated series is seeded from its own identifiers, so the study regenerates
exactly, independently of core count or execution order, and each cached stage can be rerun alone. The
foundation models were run in 32-bit arithmetic without random sampling; rerunning two TimesFM-3 cells
reproduced the stored quantiles exactly, although other hardware may differ in the last digits because GPU
floating-point reductions are not associative. The protocol, with its five hypotheses, was frozen on 8
September 2026, before any forecast was produced; it is in the replication archive with a dated log of the
thirteen departures from it, each reasoned, and every post-hoc analysis is marked as such. Every DOI in the
bibliography was resolved and compared with its entry.

"""


def robust_design_table():
    p = ROOT / "manuscript_jof" / "tab_robust_design.tex"
    t = p.read_text(encoding="utf-8")
    t = rep(t, "Est.\\ period", "Tested seas.")
    t = rep(t, "the ranges in Table~S9 of", "the ranges in Table~S8 of")
    t = rep(t, "within each (column, opponent) family of 36 cells, as in the main design.",
            "within each (column, opponent) family of 36 cells (the main design's families also include the "
            "three horizon slices).")
    t = rep(t, "In the estimated-period column the classical methods receive the period chosen by the M4 "
               "seasonality test;",
            "In the tested-seasonality column the classical methods use $m = 12$ only where the M4 "
            "seasonality test finds seasonality;")
    p.write_text(t, encoding="utf-8")


def main():
    robust_table()
    robust_design_table()
    s = P.read_text(encoding="utf-8")

    # Front matter and introduction.
    s = block(s, "\\abstract[Abstract]{", "\\maketitle", ABSTRACT)
    s = rep(s, "which its developers report as the top-ranked pre-trained model on three\npublic benchmarks "
               "\\citep{timesfm3blog}.",
            "which its developers report as the top-ranked pre-trained model on three\npublic benchmarks "
            "\\citep{timesfm3blog}, a claim open to the leakage concerns discussed next.")
    s = rep(s, "horizons, under a protocol pre-registered before any forecast was produced; every departure from it is\n"
               "recorded.",
            "horizons, under a protocol written and frozen before any forecast was produced; every departure from it\n"
            "is recorded. This pre-registered comparison is confirmatory in design; everything after it is post hoc\n"
            "and exploratory, and is labelled as such.")
    s = rep(s, "judged \\citep{makridakis2020m4}.", "judged \\citep{makridakis2000m3, makridakis2020m4}.")
    s = rep(s, "Theta won M3 \\citep{assimakopoulos2000theta}",
            "Theta \\citep{assimakopoulos2000theta} won M3 \\citep{makridakis2000m3}")
    s = block(s, "\\subsection{Architecture and pre-training data}", "\\section{Design of the simulation study}",
              MODEL)

    # Design.
    s = rep(s, "  pinball loss, 80\\% coverage); for each pair of methods and cell: the pseudo-median of the paired\n"
               "  MASE difference. \\\\[2pt]",
            "  pinball loss, 80\\% coverage); for each pair of methods and cell: the pseudo-median of the paired\n"
            "  MASE difference. Summaries across cells (worst ratio, win counts) were defined post hoc. \\\\[2pt]")
    s = rep(s, "  intervals. \\\\\n\\bottomrule",
            "  intervals. With 200 replications the Monte Carlo standard error of a paired MASE difference is about\n"
            "  2\\% of the mean (\\sectionref{sec:effects}). \\\\\n\\bottomrule")
    s = rep(s, "  (\\sectionref{sec:departures}): parameters drawn per series from wide ranges (Table~S9), four versions\n"
               "  (Gaussian, heavy-tailed, outliers, estimated period), 200 replications per cell.",
            "  (\\sectionref{sec:departures}): parameters drawn per series from wide ranges (Table~S8), four versions\n"
            "  (Gaussian, heavy-tailed, outliers, tested seasonality), 200 replications per cell.")
    s = rep(s, "D8 & Intermittent demand          & $P = 0.3$, size $1 + \\mathrm{Pois}(4)$      & neither \\\\",
            "D8 & Intermittent demand          & $p = 0.3$, size $1 + \\mathrm{Pois}(4)$      & neither \\\\")
    s = rep(s, "the conditional variance is not. In D6, $\\sigma$ is the standard deviation of the observation\nnoise.",
            "the conditional variance is not. Innovations are Gaussian with standard deviation $\\sigma = 2$ ($\\sigma = 3$\n"
            "in D7; D8 has none). D1, D2 and D9 fluctuate about a mean of 100 after a burn-in of 300 steps (D9:\n"
            "$\\omega = 0.1$); D3 starts at 100 after its differences are burnt in; D4 starts from the cycle\n"
            "$100 + 10\\sin(2\\pi k/12)$ plus noise, its seasonal differences burnt in; D5 starts from level 100, trend\n"
            "0.2 and seasonal states $10\\sin(2\\pi k/12)$; in D6 the level is a random walk from 100 with innovation\n"
            "standard deviation 0.5 and $\\sigma$ is that of the observation noise; D7 has lower asymptote 20; in D8 a\n"
            "demand occurs with probability $p$.")
    s = rep(s, "that data are monthly---but it favours the classical methods on D4 and D5; \\sectionref{sec:robustness}\n"
               "removes the advantage by making them estimate the period.",
            "that data are monthly---but it favours the classical methods on D4 and D5 once enough cycles are\n"
            "observed; with two cycles they rarely use it (\\sectionref{sec:estimability}).\n"
            "\\sectionref{sec:robustness} examines the alternative of testing for seasonality.")
    s = rep(s, "symmetric percentage error of the M4 competition. MAPE, undefined at zero---for 9.96\\% of all evaluations, every one on D8\n"
               "\\citep{hyndman2006mase, kolassa2016count}---is reported only in the Supporting Information (Section~S1).",
            "symmetric percentage error of the M4 competition. MAPE is undefined when an actual value is zero, which\n"
            "happens only on D8 (in 9.96\\% of all evaluations over the three horizon slices), and is reported only\n"
            "in the Supporting Information (Section~S1) \\citep{hyndman2006mase, kolassa2016count}.")
    s = rep(s, "Within each (DGP, length, horizon) cell, TimesFM-3 is compared",
            "Within each (DGP, length) cell and horizon slice ($h = 1$, $1$--$6$ and $1$--$12$), TimesFM-3 is compared")
    s = rep(s, "Benjamini--Hochberg procedure at a false discovery rate of 0.05 within each opponent family\n"
               "\\citep{benjamini1995fdr}.",
            "Benjamini--Hochberg procedure at a false discovery rate of 0.05 within each opponent family of 108\n"
            "tests (36 cells and three slices), as pre-registered \\citep{benjamini1995fdr}; the results report the\n"
            "$h = 1$--12 slice.")

    # Results.
    s = block(s, "TimesFM-3 has the lowest mean MASE in 16 of the 36", "\\begin{table}[!htbp]\n\\centering\n"
              "\\begin{threeparttable}\n\\caption{Significant pairwise", OVERALL)
    s = rep(s, "\\item \\textit{Note:} Paired Wilcoxon signed-rank tests in the 36 (process, length) cells,\n"
               "Benjamini--Hochberg corrected within each opponent family.",
            "\\item \\textit{Note:} Paired Wilcoxon signed-rank tests in the 36 (process, length) cells at\n"
            "$h = 1, \\dots, 12$, Benjamini--Hochberg corrected within each opponent family of 108 tests (three\n"
            "horizon slices).")
    s = block(s, "\\subsection{Effect sizes and sensitivity", "\\subsection{Correct specification versus", EFFECTS)
    s = block(s, "\\subsection{Correct specification versus", "\\input{tab_robust}", ESTIM)
    s = block(s, "\\subsection{Seasonal and intermittent regimes}", "\\subsection{Coverage of intervals", REGIMES)
    s = block(s, "Averaged over the processes (\\figureref{fig:coverage})", "\\section{Extended evaluation}",
              COVERAGE)

    # Extended evaluation.
    s = block(s, "\\section{Extended evaluation}", "\\input{tab_extended}", EXT_INTRO)
    s = block(s, "The stronger classical benchmarks do not change the picture.",
              "\\subsection{Configuration and output of TimesFM-3}", BENCH)
    s = block(s, "\\subsection{Configuration and output of TimesFM-3}", "\\subsection{Intermittent demand re-examined}",
              TFMCHECK)
    s = block(s, "\\subsection{Intermittent demand re-examined}", "\\section{Representativeness and robustness",
              D8EXT)

    # Robustness.
    s = rep(s, "78.4\\%) with half as many series. Across thresholds", "78.4\\%). Across thresholds")
    s = rep(s, "covers 76\\% to 89\\% of M4 at the 95th percentile and always more than the fixed design,",
            "covers 76\\% to 89\\% of M4 at the 95th percentile and never less than the fixed design,")
    s = rep(s, "\\tableref{tab:dgps} (Supporting Information, Table~S9):", "\\tableref{tab:dgps} (Supporting Information, Table~S8):")
    s = rep(s, "(a demand multiplied by five on D8), with the held-out values left clean; and \\emph{estimated period}, in\n"
               "which the classical methods receive the period chosen by the 90\\% autocorrelation test of the M4\n"
               "benchmarks \\citep{makridakis2020m4}, applied when at least three cycles are observed.",
            "(a demand multiplied by five on D8), with the held-out values left clean; and \\emph{tested seasonality},\n"
            "in which the classical methods use $m = 12$ only if the 90\\% autocorrelation test of the M4 benchmarks\n"
            "\\citep{makridakis2020m4} finds seasonality, applied when at least three cycles are observed, and\n"
            "$m = 1$ otherwise.")
    s = block(s, "In the three versions with a known period the conclusions", "\\section{Application to M4 monthly data}",
              DEPART)

    # M4, cost.
    s = block(s, "\\section{Application to M4 monthly data}", "\\subsection{The official M4 test period}", M4)
    s = block(s, "Rolling origins cut from the training data cannot", "\\input{tab_truncation}", M4OFF)
    s = block(s, "\\subsection{Computational cost}", "\\subsection{Licensing, interpretability", COST)
    s = rep(s, "simulation (\\sectionref{sec:coverage}) but not on M4,", "simulation (\\sectionref{sec:coverage}) but under-covered on M4,")

    # Discussion, conclusion, reproducibility.
    s = block(s, "\\subsection{Assessment of the pre-registered hypotheses}", "\\subsection{Practical recommendations}", HYP)
    s = block(s, "\\subsection{Limitations}", "\\section*{Acknowledgements}", LIMITS)

    for gone in ["tab:mase", "sec:conformal", "estimated period", "15\\% lower", "refuted"]:
        assert gone not in s, gone
    P.write_text(s, encoding="utf-8")
    print("round-2 revisions applied")


if __name__ == "__main__":
    main()
