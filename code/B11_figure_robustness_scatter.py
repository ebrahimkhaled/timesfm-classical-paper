"""Typical against worst-case accuracy of the fifteen methods of the main design (structural revision).

x: geometric mean over the 36 scenarios of the ratio to the scenario-best; y: worst ratio. Both from
results/revision/robustness_ci.csv (set "extended fifteen"), with 95% bootstrap intervals.
Crowded points are shown in a zoomed inset instead of with leader lines (author's request).
Output: figures/fig6_robustness_scatter.pdf
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import Rectangle
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FM = {"TimesFM3", "TimesFM3eval", "TimesFM25", "TimesFM25raw", "ChronosBolt", "Chronos2", "TiRex"}
LAB = {"SeasonalNaive": "Seasonal naive", "Theta": "Theta", "DOTM": "DOTM", "AutoETS": "AutoETS",
       "AutoARIMA": "AutoARIMA", "M4Comb": "M4 Comb", "ChronosBolt": "Chronos-Bolt",
       "TimesFM25": "TimesFM-2.5", "TimesFM25raw": "TimesFM-2.5 (settings off)", "Chronos2": "Chronos-2",
       "TiRex": "TiRex"}
# Main panel: text offset (points) and alignment; pairs that coincide get one label.
MAIN = {"SeasonalNaive": (7, -2, "left"), "Theta": (7, -2, "left"), "DOTM": (-7, 4, "right"),
        "M4Comb": (-7, -9, "right"), "AutoETS": (7, -2, "left"), "ChronosBolt": (7, -2, "left")}
GROUPS = {("TimesFM3", "TimesFM3eval"): ("TimesFM-3 (both settings)", (9, -3, "left")),
          ("Combination", "CombEAD"): ("two combinations", (0, -11, "center"))}
ZOOM = ["TimesFM25", "TimesFM25raw", "TiRex", "AutoARIMA", "Chronos2"]
INSET_LAB = {"TimesFM25": (-7, -8, "right"), "TimesFM25raw": (7, 10, "left"), "TiRex": (-7, 5, "right"),
             "AutoARIMA": (8, -6, "left"), "Chronos2": (-7, 0, "right")}


def colour(m):
    return "#0072B2" if m.startswith("TimesFM3") else ("#56B4E9" if m in FM else "#7f7f7f")


def point(ax, x, ms=5):
    c = colour(x.method)
    ax.errorbar(x.meanlog, x.worst, xerr=[[x.meanlog - x.meanlog_lo], [x.meanlog_hi - x.meanlog]],
                yerr=[[x.worst - x.worst_lo], [x.worst_hi - x.worst]], fmt="o" if x.method in FM else "s",
                ms=ms, color=c, ecolor=c, elinewidth=0.8, capsize=0)


def label(ax, x, y, text, spec, size=7.5):
    dx, dy, ha = spec
    ax.annotate(text, (x, y), textcoords="offset points", xytext=(dx, dy), ha=ha, va="center",
                fontsize=size, color="0.15")


def main():
    r = pd.read_csv(ROOT / "results" / "revision" / "robustness_ci.csv")
    r = r[r.set == "extended fifteen"].set_index("method", drop=False)
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for _, x in r.iterrows():
        point(ax, x)
    for m, spec in MAIN.items():
        label(ax, r.loc[m, "meanlog"], r.loc[m, "worst"], LAB[m], spec)
    for members, (text, spec) in GROUPS.items():
        g = r.loc[list(members)]
        label(ax, g.meanlog.mean(), g.worst.mean(), text, spec)
    x0, x1, y0, y1 = 1.108, 1.150, 2.02, 2.95
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="0.45", lw=0.7, ls="--"))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1.04, 1.52)
    ax.set_ylim(1.18, 6.6)
    ax.set_yticks([1.25, 1.5, 2, 3, 4, 6])
    ax.set_yticklabels(["1.25", "1.5", "2", "3", "4", "6"])
    ax.set_xticks([1.05, 1.1, 1.2, 1.3, 1.4, 1.5])
    ax.set_xticklabels(["1.05", "1.10", "1.20", "1.30", "1.40", "1.50"])
    for a in (ax.xaxis, ax.yaxis):
        a.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("typical ratio to the best method in a scenario (geometric mean over 36 scenarios)")
    ax.set_ylabel("worst ratio to the best method in a scenario")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    ins = ax.inset_axes([0.05, 0.61, 0.37, 0.36])
    for m in ZOOM:
        point(ins, r.loc[m])
        label(ins, r.loc[m, "meanlog"], r.loc[m, "worst"], LAB[m], INSET_LAB[m], size=7)
    ins.set_xlim(x0, x1)
    ins.set_ylim(y0, y1)
    ins.set_xticks([1.12, 1.13, 1.14])
    ins.set_yticks([2.2, 2.5, 2.8])
    ins.tick_params(labelsize=6.5)
    for s in ins.spines.values():
        s.set_edgecolor("0.45")
        s.set_linestyle("--")
        s.set_linewidth(0.7)
    ins.set_title("dashed box enlarged", fontsize=7, pad=2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "fig6_robustness_scatter.pdf")
    print("wrote figures/fig6_robustness_scatter.pdf")


if __name__ == "__main__":
    main()
