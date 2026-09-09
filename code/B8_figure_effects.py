"""Draw the figure behind section 8.9: how big the wins are, and why two tests disagree.

The section makes two points that a reader has to take on faith.

The first is that a statistically significant difference can be too small to act on: against
AutoARIMA the typical MASE gap is 0.010, one hundredth of a unit, on forecasts whose MASE is
around 1.4. The bar chart puts that next to the other four opponents and next to the scale it
lives on.

The second is more interesting. On D8 against SeasonalNaive the t-test reports a decisive win
at every length (p < 1e-6) while Wilcoxon reports nothing (p = 0.115 to 0.922). That is not a
technicality about tests -- it is a real fact about the forecasts, and the sorted differences
show it directly. On roughly two series in three TimesFM-3 is very slightly WORSE. On a small
minority SeasonalNaive fails catastrophically and TimesFM-3 is better by whole MASE units. The
mean follows the minority, the median follows the majority, and both are reporting honestly.

  A  Hodges-Lehmann shift per opponent, against the MASE scale it sits on
  B  the 200 per-series differences on D8 / n = 48, sorted, with mean and median marked
  C  the two p-values at all four lengths

Output: figures/fig10_effects.pdf
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
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig10_effects.pdf"

ORANGE, BLUE, GREY, GREEN, BAD = "#D55E00", "#0072B2", "#8c8c8c", "#1a7a3c", "#c0392b"
SLICE = "h1_12"
CASE_N = 48          # the length drawn in panel B
LENGTHS = [24, 48, 96, 200]

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(t: str) -> str:
    return get_display(arabic_reshaper.reshape(t))


tests = pd.read_csv(ROOT / "results" / "table_tests.csv")
tests = tests[tests.horizon_slice == SLICE]
allm = pd.read_csv(ROOT / "results" / "all_metrics.csv")
allm = allm[allm.horizon_slice == SLICE]

fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(13.0, 4.6))

# ---------------- A: effect sizes ----------------
hl = tests.groupby("opponent")["hodges_lehmann"].median().sort_values()
typical = float(allm[allm.method == "TimesFM3"]["MASE"].median())

y = np.arange(len(hl))
colours = [ORANGE if abs(v) < 0.02 else BLUE for v in hl.values]
axA.barh(y, hl.values, 0.62, color=colours, edgecolor="white")
for i, (name, v) in enumerate(hl.items()):
    axA.text(v - 0.006, i, f"{v:+.3f}", va="center", ha="right", fontsize=9.6,
             fontweight="bold", color="#333333")

axA.axvline(0, color="#444444", lw=1.1)
axA.set_yticks(y); axA.set_yticklabels(list(hl.index), fontsize=9.5)
axA.set_xlim(-0.275, 0.055)
axA.set_xlabel(ar("فرق MASE النموذجي (سالب = TimesFM-3 أحسن)"), fontsize=10)
axA.set_title(ar(f"أ) الفرق معنوي — بس قدّ إيه؟  (MASE النموذجي ≈ {typical:.2f})"),
              fontsize=11, pad=9)
axA.annotate(ar("واحد من مية من وحدة MASE"), xy=(hl["AutoARIMA"], y[list(hl.index).index("AutoARIMA")]),
             xytext=(-0.145, len(hl) - 1.55), fontsize=9.4, color=ORANGE, fontweight="bold",
             ha="center", arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.3))
axA.grid(axis="x", color="#e8e8e8", lw=0.4); axA.set_axisbelow(True)


# ---------------- B: the 200 differences, sorted ----------------
def diffs(n: int) -> np.ndarray:
    g = allm[(allm.dgp == "D8") & (allm.n == n)]
    tf = g[g.method == "TimesFM3"].sort_values("rep")["MASE"].values
    sn = g[g.method == "SeasonalNaive"].sort_values("rep")["MASE"].values
    return tf - sn


d = np.sort(diffs(CASE_N))
share_worse = 100 * np.mean(d > 0)
tail = np.sort(d)[:10].sum() / d.size

axB.bar(np.arange(d.size), d, 1.0,
        color=[GREEN if v < 0 else BAD for v in d])
axB.axhline(float(np.median(d)), color=BLUE, lw=1.8, ls="-")
axB.axhline(float(d.mean()), color=ORANGE, lw=1.8, ls="--")

axB.text(198, np.median(d) + 0.28, ar(f"الوسيط {np.median(d):+.3f} — اللي Wilcoxon بيشوفه"),
         color=BLUE, fontsize=9.3, ha="right", fontweight="bold")
axB.text(198, d.mean() - 0.30, ar(f"المتوسط {d.mean():+.3f} — اللي t-test بيشوفه"),
         color=ORANGE, fontsize=9.3, ha="right", va="top", fontweight="bold")
axB.annotate(ar("أقل 5% من السلاسل\nبتجيب 42% من المتوسط"), xy=(5, d[4]),
             xytext=(62, -3.75), fontsize=9.3, color=GREEN, fontweight="bold",
             ha="center", arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.3))
axB.text(0.97, 0.055, ar(f"{share_worse:.0f}% من السلاسل TimesFM-3 أسوأ فيها (بشعرة)"),
         transform=axB.transAxes, fontsize=9.3, color=BAD, ha="right", fontweight="bold")

axB.set_xlim(-3, d.size + 2); axB.set_ylim(-5.4, 1.5)
axB.set_xlabel(ar("الـ 200 سلسلة، مرتبة من الأسوأ للأحسن"), fontsize=10)
axB.set_ylabel(ar("فرق MASE (سالب = TimesFM-3 أحسن)"), fontsize=10)
axB.set_title(ar(f"ب) D8 قدام SeasonalNaive (n = {CASE_N})"), fontsize=11.5, pad=9)
axB.grid(axis="y", color="#e8e8e8", lw=0.4); axB.set_axisbelow(True)

# ---------------- C: what each test reports ----------------
pw, pt = [], []
for n in LENGTHS:
    dd = diffs(n)
    pw.append(stats.wilcoxon(dd).pvalue)
    pt.append(stats.ttest_1samp(dd, 0).pvalue)

x = np.arange(len(LENGTHS)); w = 0.34
axC.bar(x - w / 2, pt, w, color=ORANGE, label="t-test")
axC.bar(x + w / 2, pw, w, color=BLUE, label="Wilcoxon")
axC.axhline(0.05, color=BAD, ls="--", lw=1.5)
axC.text(-0.45, 0.021, ar("حد المعنوية 0.05"), color=BAD, fontsize=9.4,
         ha="left", va="top", fontweight="bold")
for i, v in enumerate(pw):
    axC.text(i + w / 2, v * 1.5, f"{v:.2f}", ha="center", fontsize=9, color=BLUE,
             fontweight="bold")

axC.set_yscale("log"); axC.set_ylim(1e-11, 12)
axC.set_xticks(x); axC.set_xticklabels([f"n = {n}" for n in LENGTHS], fontsize=9.5)
axC.set_ylabel(ar("قيمة p (مقياس لوغاريتمي)"), fontsize=10)
axC.set_title(ar("ج) نفس البيانات — نتيجتين مختلفتين"), fontsize=11.5, pad=30)
axC.legend(fontsize=9.4, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0),
           ncol=2, columnspacing=1.8)
axC.grid(axis="y", color="#e8e8e8", lw=0.4); axC.set_axisbelow(True)

fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
print(f"  HL: " + ", ".join(f"{k} {v:+.3f}" for k, v in hl.items()))
print(f"  typical TimesFM-3 MASE {typical:.3f}")
print(f"  D8 n={CASE_N}: mean {d.mean():+.3f}  median {np.median(d):+.3f}  "
      f"{share_worse:.0f}% of series worse")
print(f"  worst 10 reps contribute {tail:+.3f} of the {d.mean():+.3f} mean "
      f"({100*tail/d.mean():.0f}%)")
print(f"  Wilcoxon p: {[round(v, 3) for v in pw]}")
print(f"  t-test  p: {['%.1e' % v for v in pt]}")
