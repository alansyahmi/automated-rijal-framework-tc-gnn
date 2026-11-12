import unittest

from dataset_discovery.target_feasibility.audit_target_feasibility import (
    build_crosswalk,
    field_stats,
    normalize_name,
    parse_biography,
)


class TargetFeasibilityHelpersTest(unittest.TestCase):
    def test_normalization_is_conservative_and_preserves_ta_marbuta(self):
        self.assertEqual(normalize_name("أَحْمَدُ ـ بْنُ مُحَمَّدٍ"), "احمد بن محمد")
        self.assertEqual(normalize_name("فاطمة"), "فاطمة")
        self.assertNotEqual(normalize_name("فاطمة"), normalize_name("فاطمه"))

    def test_parse_biography_preserves_repeated_original_values(self):
        bio, status = parse_biography('{"summary":[["الرتبة عند ابن حجر","ثقة"],["الرتبة عند ابن حجر","ضعيف"]]}')
        self.assertEqual(status, "valid")
        self.assertEqual(bio["الرتبة عند ابن حجر"], ["ثقة", "ضعيف"])

    def test_field_stats_counts_conflicting_values_as_ambiguous(self):
        records = [{"grade": "ثقة"}, {"grade": "ثقة"}, {"grade": ["ثقة", "ضعيف"]}, {"grade": None}]
        distribution, counts = field_stats(records, lambda row: row["grade"] if isinstance(row["grade"], list) else [row["grade"]])
        self.assertEqual(distribution, {"ثقة": 3, "ضعيف": 1})
        self.assertEqual(counts, {"labelled": 3, "missing": 1, "ambiguous": 1})

    def test_numeric_id_coincidence_does_not_create_crosswalk_match(self):
        shamela = [{"id": 7, "short_name": "اسم مختلف", "long_name": "اسم مختلف"}]
        hadith = {"7": {"id": 7, "name": "راو آخر", "data": {}}}
        rows = build_crosswalk(shamela, hadith)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["match_result"], "unmatched_candidate")
        self.assertEqual(rows[0]["verification_status"], "unmatched_conservative_search")

    def test_normalized_name_candidate_is_never_marked_verified(self):
        shamela = [{"id": 9, "short_name": "احمد بن محمد", "long_name": "احمد بن محمد"}]
        hadith = {"29": {"id": 29, "name": "أَحْمَدُ بْنُ مُحَمَّدٍ", "data": {}}}
        rows = build_crosswalk(shamela, hadith)
        self.assertEqual(rows[0]["matching_method"], "normalized_primary")
        self.assertEqual(rows[0]["verification_status"], "unverified_candidate")
        self.assertEqual(rows[0]["confidence"], "medium_candidate")

    def test_duplicate_candidate_names_remain_separate_ambiguous_rows(self):
        shamela = [
            {"id": 9, "short_name": "احمد بن محمد", "long_name": "احمد بن محمد"},
            {"id": 10, "short_name": "أحمد بن محمد", "long_name": "أحمد بن محمد"},
        ]
        hadith = {"29": {"id": 29, "name": "أَحْمَدُ بْنُ مُحَمَّدٍ", "data": {}}}
        rows = build_crosswalk(shamela, hadith)
        self.assertEqual({row["shamela_id"] for row in rows}, {"9", "10"})
        self.assertTrue(all(row["verification_status"] == "unverified_candidate" for row in rows))


if __name__ == "__main__":
    unittest.main()
