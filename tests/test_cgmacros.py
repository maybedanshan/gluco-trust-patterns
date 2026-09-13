import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file, regular_window, agreement


def series(minutes, values):
    start=datetime(2020,1,1)
    return [{'timestamp':(start+timedelta(minutes=t)).isoformat(),'glucose_mg_dl':v} for t,v in zip(minutes,values)]


class AdapterTests(unittest.TestCase):
    def test_parse_missing_not_zero_and_preserve_interpolation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sample.csv'
            p.write_text('Timestamp,Libre GL,Dexcom GL\n2020-01-01 00:00:00,84,\n2020-01-01 00:01:00,84.13333333333334,100\n',encoding='utf-8')
            data, audit=parse_file(p)
            self.assertEqual(len(data['dexcom']),1)
            self.assertAlmostEqual(data['libre'][1]['glucose_mg_dl'],84.13333333333334)
            self.assertEqual(audit['empty_cells_by_device']['dexcom'],1)
    def test_full_window_boundary_and_gap(self):
        rows=series(range(1441),[100]*1441)
        self.assertEqual(len(regular_window(rows,1)),1441)
        self.assertIsNone(regular_window(rows[:-1],1))
        self.assertIsNone(regular_window(rows[:700]+rows[701:],1))
    def test_common_support_excludes_long_gaps(self):
        data={'dexcom':series([0,1,10,11],[100,200,100,100]),
              'libre':series([0,1,2,3,10,11],[110,110,110,110,110,110])}
        result=agreement(data)
        self.assertEqual(result['common_supported_minutes'],3)
        self.assertAlmostEqual(result['dexcom_minus_libre_mean_mg_dl'],70/3)
        self.assertAlmostEqual(result['between_device_mae_mg_dl'],110/3)
        self.assertAlmostEqual(result['dexcom_minus_libre_tir_pp'],-100/3)
    def test_no_common_support_is_unavailable(self):
        self.assertIsNone(agreement({'dexcom':series([0,1],[100,100]),'libre':series([10,11],[100,100])})['between_device_mae_mg_dl'])


if __name__=='__main__': unittest.main()
