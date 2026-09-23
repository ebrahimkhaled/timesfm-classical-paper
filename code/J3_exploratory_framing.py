"""JoF version: exploratory framing (author's decision, 2026-09-23).

TimesFM-3 is a black box: the design can measure how its forecasts behave under known conditions,
not why. The abstract, introduction, results, discussion and conclusion are revised so that
(i) the study is described as exploratory, (ii) explanations of TimesFM-3's behaviour are marked
as interpretations, and (iii) generalisations are confined to the model and regimes examined.
Numbers and test results are unchanged.
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

EDITS = [
    # ---------------------------------------------------------------- abstract
    (r"""The aim of this study is to establish, under controlled
conditions, when TimesFM-3 should be preferred to classical forecasting methods.""",
     r"""The aim of this exploratory study is to describe, under
controlled conditions, how TimesFM-3 behaves relative to classical forecasting methods and in
which regimes it may be preferred."""),
    (r"""The findings are diagnostic baselines for the regimes examined rather
than universal prescriptions.""",
     r"""Because TimesFM-3 is a black box whose pre-training data cannot be
inspected, the study characterises its behaviour, not the reasons for it, and its conclusions are
conditional on the regimes examined."""),

    # ---------------------------------------------------------------- introduction
    (r"""This is a boundary of what the design can establish rather than a flaw, and its effect has a
predictable direction. Family-level familiarity would tend to \emph{help} TimesFM-3 on D1--D5,
the processes where a classical model is correctly specified. Since those are precisely the
cells where the classical methods win, the effect works against this paper's more favourable
findings rather than for them. Where TimesFM-3 wins---intermittency, breaks---it wins on
processes least likely to be over-represented in a synthetic ARMA corpus. The results
therefore give a lower bound on the accuracy a foundation model gives up where a classical model
is correctly specified: for a model less familiar with ARMA-type structure the gap would be wider,
not narrower.""",
     r"""This is a boundary of what the design can establish. Whether family-level familiarity affects
the results cannot be tested here, because the pre-training corpus is not available for
inspection. If it does, it would be expected to help TimesFM-3 most on D1--D5, the processes where
a classical model is correctly specified and where the classical methods win; under that
conjecture the gap measured there would understate rather than overstate the accuracy TimesFM-3
gives up. The conjecture is stated for transparency and no conclusion relies on it."""),
    (r"""The aim of the study is therefore to establish, under controlled experimental conditions, diagnostic
boundaries for when TimesFM-3 should be preferred to classical forecasting methods and when it should
not. It proposes no new estimator, test or theory. Its contribution is evidential: a controlled
measurement of the trade-off between the two families within defined parametric and empirical regimes.
Crucially, these findings are presented as structured diagnostic baselines rather than unconstrained
prescriptions for all applied settings; because operational series introduce complexities beyond any
controlled design, they serve as a benchmark against which broader multi-domain investigations can build.""",
     r"""The aim of the study is therefore exploratory: to describe, under controlled experimental
conditions, how the accuracy of TimesFM-3 relative to classical methods varies across regimes, and
to derive from that description diagnostic baselines for when it may be preferred and when it
should not. It proposes no new estimator, test or theory.

The design can establish what TimesFM-3 does; it cannot establish why. The behaviour of a classical
model can be traced to its equations and estimated parameters, whereas TimesFM-3 is a black box:
its 330 million parameters have no individual interpretation, and its pre-training corpus is not
available for inspection. Explanations of its behaviour offered in this paper, for example that
its forecasts behave as if they drew on a prior over common series shapes, are therefore
interpretations consistent with the measurements, not findings. The measurements themselves are
also bounded. They concern one model, one checkpoint, univariate zero-shot use and the regimes
examined, and they do not support general statements about foundation models as a class. Within
these bounds the controlled design offers what public benchmarks cannot: a known ground truth,
series the model cannot have seen, and a pre-registered analysis."""),

    # ---------------------------------------------------------------- model section
    (r"""The model is opaque in a specific and limited sense. Its weights, architecture and inference code
are public, so every forecast in this study can be reproduced exactly by any reader, and the
checkpoint is fixed, so the results do not depend on a service that may change. What is not
available is the pre-training corpus itself and any interpretation of the 330 million parameters
comparable to the coefficients of an ARIMA model.""",
     r"""TimesFM-3 is a black box in the sense that matters for interpretation, though not in the sense
that matters for reproducibility. Its weights, architecture and inference code are public, so every
forecast in this study can be reproduced exactly by any reader, and the checkpoint is fixed, so the
results do not depend on a service that may change. What is not available is the pre-training
corpus itself and any interpretation of the 330 million parameters comparable to the coefficients
of an ARIMA model."""),
    (r"""and calibration on data whose generating mechanism is known. This is the purpose of the
