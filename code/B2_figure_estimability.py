"""Draw the figure that makes 'specification is not estimability' click.

The finding is stated in the companion but never *shown*. The intuition is a counting
argument: ETS(A,A,A) with a period of 12 must estimate 16 numbers -- three smoothing
parameters, an initial level and trend, and eleven free initial seasonal states. At n = 24
that is 1.5 observations per parameter, which is hopeless; at n = 200 it is 12.5, which is
comfortable. Nothing about the model changed between those two cases. Only the data did.

  Panel A  what has to be estimated, against how much data there is
  Panel B  the consequence: AutoETS on D5 -- the process it is correctly specified for --
           collapsing from 3.03 (worst of six) at n = 24 to 0.68 (best) at n = 200

Output: figures/fig6_estimability.pdf
"""

from __future__ import annotations

from pathlib import Path

import arabic_reshaper
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import pandas as pd
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig6_estimability.pdf"

LENGTHS = [24, 48, 96, 200]
N_PARAMS = 16          # 3 smoothing + level + trend + 11 free seasonal states
BLUE, ORANGE, GREY, BAD = "#0072B2", "#D55E00", "#999999", "#c0392b"

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(t: str) -> str:
    return get_display(arabic_reshaper.reshape(t))


fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.2, 4.1))

# ---------------- Panel A: data per parameter ----------------
x = range(len(LENGTHS))
per = [n / N_PARAMS for n in LENGTHS]
colours = [BAD if p < 4 else BLUE for p in per]

axA.bar(x, per, color=colours, width=0.6, edgecolor="white")
axA.axhline(4, color=BAD, ls="--", lw=1.1)
axA.text(len(LENGTHS) - 0.5, 4.25, ar("أقل من كده = تقدير جعان"),
         color=BAD, fontsize=8.5, ha="right")

for i, (n, p) in enumerate(zip(LENGTHS, per)):
    axA.text(i, p + 0.35, f"{p:.1f}", ha="center", fontsize=10, fontweight="bold",
             color=BAD if p < 4 else BLUE)
    axA.text(i, -1.4, f"n = {n}", ha="center", fontsize=8.5)

axA.set_xticks([])
axA.set_ylim(0, 14.5)
axA.set_ylabel(ar("نقاط بيانات لكل parameter"), fontsize=9)
axA.set_title(ar("AutoETS لازم يقدّر 16 رقم — عنده كام نقطة لكل رقم؟"),
              fontsize=10, pad=10)
axA.grid(axis="y", color="#dddddd", lw=0.4)
axA.set_axisbelow(True)

# ---------------- Panel B: the consequence ----------------
m = pd.read_csv(ROOT / "results" / "table_mase.csv")
m = m[(m.horizon_slice == "h1_12") & (m.dgp == "D5")]
piv = m.pivot_table(index="n", columns="method", values="mean_MASE")

series = [("AutoETS", ORANGE, 2.4, "o"),
          ("SeasonalNaive", GREY, 1.4, "s"),
          ("TimesFM3", BLUE, 1.4, "^")]
labels = {"AutoETS": "AutoETS — المخصّص صح", "SeasonalNaive": "SeasonalNaive — أغبى قاعدة",
          "TimesFM3": "TimesFM-3"}

for name, colour, lw, mk in series:
    axB.plot(range(len(LENGTHS)), [piv.loc[n, name] for n in LENGTHS],
             marker=mk, ms=6, lw=lw, color=colour, label=ar(labels[name]))

axB.annotate(ar("كارثة: 3.03"), xy=(0, piv.loc[24, "AutoETS"]),
             xytext=(0.35, 2.75), fontsize=9, color=BAD, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=BAD, lw=1.2))
axB.annotate(ar("الأحسن: 0.68"), xy=(3, piv.loc[200, "AutoETS"]),
             xytext=(2.0, 1.35), fontsize=9, color="#1a7a3c", fontweight="bold",
             arrowprops=dict(arrowstyle="->", color="#1a7a3c", lw=1.2))

axB.axhline(1.0, color="#bbbbbb", ls=":", lw=1)
axB.text(3.05, 1.03, "MASE = 1", fontsize=7.5, color="#888888", ha="right")

axB.set_xticks(range(len(LENGTHS)))
axB.set_xticklabels([f"n = {n}" for n in LENGTHS], fontsize=8.5)
axB.set_ylabel("MASE", fontsize=9)
axB.set_title(ar("نفس الموديل، نفس البيانات — الطول بس هو اللي اتغيّر (D5)"),
              fontsize=10, pad=10)
axB.legend(fontsize=8.5, frameon=False, loc="upper right")
axB.grid(axis="y", color="#dddddd", lw=0.4)
axB.set_axisbelow(True)

fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
print(f"  AutoETS on D5: n=24 -> {piv.loc[24,'AutoETS']:.3f}, n=200 -> {piv.loc[200,'AutoETS']:.3f}")
