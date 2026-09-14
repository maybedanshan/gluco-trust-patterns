import unittest
import json
import os
import tempfile
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer
from http.client import HTTPConnection
from unittest.mock import patch
import webapp_server
from webapp_server import simulate


class WebAppTests(unittest.TestCase):
    def test_zero_control(self):
        result = simulate({'ratio': 0})
        self.assertEqual(result['reference'], result['observed'])
        self.assertEqual(result['removed_indices'], [])

    def test_reproducible_mask(self):
        args = {'ratio': .2, 'seed': 7, 'mode': 'random'}
        self.assertEqual(simulate(args), simulate(args))

    def test_infeasible_night(self):
        with self.assertRaisesRegex(ValueError, 'Night'):
            simulate({'ratio': .3, 'mode': 'night'})

    def test_invalid_request(self):
        for body in [[], {'ratio': float('nan')}, {'seed': True}, {'ratio': -.1}, {'mode': 'unknown'}]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                simulate(body)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), webapp_server.Handler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, method, path, body=None, content_type='application/json'):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            conn.request(method, path, body, {'Content-Type': content_type})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            conn.close()

    def test_health_and_headers(self):
        status, headers, body = self.request('GET', '/api/health?probe=1')
        self.assertEqual((status, body), (200, {'status': 'ok'}))
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn("connect-src 'self'", headers['Content-Security-Policy'])

    def test_post_query_and_zero(self):
        status, _, body = self.request('POST', '/api/simulate?x=1', '{"ratio":0}')
        self.assertEqual(status, 200)
        self.assertEqual(body['tir_bias_pp'], 0)

    def test_http_errors(self):
        for path, body, kind, expected in [
            ('/api/simulate', '{}', 'text/plain', 415),
            ('/api/simulate', '{', 'application/json', 400),
            ('/api/simulate', ' ' * 4097, 'application/json', 400),
            ('/api/simulate', '{"mode":"night","ratio":0.3}', 'application/json', 400),
            ('/unknown', '{}', 'application/json', 404),
        ]:
            with self.subTest(path=path, expected=expected):
                self.assertEqual(self.request('POST', path, body, kind)[0], expected)
        self.assertEqual(self.request('GET', '/data/local/private.csv')[0], 404)

    def test_internal_error_is_generic(self):
        with patch('webapp_server.simulate', side_effect=IndexError('private diagnostic')):
            status, _, body = self.request('POST', '/api/simulate', '{}')
        self.assertEqual((status, body), (500, {'error': 'internal'}))


class ResearchCacheTests(unittest.TestCase):
    def test_cache_invalidation_and_missing_source(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(webapp_server, 'ROOT', Path(tmp)), patch.object(webapp_server, '_research_cache', None):
            docs = Path(tmp) / 'docs'
            docs.mkdir()
            for name, key in [('model-comparison-results.json', 'evaluations'), ('selected-history-results.json', 'summaries'), ('label-missingness-results.json', 'summaries')]:
                (docs / name).write_text(json.dumps({key: [{'value': 1, 'per_person': ['private']}]}))
            initial = webapp_server.research()
            self.assertIs(initial, webapp_server.research())
            self.assertNotIn('per_person', initial['models'][0])
            file = docs / 'model-comparison-results.json'
            old = file.stat().st_mtime_ns
            file.write_text(json.dumps({'evaluations': [{'value': 2}]}))
            os.utime(file, ns=(old + 1000000, old + 1000000))
            self.assertEqual(webapp_server.research()['models'][0]['value'], 2)
            file.unlink()
            with self.assertRaises(FileNotFoundError):
                webapp_server.research()
