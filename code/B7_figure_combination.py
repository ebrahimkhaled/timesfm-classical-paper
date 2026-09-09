"""Draw the figure that explains why the robust combination lost.

Section 8.8 answers a fair objection -- the equal-weight combination averages its members, and
an average is not robust to one member collapsing -- by rerunning the comparison against a
median combination and reporting that it came out slightly worse. True, and unexplained. A
reader is left thinking the robust version should have won and cannot see why it did not.

The reason is arithmetic, and it is specific to this ensemble: the combination has THREE
members (Theta, AutoETS, AutoARIMA). The median of three numbers is the middle one. So the
"robust" combination keeps one forecast and discards the other two, which is precisely the
averaging that made combining worth doing. It buys protection against a bad member by giving
up the mechanism.

  A  one cell worked through: D5 at n = 24, the three members, their average, and what each
     combination rule produces from them
  B  the same comparison over all 36 cells -- the median rule wins in 8
  C  the proof that the median combination IS the middle member: the two agree to 0.059 MASE
     on average, while the mean combination sits well away from it

Output: figures/fig9_combination.pdf
"""

from __future__ import annotations

from pathlib import Path

import arabic_reshaper
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bidi.algorithm import get_display

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig9_combination.pdf"

ORANGE, BLUE, GREY, GREEN, BAD = "#D55E00", "#0072B2", "#8c8c8c", "#1a7a3c", "#c0392b"
PARTS = ["Theta", "AutoETS", "AutoARIMA"]
CELL = ("D5", 24)

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(t: str) -> str:
    return get_display(arabic_reshaper.reshape(t))


# ---------------- data ----------------
m = pd.read_csv(ROOT / "results" / "table_mase.csv")
m = m[m.horizon_slice == "h1_12"]
rc = pd.read_csv(ROOT / "results" / "table_robust_combination.csv")
comb = rc.pivot_table(index=["dgp", "n"], columns="opponent", values="mean_MASE_opponent")

rows = []
for (d, n), g in m.groupby(["dgp", "n"]):
    v = g.set_index("method").loc[PARTS, "mean_MASE"].values
    rows.append({"dgp": d, "n": n,
                 "mid_member": float(np.median(v)), "mean_of_3": float(np.mean(v)),
                 "mean_comb": comb.loc[(d, n), "MeanCombination"],
                 "median_comb": comb.loc[(d, n), "MedianCombination"]})
t = pd.DataFrame(rows)

fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(12.8, 4.5))

# ---------------- A: one cell, worked through ----------------
cell = m[(m.dgp == CELL[0]) & (m.n == CELL[1])].set_index("method")["mean_MASE"]
members = [cell[p] for p in PARTS]
avg = float(np.mean(members))
mean_c = comb.loc[CELL, "MeanCombination"]
median_c = comb.loc[CELL, "MedianCombination"]

labels = PARTS + ["Mean\ncomb.", "Median\ncomb."]
vals = members + [mean_c, median_c]
colours = [GREY, GREY, GREY, BLUE, ORANGE]
xs = [0, 1, 2, 3.7, 4.9]

axA.bar(xs, vals, 0.74, color=colours, edgecolor="white")
axA.axhline(avg, color=GREEN, ls="--", lw=1.6)
for x, v in zip(xs, vals):
    axA.text(x, v + 0.07, f"{v:.2f}", ha="center", fontsize=9.6, fontweight="bold")

# the reading goes in the empty band above the tallest bar, one line each
READINGS = [
    (4.98, GREEN, f"متوسط الأعضاء التلاتة = {avg:.2f}"),
    (4.62, BLUE, f"الدمج بالمتوسط {mean_c:.2f} — أحسن منهم ✓"),
    (4.26, ORANGE, f"الدمج بالوسيط {median_c:.2f} — نفس AutoETS ✗"),
]
for y, colour, txt in READINGS:
    axA.text(5.45, y, ar(txt), color=colour, fontsize=9.6, ha="right", va="center",
             fontweight="bold")

