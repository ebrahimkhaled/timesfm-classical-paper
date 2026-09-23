"""Length pass, part 1: title-page statements to the back matter; condensed Introduction and
TimesFM-3 sections. Every claim and citation is kept; wording is tightened and repetition removed.

The JoF guidelines list the statements under the title page, but the submission portal collects
each of them in its own field and published JoF articles print them after the conclusion. They are
therefore moved to the end, in Wiley's order, which also removes the separate page between the
abstract and the introduction.
"""

from pathlib import Path

P = Path(__file__).resolve().parent.parent / "manuscript_jof" / "timesfm_jof.tex"

FRONT_STATEMENTS_START = "\\noindent\\textbf{Running title:}"
FRONT_STATEMENTS_END = "\\newpage\n\\linenumbers\n"

INTRO = r"""\section{Introduction}
\label{sec:intro}

Time-series foundation models are large neural networks, pre-trained on many series and then applied
to new series without task-specific training. On 31 August 2026 Google Research released TimesFM-3, a
330-million-parameter decoder-only transformer and the first member of its family designed for
multivariate forecasting, which its developers report as the top-ranked pre-trained model on three
public benchmarks \citep{timesfm3blog}. For applied forecasting the relevant question is whether such a
model should be used, in preference to a classical method such as ARIMA, for the series at hand; the two
families also differ in cost, interpretability, the basis of their prediction intervals and the terms
under which they may be used (\sectionref{sec:operational}).

Published benchmarks are poorly suited to answering that question. Of 401 datasets used to evaluate
22 time-series foundation models, only about 6\% had never appeared in any model's pre-training
corpus, and even a 0.1\% overlap can move the mean absolute percentage error by 8 to 29 percentage
points \citep{meyer2025leakage}. Foundation-model evaluations have also been criticised for comparing
against under-tuned classical baselines rather than the combinations that win forecasting competitions
\citep{makridakis2020m4}. This study therefore generates its own evaluation data. Under a known
data-generating process (DGP) the foundation model cannot have seen the series, because they did not
exist before the experiment, and the model families searched by AutoARIMA and AutoETS contain the true
process of the linear and exponential-smoothing DGPs. What the design excludes is contamination at the
level of the realisation; what it cannot exclude is familiarity at the level of the family, because
TimesFM-3 is pre-trained partly on synthetic series \citep{timesfm3blog}. Such familiarity cannot be
measured here, and its direction cannot be assumed: synthetic corpora contain autoregressive and seasonal
structure, resembling D1--D5, but also level shifts, piecewise trends and sparse spikes, resembling
D6--D8. No conclusion of this paper relies on its direction.

The aim of the study is exploratory: to describe, under controlled conditions, how the accuracy of
TimesFM-3 relative to classical methods varies across regimes, and to derive diagnostic baselines for
when it may be preferred and when it should not. It proposes no new estimator, test or theory. The
design can establish what TimesFM-3 does but not why: the 330 million parameters have no individual
interpretation and the pre-training corpus cannot be inspected, so explanations of its behaviour offered
here are interpretations consistent with the measurements, not findings. The measurements concern one
model, one checkpoint and univariate zero-shot use, and they do not support general statements about
foundation models as a class.

TimesFM-3 is compared with seasonal naive, Theta, AutoETS, AutoARIMA and an equal-weight combination of
the last three on 7\,200 series from nine DGPs, four lengths from 24 to 200 observations and three
horizons, under a protocol pre-registered before any forecast was produced; every departure from it is
recorded. The evaluation is then extended with stronger benchmarks and two further foundation models,
tested for representativeness and robustness, and repeated on 1\,000 M4 monthly series.
\sectionref{sec:timesfm} describes TimesFM-3, \sectionref{sec:design} the design and
\sectionref{sec:results} the pre-registered results. \sectionref{sec:extended} extends the evaluation,
\sectionref{sec:robustness} examines representativeness and robustness, and \sectionref{sec:realdata}
turns to M4. \sectionref{sec:operational} covers operational considerations,
\sectionref{sec:discussion} discusses the evidence, and \sectionref{sec:conclusion} concludes;
reproducibility details are in \sectionref{sec:repro}.

\subsection{Related work}
\label{sec:related}

TimesFM \citep{das2024timesfm}, Chronos \citep{ansari2024chronos}, Moirai \citep{woo2024moirai},
TimeGPT \citep{garza2023timegpt} and Lag-Llama \citep{rasul2023lagllama} established that a single
pre-trained network can forecast unseen series zero-shot, and GIFT-Eval \citep{aksu2024gifteval} and
fev-bench \citep{shchur2025fevbench} supplied common benchmarks that include AutoARIMA, AutoETS and
seasonal naive among their baselines. The critical literature has grown alongside: \citet{meyer2025leakage}
on contamination, and \citet{adler2026calibrated}, who found on six public datasets that the calibration
error of five foundation models grows with forecast length. The present study differs from the latter in
using generated rather than public data, in testing accuracy differences with multiplicity control
rather than only summarising calibration, and in evaluating TimesFM-3. Applied comparisons on real data
are appearing in several fields---\citet{chu2026influenza} compare six foundation models with SARIMA on
influenza surveillance data---but they cannot say why a model works, because the generating mechanism is
unknown.

The design follows a pattern established in this journal, a controlled simulation over several DGPs
followed by an empirical application \citep{berger2025deep, chu2026intervals, lisi2025multiple}, and it
checks the realism of the simulated series in a feature space, as in \citet{kang2017instance} and
\citet{talagala2023metalearning}. AutoARIMA and AutoETS follow the Hyndman--Khandakar procedures
\citep{hyndman2008forecast, hyndman2002statespace}, Theta won M3 \citep{assimakopoulos2000theta}, and the
combination is included because combinations are the standard against which competition entries are
judged \citep{makridakis2020m4}. Evaluation follows the scale-free conventions of
\citet{hyndman2006mase} and the M5 competition \citep{makridakis2022m5, makridakis2022m5unc} and avoids
the pitfalls catalogued by \citet{hewamalage2023evaluation}.

\section{The TimesFM-3 model}
\label{sec:timesfm}

This section describes the architecture and pre-training data of TimesFM-3
(\sectionref{sec:tfm-architecture}) and the checkpoint and configuration used
(\sectionref{sec:tfm-config}).

\subsection{Architecture and pre-training data}
\label{sec:tfm-architecture}

TimesFM-3 is the third generation of the decoder-only TimesFM family \citep{das2024timesfm,
timesfm3blog}. Each input series is normalised and divided into non-overlapping patches of 32 time
points, each embedded as a token; 20 transformer layers with model dimension 1280 and 16 attention
heads give about 330 million parameters (the checkpoint loaded here has 330\,710\,976). Layers of causal
attention along time alternate with layers of attention across variates, so target series and covariates
can be processed jointly, and a contiguous patch masking scheme produces the whole horizon in one forward
pass, in output patches of 64 points. For each step the model returns nine quantiles, the 10th to the
90th percentile, and its point forecast is the median \citep{timesfm3blog, timesfm3card, timesfm3repo}.
These details are as reported by the developers (blog post and model card, accessed 23 September 2026).
The pre-training corpus of more than one trillion time points combines the GIFT-Eval pre-training
collection, Wikipedia page views to November 2023, Google Trends queries to the end of 2022, and
synthetic and augmented series \citep{timesfm3card}.

\subsection{Checkpoint and configuration}
\label{sec:tfm-config}

The weights (\code{google/\allowbreak timesfm-3.0-pytorch} on the Hugging Face Hub) are loaded with
version 3.0.1 of the \pkg{timesfm} \proglang{Python} package \citep{timesfm3repo, timesfm3card} and are
licensed for non-commercial use only (\sectionref{sec:operational}). The model is used zero-shot: it
receives only the raw context, with no fine-tuning, covariates or seasonal period, through
\code{predict\_batch} with its default settings (no symmetric averaging, no positivity constraint,
sorted quantiles, 32-bit arithmetic). A context shorter than the model's working length is left-padded
with zeros and masked, so at $n = 24$ the model sees one partly filled patch; the maximum context of
15\,360 points truncates no series in this study, and a series forecast alone or inside a batch of other
lengths gives quantiles that agree to within $2 \times 10^{-5}$. Because no quantile outside the 10th and
90th percentiles is available, the widest interval that can be formed is the nominal 80\% interval. The
weights and code are public and the checkpoint is fixed, so every forecast can be regenerated
(\sectionref{sec:repro}); the developers' own evaluator settings are examined in \sectionref{sec:tfm-check}.

"""

