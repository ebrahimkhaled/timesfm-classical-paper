"""Figure for the longer-horizon check (N9, H = 48): Supporting Information Figure S3.

(a) worst ratio to the cell-best by horizon block, D7 excluded; (b) mean 80% coverage by block;
(c) D7 at n = 200: mean of the truth and of the point forecasts over the 48 steps.
"""

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
COL = {"SeasonalNaive": "#999999", "Theta": "#CC79A7", "AutoETS": "#E69F00", "AutoARIMA": "#009E73",
       "Combination": "#56B4E9", "TimesFM3": "#0072B2", "TimesFM25": "#D55E00", "Chronos2": "#8C564B"}
LAB = {"SeasonalNaive": "Seasonal naive", "TimesFM3": "TimesFM-3", "TimesFM25": "TimesFM-2.5",
       "Chronos2": "Chronos-2"}
BLOCKS = ["h1_12", "h13_24", "h25_48"]
XL = ["1-12", "13-24", "25-48"]


def main():
    c = pd.read_csv(ROOT / "results" / "h48" / "cell_means.csv")
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    worst = {}
    for b in BLOCKS:
        w = c[(c.block == b) & (c.dgp != "D7")].pivot_table(index=["dgp", "n"], columns="method", values="MASE")
        worst[b] = w.div(w.min(axis=1), axis=0).max()
    worst = pd.DataFrame(worst)
    cov = c.pivot_table(index="method", columns="block", values="cover80")[BLOCKS]
    for m in COL:
        kw = dict(color=COL[m], marker="o", ms=3, lw=1.8 if m == "TimesFM3" else 1, label=LAB.get(m, m))
        ax[0].plot(XL, worst.loc[m, BLOCKS], **kw)
        ax[1].plot(XL, cov.loc[m], **kw)
    ax[0].set_yscale("log")
    ax[0].set_yticks([1, 1.5, 2, 3, 5])
    ax[0].set_yticklabels(["1", "1.5", "2", "3", "5"])
    ax[0].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[0].set_ylabel("worst ratio to scenario-best (D7 excluded)")
    ax[1].axhline(0.8, color="0.3", ls="--", lw=0.8)
    ax[1].set_ylabel("mean 80% coverage")
    for a in ax[:2]:
        a.set_xlabel("forecast steps")

    spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
    dgp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dgp)
    s = np.array([dgp.simulate("D7", 200, r, 48) for r in range(200)])
    fc = ROOT / "results" / "h48" / "forecasts"
    cl = np.load(fc / "classical_D7_n200_r200.npz")
    tf = np.load(fc / "timesfm_D7_n200_r200.npz")
    fm = np.load(fc / "fm_D7_n200_r200.npz")
    t = np.arange(150, 248)
    ax[2].plot(t, s[:, 150:].mean(axis=0), color="black", lw=1.6, label="truth (mean)")
    steps = np.arange(200, 248)
    for m, z in (("AutoARIMA", cl), ("SeasonalNaive", cl), ("TimesFM3", tf), ("TimesFM25", fm), ("Chronos2", fm)):
        ax[2].plot(steps, z[f"{m}_pt"].mean(axis=0), color=COL[m], lw=1.8 if m == "TimesFM3" else 1)
    ax[2].axvline(199.5, color="0.5", ls=":", lw=0.8)
    ax[2].set_xlabel("time (context ends at 200)")
    ax[2].set_ylabel("level, D7 at n = 200")
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=8, fontsize=7, frameon=False)
    for a, tag in zip(ax, "abc"):
        a.set_title(f"({tag})", fontsize=9, loc="left")
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(ROOT / "figures" / "fig_si_h48.pdf")
    print(worst.round(2).to_string())
    print(cov.round(3).to_string())


if __name__ == "__main__":
    main()
