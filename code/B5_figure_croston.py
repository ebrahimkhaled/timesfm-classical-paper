"""Draw the figure that PROVES why the two metrics disagree on intermittent demand.

The companion asserts the mechanism -- absolute error is minimised at the median, squared
error at the mean -- and then shows that TimesFM-3 wins MASE while Croston wins RMSSE. The
assertion and the result sit next to each other with nothing connecting them.

This figure supplies the connection, computed from the D8 data itself:

  A  the demand distribution: 69.8% zeros, median 0, mean 1.51
  B  the proof. For a constant forecast c, plot mean|y-c| and mean(y-c)^2 against c. The
     first bottoms out at c = 0, the second at c = 1.5. The two losses literally ask for
     different forecasts, so a method tuned to one must lose on the other.
  C  the consequence in the actual results: TimesFM-3 against the best Croston-family method,
     on MASE and on RMSSE, at all four lengths.

Output: figures/fig7_croston.pdf
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

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig7_croston.pdf"
ORANGE, BLUE, GREY, GREEN = "#D55E00", "#0072B2", "#999999", "#1a7a3c"

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(t: str) -> str:
    return get_display(arabic_reshaper.reshape(t))


spec = importlib.util.spec_from_file_location("dgp", ROOT / "code" / "01_dgp.py")
dgp = importlib.util.module_from_spec(spec); spec.loader.exec_module(dgp)
y = np.concatenate([dgp.simulate("D8", 200, r) for r in range(200)])
med, mean = float(np.median(y)), float(y.mean())

fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(11.6, 4.3))

# ---------------- A: the distribution ----------------
vals, cnts = np.unique(y, return_counts=True)
pct = 100 * cnts / cnts.sum()
axA.bar(vals, pct, color=BLUE, width=0.8, edgecolor="white")
axA.axvline(med, color=ORANGE, lw=2, ls="-")
axA.axvline(mean, color=GREEN, lw=2, ls="--")
axA.text(med + 0.3, 40, ar(f"الوسيط = {med:.0f}"), color=ORANGE, fontsize=11.5, fontweight="bold")
axA.text(mean + 0.4, 30, ar(f"المتوسط = {mean:.2f}"), color=GREEN, fontsize=11.5, fontweight="bold")
axA.annotate(ar(f"{100*np.mean(y==0):.0f}% من المشاهدات = صفر"), xy=(0, 69.8),
             xytext=(3.4, 62), fontsize=11.5, color=BLUE, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.3))
axA.set_xlim(-0.6, 12); axA.set_ylim(0, 78); axA.set_xticks(range(0, 13, 2))
axA.set_xlabel(ar("قيمة الطلب"), fontsize=11)
axA.set_ylabel(ar("نسبة من المشاهدات %"), fontsize=11)
axA.set_title(ar("أ) شكل الطلب المتقطع (D8)"), fontsize=12, pad=8)
axA.grid(axis="y", color="#e3e3e3", lw=0.4); axA.set_axisbelow(True)

# ---------------- B: the proof ----------------
cs = np.linspace(0, 4, 161)
mae = np.array([np.abs(y - c).mean() for c in cs])
mse = np.array([((y - c) ** 2).mean() for c in cs])
c_mae, c_mse = cs[mae.argmin()], cs[mse.argmin()]

axB.plot(cs, mae / mae.max(), color=ORANGE, lw=2.4, label=ar("خطأ مطلق (زي MASE)"))
axB.plot(cs, mse / mse.max(), color=BLUE, lw=2.4, ls="--", label=ar("خطأ تربيعي (زي RMSSE)"))
axB.plot([c_mae], [mae.min() / mae.max()], "o", color=ORANGE, ms=10, zorder=5)
axB.plot([c_mse], [mse.min() / mse.max()], "s", color=BLUE, ms=10, zorder=5)
axB.annotate(ar(f"أقل خطأ عند {c_mae:.0f}\n= الوسيط"), xy=(c_mae, mae.min() / mae.max()),
             xytext=(0.75, 0.30), fontsize=11.5, color=ORANGE, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.3))
axB.annotate(ar(f"أقل خطأ عند {c_mse:.1f}\n= المتوسط"), xy=(c_mse, mse.min() / mse.max()),
             xytext=(2.15, 0.60), fontsize=11.5, color=BLUE, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.3))
axB.set_xlabel(ar("التنبؤ الثابت c"), fontsize=11)
axB.set_ylabel(ar("الخسارة (منسوبة لأقصاها)"), fontsize=11)
axB.set_title(ar("ب) البرهان: المقياسين عايزين تنبؤ مختلف"), fontsize=12, pad=8)
axB.set_ylim(0.22, 1.08)
axB.legend(fontsize=10.5, frameon=False, loc="upper center")
axB.grid(color="#e3e3e3", lw=0.4); axB.set_axisbelow(True)

# ---------------- C: the consequence ----------------
# Plotted as a RATIO to the best Croston-family method, so the 1.0 line is the whole story:
# below it TimesFM-3 wins, above it Croston wins. On the same forecasts, MASE lands below
# at every length and RMSSE lands above at every length.
df = pd.read_csv(ROOT / "results" / "croston_d8_metrics.csv")
CROSTON = ["CrostonClassic", "CrostonOptimized", "CrostonSBA", "ADIDA", "IMAPA", "TSB"]
lengths = sorted(df.n.unique())


def ratio(metric: str) -> list[float]:
    out = []
    for n in lengths:
        d = df[df.n == n]
        tf = d[d.method == "TimesFM3"][metric].mean()
        best = d[d.method.isin(CROSTON)].groupby("method")[metric].mean().min()
        out.append(tf / best)
    return out


r_mase, r_rmsse = ratio("MASE"), ratio("RMSSE")

x = np.arange(len(lengths))
w = 0.3
axC.axhspan(1.0, 1.335, color=BLUE, alpha=0.06)
axC.axhspan(0.615, 1.0, color=ORANGE, alpha=0.06)
axC.axhline(1.0, color="#444444", lw=1.2)

axC.bar(x - w / 2, np.array(r_mase) - 1, w, bottom=1, color=ORANGE, label="_MASE")
axC.bar(x + w / 2, np.array(r_rmsse) - 1, w, bottom=1, color=BLUE, label="_RMSSE")

for i, (a, b) in enumerate(zip(r_mase, r_rmsse)):
    axC.text(i - w / 2, a + 0.014, f"{a:.2f}", ha="center", va="bottom",
             fontsize=10.5, color="white", fontweight="bold")
    axC.text(i + w / 2, b + 0.012, f"{b:.2f}", ha="center", va="bottom",
             fontsize=10.5, color=BLUE, fontweight="bold")

axC.text(1.5, 1.285, ar("فوق الخط ← Croston أحسن"), color=BLUE,
         fontsize=10.2, ha="center", va="center", fontweight="bold")
axC.text(1.5, 0.655, ar("تحت الخط ← TimesFM-3 أحسن"), color=ORANGE,
         fontsize=10.2, ha="center", va="center", fontweight="bold")

# name each colour once, on the first pair
axC.text(-w / 2, r_mase[0] - 0.024, "MASE", color=ORANGE, fontsize=9,
         ha="center", va="top", fontweight="bold")
axC.text(w / 2, r_rmsse[0] + 0.058, "RMSSE", color=BLUE, fontsize=9,
         ha="center", va="bottom", fontweight="bold")

axC.set_xticks(x); axC.set_xticklabels([f"n = {n}" for n in lengths], fontsize=10.5)
axC.set_xlim(-0.55, 3.55); axC.set_ylim(0.615, 1.335)
axC.set_ylabel(ar("النسبة لأحسن Croston"), fontsize=11)
axC.set_title(ar("ج) نفس التنبؤات — والمقياس هو اللي بيحدّد الفايز"), fontsize=12, pad=8)
axC.grid(axis="y", color="#e3e3e3", lw=0.4); axC.set_axisbelow(True)

fig.tight_layout()
OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
print(f"  zeros {100*np.mean(y==0):.1f}% | median {med:.0f} | mean {mean:.2f}")
print(f"  MAE minimised at c={c_mae:.2f}; MSE minimised at c={c_mse:.2f}")
print(f"  ratio MASE  {[round(v,3) for v in r_mase]}")
print(f"  ratio RMSSE {[round(v,3) for v in r_rmsse]}")