BACK = r"""
\section*{Acknowledgements}
First and foremost, the authors thank Allah, the Almighty, for everything He has given them, including
the ability to complete this work. The authors used a large language model to improve the language and
readability of this manuscript and to assist with the implementation of the simulation code; they
reviewed and edited all content and take full responsibility for it.

\section*{Funding}
No funding was received for this work.

\section*{Conflict of interest}
The authors declare no conflicts of interest.

\section*{Ethics approval}
Not applicable; the study uses simulated data and the publicly available M4 competition data, and
involves no human participants. No material is reproduced from other sources.

\section*{Data availability statement}
DATA_STATEMENT

\section*{Author e-mail addresses}
Ebrahim Khaled Ebrahim, ebrahimkhaled@alexu.edu.eg; Somaia Mohamed Ali, somaia.said@alexu.edu.eg;
Ahmed El-Kotory, ahmed.elkatory@alexu.edu.eg.

"""


def main():
    s = P.read_text(encoding="utf-8")
    # 1. statements out of the front matter
    a = s.index(FRONT_STATEMENTS_START)
    b = s.index(FRONT_STATEMENTS_END) + len(FRONT_STATEMENTS_END)
    front = s[a:b]
    data = front[front.index("\\textbf{Data availability statement:}") + len("\\textbf{Data availability statement:}"):]
    data = data[:data.index("\n\n")].strip()
    s = s[:a] + "\\linenumbers\n\n" + s[b:]
    # 2. intro + model section
    a = s.index("\\section{Introduction}")
    b = s.index("\\section{Design of the simulation study}")
    s = s[:a] + INTRO + s[b:]
    # 3. back matter before the bibliography, replacing the old data-availability section
    a = s.index("\\section*{Data and code availability}")
    b = s.index("\\bibliography{refs}")
    old = s[a:b]
    tail = old[old.index("The raw forecasts"):].strip() if "The raw forecasts" in old else ""
    s = s[:a] + BACK.replace("DATA_STATEMENT", data + ("\n\n" + tail if tail else "")) + s[b:]
    P.write_text(s, encoding="utf-8")
    print("front statements moved to the back; introduction and model section condensed")


if __name__ == "__main__":
    main()
