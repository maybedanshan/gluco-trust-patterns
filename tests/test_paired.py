import copy
import random
import unittest
from paired_analysis import bootstrap_columns, paired_values, quantile

class PairedTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(participant=p, mode=m, requested_ratio=.2, seed=s,
                          tir_bias_pp=v, time_missing_ratio=.2)
                     for p in ['a', 'b'] for m in ['random', 'block']
                     for s, v in enumerate([1, -1] if m == 'random' else [3, -3])]

    def test_absolute_before_seed_average_and_pairing(self):
        values = paired_values(self.rows[::-1], .2, 'block', 'tir_bias_pp', [0, 1])
        self.assertEqual([v['participant'] for v in values], ['a', 'b'])
        self.assertEqual([v['difference'] for v in values], [2, 2])

    def test_bad_pairs_fail_without_silent_exclusion(self):
        cases = [self.rows[:-1], self.rows + [self.rows[0]]]
        for field, value in [('time_missing_ratio', .1), ('tir_bias_pp', float('nan'))]:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            cases.append(rows)
        for rows in cases:
            with self.assertRaises(ValueError):
                paired_values(rows, .2, 'block', 'tir_bias_pp', [0, 1])

    def test_constant_effect_degenerate_interval(self):
        self.assertEqual(bootstrap_columns([[2] * 5], 100, 1), [(2, 2)])

    def test_shared_draws_preserve_cross_column_relation(self):
        a, b = bootstrap_columns([[1, 2, 8], [-1, -2, -8]], 1000, 7)
        self.assertAlmostEqual(a[0], -b[1])
        self.assertAlmostEqual(a[1], -b[0])

    def test_bootstrap_matches_direct_participant_sampling(self):
        rng = random.Random(19)
        population = [0, 2, 7]
        samples = sorted(sum(population[rng.randrange(3)] for _ in range(3)) / 3 for _ in range(100))
        expected = (samples[2] * .525 + samples[3] * .475,
                    samples[96] * .475 + samples[97] * .525)
        actual = bootstrap_columns([population], 100, 19)[0]
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b)
        self.assertEqual(actual, bootstrap_columns([population], 100, 19)[0])

    def test_quantile_and_invalid_bootstrap(self):
        self.assertEqual(quantile([0, 10], .25), 2.5)
        for columns in [[], [[1]], [[1, 2], [1]], [[1, float('inf')]]]:
            with self.assertRaises(ValueError):
                bootstrap_columns(columns, 100, 1)

if __name__ == '__main__':
    unittest.main()
