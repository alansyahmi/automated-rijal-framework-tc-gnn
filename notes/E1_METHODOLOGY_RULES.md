# `E₁` & `E₂` Methodological Rules (`taqrib-oriented-simplified`, `DEC-011`)

**Status:** Active methodological specification (`schema_version = 3.1`)  
**Decision Log:** `DEC-011` in [governance/DECISION_LOG.md](../governance/DECISION_LOG.md)  
**Charter Alignment:** [notes/simplified_research_direction.md](simplified_research_direction.md) §4.2, §5, and §9  

---

## 1. Principle: Evidence-First, Not Score-First

In *Taqrīb al-Tahdhīb* (`3076`), Ibn Ḥajar often appends additional descriptors outside the core grade span (`taqrib_target_span`). Under `DEC-011`, **Layer `E₁`** records all qualifying spans in [LAYER_EVIDENCE_LONG_V3.csv](../data/2_interim/rijal_fyp_modelling_pipeline/layered_scores_v3_2026-11-21/LAYER_EVIDENCE_LONG_V3.csv) first, and distinguishes strictly between:

1. **Direct transmission-reliability qualifiers** whose negative impact on *ḍabṭ* (precision) or *ittiṣāl* (continuity) is explicit and uncaptured by `score_B` → **eligible for bounded within-band numeric adjustment**.
2. **Non-transmission praise or ambiguous contextual remarks** → **retained as `0.0`-delta descriptive evidence** (`double_count_check = "descriptive_evidence_only"`).

---

## 2. Classification of `E₁` Terms

| Rule ID | Arabic Pattern | Evidence Role | Weight (in local half-width) | Rationale |
|---|---|---|---|---|
| `qual_ikhtalata` | `اختلط` / confusion | Numeric adjustment | `-0.5` | Direct deterioration of narrator retention (*ḍabṭ*) later in life |
| `qual_sayyi_hifz` | `سيء الحفظ` / poor memory | Numeric adjustment | `-0.5` | Explicit precision defect when outside main rank span |
| `qual_lin` | `لين` / mild weakness | Numeric adjustment | `-0.5` | Explicit transmission softening when outside main rank span |
| `qual_yukhti_yahim` | `يهم` / `يخطئ` / errs | Numeric adjustment | `-0.4` | Explicit transmission-error qualifier when outside main rank span |
| `qual_yudallis` | `يدلس` / conceals teacher | Numeric adjustment | `-0.25` | Transmission-continuity caveat outside main grade term |
| `qual_yursil` | `يرسل` / skips link | Numeric adjustment | `-0.15` | Transmission-continuity caveat outside main grade term |
| `praise_hafiz` | `حافظ` / *ḥāfiẓ* | **Evidence-only (`0.0`)** | `0.0` | Scholarly distinction/memorization title ≠ *Taqrīb* reliability tier override (Charter §5) |
| `praise_faqih` | `فقيه` / jurist | **Evidence-only (`0.0`)** | `0.0` | Jurisprudential stature ≠ transmission reliability (Charter §5) |
| `qual_qalil_hadith` | `قليل الحديث` / few reports | **Evidence-only (`0.0`)** | `0.0` | Transmission volume is descriptive, not reliability |
| `qual_rumiya_bidah` | `رمي ببدعة` / sectarian charge | **Evidence-only (`0.0`)** | `0.0` | Treated conditionally by *ḥadīth* scholars; never penalized by fixed rule |

*(Any qualifier already matched inside `taqrib_target_span` continues to receive `delta = 0.0` with `double_count_check = "inside_rank_span"` to prevent double-counting.)*

---

## 3. Scale-Local Ordinal Bounds (`local_band_half_width`)

A numeric adjustment on an ordinal `0–100` scale must respect both **adjacent rank spacing** and **decision thresholds** on the active scale ([common/rank_scale.py](../common/rank_scale.py)). Fixed global offsets (`4.5455` from `linear_v1`) are removed (`DEC-011`).

