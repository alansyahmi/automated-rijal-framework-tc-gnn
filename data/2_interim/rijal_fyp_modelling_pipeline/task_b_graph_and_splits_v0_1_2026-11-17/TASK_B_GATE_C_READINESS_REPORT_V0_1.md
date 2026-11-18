# Task B Graph, Narrator-Disjoint Splits, and Gate C Readiness Report v0.1 (TODO Lines 54-59)

**Status:** constructed zero-leakage transmission graph (`Bukhari` isnads + `Tahdhib al-Kamal` teacher/student lists) and narrator-disjoint stratified `70/15/15` Train/Val/Test splits (`seed=20261117`). Leakage and split-disjointness assertions passed.

## 1. Validated Graph Coverage
- Total directed edges across high-confidence Task A nodes (`7,961`): **6141** (`{'bukhari_isnad_edge': 4740, 'tahdhib_alkamal_rawa_an': 726, 'tahdhib_alkamal_rawa_anhu': 675}`)
- Edges with BOTH endpoints inside the `4,830`-node eligible Task B cohort: **2494** (`{'bukhari_isnad_edge': 2015, 'tahdhib_alkamal_rawa_an': 256, 'tahdhib_alkamal_rawa_anhu': 223}`)
- Eligible narrators with graph degree `>= 1`: **1313 / 4830** (`27.2%`)
- *Tahdhīb al-Kamāl* (`1716`) entries matched uniquely: `788`

## 2. Narrator-Disjoint Stratified Splits (`N = 4,830` Eligible Narrators)
- Partition totals: `{'test': 725, 'train': 3380, 'val': 725}` (`0` overlap on `entry_id` or `shamela_narrator_id`)
- Source-work overlap note (`TODO` line 54): the same classical reference collections (especially `تهذيب الكمال` and `الجرح والتعديل`) supply independent non-*Taqrīb* passages across partitions; all narrator identities and *Taqrīb*-derived text remain strictly disjoint and excluded.

## 3. Per-Rank Split Distribution (`12` Original Ranks Preserved)
- Rank **1**: total=`373` | train=`261` | val=`56` | test=`56`
- Rank **2**: total=`250` | train=`174` | val=`38` | test=`38`
- Rank **3**: total=`1640` | train=`1148` | val=`246` | test=`246`
- Rank **4**: total=`1083` | train=`759` | val=`162` | test=`162`
- Rank **5**: total=`577` | train=`403` | val=`87` | test=`87`
- Rank **6**: total=`91` | train=`63` | val=`14` | test=`14`
- Rank **7**: total=`114` | train=`80` | val=`17` | test=`17`
- Rank **8**: total=`302` | train=`212` | val=`45` | test=`45`
- Rank **9**: total=`288` | train=`202` | val=`43` | test=`43`
- Rank **10**: total=`91` | train=`63` | val=`14` | test=`14`
- Rank **11**: total=`5` | train=`3` | val=`1` | test=`1`
- Rank **12**: total=`16` | train=`12` | val=`2` | test=`2`
