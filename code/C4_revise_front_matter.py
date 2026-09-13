"""Revision after supervisor review, part A: preamble, abstract and introduction.

Addresses: the aim of the paper stated explicitly in the abstract and the introduction; first-
person plural removed from a sole-authored paper; a statement of the paper's structure at the
end of the introduction; the technical description of TimesFM-3 moved out of the introduction
into its own section (added in part B); academic register throughout.

Matching ignores line wrapping: every run of whitespace in an old passage matches any run of
whitespace in the manuscript, and every replacement must match exactly once.
"""

from __future__ import annotations

import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "manuscript" / "timesfm_vs_classical.tex"


def swap(s: str, old: str, new: str) -> str:
    pattern = r"\s+".join(re.escape(tok) for tok in old.split())
    matches = list(re.finditer(pattern, s))
    assert len(matches) == 1, f"{len(matches)} matches for: {old.split()[:8]}"
    m = matches[0]
    return s[:m.start()] + new.strip("\n") + s[m.end():]


PREAMBLE_OLD = r"""\usepackage{booktabs}
\usepackage{amsmath}"""
PREAMBLE_NEW = r"""\usepackage{booktabs}
\usepackage{threeparttable}
\usepackage{amsmath}"""

ABSTRACT_NEW = r"""
\Abstract{%
Time-series foundation models forecast series they were never trained on, and Google's
TimesFM-3, a 330-million-parameter model released in August 2026, is the most recent example.
Whether such models should replace classical methods such as ARIMA and exponential smoothing in
applied work cannot be settled on public benchmarks, because only about 6\% of the datasets used
to evaluate published foundation models are absent from every model's pre-training corpus. The
aim of this study is to establish, under controlled conditions, when TimesFM-3 should be
preferred to classical forecasting methods and when it should not. The evaluation data are
generated from nine known processes, so that the foundation model cannot have seen the series
and the classical models are correctly specified by construction. Across 7\,200 series, four
series lengths and a pre-registered protocol, neither family dominates. TimesFM-3 has the lowest
mean absolute scaled error (MASE) in 16 of 36 design cells and the classical methods in 20, but
those 20 are divided among five different methods, and TimesFM-3 wins 113 of 132 significant
pairwise comparisons; only automatic ARIMA performs comparably. TimesFM-3 is never more than
$1.31\times$ worse than the best method in any cell, whereas every classical method is at least
$2.2\times$ worse in some cell. On strongly seasonal series with at least four observed cycles,
automatic ARIMA is 21--24\% more accurate. On intermittent demand, TimesFM-3 is more accurate
than six purpose-built Croston-family methods under MASE but less accurate under the root mean
squared scaled error, because absolute and squared losses reward different functionals of a
distribution that is 70\% zeros. Estimability proves more decisive than correct specification:
with two seasonal cycles, the correctly specified exponential smoothing model had a MASE 2.7 times
that of the seasonal naive method. An analysis of 1\,000 monthly series from the M4 competition
reproduces the pattern. TimesFM-3 is also 103 times faster per series than automatic ARIMA, but
its weights are licensed for non-commercial use only.
}
"""

