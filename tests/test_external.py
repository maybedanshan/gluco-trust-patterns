import unittest
import json
from pathlib import Path
from datetime import datetime, timedelta
from audit_physio import gap_events, parse_time
from cgmacros import regular_window
from shanghai import parse_rows


class ExternalTests(unittest.TestCase):
    def test_last_window_stays_after_gap(self):
        start=datetime(2020,1,1)
        rows=[{'timestamp':(start+timedelta(minutes=i)).isoformat(),'glucose_mg_dl':100}
              for i in list(range(1441))+list(range(2000,3501))]
        result=regular_window(rows,1,24,'last')
        self.assertEqual(result[0]['timestamp'],(start+timedelta(minutes=2060)).isoformat())
        self.assertEqual(len(result),1441)
        self.assertIsNone(regular_window(rows,1,48,'first'))
    def test_empty_and_conflicting_workbook(self):
        with self.assertRaises(ValueError): parse_rows([])
        with self.assertRaises(ValueError):
            parse_rows([['Date','CGM (mg / dl)'],[datetime(2020,1,1),100],[datetime(2020,1,1),101]])
    def test_missing_and_identical_duplicate(self):
        rows,audit=parse_rows([['Date','CGM (mg / dl)'],[datetime(2020,1,1),100],
                              [datetime(2020,1,1),100],[datetime(2020,1,2),None]])
        self.assertEqual(len(rows),1)
        self.assertEqual(audit,{'rows_without_cgm':1,'identical_duplicates_collapsed':1})
    def test_gap_jitter_duplicates_and_boundary(self):
        start=datetime(2020,1,1)
        times=[start+timedelta(seconds=s) for s in [0,299,299,600,1800]]
        gaps=gap_events(times)
        self.assertEqual(len(gaps),1)
        self.assertEqual(gaps[0]['excess_over_expected_minutes'],15)
        self.assertEqual(gaps[0]['start'],(start+timedelta(minutes=15)).isoformat())
    def test_export_timestamp_variants(self):
        self.assertEqual(parse_time('2022-04-02 0:03:05'),parse_time('2022-04-02T00:03:05'))

    @unittest.skipUnless((Path(__file__).resolve().parents[1]/'outputs/shanghai_v5/experiment/results.json').exists(), 'Run Shanghai pipeline first')
    def test_shanghai_actual_time_budget_and_metrics(self):
        out=Path(__file__).resolve().parents[1]/'outputs/shanghai_v5'
        cohort=json.loads((out/'cohort.json').read_text(encoding='utf-8'))
        results=json.loads((out/'experiment/results.json').read_text(encoding='utf-8'))['results']
        self.assertEqual(len(cohort),100)
        self.assertEqual(len(results),9000)
        for pid,rows in cohort.items():
            self.assertEqual(len(rows),97)
            times=[datetime.fromisoformat(r['timestamp']) for r in rows]
            self.assertTrue(all((b-a).total_seconds()==900 for a,b in zip(times,times[1:])))
        for r in results:
            deleted=set(r['removed_indices'])
            self.assertEqual(len(deleted),round(96*r['requested_ratio']))
            self.assertAlmostEqual(r['time_missing_ratio'],len(deleted)/96)
            before=[v['glucose_mg_dl'] for v in cohort[r['participant']][:-1]]
            after=[v for i,v in enumerate(before) if i not in deleted]
            self.assertAlmostEqual(r['mean_bias_mg_dl'],sum(after)/len(after)-sum(before)/96)
            self.assertAlmostEqual(r['tir_bias_pp'],100*(sum(70<=v<=180 for v in after)/len(after)-sum(70<=v<=180 for v in before)/96))


if __name__=='__main__': unittest.main()
