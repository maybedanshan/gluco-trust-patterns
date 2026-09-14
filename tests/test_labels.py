import copy
import json
import unittest
from datetime import datetime,timedelta
from pathlib import Path
from label_missingness import damaged_label,histories


class LabelPolicyTests(unittest.TestCase):
    def setUp(self):
        self.t=datetime(2025,1,1,12)
        self.glucose={self.t+timedelta(minutes=m):(100. if m<0 else 150.) for m in range(-30,120)}
        self.meal={'meal_id':'m','timestamp':self.t.isoformat(),'features':[1,2,3,4,5,100.,0.,0.,-1.],'target':50.}

    def test_complete_and_boundary_support(self):
        self.assertEqual(damaged_label(self.meal,self.glucose,set(),.7),(50.,30,120))
        deleted={self.t+timedelta(minutes=m) for m in range(36)}
        self.assertEqual(damaged_label(self.meal,self.glucose,deleted,.7),(50.,30,84))
        deleted.add(self.t+timedelta(minutes=36))
        self.assertIsNone(damaged_label(self.meal,self.glucose,deleted,.7)[0])
        self.assertEqual(damaged_label(self.meal,self.glucose,deleted,.5)[0],50.)

    def test_actual_label_bias_and_arm_isolation(self):
        for m in range(60):self.glucose[self.t+timedelta(minutes=m)]=200.
        meal=copy.deepcopy(self.meal);meal['target']=75.
        deleted={self.t+timedelta(minutes=m) for m in range(30)}
        arms,diags=histories([meal],self.glucose,deleted,.7)
        expected=(30*200+60*150)/90-100
        self.assertAlmostEqual(arms['label_only'][0]['target'],expected)
        self.assertEqual(arms['input_only'][0]['target'],75.)
        self.assertEqual(arms['label_only'][0]['features'],meal['features'])
        self.assertAlmostEqual(diags[0]['label_error'],expected-75.)
        self.assertEqual(meal['target'],75.)

    def test_unusable_label_is_null_not_zero(self):
        deleted={self.t+timedelta(minutes=m) for m in range(120)}
        arms,diags=histories([self.meal],self.glucose,deleted,.7)
        self.assertEqual(len(arms['input_only']),1)
        self.assertEqual(arms['label_only'],[])
        self.assertEqual(arms['joint'],[])
        self.assertIsNone(diags[0]['label_error'])

    def test_precoverage_also_gates_label_and_joint(self):
        deleted={self.t+timedelta(minutes=m) for m in range(-30,-14)}
        label,pre,post=damaged_label(self.meal,self.glucose,deleted,.7)
        self.assertIsNone(label);self.assertEqual((pre,post),(14,120))
        arms,_=histories([self.meal],self.glucose,deleted,.7)
        self.assertTrue(all(not v for v in arms.values()))


ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'outputs/label_missingness/runs.json'

@unittest.skipUnless(LOCAL.exists(),'Optional label-study outputs')
class LabelOutputTests(unittest.TestCase):
    def test_shared_masks_fixed_tests_and_zero_identity(self):
        runs=json.loads(LOCAL.read_text())
        splits=json.loads((ROOT/'outputs/glucopatterns/splits.json').read_text())
        counts={f['participant']:len(f['history']['test']) for f in splits if f['history']}
        groups={}
        self.assertEqual(len(runs),len(counts)*4*3*10*3*3)
        for r in runs:
            self.assertEqual(r['test_meals'],counts[r['participant']])
            if r['status']!='ok':continue
            groups.setdefault((r['participant'],r['ratio'],r['mode'],r['seed']),[]).append(r)
            self.assertAlmostEqual(r['cost'],r['personalized_mae']-r['clean_mae'])
            if r['ratio']==0:
                self.assertAlmostEqual(r['cost'],0)
                self.assertEqual(r['usable_history'],10)
        for rs in groups.values():
            self.assertEqual(len({r['mask_indices_sha256'] for r in rs}),1)
            self.assertEqual(len({r['personalized_mae'] for r in rs if r['arm']=='input_only'}),1)
            for threshold in [.5,.7,.9]:
                arms={r['arm']:r for r in rs if r['post_threshold']==threshold}
                self.assertAlmostEqual(arms['joint']['joint_minus_input'],arms['joint']['personalized_mae']-arms['input_only']['personalized_mae'])
                self.assertAlmostEqual(arms['joint']['joint_minus_label'],arms['joint']['personalized_mae']-arms['label_only']['personalized_mae'])

    def test_report_metrics_and_no_missing_label_imputation(self):
        runs=json.loads(LOCAL.read_text())
        summary=json.loads((ROOT/'docs/label-missingness-results.json').read_text())
        for r in runs:
            if r['status']=='ok' and r['valid_label_count']==0:self.assertIsNone(r['label_max_abs_error'])
        for s in summary['summaries']:
            if s['status']!='complete':continue
            if not s['label_evaluable_people']:
                self.assertIsNone(s['label_bias']);self.assertIsNone(s['label_mae'])
            self.assertEqual(s['n'],len(s['per_person']))


if __name__=='__main__':unittest.main()
