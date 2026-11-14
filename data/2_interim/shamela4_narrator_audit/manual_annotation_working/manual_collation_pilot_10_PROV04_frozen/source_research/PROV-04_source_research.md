# PROV-04 Source Research Note (Working Draft)

## Scope
This memo records local corpus verification and historical context for `PROV-04` (`HadithDB` narrator ID `278`, `قَيْسُ بْنُ حَفْصٍ`), covering both candidate entries in `Taqrib al-Tahdhib` (`3076`, local p. 456, sequence 5554):
- `PROV-04-C01`: Taqrib entry `5569` (confirmed match).
- `PROV-04-C02`: Taqrib entry `5570` (rejected homonym mismatch).

No printed page image was inspected; all readings come from the local Shamela4 digital corpus (`3076`, `1615`, `1716`) and the raw local snapshot `narrators_db.json` (`/278`).

## Identity Resolution and Homonym Disambiguation

### PROV-04-C01 (Taqrib 5569) -> Confirmed Match
Grade-free identity bridge:
- `EVID-PROV-04-C01-ID02` isolates only the non-grade biographical fields from `narrators_db.json` `/278`: `الاسم` (`: قيس بن حفص بن القعقاع`), `الكنية` (`أبو محمد`), `النسب` (`التميمي, الدارمي مولاهم, البصري`), `علاقات الراوي` (`مولى الدارميين`), and `تاريخ الوفاة` (`227 هـ`), explicitly excluding `الرتبة عند ابن حجر`, `طبقة رواة التقريب`, and `الجرح والتعديل` (which remain preserved separately in `EVID-PROV-04-C01-DATA01`).
- `EVID-PROV-04-C01-ID01` (`Ibn Abi Hatim`, `al-Jarh wa-al-taʿdil`, vol. 7, p. 95, entry `546`, seq `3013`) identifies `قيس بن حفص بن القعقاع الدارمي بصرى أبو محمد مولى`.
- `Tahdhib al-Kamal` (`1716`, vol. 24, pp. 21-23, entry `4899`, seqs `12534-12536`) identifies `قَيْس بن حَفْص بن القعقاع التَّمِيمِيّ الدارمي، مولاهم، أبو محمد البَصْرِيّ` and cites al-Bukhari for his death in `227 AH` or thereabouts. Because Taqrib draws heavily on al-Mizzi's `Tahdhib al-Kamal`, correspondence between `4899` and `5569` may reflect literary dependence rather than independent witness testimony.

### PROV-04-C02 (Taqrib 5570) -> Confirmed Mismatch
`Taqrib` entry `5570` reads: `٥٥٧٠- قيس ابن حفص آخر بصري سكن مصر يكنى أبا محمد مقبول من الثانية عشرة مات سنة إحدى وثمانين تمييز`.
`Tahdhib al-Kamal` (`1716`, vol. 24, p. 24, entry `4900` `تمييز`, seq `12537`) explicitly disambiguates this second Qays ibn Hafs: Basran, kunyah Abu Muhammad, settled in Egypt, chamberlain to judge Bakkar ibn Qutaybah, noted by Abu Sa'id ibn Yunus, and died in Dhu al-Hijjah `281 AH`. Although sharing name, kunyah, and Basran origin with HadithDB `278`, chronological generation (12th tabaqah, d. `281 AH`), Egypt residence, and missing Darimi/Qa'qa' lineage establish a homonym mismatch. Candidate `PROV-04-C02` is therefore kept strictly for audit completeness and excluded from any accepted target extract (`target_task_scope=not_in_defined_task`, unranked).

## Statement Segmentation and Cautions
For `PROV-04-C01` (`5569`), three statements are segmented:
1. `PROV-04-C01-S01`: `ثقة له أفراد` (`qualified_narrator_grade`, with `grade_base_verbatim=ثقة` and `grade_qualification_verbatim=له أفراد`). The Arabic phrasing of `له أفراد` is preserved without translating or forcing a negative interpretation; both `taqrib_rank_number` (`rank_status=unranked`) and `target_task_scope` (`unresolved`) remain open for Pass 2 adjudication.
2. `PROV-04-C01-S02`: `من العاشرة` (`descriptive_or_generational_status`, tabaqah 10, not a reliability rank).
3. `PROV-04-C01-S03`: `مات سنة سبع وعشرين` (`biographical_or_factual_statement`, `temporal_policy_result=cannot_assess`).

## Earlier Evaluative Context (Distinct from Taqrib Wordings)
`EVID-PROV-04-C01-HIST-CONTEXT01` preserves earlier reports collected in `al-Mizzi` entry `4899` (alongside `Ibn Abi Hatim` `546`):
- Yahya ibn Ma'in: `ثقة`
- Al-Ijli: `لا بأس به، كتبت عنه شيئا يسيرا`
- Abu Hatim: `شيخ`
Note also in `Tahdhib al-Kamal` p. 23 footnote (1) that al-Mizzi left a blank in his text for an intermediary authority before Yahya ibn Ma'in (`al-Rawandi`). These reports are kept strictly contextual and do not establish who authored Taqrib's summary wording `ثقة له أفراد`.
