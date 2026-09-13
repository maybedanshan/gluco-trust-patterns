"""Optional independent checks on locally generated real-data outputs (no downloads)."""
import json
import unittest
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'outputs/cgmacros'


@unittest.skipUnless((OUTPUT/'provenance.json').exists(),'Run run_cgmacros.py first; real data are not required in CI')
class RealOutputTests(unittest.TestCase):
    def test_paired_masks_time_budget_and_independent_metrics(self):
        device_results={d:json.loads((OUTPUT/d/'results.json').read_text(encoding='utf-8'))['results'] for d in ['dexcom','libre']}
        self.assertEqual(len(device_results['dexcom']),len(device_results['libre']))
        for a,b in zip(device_results['dexcom'],device_results['libre']):
            for key in ['participant','mode','requested_ratio','seed','removed_timestamps']:
                self.assertEqual(a[key],b[key])
        for device,results in device_results.items():
            cohort=json.loads((ROOT/f'data/local/cgmacros/prepared/{device}.json').read_text(encoding='utf-8'))
            for r in results:
                rows=cohort[r['participant']]
                self.assertEqual(len(rows),1441)
                self.assertEqual(r['reference_supported_minutes'],1440)
                self.assertAlmostEqual(r['time_missing_ratio'],r['requested_ratio'])
                self.assertEqual(len(set(r['removed_indices'])),round(1440*r['requested_ratio']))
                if r['mode']=='night':
                    self.assertTrue(all(datetime.fromisoformat(t).hour<6 for t in r['removed_timestamps']))
                removed=set(r['removed_indices'])
                before=[p['glucose_mg_dl'] for p in rows[:-1]]
                after=[v for i,v in enumerate(before) if i not in removed]
                mean_error=sum(after)/len(after)-sum(before)/len(before)
                tir_error=100*(sum(70<=v<=180 for v in after)/len(after)-sum(70<=v<=180 for v in before)/len(before))
                self.assertAlmostEqual(r['mean_bias_mg_dl'],mean_error)
                self.assertAlmostEqual(r['tir_bias_pp'],tir_error)


if __name__=='__main__': unittest.main()
