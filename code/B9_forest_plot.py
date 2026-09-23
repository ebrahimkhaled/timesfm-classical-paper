"""Forest plot of the pre-registered pairwise comparisons (second referee round, R2-M2).

For every (process, length) cell and each classical opponent: the median of the paired per-series ratios
MASE(TimesFM-3) / MASE(opponent) over h = 1..12, with a 95% percentile bootstrap interval (2,000
resamples of the 200 replications). Filled markers: significant after Benjamini-Hochberg in the
pre-registered family (results/table_tests.csv, h = 1..12 slice); hollow: not significant.

Outputs: figures/fig5_forest.pdf, results/round2/forest.csv
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RNG = np.random.default_rng(20260925)
LIM = (-1.6, 1.0)
OPP = ["AutoARIMA", "Combination", "SeasonalNaive", "AutoETS", "Theta"]
LAB = {"AutoARIMA": "AutoARIMA", "Combination": "Combination", "SeasonalNaive": "Seasonal naive",
       "AutoETS": "AutoETS", "Theta": "Theta"}
DGPS = [f"D{i}" for i in range(1, 10)]
NS = [24, 48, 96, 200]


def compute():
    d = pd.read_csv(ROOT / "results" / "all_metrics.csv", usecols=["dgp", "n", "rep", "method", "horizon_slice", "MASE"])
    d = d[(d.horizon_slice == "h1_12") & d.method.isin(OPP + ["TimesFM3"])]
    w = d.pivot_table(index=["dgp", "n", "rep"], columns="method", values="MASE")
    t = pd.read_csv(ROOT / "results" / "table_tests.csv")
    t = t[t.horizon_slice == "h1_12"].set_index(["dgp", "n", "opponent"])
    rows = []
    for (g, n), cell in w.groupby(level=["dgp", "n"]):
        for o in OPP:
            x = (cell["TimesFM3"] / cell[o]).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
            x = np.log2(x[x > 0])
            b = np.array([np.median(x[RNG.integers(0, len(x), len(x))]) for _ in range(2000)])
            rows.append({"dgp": g, "n": n, "opponent": o, "log2_med": np.median(x),
                         "lo": np.quantile(b, .025), "hi": np.quantile(b, .975),
                         "significant": bool(t.loc[(g, n, o), "significant"])})
    f = pd.DataFrame(rows)
    f.to_csv(ROOT / "results" / "round2" / "forest.csv", index=False)
    return f


def plot(f):
    order = [(g, n) for g in DGPS for n in NS]
    y = {c: i + DGPS.index(c[0]) * 0.8 for i, c in enumerate(order)}
    fig, axes = plt.subplots(1, len(OPP), figsize=(10, 8.4), sharey=True)
    for ax, o in zip(axes, OPP):
        g = f[f.opponent == o]
        for _, r in g.iterrows():
            yy = y[(r.dgp, r.n)]
            col = "#0072B2" if r.log2_med < 0 else "#D55E00"
            lo, hi, m = max(r.lo, LIM[0]), min(r.hi, LIM[1]), float(np.clip(r.log2_med, *LIM))
            ax.plot([lo, hi], [yy, yy], color=col, lw=1.1)
            if m != r.log2_med:   # off-scale: arrowhead at the edge
                ax.plot(m, yy, "<" if m < 0 else ">", ms=4, color=col)
            else:
                ax.plot(m, yy, "o", ms=3.6, color=col, mfc=col if r.significant else "white", mew=0.9)
        ax.axvline(0, color="0.3", lw=0.8)
        ax.set_title(f"vs {LAB[o]}", fontsize=9)
        ax.set_xlim(LIM[0] - 0.05, LIM[1] + 0.05)
        ax.set_xticks([-1.585, -1, -0.415, 0, 0.585, 1])
        ax.set_xticklabels(["1/3", "1/2", "3/4", "1", "1.5", "2"], fontsize=7)
        ax.grid(axis="x", color="0.9", lw=0.5)
        ax.tick_params(axis="y", length=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_yticks([y[c] for c in order])
    axes[0].set_yticklabels([f"{g}  {n}" if n == 24 else f"{n}" for g, n in order], fontsize=6.5)
    axes[0].invert_yaxis()
    fig.supxlabel("Median paired ratio of MASE, TimesFM-3 / opponent (log scale; left of 1 favours TimesFM-3; filled: significant)",
                  fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig5_forest.pdf")
    print("wrote figures/fig5_forest.pdf")


if __name__ == "__main__":
    f = compute()
    print(f.groupby("opponent").apply(lambda g: pd.Series({
        "sig_tfm": int((g.significant & (g.log2_med < 0)).sum()),
        "sig_opp": int((g.significant & (g.log2_med > 0)).sum()),
        "ci_excl_0": int(((g.hi < 0) | (g.lo > 0)).sum())})).to_string())
    plot(f)
