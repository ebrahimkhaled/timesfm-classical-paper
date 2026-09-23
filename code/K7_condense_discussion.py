"""Length pass, part 7: condensed discussion, conclusion and reproducibility sections."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

NEW = r"""\section{Discussion}
\label{sec:discussion}

This section assesses the pre-registered hypotheses (\sectionref{sec:hypotheses}), interprets the balance
between robustness and peak accuracy (\sectionref{sec:tradeoff}), gives practical recommendations
(\sectionref{sec:recommendations}) and states the limitations (\sectionref{sec:limitations}).

\subsection{Assessment of the pre-registered hypotheses}
\label{sec:hypotheses}

\textbf{None of the five hypotheses survives unqualified}: three are refuted and two partially supported.
\textbf{H1} (correctly specified classical models beat TimesFM-3 on their home ground, most at short lengths)
is refuted as stated---at short lengths the gap runs the other way---and survives only where a model is both
correctly specified and estimable (D4 and D5 at $n \geq 48$). \textbf{H2} (TimesFM-3 wins wherever no
classical form is correct) is partially supported: on intermittent demand only for the pinball loss, since
its MASE advantage is matched by the all-zero forecast and RMSSE favours the Croston family; mildly on
breaks; not on the logistic process, where the outcome depends on length. \textbf{H3} (on D9 the families
tie in the mean and classical intervals under-cover) is partially supported: they tie, but only AutoARIMA
under-covers. \textbf{H4} (the combination beats every classical method and is TimesFM-3's hardest
opponent) is refuted in both clauses: AutoARIMA beats the combination on mean MASE and is the harder
opponent (11--9 against 27--3). \textbf{H5} (both families under-cover at 80\%) is refuted: averaged over
processes TimesFM-3 is close to nominal and the classical methods over-cover from $n = 96$, and per cell the
deviations are large but not systematically downward.

\subsection{Robustness versus peak accuracy}
\label{sec:tradeoff}

The classical methods' 20 cell wins are spread over five methods, so which classical method wins is not
knowable in advance without the model selection a foundation model is meant to remove. TimesFM-3, one
untuned model, is within noise of the cell-best in half the design; the best classical method is
significantly better in 11 cells over five processes, by less than 3\% on D2 and D3 and by large margins
only on D4, D5 and D7 at $n = 96$. The evidence therefore supports neither the conclusion that foundation
models have superseded classical methods nor the opposite, but a narrower one: \textbf{TimesFM-3 provides
robustness rather than peak accuracy}. It is rarely the best method and never among the worst in this
design, whereas the automatic classical methods are sometimes excellent and sometimes catastrophic. For
one well-understood series that trade is unattractive; for many heterogeneous series and no capacity to
diagnose each one, it favoured TimesFM-3 here.

The extended evidence qualifies the trade twice. It belongs to TimesFM-3, not to foundation models in
general (\sectionref{sec:benchmarks}). And it depends on configuration: when the classical methods estimate
the seasonal period, as a practitioner would, their worst case (1.58) is level with TimesFM-3's (1.55)
(\sectionref{sec:departures}). On the M4 test period with long histories, TimesFM-3 is one of a group of
leading methods that cannot be separated (\sectionref{sec:m4official}).

\subsection{Practical recommendations}
\label{sec:recommendations}

\tableref{tab:decision} translates the evidence into recommendations. They apply only to the regimes
examined, name more than one option where the evidence does not favour one, and should be checked against
features these designs do not cover, such as multiple seasonalities or irregular sampling.

\begin{table}[!htbp]
\centering
\begin{threeparttable}
\caption{Recommended forecasting family by situation, within the regimes examined.}
\label{tab:decision}
\small
\begin{tabular}{>{\raggedright\arraybackslash}p{5.0cm}>{\raggedright\arraybackslash}p{3.0cm}>{\raggedright\arraybackslash}p{5.8cm}}
\toprule
Situation & Use & Evidence \\
\midrule
Commercial or production deployment
  & Classical, or TimesFM-2.5
  & TimesFM-3 weights are non-commercial; TimesFM-2.5 (Apache-2.0) is less robust in the simulation
    (worst ratio 2.18) but level on M4 \\[2pt]
Intermittent demand, distribution needed (e.g.\ service levels)
  & \textbf{TimesFM-3} quantiles
  & Pinball loss about 15\% below the best classical method (D8) \\[2pt]
Intermittent demand, mean rate needed
  & Croston family, or TimesFM-3's mean of deciles
  & Level on RMSSE with little bias; TimesFM-3's median forecast is no better than zero on MASE (D8) \\[2pt]
Strong seasonality, at least four cycles
  & \textbf{AutoARIMA}
  & 21--24\% lower mean MASE than TimesFM-3, $p < 0.0001$ (D4); reverses below four cycles \\[2pt]
Seasonality with two cycles or fewer
  & Seasonal naive or TimesFM-3
  & Automatic classical methods fail with or without a seasonal model (AutoETS 3.03 and 2.55, D5) \\[2pt]
Many heterogeneous series, no per-series tuning
  & \textbf{TimesFM-3}
  & Beats every classical method except AutoARIMA in most significant comparisons \\[2pt]
One series whose model can be identified
  & Classical
  & AutoARIMA close to TimesFM-3 (11--9), free, interpretable and diagnosable \\[2pt]
Recent structural break, intervals matter
  & \textbf{TimesFM-3}
  & Comparable coverage with intervals about half as wide (D6) \\[2pt]
Throughput, GPU available
  & TimesFM-3
  & $2.3\times$ faster end to end than the classical suite on 22 cores \\[2pt]