controlled design in \sectionref{sec:design} and of the robustness study in
\sectionref{sec:robustness}.""",
     r"""and calibration on data whose generating mechanism is known. This is the purpose of the
controlled design in \sectionref{sec:design} and of the robustness study in
\sectionref{sec:robustness}. Such measurements describe the model's behaviour; they do not
reveal the mechanism that produces it."""),

    # ---------------------------------------------------------------- results
    (r"""prediction intervals, and \sectionref{sec:combination} and \sectionref{sec:mape} report two
robustness analyses.""",
     r"""prediction intervals, and \sectionref{sec:combination} and \sectionref{sec:mape} report two
robustness analyses. Throughout, statements about TimesFM-3 describe the behaviour of its
forecasts; where an explanation is offered, it is an interpretation, since the model's internal
workings cannot be inspected."""),
    (r"""is significant. Being correctly specified bought AutoARIMA nothing detectable on short and
moderate series, because the parameters still have to be estimated from the data at hand,
whereas TimesFM-3 brings a prior learned from more than a trillion time points.""",
     r"""is significant. Being correctly specified bought AutoARIMA nothing detectable on short and
moderate series. A plausible reading is that the classical parameters still have to be estimated
from the data at hand, whereas the forecasts of TimesFM-3 behave as if they drew on a prior
learned in pre-training; the design can verify the first half of this explanation, as the next
paragraph shows, but not the second."""),
    (r"""This demonstrates that
the short-sample deficit of automated classical methods is driven by model selection uncertainty
rather than by an inability of the classical model structure to fit the data.""",
     r"""This indicates that
the short-sample deficit of automated classical methods is largely attributable to model
selection uncertainty rather than to an inability of the classical model structure to fit the
data."""),
    (r"""error measures is therefore a property of the regime, not of one parameter value.""",
     r"""error measures therefore holds across the parameter range examined, not only at one value."""),

    # ---------------------------------------------------------------- discussion
    (r"""somewhere at least $2.2\times$ worse. It is rarely the best method and never a bad one, whereas""",
     r"""somewhere at least $2.2\times$ worse. In this design it is rarely the best method and never among
the worst, whereas"""),
    (r"""heterogeneous series and no capacity to diagnose each one, the trade is decisive.""",
     r"""heterogeneous series and no capacity to diagnose each one, the trade favoured TimesFM-3 in this
design, because its worst case was much milder than that of any classical method."""),
    (r"""\caption{Recommended forecasting family by situation.}""",
     r"""\caption{Recommended forecasting family by situation, within the regimes examined.}"""),

    # ---------------------------------------------------------------- conclusion
    (r"""The most transferable finding is not about either family in particular. It is that the
decisive property is not whether a classical model is correctly \emph{specified} but whether it
is \emph{estimable}: with two seasonal cycles, AutoETS had a mean MASE 2.7 times that of the
seasonal naive method on data generated by an ETS process. Foundation models are most valuable exactly where
classical estimation is starved, and least valuable where it is comfortable.""",
     r"""The finding most likely to transfer beyond this design concerns the classical side, where the
mechanism can be examined: the decisive property is not whether a classical model is correctly
\emph{specified} but whether it is \emph{estimable}. With two seasonal cycles, AutoETS had a mean
MASE 2.7 times that of the seasonal naive method on data generated by an ETS process. In this
design TimesFM-3 was most useful relative to the classical methods where classical estimation was
starved, and least useful where it was comfortable; whether the same holds for other foundation
models is not tested here."""),
    (r"""Finally, these findings reflect the specific data-generating mechanisms, parameterisations and
monthly horizons examined here. While clean-room simulations guarantee known ground truth and
pre-registration prevents retrospective bias, no synthetic design exhaustively spans the vast heterogeneity
of applied forecasting. Further empirical and methodological research across broader architectural classes,
higher sampling frequencies, and multivariate domains with exogenous regressors will be essential to
deepen these insights and establish the general boundary between learned representations and parametric models.""",
     r"""Finally, the study is exploratory. It describes how one black-box model behaves on data of
known structure; it does not explain that behaviour, and its conclusions remain conditional on the
processes, parameter ranges and monthly horizons examined, even after the robustness analysis. A
simulation with a known ground truth and a pre-registered analysis can make such a description
reliable, but no synthetic design spans the heterogeneity of applied forecasting. Studies of other
foundation models, other sampling frequencies and multivariate problems with exogenous
regressors, and work on the internal representations of these models, will be needed before the
boundary between learned and parametric forecasting can be stated in general terms."""),
]


def main() -> None:
    s = P.read_text(encoding="utf-8")
    for old, new in EDITS:
        n = s.count(old)
        assert n == 1, f"{n} matches for: {old[:70]!r}"
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8")
    print(f"{len(EDITS)} edits applied")


if __name__ == "__main__":
    main()
