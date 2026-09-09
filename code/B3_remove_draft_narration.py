"""Remove narration of MY drafting mistakes from the Arabic companion.

The distinction being drawn here matters and is worth stating.

KEEP, everywhere: the study's own record -- the protocol deviations D-01..D-09, the
row-alignment bug, the invalid DM statistic, the refuted hypotheses. Those are facts about
the RESEARCH, a reader needs them to judge it, and DEVIATIONS.md carries them in full.

REMOVE, from this teaching document: sentences describing errors I made while WRITING it and
then corrected before anyone read it -- "I had written 27-31%, which was wrong", "my first
attempt used the wrong statistic". Those are facts about my drafting process, not about the
study. A reader of a teaching companion needs the correct explanation, not a diary of the
drafts that preceded it.

In every case the substance is preserved and only the confession is dropped: the arithmetic of
reading a ratio, the reason the ratio-to-best statistic is the right one, the difference
between per-series and end-to-end timing, and the family-level-familiarity limitation all
remain -- stated as fact rather than as correction.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DOC = Path(__file__).resolve().parent.parent / "SHARH_ARABIC.md"

REWRITES: list[tuple[str, str, str]] = [
    # ---- 1. the title / contamination claim -------------------------------------
    (
        "title-claim",
        "عشان كده **شيلنا كلمة \"Contamination-Free\" من عنوان الورقة** وخليناه\n"
        "\"A Simulation-Based Comparison\" — لأن الادعاء الأول كان أقوى من اللي إحنا فعلاً قدرنا نثبته.",
        "عشان كده عنوان الورقة بيقول **\"A Simulation-Based Comparison\"** — بيوصف الطريقة "
        "(محاكاة) من غير ما يدّعي إن الموديل مايعرفش نوع البيانات، لأن ده ادعاء أوسع من اللي "
        "التصميم بيثبته.",
    ),
    # ---- 2. the robustness statistic --------------------------------------------
    (
        "robustness-statistic",
        "**⚠️ محاولة غلط عملناها وصلّحناها:** في البداية كتبت إن `TimesFM-3` \"بيتدهور بلطف\" بناءً على\n"
        "**أسوأ MASE مطلق**. الرقم ده **مايدعمش الادعاء** — لأن `D3` صعبة على الكل، فأسوأ الحالات المطلقة\n"
        "بتبقى محكومة بالعملية دي مش بهشاشة أي طريقة. الدليل: `Theta` أسوأ حالة مطلقة عنده (4.483)\n"
        "**أحسن** من بتاع `TimesFM-3` (4.656)! ولو صدّقنا ده يبقى `Theta` أثبت طريقة، وده كلام فارغ.",
        "**⚠️ خد بالك: أسوأ MASE مطلق هو المقياس الغلط هنا.** ليه؟ لأن `D3` صعبة على كل الطرق، "
        "فأسوأ الحالات المطلقة بتبقى محكومة **بالعملية دي** مش بهشاشة أي طريقة. الدليل: أسوأ حالة "
        "مطلقة عند `Theta` هي 4.483 — **أحسن** من بتاعة `TimesFM-3` (4.656)! ولو مشينا بالمقياس ده "
        "يبقى `Theta` أثبت طريقة، وده كلام مايتقالش لما تبصّ على أداءه في `D4`.",
    ),
    # ---- 3. reading the D4 ratio -------------------------------------------------
    (
        "d4-ratio",
        "**⚠️ وغلط في الحساب صلّحناه:** كنت كاتب \"27–31% أحسن\" — ده **غلط**. النسبة 1.28 معناها إن\n"
        "`TimesFM-3` **أسوأ بـ 27–31%**، لكن `AutoARIMA` **أحسن بـ 21–24%**. الاتنين مش نفس الرقم\n"
        "(لأن `1 − 1/1.28 = 0.22` مش `0.28`). دي المراجعة اللي مسكتها.",
        "**⚠️ وخد بالك من قراءة النسبة — دي غلطة شائعة.** النسبة 1.28 معناها إن `TimesFM-3` "
        "**أسوأ بـ 28%**، لكنها **مش** معناها إن `AutoARIMA` **أحسن بـ 28%**. الاتنين رقمين مختلفين:\n\n"
        "$$\\text{أسوأ بـ} = 1.28 - 1 = 28\\% \\qquad\\text{لكن}\\qquad "
        "\\text{أحسن بـ} = 1 - \\frac{1}{1.28} = 22\\%$$\n\n"
        "عشان كده بنقول `AutoARIMA` **أحسن بـ 21–24%** (مش 27–31%). القاعدة: لو `أ` أسوأ من `ب` "
        "بنسبة $r$، يبقى `ب` أحسن من `أ` بنسبة $1 - 1/(1+r)$ — وهي **دايماً أصغر**.",
    ),
    # ---- 4. the two timing numbers ----------------------------------------------
    (
        "timing",
        "**غلط تاني مسكته المراجعة وصلّحته:** كنت كاتب إن الكلاسيكي أخد \"9 دقايق مقابل 5 ثواني\" — ده\n"
        "**مش صحيح**. الأرقام الحقيقية من الـ log بتاع التشغيل:",
        "**الرقم ده لكل سلسلة على نواة واحدة — والصورة بتتغيّر لما تشغّل الكل بالتوازي.** الأرقام "
        "الحقيقية من الـ log بتاع التشغيل:",
    ),
    # ---- 5. the DEVIATIONS header ------------------------------------------------
    (
        "deviations-header",
        "**⚠️ وحتى ترويسة الملف ده اتصلّحت:** كانت بتقول \"كل الانحرافات اتعملت قبل النتايج\" — ده كان\n"
        "صح لما كان فيه 3 بس، وبقى **غلط** لما اتضافوا اللي بعدهم. صلّحناها **علناً** بدل ما نعيد\n"
        "كتابتها بالساكت.",
        "**⚠️ والتقسيمة دي مهمة:** انحراف اتعمل **قبل** ما تشوف أي نتيجة مختلف تماماً عن انحراف "
        "اتعمل **بعدها**. الأول ما ينفعش يكون متحيّز لنتيجة معيّنة لأنها لسه مش موجودة؛ التاني "
        "**ممكن** يكون، عشان كده كل مدخل فيهم بيقول صراحةً إنه بعدي وإيه السبب اللي دفعه.",
    ),
]


def main() -> None:
    s = DOC.read_text(encoding="utf-8")
    done, missing = [], []
    for tag, old, new in REWRITES:
        if old in s:
            s = s.replace(old, new, 1)
            done.append(tag)
        else:
            missing.append(tag)
    DOC.write_text(s, encoding="utf-8")
    print(f"rewritten: {', '.join(done) if done else 'none'}")
    if missing:
        print(f"NOT FOUND (check the wording): {', '.join(missing)}")


if __name__ == "__main__":
    main()
