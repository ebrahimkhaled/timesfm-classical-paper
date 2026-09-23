"""Length pass, part 8 (author request):

1. The practical-recommendation table (Table 11) becomes hedged prose: a table of rules reads as a
   stronger claim than an exploratory simulation supports.
2. The full cell-mean MASE table (Table 3) moves to the Supporting Information (Table S9); Figure 2
   carries the comparison in the main text and the key cell values are quoted in the prose.
The wording already reflects the second referee round (D8 history benchmarks, interval score).
"""

from pathlib import Path

D = Path(__file__).resolve().parent.parent / "manuscript_jof"
P = D / "timesfm_jof.tex"

RECS = r"""\subsection{Practical recommendations}
\label{sec:recommendations}

The recommendations below are conditional on the processes, lengths and horizon examined. They describe how
the methods behaved here and are offered as diagnostic starting points to be checked on the user's own
data, not as rules; several rest on considerations outside the accuracy comparison, and where the evidence
does not favour one family, more than one option is named.

\textbf{Many heterogeneous series without per-series tuning.} This is where TimesFM-3's robustness mattered
most in this design: it won most significant comparisons against every classical method except AutoARIMA
and was never far from the best method of a cell. Where a model can be identified for a single series, the
classical route loses little---against AutoARIMA the comparisons split 11--9---and keeps parameters,
diagnostics and interval theory that can be explained and audited.

\textbf{Seasonal series.} With at least four observed cycles, AutoARIMA was 21--24\% more accurate than
TimesFM-3 on the seasonal ARIMA process D4 and 4--12\% on the ETS process D5, and seasonal naive was also
ahead on D4. With two cycles the automatic classical methods fell back to non-seasonal models and failed,
and seasonal naive, or TimesFM-3, was the safer choice.

\textbf{Intermittent demand.} Simple benchmarks built from the history were as good as anything tested:
the empirical deciles of the history gave the lowest pinball loss, and its mean, like the Croston family,
the lowest RMSSE. TimesFM-3 came close on both only with a suitable read-out of its deciles, and its median
forecast was no better than forecasting zero. These results come from a process that is independent over
time, the case most favourable to history-based benchmarks.

\textbf{Intervals, cost and licence.} TimesFM-3 had the best 80\% interval score in 22 of the 36 cells,
including every length after a structural break (D6); on M4, however, its 80\% intervals under-covered
(0.765 against 0.801 for the classical combination on the rolling origins), so interval quality on real
data should be checked rather than assumed. On the hardware used, TimesFM-3 on a GPU was faster end to end
than the parallelised classical suite, a comparison dominated by AutoARIMA. For commercial deployment the
licence decides before accuracy does: TimesFM-3's weights are non-commercial, and the Apache-2.0
TimesFM-2.5 was less robust in the simulation (worst ratio 2.18) though level with TimesFM-3 on M4.

"""


def main():
    s = P.read_text(encoding="utf-8")

    # 1. Recommendations as prose.
    a = s.index("\\subsection{Practical recommendations}")
    b = s.index("\\subsection{Limitations}")
    s = s[:a] + RECS + s[b:]

    # 2. Cell-mean table to the SI.
    s = s.replace("\n\\input{tab_mase}\n", "\n", 1)
    s = s.replace(
        "\\tableref{tab:mase} reports mean MASE over $h = 1, \\dots, 12$ for the 7\\,200 series, and\n"
        "\\figureref{fig:ratio} shows TimesFM-3 relative to the best classical method in each cell.",
        "\\figureref{fig:ratio} shows TimesFM-3 relative to the best classical method in each of the 36\n"
        "(process, length) cells; the mean MASE of every method in every cell, over $h = 1, \\dots, 12$ and 200\n"
        "replications, is given in Table~S9 of the Supporting Information.", 1)
    assert "tab:mase" not in s and "tab:decision" not in s
    P.write_text(s, encoding="utf-8")
    # The SI side (Table S9) is built by J12_supporting_information.py.
    print("recommendations as prose; tab_mase removed from the main text (rerun J12 for the SI)")


if __name__ == "__main__":
    main()
