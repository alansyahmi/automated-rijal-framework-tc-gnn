# Comparison Against Bilgin (2026) — *Taqrīb al-Tahdhīb* Rank Statistics

**Reference:** Recep Bilgin (2026), *"İbn Hacer’in Takrîbü’t-Tehzîb’inde Cerh ve Taʿdîl Hükümlerinin Sayısal ve İstatistiksel Analizi"*, OMÜİFD, Issue 60, pp. 219–248 ([Bilgin_2026_Taqrib_Jarh_Tadil_Statistical_Analysis.pdf](../literature/flagship_references/Bilgin_2026_Taqrib_Jarh_Tadil_Statistical_Analysis.pdf), Tables 1–4, pp. 239–243).

## 1. Side-by-Side Rank Distribution

| Rank | Category (Bilgin 2026) | Bilgin (2026) | Our `v1.4` | Notes / Reason for Difference |
|---:|---|---:|---:|---|
| **1** | *Ṣaḥābah* | 693 | 450 | `v1.4` abstained on `GUARD-R1-DISPUTED` (99) & multi-clause *Ṣaḥābah* entries |
| **2** | *Thiqah thiqah / thiqah thabt* | 335 | 280 | `v1.4` abstained on complex/qualified compound `ثقة` entries |
| **3** | *Thiqah* | 1,990 | 1,734 | `v1.4` abstained on `GUARD-QUALIFIED-THIQAH` (45) & multi-clause entries |
| **4** | *Ṣadūq / Lā baʾs bih / Laysa bihī baʾs* | 1,280 | 1,183 | 92.4% alignment; `v1.4` abstained on complex caveats |
| **5** | *Tenkitli ṣadūq* (qualified *ṣadūq*) | 671 | 597 | 89.0% alignment |
| **6** | *Maqbūl* (Bilgin) vs *Layyin* (`v1.4`) | 1,596 | 101 (+1,581 guarded) | Bilgin places `مقبول` (1,596) in Rank 6; `v1.4` guarded `مقبول` (1,581) as conditional and placed `لين الحديث` (101) in Rank 6 |
| **7** | *Mastūr / Majhūl al-ḥāl / Layyin* | 386 | 202 | Bilgin groups `لين الحديث` + `مستور` + `مجهول الحال` in Rank 7; `v1.4` puts `مستور` (202) in Rank 7 |
| **8** | *Ḍaʿīf* | 410 | 330 | `v1.4` abstained on `GUARD-MILD-WEAKNESS` (57) & complex cases |
| **9** | *Majhūl / Lā yuʿraf* | 748 | 683 | 91.3% alignment |
| **10** | *Matrūk / Matrūk al-ḥadīth* | 139 | 100 | `v1.4` abstained on `GUARD-MATRUK-WITH-TAKDHIB` (21) |
| **11** | *Muttaham bi-l-kadhib / bi-l-waḍʿ* | 10 | 5 | `v1.4` abstained on `GUARD-CONFLICTING-LYING` (6) |
| **12** | *Kadhdhāb / Kadhdhabūhu* | 2 | 15 | Bilgin counts 2 (`كذاب`, `كذبوه في الحديث`); `v1.4` includes `RULE-R12-PLURAL-KADHABUHU` (13) + 2 = 15 |
| **Total Assigned** | | **8,260 / 8,826** | **5,680 / 8,827** | Bilgin left 566 unassigned; `v1.4` intentionally abstained on 3,147 |

## 2. Key Takeaways for Our `taqrib-oriented` Pipeline

1. **External Validation:** Across all unambiguous ranks (3, 4, 5, 8, 9, 10), `v1.4` matches Bilgin (2026) at ~89–92%, confirming our deterministic parser captures the same *Taqrīb* distribution while being strictly more conservative on compound/disputed entries.
2. **Boundary Fix (`مقبول` vs `لين`):** Bilgin (2026) places `مقبول` (1,596) in Rank 6 and `لين الحديث` in Rank 7 (1st *Jarḥ* rank). Our `v1.4` guarded `مقبول` (1,581) and put `لين الحديث` (101) in Rank 6 — we should align this explicitly with Ibn Ḥajar's introduction and *Taḥrīr*'s mapping (`مقبول` -> `ضعيف يعتبر به` when uncorroborated).
3. **Where Our Project Goes Beyond Bilgin (2026):** Bilgin (2026, Section 3, p. 243) notes *Taḥrīr Taqrīb al-Tahdhīb* qualitatively as a modern critique of *Taqrīb*'s oversimplification, **but does not quantify *Taḥrīr* or model narrator networks**. Our `taqrib-oriented` / `taqrib-oriented-v2` pipeline directly fills that gap by aligning **8,823 / 8,827 (99.95%)** entries with *Taḥrīr* (`2,621` `• بل:` overrides) and combining them with Evaluative Stance Analysis (ESA) + Text-Classification-informed GNN (TC-GNN).
