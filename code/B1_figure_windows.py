"""Draw the rolling-origin diagram that explains why 1,000 series give 2,932 windows.

The Arabic companion stated the rule but never showed it, and the arithmetic
(951x3 + 30x2 + 19x1) reads like a fudge until you can see WHY a short series yields fewer
windows. Three panels:

  A  a long series: all three windows fit
  B  a short series: the second window would leave too little history, so it is refused
  C  the resulting counts, with the exact length threshold for each

Arabic labels are shaped with arabic_reshaper + python-bidi, because matplotlib draws raw
code points: without shaping the letters appear isolated and in the wrong order.

Output: figures/fig5_windows.pdf (vector, matching the paper's other figures).
"""

from __future__ import annotations

from pathlib import Path

import arabic_reshaper
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures" / "fig5_windows.pdf"

MIN_LEN, HORIZON, STEP = 120, 18, 12
CTX, HOR, BAD, GRID = "#9ecae1", "#D55E00", "#c0392b", "#cccccc"

plt.rcParams.update({
    "font.family": ["Tahoma", "Segoe UI", "DejaVu Sans"],
    "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def ar(text: str) -> str:
    """Shape Arabic for matplotlib, which otherwise draws unjoined letters in reverse."""
    return get_display(arabic_reshaper.reshape(text))


def draw_series(ax, n: int, title: str, max_windows: int = 3) -> None:
    ax.set_title(ar(title), fontsize=10, pad=8)
    y = 0
    for k in range(max_windows):
        end = n - k * STEP
        ctx_end = end - HORIZON
        ok = ctx_end >= MIN_LEN
        colour_ctx = CTX if ok else "#e8e8e8"
        colour_hor = HOR if ok else "#f0c6bd"

        ax.barh(y, ctx_end, height=0.55, color=colour_ctx,
                edgecolor="white", linewidth=0.6)
        ax.barh(y, HORIZON, left=ctx_end, height=0.55, color=colour_hor,
                edgecolor="white", linewidth=0.6)

        label = ar(f"نافذة {k + 1}")
        ax.text(-n * 0.015, y, label, ha="right", va="center", fontsize=8.5)

        if ok:
            ax.text(ctx_end / 2, y, f"{ctx_end}", ha="center", va="center",
                    fontsize=7.5, color="#08306b")
            ax.text(ctx_end + HORIZON / 2, y + 0.42, f"{ctx_end + 1}-{end}",
                    ha="center", va="bottom", fontsize=7, color=HOR)
        else:
            ax.text(ctx_end / 2, y, f"{ctx_end} < {MIN_LEN}", ha="center", va="center",
                    fontsize=7.5, color=BAD, fontweight="bold")
            ax.text(n * 0.52, y, ar("مرفوضة — التاريخ مش كفاية"),
                    ha="left", va="center", fontsize=8, color=BAD)
        y -= 1

    ax.axvline(MIN_LEN, color=BAD, lw=1.1, ls="--", zorder=5)
    ax.text(MIN_LEN, 0.75, ar(f"الحد الأدنى للتاريخ = {MIN_LEN} شهر"),
            color=BAD, fontsize=7.5, ha="center", va="bottom")
    ax.set_xlim(0, max(n * 1.05, MIN_LEN * 1.6))
    ax.set_ylim(-max_windows + 0.4, 1.25)
    ax.set_yticks([])
    ax.set_xlabel(ar("الشهر"), fontsize=8.5)
    ax.grid(axis="x", color=GRID, lw=0.4, alpha=0.6)
    ax.set_axisbelow(True)


fig, axes = plt.subplots(3, 1, figsize=(7.6, 8.4),
                         gridspec_kw={"height_ratios": [1, 1, 0.85], "hspace": 0.55})

draw_series(axes[0], 346, "سلسلة طويلة (346 شهر) — التلات نوافذ كلها بتعدّي")
draw_series(axes[1], 145, "سلسلة قصيرة (145 شهر) — نافذة واحدة بس بتعدّي")

# --- panel C: the counts, with the exact threshold per window ---------------------
ax = axes[2]
counts = [(3, 951, "n ≥ 162"), (2, 30, "150 ≤ n < 162"), (1, 19, "138 ≤ n < 150")]
ys = [0, -1, -2]
for (w, c, rule), y in zip(counts, ys):
    ax.barh(y, c, height=0.55, color=CTX, edgecolor="white")
    # The count sits just past the bar's end; the length rule sits at a FIXED column.
    # Placing the rule at c/2 put it on top of the row label whenever the bar was short
    # (30 and 19 are tiny next to 951), which made the panel unreadable.
    # A long bar carries its count INSIDE; a short one carries it just outside. Always
    # placing it outside pushed the 951 label into the rule column and they overlapped.
    if c > 400:
        ax.text(c - 25, y, f"{c}  " + ar("سلسلة"), va="center", ha="right",
                fontsize=9, fontweight="bold", color="#08306b")
    else:
        ax.text(c + 20, y, f"{c}  " + ar("سلسلة"), va="center", ha="left",
                fontsize=9, fontweight="bold")
    ax.text(-20, y, ar(f"{w} نوافذ" if w > 1 else "نافذة واحدة"),
            ha="right", va="center", fontsize=8.5)
    ax.text(1230, y, rule, ha="right", va="center", fontsize=8.5, color="#08306b",
            family="DejaVu Sans")

ax.set_title(ar("كل طول بيدّي كام نافذة؟") + "   951×3 + 30×2 + 19×1 = 2,932",
             fontsize=10, pad=8)
ax.set_xlim(-230, 1260)
ax.set_ylim(-2.7, 0.7)
ax.set_yticks([])
ax.set_xlabel(ar("عدد السلاسل"), fontsize=8.5)
ax.set_xticks([0, 200, 400, 600, 800, 1000])   # hide the negative padding tick
ax.grid(axis="x", color=GRID, lw=0.4, alpha=0.6)
ax.set_axisbelow(True)

fig.legend(handles=[Patch(color=CTX, label=ar("اللي الموديل بيشوفه (context)")),
                    Patch(color=HOR, label=ar("اللي بيتنبأ بيه (18 شهر)"))],
           loc="lower center", ncol=2, frameon=False, fontsize=9,
           bbox_to_anchor=(0.5, -0.02))

OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT)
print(f"wrote {OUT.relative_to(ROOT)}")
