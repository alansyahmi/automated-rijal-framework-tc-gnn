# Fwaed verification

## Narrator 6142: raw structure comparison

- Narrator row found in original Parquet: yes.
- Garh grouped entries: 16; fwaed grouped entries: 16.
- Exact (category, full-entry) matches between fwaed and garh: 16/16.
- Exact nested entry matches ignoring category: 16/16.
- Each unexpected-label `fwaed` entry is exactly equal to a full `garh` entry, and its raw label is also present among the `garh` group labels. Exact equality is evidence of duplicated nested content, not of why it happened.
- Complete original `fwaed` entries for narrator 6142:

  - `ابن حبان`: `["ذكره ابن حبان في كتاب \" الثقات \"","تهذيب الكمال (27/ 556)",455084]`
  - `ابن حبان`: `["ذكره ابن حبان في \" الثقات \"","تهذيب التهذيب (4/ 74)",480150]`
  - `ابن حبان`: `["وخرج ابن حبان حديثه في « صحيحه »، وكذلك الحاكم","إكمال تهذيب الكمال (11/ 187)",540622]`
  - `ابن حجر`: `["مقبول","تقريب التهذيب (1/ 941)",521983]`
  - `الذهبى`: `["عن: نعيم بن ربيعة، عن: عمر، وربما أرسله","الكاشف في معرفة من له رواية في الكتب الستة (4/ 282)",501137]`
  - `الذهبى`: `["وثق","الكاشف في معرفة من له رواية في الكتب الستة (4/ 282)",501137]`
  - `العجلي`: `["قال أحمد بن صالح العجلي: بصري، تابعي ثقة","إكمال تهذيب الكمال (11/ 187)",540622]`
  - `العجلي`: `["وقال العجلي: بصري تابعي ثقة","تهذيب التهذيب (4/ 74)",480150]`
  - `المزي`: `["عن عمر بن الخطاب (د ت س) في قوله: وإذ أخذ ربك من بني آدم من ظهورهم ذريتهم، وقيل: عن نعيم بن ربيعة (د) ، عن عمر، وهو الصحيح","تهذيب الكمال (27/ 556)",455084]`
  - `الطحاوي`: `["وكان هذا الحديث منقطعا; لأن مسلم بن يسار الجهني لم يلق عمر رضي الله عنه فنظرنا في الذي أخذه عنه، عن عمر من هو","شرح مشكل الآثار (10/ 24)",294209]`
  - `أبو حاتم الرازي`: `["وقال أبو حاتم: لم يسمع من عمر بينهما نعيم بن ربيعة","تحفة التحصيل في المراسيل (1/ 494)",681697]`
  - `أبو زرعة الرازي`: `["قال أبو زرعة: حديثه عن عمر مرسل","تحفة التحصيل في المراسيل (1/ 494)",681697]`
  - `أبو زرعة العراقي`: `["قلت: الراوي عن هؤلاء الثلاثة مرسلا ليس هو الجهني إنما هو","تحفة التحصيل في المراسيل (1/ 494)",681697]`
  - `ابن عساكر`: `["وذكر الحافظ ابن عساكر أنه روى عن ابن عباس، وعبادة بن الصامت، وأبي الأشعث الصنعاني مرسلا","تحفة التحصيل في المراسيل (1/ 494)",681697]`
  - `الترمذي`: `["هذا حديث حسن، ومسلم بن يسار لم يسمع من عمر، وقد ذكر بعضهم في هذا الإسناد بين مسلم بن يسار، وبين عمر رجلا","جامع الترمذي (5/ 158)",101555]`
  - `الحاكم`: `["وخرج ابن حبان حديثه في « صحيحه »، وكذلك الحاكم","إكمال تهذيب الكمال (11/ 187)",540622]`

## Raw fwaed labels and shapes

- Distinct non-empty raw labels: 25 (25 in this corpus); expected-label set size: 13. Two additional group labels (`جرح وتعديل`, `مصادر الترجمة`) have empty lists and zero entries.
- Observed non-empty raw label counts:

  - `أبو حاتم الرازي`: 1
  - `أبو زرعة الرازي`: 1
  - `أبو زرعة العراقي`: 1
  - `إثبات سماع الراوي`: 2376
  - `ابن حبان`: 3
  - `ابن حجر`: 1
  - `ابن عساكر`: 1
  - `الإدراك`: 1429
  - `الإرسال`: 5134
  - `الاختلاط`: 813
  - `الاختلاف في سماع الراوي`: 467
  - `التدليس`: 604
  - `الترمذي`: 1
  - `التضعيف الاستثنائي`: 334
  - `التضعيف الضمني`: 87
  - `التوثيق الاستثنائي`: 136
  - `التوثيق الضمني`: 1573
  - `الحاكم`: 1
  - `الذهبى`: 2
  - `الطحاوي`: 1
  - `العجلي`: 2
  - `المزي`: 1
  - `المفاضلة بين الرواة`: 2557
  - `المفاضلة بين الرواة في بلد`: 42
  - `المفاضلة بين الرواة في راو`: 395

- Unexpected non-empty raw labels: {"أبو حاتم الرازي": 1, "أبو زرعة الرازي": 1, "أبو زرعة العراقي": 1, "ابن حبان": 3, "ابن حجر": 1, "ابن عساكر": 1, "الترمذي": 1, "الحاكم": 1, "الذهبى": 2, "الطحاوي": 1, "العجلي": 2, "المزي": 1}.
- Entry Python-shape counts across corpus: {"list:3": 15963}.
- The 13 labels in the expected list are raw category strings. Repeated three-element serialization, when observed, establishes structural consistency only. It does not independently verify semantic meaning.
- Interpretations involving transmission, chronology, comparison, or implicit accreditation remain hypotheses unless each category's content and scholarly usage are separately validated. Do not map labels directly to graph edges or node features on these data alone.

## Limits

This verifies raw labels, nested shapes, and exact field equality. It does not verify historical speakers, the truth of a category's claim, or the database compiler's intended semantics.