axA.set_xticks(xs)
axA.set_xticklabels(labels, fontsize=9)
axA.set_xlim(-0.6, 5.55)
axA.set_ylim(0, 5.25)
axA.set_ylabel("MASE", fontsize=10)
axA.set_title(ar(f"أ) خلية واحدة بالتفصيل ({CELL[0]}، n = {CELL[1]})"), fontsize=11.5, pad=9)
axA.grid(axis="y", color="#e8e8e8", lw=0.4); axA.set_axisbelow(True)

# ---------------- B: all 36 cells ----------------
wins = int((t.median_comb < t.mean_comb).sum())
lim = (0.5, max(t.mean_comb.max(), t.median_comb.max()) * 1.06)
axB.plot(lim, lim, color="#444444", lw=1.2)
axB.fill_between(lim, lim, lim[1], color=BLUE, alpha=0.07)
axB.fill_between(lim, lim[0], lim, color=ORANGE, alpha=0.07)
axB.scatter(t.mean_comb, t.median_comb, s=46, color=ORANGE, alpha=0.8, zorder=3)

axB.text(0.96, 0.06, ar(f"الوسيط أحسن هنا — {wins} خلايا بس"), transform=axB.transAxes,
         fontsize=9.6, color=ORANGE, ha="right", fontweight="bold")
axB.text(0.06, 0.94, ar(f"المتوسط أحسن هنا — {36 - wins} خلية"), transform=axB.transAxes,
         fontsize=9.6, color=BLUE, ha="left", va="top", fontweight="bold")

axB.set_xlim(lim); axB.set_ylim(lim)
axB.set_xlabel(ar("الدمج بالمتوسط (MASE)"), fontsize=10)
axB.set_ylabel(ar("الدمج بالوسيط (MASE)"), fontsize=10)
axB.set_title(ar("ب) على الـ 36 خلية كلها"), fontsize=11.5, pad=9)
axB.grid(color="#e8e8e8", lw=0.4); axB.set_axisbelow(True)

# ---------------- C: the median combination IS the middle member ----------------
gap_med = float(np.abs(t.median_comb - t.mid_member).mean())
gap_mean = float(np.abs(t.mean_comb - t.mid_member).mean())

axC.plot(lim, lim, color="#444444", lw=1.2)
axC.scatter(t.mid_member, t.median_comb, s=52, color=ORANGE, alpha=0.85, zorder=3,
            label=ar(f"الدمج بالوسيط — الفرق {gap_med:.3f}"))
axC.scatter(t.mid_member, t.mean_comb, s=42, color=BLUE, alpha=0.6, marker="^", zorder=2,
            label=ar(f"الدمج بالمتوسط — الفرق {gap_mean:.3f}"))
axC.set_xlim(lim); axC.set_ylim(lim)
axC.set_xlabel(ar("العضو الأوسط لوحده (MASE)"), fontsize=10)
axC.set_ylabel(ar("الدمج (MASE)"), fontsize=10)
axC.set_title(ar("ج) الوسيط مابيدمجش — بيختار واحد"), fontsize=11.5, pad=9)
axC.legend(fontsize=8.8, frameon=False, loc="upper left")
axC.grid(color="#e8e8e8", lw=0.4); axC.set_axisbelow(True)

fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
print(f"  cell {CELL}: members {[round(v, 2) for v in members]}, avg {avg:.3f}")
print(f"    mean-comb {mean_c:.3f} (beats the members' average)  "
      f"median-comb {median_c:.3f} (= middle member {t.set_index(['dgp','n']).loc[CELL,'mid_member']:.3f})")
print(f"  median rule better in {wins}/36 cells")
print(f"  |median-comb - middle member| {gap_med:.3f}   |mean-comb - middle member| {gap_mean:.3f}")
print(f"  mean-comb beats its members' average in "
      f"{int((t.mean_comb < t.mean_of_3).sum())}/36 cells")
