import ast
import unittest
from pathlib import Path

from build_dashboard import summarize
from build_release import release_files
from glucotrust import weights, experiment

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    def test_absolute_errors_do_not_cancel_across_seeds(self):
        rows = [dict(participant='p', mode='random', requested_ratio=.1,
                     time_missing_ratio=.1, seed=s, mean_bias_mg_dl=b,
                     tir_bias_pp=b) for s, b in [(1, 2), (2, -2)]]
        result = summarize(rows, 'demo', 'Demo', '24 h', '')
        self.assertEqual(result['participants'][0]['tir_bias'], 0)
        self.assertEqual(result['participants'][0]['tir_mae'], 2)
        self.assertEqual(result['people'], 1)

    def test_invalid_support_caps_and_duplicate_runs(self):
        rows = [{'timestamp': '2025-01-01T00:00:00', 'glucose_mg_dl': 100},
                {'timestamp': '2025-01-01T00:05:00', 'glucose_mg_dl': 100}]
        for cap in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                weights(rows, cap)
        for ratios, seeds in [([.1, .1], [1]), ([.1], [1, 1])]:
            with self.assertRaises(ValueError):
                experiment({'p': rows}, ratios, seeds, 5)

    def test_source_syntax_supports_python310(self):
        for path in ROOT.glob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 10))

    def test_release_excludes_local_data_and_environments(self):
        names = [p.relative_to(ROOT).as_posix() for p in release_files(ROOT)]
        self.assertIn('docs/demo/index.html', names)
        for name in names:
            self.assertFalse(name.startswith(('data/', 'outputs/', '.venv/', 'dist/')))


if __name__ == '__main__':
    unittest.main()
