"""The remaining referee requests (author: "continue all the partially done"), 2026-09-24.

Evidence: results/round3/ (L4 count benchmarks, L6 simultaneous intervals, familiarity, instance transfer,
M4 reweighting, MASE scale), results/robust/ (heavy tails and outliers combined, R2/R4/R5),
results/post_cutoff/ (L5, FRED-MD, 2025-01..2026-06). Whitespace-tolerant replacements; a failed match
stops the script.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [ROOT / "manuscript_jof" / "timesfm_jof.tex", ROOT / "code" / "K11_body.tex"]


def rep(s, old, new, must=True):
    pat = r"\s+".join(re.escape(w) for w in old.split())
    s2, k = re.subn(pat, lambda m: new, s, count=1)
    if must:
        assert k == 1, f"not found: {old[:70]!r}"
    return s2


EDITS = [
    # abstract
    ("outliers leave these patterns qualitatively unchanged, and on the official test period of 1\\,000 M4 "
     "monthly series TimesFM-3 is level with the fifth- to seventh-ranked M4 entries, behind the four best, and "
     "among ten methods whose ranks cannot be separated.",
     "outliers, alone or together, leave these patterns qualitatively unchanged; on the official test period of\n"
     "1\\,000 M4 monthly series TimesFM-3 is level with the fifth- to seventh-ranked M4 entries, behind the four\n"
     "best, and on 101 macroeconomic series observed after the models' documented training data it is\n"
     "statistically level with the classical methods."),
    # MASE scale at n = 24
    ("\\citep{hyndman2006mase, kolassa2016count}. Probabilistic accuracy",
     "\\citep{hyndman2006mase, kolassa2016count}. With $m = 12$ and $n = 24$ the MASE denominator rests on 12\n"
     "seasonal differences: its coefficient of variation across replications is 0.33 on D4 (0.09 at $n = 200$)\n"
     "and 0.35 to 0.44 on D5 at every length, so absolute MASE levels in those scenarios are imprecise, whereas\n"
     "the paired ratios used for inference are much less affected. Probabilistic accuracy"),
    # simultaneous intervals
    ("stable---TimesFM-3's 16 has an interval of 13 to 20---and no conclusion rests on it.",
     "stable---TimesFM-3's 16 has an interval of 13 to 20---and no conclusion rests on it. Simultaneous\n"
     "bootstrap bands over the 36 scenarios (max-$t$), which control the error of the whole set of intervals, are\n"
     "about 1.9 times wider than the per-scenario intervals of \\figureref{fig:forest}; against AutoARIMA they\n"
     "separate 8 scenarios in favour of TimesFM-3 and 4 against it, and against every other opponent they keep\n"
     "the direction of the pattern (Supporting Information, Table~S17)."),
    # count benchmarks
    ("foundation models (\\tableref{tab:d8ext}). The result concerns a process that is independent over time,",
     "foundation models (\\tableref{tab:d8ext}). A model built for intermittent demand, iETS with automatic\n"
     "occurrence selection \\citep{svetunkov2023iets}, has a pinball loss of 0.283 to 0.306, lower than\n"
     "TimesFM-3's at every length (paired Wilcoxon $p < 0.001$) and level with the empirical deciles: it selects\n"
     "a fixed occurrence probability for 791 of 797 series, which brings its predictive distribution close to\n"
     "that of the history. Negative-binomial and TSB-type predictive distributions fitted to the context do\n"
     "worse than the empirical deciles (Supporting Information, Table~S15). The result concerns a process that\n"
     "is independent over time,"),
    # combined departures
    ("otherwise. TimesFM-3 never receives a period, so its forecasts are unchanged in the last version.",
     "otherwise. TimesFM-3 never receives a period, so its forecasts are unchanged in the last version. A fifth\n"
     "version, added later, applies the heavy tails and the outliers together, with the same draws."),
    ("In the three versions with a known period", "In the four versions with a known period"),
    ("it is the best method in 14 to 16 scenarios", "it is the best method in 14 to 19 scenarios"),
    ("TimesFM-3 wins 93 to 101 of 180 comparisons and loses 27 to 29,",
     "TimesFM-3 wins 93 to 104 of 180 comparisons and loses 24 to 29,"),
    ("with outliers it is ahead at two of the three lengths, by 15\\% and 5\\%),",
     "with outliers it is ahead at two of the three lengths, by 15\\% and 5\\%, and with outliers and heavy\n"
     "tails together by 16\\% and 6\\%),"),
    ("the departures from the assumptions were applied one at a time.",
     "the departures from the assumptions were applied one at a time and in one combination."),
    # familiarity
    ("explain little of the per-series variation ($R^2 \\leq 0.26$).",
     "explain little of the per-series variation ($R^2 \\leq 0.26$).\n\n"
     "\\textbf{Familiarity.} Because TimesFM-3 is pre-trained partly on synthetic series, its advantage could\n"
     "reflect familiarity with some process families rather than their difficulty. At matched difficulty\n"
     "(spectral entropy and length), its advantage over AutoARIMA is about 5\\% to 6\\% larger on the processes\n"
     "that no classical family specifies (D6--D8) than on D1--D5 (shift in the $\\log_2$ ratio $-0.096$, 95\\%\n"
     "interval $-0.128$ to $-0.064$; median regression $-0.066$), which is consistent with an effect of\n"
     "familiarity but does not establish one."),
    # instance transfer
    ("nearest to D8, because M4 has no intermittent series; the intermittent-demand results rest on the simulation alone.",
     "nearest to D8, because M4 has no intermittent series; the intermittent-demand results rest on the simulation\n"
     "alone. Coverage of the feature space does not mean that results transfer series by series: predicting each\n"
     "M4 series' $\\log_2$ ratio of TimesFM-3's MASE to AutoARIMA's from its ten nearest simulated series gives a\n"
     "Spearman correlation of 0.06 (95\\% interval $-0.01$ to 0.13) with the realised ratio, no better than a\n"
     "constant prediction."),
    # M4 reweighting
    ("TimesFM-3 matches good specialised methods of 2018 without per-series tuning, but not the best of them.",
     "TimesFM-3 matches good specialised methods of 2018 without per-series tuning, but not the best of them.\n"
     "Reweighting the sample to the length distribution of the population it was drawn from leaves TimesFM-3's\n"
     "OWA at 0.861 and the four leading entries unchanged; the shorter third of the M4 Monthly series is not\n"
     "represented, and the truncation experiment below stands in for it."),
    # summary-of-findings row
    ("On M4, TimesFM-3 is level with the fifth- to seventh-ranked entries, behind the four best &\n"
     "  \\sectionref{sec:m4official} & Post hoc & 1\\,000 long monthly series \\\\",
     "On M4, TimesFM-3 is level with the fifth- to seventh-ranked entries, behind the four best &\n"
     "  \\sectionref{sec:m4official} & Post hoc & 1\\,000 long monthly series \\\\[2pt]\n"
     "On data observed after the documented training corpora, TimesFM-3 is level with the classical methods &\n"
     "  \\sectionref{sec:postcutoff} & Post hoc & 101 FRED-MD series, 2025--2026 \\\\"),
    # conclusion
    ("On the M4 test period TimesFM-3 is level with good but not the best M4 entries.",
     "On the M4 test period TimesFM-3 is level with good but not the best M4 entries, and on macroeconomic data\n"
     "observed after its documented training data it is level with the classical methods."),
    ("post hoc. \\emph{External.}",
     "post hoc; only the data of \\sectionref{sec:postcutoff} are known to post-date the documented training\n"
     "corpora. \\emph{External.}"),
]

POSTCUTOFF = r"""
\subsection{Data observed after the training corpora}
\label{sec:postcutoff}

