"""Bring the arXiv metadata in line with the AJS preprint rule.

The AJS FAQ allows a preprint on condition that the paper states it is under review at AJS, and
asks that the preprint be replaced with the final AJS version once published. The metadata
generator therefore says "Under review" rather than "Submitted", tells the submitter to submit to
AJS before posting (the statement must be true on the day it goes up), and adds the replacement
step for after publication.
"""

from __future__ import annotations

import re
from pathlib import Path

A1 = Path(__file__).resolve().parent / "A1_arxiv_metadata.py"


def swap(s: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old[:60]!r}"
    return s[:matches[0].start()] + new + s[matches[0].end():]


def main() -> None:
    s = A1.read_text(encoding="utf-8")
    if "Under review at the Austrian Journal of Statistics." in s:
        print("A1 already carries the preprint wording")
        return
    s = swap(s, "Submitted to the Austrian Journal of Statistics.",
             "Under review at the Austrian Journal of Statistics.")
    s = swap(s, "## Before pressing submit\n1. Upload",
             "## Before pressing submit\n"
             "0. **Submit the paper to AJS first.** The preprint's first-page note and these Comments say it\n"
             "   is under review there, so both must be true on the day it is posted (AJS FAQ).\n"
             "1. Upload")
    s = swap(s, "so one identifier accrues all\n   the citations.",
             "so one identifier accrues all\n   the citations.\n"
             "5. When AJS publishes the paper, **Replace** this preprint with the final AJS-style version and\n"
             "   fill in Journal-ref and DOI, as the AJS FAQ asks.")
    A1.write_text(s, encoding="utf-8")
    print("A1: 'Under review' in Comments, submit-to-AJS-first step, replace-after-publication step")


if __name__ == "__main__":
    main()
