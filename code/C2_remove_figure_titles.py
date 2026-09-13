"""Revision after supervisor review: remove the titles baked into the figure images.

Each figure carried a matplotlib suptitle ("Figure 1: ...") above the plot, duplicating the
LaTeX caption beneath it. The baked-in numbers were also wrong for two figures, because the
horizon and coverage figures appear in the manuscript in the opposite order to their file
names. The caption is the only title a journal figure should have, so the suptitle calls are
removed from the generator and the four figures are rebuilt.
"""

from __future__ import annotations

from pathlib import Path

SRC = Path(__file__).resolve().parent / "06_figures.py"

SUPTITLES = [
    '    fig.suptitle("Figure 1: One realisation of each data-generating process "\n'
    '                 "(n = 96; held-out horizon in colour)", fontsize=9, y=1.01)\n',
    '    fig.suptitle("Figure 2: Accuracy of TimesFM-3 relative to the best classical method",\n'
    '                 fontsize=9, y=1.02)\n',
    '    fig.suptitle("Figure 3: Interval reliability, averaged over all nine processes",\n'
    '                 fontsize=9, y=1.03)\n',
    '    fig.suptitle("Figure 4: Accuracy by horizon, split by whether a classical model is correct",\n'
    '                 fontsize=9, y=1.03)\n',
]


def main() -> None:
    s = SRC.read_text(encoding="utf-8")
    removed = 0
    for block in SUPTITLES:
        if block in s:
            s = s.replace(block, "", 1)
            removed += 1
    assert "suptitle" not in s, "a suptitle call remains in 06_figures.py"
    SRC.write_text(s, encoding="utf-8")
    print(f"removed {removed} in-image title(s); none remain")


if __name__ == "__main__":
    main()