Neither the simulation nor M4 can show how the foundation models behave on real data they cannot have
memorised. The monthly FRED-MD database \citep{mccracken2016fredmd}, in its August 2026 vintage, offers such
data: 101 of its 126 series are complete from 1990 to June 2026, and every method forecast January 2025 to
June 2026 (18 steps) from the 240 months to December 2024, raw levels without transformation. The evaluation
window post-dates the documented corpora of TimesFM-3 and TimesFM-2.5 (to November 2023) and the releases of
Chronos-Bolt; TiRex and Chronos-2 were released within it, and restricting the window to November 2025
onwards leaves AutoARIMA first and TimesFM-3 behind it (mean MASE 0.722 and 0.857). On this tier \textbf{TimesFM-3 is statistically level with the classical methods}
(Supporting Information, Table~S16): AutoARIMA has the lowest mean MASE (0.540), TiRex and the combination
follow (0.556), and TimesFM-3 has 0.607, with a median (0.426) close to AutoARIMA's (0.411); paired Wilcoxon
tests with Benjamini--Hochberg correction separate TimesFM-3 only from seasonal naive, which it beats, and a
Friedman test puts all nine other methods within the Nemenyi critical difference of the best mean rank.
TimesFM-3's mean is raised by a few series on which it extended a recent movement far beyond what followed,
such as the 2024 cuts in short-term interest rates. The tier is small and dominated by trending
macroeconomic levels, and it rules out memorised test values, not familiarity with the series' past.

"""


def main():
    for f in FILES:
        s = f.read_text(encoding="utf-8")
        for old, new in EDITS:
            if f.name == "K11_body.tex" and old.startswith("outliers leave these patterns"):
                continue   # the abstract lives in the main file only
            s = rep(s, old, new)
        a = s.index("\\input{tab_truncation}")
        b = a + len("\\input{tab_truncation}")
        s = s[:b] + "\n" + POSTCUTOFF + s[b:].lstrip("\n")
        f.write_text(s, encoding="utf-8")
    print("K13 applied")


if __name__ == "__main__":
    main()
