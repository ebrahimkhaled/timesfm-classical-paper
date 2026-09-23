"""Build manuscript_jof/supporting_information.tex (JoF: appendices as separate files).

S1  Results under the mean absolute percentage error (the appendix of the AJS version)
S2  Mean MASE with Monte Carlo standard errors (N7 si_mcse.tex)
S3  Coverage of 80% intervals by process (N7 si_coverage.tex)
S4  Gaussian versus split-conformal intervals (N7 si_conformal.tex)
S5  Response-surface regressions of the robustness study (from results/robust/robust_response.csv)
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "manuscript_jof"
SRC_AJS = ROOT / "manuscript" / "timesfm_vs_classical.tex"

RANGES_TEX = r"""\begin{table}[!htbp]
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
\item \textit{Note:} Parameters not listed are as in Table~2 of the main text. The intervals contain the
fixed values of the main design. The rule for D9 keeps the conditional variance stationary and puts
a small point mass at $b = 0.97 - a$. Seeds are disjoint from those of the main design; the five
versions share the parameter draws and, except for the heavy-tailed D8 sizes, the underlying normal
draws.
\end{tablenotes}
\end{threeparttable}
\end{table}"""


def response_table():
    full = pd.read_csv(ROOT / "results" / "robust" / "robust_response.csv")
    return (one_table(full[full.dgp.isin(["D1", "D2", "D3", "D4"])], "D1--D4", "tab:si-response")
            + "\n" + one_table(full[full.dgp.isin(["D5", "D6", "D7", "D8", "D9"])], "D5--D9",
                               "tab:si-response2"))


def one_table(r, part, label):
    r = r[r.term != "Intercept"].copy()
    name = {"logn": "$\\log_2 n$"}
    rows = []
    for _, x in r.iterrows():
        t = x.term
        if t.startswith("C(variant"):
            t = "version: " + t.split("[T.")[1].rstrip("]").replace("_", " ")
        elif t.startswith("par_"):
            t = "parameter " + t[4:].replace("_", " ")
        else:
            t = name.get(t, t)
        rows.append(f"{x.dgp} & {t} & {x.coef:.3f} & [{x.lo:.3f}, {x.hi:.3f}] & {x.p:.3f} & {x.r2:.3f} \\\\")
    body = "\n".join(rows)
    return ("\\begin{table}[!htbp]\n\\centering\n\\begin{threeparttable}\n"
            f"\\caption{{Response-surface regressions of the robustness study, processes {part}.}}\n"
            f"\\label{{{label}}}\n"
            "\\scriptsize\n\\begin{tabular}{llcccc}\n\\toprule\n"
            "Process & Term & Coefficient & 95\\% interval & $p$ & $R^2$ \\\\\n\\midrule\n"
            f"{body}\n\\bottomrule\n\\end{{tabular}}\n"
            "\\begin{tablenotes}[flushleft]\\footnotesize\n\\item \\textit{Note:} One ordinary "
            "least-squares regression per process of the per-series $\\log_2$ ratio of the MASE of "
            "TimesFM-3 to that of AutoARIMA on $\\log_2 n$ (not standardised), the version (reference: "
            "random parameters with Gaussian innovations) and the drawn parameters, each standardised to "
            "mean 0 and standard deviation 1. Standard errors are clustered by parameter draw, because the "
            "five versions of a draw share its parameters and normal draws; 4\\,000 series per "
            "process (3\\,985 for D8, where series with a zero MASE denominator are excluded). Positive "
            "coefficients move the ratio against TimesFM-3.\n\\end{tablenotes}\n"
            "\\end{threeparttable}\n\\end{table}\n")


NAMES = {"SeasonalNaive": "Seasonal naive", "Theta": "Theta", "AutoETS": "AutoETS",
         "AutoARIMA": "AutoARIMA", "Combination": "Combination", "TimesFM3": "TimesFM-3"}


def _tab(caption, label, spec, head, rows, note, size="\\small"):
    return ("\\begin{table}[!htbp]\n\\centering\n\\begin{threeparttable}\n"
            f"\\caption{{{caption}}}\n\\label{{{label}}}\n{size}\\setlength{{\\tabcolsep}}{{4pt}}\n"
            f"\\begin{{tabular}}{{{spec}}}\n\\toprule\n{head} \\\\\n\\midrule\n"
            + "\n".join(r + " \\\\" for r in rows)
            + "\n\\bottomrule\n\\end{tabular}\n\\begin{tablenotes}[flushleft]\\footnotesize\n"
            f"\\item \\textit{{Note:}} {note}\n\\end{{tablenotes}}\n\\end{{threeparttable}}\n\\end{{table}}\n")


def _cell(c):
    d, n = c.strip("()").replace("np.int64(", "").replace(")", "").replace("'", "").split(", ")
    return f"{d}, $n = {n}$"


def diagnostics():
    """Second-review-round diagnostics (results/round2, from L1_round2_analyses.py)."""
    r2 = ROOT / "results" / "round2"
    w = pd.read_csv(r2 / "worst_ratio_variants.csv")
    rows = [f"{NAMES[r.method]} & {r.median_all:.3f} & {r.geo_mean_all:.3f} & {r.p90_all:.2f} & "
            f"{r.worst_all:.2f} & {r.worst_excl_two_cycle:.2f} & {_cell(r.cell_excl)}"
            for r in w.itertuples()]
    t1 = _tab("Ratio of each method's mean MASE to the best in the same cell, with and without the "
              "two-cycle cells.", "tab:si-worst", "lcccccl",
              "Method & Median & Geom.\\ mean & 90th pct. & Worst & Worst excl. & Cell of worst excl.",
              rows, "Main design, 36 cells, $h = 1, \\dots, 12$. ``Excl.'' leaves out D4 and D5 at "
              "$n = 24$, where only two seasonal cycles are observed; the 90th percentile is taken over "
              "the 36 cells.")
    ms = pd.read_csv(r2 / "model_selection.csv")
    rows = []
    for (d, n), g in ms.groupby(["dgp", "n"]):
        e = ", ".join(f"{k} ({v})" for k, v in g.ets.value_counts().head(3).items())
        a = ", ".join(f"{k.replace('[12]', '')} ({v})" for k, v in g.arima.value_counts().head(2).items())
        rows.append(f"{d} & {n} & {100 * g.ets_seasonal.mean():.1f} & "
                    f"{100 * g.arima_seasonal.mean():.1f} & {e} & {a}")
    t2 = _tab("Model forms chosen by AutoETS and AutoARIMA on the seasonal processes, given $m = 12$.",
              "tab:si-forms", "llccp{4.3cm}p{4.3cm}",
              "Process & $n$ & ETS seas.\\ (\\%) & ARIMA seas.\\ (\\%) & Most frequent ETS forms & "
              "Most frequent ARIMA orders", rows,
              "200 replications per row, the series of the main design; counts out of 200 in "
              "parentheses. A form is seasonal when it has a seasonal component (ETS) or a non-zero "
              "seasonal order (ARIMA).", size="\\scriptsize")
    iv = pd.read_csv(r2 / "interval_score.csv")
    p = iv.pivot_table(index="dgp", columns="method", values="IS80")[list(NAMES)]
    rows = []
    for d, r in p.iterrows():
        b = r.idxmin()
        rows.append(d + " & " + " & ".join(
            (f"\\textbf{{{r[c]:.2f}}}" if c == b else f"{r[c]:.2f}") for c in NAMES))
    t3 = _tab("Scaled 80\\% interval score by process, averaged over the four lengths.", "tab:si-is",
              "lcccccc", "Process & " + " & ".join(NAMES.values()), rows,
              "Interval score of $[q_{0.1}, q_{0.9}]$ with $\\alpha = 0.2$ (width plus $2/\\alpha$ times "
              "the distance by which the outcome falls outside the interval), averaged over the horizon "
              "and scaled by the MASE denominator, as for MSIS; lower is better, the best in bold. "
              "TimesFM-3 has the lowest score in 22 of the 36 (process, length) cells.")
    rc = pd.read_csv(r2 / "r_forecast_check_summary.csv")
    rows = [f"{r.dgp} & {r.n} & {r['MASE_R_auto.arima']:.3f} & {r.MASE_AutoARIMA:.3f} & {r.MASE_R_ets:.3f} & "
            f"{r.MASE_AutoETS:.3f} & {r.MASE_R_thetaf:.3f} & {r.MASE_Theta:.3f} & "
            f"{100 * r.R_arima_seasonal_share:.0f} / {100 * r.R_ets_seasonal_share:.0f}"
            for _, r in rc.iterrows()]
    t4 = _tab("Classical methods in \\pkg{forecast} (R) and \\pkg{StatsForecast} (Python) on the seasonal "
              "processes: mean MASE over $h = 1, \\dots, 12$.", "tab:si-rcheck", "llccccccc",
              "Process & $n$ & R ARIMA & SF ARIMA & R ETS & SF ETS & R Theta & SF Theta & R seas.\\ (\\%)",
              rows, "The same 200 series per row. R: \\code{auto.arima}, \\code{ets} and \\code{thetaf} of "
              "\\pkg{forecast} 9.0.2 at their defaults, with frequency 12; SF: \\pkg{StatsForecast} 2.1.1 as in "
              "the main text. R seas.: share of series given a seasonal form by \\code{auto.arima} / \\code{ets}. "
              "No R fit failed. On D4 at $n = 96$ \\pkg{StatsForecast}'s AutoETS settles on a near-zero seasonal "
              "smoothing parameter with a much lower likelihood than R's fit of the same form.",
              size="\\footnotesize")
    return t1 + "\n\\input{tab_extended}\n\n" + t2 + "\n" + t3 + "\n" + t4


def further():
    """Section S8: count benchmarks on D8, post-cutoff FRED-MD tier, simultaneous intervals."""
    r3 = ROOT / "results" / "round3"
    c = pd.read_csv(r3 / "d8_count_benchmarks.csv")
    d8 = pd.read_csv(ROOT / "results" / "revision" / "d8_table.csv")
    hb = pd.read_csv(ROOT / "results" / "round2" / "d8_benchmarks.csv")
    lab = {"iETS": "iETS", "NegBin": "Negative binomial", "TSBcomp": "TSB compound"}
    rows = []
    for m in ["iETS", "NegBin", "TSBcomp"]:
        g = c[c.method == m].set_index("n")
        rows.append(f"{lab[m]} & " + " & ".join(f"{g.loc[n, 'SPL']:.3f}" for n in (24, 48, 96, 200)) + " & "
                    + " & ".join(f"{g.loc[n, 'RMSSE']:.3f}" for n in (24, 48, 96, 200)))
    h = hb[hb.method == "EmpiricalMedian"].set_index("n")["SPL"]
    hm = hb[hb.method == "ContextMean"].set_index("n")["RMSSE"]
    rows.append("History: deciles; mean & " + " & ".join(f"{h[n]:.3f}" for n in (24, 48, 96, 200)) + " & "
                + " & ".join(f"{hm[n]:.3f}" for n in (24, 48, 96, 200)))
    t = d8[d8.method == "TimesFM3"].set_index("n")
    tm = d8[d8.method == "TimesFM3mean"].set_index("n")
    rows.append("TimesFM-3 (mean of deciles) & " + " & ".join(f"{t.loc[n, 'SPL']:.3f}" for n in (24, 48, 96, 200))
                + " & " + " & ".join(f"{tm.loc[n, 'RMSSE']:.3f}" for n in (24, 48, 96, 200)))
    t15 = _tab("Count-data benchmarks on the intermittent process D8.", "tab:si-count", "lcccccccc",
               "& \\multicolumn{4}{c}{Scaled pinball loss} & \\multicolumn{4}{c}{RMSSE of the mean} \\\\\n"
               "Method & 24 & 48 & 96 & 200 & 24 & 48 & 96 & 200", rows,
               "200 replications per length (iETS failed on 3 series at $n = 24$). iETS: "
               "\\code{smooth::adam(y, \"MNN\", occurrence = \"auto\")} with simulated quantiles; negative "
               "binomial fitted by maximum likelihood to the context; TSB compound: TSB occurrence probability "
               "($\\alpha = 0.2$) times the empirical distribution of the non-zero sizes. Point forecasts are the "
               "predictive means.", size="\\footnotesize")
    s = pd.read_csv(ROOT / "results" / "post_cutoff" / "summary.csv")
    s = s[s.method != "Naive"].sort_values("mean_MASE")
    nm = {"TimesFM3": "TimesFM-3", "TimesFM25": "TimesFM-2.5", "ChronosBolt": "Chronos-Bolt",
          "Chronos2": "Chronos-2", "SeasonalNaive": "Seasonal naive"}
    rows = [f"{nm.get(r.method, r.method)} & {r.mean_MASE:.3f} & {r.median_MASE:.3f} & {r.mean_MASE_late:.3f} & "
            f"{r.cover80:.3f} & {r.SPL:.3f}" for r in s.itertuples()]
    t16 = _tab("Data observed after the documented training corpora: 101 FRED-MD series, January 2025 to June 2026.",
               "tab:si-postcutoff", "lccccc",
               "Method & Mean MASE & Median MASE & Mean MASE, 2025-11 on & Coverage 80\\% & SPL", rows,
               "FRED-MD, August 2026 vintage, raw levels; context January 2005 to December 2024, horizon 18. "
               "MASE scaled by the in-sample seasonal-naive error ($m = 12$). The later window (November 2025 "
               "to June 2026) post-dates the release of every model evaluated.")
    sc = pd.read_csv(r3 / "simultaneous_ci.csv")
    rows = []
    onm = {"AutoARIMA": "AutoARIMA", "SeasonalNaive": "Seasonal naive", "Theta": "Theta", "AutoETS": "AutoETS",
           "Combination": "Combination"}
    for o, g in sc.groupby("opponent", sort=False):
        rows.append(f"{onm.get(o, o)} & {int((g.sim_hi < 0).sum())} & {int((g.sim_lo > 0).sum())} & "
                    f"{int((g.pct_hi < 0).sum())} & {int((g.pct_lo > 0).sum())}")
    t17 = _tab("Scenarios in which TimesFM-3 is separated from each opponent: simultaneous against per-scenario "
               "intervals.", "tab:si-simult", "lcccc",
               "& \\multicolumn{2}{c}{Simultaneous (max-$t$)} & \\multicolumn{2}{c}{Per scenario} \\\\\n"
               "Opponent & TimesFM-3 better & Opponent better & TimesFM-3 better & Opponent better", rows,
               "Median paired $\\log_2$ ratio of MASE over $h = 1, \\dots, 12$ in each of the 36 scenarios; 95\\% "
               "intervals from 2\\,000 bootstrap resamples of the replications, simultaneous over the 36 "
               "scenarios (studentised maximum) or per scenario (percentile).")
    return t15 + "\n" + t16 + "\n" + t17


def horizon48():
    """Section S7: the H = 48 check (N9_horizon48.py, B10_figure_h48.py)."""
    s = pd.read_csv(ROOT / "results" / "h48" / "summary.csv")
    c = pd.read_csv(ROOT / "results" / "h48" / "cell_means.csv")
    blocks = ["h1_12", "h13_24", "h25_48"]
    rows = []
    for m in ["TimesFM3", "TimesFM25", "Chronos2", "AutoARIMA", "AutoETS", "Theta", "Combination",
              "SeasonalNaive"]:
        wx = []
        for b in blocks:
            w = c[(c.block == b) & (c.dgp != "D7")].pivot_table(index=["dgp", "n"], columns="method",
                                                                 values="MASE")
            wx.append(w.div(w.min(axis=1), axis=0)[m].max())
        cv = s[s.method == m].set_index("block").cover80
        d7 = c[(c.block == "h1_48") & (c.dgp == "D7") & (c.n == 200) & (c.method == m)].MASE.iloc[0]
        nm = {"TimesFM25": "TimesFM-2.5", "Chronos2": "Chronos-2"}.get(m, NAMES.get(m, m))
        rows.append(f"{nm} & " + " & ".join(f"{v:.2f}" for v in wx) + " & "
                    + " & ".join(f"{cv[b]:.3f}" for b in blocks) + f" & {d7:.2f}")
    return _tab("Longer horizon ($H = 48$): worst ratio to the cell-best and 80\\% coverage by block of steps.",
                "tab:si-h48", "lccccccc",
                "Method & \\multicolumn{3}{c}{Worst ratio, D7 excluded} & \\multicolumn{3}{c}{Coverage 80\\%} & "
                "D7, $n = 200$ \\\\\n & 1--12 & 13--24 & 25--48 & 1--12 & 13--24 & 25--48 & MASE 1--48",
                rows, "The nine processes regenerated with the same seeds at length $n + 48$, 200 replications "
                "per cell; ratios to the best of the eight methods in each of the 32 (process, length) cells "
                "without D7. Coverage is averaged over all 36 cells. The last column is the mean MASE over the "
                "48 steps on D7 at $n = 200$, where the process has reached its plateau before the forecast "
                "origin.")


def main():
    si = (D / "supporting_information.tex").read_text(encoding="utf-8")
    head = si[:si.index("\\maketitle") + len("\\maketitle")]
    head = head.replace("Section S1 onwards.", "Sections S1 to S8.")
    for k in (5, 6, 7):
        head = head.replace(f"Sections S1 to S{k}.", "Sections S1 to S8.")
    if "\\providecommand{\\pkg}" not in head:
        head = head.replace("\\providecommand{\\tableref}",
                            "\\providecommand{\\pkg}[1]{\\textsf{#1}}\n\\providecommand{\\proglang}[1]{\\textsf{#1}}\n"
                            "\\providecommand{\\code}[1]{\\texttt{#1}}\n\\providecommand{\\tableref}", 1)
    if "\\graphicspath" not in head:
        head = head.replace("\\usepackage{xurl}", "\\usepackage{xurl}\n\\graphicspath{{images/}{./images/}}")
    ajs = SRC_AJS.read_text(encoding="utf-8")
    app = ajs[ajs.index("\n\\appendix\n") + len("\n\\appendix\n"):ajs.index("\\end{document}")]
    app = app.replace("\\label{app:mape}", "\\label{si:mape}")
    app = app.replace("and the process on which TimesFM-3 achieves its largest\nand most consistent advantage "
                      "simply drops out of the comparison.",
                      "and the process on which the error measures disagree most drops out of the comparison.")
    (D / "si_response.tex").write_text(response_table(), encoding="utf-8")
    RANGES = RANGES_TEX
    DIAG = diagnostics()
    H48 = horizon48()
    FURTHER = further()
    body = f"""
{app.strip()}

