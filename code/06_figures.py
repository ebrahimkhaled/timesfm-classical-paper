"""P6: figures, as vector PDF.

AJS rule C2.graphics is explicit: use vector graphics (PDF); do not use PNG or JPEG, and do
not convert from PNG to PDF. Every figure here is written straight to PDF by the matplotlib
PDF backend, so the text stays selectable and the lines stay sharp at any zoom.

House style mirrors the project's _ek_theme.R: serif (Times) type, the Okabe-Ito
colour-blind-safe palette, no chart junk.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib
matplotlib.use("pdf")  # vector output only
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dgp)

# Okabe-Ito, matching the project's house palette.
COLOURS = {
    "SeasonalNaive": "#999999",
    "Theta":         "#CC79A7",
    "AutoETS":       "#E69F00",
    "AutoARIMA":     "#0072B2",
    "Combination":   "#238B45",
    "TimesFM3":      "#D55E00",
}
METHOD_ORDER = ["SeasonalNaive", "Theta", "AutoETS", "AutoARIMA", "Combination", "TimesFM3"]
PRETTY = {"TimesFM3": "TimesFM-3", "SeasonalNaive": "Seasonal naive",
          "AutoETS": "AutoETS", "AutoARIMA": "AutoARIMA", "Theta": "Theta",
          "Combination": "Combination"}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,  # embed TrueType so text stays selectable
})


def save(fig, name: str) -> None:
    path = FIG / f"{name}.pdf"
    fig.savefig(path)
    plt.close(fig)
    print(f"  wrote figures/{name}.pdf")


# ------------------------------------------------------------------ Figure 1
def fig_example_series() -> None:
    """One realisation of each DGP, so the reader can see what is being forecast."""
    fig, axes = plt.subplots(3, 3, figsize=(7.2, 5.4), sharex=False)
    for ax, d in zip(axes.ravel(), dgp.DGP_IDS):
        n, H = 96, dgp.HORIZON
        s = dgp.simulate(d, n, 0, H)
        ax.plot(np.arange(n), s[:n], color="#333333", lw=0.8)
        ax.plot(np.arange(n, n + H), s[n:], color=COLOURS["TimesFM3"], lw=1.1)
        ax.axvline(n - 0.5, color="#999999", lw=0.6, ls=":")
        ax.set_title(f"{d}: {dgp.DGP_LABELS[d]}", fontsize=8)
        ax.tick_params(labelsize=7)
    fig.suptitle("Figure 1: One realisation of each data-generating process "
                 "(n = 96; held-out horizon in colour)", fontsize=9, y=1.01)
    fig.tight_layout()
    save(fig, "fig1_example_series")


# ------------------------------------------------------------------ Figure 2
def fig_mase_ratio(dec: pd.DataFrame) -> None:
    """Log2 ratio of TimesFM-3's MASE to the best classical method's, per cell.

    Below the zero line, TimesFM-3 is more accurate; above it, the classical method is.
    """
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    lengths = sorted(dec.n.unique())
    width = 0.8 / len(lengths)
    shades = ["#9ecae1", "#6baed6", "#3182bd", "#08519c"]

    for j, n in enumerate(lengths):
        sub = dec[dec.n == n].sort_values("dgp")
        x = np.arange(len(sub)) + j * width - 0.4 + width / 2
        ax.bar(x, np.log2(sub.ratio_timesfm_over_best), width=width,
               color=shades[j % len(shades)], label=f"n = {n}", edgecolor="none")

    ax.axhline(0, color="#333333", lw=0.8)
    order = sorted(dec.dgp.unique())
    ax.set_xticks(np.arange(len(order)))
    ax.set_xticklabels([f"{d}\n{dgp.CORRECT_MODEL[d]}" for d in order], fontsize=7)
    ax.set_ylabel(r"$\log_2$(MASE TimesFM-3 / MASE best classical)")
    ax.set_xlabel("Data-generating process, and the family correctly specified for it")
    ax.legend(ncol=4, fontsize=8, loc="upper right")
    ax.text(0.005, 0.03, "below 0: TimesFM-3 more accurate", transform=ax.transAxes,
            fontsize=7, color="#555555")
    fig.suptitle("Figure 2: Accuracy of TimesFM-3 relative to the best classical method",
                 fontsize=9, y=1.02)
    fig.tight_layout()
    save(fig, "fig2_mase_ratio")


# ------------------------------------------------------------------ Figure 3
def fig_coverage(cov: pd.DataFrame) -> None:
    """Empirical coverage of the nominal 60% and 80% intervals, by method and length."""
    c = cov[cov.horizon_slice == "h1_12"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, (col, nominal, lab) in zip(
            axes, [("cover60", 0.60, "60% interval"), ("cover80", 0.80, "80% interval")]):
        g = c.groupby(["method", "n"])[col].mean().reset_index()
        for meth in METHOD_ORDER:
            s = g[g.method == meth].sort_values("n")
            if s.empty:
                continue
            ax.plot(s.n, s[col], marker="o", ms=3.5, lw=1.2,
                    color=COLOURS[meth], label=PRETTY[meth])
        ax.axhline(nominal, color="#333333", lw=0.9, ls="--")
        ax.set_xscale("log")
        ax.set_xticks(sorted(c.n.unique()))
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.set_xlabel("series length $n$")
        ax.set_title(f"{lab} (nominal shown dashed)", fontsize=8)
    axes[0].set_ylabel("empirical coverage")
    axes[1].legend(fontsize=7, ncol=2, loc="lower right")
    fig.suptitle("Figure 3: Interval reliability, averaged over all nine processes",
                 fontsize=9, y=1.03)
    fig.tight_layout()
    save(fig, "fig3_coverage")


# ------------------------------------------------------------------ Figure 4
def fig_horizon(mase: pd.DataFrame) -> None:
    """How the ranking changes with forecast horizon."""
    order = ["h1", "h1_6", "h1_12"]
    labels = {"h1": "h = 1", "h1_6": "h = 1..6", "h1_12": "h = 1..12"}
    regimes = [("classical correctly specified (D1-D5)", ["D1", "D2", "D3", "D4", "D5"]),
               ("no classical model correct (D6-D9)", ["D6", "D7", "D8", "D9"])]

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, (title, dgps) in zip(axes, regimes):
        sub = mase[mase.dgp.isin(dgps)]
        for meth in METHOD_ORDER:
            s = sub[sub.method == meth].groupby("horizon_slice")["mean_MASE"].mean()
            s = s.reindex(order)
            ax.plot(range(len(order)), s.values, marker="o", ms=3.5, lw=1.2,
                    color=COLOURS[meth], label=PRETTY[meth])
        ax.set_xticks(range(len(order)))
        ax.set_xticklabels([labels[o] for o in order])
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("forecast horizon")
    axes[0].set_ylabel("mean MASE")
    axes[1].legend(fontsize=7, ncol=2)
    fig.suptitle("Figure 4: Accuracy by horizon, split by whether a classical model is correct",
                 fontsize=9, y=1.03)
    fig.tight_layout()
    save(fig, "fig4_horizon")


def main() -> None:
    mase = pd.read_csv(RES / "table_mase.csv")
    cov = pd.read_csv(RES / "table_coverage.csv")
    dec = pd.read_csv(RES / "table_decision.csv")

    fig_example_series()
    fig_mase_ratio(dec)
    fig_coverage(cov)
    fig_horizon(mase)
    print("all figures written as vector PDF (AJS rule C2.graphics)")


if __name__ == "__main__":
    main()
