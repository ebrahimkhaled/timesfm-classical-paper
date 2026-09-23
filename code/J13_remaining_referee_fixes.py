"""JoF revision: the remaining referee items that change only wording or add small facts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "manuscript_jof" / "timesfm_jof.tex"
BIB = ROOT / "manuscript_jof" / "refs.bib"

EDITS = [
    # R3-m3: developer-reported architecture
    ("R3-m3", r"""and 16 attention heads, for a total of about 330 million parameters
\citep{timesfm3blog, timesfm3card}.""",
     r"""and 16 attention heads, for a total of about 330 million parameters
\citep{timesfm3blog, timesfm3card}. These and the following architectural details are as reported
by the developers (blog post and model card, accessed 23 September 2026); the checkpoint loaded in
this study has 330\,710\,976 parameters."""),
    # R3-M1: inference settings, short contexts, batch invariance
    ("R3-M1", r"""formed from its output is the nominal 80\% interval (\sectionref{sec:evaluation}).""",
     r"""formed from its output is the nominal 80\% interval (\sectionref{sec:evaluation}).

The inference settings are those of \code{predict\_batch} in \pkg{timesfm} 3.0.1: no symmetric
averaging, no positivity constraint, quantiles sorted, 32-bit floating point. A context shorter
than the model's working length is left-padded with zeros and the padded positions are masked, so
at $n = 24$ the model sees a single, partly filled input patch; the maximum context is 15\,360
points, so no series in this study is truncated. Forecasting a series on its own and inside a batch
of series of other lengths gave quantiles that agree to within $2 \times 10^{-5}$. The settings of the
developers' own benchmark evaluator differ from these defaults and are examined in
\sectionref{sec:tfm-check}."""),
    # R1-m10: MASE denominator convention
    ("R1-m10", r"""where $m$ is the seasonal period ($m = 12$ on D4 and D5; $m = 1$ elsewhere). The Root Mean Squared Scaled""",
     r"""where $m$ is the seasonal period ($m = 12$ on D4 and D5; $m = 1$ elsewhere). The scaling therefore
uses the seasonal-naive error for the seasonal processes and the naive error for the others; the M4
convention of scaling every monthly series with $m = 12$ is used for the M4 tier. The Root Mean Squared Scaled"""),
    # R1-M7 and R1-m2: Oracle ARIMA
    ("R1-M7", r"""Evaluating an \emph{Oracle ARIMA} baseline (where the true orders $(p,d,q)(P,D,Q)$ are known
and only parameters are estimated via conditional MLE) confirms that order selection uncertainty
under AICc imposes a sizable penalty in small samples: on D1--D3 at $n = 24$, AutoARIMA incurs an
8.8\%--13.9\% selection penalty relative to Oracle ARIMA, and on D4 at $n = 24$ (two seasonal cycles)
the penalty reaches 81.2\%.""",
     r"""A post-hoc \emph{Oracle ARIMA} baseline, in which the true orders $(p,d,q)(P,D,Q)$ are known and
only the parameters are estimated by Gaussian maximum likelihood, confirms that order selection
under AICc imposes a sizable penalty in small samples: on D1--D3 at $n = 24$, AutoARIMA incurs a
9.9\% to 13.9\% selection penalty relative to Oracle ARIMA, and on D4 at $n = 24$ (two seasonal
cycles) the penalty reaches 81.2\%, although there the optimiser fails to converge in 156 of the 200
oracle fits, so that figure is only indicative."""),
    # R1-M2c: TSB smoothing constants
    ("R1-M2c", r"""Syntetos--Boylan approximation (Croston-SBA), ADIDA, IMAPA and TSB. \tableref{tab:croston} gives""",
     r"""Syntetos--Boylan approximation (Croston-SBA), ADIDA, IMAPA and TSB. \pkg{StatsForecast} estimates
