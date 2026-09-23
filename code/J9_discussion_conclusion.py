"""JoF revision: discussion, recommendations, limitations and conclusion after the extended evidence."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

EDITS = [
    # R2-m5 hypothesis tally
    (r"""Of the five pre-registered hypotheses, \textbf{none survives unqualified}: two are refuted
outright, two are partially supported, and one is refuted in its second clause.""",
     r"""Of the five pre-registered hypotheses, \textbf{none survives unqualified}: three are refuted
(H1 as stated, H4 in both clauses, and H5) and two are partially supported (H2 and H3)."""),
    (r"""      \textbf{partially supported}. It holds on intermittent demand under MASE and pinball loss
      but not under RMSSE or sMAPE, mildly on structural breaks, and not on the logistic process,
      where the outcome depends on length.""",
     r"""      \textbf{partially supported}. On intermittent demand it holds for the pinball loss, which
      scores the whole predictive distribution; the MASE advantage is matched by the all-zero
      forecast (\sectionref{sec:d8-extended}) and RMSSE favours the Croston family. It holds mildly
      on structural breaks, and not on the logistic process, where the outcome depends on length."""),
    # R1-m3
    (r"""TimesFM-3, one model with no tuning, is within noise of that per-cell best in half the design
and beaten decisively in only two regimes.""",
     r"""TimesFM-3, one model with no tuning, is within noise of that per-cell best in half the design.
The best classical method is significantly better in 11 cells spread over five processes, although
on D2 and D3 those differences are below 3\%; the large ones are on the seasonal processes D4 and
D5 and on the logistic process D7 at $n = 96$."""),
    (r"""heterogeneous series and no capacity to diagnose each one, the trade favoured TimesFM-3 in this
design, because its worst case was much milder than that of any classical method.""",
     r"""heterogeneous series and no capacity to diagnose each one, the trade favoured TimesFM-3 in this
design, because its worst case was much milder than that of any classical method.

The extended evidence qualifies this trade in two ways. It is a property of TimesFM-3 and not of
foundation models in general: TimesFM-2.5 and Chronos-Bolt have worst cases of 2.18 and 3.06, no
better than AutoARIMA (\sectionref{sec:benchmarks}). And it depends on how the classical methods are
configured: when they must estimate the seasonal period, as a practitioner would, their worst case
in the randomised design (1.58) is level with that of TimesFM-3 (1.55), because the largest
classical failures arise where a seasonal model is imposed on two cycles
(\sectionref{sec:departures}). On the M4 official test period, with long histories, TimesFM-3 belongs
to a group of leading methods that cannot be separated statistically (\sectionref{sec:m4official})."""),
    # recommendations table
    (r"""Commercial or production deployment
  & Classical (or TimesFM-2.5)
  & Version-3 weights are licensed non-commercial; accuracy is not the binding constraint \\[2pt]""",
     r"""Commercial or production deployment
  & Classical (or TimesFM-2.5)
  & Version-3 weights are licensed non-commercial. TimesFM-2.5 (Apache-2.0) is less robust than
    TimesFM-3 in the simulation (worst ratio 2.18) but level with it on M4 \\[2pt]"""),
    (r"""Intermittent demand, and the decision loss is roughly linear in units
  & \textbf{TimesFM-3}, but see the caveat
  & Beats all six Croston-family methods on MASE at every length (24/24 significant), and the
    general-purpose set by 22--26\%, but worse on RMSSE and sMAPE (D8) \\[2pt]
Intermittent demand, and the decision loss is roughly quadratic
  & Classical
  & The metrics reverse: Croston-SBA and ADIDA win on RMSSE at every length (D8) \\[2pt]""",
     r"""Intermittent demand, and a full predictive distribution is needed (for example to set
    service levels)
  & \textbf{TimesFM-3} quantiles
  & Pinball loss about 15\% lower than the best classical method at every length (D8) \\[2pt]
Intermittent demand, and a point forecast of the mean rate is needed
  & Croston family, or TimesFM-3's mean of deciles
  & Level on RMSSE with little bias; TimesFM-3's default median forecast is no better on MASE than
    forecasting zero and under-stocks persistently (D8) \\[2pt]"""),
    (r"""  & Automatic classical methods fail badly here: AutoETS scores 3.03 on its own process (D5, $n=24$) \\[2pt]""",
     r"""  & Automatic classical methods fail here whether or not a seasonal model is imposed: AutoETS scores
    3.03 on its own process (D5, $n=24$), and 2.55 when the period is estimated \\[2pt]"""),
    (r"""Throughput matters and a GPU is available
  & \textbf{TimesFM-3}
  & 103$\times$ faster per series than AutoARIMA; $2.3\times$ faster than the whole
    classical suite on 22 cores \\[2pt]""",
     r"""Throughput matters and a GPU is available
  & TimesFM-3
  & $2.3\times$ faster end to end than the whole classical suite on 22 cores; single-process
    AutoARIMA is 103 times slower per series on the most expensive cell \\[2pt]"""),
    # limitations
    (r"""Fifth, the intermittent-demand analysis of \sectionref{sec:croston} is post hoc: the
Croston-family baselines were added after the main results were seen, in response to an
identified gap, and are reported separately from the pre-registered comparison.""",
     r"""Fifth, several analyses are post hoc: the Croston-family baselines, the combination rule
comparison, the Oracle ARIMA baseline, and everything in Sections~\ref{sec:extended} and
\ref{sec:robustness}. They were designed after the main results were seen and are reported
separately from the pre-registered comparison; the deviation log records each one."""),
    (r"""Sixth, this study evaluates a single foundation model architecture: Google's TimesFM-3, a
