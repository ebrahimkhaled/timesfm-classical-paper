"""Length pass, part 2: condensed design section (parameter justification, methods, evaluation).
Every criterion, choice and citation is kept."""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

START = "The parameter values in \\tableref{tab:dgps} were fixed in the pre-registered protocol"
END = "\\section{Simulation results}"

NEW = r"""The parameter values in \tableref{tab:dgps} were fixed in the pre-registered protocol, each chosen so
that its process represents its regime unambiguously. The linear processes D1--D4 and the conditional
mean of D9 use coefficients no larger than 0.7 in absolute value, well inside the stationarity and
invertibility regions \citep{brockwell2016introduction}. The smoothing parameters of D5 lie inside the
usual region $0 < \beta < \alpha < 1$, $0 < \gamma < 1 - \alpha$ \citep{hyndman2008ets}, with a small trend
parameter so that the level stays positive. The break in D6 equals ten noise standard deviations, so the
comparison concerns adaptation to the break rather than its detection \citep{pesaran2007breaks}; D7
follows the logistic curve, the standard model of saturating growth \citep{meade2006diffusion}. In D8 the
mean interval between demands is $1/0.3 \approx 3.3$ periods and the squared coefficient of variation of
the sizes is $4/25 = 0.16$, so against the cut-offs of \citet{syntetos2005categorization} the process is
intermittent rather than lumpy, the regime for which Croston's method was developed \citep{croston1972}.
The GARCH(1,1) errors of D9 \citep{bollerslev1986garch} have persistence $a + b = 0.95$, strongly
persistent but covariance-stationary \citep{engle1986persistence}, a standard benchmark specification in
volatility forecasting \citep{hansen2005garch}. Every series has a level of about 100, or a positive lower
asymptote in D7, so percentage errors are defined except where zeros are intrinsic (D8); the trend
parameter of D5 and the asymptote of D7 were adjusted for this reason before any forecast was produced.
Because the conclusions could depend on these values, \sectionref{sec:robustness} repeats the comparison
with parameters drawn at random.

Three design choices need a word. The break in D6 is placed inside the context, at $0.7n$: a break in the
held-out window is unforecastable by any method, whereas one in the context asks whether a method
forecasts from the new level or reverts to the old one. The inflection of D7 sits at $0.6(n+H)$, so the
held-out window lies in the saturating arm, where a method that fits a linear drift overshoots. And the
shortest length, $n = 24$, leaves a seasonal model only two cycles from which to estimate its seasonal
structure, which separates whether a model is correctly \emph{specified} from whether it is
\emph{estimable}. Two hundred replications per (DGP, length) cell give $9 \times 4 \times 200 = 7\,200$
series, each seeded from its own identifiers.

\subsection{Forecasting methods}
\label{sec:methods}

No method is tuned by hand; each classical model uses its own automatic selection, the comparison a
practitioner faces. The classical models are fitted with \pkg{StatsForecast} \citep{statsforecast} at its
default settings, stated because the results depend on them. AutoARIMA searches stepwise over $p, q \le 5$
and $P, Q \le 2$ with $p + q + P + Q \le 5$, chooses $d \le 2$ and $D \le 1$ by unit-root tests, allows a
mean or drift and selects by AICc; AutoETS searches the full error--trend--season space (\code{ZZZ}) with
damped and undamped trends by AICc; Theta is the standard theta method with classical multiplicative
seasonal adjustment \citep{hyndman2021fpp}. The equal-weight combination of Theta, AutoETS and AutoARIMA
is included because the classical state of the art is a combination \citep{makridakis2020m4,
petropoulos2022theory}. Its point forecast is the mean of the members' forecasts and its quantiles the
decile-by-decile mean of theirs (vincentization), which gives a narrower distribution than a mixture when
the members disagree.

Every classical method receives the true seasonal period ($m = 12$ on D4 and D5, $m = 1$ elsewhere),
whereas TimesFM-3 receives only the raw context. This reflects ordinary practice---an analyst usually knows
that data are monthly---but it favours the classical methods on D4 and D5; \sectionref{sec:robustness}
removes the advantage by making them estimate the period.

\subsection{Evaluation measures and statistical inference}
\label{sec:evaluation}

Point accuracy is measured mainly by the mean absolute scaled error \citep[MASE;][]{hyndman2006mase}.
With context $y_1, \dots, y_T$ ($T = n$), horizon $H$ and point forecasts $\hat{y}_{T+h}$,
\begin{equation}
\label{eq:mase}
\text{MASE} = \frac{\frac{1}{H}\sum_{h=1}^H |y_{T+h} - \hat{y}_{T+h}|}{\frac{1}{T-m}\sum_{t=m+1}^T |y_t - y_{t-m}|},
\end{equation}
so the scale is the in-sample seasonal-naive error for the seasonal processes and the naive error for the
others ($m = 12$ throughout for the M4 tier, as in M4). The root mean squared scaled error (RMSSE) replaces
absolute by squared errors in both numerator and denominator and takes the square root, and sMAPE is the
symmetric percentage error of the M4 competition. MAPE, undefined at zero and unusable on D8
\citep{hyndman2006mase, kolassa2016count}, is reported only in the Supporting Information (Section~S1).
Probabilistic accuracy is measured by a strictly proper scoring rule \citep{gneiting2007scoring}, the
pinball loss over the nine deciles $\tau \in \{0.1, \dots, 0.9\}$ scaled by the same denominator,
\begin{equation}
\label{eq:spl}
\text{SPL} = \frac{\frac{1}{9H} \sum_{\tau} \sum_{h=1}^H \max\{\tau(y_{T+h} - \hat{q}^{(\tau)}_{T+h}),\, (1-\tau)(\hat{q}^{(\tau)}_{T+h} - y_{T+h})\}}{\frac{1}{T-m}\sum_{t=m+1}^T |y_t - y_{t-m}|},
\end{equation}
where $\hat{q}^{(\tau)}_{T+h}$ is the $\tau$-quantile forecast, together with the coverage and width of
the nominal 60\% and 80\% intervals \citep{gneiting2007calibration}. Wider intervals cannot be formed from
TimesFM-3's nine deciles, so $[q_{0.1}, q_{0.9}]$ is the widest interval compared; classical quantiles are
taken from intervals at levels 20, 40, 60 and 80, which map onto the same deciles.

Within each (DGP, length, horizon) cell, TimesFM-3 is compared with each classical method by a paired
Wilcoxon signed-rank test \citep{wilcoxon1945} on per-replication MASE differences, with the
Hodges--Lehmann estimate \citep{hodges1963} and the median MASE ratio as effect sizes, and the
Benjamini--Hochberg procedure at a false discovery rate of 0.05 within each opponent family
\citep{benjamini1995fdr}. The Diebold--Mariano test \citep{diebold1995comparing} is not used: the
replications are independent, so there is no serial dependence for it to model, and in the real-data tier
three rolling origins per series leave it without power even with small-sample corrections
\citep{harvey1997testing}. The pre-registered protocol had reserved it for that tier; the departure is
recorded.

"""


def main():
    s = P.read_text(encoding="utf-8")
    a = s.index(START)
    b = s.index(END)
    s = s[:a] + NEW + s[b:]
    P.write_text(s, encoding="utf-8")
    print("design section condensed")


if __name__ == "__main__":
    main()