\\section{{Monte Carlo standard errors}}
\\label{{si:mcse}}

\\tableref{{tab:si-mcse}} gives the mean MASE of the six methods of the main design in every cell,
with its Monte Carlo standard error.

\\input{{si_mcse}}

\\section{{Coverage by process}}
\\label{{si:coverage}}

\\tableref{{tab:si-coverage}} gives the empirical coverage of the nominal 80\\% intervals of the four
foundation-model configurations and of AutoARIMA and AutoETS, by process.

\\input{{si_coverage}}

\\section{{Response-surface regressions}}
\\label{{si:response}}

Tables~\\ref{{tab:si-response}} and~\\ref{{tab:si-response2}} report the regressions summarised in the section of the main text on
randomised parameters and departures from the assumptions.

\\input{{si_response}}

\\section{{Intermittent demand, parameter ranges and horizons}}
\\label{{si:additional}}

\\tableref{{tab:d8metrics}} gives the error measures of the six pre-registered methods on the
intermittent process D8, and \\tableref{{tab:croston}} compares TimesFM-3 with six Croston-family methods.
\\tableref{{tab:ranges}} lists the parameter ranges of the randomised design, Figure~S1 shows accuracy by
forecast horizon, and Figure~S2 shows how the relative accuracy of TimesFM-3 and AutoARIMA varies with the
drawn parameters.