the smoothing constants of the optimised Croston variant but requires them to be fixed for TSB, for
which the common values $\alpha_d = \alpha_p = 0.2$ are used. Tuning them could lower TSB's errors
somewhat, but it would not change the conclusions: on RMSSE the Croston family is already ahead of
TimesFM-3's median forecast, and the MASE comparison is dominated by the all-zero forecast
(\sectionref{sec:d8-extended}). \tableref{tab:croston} gives"""),
    # R1-m6: one direction for the D4 effect
    ("R1-m6", r"""  & AutoARIMA 21--24\% better; TimesFM-3 27--31\% worse, all $p < 0.0001$ (D4).""",
     r"""  & AutoARIMA 21--24\% lower mean MASE than TimesFM-3, all $p < 0.0001$ (D4)."""),
    # R1-m1 / R2-M7b: deviation count and post-hoc analyses
    ("R1-m1", r"""forecast was produced, and the frozen file was never edited afterwards; nine departures from it
are recorded separately, each dated and reasoned, with the two post-hoc analyses marked as such.""",
     r"""forecast was produced, and the frozen file was never edited afterwards; twelve departures from it
are recorded separately, each dated and reasoned, and every post-hoc analysis (the Croston-family
baselines, the combination rule, the Oracle ARIMA baseline, the extended evaluation and the
robustness study) is marked as such."""),
    ("R1-m1", r"""robustness study of \sectionref{sec:robustness} uses a separate seed range and adds 91\,200""",
     r"""robustness study of \sectionref{sec:robustness} uses a separate seed range and adds 182\,400"""),
    # R3-m6: foundation-model literature
    ("R3-m6", r"""training, and GIFT-Eval \citep{aksu2024gifteval} supplied a common benchmark.""",
     r"""training, and TimeGPT \citep{garza2023timegpt} and Lag-Llama \citep{rasul2023lagllama} followed
the same idea; GIFT-Eval \citep{aksu2024gifteval} and fev-bench \citep{shchur2025fevbench} supplied
common benchmarks, both of which include AutoARIMA, AutoETS and seasonal naive among their
baselines."""),
]

BIB_ADD = r"""

% ---------------------------------------------------------------- foundation-model literature (R3-m6)
% arXiv identifiers checked against the arXiv API on 2026-09-23.
@misc{garza2023timegpt,
  author        = {Azul Garza and Cristian Challu and Max Mergenthaler-Canseco},
  title         = {{TimeGPT-1}},
  year          = {2023},
  howpublished  = {arXiv preprint arXiv:2310.03589},
  doi           = {10.48550/arXiv.2310.03589}
}

@misc{rasul2023lagllama,
  author        = {Kashif Rasul and Arjun Ashok and Andrew Robert Williams and Hena Ghonia and Rishika Bhagwatkar and Arian Khorasani and others},
  title         = {{Lag-Llama}: Towards Foundation Models for Probabilistic Time Series Forecasting},
  year          = {2023},
  howpublished  = {arXiv preprint arXiv:2310.08278},
  doi           = {10.48550/arXiv.2310.08278}
}

@misc{shchur2025fevbench,
  author        = {Oleksandr Shchur and Abdul Fatir Ansari and Caner Turkmen and Lorenzo Stella and Nick Erickson and Pablo Guerron and Michael Bohlke-Schneider and Yuyang Wang},
  title         = {{fev-bench}: A Realistic Benchmark for Time Series Forecasting},
  year          = {2025},
  howpublished  = {arXiv preprint arXiv:2509.26468},
  doi           = {10.48550/arXiv.2509.26468}
}
"""


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
            raise SystemExit(f"{tag}: {n} matches")
    P.write_text(s, encoding="utf-8")
    b = BIB.read_text(encoding="utf-8")
    if "garza2023timegpt" not in b:
        BIB.write_text(b + BIB_ADD, encoding="utf-8")
        print("bib: 3 entries added")


if __name__ == "__main__":
    main()
