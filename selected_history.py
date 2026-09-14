"""Repeat exact v1 masks with selected ridge; decompose availability/feature costs."""
import hashlib
import json
import math
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from cgmacros import parse_file
from glucotrust import mask
from glucopatterns import predict, adaptation_offset
from history_missingness import degrade_meal
from model_comparison import fit_ridge
from paired_analysis import bootstrap_columns

ROOT = Path(__file__).resolve().parent
METRICS = ['benefit', 'total_cost', 'availability_cost', 'feature_cost', 'selected_advantage']


def decompose(model, history, test, glucose, deleted):
    retained, degraded = [], []
    removed = 0
    for meal in history:
        damaged, count = degrade_meal(meal, glucose, deleted)
        removed += count
        if damaged is not None:
            retained.append(meal)
            degraded.append(damaged)
    residuals = [predict(model, r) - r['target'] for r in test]
    def error(rows):
        offset = adaptation_offset(model, rows)
        return statistics.mean(abs(v + offset) for v in residuals)
    a, b, c = error(history), error(retained), error(degraded)
    pooled = statistics.mean(abs(v) for v in residuals)
    return {'clean_mae': a, 'availability_only_mae': b, 'degraded_mae': c, 'pooled_mae': pooled,
            'benefit': pooled - c, 'total_cost': c-a, 'availability_cost': b-a, 'feature_cost': c-b,
            'usable_history': len(retained), 'premeal_missing_fraction': removed / (30 * len(history))}


