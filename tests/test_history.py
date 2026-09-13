import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from history_missingness import degrade_meal


class DegradationTests(unittest.TestCase):
    def setUp(self):
        self.t = datetime(2025, 1, 1, 12)
        self.glucose = {self.t + timedelta(minutes=m): 100 + m for m in range(-30, 0)}
        self.meal = {'timestamp': self.t.isoformat(), 'target': 41, 'features': [1, 2, 3, 4, 5, 84.5, 1, 0, -1]}

    def test_no_mask_identity_and_input_immutability(self):
        original = copy.deepcopy(self.meal)
        degraded, removed = degrade_meal(self.meal, self.glucose, set())
        self.assertEqual(degraded, self.meal)
        self.assertEqual(removed, 0)
        self.assertEqual(self.meal, original)

    def test_retained_support_slope_and_frozen_label(self):
        deleted = set(sorted(self.glucose)[:15])
        degraded, removed = degrade_meal(self.meal, self.glucose, deleted)
        self.assertEqual(removed, 15)
        self.assertEqual(degraded['features'][5], 92)
        self.assertEqual(degraded['features'][6], 1)
        self.assertEqual(degraded['target'], 41)
        self.assertEqual(degraded['features'][:5], self.meal['features'][:5])
        deleted.add(sorted(self.glucose)[15])
        self.assertIsNone(degrade_meal(self.meal, self.glucose, deleted)[0])

    def test_non_input_missingness_does_not_change_features(self):
        degraded, removed = degrade_meal(self.meal, self.glucose, {self.t - timedelta(hours=6)})
        self.assertEqual(degraded, self.meal)
        self.assertEqual(removed, 0)


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'outputs/history_missingness/runs.json'

@unittest.skipUnless(RUNS.exists(), 'Optional joint experiment outputs')
class JointOutputTests(unittest.TestCase):
    def test_fixed_tests_zero_mask_and_accounting(self):
        runs = json.loads(RUNS.read_text())
        split = json.loads((ROOT / 'outputs/glucopatterns/splits.json').read_text())
        counts = {f['participant']: len(f['history']['test']) for f in split if f['history']}
        self.assertEqual(len(runs), len(counts) * 4 * 3 * 10)
        for r in runs:
            self.assertEqual(r['test_meals'], counts[r['participant']])
            if r['status'] != 'ok': continue
            self.assertAlmostEqual(r['cost'], r['personalized_mae'] - r['clean_mae'])
            self.assertAlmostEqual(r['benefit'], r['pooled_mae'] - r['personalized_mae'])
            self.assertTrue(0 <= r['usable_history'] <= 10)
            if r['ratio'] == 0:
                self.assertAlmostEqual(r['personalized_mae'], r['clean_mae'])
                self.assertEqual(r['usable_history'], 10)
                self.assertEqual(r['premeal_missing_fraction'], 0)


if __name__ == '__main__': unittest.main()