decoder-only transformer operating on continuous, patched representations. Other architectures---such
as tokenized language models (e.g., Chronos; \citealp{ansari2024chronos}) or masked encoder-decoder
networks (e.g., MOIRAI; \citealp{woo2024moirai})---possess distinct inductive biases, loss functions,
and pre-training mixtures. Whether the robustness-versus-peak-accuracy trade-off documented here
holds across alternative foundation-model families remains an open question for multi-architecture comparisons.""",
     r"""Sixth, the study centres on one foundation model. TimesFM-2.5 and Chronos-Bolt were added in
\sectionref{sec:benchmarks}, and they behave differently from TimesFM-3, which is itself evidence
that conclusions about one model do not transfer to the class. Other architectures, such as masked
encoder models (Moirai; \citealp{woo2024moirai}), and later releases were not evaluated."""),
    (r"""period. The randomised design covers 81\% of the M4 monthly series in a four-feature space, which
leaves a fifth of real monthly series, and all series at other frequencies, outside the regions
studied.""",
     r"""period. The randomised design covers about three quarters of the M4 monthly series in a
four-feature space, which leaves a quarter of real monthly series, and all series at other
frequencies, outside the regions studied."""),
    # conclusion
    (r"""known processes, under a pre-registered protocol, in a design where contamination of the
foundation model is impossible by construction and the classical models are correctly specified
by construction.""",
     r"""known processes, under a pre-registered protocol, in a design where realisation-level
contamination of the foundation model is impossible and the model families searched by AutoARIMA and
AutoETS contain the true process of D1--D5."""),
    (r"""data with at least four observed cycles AutoARIMA is 21--24\% better. On intermittent demand the
answer depends on the loss function: TimesFM-3 is about a quarter better on MASE and best on the
scaled pinball loss, but worse on RMSSE and much worse on sMAPE, because absolute- and
squared-error metrics reward different functionals of a predictive distribution that is 70\%
zeros.""",
     r"""data with at least four observed cycles AutoARIMA is 21--24\% better. On intermittent demand the
MASE comparison is uninformative, because the all-zero forecast has the lowest MASE of all; TimesFM-3's
advantage there lies in its predictive distribution, whose pinball loss is about 15\% lower than
that of the best classical method, and its mean-of-deciles forecast is level with the Croston family
on RMSSE. The robustness of TimesFM-3 holds with 95\% bootstrap intervals, but it is specific to this
model: TimesFM-2.5 and Chronos-Bolt are no more robust than AutoARIMA."""),
    (r"""These conclusions do not rest on the particular parameter values of the main design. When every
series draws its own parameters from wide ranges, and when the data have heavy-tailed noise,
outliers or a seasonal period that the classical methods must estimate, the same pattern holds:
TimesFM-3 is at most 1.51 times worse than the best method in any cell, the seasonal advantage of
AutoARIMA and the reversal between error measures on intermittent demand persist, and the collapse
of seasonal models on two cycles disappears once a standard seasonality test is applied. The
randomised design is also closer to real data, covering 81\% of M4 monthly series in a feature
space against 56\% for the fixed design.""",
     r"""When every series draws its own parameters from wide ranges, and when the data have heavy-tailed
noise or outliers, the pattern was consistent with that of the main design within Monte Carlo
error: TimesFM-3 is at most 1.56 times worse than the best method in any cell, against at least 2.09
for the classical methods, and the seasonal advantage of AutoARIMA persists. When the classical
methods must estimate the seasonal period, the worst cases of the two families are level, because
the largest classical failures come from imposing a seasonal model on two cycles. The randomised
design is also closer to real data, covering 76\% of M4 monthly series in a feature space against
49\% for the fixed design."""),
    (r"""A secondary analysis of 1\,000 M4 Monthly series reproduces the pattern closely: TimesFM-3 beats
seasonal naive, Theta and AutoETS significantly, and ties with AutoARIMA and the combination.
Real monthly series are long and seasonal---the estimable regime---and the tiers agree on what
happens there, which is worth more than either tier alone given their opposite weaknesses.""",
     r"""On 1\,000 M4 Monthly series, TimesFM-3 beats seasonal naive, Theta and AutoETS and ties with
AutoARIMA and the combinations; on the official test period it is one of six methods that cannot be
separated statistically, with an OWA of 0.862. With only the last 24 observations of each series it
is 11\% more accurate than AutoARIMA, so the advantage where data are scarce appears on real series
too."""),
    (r"""Two findings outside the accuracy comparison deserve equal weight. TimesFM-3 is 103 times
faster per series than AutoARIMA, so the foundation model is the less expensive option per series,
although parallelising the classical suite across 22 cores narrows the end-to-end difference to
$2.3\times$. And its released weights may not be used commercially. For commercial applications,
this restriction takes precedence over the accuracy comparison.""",
     r"""Two findings outside the accuracy comparison matter in practice. On a single consumer GPU,
TimesFM-3 forecast the 7\,200 series 2.3 times faster than the whole classical suite running on 22
CPU cores. And its released weights are licensed for non-commercial use only, so for commercial
applications the licence, not accuracy, decides whether it can be used."""),
]


def main():
    s = P.read_text(encoding="utf-8")
    for old, new in EDITS:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f"{n} matches for: {old[:80]!r}")
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8")
    print(f"{len(EDITS)} edits applied")


if __name__ == "__main__":
    main()
