"""Checks the website model contract and the scientific safeguards."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
import index


class ModelTests(unittest.TestCase):
    def test_original_example_scores_and_shap_additivity(self):
        expected = [0.4836573898792267, 0.6149255037307739, 0.7936624884605408]
        for profile, probability in zip(index.CONFIG['examples'], expected):
            result = index.predict(profile)
            self.assertEqual(result['probability'], probability)
            self.assertEqual(len(result['reasons']), 23)
            margin = result['base_value'] + sum(r['contribution'] for r in result['reasons'])
            self.assertAlmostEqual(1 / (1 + math.exp(-margin)), probability, places=6)

    def test_invalid_profiles_are_rejected(self):
        profile = index.CONFIG['examples'][0]
        for invalid in [None, {}, {**profile, 'ExternalRiskEstimate': True},
                        {**profile, 'ExternalRiskEstimate': 2.5},
                        {**profile, 'ExternalRiskEstimate': -1},
                        {**profile, 'ExternalRiskEstimate': 101},
                        {**profile, 'ExternalRiskEstimate': float('nan')},
                        {**profile, 'ExternalRiskEstimate': '72'}]:
            with self.assertRaises(ValueError):
                index.validate(invalid)

    def test_special_codes_are_kept_fixed(self):
        profile = index.CONFIG['examples'][1]
        vary, ranges = index.action_bounds(profile)
        for feature in index.ORDER:
            if profile[feature] < 0 or index.RULES_FILE['rules'][feature] == 'fixed':
                self.assertNotIn(feature, vary)
                self.assertNotIn(feature, ranges)

    def test_every_option_is_valid_and_really_flips_the_decision(self):
        profile = index.CONFIG['examples'][1]
        result = index.options(profile)
        _, ranges = index.action_bounds(profile)
        self.assertEqual(result['status'], 'found')
        self.assertGreater(len(result['options']), 0)
        for option in result['options']:
            self.assertTrue(index.valid_option(profile, option['values'], ranges))
            self.assertLess(index.predict(option['values'])['probability'], 0.5)
            self.assertEqual(option['probability'], index.predict(option['values'])['probability'])

    def test_unsuccessful_search_is_a_result_not_a_server_error(self):
        result = index.options(index.CONFIG['examples'][2])
        self.assertEqual(result['status'], 'not_found')
        self.assertEqual(result['options'], [])

    def test_lower_risk_profile_does_not_need_recourse(self):
        result = index.options(index.CONFIG['examples'][0])
        self.assertEqual(result['status'], 'already_below_threshold')


if __name__ == '__main__':
    unittest.main()
