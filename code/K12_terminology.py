"""Terminology (author's preference, 2026-09-24): a combination of simulation factors is a "scenario",
the term of the ADEMP framework (Morris et al. 2019), not a "cell".

Run LAST, after the table generators (N7, K9, R4) and the SI builder (J12), because it edits the finished
.tex files; word boundaries protect words such as "excellent".
"""

import re
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "manuscript_jof"
RULES = [(r"\bcell-best\b", "scenario-best"), (r"\bper-cell\b", "per-scenario"),
         (r"\bcell[- ]by[- ]cell\b", "scenario by scenario"), (r"\bcell-winner\b", "scenario-winner"),
         (r"\bCells\b", "Scenarios"), (r"\bCell\b", "Scenario"), (r"\bcells\b", "scenarios"),
         (r"\bcell\b", "scenario")]


def scenario(text: str) -> str:
    for a, b in RULES:
        text = re.sub(a, b, text)
    return text


def main():
    files = [D / "timesfm_jof.tex", D / "supporting_information.tex"] + sorted(D.glob("tab_*.tex")) \
        + sorted(D.glob("si_*.tex"))
    n = 0
    for f in files:
        s = f.read_text(encoding="utf-8")
        t = scenario(s)
        if t != s:
            f.write_text(t, encoding="utf-8")
            n += 1
    print(f"terminology: {n} files updated")


if __name__ == "__main__":
    main()