\\input{{tab_d8metrics}}

\\input{{tab_croston}}

{RANGES}

\\begin{{figure}}[!htbp]
\\centering
\\includegraphics[width=\\textwidth]{{../figures/fig4_horizon.pdf}}
\\caption{{Mean MASE by forecast horizon, averaged within each regime. Left: D1--D5, for which a classical
family is correctly specified. Right: D6--D9, for which none is, or only in the conditional mean (D9).}}
\\label{{fig:si-horizon}}
\\end{{figure}}

\\begin{{figure}}[!htbp]
\\centering
\\includegraphics[width=\\textwidth]{{../figures/fig12_parameter_response.pdf}}
\\caption{{Median $\\log_2$ ratio of the MASE of TimesFM-3 to that of AutoARIMA, by quintile of the drawn
parameter, randomised-parameter design with Gaussian innovations. Values below zero favour TimesFM-3. For D8
the ratio compares median-type forecasts and is shown for completeness only.}}
\\label{{fig:si-response}}
\\end{{figure}}

\\section{{Supplementary diagnostics}}
\\label{{si:diagnostics}}

\\tableref{{tab:si-worst}} summarises each method's ratio to the best method of a cell with and without the
two cells in which only two seasonal cycles are observed (D4 and D5 at $n = 24$), and \\tableref{{tab:extended}}
gives the robustness summaries of the fifteen methods of Figure~5 of the main text, with bootstrap intervals.
\\tableref{{tab:si-forms}}
lists the model forms chosen by AutoETS and AutoARIMA on the seasonal processes at $n = 24$ and $n = 48$,
and \\tableref{{tab:si-is}} gives the 80\\% interval score by process. Pooling all 180 tests of the
$h = 1$--12 slice into one Benjamini--Hochberg family gives 134 significant comparisons, 115 won by
TimesFM-3 (13--9 against AutoARIMA); pooling all 540 tests gives 132 and 113 (12--9), against 132 and 113
(11--9) with the pre-registered families.

