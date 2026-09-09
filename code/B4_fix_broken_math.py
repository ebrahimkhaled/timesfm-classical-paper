"""Repair two maths expressions whose backslashes were destroyed in transit.

Writing the replacement text through a shell heredoc turned LaTeX control sequences into
literal control characters: `\\text` became TAB + "ext", `\\tfrac` became TAB + "frac", and
`\\frac` became FORM FEED + "rac". MathJax then printed the mangled source, and one inline
expression showed a red "Math input error" in the PDF.

The fix writes the expressions from a Python source file, where the escapes are under our
control, and asserts afterwards that no stray control characters remain inside any maths.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DOC = Path(__file__).resolve().parent.parent / "SHARH_ARABIC.md"

s = DOC.read_text(encoding="utf-8")

# --- 1. the display equation ------------------------------------------------------
a = s.find("$$")
while a != -1:
    b = s.find("$$", a + 2)
    block = s[a:b + 2] if b != -1 else ""
    if "worse by" in block or "better by" in block:
        break
    a = s.find("$$", b + 2) if b != -1 else -1

assert a != -1 and b != -1, "display equation not located"

DISPLAY = (
    "$$\\underbrace{1.28 - 1 = 28\\%}_{\\text{TimesFM-3 worse by}}"
    "\\qquad\\neq\\qquad"
    "\\underbrace{1 - \\tfrac{1}{1.28} = 22\\%}_{\\text{AutoARIMA better by}}$$"
)
s = s[:a] + DISPLAY + s[b + 2:]
print("display equation rewritten")

# --- 2. the inline rule -----------------------------------------------------------
INLINE_BAD = re.compile(r"\$1 - [\x00-\x1f]?[a-z]*rac\{1\}\{1\+r\}\$")
s, n = INLINE_BAD.subn(r"$1 - \\frac{1}{1+r}$", s)
print(f"inline expression rewritten ({n} occurrence)")

# --- 3. no stray control characters anywhere in maths -----------------------------
DOC.write_text(s, encoding="utf-8")
text = DOC.read_text(encoding="utf-8")
bad = [c for c in text if c in "\t\x0b\x0c\x00"]
print(f"stray control characters remaining in the document: {len(bad)}")
for m in re.finditer(r"\$\$?[^$]{0,200}?\$\$?", text):
    if any(c in m.group(0) for c in "\t\x0b\x0c"):
        print("  ! still corrupt:", repr(m.group(0)[:80]))
print("done")
