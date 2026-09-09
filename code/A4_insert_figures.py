"""Insert the paper's four figures into SHARH_ARABIC.md, each with an Arabic caption.

The captions do not merely name the figure; they tell the reader what to LOOK at in it and
tie it back to the number in the text, which is the point of putting a figure in a teaching
document at all. Anchors are short and unique so they survive later edits to the surrounding
prose. Idempotent: a figure already present is not inserted twice.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOC = Path(__file__).resolve().parent.parent / "SHARH_ARABIC.md"

FIGURES = [
    (
        "fig1",
        "كل واحدة ليها seed ثابتة",
        """

![شكل 1](figures/fig1_example_series.pdf)

**شكل 1 — عيّنة واحدة من كل عملية من التسعة (عند `n = 96`).** الجزء الرمادي هو البيانات اللي
الموديل بيشوفها، والجزء الملوّن في الآخر هو الـ 12 نقطة المخبّية اللي بنقيس عليها. بصّ على `D6`:
الكسر الهيكلي واضح عند النقطة 67 تقريباً — يعني `0.7 × 96` بالظبط زي ما صمّمناه. وبصّ على `D8`:
معظمها أصفار، وده اللي هيبوّظ الـ `MAPE` بعدين.
""",
    ),
    (
        "fig2",
        "**مش محتاج تعرف** أنهي طريقة تختار",
        """

![شكل 2](figures/fig2_mase_ratio.pdf)

**شكل 2 — دقة `TimesFM-3` بالنسبة لأحسن طريقة كلاسيكية في كل خلية.** العمود اللي **تحت** الصفر
معناه `TimesFM-3` أدق، واللي **فوق** الصفر معناه الكلاسيكي أدق. شوف `D8` (الطلب المتقطع) نازل
تحت بوضوح في الأطوال الأربعة، و`D4` (الموسمية) طالع فوق في الأربعة — دول النظامين الحاسمين
اللي هنتكلم عنهم في 8.5. والباقي قريب من الصفر، يعني تعادل.
""",
    ),
    (
        "لازم تبص على **العرض** معاها",
        "لازم تبص على **العرض** معاها",
        """

![شكل 3](figures/fig3_coverage.pdf)

**شكل 3 — التغطية الفعلية للفترات مقابل المطلوب** (الخط المتقطّع)، بمتوسط على العمليات التسعة.
لاحظ إن `TimesFM-3` ماشي على الخط المطلوب تقريباً في كل الأطوال، بينما الكلاسيكي **بيقصّر** عند
`n = 24` و**بيزوّد** من `n = 96`. ⚠️ بس افتكر التحذير فوق: ده **المتوسط**، والانحراف الحقيقي
لكل خلية أكبر 3 مرات.
""",
    ),
    (
        "fig4",
        "قرارك التجاري بيواجهها فعلاً.",
        """

![شكل 4](figures/fig4_horizon.pdf)

**شكل 4 — الدقة حسب طول الأفق**، مقسومة على النظامين. الشمال: العمليات اللي فيها موديل كلاسيكي
صح (`D1`–`D5`). اليمين: اللي مفيهاش (`D6`–`D9`). كل الطرق بتسوء كل ما الأفق يطول — وده طبيعي.

⚠️ **بس خد بالك من قراءة غلط هنا:** `TimesFM-3` مبيّن الأقل في **اللوحتين**، وده مش بيناقض إن
الكلاسيكي كسب خلايا أكتر — لأن **المتوسط** بيخلط الخلايا اللي الكلاسيكي كسبها بالخلايا اللي
**وقع** فيها، وخلية واحدة كارثية (زي `Theta` بـ 4.16 على `D4`) بتحرّك المتوسط أكتر بكتير من
كذا مكسب صغير.
""",
    ),
]


def main() -> None:
    s = DOC.read_text(encoding="utf-8")
    inserted, skipped, missing = 0, 0, []

    for tag, anchor, block in FIGURES:
        marker = block.strip().splitlines()[0]  # the ![...] line
        if marker in s:
            skipped += 1
            continue
        idx = s.find(anchor)
        if idx == -1:
            missing.append(tag)
            continue
        end = idx + len(anchor)
        s = s[:end] + block + s[end:]
        inserted += 1

    DOC.write_text(s, encoding="utf-8")
    print(f"inserted {inserted}, already present {skipped}")
    if missing:
        print("ANCHOR NOT FOUND for:", ", ".join(missing))


if __name__ == "__main__":
    main()
