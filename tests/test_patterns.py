import importlib.util
import json
import statistics
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from glucopatterns import meal_vectors, history_split, fit_model, predict, adaptation_offset


class MealProtocolTests(unittest.TestCase):
    def test_target_support_and_no_postmeal_features(self):
        values = {m: 100. for m in range(-30, 121)}
        a, y = meal_vectors(values, [10.] * 5, datetime(2025, 1, 1, 12))
        self.assertEqual(y, 0)
        for m in range(120): values[m] = 150
        values[120] = 999
        b, z = meal_vectors(values, [10.] * 5, datetime(2025, 1, 1, 12))
        self.assertEqual(a, b)
        self.assertEqual(z, 50)

    def test_history_boundary_and_eligibility(self):
        t = datetime(2025, 1, 1)
        rows = [{'timestamp': (t + timedelta(minutes=150 * i)).isoformat()} for i in range(13)]
        history, test = history_split(rows[::-1])
        self.assertEqual(len(history), 10)
        self.assertEqual(len(test), 3)
        self.assertIsNone(history_split(rows[:12]))
        rows[10]['timestamp'] = (t + timedelta(minutes=150 * 10 - 1)).isoformat()
        with self.assertRaises(ValueError): history_split(rows)


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'Optional patterns dependency numpy')
class ModelTests(unittest.TestCase):
    def test_participant_balancing_and_constant_features(self):
        rows = [{'participant': 'a', 'features': [1., 2.], 'target': 0.}] * 10
        rows += [{'participant': 'b', 'features': [1., 2.], 'target': 10.}]
        model = fit_model(rows)
        self.assertAlmostEqual(model['baseline'], 5)
        self.assertAlmostEqual(predict(model, rows[0]), 5)

    def test_fixed_early_residual_shrinkage(self):
        rows = [{'participant': 'a', 'features': [1.], 'target': 10.},
                {'participant': 'b', 'features': [1.], 'target': 10.}]
        model = fit_model(rows)
        history = [{'features': [1.], 'target': 18.}] * 3
        self.assertAlmostEqual(adaptation_offset(model, history), 3)
        self.assertEqual(adaptation_offset(model, []), 0)
        held = {'features': [1.], 'target': 9999}
        self.assertAlmostEqual(predict(model, held), 10)


ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'outputs/glucopatterns'

@unittest.skipUnless((LOCAL / 'splits.json').exists(), 'Optional local prediction outputs')
class LocalSplitTests(unittest.TestCase):
    def test_subject_isolation_fixed_tests_and_temporal_purge(self):
        splits = json.loads((LOCAL / 'splits.json').read_text())
        meals = {r['meal_id']: r for r in json.loads((LOCAL / 'eligible-meals.json').read_text())}
        predictions = json.loads((LOCAL / 'predictions.json').read_text())
        for fold in splits:
            pid = fold['participant']
            self.assertNotIn(pid, fold['training_participants'])
            self.assertTrue(all(meals[mid]['participant'] == pid for mid in fold['unseen_test']))
            if not fold['history']: continue
            test_ids = set(fold['history']['test'])
            for k in [3, 5, 10]:
                adaptation = fold['history']['adaptation_by_budget'][str(k)]
                self.assertEqual(len(adaptation), k)
                self.assertFalse(set(adaptation) & test_ids)
                observed = {r['meal_id'] for r in predictions if r['participant'] == pid and r['setting'] == 'history' and r['history_budget'] == k}
                self.assertEqual(observed, test_ids)
                last_label_end = max(datetime.fromisoformat(meals[mid]['timestamp']) for mid in adaptation) + timedelta(minutes=120)
                first_input_start = min(datetime.fromisoformat(meals[mid]['timestamp']) for mid in test_ids) - timedelta(minutes=30)
                self.assertLessEqual(last_label_end, first_input_start)

    def test_macro_metrics_match_per_meal_predictions(self):
        predictions = json.loads((LOCAL / 'predictions.json').read_text())
        report = json.loads((ROOT / 'docs/glucopatterns-results.json').read_text())
        for summary in report['evaluations']:
            rows = [r for r in predictions if r['setting'] == summary['setting'] and r['history_budget'] == summary['history_budget']]
            ids = {r['participant'] for r in rows}
            for model in ['baseline', 'pooled', 'personalized']:
                expected = statistics.mean(statistics.mean(abs(r[model] - r['target']) for r in rows if r['participant'] == pid) for pid in ids)
                self.assertAlmostEqual(expected, summary['macro_mae'][model])

if __name__ == '__main__': unittest.main()
