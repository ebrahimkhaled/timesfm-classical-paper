"""Move every table \\caption above its tabular, as AJS requires.

The rule, from the journal's own guidelines (template-guidelinesAJS.tex):

    "Graphics and tables must contain captions, above tables and below graphics (figures)."

and its example table places \\caption before \\begin{tabular}. Figures are already correct
(caption after the includegraphics); only tables needed moving. AJS states that manuscripts
ignoring its style are usually declined without review, so this is not cosmetic.

The transformation, per table environment: lift the \\caption{...} (brace-balanced, may span
lines) and its following \\label{...} out of wherever they sit, and reinsert them immediately
after \\centering. Idempotent -- a table whose caption already precedes \\begin{tabular} is
left alone.

Usage:  python code/91_fix_caption_placement.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAN = ROOT / "manuscript"
TARGETS = ["timesfm_vs_classical.tex", "tab_mase.tex", "tab_mape.tex", "tab_robust.tex",
           "tab_d8metrics.tex"]


def brace_span(s: str, start: int) -> int:
    """Index just past the balanced {...} beginning at s[start] == '{'."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced braces")


def fix_table(block: str) -> tuple[str, bool]:
    m = re.search(r"\\caption\s*\{", block)
    if not m:
        return block, False
    cap_start = m.start()
    cap_end = brace_span(block, block.index("{", m.start()))
    caption = block[cap_start:cap_end]

    rest = block[cap_end:]
    lab = re.match(r"\s*(\\label\{[^}]*\})", rest)
    label = lab.group(1) if lab else ""
    cut_end = cap_end + (lab.end() if lab else 0)

    tabular = block.find("\\begin{tabular}")
    if tabular != -1 and cap_start < tabular:
        return block, False  # already above the tabular

    stripped = block[:cap_start] + block[cut_end:]
    stripped = re.sub(r"\n\s*\n+", "\n", stripped)

    anchor = re.search(r"\\centering\s*\n", stripped)
    insert_at = anchor.end() if anchor else stripped.index("\n") + 1
    moved = caption + ("\n" + label if label else "") + "\n"
    return stripped[:insert_at] + moved + stripped[insert_at:], True


def main() -> None:
    total = 0
    for name in TARGETS:
        p = MAN / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        out, n = [], 0
        pos = 0
        for m in re.finditer(r"\\begin\{table\}.*?\\end\{table\}", text, re.S):
            out.append(text[pos:m.start()])
            fixed, changed = fix_table(m.group(0))
            out.append(fixed)
            n += changed
            pos = m.end()
        out.append(text[pos:])
        if n:
            p.write_text("".join(out), encoding="utf-8")
        print(f"  {name}: {n} table(s) fixed")
        total += n
    print(f"moved {total} caption(s) above their tabular")


if __name__ == "__main__":
    main()