REPLACEMENTS = [
    # ---- introduction, paragraph 1: the model is introduced briefly; details go to Section 2
    (r"""On 31 August 2026 Google Research released TimesFM-3, the third generation of its
time-series foundation model \citep{timesfm3blog}. It is a decoder-only transformer with
330 million parameters, pre-trained on more than a trillion time points, and it is the first
model in the family trained natively for \emph{multivariate} forecasting: it consumes several
related series together through alternating causal-temporal and full-variate attention
layers, accepts past and past-future covariates, and emits an entire forecast horizon in a
single non-autoregressive forward pass. Its authors report that it takes the top average rank
among pre-trained foundation models on three public benchmarks, for both point and
probabilistic accuracy.""",
     r"""Time-series foundation models are large neural networks that are pre-trained on many series
and then applied to new series without task-specific training. On 31 August 2026 Google Research
released TimesFM-3, the third generation of its TimesFM family \citep{timesfm3blog}: a
330-million-parameter decoder-only transformer, the first member of the family designed for
\emph{multivariate} forecasting, which its developers report as the top-ranked pre-trained model
on three public benchmarks for both point and probabilistic accuracy. \sectionref{sec:timesfm}
describes the model in detail."""),

    # ---- paragraph 2
    (r"""For a practising forecaster the interesting question is not whether such a model tops a
leaderboard. It is narrower and more useful: \emph{given the series actually in front of me,
should I use it, or should I use ARIMA?} A 330-million-parameter network and a three-parameter
state-space model are not merely two points on an accuracy scale. They differ in what they
cost to run, in whether their parameters mean anything, in whether their intervals can be
justified from theory, and---as \sectionref{sec:licence} discusses---in whether they may
lawfully be used at all for a given purpose.""",
     r"""For applied forecasting, the relevant question is not whether such a model ranks first on a
leaderboard but whether it should be used, in preference to a classical method such as ARIMA, for
the series at hand. The two families also differ in more than accuracy: in computational cost, in
the interpretability of their parameters, in the theoretical basis of their prediction intervals
and, as \sectionref{sec:licence} discusses, in the terms under which they may be used."""),

    # ---- paragraph 3, opening sentence
    (r"""The published evidence is not well suited to answering that question, for a reason that has
become difficult to ignore.""",
     r"""Published benchmark evidence is poorly suited to answering this question."""),
    (r"""Compounding this, foundation-model papers have repeatedly
been criticised""",
     r"""In addition, foundation-model evaluations have been
criticised"""),

    # ---- paragraph 4
    (r"""This paper takes the one route that closes both objections at once: \textbf{it generates its
own data}. Under a known data-generating process (DGP), two things become true simultaneously
that are never true on a public benchmark. First, the foundation model provably has not seen
the series, because the series did not exist until the experiment ran. Second---and this is
the part that gives the comparison its edge---the classical model can be made
\emph{correctly specified by construction}. When the data really are ARIMA(1,1,1) with drift,
AutoARIMA is not an approximation of the truth; it is the truth, up to parameter estimation.""",
     r"""This study addresses both objections by generating its own evaluation data. Under a known
data-generating process (DGP), two conditions hold that cannot hold on a public benchmark.
First, the foundation model cannot have seen the series, because the series did not exist before
the experiment was run. Second, the classical model can be made \emph{correctly specified by
construction}: when the data are generated by an ARIMA(1,1,1) process with drift, the model
family searched by AutoARIMA contains the true process, and only its parameters remain to be
estimated."""),

    # ---- paragraph 5, opening sentence
    (r"""One distinction must be drawn carefully here, because the paper's central claim depends on it.""",
     r"""One distinction is essential to the interpretation of the results."""),

    # ---- paragraph 6
    (r"""That is not a flaw in the design; it is the boundary of what the design can claim, and it cuts
in a specific direction.""",
     r"""This is a boundary of what the design can establish rather than a flaw, and its effect has a
predictable direction."""),
    (r"""Read strictly, then,
the results below bound how much a foundation model gives up on classical home ground from
\emph{below}: with a less ARMA-fluent model the gap would be wider, not narrower.""",
     r"""The results
therefore give a lower bound on the accuracy a foundation model gives up where a classical model
is correctly specified: for a model less familiar with ARMA-type structure the gap would be wider,
not narrower."""),

    # ---- paragraph 7
    (r"""That turns a vague question into a sharp one. Instead of asking which method is better in
general, we can ask:""",
     r"""The design therefore replaces the general question of which method is better with two specific
questions:"""),

    # ---- paragraph 8
    (r"""We answer both across nine DGPs, four series lengths from 24 to 200 observations, three
forecast horizons and 7\,200 simulated series, comparing TimesFM-3""",
     r"""Both questions are addressed across nine DGPs, four series lengths from 24 to 200
observations, three forecast horizons and 7\,200 simulated series, by comparing TimesFM-3"""),

    # ---- paragraph 9: the aim, then the structure of the paper
    (r"""We make no claim to a new estimator, test or theory. This is a comparative simulation study,
and it is framed as one. Its contribution is evidential: a clean measurement of a trade-off
that practitioners currently have to guess at, together with an explicit statement of the
conditions under which each answer holds.""",
     r"""The aim of the study is therefore to determine, under controlled conditions, when TimesFM-3
should be preferred to classical forecasting methods and when it should not. It proposes no new
estimator, test or theory. Its contribution is evidential: a controlled measurement of the
trade-off between the two families, together with an explicit statement of the conditions under
which each is preferable.

The remainder of the paper is organised as follows. \sectionref{sec:timesfm} describes
TimesFM-3. \sectionref{sec:design} sets out the design of the simulation study, and
\sectionref{sec:results} reports its results. \sectionref{sec:realdata} applies the comparison to
monthly series from the M4 competition. \sectionref{sec:operational} examines computational cost,
licensing, interpretability and the basis of prediction intervals. \sectionref{sec:discussion}
assesses the pre-registered hypotheses and presents practical recommendations and limitations,
and \sectionref{sec:conclusion} concludes. Computational details are given in
\sectionref{sec:repro}, and results under the mean absolute percentage error in
\appendixref{app:mape}."""),

    # ---- related work
    (r"""\subsection{Related work and this paper's position}""",
     r"""\subsection{Related work}
\label{sec:related}"""),
    (r"""Our study is complementary to \citet{adler2026calibrated} rather than a repeat of it, in three
respects. Their evidence comes from public datasets and therefore inherits the contamination
problem; ours is generated. They summarise reliability with calibration \emph{metrics}; we
pair interval reliability with pre-registered \emph{hypothesis tests} on accuracy differences,
with multiplicity control. And their study predates TimesFM-3, the first natively multivariate
member of the family.""",
     r"""The present study complements that of \citet{adler2026calibrated} in three respects. Their
evidence comes from public datasets and therefore inherits the contamination problem, whereas the
data here are generated. They summarise reliability with calibration \emph{metrics}, whereas this
study combines interval coverage with pre-registered \emph{hypothesis tests} on accuracy
differences, with control of multiplicity. Finally, their study predates TimesFM-3, the first
natively multivariate member of the family."""),
    (r"""with the pitfalls catalogued by
\citet{hewamalage2023evaluation} treated as constraints rather than suggestions.""",
     r"""and the design avoids the
evaluation pitfalls catalogued by \citet{hewamalage2023evaluation}."""),
]


def main() -> None:
    s = TEX.read_text(encoding="utf-8")
    if "\\label{sec:related}" in s:
        print("part A already applied")
        return
    s = swap(s, PREAMBLE_OLD, PREAMBLE_NEW)
    a, b = s.index("\\Abstract{%"), s.index("\\Keywords{")
    s = s[:a] + ABSTRACT_NEW.strip("\n") + "\n\n" + s[b:]
    for old, new in REPLACEMENTS:
        s = swap(s, old, new)
    TEX.write_text(s, encoding="utf-8")
    print(f"part A applied: preamble, abstract, {len(REPLACEMENTS)} introduction edits")


if __name__ == "__main__":
    main()
