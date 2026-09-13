"""Joint GlucoTrust/GlucoPatterns experiment: degrade historical premeal inputs."""
import hashlib
import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file
from glucopatterns import fit_model, predict, adaptation_offset
from glucotrust import mask
from paired_analysis import bootstrap_columns

ROOT = Path(__file__).resolve().parent
RATIOS = [0., .05, .1, .2]
MODES = ['random', 'block', 'night']
SEEDS = list(range(10))


def degrade_meal(meal, glucose, deleted):
    t = datetime.fromisoformat(meal['timestamp'])
    window = [t + timedelta(minutes=m) for m in range(-30, 0)]
    if any(q not in glucose for q in window): raise ValueError('Original premeal window incomplete')
    retained = [q for q in window if q not in deleted]
    if len(retained) < 15: return None, 30 - len(retained)
    features = list(meal['features'])
    features[5] = statistics.mean(glucose[q] for q in retained)
    features[6] = (glucose[retained[-1]] - glucose[retained[0]]) / ((retained[-1] - retained[0]).total_seconds() / 60)
    return {**meal, 'features': features}, 30 - len(retained)


def main():
    import numpy as np
    base = ROOT / 'outputs/glucopatterns'
    meals = json.loads((base / 'eligible-meals.json').read_text())
    indexed = {r['meal_id']: r for r in meals}
    splits = json.loads((base / 'splits.json').read_text())
    manifest = json.loads((ROOT / 'data/local/cgmacros/raw/manifest.json').read_text())
    raw = ROOT / 'data/local/cgmacros/raw'
    sources = {Path(e['file']).stem: e for e in manifest['files']}
    runs = []
    for fold in splits:
        if not fold['history']: continue
        pid = fold['participant']
        history = [indexed[mid] for mid in fold['history']['adaptation_by_budget']['10']]
        test = [indexed[mid] for mid in fold['history']['test']]
        model = fit_model([r for r in meals if r['participant'] != pid])
        clean_offset = adaptation_offset(model, history)
        residuals = [predict(model, r) - r['target'] for r in test]
        pooled = statistics.mean(abs(v) for v in residuals)
        clean = statistics.mean(abs(v + clean_offset) for v in residuals)
        entry = sources[pid]
        path = raw / entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']: raise ValueError('Source checksum mismatch')
        series, _ = parse_file(path)
        glucose = {datetime.fromisoformat(r['timestamp']): r['glucose_mg_dl'] for r in series['dexcom']}
        start = datetime.fromisoformat(history[0]['timestamp']) - timedelta(minutes=30)
        stop = datetime.fromisoformat(history[-1]['timestamp'])
        timeline = sorted(q for q in glucose if start <= q < stop)
        rows = [{'timestamp': q.isoformat()} for q in timeline] + [{'timestamp': stop.isoformat()}]
        for ratio in RATIOS:
            for mode in MODES:
                for seed in SEEDS:
                    key = f'{pid}|history-input-v1|{ratio}|{mode}|{seed}'
                    rng = random.Random(int(hashlib.sha256(key.encode()).hexdigest(), 16))
                    run = {'participant': pid, 'ratio': ratio, 'mode': mode, 'seed': seed, 'test_meals': len(test),
                           'pooled_mae': pooled, 'clean_mae': clean, 'timeline_minutes': len(timeline)}
                    if mode == 'night' and round(len(timeline) * ratio) > sum(q.hour < 6 for q in timeline):
                        runs.append({**run, 'status': 'infeasible_night_budget'})
                        continue
                    indices = mask(rows, ratio, mode, rng)
                    deleted = {timeline[i] for i in indices}
                    adapted, removed = [], 0
                    for meal in history:
                        degraded, count = degrade_meal(meal, glucose, deleted)
                        removed += count
                        if degraded is not None: adapted.append(degraded)
                    offset = adaptation_offset(model, adapted)
                    mae = statistics.mean(abs(v + offset) for v in residuals)
                    runs.append({**run, 'status': 'ok', 'personalized_mae': mae, 'benefit': pooled - mae,
                        'cost': mae - clean, 'usable_history': len(adapted), 'premeal_missing_fraction': removed / 300,
                        'actual_timeline_fraction': len(indices) / len(timeline),
                        'mask_indices_sha256': hashlib.sha256(json.dumps(indices).encode()).hexdigest()})
    out = ROOT / 'outputs/history_missingness'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'runs.json').write_text(json.dumps(runs), encoding='utf-8')
    participants = sorted({r['participant'] for r in runs})
    summaries = []
    for ratio in RATIOS:
        for mode in MODES:
            selected = [r for r in runs if r['ratio'] == ratio and r['mode'] == mode]
            failed = [r for r in selected if r['status'] != 'ok']
            if failed:
                summaries.append({'ratio': ratio, 'mode': mode, 'status': 'incomplete', 'infeasible_runs': len(failed)})
                continue
            per_person = []
            for pid in participants:
                rs = [r for r in selected if r['participant'] == pid]
                if len(rs) != 10: raise ValueError('Incomplete seed set')
                per_person.append({'participant': pid, **{key: statistics.mean(r[key] for r in rs) for key in
                    ['pooled_mae', 'clean_mae', 'personalized_mae', 'benefit', 'cost', 'usable_history', 'premeal_missing_fraction', 'actual_timeline_fraction']}})
            summaries.append({'ratio': ratio, 'mode': mode, 'status': 'complete', 'n': len(participants), 'per_person': per_person,
                              **{key: statistics.mean(p[key] for p in per_person) for key in per_person[0] if key != 'participant'}})
    complete = [s for s in summaries if s['status'] == 'complete']
    columns = [[p[key] for p in s['per_person']] for s in complete for key in ['benefit', 'cost']]
    intervals = iter(bootstrap_columns(columns, 10000, 20260915))
    for s in complete:
        s['benefit_ci95'] = next(intervals)
        s['cost_ci95'] = next(intervals)
    paths = [base / 'eligible-meals.json', base / 'splits.json', raw / 'manifest.json', out / 'runs.json',
             ROOT / 'docs/HISTORY_MISSINGNESS_PROTOCOL.md', ROOT / 'history_missingness.py', ROOT / 'glucopatterns.py',
             ROOT / 'glucotrust.py', ROOT / 'cgmacros.py', ROOT / 'paired_analysis.py']
    payload = {'config': {'ratios': RATIOS, 'modes': MODES, 'simulation_seeds': SEEDS, 'history_meals': 10,
                           'bootstrap_replicates': 10000, 'bootstrap_seed': 20260915, 'numpy_version': np.__version__},
               'sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               'participants': len(participants), 'test_meals': sum(len(f['history']['test']) for f in splits if f['history']),
               'runs': len(runs), 'summaries': summaries}
    (ROOT / 'docs/history-missingness-results.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    lines = ['# Does personalization survive missing historical inputs?', '',
        '[Protocol](HISTORY_MISSINGNESS_PROTOCOL.md). Exploratory input-only degradation; outcome labels and later evaluation inputs remain complete. Source-derived summaries: CC BY-NC-SA 4.0.', '',
        f'{len(participants)} people, {payload["test_meals"]} fixed later test meals, {len(runs)} simulation runs. Runs and seeds are not independent participants. Ten original history meals per person; fewer may remain usable after masking.', '',
        'Masks apply to the whole early-history timeline. Exposure is the actual missing fraction inside the historical premeal feature windows; it need not equal the requested timeline budget. Positive benefit favors personalization over pooled prediction; positive cost means worse than clean-history personalization. Units of MAE, benefit and cost: mg/dL.', '',
        '| Requested | Pattern | Premeal exposure | Usable history | Personalized MAE | Remaining benefit [95% CI] | Degradation cost [95% CI] |',
        '|---|---|---:|---:|---:|---|---|']
    for s in summaries:
        if s['status'] != 'complete':
            lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | Infeasible: {s["infeasible_runs"]} runs | — | — | — | — |')
        else:
            b, c = s['benefit_ci95'], s['cost_ci95']
            lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | {s["premeal_missing_fraction"]:.2%} | {s["usable_history"]:.2f} | {s["personalized_mae"]:.3f} | {s["benefit"]:.3f} [{b[0]:.3f}, {b[1]:.3f}] | {s["cost"]:.3f} [{c[0]:.3f}, {c[1]:.3f}] |')
    lines += ['', '## Interpretation boundaries', '',
        'A small or zero night effect can result from little overlap with the premeal windows that this model uses; it does not establish general robustness to nighttime data loss. The adaptation policy drops a meal when fewer than 15/30 premeal minutes remain, but never drops its participant or later test meals. Any incomplete night configuration is reported without an aggregate effect.', '',
        'Intervals are pointwise participant-bootstrap percentiles after averaging seeds within person, conditional on the fitted folds and fixed simulations. No clinical, causal, multiplicity-adjusted or real-time forecasting claim is made. Published source interpolation remains a limitation. This experiment does not degrade historical labels or nutrition records.', '',
        '## Reproduction', '',
        'Run `python reproduce.py patterns` first, then `python reproduce.py history`. Local run metrics and deterministic mask hashes are in `outputs/history_missingness/runs.json`; [aggregate results and source/code hashes](history-missingness-results.json) are bundled. Exact masks regenerate from the fixed timeline, key, seed and code.']
    (ROOT / 'docs/HISTORY_MISSINGNESS_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'people': len(participants), 'runs': len(runs), '20_percent': [{k:v for k,v in s.items() if k != 'per_person'} for s in summaries if s['ratio'] == .2]}, indent=2))


if __name__ == '__main__': main()