{DIAG}

\\section{{A longer horizon}}
\\label{{si:h48}}

The main design forecasts 12 steps. To see whether its conclusions depend on that choice, the nine
processes were regenerated with the same seeds at length $n + 48$ and forecast 48 steps ahead by the six
pre-registered methods, TimesFM-2.5 and Chronos-2 (post hoc). Because the inflection of D7 sits at
$0.6(n + H)$, the longer horizon moves it into the context for $n = 200$: the series has reached its plateau
before the forecast origin. \\tableref{{tab:si-h48}} and Figure~S3 summarise the results.

{H48}

\\begin{{figure}}[!htbp]
\\centering
\\includegraphics[width=\\textwidth]{{../figures/fig_si_h48.pdf}}
\\caption{{Longer horizon ($H = 48$). (a) Worst ratio to the cell-best method by block of forecast steps, D7
excluded. (b) Mean coverage of the nominal 80\\% intervals by block; the dashed line is the nominal level.
(c) D7 at $n = 200$: mean of the 200 series (black) and mean point forecasts over the 48 steps.}}
\\label{{fig:si-h48}}
\\end{{figure}}

\\section{{Further checks}}
\\label{{si:further}}

\\tableref{{tab:si-count}} compares count-data benchmarks with the history benchmark and TimesFM-3 on the
intermittent process, \\tableref{{tab:si-postcutoff}} reports the tier of data observed after the documented
training corpora, and \\tableref{{tab:si-simult}} counts the scenarios separated by simultaneous and by
per-scenario intervals.

{FURTHER}

\\end{{document}}
"""
    # USG.cls cannot place floats on the title page: start the body on a new page.
    (D / "supporting_information.tex").write_text(head + "\n\\clearpage\n" + body, encoding="utf-8")
    print("supporting_information.tex rebuilt")


if __name__ == "__main__":
    main()
