"""Draw the figure that makes interval coverage concrete.

Section 8.7 asks whether an interval labelled 80% actually contains the truth 80% of the
time. It answers with three aggregate statistics -- mean coverage, mean absolute deviation
per cell, and interval width -- and a reader who has not already internalised what coverage
IS has nowhere to stand.

So the figure starts from the thing itself. Panels A and B show twenty individual forecast
cases from D6 at n = 96, twelve steps ahead: each bar is that case's 80% interval, each dot
is what actually happened. Counting the dots inside the bars IS the coverage. Put the two
methods side by side and the section's whole argument is visible at once -- AutoARIMA
catches every single case, and it catches them because its bars are nearly twice as long.

  A  TimesFM-3   -- 18 of 20 inside, mean width 11.5
  B  AutoARIMA   -- 20 of 20 inside, mean width 20.2
  C  why the headline average flatters everyone: averaging coverage across processes lets a
     cell that runs high cancel a cell that runs low. Per cell the miss is ~3x larger.
  D  coverage against width on D6. The target is the 0.80 line at the LEFT. Up and to the
     right is the weather forecast that promises -50 to +80 degrees.

Output: figures/fig8_coverage.pdf
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import arabic_reshaper
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bidi.algorithm import get_display
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig8_coverage.pdf"

ORANGE, BLUE, GREY = "#D55E00", "#0072B2", "#8c8c8c"
GOOD, BAD = "#1a7a3c", "#c0392b"

DGP, N, REPS, H = "D6", 96, 200, 12
SHOW = 20          # cases drawn in panels A and B
STEP = 11          # horizon index (the 12th step)
LO, HI = 0, 8      # q0.1 and q0.9 -> the nominal 80% interval

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(t: str) -> str:
    return get_display(arabic_reshaper.reshape(t))


# ---------------- data ----------------
spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dgp)
truth = np.array([dgp.simulate(DGP, N, r, H)[N:] for r in range(REPS)])

cl = np.load(ROOT / "results" / "forecasts" / f"classical_{DGP}_n{N}_r{REPS}.npz")
tf = np.load(ROOT / "results" / "forecasts" / f"timesfm_{DGP}_n{N}_r{REPS}.npz")
QUANTS = {"TimesFM3": tf["TimesFM3_q"], "AutoARIMA": cl["AutoARIMA_q"]}

fig = plt.figure(figsize=(12.4, 7.6))
gs = GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.22)


# ---------------- A and B: coverage, one case at a time ----------------
def strip(ax, method: str, colour: str, letter: str, title: str) -> tuple[int, float]:
    q = QUANTS[method]
    lo, hi = q[:SHOW, STEP, LO], q[:SHOW, STEP, HI]
    y = truth[:SHOW, STEP]
    inside = (y >= lo) & (y <= hi)
    x = np.arange(SHOW)

    ax.vlines(x, lo, hi, color=colour, lw=6, alpha=0.45,
              label=ar("الفترة اللي الموديل بيقول إنها 80%"))
    ax.scatter(x[inside], y[inside], s=32, color=GOOD, zorder=4, marker="o",
               label=ar("الحقيقة وقعت جوه الفترة"))
    ax.scatter(x[~inside], y[~inside], s=64, color=BAD, zorder=5, marker="X",
               label=ar("وقعت بره"))

    ax.set_xticks([]); ax.set_xlabel(ar("20 حالة تنبؤ (كل عمود حالة)"), fontsize=10)
    ax.set_title(ar(f"{letter}) {title}"), fontsize=11.5, pad=9)
    ax.grid(axis="y", color="#e8e8e8", lw=0.4); ax.set_axisbelow(True)
    return int(inside.sum()), float(np.mean(hi - lo))


axA, axB = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
n_tf, w_tf = strip(axA, "TimesFM3", ORANGE, "أ", "TimesFM-3")
n_ar, w_ar = strip(axB, "AutoARIMA", BLUE, "ب", "AutoARIMA")

span = (min(axA.get_ylim()[0], axB.get_ylim()[0]), max(axA.get_ylim()[1], axB.get_ylim()[1]))
for ax, n_in, wid, colour in [(axA, n_tf, w_tf, ORANGE), (axB, n_ar, w_ar, BLUE)]:
    ax.set_ylim(span)
    ax.text(0.03, 0.955, ar(f"{n_in} من 20 جوه = {100*n_in/SHOW:.0f}%"),
            transform=ax.transAxes, fontsize=11, fontweight="bold", color=colour,
            va="top", ha="left")
    ax.text(0.03, 0.865, ar(f"متوسط عرض الفترة = {wid:.1f}"), transform=ax.transAxes,
            fontsize=10, color="#555555", va="top", ha="left")

axA.set_ylabel(ar("قيمة السلسلة"), fontsize=10)
axA.legend(fontsize=8.6, frameon=False, loc="lower left", ncol=1,
           handletextpad=0.6, borderpad=0.2)
axB.text(0.5, 0.03, ar(f"بيمسك كل الحالات — بفترة أعرض {w_ar/w_tf:.1f} مرة"),
         transform=axB.transAxes, fontsize=10.2, color=BAD, fontweight="bold", ha="center")

# ---------------- C: the averaging trap ----------------
axC = fig.add_subplot(gs[1, 0])
cov = pd.read_csv(ROOT / "results" / "table_coverage.csv")
cov = cov[cov.horizon_slice == "h1_12"]

rows = []
for m, g in cov.groupby("method"):
    rows.append((m,
                 float((g.groupby("n")["cover80"].mean() - 0.80).abs().mean()),
                 float((g["cover80"] - 0.80).abs().mean())))
rows.sort(key=lambda r: r[2])
names = [r[0] for r in rows]
avg_first = [r[1] for r in rows]
per_cell = [r[2] for r in rows]

ypos = np.arange(len(names))
axC.barh(ypos + 0.19, avg_first, 0.36, color=GREY, alpha=0.55,
         label=ar("لو حسبت المتوسط الأول"))
axC.barh(ypos - 0.19, per_cell, 0.36,
         color=[ORANGE if n == "TimesFM3" else BLUE for n in names],
         label=ar("الانحراف الحقيقي لكل خلية"))
for i, (a, p) in enumerate(zip(avg_first, per_cell)):
    axC.text(p + 0.004, i - 0.19, f"{p:.3f}", va="center", fontsize=9,
             fontweight="bold", color="#333333")
    axC.text(a + 0.004, i + 0.19, f"{a:.3f}", va="center", fontsize=8.6, color=GREY)

axC.set_yticks(ypos)
axC.set_yticklabels(["TimesFM-3" if n == "TimesFM3" else n for n in names], fontsize=9.5)
axC.invert_yaxis()
axC.set_xlim(0, max(per_cell) * 1.42)
axC.set_xlabel(ar("المسافة بين التغطية الفعلية و 0.80 المطلوبة (أقل = أحسن)"),
               fontsize=10)
axC.set_title(ar("ج) المتوسط بيداري الانحراف — الحقيقي حوالي 3 أضعاف"),
              fontsize=11.5, pad=30)
axC.legend(fontsize=9, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
           ncol=2, borderpad=0.2, columnspacing=1.6)
axC.grid(axis="x", color="#e8e8e8", lw=0.4); axC.set_axisbelow(True)

# ---------------- D: coverage against width ----------------
axD = fig.add_subplot(gs[1, 1])
d6 = cov[cov.dgp == "D6"]
cls = d6[d6.method != "TimesFM3"]
t3 = d6[d6.method == "TimesFM3"].sort_values("n")

axD.axhline(0.80, color=GOOD, lw=1.6, ls="--")
axD.text(0.25, 0.804, ar("المطلوب 0.80"), color=GOOD, fontsize=9.8, fontweight="bold",
         va="bottom", ha="left")
axD.scatter(cls.width80, cls.cover80, s=52, color=BLUE, alpha=0.72,
            label=ar("الطرق الكلاسيكية الخمسة"))
axD.scatter(t3.width80, t3.cover80, s=95, color=ORANGE, marker="D", zorder=4,
            label="TimesFM-3")
OFFSETS = {24: (10, -2), 48: (10, 4), 96: (10, -11), 200: (10, -2)}
for _, r in t3.iterrows():
    axD.annotate(f"n={int(r.n)}", (r.width80, r.cover80), textcoords="offset points",
                 xytext=OFFSETS[int(r.n)], fontsize=8.6, color=ORANGE,
                 fontweight="bold")

axD.annotate(ar("تغطية شبه كاملة\nبفترة ضِعف العرض"), xy=(9.3, 0.995),
             xytext=(6.0, 0.925), fontsize=9.6, color=BAD, fontweight="bold",
             ha="center", arrowprops=dict(arrowstyle="->", color=BAD, lw=1.3))

axD.set_xlim(0, 11.6); axD.set_ylim(0.78, 1.02)
axD.set_xlabel(ar("عرض الفترة (أوسع ⟵ أقل فايدة)"), fontsize=10)
axD.set_ylabel(ar("التغطية الفعلية"), fontsize=10)
axD.set_title(ar("د) على الكسر الهيكلي D6: التغطية لوحدها بتكدب"), fontsize=11.5, pad=9)
axD.legend(fontsize=9, frameon=False, loc="lower right")
axD.grid(color="#e8e8e8", lw=0.4); axD.set_axisbelow(True)

OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
print(f"  A TimesFM-3 {n_tf}/{SHOW} inside, width {w_tf:.2f}")
print(f"  B AutoARIMA {n_ar}/{SHOW} inside, width {w_ar:.2f}  ({w_ar/w_tf:.2f}x wider)")
print(f"  C per-cell deviation: {dict(zip(names, [round(p, 3) for p in per_cell]))}")
