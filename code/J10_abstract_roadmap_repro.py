"""JoF revision: abstract, roadmap, and reproducibility details after the extended evidence."""

import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

ABSTRACT = r"""Time-series foundation models such as Google's TimesFM-3 forecast series they were never
trained on. Whether they should replace classical methods such as ARIMA and exponential smoothing is
difficult to settle on public benchmarks, because few benchmark datasets are absent from every
model's pre-training corpus. This exploratory study describes, under controlled conditions, how
TimesFM-3 behaves relative to classical methods and in which regimes it may be preferred. The
evaluation data are generated from nine known processes, so the model cannot have seen the series.
Across 7\,200 series and a pre-registered protocol, neither family dominates. TimesFM-3 is never more
than 1.31 times worse than the best method in a cell (95\% bootstrap interval 1.28 to 1.36), whereas
every classical method is at least 2.2 times worse somewhere; with four seasonal cycles observed,
automatic ARIMA is 21--24\% more accurate. This robustness is specific to TimesFM-3: TimesFM-2.5 and
Chronos-Bolt are no more robust than automatic ARIMA, and when the classical methods must estimate the
seasonal period, their worst case is level with that of TimesFM-3. On intermittent demand the median
forecast of TimesFM-3 is no better on the mean absolute scaled error than forecasting zero; its
advantage lies in its predictive distribution, whose pinball loss is about 15\% lower. Randomised
parameters, heavy-tailed noise and outliers leave these findings intact within Monte Carlo error. On
the official test period of 1\,000 M4 monthly series, TimesFM-3 is one of six statistically
indistinguishable leading methods, and with only 24 observations of history it is 11\% more accurate
than automatic ARIMA. Because TimesFM-3 is a black box, the study characterises its behaviour, not
the reasons for it, and its weights are licensed for non-commercial use only."""

ROADMAP_OLD = r"""\sectionref{sec:results} reports its results. \sectionref{sec:robustness} examines how"""
ROADMAP_NEW = r"""\sectionref{sec:results} reports its results. \sectionref{sec:extended} extends the
evaluation with Monte Carlo uncertainty, stronger classical benchmarks, two further foundation
models, checks on the configuration of TimesFM-3 and a re-examination of intermittent demand.
\sectionref{sec:robustness} examines how"""

REPRO_OLD = r"""be re-run alone and the results reproduced without repeating the whole computation."""
REPRO_NEW = r"""be re-run alone and the results reproduced without repeating the whole computation.
TimesFM-3 was run in 32-bit floating point with the package defaults of \pkg{timesfm} 3.0.1 and no
random sampling; rerunning two cells (D1 at $n = 24$ and D8 at $n = 96$) on the same machine
reproduced the stored quantiles exactly, although results on other hardware may differ in the last
digits because floating-point reductions on a GPU are not associative.
TimesFM-2.5 (\pkg{timesfm}, maximum context 512, the configuration of its model card) and
Chronos-Bolt (\pkg{chronos-forecasting} 2.3.2) were run in the same way."""


def main():
    s = P.read_text(encoding="utf-8")
    m = re.search(r"\\abstract\[Abstract\]\{(.*?)\}\n\n\\maketitle", s, re.S)
    assert m, "abstract not found"
    s = s[:m.start(1)] + ABSTRACT + s[m.end(1):]
    assert s.count(ROADMAP_OLD) == 1
    s = s.replace(ROADMAP_OLD, ROADMAP_NEW)
    assert s.count(REPRO_OLD) == 1
    s = s.replace(REPRO_OLD, REPRO_NEW)
    P.write_text(s, encoding="utf-8")
    print("abstract, roadmap and reproducibility updated;", len(ABSTRACT.split()), "words in abstract")


if __name__ == "__main__":
    main()
