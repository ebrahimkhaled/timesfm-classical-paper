"""Rebuild the 'Figure legends' list (JoF: legends beneath each figure AND listed in the text).

Regenerated from the captions in the manuscript, in order of appearance, so the list cannot drift
from the figures. Run after any change to a figure caption.
"""

import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"


def caption_of(block: str) -> str:
    i = block.index("\\caption{") + len("\\caption{")
    depth, j = 1, i
    while depth:
        depth += {"{": 1, "}": -1}.get(block[j], 0)
        j += 1
    return " ".join(block[i:j - 1].split())


def main():
    s = P.read_text(encoding="utf-8")
    head = s[:s.index("\\section*{Figure legends}")] if "\\section*{Figure legends}" in s else \
        s[:s.index("\\end{document}")]
    figs = re.findall(r"\\begin\{figure\}.*?\\end\{figure\}", head, re.S)
    items = [f"\\item[Figure {i}.] {caption_of(f)}" for i, f in enumerate(figs, 1)]
    block = "\\section*{Figure legends}\n\n\\begin{description}\n" + "\n".join(items) + \
        "\n\\end{description}\n\n"
    s = head.rstrip() + "\n\n" + block + "\\end{document}\n"
    P.write_text(s, encoding="utf-8")
    print(f"{len(items)} figure legends listed")


if __name__ == "__main__":
    main()