For rank $r \in \{1,\dots,12\}$ with score $S(r)$ and threshold set $\mathcal{T}_{\text{scale}}$ (`{80.0, 50.0, 25.0}` on `hukm_v1`):

- **Downward half-width ($\text{direction} < 0$):**
  - If $r = 12$, width $= 0.0$.
  - Otherwise let $g_{\downarrow} = \tfrac{1}{2}\big(S(r) - S(r+1)\big)$.
  - For any threshold $T \in \mathcal{T}_{\text{scale}}$ with $S(r+1) < T \le S(r)$, clamp to $\min\big(g_{\downarrow},\, S(r) - T\big)$ so $S(r) + \Delta \ge T$.
- **Upward half-width ($\text{direction} > 0$):**
  - If $r = 1$, width $= 0.0$.
  - Otherwise let $g_{\uparrow} = \tfrac{1}{2}\big(S(r-1) - S(r)\big)$.
  - For any threshold $T \in \mathcal{T}_{\text{scale}}$ with $S(r) < T \le S(r-1)$, clamp strictly below $T$: $\min\big(g_{\uparrow},\, \max(0.0,\, T - S(r) - 10^{-6})\big)$.

### Resulting Caps on `hukm_v1` vs. `linear_v1`

| Rank $r$ | `hukm_v1` $S(r)$ | Downward Cap (`hukm_v1`) | Upward Cap (`hukm_v1`) | Down/Up Cap (`linear_v1`) |
|---:|---:|---:|---:|---:|
| 1 | `100.0` | `2.5000` | `0.0000` | `4.5455` / `0.0000` |
| 2 | `95.0` | `5.0000` | `2.5000` | `4.5455` / `4.5455` |
| 3 | `85.0` | `5.0000` *(clamped at `T=80`)* | `5.0000` | `4.5455` / `4.5455` |
| 4 | `70.0` | `12.5000` *(stays `≥57.5 > 50`)* | `7.5000` *(stays `<80`)* | `4.5455` / `4.5455` |
| 5 | `45.0` | `2.5000` | `5.0 − 1e-6` *(stays `<50`)* | `4.5455` / `4.5455` |
| 6 | `40.0` | `2.5000` | `2.5000` | `4.5455` / `4.5455` |
| 7 | `35.0` | `2.5000` | `2.5000` | `4.5455` / `4.5455` |
| 8 | `30.0` | `1.5000` *(half of `30→27`)* | `2.5000` | `4.5455` / `4.5455` |
| 9 | `27.0` | `2.0000` *(clamped at `T=25`)* | `1.5000` | `4.5455` / `4.5455` |
| 10 | `15.0` | `5.0000` | `6.0000` *(stays `<25`)* | `4.5455` / `4.5455` |
| 11 | `5.0` | `2.5000` | `5.0000` | `4.5455` / `4.5455` |
| 12 | `0.0` | `0.0000` | `2.5000` | `0.0000` / `4.5455` |

---

## 4. Separation Between `E₁` (*Taqrīb*) and `E₂` (*Taḥrīr*)

Per Charter §5 (*"No hidden inheritance"*):

- **Preserved inheritance (silent editorial continuity):** Where *Taḥrīr* offers no grade change (`observed_agreement`, `observed_no_grade`, or `observed_qualification`), `score_E2` inherits `score_E1` cleanly (plus *Taḥrīr*'s explicit p. 47 bare `ضعيف = 22.0` override when `rank_E2 == 8` and `tahrir_r8_itibar == "False"`).
- **No implicit inheritance on band replacement:** Whenever *Taḥrīr* assigns a new rank band (`observed_dissent` or `observed_maqbul_to_r7` per Intro p. 45), `dissent_carry_e1_ranks` is **`[]`** and `score_E2` initializes purely from `rank_to_score(rank_E2, scale)` (`e1_carry = 0.0`, `double_count_check = "band_replaced_no_e1_inheritance"` or `"band_replaced_maqbul_p45_no_e1_inheritance"`). *Taqrīb*'s unmerged `E₁` qualifier remains recorded in Layer `E₁` rather than silently altering *Taḥrīr*'s independent grade.
