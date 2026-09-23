"""JoF revision: LaTeX tables for the extended evaluation, generated from the result CSVs.

Writes to manuscript_jof/:
  tab_extended.tex     robustness summaries of the twelve methods, with bootstrap intervals
  tab_d8ext.tex        intermittent demand re-examined: zero forecast, bias, PIS, pinball loss
  tab_m4official.tex   M4 official test period: sMAPE, MASE, OWA, coverage, MSIS, MCB rank
  tab_truncation.tex   M4 with truncated contexts
Supporting information (manuscript_jof/si_*.tex):
  si_mcse.tex          mean MASE with Monte Carlo SE, original six methods, all cells
  si_coverage.tex      80% coverage per process for the foundation models and AutoARIMA/AutoETS,
                       Gaussian versus conformal intervals
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REV = ROOT / "results" / "revision"
M4 = ROOT / "results" / "m4_official"
OUT = ROOT / "manuscript_jof"
LABEL = {"SeasonalNaive": "Seasonal naive", "Theta": "Theta", "DOTM": "DOTM", "AutoETS": "AutoETS",
         "AutoARIMA": "AutoARIMA", "Combination": "Combination (Theta, ETS, ARIMA)",
         "CombEAD": "Combination (ETS, ARIMA, DOTM)", "M4Comb": "M4 Comb", "TimesFM3": "TimesFM-3",
         "TimesFM3eval": "TimesFM-3, evaluator settings", "TimesFM25": "TimesFM-2.5",
         "ChronosBolt": "Chronos-Bolt", "Naive2": "Naive2", "Zero": "All-zero forecast",
         "TimesFM3mean": "TimesFM-3, mean of deciles", "CrostonSBA": "Croston--SBA", "ADIDA": "ADIDA",
         "TSB": "TSB", "Chronos2": "Chronos-2", "TiRex": "TiRex", "TimesFM25raw": "TimesFM-2.5, settings off", "History": "History: mean; empirical deciles", "IMAPA": "IMAPA", "CrostonClassic": "Croston", "CrostonOptimized": "Croston (opt.)"}


def table(caption, label, head, rows, note, spec):
    L = ["\\begin{table}[!htbp]", "\\centering", "\\begin{threeparttable}",
         f"\\caption{{{caption}}}", f"\\label{{{label}}}", "\\small\\setlength{\\tabcolsep}{4pt}",
         f"\\begin{{tabular}}{{{spec}}}", "\\toprule", head + " \\\\", "\\midrule"]
    L += [r + " \\\\" for r in rows]
    L += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}[flushleft]\\footnotesize",
          f"\\item \\textit{{Note:}} {note}", "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    return "\n".join(L) + "\n"


def ci(v, lo, hi, d=2):
    return f"{v:.{d}f} [{lo:.{d}f}, {hi:.{d}f}]"


def extended():
    rc = pd.read_csv(REV / "robustness_ci.csv")
    ex = rc[rc.set == "extended fifteen"].sort_values("meanlog")
    rows = []
    for _, r in ex.iterrows():
        rows.append(f"{LABEL.get(r.method, r.method)} & {ci(r.worst, r.worst_lo, r.worst_hi)} & "
                    f"{ci(r.meanlog, r.meanlog_lo, r.meanlog_hi, 3)} & {100 * r.within10:.0f} & "
                    f"{int(r.wins)} [{int(r.wins_lo)}, {int(np.ceil(r.wins_hi))}]")
    o = rc[rc.set == "original six"].set_index("method")
    note = ("Main design, 7\\,200 series, mean MASE over $h = 1, \\dots, 12$, ratios to the best of "
            "the fifteen methods in each of the 36 (process, length) cells. Brackets: 95\\% intervals "
            "from 500 bootstrap resamples of the replications within each cell. Mean ratio is the "
            "geometric mean over cells. Intervals for the original six methods from 2\\,000 paired "
            "resamples are given in Section~5.1 of the main text. "
            "Cells won: the two TimesFM-3 configurations split the cells they win (among the original six "
            "methods TimesFM-3 wins 16), and ratios can differ slightly from Table~3 of the main text because the "
            "best method of a cell is taken over fifteen methods (seasonal naive: 5.70 against 5.65).")
    (OUT / "tab_extended.tex").write_text(table(
        "Robustness of fifteen methods across the 36 cells of the main design.", "tab:extended",
        "Method & Worst ratio to best & Mean ratio to best & Within 10\\% (\\%) & Cells won",
        rows, note, "lcccc"), encoding="utf-8")


def d8():
    t = pd.read_csv(REV / "d8_table.csv")
    # Second review round: the history's mean as point forecast and its empirical deciles as the
    # predictive distribution (L1_round2_analyses.py), merged into one row.
    hb = pd.read_csv(ROOT / "results" / "round2" / "d8_benchmarks.csv")
    hm = hb[hb.method == "ContextMean"].drop(columns="SPL").set_index("n")
    hm["SPL"] = hb[hb.method == "EmpiricalMedian"].set_index("n")["SPL"]
    hm = hm.reset_index().assign(method="History")
    t = pd.concat([t, hm], ignore_index=True)
    meths = ["Zero", "History", "TimesFM3", "TimesFM3mean", "TimesFM25", "ChronosBolt", "Chronos2", "TiRex", "CrostonSBA",
             "ADIDA", "TSB", "AutoARIMA"]
    rows = []
    for m in meths:
        g = t[t.method == m].set_index("n")
        def rng(col, d=3):
            v = g[col].dropna()
            if v.empty:
                return "--"
            a, b = round(v.min(), d) + 0.0, round(v.max(), d) + 0.0  # + 0.0 turns -0.0 into 0.0
            if a < 0:  # "--" between negative numbers reads as a dash with a lost minus sign
                return f"${a:.{d}f}$ to ${b:.{d}f}$".replace("$-", "$-")
            return f"{a:.{d}f}--{b:.{d}f}"
        rows.append(f"{LABEL[m]} & {rng('MASE')} & {rng('RMSSE')} & {rng('sME', 2)} & "
                    f"{rng('sPIS', 0)} & {rng('SPL')}")
    note = ("Process D8, 200 replications per length; ranges over the four lengths $n \\in \\{24, 48, "
            "96, 200\\}$. sME: mean error (forecast minus actual) scaled by the MASE denominator; "
            "negative values mean under-forecasting. sPIS: periods in stock \\citep{wallstrom2010pis}, "
            "cumulated over the horizon and scaled by the mean demand of the context; large negative "
            "values mean persistent stock-outs. SPL: scaled pinball loss over the nine deciles, "
            "defined only for methods with a predictive distribution. TimesFM-3, mean of deciles, "
            "uses the average of its nine deciles as point forecast. History: the mean of the context as point "
            "forecast and the empirical deciles of the context as predictive distribution; the median of the "
            "context is zero or near it, so its point forecast would repeat the all-zero row.")
    (OUT / "tab_d8ext.tex").write_text(table(
        "Intermittent demand (D8) re-examined with simple benchmarks, bias and stock measures.",
        "tab:d8ext", "Method & MASE & RMSSE & sME & sPIS & SPL", rows, note, "lccccc"),
        encoding="utf-8")


def m4():
    s = pd.read_csv(M4 / "summary.csv").set_index("method")
    mcb = pd.read_csv(M4 / "mcb.csv").set_index("method")
    test = pd.read_csv(M4 / "mcb_test.csv").iloc[0]
    # Published M4 submissions (L3_m4_published.py); the official Theta and Comb files duplicate the
    # paper's own Theta and M4 Comb and are left out of the table.
    s = s.drop(index=[m for m in ("M4Theta", "M4CombPub") if m in s.index])
    pub = {"FFORMA": "FFORMA (M4, 2nd)", "Smyl": "ES-RNN, Smyl (M4, 1st)",
           "Pawlikowski": "Pawlikowski et al.\\ (M4, 3rd)", "Jaganathan": "Jaganathan \\& Prakash (M4, 4th)",
           "Fiorucci": "Fiorucci \\& Louzada (M4, 5th)", "Petropoulos": "Petropoulos \\& Svetunkov (M4, 6th)",
           "Shaub": "Shaub (M4, 7th)", "Legaki": "Legaki \\& Koutsouri (M4, 8th)",
           "Doornik": "Doornik et al.\\ (M4, 9th)", "Pedregal": "Pedregal et al.\\ (M4, 10th)"}
    LABEL.update(pub)
    rows = []
    for m, r in s.sort_values("OWA").iterrows():
        cov = "--" if pd.isna(r.cover80) else f"{r.cover80:.3f}"
        msis = "--" if pd.isna(r.MSIS80) else f"{r.MSIS80:.2f}"
        if m in mcb.index:
            tie = "" if mcb.loc[m, "differs_from_best"] else "$^\\ast$"
            rank = f"{mcb.loc[m, 'mean_rank']:.2f}{tie}"
        else:
            rank = "--"
        rows.append(f"{LABEL.get(m, m)} & {r.sMAPE:.2f} & {r.MASE:.3f} & {r.OWA:.3f} & {cov} & {msis} & {rank}")
    note = ("1\\,000 M4 Monthly series, each forecast for the official 18-month test period from its "
            "full training history. sMAPE and MASE as defined in M4; OWA relative to the official "
            "Naive2 forecasts. Coverage and MSIS use the nominal 80\\% interval, the widest that every "
            "probabilistic method can form from nine deciles. Mean rank: average rank of per-series "
            f"MASE among {int(test.k)} methods, one configuration per model (Friedman $\\chi^2 = {test.friedman_chi2:.0f}$, "
            f"$p < 10^{{-100}}$); $^\\ast$ marks methods whose mean rank is within the Nemenyi critical "
            f"difference ({test.cd:.2f}) of the best; -- marks alternative configurations and Naive2, left out "
            "of the ranking. Published M4 submissions, ranked by their overall M4 position, provide point forecasts only "
            "\\citep{makridakis2020m4, smyl2020hybrid, monteromanso2020fforma}.")
    (OUT / "tab_m4official.tex").write_text(table(
        "M4 Monthly official test period: accuracy, OWA and multiple comparisons.", "tab:m4official",
        "Method & sMAPE & MASE & OWA & Coverage & MSIS & Mean rank", rows, note, "lcccccc"),
        encoding="utf-8")

    tr = pd.read_csv(M4 / "truncation.csv").pivot(index="method", columns="context", values="mean")
    meths = ["TimesFM3", "TimesFM3eval", "TimesFM25", "ChronosBolt", "Chronos2", "TiRex", "AutoARIMA", "AutoETS", "Theta",
             "DOTM", "Combination", "CombEAD", "SeasonalNaive"]
    rows = [f"{LABEL[m]} & {tr.loc[m, 'last24']:.3f} & {tr.loc[m, 'last48']:.3f} & "
            f"{tr.loc[m, 'last96']:.3f} & {tr.loc[m, 'full']:.3f}" for m in meths]
    note = ("Mean MASE on the M4 official test period when each method sees only the last 24, 48 or "
            "96 training observations, or the full history (median 281 observations). All columns "
            "use the full-history MASE denominator, so only the information given to the methods "
            "changes. Seasonal naive uses only the last 12 observations and is unaffected.")
    (OUT / "tab_truncation.tex").write_text(table(
        "M4 Monthly with truncated contexts: mean MASE by context length.", "tab:truncation",
        "Method & Last 24 & Last 48 & Last 96 & Full", rows, note, "lcccc"), encoding="utf-8")


def si():
    cm = pd.read_csv(REV / "cell_means.csv")
    orig = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]
    rows = []
    for (d, n), g in cm[cm.method.isin(orig)].groupby(["dgp", "n"]):
        g = g.set_index("method")
        rows.append(f"{d} & {n} & " + " & ".join(f"{g.loc[m,'mean']:.3f} ({g.loc[m,'mcse']:.3f})"
                                                    for m in orig))
    note = ("Mean MASE over $h = 1, \\dots, 12$ with its Monte Carlo standard error in parentheses "
            "(standard deviation over the 200 replications divided by $\\sqrt{200}$).")
    # 36 rows: set small enough to fit one page of the USG layout
    (OUT / "si_mcse.tex").write_text(table(
        "Mean MASE and Monte Carlo standard errors, main design.", "tab:si-mcse",
        "DGP & $n$ & " + " & ".join(LABEL[m].split(" (")[0] for m in orig), rows, note,
        "ll" + "c" * 6).replace("\\small\\setlength{\\tabcolsep}{4pt}",
                                "\\scriptsize\\setlength{\\tabcolsep}{3pt}"
                                "\\renewcommand{\\arraystretch}{0.9}"), encoding="utf-8")

    cov = pd.read_csv(REV / "coverage.csv")
    meths = ["TimesFM3", "TimesFM3eval", "TimesFM25", "ChronosBolt", "AutoARIMA", "AutoETS"]
    rows = []
    for d in [f"D{i}" for i in range(1, 10)]:
        vals = []
        for m in meths:
            r = cov[(cov.method == m) & (cov.dgp == d)]
            vals.append(f"{r.cover80.iloc[0]:.3f}" if len(r) else "--")
        rows.append(f"{d} & " + " & ".join(vals))
    mc = cov[cov.dgp != "all"].mcse.max()
    note = ("Empirical coverage of the nominal 80\\% interval $[q_{0.1}, q_{0.9}]$, averaged over "
            f"lengths and replications; series-cluster bootstrap Monte Carlo SE at most {mc:.3f}.")
    (OUT / "si_coverage.tex").write_text(table(
        "Coverage of 80\\% prediction intervals by process.", "tab:si-coverage",
        "Process & " + " & ".join(LABEL[m].replace(", evaluator settings", " (eval.)") for m in meths),
        rows, note, "l" + "c" * 6), encoding="utf-8")

    gc = pd.read_csv(REV / "coverage_gaussian_vs_conformal.csv", index_col=0)
    name = {"AutoARIMA": "AutoARIMA, Gaussian", "AutoARIMA_cf": "AutoARIMA, conformal",
            "AutoETS": "AutoETS, Gaussian", "AutoETS_cf": "AutoETS, conformal"}
    rows = [f"{name[m]} & " + " & ".join(f"{gc.loc[m, d]:.3f}" for d in gc.columns)
            for m in ("AutoARIMA", "AutoARIMA_cf", "AutoETS", "AutoETS_cf")]
    note = ("Empirical coverage of the nominal 80\\% interval at $n \\in \\{96, 200\\}$. Conformal: "
            "split-conformal intervals with two 12-step calibration windows (statsforecast "
            "\\texttt{ConformalIntervals}); Gaussian: the models' analytic intervals.")
    (OUT / "si_conformal.tex").write_text(table(
        "Gaussian versus split-conformal 80\\% intervals for AutoARIMA and AutoETS.",
        "tab:si-conformal", "Interval & " + " & ".join(gc.columns), rows, note,
        "l" + "c" * len(gc.columns)), encoding="utf-8")


if __name__ == "__main__":
    extended()
    d8()
    m4()
    si()
    print("tables written")
