"""JoF version: abstract, parameter-justification sentence and seventh limitation after the
robustness study (Section sec:robustness)."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

ABSTRACT = r"""Time-series foundation models such as Google's TimesFM-3, a 330-million-parameter model released
in August 2026, forecast series they were never trained on. Whether such models should replace
classical methods such as ARIMA and exponential smoothing is difficult to settle on public
benchmarks, because only about 6\% of the datasets used to evaluate published models are absent
from every model's pre-training corpus. The aim of this study is to establish, under controlled
conditions, when TimesFM-3 should be preferred to classical forecasting methods. The evaluation data
are generated from nine known processes, so the foundation model cannot have seen the series and
the classical models are correctly specified by construction. Across 7\,200 series, four lengths
and a pre-registered protocol, neither family dominates. TimesFM-3 has the lowest mean absolute
scaled error (MASE) in 16 of 36 design cells and wins 113 of 132 significant pairwise comparisons;
only automatic ARIMA performs comparably. TimesFM-3 is never more than 1.31 times worse than the
best method in a cell, whereas every classical method is at least 2.2 times worse in some cell.
With four seasonal cycles observed, automatic ARIMA is 21--24\% more accurate. On intermittent
demand, TimesFM-3 outperforms six Croston-family methods under MASE but not under the root mean
squared scaled error. A robustness study in which every series draws its own parameters, and the
data have heavy tails, outliers or a seasonal period that must be estimated, preserves these
conclusions, with TimesFM-3 at most 1.51 times worse than the best method. In a feature space,
this randomised design covers 81\% of M4 monthly series, and results on 1\,000 of them agree.
TimesFM-3 is 103 times faster per series than automatic ARIMA, but its weights are licensed for
non-commercial use only. The findings are diagnostic baselines for the regimes examined rather
than universal prescriptions.
"""

OLD_JUSTIFY = r"""are recorded in the deviation log. The conclusions are conditional on these values, which is
listed among the limitations in \sectionref{sec:limitations}."""
NEW_JUSTIFY = r"""are recorded in the deviation log. Because the conclusions could depend on these particular
values, \sectionref{sec:robustness} repeats the comparison with parameters drawn at random from
wide ranges."""

SEVENTH = r"""Seventh, although \sectionref{sec:robustness} draws the parameters at random and relaxes three
assumptions, the processes themselves are fixed: nine univariate families at a single seasonal
period. The randomised design covers 81\% of the M4 monthly series in a four-feature space, which
leaves a fifth of real monthly series, and all series at other frequencies, outside the regions
studied. Coverage in four features is also a necessary rather than a sufficient condition for
similarity, since two series can share these features and differ in others."""


def main() -> None:
    s = P.read_text(encoding="utf-8")
    a0 = s.index("\\begin{abstract}\n") + len("\\begin{abstract}\n")
    a1 = s.index("\\end{abstract}")
    s = s[:a0] + ABSTRACT + s[a1:]
    assert s.count(OLD_JUSTIFY) == 1
    s = s.replace(OLD_JUSTIFY, NEW_JUSTIFY)
    i = s.index("Seventh, the results are conditional")
    j = s.index("\n\n", i)
    s = s[:i] + SEVENTH + s[j:]
    P.write_text(s, encoding="utf-8")
    print("abstract, justification and seventh limitation revised")


if __name__ == "__main__":
    main()
