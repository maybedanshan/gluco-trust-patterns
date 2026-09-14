import importlib.util
import json
import unittest
from datetime import datetime,timedelta
from pathlib import Path
from selected_history import decompose

@unittest.skipUnless(importlib.util.find_spec('numpy'),'Optional NumPy')
class DecompositionTests(unittest.TestCase):
    def test_full_loss_falls_back_to_pooled_and_costs_add(self):
        import numpy as np
        t=datetime(2025,1,1,12)
        meal={'timestamp':t.isoformat(),'target':20.,'features':[0.]*9}
        model={'mean':np.zeros(9),'scale':np.ones(9),'beta':np.zeros(10)}
        glucose={t+timedelta(minutes=m):0. for m in range(-30,0)}
        stats=decompose(model,[meal],[meal],glucose,set(glucose))
        self.assertEqual(stats['usable_history'],0)
        self.assertEqual(stats['degraded_mae'],stats['pooled_mae'])
        self.assertEqual(stats['feature_cost'],0)
        self.assertAlmostEqual(stats['total_cost'],stats['availability_cost']+stats['feature_cost'])
        clean=decompose(model,[meal],[meal],glucose,set())
        self.assertEqual(clean['total_cost'],0)

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'outputs/selected_history/runs.json'

@unittest.skipUnless(LOCAL.exists(),'Optional selected-history outputs')
class SelectedOutputTests(unittest.TestCase):
    def test_masks_and_exact_decomposition_match(self):
        old=json.loads((ROOT/'outputs/history_missingness/runs.json').read_text())
        key=lambda r:(r['participant'],r['ratio'],r['mode'],r['seed'])
        lookup={key(r):r for r in old}
        new=json.loads(LOCAL.read_text())
        self.assertEqual(set(lookup),{key(r) for r in new})
        for r in new:
            v1=lookup[key(r)]
            self.assertEqual(r['test_meals'],v1['test_meals'])
            self.assertEqual(r['status'],v1['status'])
            if r['status']!='ok':continue
            self.assertEqual(r['mask_indices_sha256'],v1['mask_indices_sha256'])
            self.assertAlmostEqual(r['total_cost'],r['availability_cost']+r['feature_cost'])
            self.assertAlmostEqual(r['selected_advantage'],v1['personalized_mae']-r['degraded_mae'])
            if r['ratio']==0:self.assertAlmostEqual(r['total_cost'],0)

    def test_clean_reference_matches_selected_benchmark(self):
        benchmark=json.loads((ROOT/'docs/model-comparison-results.json').read_text())
        people={p['participant']:p for s in benchmark['evaluations'] if s['history_budget']==10 for p in s['per_person']}
        for r in json.loads(LOCAL.read_text()):
            if r['status']!='ok':continue
            self.assertAlmostEqual(r['clean_mae'],people[r['participant']]['personalized'])
            self.assertAlmostEqual(r['pooled_mae'],people[r['participant']]['selected_pooled'])

if __name__=='__main__':unittest.main()
