"""JoF revision: text fixes that do not depend on the new computations.

Each edit is tagged with the referee comment it answers (see submission/JoF_revision_tracker.md).
Idempotent: an edit whose target text is gone is reported and skipped, never applied twice.
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

EDITS = [
    # R3-M5: symmetric treatment of family-level familiarity
    ("R3-M5", r"""inspection. If it does, it would be expected to help TimesFM-3 most on D1--D5, the processes where
a classical model is correctly specified and where the classical methods win; under that
conjecture the gap measured there would understate rather than overstate the accuracy TimesFM-3
gives up. The conjecture is stated for transparency and no conclusion relies on it.""",
     r"""inspection. Its direction cannot be assumed either. Synthetic pre-training corpora for
time-series models commonly contain autoregressive and seasonal structure, which resembles
D1--D5, but also level shifts, piecewise trends and sparse spikes, which resemble D6--D8, so
familiarity could favour TimesFM-3 anywhere in the design. No conclusion of this paper relies on
its direction."""),
    ("R3-M5", r"""the leakage documented by \citet{meyer2025leakage} is impossible by construction. What the design""",
     r"""realisation-level leakage of the kind documented by \citet{meyer2025leakage} is impossible. What the design"""),
    # R1-m11: "deliberately strong" overstates
    ("R1-m11", r"""The classical side of the comparison is deliberately strong. AutoARIMA and AutoETS follow the""",
     r"""The classical side of the comparison uses standard automatic methods. AutoARIMA and AutoETS follow the"""),
    # R1-m4: consistent rounding of Theta on D4 n = 200 (4.155)
    ("R1-m4", r"""records 4.15 at $n = 200$ against AutoARIMA's 0.89.""",
     r"""records 4.16 at $n = 200$ against AutoARIMA's 0.89."""),
    # R3-m2: wording of D8 and D9
    ("R3-m2", r"""process D8 (Poisson arrivals) and the GARCH process D9 (heavy-tailed innovations with time-varying volatility).""",
     r"""process D8 (Bernoulli demand occurrence with Poisson demand sizes) and the GARCH process D9
(conditionally Gaussian innovations with time-varying volatility, hence unconditionally
heavy-tailed)."""),
    # R3-m4: licence wording
    ("R3-m4", r"""TimesFM-3 as released is unavailable at any accuracy}""",
     r"""TimesFM-3 is not licensed for that use as released}"""),
    # R3-m11: cores
    ("R3-m11", r"""on an NVIDIA GTX 1660 Ti with a 24-core CPU and 32\,GB of memory; the loaded TimesFM-3""",
     r"""on an NVIDIA GTX 1660 Ti with a 24-core CPU and 32\,GB of memory (parallel classical runs use
$22 = 24 - 2$ worker processes, leaving two cores for the operating system); the loaded TimesFM-3"""),
]


def main():
    s = P.read_text(encoding="utf-8")
    for tag, old, new in EDITS:
        n = s.count(old)
        if n == 1:
            s = s.replace(old, new)
            print(f"{tag}: applied")
        elif new in s:
            print(f"{tag}: already applied")
        else:
            print(f"{tag}: TARGET NOT FOUND ({n})")
    P.write_text(s, encoding="utf-8")


if __name__ == "__main__":
    main()
