import random
import unittest
from glucotrust import weights, metrics, mask, experiment, synthetic

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'timestamp':f'2025-01-01T00:{m:02}:00','glucose_mg_dl':v} for m,v in [(0,100),(2,200),(12,100)]]
    def test_irregular_support_and_no_gap_bridging(self):
        w=weights(self.rows,5)
        self.assertEqual(w,[2,5,0])
        self.assertAlmostEqual(metrics(self.rows,w)['tir_pct'],200/7)
        self.assertEqual(metrics(self.rows,w,[1])['tir_pct'],100)
    def test_threshold_inclusive(self):
        rows=[{'glucose_mg_dl':v} for v in [70,180,181,69]]
        self.assertEqual(metrics(rows,[1]*4)['tir_pct'],50)
    def test_masks_equal_counts_reproducible(self):
        rows=synthetic()['synthetic-01']
        for mode in ['random','block','night']:
            a=mask(rows,.1,mode,random.Random(7))
            self.assertEqual(a,mask(rows,.1,mode,random.Random(7)))
            self.assertEqual(len(a),round((len(rows)-1)*.1))
            self.assertEqual(len(a),len(set(a)))
            if mode=='block': self.assertEqual(a,list(range(a[0],a[-1]+1)))
    def test_zero_missing_zero_bias(self):
        for r in experiment({'p':self.rows},[0],[1],5):
            self.assertEqual(r['tir_bias_pp'],0)
            self.assertEqual(r['mean_bias_mg_dl'],0)
    def test_invalid_timestamps(self):
        with self.assertRaises(ValueError): weights(self.rows[::-1])

if __name__=='__main__': unittest.main()
