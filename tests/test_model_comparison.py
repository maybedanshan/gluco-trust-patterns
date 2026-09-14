import copy
import importlib.util
import json
import statistics
import unittest
from pathlib import Path
from model_comparison import inner_folds, fit_outer, fit_ridge
from glucopatterns import fit_model


class FoldTests(unittest.TestCase):
    def test_inner_participants_are_partitioned_once(self):
        ids = [f'p{i}' for i in range(11)]
        folds = inner_folds(ids)
        self.assertEqual(sorted(p for f in folds for p in f), sorted(ids))
        self.assertEqual(folds, inner_folds(ids[::-1]))


@unittest.skipUnless(importlib.util.find_spec('numpy'), 'Optional numpy')
class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{'participant': f'p{i}', 'features': [float(i), float(j)], 'target': float(i+j)} for i in range(7) for j in range(3)]

    def test_outer_subject_changes_cannot_change_selection_or_fit(self):
        model, _, selection = fit_outer(self.rows, 'p0')
        changed = copy.deepcopy(self.rows)
        for r in changed:
            if r['participant'] == 'p0':
                r['target'] = 1e9
                r['features'] = [-1e9, 1e9]
        other, _, other_selection = fit_outer(changed, 'p0')
        self.assertEqual(selection, other_selection)
        self.assertEqual(model['mean'].tolist(), other['mean'].tolist())
        self.assertEqual(model['beta'].tolist(), other['beta'].tolist())
        self.assertNotIn('p0', [p for f in selection['validation_participant_folds'] for p in f])

    def test_fixed_penalty_matches_original_and_training_only_scale(self):
        model = fit_ridge(self.rows, 10)
        original = fit_model(self.rows)
        self.assertEqual(model['beta'].tolist(), original['beta'].tolist())
        subset = [r for r in self.rows if r['participant'] != 'p6']
        self.assertAlmostEqual(fit_ridge(subset, .1)['mean'][0], 2.5)
        for penalty in [0, -1, float('nan')]:
            with self.assertRaises(ValueError): fit_ridge(self.rows, penalty)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/model_comparison'

@unittest.skipUnless((OUT / 'selection.json').exists(), 'Optional local nested comparison')
class ComparisonOutputTests(unittest.TestCase):
    def test_all_inner_folds_exclude_outer_test_and_cover_training(self):
        for fold in json.loads((OUT / 'selection.json').read_text()):
            flattened = [p for f in fold['validation_participant_folds'] for p in f]
            self.assertEqual(sorted(flattened), fold['training_participants'])
            self.assertNotIn(fold['held_out'], flattened)
            scores = {float(k):v for k,v in fold['candidate_macro_mae'].items()}
            self.assertEqual(fold['selected_penalty'], min(scores, key=lambda p:(scores[p], -p)))

    def test_fixed_reference_and_test_meals_are_preserved(self):
        original = json.loads((ROOT / 'outputs/glucopatterns/predictions.json').read_text())
        key = lambda r:(r['participant'], r['meal_id'], r['setting'], r['history_budget'])
        lookup = {key(r):r for r in original}
        updated = json.loads((OUT / 'predictions.json').read_text())
        self.assertEqual(set(lookup), {key(r) for r in updated})
        for r in updated:
            before = lookup[key(r)]
            self.assertEqual(r['target'], before['target'])
            self.assertAlmostEqual(r['fixed_pooled'], before['pooled'])
            if r['setting']=='unseen': self.assertIsNone(r['history_mean'])

    def test_history_mean_uses_only_selected_early_labels(self):
        rows = {r['meal_id']:r for r in json.loads((ROOT/'outputs/glucopatterns/eligible-meals.json').read_text())}
        splits = {s['participant']:s for s in json.loads((ROOT/'outputs/glucopatterns/splits.json').read_text())}
        for r in json.loads((OUT/'predictions.json').read_text()):
            if r['setting']!='history': continue
            ids = splits[r['participant']]['history']['adaptation_by_budget'][str(r['history_budget'])]
            self.assertAlmostEqual(r['history_mean'], statistics.mean(rows[mid]['target'] for mid in ids))


if __name__ == '__main__': unittest.main()
