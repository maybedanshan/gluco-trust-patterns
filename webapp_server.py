"""Local frontend/API prototype. Run python webapp_server.py (loopback only)."""
import argparse
import json
import random
from threading import Lock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from glucotrust import mask, metrics, synthetic, weights

ROOT = Path(__file__).resolve().parent
DEMO_POINTS = 289  # 24 hours at 5-minute intervals, plus the terminal endpoint.
_research_cache = None
_research_lock = Lock()


def simulate(body):
    if not isinstance(body, dict):
        raise ValueError('Expected a JSON object')
    ratio = body.get('ratio', 0.2)
    seed = body.get('seed', 0)
    mode = body.get('mode', 'block')
    if type(ratio) not in (int, float) or not 0 <= ratio <= 0.5:
        raise ValueError('ratio must be between 0 and 0.5')
    if type(seed) is not int or not 0 <= seed <= 1000000:
        raise ValueError('seed must be an integer between 0 and 1000000')
    if mode not in ('random', 'block', 'night'):
        raise ValueError('Unknown mode')
    rows = synthetic()['synthetic-01'][:DEMO_POINTS]
    w = weights(rows)
    removed = mask(rows, ratio, mode, random.Random(seed))
    before, after = metrics(rows, w), metrics(rows, w, removed)
    return {'source': 'synthetic demonstration, not participant evidence',
            'seed': seed,
            'seed_scope': 'Independent demo RNG; not the report participant-keyed seed convention.',
            'reference': before, 'observed': after,
            'mean_bias_mg_dl': after['mean_mg_dl'] - before['mean_mg_dl'],
            'tir_bias_pp': after['tir_pct'] - before['tir_pct'],
            'requested_ratio': ratio, 'time_missing_ratio': sum(w[i] for i in removed) / sum(w),
            'removed_indices': removed, 'readings': rows}


def research():
    global _research_cache
    specs = [('models', 'model-comparison-results.json', 'evaluations'),
             ('history', 'selected-history-results.json', 'summaries'),
             ('labels', 'label-missingness-results.json', 'summaries')]
    with _research_lock:
        paths = [ROOT / 'docs' / file for _, file, _ in specs]
        signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)
        if _research_cache is not None and _research_cache[0] == signature:
            return _research_cache[1]
        payload = {key: [{k: v for k, v in row.items() if k != 'per_person'}
                        for row in json.loads(path.read_text(encoding='utf-8'))[field]]
                   for (key, _, field), path in zip(specs, paths)}
        _research_cache = (signature, payload)
        return payload


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Request bodies and clinical data are never logged.

    def send(self, status, value, content_type='application/json; charset=utf-8'):
        data = json.dumps(value, allow_nan=False).encode() if not isinstance(value, bytes) else value
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            self.send(200, (ROOT / 'frontend/index.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/api/health':
            self.send(200, {'status': 'ok'})
        elif path == '/api/research':
            try:
                self.send(200, research())
            except (OSError, ValueError, KeyError):
                self.send(503, {'error': 'Research artifacts unavailable; reproduce studies first.'})
        else:
            self.send(404, {'error': 'Not found'})

    def do_POST(self):
        if urlsplit(self.path).path != '/api/simulate':
            self.send(404, {'error': 'Not found'})
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.send(415, {'error': 'Use application/json'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError('Request must contain 1–4096 bytes')
            body = json.loads(self.rfile.read(size))
            self.send(200, simulate(body))
        except (ValueError, TypeError, UnicodeError) as exc:
            self.send(400, {'error': str(exc)})
        except Exception:
            self.send(500, {'error': 'internal'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    print(f'Open http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
