"""Revision after supervisor review: the Croston table follows the title-plus-note convention.

Patches write_table() in 10_croston_d8.py so that the caption above the table is a title only
and the reading guide sits in a note beneath it, and adds a --table-only switch so the table
can be rebuilt from results/croston_d8_metrics.csv without re-running the baselines.
"""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parent / "10_croston_d8.py"

OLD_FLOAT = r'"\\begin{table}[t!]", "\\centering",'
NEW_FLOAT = r'"\\begin{table}[!htbp]", "\\centering", "\\begin{threeparttable}",'

CAPTION_START = r'"\\caption{Intermittent-demand baselines on D8, added post hoc.'
CAPTION_END = r'value in each row is in bold.}",'
NEW_CAPTION = r'"\\caption{Intermittent-demand baselines on the process D8 (post hoc analysis).}",'

OLD_SIZE = r'"\\footnotesize", "\\setlength{\\tabcolsep}{3pt}",'
NEW_SIZE = r'"\\footnotesize\\setlength{\\tabcolsep}{3pt}",'

OLD_END = r'lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]'
NEW_END = r'''lines += ["\\bottomrule", "\\end{tabular}",
              "\\begin{tablenotes}[flushleft]\\footnotesize",
              "\\item \\textit{Note:} Mean MASE and RMSSE over $h = 1,\\dots,12$ and 200 "
              "replications per length. Croston-opt is Croston's method with optimised "
              "smoothing parameters and Croston-SBA the Syntetos--Boylan approximation. "
              "Lower is better; the best value in each row is in bold.",
              "\\end{tablenotes}", "\\end{threeparttable}", "\\end{table}"]'''

OLD_MAIN = 'if __name__ == "__main__":\n    main()'
NEW_MAIN = '''if __name__ == "__main__":
    import sys as _sys
    if "--table-only" in _sys.argv:
        write_table(pd.read_csv(RES / "croston_d8_metrics.csv"))
        print("rewrote manuscript/tab_croston.tex from results/croston_d8_metrics.csv")
    else:
        main()'''


def main() -> None:
    s = SRC.read_text(encoding="utf-8")
    if "threeparttable" in s:
        print("10_croston_d8.py already revised")
        return
    for old, new in [(OLD_FLOAT, NEW_FLOAT), (OLD_SIZE, NEW_SIZE), (OLD_END, NEW_END),
                     (OLD_MAIN, NEW_MAIN)]:
        assert s.count(old) == 1, f"expected exactly one match for: {old[:60]}"
        s = s.replace(old, new, 1)
    a = s.find(CAPTION_START)
    b = s.find(CAPTION_END, a)
    assert a != -1 and b != -1, "Croston caption block not found"
    s = s[:a] + NEW_CAPTION + s[b + len(CAPTION_END):]
    SRC.write_text(s, encoding="utf-8")
    print("10_croston_d8.py: title-only caption, note beneath, --table-only switch")


if __name__ == "__main__":
    main()