Calibrated intervals on real data
  & Classical combination
  & M4 coverage 0.801 against 0.765 for TimesFM-3 (nominal 0.80) \\[2pt]
Forecast must be explained or audited
  & Classical
  & TimesFM-3 exposes no parameters, diagnostics or interval theory \\
\bottomrule
\end{tabular}
\begin{tablenotes}[flushleft]\footnotesize
\item \textit{Note:} Based on Sections~\ref{sec:results}--\ref{sec:operational}. Bold marks a preference
supported by significant differences; the other rows rest on considerations outside the accuracy
comparison.
\end{tablenotes}
\end{threeparttable}
\end{table}

\subsection{Limitations}
\label{sec:limitations}

First, simulated series are clean and free of the measurement error, calendar effects and regime changes of
applied work; the M4 tier addresses this only in part, and the randomised design still leaves about a
quarter of M4 monthly series, and all other frequencies, outside the regions studied, with coverage in four
features a necessary rather than sufficient condition for similarity. Second, the nine process families are
fixed, the horizon is short ($H = 12$), the seasonal period is 12, and the departures from the assumptions
were applied one at a time, so their interactions were not examined; calibration of foundation models is
reported to degrade with horizon \citep{adler2026calibrated}. Third, TimesFM-3 was used zero-shot and
univariate, leaving its multivariate and covariate capabilities untested; fine-tuning was excluded because
fine-tuning on one series of 24 to 200 points is not meaningful for a model of this size and fine-tuning on
the DGPs would remove the separation between model and test data. Fourth, no method was tuned by hand; an
expert who identified each process would beat every automatic method here. Fifth, three foundation models
were evaluated and they behave differently, so conclusions about one do not transfer to the class; masked
encoder models such as Moirai \citep{woo2024moirai} were not included. Sixth, several analyses are post
hoc---the Croston baselines, the combination rule, the Oracle ARIMA and Sections~\ref{sec:extended}
and~\ref{sec:robustness}---and are reported separately from the pre-registered comparison.

\section{Conclusion}
\label{sec:conclusion}

This study compared TimesFM-3 with classical methods on 7\,200 series from nine known processes under a
pre-registered protocol, in a design where realisation-level contamination is impossible and the model
families searched by AutoARIMA and AutoETS contain the true process of D1--D5. Neither family dominates.
TimesFM-3 wins 113 of 132 significant pairwise comparisons, only AutoARIMA holding its own (11--9), and it
is never more than 1.31 times worse than the best method in a cell (95\% interval 1.28 to 1.36), while every
classical method is at least 2.2 times worse somewhere; with at least four seasonal cycles AutoARIMA is
21--24\% more accurate. This robustness is specific to TimesFM-3---TimesFM-2.5 and Chronos-Bolt are no more
robust than AutoARIMA---and it largely disappears when the classical methods estimate the seasonal period.
Randomised parameters, heavy tails and outliers leave these findings intact within Monte Carlo error. On
intermittent demand the MASE comparison is uninformative, because forecasting zero wins it; TimesFM-3's
advantage there is its predictive distribution, with a pinball loss about 15\% lower.

On 1\,000 M4 monthly series TimesFM-3 is one of six statistically indistinguishable leading methods on the
official test period (OWA 0.862), and with only 24 observations of history it is 11\% more accurate than
AutoARIMA. The finding most likely to transfer concerns the classical side, where the mechanism can be
examined: what matters is whether a classical model is \emph{estimable} from the data, not only whether it is
correctly \emph{specified}---with two cycles, AutoETS had 2.7 times the error of seasonal naive on data from an
ETS process. Outside accuracy, TimesFM-3 was 2.3 times faster end to end than the parallelised classical
suite, and its weights are licensed for non-commercial use only, which for commercial users decides the
question before accuracy does.

The study is exploratory. It describes how one black-box model behaves on data of known structure, does not
explain that behaviour, and remains conditional on the processes, parameter ranges and horizons examined.
Studies of other foundation models, frequencies and multivariate problems, and of the internal
representations of these models, will be needed before the boundary between learned and parametric
forecasting can be stated in general terms.

\section{Computational details and reproducibility}
\label{sec:repro}

All results were produced with \proglang{Python}~3.13 \citep{python}, \pkg{statsforecast}~2.1.1
\citep{statsforecast}, \pkg{timesfm}~3.0.1 with the \path{google/timesfm-3.0-pytorch} weights
\citep{timesfm3repo}, \pkg{chronos-forecasting}~2.3.2, \pkg{PyTorch}~2.6 \citep{paszke2019pytorch},
\pkg{NumPy} \citep{harris2020numpy}, \pkg{pandas} \citep{mckinney2010pandas}, \pkg{SciPy}
\citep{virtanen2020scipy} and \pkg{Matplotlib} \citep{hunter2007matplotlib}, on an NVIDIA GTX 1660 Ti
with a 24-core CPU and 32\,GB of memory (parallel classical runs use $22 = 24 - 2$ worker processes).
Every simulated series is seeded from its own identifiers, so the study regenerates exactly, independently
of core count or execution order, and each cached stage can be rerun alone. The foundation models were run
in 32-bit arithmetic without random sampling; rerunning two TimesFM-3 cells reproduced the stored quantiles
exactly, although other hardware may differ in the last digits because GPU floating-point reductions are
not associative. The protocol, with its five hypotheses, was frozen before any forecast; twelve departures
from it are recorded, each dated and reasoned, and every post-hoc analysis is marked as such. Every DOI in
the bibliography was resolved and compared with its entry.

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index("\\section{Discussion}")
    b = s.index("\\section*{Acknowledgements}")
    s = s[:a] + NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("discussion, conclusion and reproducibility condensed")


if __name__ == "__main__":
    main()
