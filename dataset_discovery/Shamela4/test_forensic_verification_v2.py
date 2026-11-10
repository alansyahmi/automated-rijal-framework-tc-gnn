"""Representative classifier cases copied from original Shamela4 tuples."""
import unittest

from dataset_discovery.Shamela4.forensic_verification_v2 import classify_tuple


class ReversalClassifierCases(unittest.TestCase):
    def test_positive_citation_only_then_locator_bearing_prose(self):
        # Original source_id 137006, narrator 4842, evaluator group أبو عمرو بن العلاء.
        result = classify_tuple(
            "سنن البيهقي الكبرى: (7/ 318) برقم: (14987)",
            "وقال أبو عمرو بن العلاء كان يعاب على قتادة، وعمرو بن شعيب أنهما كانا لا يسمعان شيئا إلا حدثا به\nتهذيب التهذيب (3/ 277)",
        )
        self.assertEqual(result["pattern"], "citation_only_then_locator_bearing_prose")
        self.assertEqual(result["certainty"], "confirmed_structure")

    def test_negative_ordinary_quote_then_citation(self):
        # Original source_id 25200, narrator 3234.
        result = classify_tuple(
            "أخبرنا أبو طاهر، قال حدثنا أبو بكر، قال: سمعت محمد بن يحيى يقول: ابن أبي ليلى لم يدرك ابن زيد",
            "صحيح ابن خزيمة (1/ 470)",
        )
        self.assertEqual(result["pattern"], "locator_bearing_prose_then_citation_only")
        self.assertEqual(result["certainty"], "confirmed_non_reversal")

    def test_negative_citation_followed_by_commentary_is_not_reversal(self):
        # Original source_id 92839, narrator 3383; slot 0 is already quotation prose.
        result = classify_tuple(
            "أشعث بن إسحاق أسقطه أحمد بن صالح حين حدثنا به، فحدثني به عنه موسى بن سهل الرملي",
            "سنن أبي داود (3/ 45) برقم (2775) \nسمعت عبدان الأهوازي يقول سمعت أبا داود السجستاني يقول أحمد بن صالح ليس هو كما يتوهم الناس، يعني ليس بذلك في الجلالة. \nالكامل في الضعفاء (1/ 295)",
        )
        self.assertEqual(result["pattern"], "prose_then_locator_bearing_commentary")
        self.assertEqual(result["certainty"], "confirmed_non_reversal")

    def test_negative_suffix_citation_pair_is_not_reversal(self):
        # Original source_id 25200, narrator 3234, unnumbered-source variant.
        result = classify_tuple(
            "صحيح ابن خزيمة: (1/ 470) (بدون ترقيم)",
            "صحيح ابن خزيمة (1/ 470) (بدون ترقيم)",
        )
        self.assertEqual(result["pattern"], "citation_only_pair")
        self.assertEqual(result["certainty"], "confirmed_non_reversal")


if __name__ == "__main__":
    unittest.main()