def main():
    provenance = {}
    for name in ['history-missingness-results.json', 'model-comparison-results.json']:
        record = json.loads((ROOT / 'docs' / name).read_text())
        for relative, digest in record['sha256'].items():
            if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != digest:
                raise ValueError(f'Upstream provenance mismatch: {relative}')
            provenance[relative] = digest
    original = json.loads((ROOT / 'outputs/history_missingness/runs.json').read_text())
    meals = json.loads((ROOT / 'outputs/glucopatterns/eligible-meals.json').read_text())
    indexed = {r['meal_id']:r for r in meals}
    splits = json.loads((ROOT / 'outputs/glucopatterns/splits.json').read_text())
    selection = {r['held_out']:r for r in json.loads((ROOT / 'outputs/model_comparison/selection.json').read_text())}
    raw = ROOT / 'data/local/cgmacros/raw'
    sources = {Path(e['file']).stem:e for e in json.loads((raw/'manifest.json').read_text())['files']}
    runs = []
    for fold in splits:
        if not fold['history']: continue
        pid = fold['participant']
        training = [r for r in meals if r['participant'] != pid]
        if sorted({r['participant'] for r in training}) != selection[pid]['training_participants']:
            raise ValueError('Selected-model training participants changed')
        model = fit_ridge(training, selection[pid]['selected_penalty'])
        history = [indexed[mid] for mid in fold['history']['adaptation_by_budget']['10']]
        test = [indexed[mid] for mid in fold['history']['test']]
        entry = sources[pid]
        path = raw / entry['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']: raise ValueError('Raw source changed')
        series, _ = parse_file(path)
        glucose = {datetime.fromisoformat(r['timestamp']):r['glucose_mg_dl'] for r in series['dexcom']}
        start = datetime.fromisoformat(history[0]['timestamp']) - timedelta(minutes=30)
        stop = datetime.fromisoformat(history[-1]['timestamp'])
        timeline = sorted(q for q in glucose if start <= q < stop)
        mask_rows = [{'timestamp':q.isoformat()} for q in timeline] + [{'timestamp':stop.isoformat()}]
        for old in [r for r in original if r['participant']==pid]:
            run = {k:old[k] for k in ['participant','ratio','mode','seed','status','test_meals']}
            if old['test_meals'] != len(test): raise ValueError('Test meals changed')
            if old['status'] != 'ok':
                runs.append(run)
                continue
            key = f'{pid}|history-input-v1|{old["ratio"]}|{old["mode"]}|{old["seed"]}'
            indices = mask(mask_rows, old['ratio'], old['mode'], random.Random(int(hashlib.sha256(key.encode()).hexdigest(),16)))
            digest = hashlib.sha256(json.dumps(indices).encode()).hexdigest()
            if digest != old['mask_indices_sha256']: raise ValueError('Mask differs from v1')
            stats = decompose(model, history, test, glucose, {timeline[i] for i in indices})
            if stats['usable_history'] != old['usable_history'] or not math.isclose(stats['premeal_missing_fraction'],old['premeal_missing_fraction'],abs_tol=1e-12):
                raise ValueError('Historical input exposure changed')
            runs.append({**run, **stats, 'mask_indices_sha256':digest, 'selected_penalty':selection[pid]['selected_penalty'],
                         'selected_advantage':old['personalized_mae']-stats['degraded_mae'], 'v1_degraded_mae':old['personalized_mae']})
    ids = sorted({r['participant'] for r in runs})
    summaries = []
    for ratio in [0.,.05,.1,.2]:
        for mode in ['random','block','night']:
            rs = [r for r in runs if r['ratio']==ratio and r['mode']==mode]
            if any(r['status']!='ok' for r in rs):
                summaries.append({'ratio':ratio,'mode':mode,'status':'incomplete'})
                continue
            keys = METRICS + ['degraded_mae','clean_mae','pooled_mae','usable_history','premeal_missing_fraction','v1_degraded_mae']
            people = []
            for pid in ids:
                pr = [r for r in rs if r['participant']==pid]
                if len(pr)!=10 or {r['seed'] for r in pr}!=set(range(10)): raise ValueError('Incomplete paired seeds')
                people.append({'participant':pid, **{k:statistics.mean(r[k] for r in pr) for k in keys}})
            summaries.append({'ratio':ratio,'mode':mode,'status':'complete','n':len(ids),'per_person':people,
                              **{k:statistics.mean(p[k] for p in people) for k in keys}})
    complete = [s for s in summaries if s['status']=='complete']
    intervals = iter(bootstrap_columns([[p[k] for p in s['per_person']] for s in complete for k in METRICS],10000,20260917))
    for s in complete:
        s['ci95'] = {k:next(intervals) for k in METRICS}
    out = ROOT/'outputs/selected_history'
    out.mkdir(parents=True,exist_ok=True)
    (out/'runs.json').write_text(json.dumps(runs),encoding='utf-8')
    for p in [ROOT/'selected_history.py',ROOT/'docs/SELECTED_HISTORY_PROTOCOL.md',out/'runs.json']:
        provenance[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    result = {'config':{'bootstrap_replicates':10000,'bootstrap_seed':20260917,'history_meals':10},'sha256':provenance,
              'n':len(ids),'test_meals':sum(len(f['history']['test']) for f in splits if f['history']),'runs':len(runs),'summaries':summaries}
    (ROOT/'docs/selected-history-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    lines = ['# Selected-model history missingness', '', '[Protocol and diagnostic definitions](SELECTED_HISTORY_PROTOCOL.md). All 5,280 original simulation keys and feasible mask hashes are reused; historical labels and 739 later test meals remain fixed for 44 participants. CGMacros-derived results: CC BY-NC-SA 4.0.', '',
        'Positive remaining benefit favors personalization over the selected pooled model. Positive cost means worse than clean selected-model personalization. Availability cost includes the change in shrinkage caused by dropping unusable meals. The retained-feature cost is evaluated on the same retained meals. These costs sum exactly but are order-dependent diagnostics, not causal attribution.', '',
        '| Requested | Pattern | Exposure | Usable meals | Selected personalized MAE | Remaining benefit [95% CI] | Total cost [95% CI] |',
        '|---|---|---:|---:|---:|---|---|']
    def interval(s,k): return f'{s[k]:.4f} [{s["ci95"][k][0]:.4f}, {s["ci95"][k][1]:.4f}]'
    for s in summaries:
        if s['status']!='complete':
            lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | Incomplete | — | — | — | — |')
        else:
            lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | {s["premeal_missing_fraction"]:.2%} | {s["usable_history"]:.2f} | {s["degraded_mae"]:.4f} | {interval(s,"benefit")} | {interval(s,"total_cost")} |')
    lines += ['', '## Decomposition and paired comparison with v1', '', '| Requested | Pattern | Availability cost [95% CI] | Retained-feature cost [95% CI] | v1 minus selected degraded MAE [95% CI] |', '|---|---|---|---|---|']
    for s in complete:
        lines.append(f'| {s["ratio"]:.0%} | {s["mode"]} | {interval(s,"availability_cost")} | {interval(s,"feature_cost")} | {interval(s,"selected_advantage")} |')
    lines += ['', '## Limits and reproduction', '',
        'Intervals are pointwise participant-bootstrap percentiles conditional on fitted folds, not multiplicity-adjusted or full-refitting intervals. Night exposure is low because masks rarely intersect these premeal features. This does not demonstrate general night robustness. Historical labels remain clean; state B uses clean retained features as a diagnostic counterfactual. Published interpolation and unknown meal-metadata timing prevent prospective forecasting claims.', '',
        'Run `python reproduce.py selected-history` after `patterns`, `history` and `compare`. Upstream hashes are validated; local exact-mask checks and all per-run metrics are in `outputs/selected_history/runs.json`. [Aggregate results and provenance](selected-history-results.json).']
    (ROOT/'docs/SELECTED_HISTORY_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in s.items() if k!='per_person'} for s in summaries if s['ratio']==.2],indent=2))


if __name__=='__main__': main()
