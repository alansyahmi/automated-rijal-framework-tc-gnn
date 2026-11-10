"""Regression cases from original Shamela4 tuples and metadata categories."""
import unittest

from dataset_discovery.Shamela4.tuple_validation_v3 import (
    classify_tuple,
    quotation_citation_separability,
)


class TupleValidationV3Tests(unittest.TestCase):
    def test_suffix_category_has_suffix_specific_separability_metadata(self):
        self.assertEqual(
            quotation_citation_separability(
                "unnumbered_suffix_variant_without_reversal_evidence"
            ),
            "suffix_occurrences_are_locator_variants; other tuples under this ID may differ",
        )

    def test_arabic_prose_cues_precede_secondary_locator(self):
        # Original source_id 137006, narrator 4842.
        result = classify_tuple(
            "سنن البيهقي الكبرى: (7/ 318) برقم: (14987)",
            "وقال أبو عمرو بن العلاء كان يعاب على قتادة، وعمرو بن شعيب أنهما كانا لا يسمعان شيئا إلا حدثا به\nتهذيب التهذيب (3/ 277)",
        )
        self.assertEqual(result["pattern"], "citation_only_then_locator_bearing_prose")

    def test_citation_only_pair_is_not_prose(self):
        # Original suffix variant for source_id 25200, narrator 3234.
        result = classify_tuple(
            "صحيح ابن خزيمة: (1/ 470) (بدون ترقيم)",
            "صحيح ابن خزيمة (1/ 470) (بدون ترقيم)",
        )
        self.assertEqual(result["pattern"], "citation_only_pair")

    def test_compound_multiline_citation_and_commentary_is_not_reversal(self):
        # Original source_id 92839, narrator 3383.
        result = classify_tuple(
            "أشعث بن إسحاق أسقطه أحمد بن صالح حين حدثنا به، فحدثني به عنه موسى بن سهل الرملي",
            "سنن أبي داود (3/ 45) برقم (2775) \nسمعت عبدان الأهوازي يقول سمعت أبا داود السجستاني يقول أحمد بن صالح ليس هو كما يتوهم الناس، يعني ليس بذلك في الجلالة. \nالكامل في الضعفاء (1/ 295)",
        )
        self.assertEqual(result["pattern"], "prose_then_locator_bearing_commentary")

    def test_unrecognised_prose_pattern_remains_unresolved(self):
        # Original source_id 23583, narrator 659; prose starts with «صدوق اختلف قول». 
        result = classify_tuple(
            "المنتقى: (1/ 143) برقم: (396)",
            "صدوق اختلف قول ابن معين فيه\nالكاشف في معرفة من له رواية في الكتب الستة (2/ 117)",
        )
        self.assertEqual(result["pattern"], "unresolved_tuple_structure")


if __name__ == "__main__":
    unittest.main()
