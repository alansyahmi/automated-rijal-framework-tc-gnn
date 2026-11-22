# External Validation Dataset Report: al-Dhahabi's *al-Kashif* (Book 1616)

## 1. Provenance Verification of Shamela4 `narrators.csv` (`الرتبة عند الذهبي`)

- Verified **`5,136 / 5,370` (95.64%)** of Shamela4 `narrators.csv` `الرتبة عند الذهبي` strings directly inside Book `1616` (*al-Kashif*) after normalizing `بن`/`ابن`.
- Because `narrators.csv` covers only `5,370` narrators and occasionally truncates multi-clause verdicts (e.g., *Ibrahim b. Tahman*), this dataset extracts all **`7,181`** entries directly from raw `1616__الكاشف.../pages.jsonl` with printed volume/page provenance.

## 2. Parsing, Linking & Mapped-Term Coverage

- **Total *al-Kāshif* entries parsed:** `7,181`
- **Unambiguously linked to *Taqrīb* `entry_id`:** `5,640 / 7,181` (**78.54%** of *al-Kāshif*, **63.89%** of *Taqrīb*)
- **Linked entries with mapped 3-tier grade:** `3,706 / 5,640` (**65.71%**); remaining `1,934` are silent/biographical or mixed/contested (`unmapped`, never guessed).

| Link Method | Count |
|---|---:|
| `shamela_crosswalk` | 3,447 |
| `n4_unique` | 974 |
| `n3_unique` | 705 |
| `n4_sigil_canon` | 358 |
| `n3_sigil_canon` | 125 |
| `n4_sigil_subset` | 31 |

| Mapped 3-Tier Label (Linked Set) | Count |
|---|---:|
| `thiqah_level` | 2,059 |
| `unmapped` | 1,934 |
| `saduq_level` | 1,111 |
| `weak_and_below` | 536 |

## 3. Verbatim Overlap Audit vs `taqrib_text_verbatim`

- **Mapped linked entries with `verbatim_overlap = True`:** `1,169 / 3,706` (**31.54%**).
- **Comparison with `main` v2.0 `24.8%` finding:** In `main` v2.0 Part D.3, `24.8%` measured exact substring overlap of Shamela `narrators.csv` `الرتبة عند الذهبي` (short editorial snippets) inside `taqrib_text_verbatim`. Extracting full multi-word verdict spans directly from `1616` (e.g., `قال أحمد ثبت في كل المشايخ`) reduces exact full-span verbatim overlap while short single-word verdicts (`ثقة`, `صدوق`, `ضعيف`, `صحابي`) still match verbatim in *Taqrīb*; both the full linked set and the strict **non-verbatim subset** are preserved for P5 evaluation.

## 4. Preview 3-Tier Convergent Agreement (`B` vs `E2` vs *al-Kāshif*)

| Subset | `score_B` (Ibn Hajar) Match | `score_E2` (Tahrir) Match |
|---|---:|---:|
| Full linked mapped set | `2,283/3,227` (**70.75%**) | `2,371/3,304` (**71.76%**) |
| Non-verbatim subset (`verbatim_overlap=False`) | `1,465/2,186` (**67.02%**) | `1,446/2,237` (**64.64%**) |
