"""Robustness study, part 3: do the headline conclusions survive?

Reads results/robust/robust_metrics.csv (R2) and writes

  results/robust/robust_cells.csv        mean MASE / RMSSE per (variant, DGP, n, method)
  results/robust/robust_worst_ratio.csv  each method's worst ratio to the cell-best, per variant
  results/robust/robust_tests.csv        paired Wilcoxon TimesFM-3 vs each classical method, BH
  results/robust/robust_claims.csv       the five headline conclusions, checked per variant
  manuscript/tab_robust_design.tex       the table for the paper
  figures/fig12_parameter_response.pdf   log MASE ratio against the drawn parameters
"""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "robust"
GENERAL = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination"]
CROSTON = ["CrostonSBA", "TSB", "ADIDA"]
VARIANTS = ["clean", "heavy_tail", "outliers", "est_period"]
VLABEL = {"clean": "Random", "heavy_tail": "Heavy tails", "outliers": "Outliers",
          "est_period": "Est.\\ period"}


def bh(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(q, 1.0)
    return out


def main() -> None:
    df = pd.read_csv(RES / "robust_metrics.csv")
    gen = df[df.method.isin(GENERAL + ["TimesFM3"])]

    cells = (gen.groupby(["variant", "dgp", "n", "method"])[["MASE", "RMSSE"]].mean()
             .reset_index())
    cells.to_csv(RES / "robust_cells.csv", index=False)
    wide = cells.pivot_table(index=["variant", "dgp", "n"], columns="method", values="MASE")
    best = wide.min(axis=1)
    ratio = wide.div(best, axis=0)
    worst = ratio.groupby(level="variant").max()
    wins = wide.idxmin(axis=1).groupby(level="variant").value_counts().unstack(fill_value=0)
    median_ratio = ratio.groupby(level="variant").median()
    worst.to_csv(RES / "robust_worst_ratio.csv")
    print("worst ratio to cell-best:\n", worst.round(2))
    print("median ratio:\n", median_ratio.round(3))
    print("cell wins:\n", wins)

    # Paired tests, TimesFM-3 against each general-purpose classical method.
    rows = []
    for (v, d, n), g in gen.groupby(["variant", "dgp", "n"]):
        piv = g.pivot_table(index="rep", columns="method", values="MASE")
        for mth in GENERAL:
            x = (piv["TimesFM3"] - piv[mth]).dropna()
            p = wilcoxon(x).pvalue if np.any(x != 0) else 1.0
            w = (x.to_numpy()[:, None] + x.to_numpy()[None, :]) / 2
            rows.append({"variant": v, "dgp": d, "n": n, "method": mth, "p": p,
                         "median_diff": float(np.median(x)),
                         "hodges_lehmann": float(np.median(w[np.triu_indices(len(x))])),
                         "median_ratio": float(np.median((piv["TimesFM3"] / piv[mth]).dropna()))})
    tests = pd.DataFrame(rows)
    # BH within each (variant, opponent) family of 36 cells -- the same family definition as the
    # main study (one family per opponent), so the tallies are comparable across the two designs.
    tests["q"] = tests.groupby(["variant", "method"])["p"].transform(bh)
    tests["tfm_wins"] = (tests.q < 0.05) & (tests.median_diff < 0)
    tests["tfm_loses"] = (tests.q < 0.05) & (tests.median_diff > 0)
    tests.to_csv(RES / "robust_tests.csv", index=False)
    tally = tests.groupby("variant")[["tfm_wins", "tfm_loses"]].sum()
    tally_m = tests.groupby(["variant", "method"])[["tfm_wins", "tfm_loses"]].sum()
    print(tally)
    print(tally_m)

    # The headline conclusions, checked in each variant.
    claims = []
    for v in VARIANTS:
        w = wide.loc[v]
        r = ratio.loc[v]
        c1 = bool(worst.loc[v, "TimesFM3"] < worst.loc[v, GENERAL].min())
        d4 = w.loc["D4"].loc[[48, 96, 200]]
        c2 = int((d4["AutoARIMA"] < d4["TimesFM3"]).sum())
        c2_gain = float((1 - d4["AutoARIMA"] / d4["TimesFM3"]).median())
        d8 = df[(df.variant == v) & (df.dgp == "D8")]
        m8 = d8.groupby(["n", "method"])[["MASE", "RMSSE"]].mean().unstack()
        best_cro_mase = m8["MASE"][CROSTON].min(axis=1)
        best_cro_rmsse = m8["RMSSE"][CROSTON].min(axis=1)
        c3a = int((m8["MASE"]["TimesFM3"] < best_cro_mase).sum())
        c3b = int((m8["RMSSE"]["TimesFM3"] > best_cro_rmsse).sum())
        # Denominator: seasonal naive with the TRUE period (clean version). Under the estimated
        # period the classical methods, seasonal naive included, run with m = 1 at n = 24.
        sn_v = "clean" if v == "est_period" else v
        c4 = float(w.loc[("D5", 24), "AutoETS"] / wide.loc[(sn_v, "D5", 24), "SeasonalNaive"])
        t = tally.loc[v]
        claims.append({"variant": v,
                       "tfm_worst": float(worst.loc[v, "TimesFM3"]),
                       "classical_worst_min": float(worst.loc[v, GENERAL].min()),
                       "C1_robustness_holds": c1,
                       "C2_arima_wins_D4_cells_of3": c2, "C2_median_gain": c2_gain,
                       "C3a_tfm_beats_croston_mase_of4": c3a,
                       "C3b_croston_beats_tfm_rmsse_of4": c3b,
                       "C4_ets_over_snaive_D5_n24": c4,
                       "C5_tfm_sig_wins": int(t.tfm_wins), "C5_tfm_sig_losses": int(t.tfm_loses),
                       "tfm_cell_wins": int(wins.loc[v].get("TimesFM3", 0)),
                       "tfm_median_ratio": float(median_ratio.loc[v, "TimesFM3"])})
    cl = pd.DataFrame(claims)
    cl.to_csv(RES / "robust_claims.csv", index=False)
    print(cl.T)

    # LaTeX table.
    lines = [
        "\\begin{table}[!htbp]", "\\centering", "\\begin{threeparttable}",
        "\\caption{Headline conclusions under randomised parameters and departures from the "
        "assumptions.}",
        "\\label{tab:robust-design}", "\\small\\setlength{\\tabcolsep}{4pt}",
        "\\begin{tabular}{lcccc}", "\\toprule",
        " & " + " & ".join(VLABEL[v] for v in VARIANTS) + " \\\\", "\\midrule"]

    def row(label, vals):
        lines.append(label + " & " + " & ".join(vals) + " \\\\")

    row("TimesFM-3 cell wins (of 36)", [str(c["tfm_cell_wins"]) for c in claims])
    row("TimesFM-3 median ratio to cell-best", [f"{c['tfm_median_ratio']:.3f}" for c in claims])
    row("TimesFM-3 worst ratio to cell-best", [f"{c['tfm_worst']:.2f}" for c in claims])
    row("Smallest worst ratio, classical", [f"{c['classical_worst_min']:.2f}" for c in claims])
    row("Significant comparisons, won--lost",
        [f"{c['C5_tfm_sig_wins']}--{c['C5_tfm_sig_losses']}" for c in claims])
    row("D4, $n \\geq 48$: AutoARIMA better (of 3)",
        [str(c["C2_arima_wins_D4_cells_of3"]) for c in claims])
    row("D8: Croston better on RMSSE (of 4)",
        [str(c["C3b_croston_beats_tfm_rmsse_of4"]) for c in claims])
    row("D5, $n = 24$: AutoETS / seasonal naive ($m = 12$)",
        [f"{c['C4_ets_over_snaive_D5_n24']:.2f}" for c in claims])
    lines += ["\\bottomrule", "\\end{tabular}", "\\begin{tablenotes}[flushleft]\\footnotesize",
              "\\item \\textit{Note:} 200 replications per (process, length) cell, 7\\,200 series "
              "per column; every series draws its own parameters from the ranges in "
              "\\tableref{tab:ranges}. Ratios use mean MASE over $h = 1, \\dots, 12$. "
              "Significant comparisons are paired Wilcoxon tests of TimesFM-3 against each of "
              "the five general-purpose classical methods in each cell (180 per column), "
              "Benjamini--Hochberg at 0.05 within each (column, opponent) family of 36 cells, as in the main design. The D8 row compares TimesFM-3 "
              "with the best of Croston-SBA, TSB and ADIDA; the last row divides by seasonal naive with the true period in every column. In the estimated-period column the "
              "classical methods receive the period chosen by the M4 seasonality test; "
              "TimesFM-3's forecasts are those of the first column.",
              "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]
    (ROOT / "manuscript" / "tab_robust_design.tex").write_text("\n".join(lines) + "\n",
                                                                encoding="utf-8")

    # Response to the drawn parameters: log ratio TimesFM-3 / AutoARIMA per series.
    panels = [("D1", "par_phi", "D1: AR coefficient $\\phi$"),
              ("D6", "par_jump_sd", "D6: break size (noise s.d.)"),
              ("D7", "par_infl_pos", "D7: inflection (share of series)"),
              ("D8", "par_p", "D8: demand probability $p$"),
              ("D9", "par_b", "D9: GARCH $b$")]
    clean = df[df.variant == "clean"]
    fig, axes = plt.subplots(1, 5, figsize=(13, 3.2), sharey=True)
    colors = {24: "#9ecae1", 48: "#6baed6", 96: "#3182bd", 200: "#08519c"}
    for ax, (d, par, label) in zip(axes, panels):
        g = clean[clean.dgp == d].pivot_table(index=["n", "rep"], columns="method",
                                               values=["MASE", par], aggfunc="first")
        lr = np.log2(g["MASE"]["TimesFM3"] / g["MASE"]["AutoARIMA"])
        x = g[par]["TimesFM3"]
        for n in [24, 48, 96, 200]:
            xs, ys = x.loc[n].to_numpy(), lr.loc[n].to_numpy()
            bins = np.quantile(xs, np.linspace(0, 1, 6))
            idx = np.clip(np.digitize(xs, bins[1:-1]), 0, 4)
            mid = [np.median(xs[idx == k]) for k in range(5)]
            med = [np.median(ys[idx == k]) for k in range(5)]
            ax.plot(mid, med, marker="o", ms=3, color=colors[n], label=f"n = {n}")
        ax.axhline(0, color="0.4", lw=0.8, ls=":")
        ax.set_xlabel(label)
    axes[0].set_ylabel("median log$_2$ MASE ratio\nTimesFM-3 / AutoARIMA")
    axes[-1].legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig12_parameter_response.pdf")
    print("wrote table and figure")


if __name__ == "__main__":
    main()
