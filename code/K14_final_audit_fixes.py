"""Corrections from the final pre-submission audit (2026-09-24). Text only; every number was re-checked
against results/ (robust_response.csv, robust_boot.csv, table_tests.csv, h48/, post_cutoff/, round3/) and the
M4 sample (data/m4_monthly_sample_1000.parquet includes the official test period, so rolling origin 0 is
that period; eligibility was >= 120 training observations, MIN_LEN in 07_realdata.py).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "manuscript_jof" / "timesfm_jof.tex"
BODY = ROOT / "code" / "K11_body.tex"


def rep(s, old, new):
    pat = r"\s+".join(re.escape(w) for w in old.split())
    s2, k = re.subn(pat, lambda m: new, s, count=1)
    return s2, k


E = [
    # 1 M4 sample and origins
    ("A seeded sample of 1\\,000 series is drawn from the 32\\,581 M4 Monthly series with at least 138 training "
     "observations, enough for a context of 120 and the 18-month horizon.",
     "A seeded sample of 1\\,000 series is drawn from the 32\\,581 M4 Monthly series with at least 120 training\n"
     "observations."),
    ("Each series is evaluated at up to three origins 12 months apart with M4's horizon $h = 18$ (2\\,932 windows);",
     "Each series is evaluated at up to three origins 12 months apart with M4's horizon $h = 18$ (2\\,932\n"
     "windows), the latest being the official test period, forecast from the training series;"),
    ("Rolling origins cut from the training data cannot be placed against published M4 results, so the same "
     "series were also forecast for the official 18-month test period from their full histories and scored as in M4,",
     "To place the results against the published M4 results, the official 18-month test period, the latest of\n"
     "the three origins above, was scored as in M4,"),
    # 2 departures count
    ("The archive holds a dated log of the fourteen departures", "The archive holds a dated log of the fifteen departures"),
    # 3 response surface
    ("each doubling of $n$ moves the ratio against TimesFM-3 by 20\\% on D4 and 11\\% on D5, and in its favour on D6 "
     "and D8. Outliers favour TimesFM-3 on the seasonal processes (14\\% and 10\\%); the other version effects are at "
     "most 0.09 in absolute value.",
     "each doubling of $n$ moves the ratio against TimesFM-3 by about 18\\% on D4 and 10\\% on D5, and in its favour\n"
     "on D6 and D8. Outliers, alone or with heavy tails, favour TimesFM-3 on the seasonal processes (14\\% and 10\\%;\n"
     "14\\% and 8\\%)."),
    ("explain little of the per-series variation ($R^2 \\leq 0.26$).", "explain little of the per-series variation ($R^2 \\leq 0.23$)."),
    # 4 H = 48: only three FMs run
    ("at 48 steps, TimesFM-3 and the other foundation models forecast a decline on a saturating process whose level "
     "stays flat, and automatic ARIMA has the smaller worst case elsewhere.",
     "at steps 25 to 48, the three foundation models run at that horizon forecast a decline on a saturating process\n"
     "whose level stays flat, and automatic ARIMA has the smaller worst case elsewhere."),
    ("On D7 at $n = 200$ every foundation model forecasts a decline", "On D7 at $n = 200$ all three foundation models forecast a decline"),
    ("(1.41 against 1.80, D7 excluded), although TimesFM-3 remains closer to the best method in the median scenario "
     "(1.075 against 1.109).",
     "(1.41 against 1.80, D7 excluded), although TimesFM-3 remains closer to the best method in the median scenario\n"
     "(1.064 against 1.092, D7 excluded)."),
    ("At 48 steps AutoARIMA has the smaller worst case; every foundation model forecasts a decline on a plateau",
     "At steps 25--48 AutoARIMA has the smaller worst case; the three foundation models run there forecast a decline on a plateau"),
    ("it holds for short horizons only: at 48 steps AutoARIMA has the smaller worst case and every foundation model "
     "forecasts a decline on a saturated process.",
     "it holds for short horizons only: at steps 25 to 48 AutoARIMA has the smaller worst case and the three\n"
     "foundation models run there forecast a decline on a saturated process."),
    ("and every foundation model forecast a decline on a process that had levelled off,",
     "and the three foundation models run there forecast a decline on a process that had levelled off,"),
    # 5 bootstrap bound
    ("(bootstrap intervals up to about 1.75)", "(bootstrap intervals up to about 1.83)"),
    # 6 straddle
    ("(11 comparisons won, 9 lost): most intervals against it straddle 1, and the scenarios where AutoARIMA is ahead "
     "are the seasonal processes from $n = 48$,",
     "(11 comparisons won, 9 lost): 16 of the 36 intervals against it straddle 1, and AutoARIMA's wins are mainly\n"
     "on the seasonal processes from $n = 48$,"),
    # 7 real-data section title and roadmap
    ("\\section{Application to M4 monthly data}", "\\section{Application to real data}"),
    ("\\sectionref{sec:realdata} the application to M4 and", "\\sectionref{sec:realdata} the application to M4 and to data\nobserved after the training corpora, and"),
    ("The real-data tier is therefore secondary evidence; its official-test and truncation analyses are post hoc.",
     "The M4 tier is therefore secondary evidence; its official-test and truncation analyses are post hoc, and\n"
     "\\sectionref{sec:postcutoff} adds, post hoc, data observed after the documented training corpora."),
    # 8 post-hoc labelling
    ("Everything in \\sectionref{sec:posthoc} and the official-test and truncation analyses of \\sectionref{sec:realdata} "
     "were added afterwards and are logged as departures.",
     "Everything in \\sectionref{sec:posthoc} and \\sectionref{sec:realdata}, except the rolling-origin evaluation\n"
     "of \\sectionref{sec:m4results}, was added afterwards and is logged as a departure."),
    ("rather than deposited with an external registry, so its only external timestamp postdates the forecasts, and the "
     "analyses of \\sectionref{sec:posthoc} and the official-test and truncation analyses of \\sectionref{sec:realdata} "
     "are post hoc; only the data of \\sectionref{sec:postcutoff} are known to post-date the documented training corpora.",
     "rather than deposited with an external registry, so its only external timestamp postdates the forecasts.\n"
     "Everything in \\sectionref{sec:posthoc} and \\sectionref{sec:realdata} except the rolling-origin evaluation is\n"
     "post hoc. Only the data of \\sectionref{sec:postcutoff} are known to post-date the documented training\n"
     "corpora."),
    # 9 Table 1
    ("per series from wide ranges in four versions", "per series from wide ranges in five versions"),
    # 13 familiarity
    ("Because TimesFM-3 is pre-trained partly on synthetic series, its advantage could reflect familiarity with some "
     "process families rather than their difficulty. At matched difficulty (spectral entropy and length), its "
     "advantage over AutoARIMA is about 5\\% to 6\\% larger",
     "Because TimesFM-3 is pre-trained partly on synthetic series, its advantage could\n"
     "reflect familiarity with some process families rather than their difficulty. In the randomised design with\n"
     "Gaussian innovations, at matched difficulty (spectral entropy and length), its advantage over AutoARIMA is\n"
     "about 4\\% to 6\\% larger"),
    ("which is consistent with an effect of familiarity but does not establish one.",
     "which is consistent with an effect of familiarity but does not establish one: on D6--D8 AutoARIMA is also\n"
     "misspecified by construction, which predicts the same shift."),
    # 14
    ("the classical route loses little against AutoARIMA and keeps", "TimesFM-3 gains little over AutoARIMA, which keeps"),
    # 15
    ("from the series at hand, not whether it is correctly specified.", "from the series at hand, not only whether it is correctly specified."),
    # 17 FRED-MD wording
    ("onwards leaves AutoARIMA first and TimesFM-3 behind it (mean MASE 0.722 and 0.857).",
     "onwards leaves AutoARIMA first (mean MASE 0.722) and puts TimesFM-3 behind every method except the naive\n"
     "benchmarks (0.857)."),
    ("Friedman test puts all nine other methods within the Nemenyi critical difference of the best mean rank.",
     "Friedman test puts every method except seasonal naive within the Nemenyi critical difference of the best\n"
     "mean rank."),
    # 18, 19
    ("and 0.35 to 0.44 on D5 at every length", "and 0.34 to 0.44 on D5 at every length"),
    ("(95\\% interval $-0.01$ to 0.13)", "(95\\% interval $-0.005$ to 0.125)"),
    # 20, 21
    ("on average across lengths closer to nominal than any other method,",
     "with the smallest mean absolute deviation from nominal across lengths of any method,"),
    ("the classical methods over-cover from $n = 96$ \\\\", "the classical methods reach or slightly exceed nominal from $n = 96$ \\\\"),
    ("the classical methods under-cover at $n = 24$ and over-cover from $n = 96$.}",
     "the classical methods under-cover at $n = 24$ and reach or exceed nominal from $n = 96$.}"),
    # 23
    ("TimesFM-3 is never more than 1.31 times worse than the best method in a scenario, whereas every classical "
     "method is at least 2.2 times worse somewhere;",
     "TimesFM-3's error is never more than 1.31 times that of the best method in a scenario, whereas every classical\n"
     "method's is at least 2.2 times somewhere;"),
    ("its worst case, never more than 1.31 times the best method in a scenario against at least 2.2 times",
     "its worst case, an error never more than 1.31 times that of the best method in a scenario against at least\n"
     "2.2 times"),
    # 24
    ("outliers, alone or together, leave these patterns qualitatively unchanged;",
     "outliers, alone or together, leave these patterns qualitatively unchanged, although testing for\n"
     "seasonality narrows the classical worst case;"),
    # 25
    ("the classical side wins only where the model is also estimable (D4, D5 at $n \\geq 48$)",
     "the classical side wins mainly where the model is also estimable (D4, D5 at $n \\geq 48$)"),
    # 12 ethics and data availability
    ("Not applicable; the study uses simulated data and the publicly available M4 competition data, and",
     "Not applicable; the study uses simulated data and publicly available data (M4 competition data and\n"
     "forecasts, FRED-MD), and"),
    ("with the seeded 1\\,000-series sample included.",
     "with the seeded 1\\,000-series sample included, and the FRED-MD database (August 2026 vintage)\n"
     "\\citep{mccracken2016fredmd} and the published M4 forecasts, which are publicly available and are fetched\n"
     "by the code rather than archived."),
    # 16 smooth version
    ("\\proglang{R}~4.4.1 with \\pkg{forecast}~9.0.2 for the cross-check,",
     "\\proglang{R}~4.4.1 with \\pkg{forecast}~9.0.2 and \\pkg{smooth}~4.5.2 for the cross-check and iETS,"),
]


def main():
    s = MAIN.read_text(encoding="utf-8")
    b = BODY.read_text(encoding="utf-8")
    missing = []
    for old, new in E:
        s, k = rep(s, old, new)
        if k == 0:
            missing.append(old[:60])
        b, _ = rep(b, old, new)
    MAIN.write_text(s, encoding="utf-8")
    BODY.write_text(b, encoding="utf-8")
    print("applied", len(E) - len(missing), "of", len(E))
    for m in missing:
        print("  NOT FOUND:", m)


if __name__ == "__main__":
    main()
